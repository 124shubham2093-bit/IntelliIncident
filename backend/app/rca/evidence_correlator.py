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
        sentry_evidence: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate factual evidence signals across 6 operational categories.
        Integrates telemetry, deployments, logs, tickets, GitHub commits, and Sentry runtime errors.
        """
        error_rate = float(metrics.get("error_rate", metrics.get("errorRate", 0.0)))
        latency_p99 = float(metrics.get("latency_p99", metrics.get("latencyP99", 0.0)))
        latency_p50 = float(metrics.get("latency_p50", metrics.get("latencyP50", 1.0)))
        cpu = float(metrics.get("cpu_utilization", metrics.get("cpuUtilization", 0.0)))
        mem = float(metrics.get("memory_utilization", metrics.get("memoryUtilization", 0.0)))
        dep_recency = int(
            metrics.get(
                "deployment_recency_minutes",
                metrics.get("deploymentRecencyMinutes", 999),
            )
        )
        req_vol = int(
            metrics.get(
                "request_volume",
                metrics.get("requestVolume", 1000),
            )
        )

        # Extract normalized Sentry data if present
        s_data = None
        if sentry_evidence:
            s_data = (
                sentry_evidence.model_dump()
                if hasattr(sentry_evidence, "model_dump")
                else (
                    sentry_evidence
                    if isinstance(sentry_evidence, dict)
                    else None
                )
            )

        s_status = s_data.get("status") if s_data else None
        s_is_active = bool(s_status == "CONNECTED")
        s_latest_issue = (
            s_data.get("latest_issue")
            if (s_is_active and s_data)
            else None
        )
        s_exc_type = (
            s_data.get("matched_exception_type")
            if (s_is_active and s_data)
            else None
        )
        s_exc_val = (
            s_data.get("matched_exception_value")
            if (s_is_active and s_data)
            else None
        )
        s_frames = (
            s_data.get("matched_stack_trace_frames", [])
            if (s_is_active and s_data)
            else []
        )
        s_release = (
            s_data.get("correlated_release")
            if (s_is_active and s_data)
            else None
        )

        # 1. DEPLOYMENT Evidence
        dep_evidence = []
        dep_score = 0.1

        if dep_recency <= 30:
            dep_evidence.append(
                f"Recent production release completed {dep_recency} minutes before incident onset."
            )
            dep_score += 0.45
        elif dep_recency <= 90:
            dep_evidence.append(
                f"Production release completed within last {dep_recency} minutes."
            )
            dep_score += 0.25

        for dep in deployments:
            if dep.get("status") == "FAILED":
                dep_evidence.append(
                    f"Failed release pipeline {dep.get('id')} reported on {dep.get('service')}."
                )
                dep_score += 0.20
            elif dep.get("status") == "ROLLED_BACK":
                dep_evidence.append(
                    f"Rollback event detected on {dep.get('service')} ({dep.get('commit_hash')})."
                )
                dep_score += 0.15

        # GitHub Commit Evidence for DEPLOYMENT
        if github_commits:
            for commit in github_commits:
                c_data = (
                    commit.model_dump()
                    if hasattr(commit, "model_dump")
                    else (
                        commit
                        if isinstance(commit, dict)
                        else {}
                    )
                )

                sha = c_data.get("sha", "")
                short_sha = c_data.get("short_sha") or (
                    sha[:7] if sha else "unknown"
                )

                msg = c_data.get("message", "").strip().split("\n")[0]

                author_info = c_data.get("author") or {}
                author_name = (
                    author_info.get("name")
                    or author_info.get("username")
                    if isinstance(author_info, dict)
                    else (
                        getattr(author_info, "name", None)
                        or "contributor"
                    )
                )

                stats = c_data.get("stats") or {}
                adds = (
                    stats.get("additions", 0)
                    if isinstance(stats, dict)
                    else getattr(stats, "additions", 0)
                )
                dels = (
                    stats.get("deletions", 0)
                    if isinstance(stats, dict)
                    else getattr(stats, "deletions", 0)
                )

                raw_files = c_data.get("files") or []
                file_count = len(raw_files)

                if msg:
                    dep_evidence.append(
                        f"Deployment commit {short_sha} ('{msg}') authored by "
                        f"{author_name} modified {file_count} files (+{adds}/-{dels})."
                    )
                else:
                    dep_evidence.append(
                        f"Deployment commit {short_sha} authored by "
                        f"{author_name} modified {file_count} files (+{adds}/-{dels})."
                    )

                changed_names = []

                for rf in raw_files:
                    fn = (
                        rf.get("filename")
                        if isinstance(rf, dict)
                        else getattr(rf, "filename", None)
                    )

                    if fn:
                        changed_names.append(fn)

                if changed_names:
                    sample_names = ", ".join(changed_names[:3])
                    dep_evidence.append(
                        f"Commit {short_sha} changed files: {sample_names}."
                    )

        # Sentry Release Evidence for DEPLOYMENT
        if s_is_active:
            matched_release = False

            if s_release:
                for dep in deployments:
                    c_hash = dep.get("commit_hash", "")

                    if c_hash and (
                        c_hash in s_release
                        or s_release in c_hash
                        or (
                            len(c_hash) >= 7
                            and c_hash[:7] in s_release
                        )
                    ):
                        dep_evidence.append(
                            f"Sentry error events tagged with release "
                            f"'{s_release}' matches deployment revision {c_hash[:7]}."
                        )
                        matched_release = True
                        break

            if not matched_release and s_latest_issue and dep_recency <= 90:
                dep_evidence.append(
                    f"Sentry error issue #{s_latest_issue.get('id')} surfaced "
                    f"during recent deployment window ({dep_recency}m)."
                )

        # 2. DATABASE Evidence
        db_evidence = []
        db_score = 0.1

        latency_ratio = latency_p99 / max(latency_p50, 1.0)

        if latency_p99 > 1200:
            db_evidence.append(
                f"P99 response latency elevated to {latency_p99:.0f}ms "
                f"indicating query execution queueing."
            )
            db_score += 0.35

        if latency_ratio > 4.0:
            db_evidence.append(
                f"Severe tail latency divergence (P99/P50 ratio "
                f"{latency_ratio:.1f}x) characteristic of connection lock contention."
            )
            db_score += 0.25

        for log in logs:
            msg = log.get("message", "").lower()

            if (
                "pool" in msg
                or "deadlock" in msg
                or "database" in msg
                or "query" in msg
            ):
                db_evidence.append(
                    f"Log marker: '{log.get('message')}'"
                )
                db_score += 0.20
                break

        # Sentry Database Error Correlation
        if s_is_active and (s_exc_type or s_exc_val):
            combined_sentry_err = (
                f"{s_exc_type or ''} {s_exc_val or ''}"
            ).lower()

            if any(
                k in combined_sentry_err
                for k in [
                    "operationalerror",
                    "pooltimeout",
                    "deadlock",
                    "databaseerror",
                    "integrityerror",
                    "connectionpool",
                    "querytimeout",
                    "timeout",
                    "databasetetimeout",
                ]
            ):
                db_evidence.append(
                    f"Sentry captured runtime database exception: diagnostic "
                    f"exception '{s_exc_type}' indicates database connection "
                    f"or query failure."
                )

        # 3. INFRASTRUCTURE Evidence
        infra_evidence = []
        infra_score = 0.1

        if cpu > 85.0:
            infra_evidence.append(
                f"Node CPU utilization saturated at {cpu:.1f}%."
            )
            infra_score += 0.40
        elif cpu > 70.0:
            infra_evidence.append(
                f"Elevated CPU utilization at {cpu:.1f}%."
            )
            infra_score += 0.20

        if mem > 85.0:
            infra_evidence.append(
                f"Process memory utilization at {mem:.1f}% "
                f"approaching container limit."
            )
            infra_score += 0.35

        for log in logs:
            msg = log.get("message", "").lower()

            if (
                "oom" in msg
                or "memory limit" in msg
                or "throttling" in msg
                or "disk" in msg
            ):
                infra_evidence.append(
                    f"Infrastructure alert in logs: '{log.get('message')}'"
                )
                infra_score += 0.25
                break

        # Sentry Infrastructure / Memory Contention Correlation
        if s_is_active and (s_exc_type or s_exc_val):
            combined_sentry_err = (
                f"{s_exc_type or ''} {s_exc_val or ''}"
            ).lower()

            if any(
                k in combined_sentry_err
                for k in [
                    "memoryerror",
                    "outofmemory",
                    "resourceexhausted",
                    "systemexit",
                ]
            ):
                infra_evidence.append(
                    f"Sentry exception '{s_exc_type}' confirms "
                    f"container resource exhaustion."
                )
                infra_score += 0.25

        # 4. CODE_ERROR Evidence
        code_evidence = []
        code_score = 0.1

        if error_rate > 15.0:
            code_evidence.append(
                f"Sustained application error rate of {error_rate:.1f}% "
                f"indicates unhandled runtime exceptions."
            )
            code_score += 0.35
        elif error_rate > 5.0:
            code_evidence.append(
                f"Elevated application error rate of {error_rate:.1f}%."
            )
            code_score += 0.20

        for log in logs:
            trace = log.get("stack_trace", "")

            if trace and len(trace) > 10:
                code_evidence.append(
                    f"Active stack trace detected: {log.get('message')}"
                )
                code_score += 0.30
                break

        # Sentry Runtime Error & Stack Trace Evidence for CODE_ERROR
        if s_is_active:
            if s_latest_issue:
                issue_title = s_latest_issue.get(
                    "title",
                    "Unhandled Sentry Exception",
                )
                ev_count = s_latest_issue.get("count", 1)

                code_evidence.append(
                    f"Sentry reports unresolved error issue "
                    f"#{s_latest_issue.get('id')} ('{issue_title}') "
                    f"with {ev_count} recorded event(s)."
                )
            elif s_data and s_data.get("issue_count", 0) > 0:
                code_evidence.append(
                    f"Sentry reports {s_data.get('issue_count')} "
                    f"unresolved issue(s)."
                )

            if s_exc_type:
                code_evidence.append(
                    f"Sentry reports diagnostic exception "
                    f"'{s_exc_type}': "
                    f"{s_exc_val or 'unhandled exception'}."
                )

            # Cross-Source Correlation:
            # Sentry stack trace frames against GitHub deployment commits
            if github_commits and s_frames:
                frame_matched = False

                for frame in s_frames:
                    f_fn = (
                        frame.get("filename")
                        if isinstance(frame, dict)
                        else getattr(frame, "filename", None)
                    )

                    f_line = (
                        frame.get("lineno")
                        if isinstance(frame, dict)
                        else getattr(frame, "lineno", None)
                    )

                    if not f_fn:
                        continue

                    f_base = (
                        f_fn.replace("\\", "/")
                        .split("/")[-1]
                    )

                    for commit in github_commits:
                        c_data = (
                            commit.model_dump()
                            if hasattr(commit, "model_dump")
                            else (
                                commit
                                if isinstance(commit, dict)
                                else {}
                            )
                        )

                        short_sha = c_data.get("short_sha") or (
                            c_data.get("sha", "")[:7]
                        )

                        raw_files = c_data.get("files") or []

                        for rf in raw_files:
                            gh_fn = (
                                rf.get("filename")
                                if isinstance(rf, dict)
                                else getattr(
                                    rf,
                                    "filename",
                                    None,
                                )
                            )

                            if not gh_fn:
                                continue

                            gh_base = (
                                gh_fn.replace("\\", "/")
                                .split("/")[-1]
                            )

                            if (
                                f_fn in gh_fn
                                or gh_fn in f_fn
                                or (
                                    len(f_base) >= 4
                                    and f_base == gh_base
                                )
                            ):
                                line_info = (
                                    f" (line {f_line})"
                                    if f_line
                                    else ""
                                )

                                code_evidence.append(
                                    f"Cross-source correlation: Sentry "
                                    f"stack trace frame '{f_fn}'{line_info} "
                                    f"matches file modified in deployment "
                                    f"commit {short_sha}."
                                )

                                frame_matched = True
                                break

                        if frame_matched:
                            break

                    if frame_matched:
                        break

        # Correlate stack trace / error logs with files changed in deployment commits
        if github_commits:
            matched = False

            for commit in github_commits:
                c_data = (
                    commit.model_dump()
                    if hasattr(commit, "model_dump")
                    else (
                        commit
                        if isinstance(commit, dict)
                        else {}
                    )
                )

                sha = c_data.get("sha", "")
                short_sha = c_data.get("short_sha") or (
                    sha[:7] if sha else "unknown"
                )

                raw_files = c_data.get("files") or []

                for rf in raw_files:
                    fn = (
                        rf.get("filename")
                        if isinstance(rf, dict)
                        else getattr(rf, "filename", None)
                    )

                    if not fn:
                        continue

                    base_fn = fn.split("/")[-1]

                    for log in logs:
                        trace = log.get("stack_trace") or ""
                        msg = log.get("message") or ""
                        combined_text = f"{trace}\n{msg}"

                        if (
                            fn in combined_text
                            or (
                                len(base_fn) >= 4
                                and base_fn in combined_text
                            )
                        ):
                            code_evidence.append(
                                f"Stack trace references '{fn}' "
                                f"modified in deployment commit {short_sha}."
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
            traffic_evidence.append(
                f"Abnormal traffic volume surge recorded at "
                f"{req_vol:,} req/s."
            )
            traffic_score += 0.45
        elif req_vol > 3500:
            traffic_evidence.append(
                f"Higher than median request load ({req_vol:,} req/s)."
            )
            traffic_score += 0.20

        if len(tickets) > 2:
            traffic_evidence.append(
                f"Concurrent spike in user-reported customer tickets "
                f"({len(tickets)} tickets)."
            )
            traffic_score += 0.15

        # 6. NETWORK Evidence
        net_evidence = []
        net_score = 0.1

        if latency_p99 > 800 and error_rate > 3.0 and cpu < 70.0:
            net_evidence.append(
                "High latency and network error rate without local CPU "
                "saturation points to upstream or network hop degradation."
            )
            net_score += 0.35

        for log in logs:
            msg = log.get("message", "").lower()

            if (
                "dns" in msg
                or "timeout" in msg
                or "reset by peer" in msg
                or "socket" in msg
            ):
                net_evidence.append(
                    f"Network error in log stream: '{log.get('message')}'"
                )
                net_score += 0.30
                break

        # Sentry Network Disruption Correlation
        if s_is_active and (s_exc_type or s_exc_val):
            combined_sentry_err = (
                f"{s_exc_type or ''} {s_exc_val or ''}"
            ).lower()

            if any(
                k in combined_sentry_err
                for k in [
                    "connectionrefused",
                    "connecttimeout",
                    "socketerror",
                    "remotedisconnected",
                    "gatewaytimeout",
                    "httperror",
                ]
            ):
                net_evidence.append(
                    f"Sentry exception '{s_exc_type}' indicates "
                    f"transport/network communication fault."
                )
                net_score += 0.20

        return {
            "DEPLOYMENT": {
                "score": min(round(dep_score, 2), 0.96),
                "evidence": dep_evidence,
            },
            "DATABASE": {
                "score": min(round(db_score, 2), 0.95),
                "evidence": db_evidence,
            },
            "INFRASTRUCTURE": {
                "score": min(round(infra_score, 2), 0.95),
                "evidence": infra_evidence,
            },
            "CODE_ERROR": {
                "score": min(round(code_score, 2), 0.95),
                "evidence": code_evidence,
            },
            "TRAFFIC": {
                "score": min(round(traffic_score, 2), 0.92),
                "evidence": traffic_evidence,
            },
            "NETWORK": {
                "score": min(round(net_score, 2), 0.92),
                "evidence": net_evidence,
            },
        }