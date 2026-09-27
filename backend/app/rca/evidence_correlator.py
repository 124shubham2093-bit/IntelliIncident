"""
Evidence Correlator for IntelliIncident Root Cause Analysis
Analyzes runtime logs, deployments, telemetry anomalies, and support tickets
to construct empirical evidence matrices for candidate hypotheses.
"""

from typing import Dict, Any, List, Optional
import datetime

class EvidenceCorrelator:
    @staticmethod
    def correlate(
        incident: Dict[str, Any],
        metrics: Dict[str, Any],
        logs: List[Dict[str, Any]],
        deployments: List[Dict[str, Any]],
        tickets: List[Dict[str, Any]],
        github_commits: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate factual evidence signals across 6 operational categories.
        """
        error_rate = float(metrics.get("error_rate", metrics.get("errorRate", 0.0)))
        latency_p99 = float(metrics.get("latency_p99", metrics.get("latencyP99", 0.0)))
        latency_p50 = float(metrics.get("latency_p50", metrics.get("latencyP50", 1.0)))
        cpu = float(metrics.get("cpu_utilization", metrics.get("cpuUtilization", 0.0)))
        mem = float(metrics.get("memory_utilization", metrics.get("memoryUtilization", 0.0)))
        dep_recency = int(metrics.get("deployment_recency_minutes", metrics.get("deploymentRecencyMinutes", 999)))
        req_vol = int(metrics.get("request_volume", metrics.get("requestVolume", 1000)))

        # 1. DEPLOYMENT Evidence
        dep_evidence = []
        dep_score = 0.1
        if dep_recency <= 30:
            dep_evidence.append(f"Recent production release completed {dep_recency} minutes before incident onset.")
            dep_score += 0.45
        elif dep_recency <= 90:
            dep_evidence.append(f"Production release completed within last {dep_recency} minutes.")
            dep_score += 0.25

        for dep in deployments:
            if dep.get("status") == "FAILED":
                dep_evidence.append(f"Failed release pipeline {dep.get('id')} reported on {dep.get('service')}.")
                dep_score += 0.20
            elif dep.get("status") == "ROLLED_BACK":
                dep_evidence.append(f"Rollback event detected on {dep.get('service')} ({dep.get('commit_hash')}).")
                dep_score += 0.15

        # GitHub Commit Evidence for DEPLOYMENT
        if github_commits:
            for commit in github_commits:
                c_data = commit.model_dump() if hasattr(commit, "model_dump") else (commit if isinstance(commit, dict) else {})
                sha = c_data.get("sha", "")
                short_sha = c_data.get("short_sha") or (sha[:7] if sha else "unknown")
                msg = c_data.get("message", "").strip().split("\n")[0]
                author_info = c_data.get("author") or {}
                author_name = author_info.get("name") or author_info.get("username") if isinstance(author_info, dict) else (getattr(author_info, "name", None) or "contributor")
                stats = c_data.get("stats") or {}
                adds = stats.get("additions", 0) if isinstance(stats, dict) else getattr(stats, "additions", 0)
                dels = stats.get("deletions", 0) if isinstance(stats, dict) else getattr(stats, "deletions", 0)
                raw_files = c_data.get("files") or []
                file_count = len(raw_files)

                if msg:
                    dep_evidence.append(
                        f"Deployment commit {short_sha} ('{msg}') authored by {author_name} modified {file_count} files (+{adds}/-{dels})."
                    )
                else:
                    dep_evidence.append(
                        f"Deployment commit {short_sha} authored by {author_name} modified {file_count} files (+{adds}/-{dels})."
                    )

                changed_names = []
                for rf in raw_files:
                    fn = rf.get("filename") if isinstance(rf, dict) else getattr(rf, "filename", None)
                    if fn:
                        changed_names.append(fn)
                if changed_names:
                    sample_names = ", ".join(changed_names[:3])
                    dep_evidence.append(f"Commit {short_sha} changed files: {sample_names}.")


        # 2. DATABASE Evidence
        db_evidence = []
        db_score = 0.1
        latency_ratio = latency_p99 / max(latency_p50, 1.0)
        if latency_p99 > 1200:
            db_evidence.append(f"P99 response latency elevated to {latency_p99:.0f}ms indicating query execution queueing.")
            db_score += 0.35
        if latency_ratio > 4.0:
            db_evidence.append(f"Severe tail latency divergence (P99/P50 ratio {latency_ratio:.1f}x) characteristic of connection lock contention.")
            db_score += 0.25

        for log in logs:
            msg = log.get("message", "").lower()
            if "pool" in msg or "deadlock" in msg or "database" in msg or "query" in msg:
                db_evidence.append(f"Log marker: '{log.get('message')}'")
                db_score += 0.20
                break

        # 3. INFRASTRUCTURE Evidence
        infra_evidence = []
        infra_score = 0.1
        if cpu > 85.0:
            infra_evidence.append(f"Node CPU utilization saturated at {cpu:.1f}%.")
            infra_score += 0.40
        elif cpu > 70.0:
            infra_evidence.append(f"Elevated CPU utilization at {cpu:.1f}%.")
            infra_score += 0.20

        if mem > 85.0:
            infra_evidence.append(f"Process memory utilization at {mem:.1f}% approaching container limit.")
            infra_score += 0.35

        for log in logs:
            msg = log.get("message", "").lower()
            if "oom" in msg or "memory limit" in msg or "throttling" in msg or "disk" in msg:
                infra_evidence.append(f"Infrastructure alert in logs: '{log.get('message')}'")
                infra_score += 0.25
                break

        # 4. CODE_ERROR Evidence
        code_evidence = []
        code_score = 0.1
        if error_rate > 15.0:
            code_evidence.append(f"Sustained application error rate of {error_rate:.1f}% indicates unhandled runtime exceptions.")
            code_score += 0.35
        elif error_rate > 5.0:
            code_evidence.append(f"Elevated application error rate of {error_rate:.1f}%.")
            code_score += 0.20

        for log in logs:
            trace = log.get("stack_trace", "")
            if trace and len(trace) > 10:
                code_evidence.append(f"Active stack trace detected: {log.get('message')}")
                code_score += 0.30
                break

        # Correlate stack trace / error logs with files changed in deployment commits
        if github_commits:
            matched = False
            for commit in github_commits:
                c_data = commit.model_dump() if hasattr(commit, "model_dump") else (commit if isinstance(commit, dict) else {})
                sha = c_data.get("sha", "")
                short_sha = c_data.get("short_sha") or (sha[:7] if sha else "unknown")
                raw_files = c_data.get("files") or []
                for rf in raw_files:
                    fn = rf.get("filename") if isinstance(rf, dict) else getattr(rf, "filename", None)
                    if not fn:
                        continue
                    base_fn = fn.split("/")[-1]
                    for log in logs:
                        trace = log.get("stack_trace") or ""
                        msg = log.get("message") or ""
                        combined_text = f"{trace}\n{msg}"
                        if fn in combined_text or (len(base_fn) >= 4 and base_fn in combined_text):
                            code_evidence.append(
                                f"Stack trace references '{fn}' modified in deployment commit {short_sha}."
                            )
                            matched = True
                            break
                    if matched:
                        break
                if matched:
                    break

        # 5. TRAFFIC Evidence
        traffic_evidence = []
        traffic_score = 0.1
        if req_vol > 6000:
            traffic_evidence.append(f"Abnormal traffic volume surge recorded at {req_vol:,} req/s.")
            traffic_score += 0.45
        elif req_vol > 3500:
            traffic_evidence.append(f"Higher than median request load ({req_vol:,} req/s).")
            traffic_score += 0.20

        if len(tickets) > 2:
            traffic_evidence.append(f"Concurrent spike in user-reported customer tickets ({len(tickets)} tickets).")
            traffic_score += 0.15

        # 6. NETWORK Evidence
        net_evidence = []
        net_score = 0.1
        if latency_p99 > 800 and error_rate > 3.0 and cpu < 70.0:
            net_evidence.append("High latency and network error rate without local CPU saturation points to upstream or network hop degradation.")
            net_score += 0.35

        for log in logs:
            msg = log.get("message", "").lower()
            if "dns" in msg or "timeout" in msg or "reset by peer" in msg or "socket" in msg:
                net_evidence.append(f"Network error in log stream: '{log.get('message')}'")
                net_score += 0.30
                break

        return {
            "DEPLOYMENT": {"score": min(round(dep_score, 2), 0.96), "evidence": dep_evidence},
            "DATABASE": {"score": min(round(db_score, 2), 0.95), "evidence": db_evidence},
            "INFRASTRUCTURE": {"score": min(round(infra_score, 2), 0.95), "evidence": infra_evidence},
            "CODE_ERROR": {"score": min(round(code_score, 2), 0.95), "evidence": code_evidence},
            "TRAFFIC": {"score": min(round(traffic_score, 2), 0.92), "evidence": traffic_evidence},
            "NETWORK": {"score": min(round(net_score, 2), 0.92), "evidence": net_evidence},
        }
