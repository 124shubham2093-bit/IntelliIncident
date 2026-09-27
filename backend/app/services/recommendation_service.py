"""
Operational Playbook Recommendation Service for IntelliIncident
Generates structured investigation and mitigation playbooks based on identified root causes.

CRITICAL SAFETY DESIGN:
IntelliIncident is strictly an analysis and recommendation platform.
It NEVER executes any operational or remediation commands automatically.
All suggested commands are explicitly labeled as "Operator action" / "Suggested command"
for manual review and execution by human SRE/on-call engineers.
"""

from typing import Dict, Any, List, Optional
from backend.app.core.config import settings

class RecommendationService:
    @staticmethod
    def generate_recommendations(
        top_candidate: Dict[str, Any],
        service_name: str,
        severity: str,
        github_commits: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        category = top_candidate.get("category", "CODE_ERROR")
        recommendations = []

        if category == "DEPLOYMENT":
            repo_slug = (
                f"{settings.GITHUB_REPO_OWNER}/{settings.GITHUB_REPO_NAME}"
                if settings.GITHUB_REPO_OWNER and settings.GITHUB_REPO_NAME
                else f"org/{service_name}"
            )
            rec02_cmd = f"gh release view --repo {repo_slug} --json tagName,publishedAt"
            rec02_desc = (
                "Operator action: Review recent commit diffs and migration scripts pushed in the last release window. "
                "Check for unhandled null safety or altered environment variables."
            )
            rec02_title = "Inspect release commit diff for unhandled exceptions or config errors"
            if github_commits:
                first_c = github_commits[0]
                c_data = first_c.model_dump() if hasattr(first_c, "model_dump") else (first_c if isinstance(first_c, dict) else {})
                sha = c_data.get("sha", "")
                short_sha = c_data.get("short_sha") or (sha[:7] if sha else "")
                html_url = c_data.get("html_url") or ""
                if short_sha:
                    rec02_cmd = f"gh browse {short_sha} --repo {repo_slug}"
                    rec02_title = f"Inspect commit {short_sha} diff for unhandled exceptions or config errors"
                    if html_url:
                        rec02_desc = f"Operator action: Review commit diff {short_sha} ({html_url}) for unhandled exceptions or breaking schema changes."
                    else:
                        rec02_desc = f"Operator action: Review commit diff {short_sha} for unhandled exceptions or breaking schema changes."

            recommendations.append({
                "id": "REC-01",
                "title": f"Roll back {service_name} to previous stable release",
                "description": (
                    f"Operator action (Suggested command): Revert the recent deployment for {service_name}. "
                    "Verify deployment status before and after execution to confirm traffic diversion."
                ),
                "priority": "CRITICAL" if severity in ["CRITICAL", "HIGH"] else "HIGH",
                "category": "ROLLBACK",
                "actionCmd": f"kubectl rollout undo deployment/{service_name} -n production",
            })
            recommendations.append({
                "id": "REC-02",
                "title": rec02_title,
                "description": rec02_desc,
                "priority": "HIGH",
                "category": "INVESTIGATION",
                "actionCmd": rec02_cmd,
            })
            recommendations.append({
                "id": "REC-03",
                "title": "Validate error rate reduction in canary telemetry post-rollback",
                "description": (
                    "Operator action: Monitor error rates and P99 latency in Prometheus/Datadog for 10 minutes post-mitigation."
                ),
                "priority": "MEDIUM",
                "category": "VERIFICATION",
                "actionCmd": f"curl -s http://prometheus:9090/api/v1/query?query=rate(http_requests_total{{service='{service_name}',status=~'5..'}}[5m])",
            })

        elif category == "DATABASE":
            recommendations.append({
                "id": "REC-01",
                "title": f"Increase connection pool max capacity for {service_name}",
                "description": (
                    f"Operator action (Suggested command): Dynamically scale active connection pool limits for {service_name} "
                    "to relieve immediate acquisition timeout bottlenecks."
                ),
                "priority": "HIGH",
                "category": "MITIGATION",
                "actionCmd": f"kubectl set env deployment/{service_name} DB_POOL_MAX=75 DB_POOL_TIMEOUT_MS=5000",
            })
            recommendations.append({
                "id": "REC-02",
                "title": "Kill long-running locking transactions on primary database",
                "description": (
                    "Operator action: Query pg_stat_activity for transactions active longer than 60 seconds and evaluate cancellation."
                ),
                "priority": "CRITICAL" if severity == "CRITICAL" else "HIGH",
                "category": "INVESTIGATION",
                "actionCmd": "psql -h db-primary -c \"SELECT pid, query_start, state, query FROM pg_stat_activity WHERE state != 'idle' AND now() - query_start > interval '60 seconds';\"",
            })
            recommendations.append({
                "id": "REC-03",
                "title": "Verify query queue depth stabilization",
                "description": (
                    "Operator action: Confirm DB wait event count returns below operational SLO threshold."
                ),
                "priority": "MEDIUM",
                "category": "VERIFICATION",
                "actionCmd": f"curl -s http://monitoring/db/{service_name}/pool-status",
            })

        elif category == "INFRASTRUCTURE":
            recommendations.append({
                "id": "REC-01",
                "title": f"Horizontally autoscale deployment replicas for {service_name}",
                "description": (
                    f"Operator action (Suggested command): Increase replica count for {service_name} "
                    "to distribute high CPU/memory utilization across more worker pods."
                ),
                "priority": "CRITICAL" if severity in ["CRITICAL", "HIGH"] else "HIGH",
                "category": "MITIGATION",
                "actionCmd": f"kubectl scale deployment/{service_name} --replicas=8 -n production",
            })
            recommendations.append({
                "id": "REC-02",
                "title": "Inspect memory profiling & JVM/Node heap metrics for leaks",
                "description": (
                    "Operator action: Collect heap dump or thread trace from deteriorating pod instances."
                ),
                "priority": "HIGH",
                "category": "INVESTIGATION",
                "actionCmd": f"kubectl exec -it $(kubectl get pods -l app={service_name} -o jsonpath='{{.items[0].metadata.name}}') -- jcmd 1 GC.heap_dump /tmp/dump.hprof",
            })
            recommendations.append({
                "id": "REC-03",
                "title": "Verify node CPU throttled ratio returns to nominal (<5%)",
                "description": (
                    "Operator action: Inspect cgroup cpu.stat metrics to ensure throttling has ceased."
                ),
                "priority": "MEDIUM",
                "category": "VERIFICATION",
            })

        elif category == "TRAFFIC":
            recommendations.append({
                "id": "REC-01",
                "title": f"Enable aggressive edge rate limiting for {service_name}",
                "description": (
                    f"Operator action (Suggested command): Adjust ingress rate-limiting policy to protect {service_name} "
                    "from inbound request volumetric saturation."
                ),
                "priority": "HIGH",
                "category": "MITIGATION",
                "actionCmd": f"kubectl annotate ingress/{service_name}-ingress nginx.ingress.kubernetes.io/limit-rps='250' --overwrite",
            })
            recommendations.append({
                "id": "REC-02",
                "title": "Inspect ingress access logs for anomalous client IP bursts",
                "description": (
                    "Operator action: Analyze top request source IPs and user-agent strings over the last 15 minutes."
                ),
                "priority": "MEDIUM",
                "category": "INVESTIGATION",
                "actionCmd": f"kubectl logs -l app=ingress-nginx --tail=5000 | grep {service_name} | awk '{{print $1}}' | sort | uniq -c | sort -nr | head -n 10",
            })
            recommendations.append({
                "id": "REC-03",
                "title": "Verify throughput equilibrium and 429 response rate",
                "description": (
                    "Operator action: Confirm successful 200 HTTP response ratio returns above 99.5%."
                ),
                "priority": "LOW",
                "category": "VERIFICATION",
            })

        else: # CODE_ERROR or NETWORK
            rec02_desc = (
                "Operator action: Stream real-time exception logs to identify the exact line and dependency fault."
            )
            if github_commits:
                first_c = github_commits[0]
                c_data = first_c.model_dump() if hasattr(first_c, "model_dump") else (first_c if isinstance(first_c, dict) else {})
                sha = c_data.get("sha", "")
                short_sha = c_data.get("short_sha") or (sha[:7] if sha else "")
                html_url = c_data.get("html_url") or ""
                if short_sha:
                    if html_url:
                        rec02_desc += f" Cross-reference with commit {short_sha} ({html_url})."
                    else:
                        rec02_desc += f" Cross-reference with commit {short_sha}."

            recommendations.append({
                "id": "REC-01",
                "title": f"Restart degraded pod instances of {service_name}",
                "description": (
                    f"Operator action (Suggested command): Perform a rolling restart on {service_name} to clear transient runtime state "
                    "and stale network connection sockets."
                ),
                "priority": "HIGH",
                "category": "MITIGATION",
                "actionCmd": f"kubectl rollout restart deployment/{service_name} -n production",
            })
            recommendations.append({
                "id": "REC-02",
                "title": "Extract full stack traces from error log stream",
                "description": rec02_desc,
                "priority": "HIGH",
                "category": "INVESTIGATION",
                "actionCmd": f"kubectl logs -l app={service_name} --tail=200 --prefix | grep -iE 'error|fatal|exception'",
            })
            recommendations.append({
                "id": "REC-03",
                "title": "Verify socket connection health and error drop",
                "description": (
                    "Operator action: Verify synthetic health check endpoints return HTTP 200 within SLA threshold."
                ),
                "priority": "MEDIUM",
                "category": "VERIFICATION",
                "actionCmd": f"curl -Iv https://api.production.internal/{service_name}/healthz",
            })

        return recommendations
