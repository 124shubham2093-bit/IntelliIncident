'''
Demo Runtime Error & Telemetry Ingestion Client for IntelliIncident.
Generates an intentional runtime error with realistic stack trace,
attaches operational metrics, and sends to POST /api/incidents
using the Environment API Key.
'''

import argparse
import json
import sys
import traceback
import urllib.request
import urllib.error


def execute_intentional_fault(file_path: str = "backend/app/main.py", target_line: int = 25):
    '''
    Generate a realistic, deterministic stack trace pointing to a repository source file.
    '''
    try:
        # Generate genuine Python traceback
        raise ConnectionRefusedError(
            f"Failed to establish database connection pool after 3 retries (upstream host timeout)"
        )
    except Exception as exc:
        raw_trace = traceback.format_exc()
        # If custom target file is requested, format a realistic trace for that file and line
        if file_path:
            formatted_trace = (
                f"Traceback (most recent call last):\n"
                f"  File \"{file_path}\", line {target_line}, in execute_query\n"
                f"    conn = await self._connection_pool.acquire(timeout=5.0)\n"
                f"ConnectionRefusedError: Failed to establish database connection pool after 3 retries"
            )
            return type(exc).__name__, str(exc), formatted_trace
        return type(exc).__name__, str(exc), raw_trace


def send_telemetry(
    api_url: str,
    api_key: str,
    service: str,
    commit_sha: str = None,
    file_path: str = "backend/app/main.py",
    target_line: int = 25,
):
    err_type, err_msg, stack_trace = execute_intentional_fault(file_path=file_path, target_line=target_line)

    endpoint = f"{api_url.rstrip('/')}/api/incidents"
    payload = {
        "title": f"Runtime Exception: {err_type} in {service}",
        "service": service,
        "summary": f"Unhandled {err_type} during query execution on {service}.",
        "status": "OPEN",
        "error_type": err_type,
        "error_message": err_msg,
        "stack_trace": stack_trace,
        "metrics": {
            "error_rate": 18.5,
            "latency_p99": 850.0,
            "latency_p50": 65.0,
            "affected_users": 1420,
            "request_volume": 4200,
            "deployment_recency_minutes": 25,
            "cpu_utilization": 78.0,
            "memory_utilization": 82.0,
            "service_criticality": 4,
        },
    }

    if commit_sha:
        payload["commit_sha"] = commit_sha

    req_data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "IntelliIncident-TelemetrySDK/1.0",
    }
    if api_key:
        headers["X-API-Key"] = api_key

    req = urllib.request.Request(endpoint, data=req_data, headers=headers, method="POST")

    print("=" * 65)
    print("INTELLIINCIDENT DEMO TELEMETRY SENDER")
    print("=" * 65)
    print(f"Target Endpoint : {endpoint}")
    print(f"Service         : {service}")
    print(f"API Key         : {api_key[:10]}...{api_key[-6:] if api_key and len(api_key) > 16 else ''}")
    print(f"Commit SHA      : {commit_sha or '(Inherited from Environment)'}")
    print(f"Fault Location  : {file_path}:{target_line}")
    print("-" * 65)

    try:
        with urllib.request.urlopen(req) as response:
            resp_body = response.read().decode("utf-8")
            data = json.loads(resp_body)
            print("[SUCCESS] Incident ingested and analyzed successfully!")
            print(f"  Incident ID       : {data.get('id')}")
            print(f"  Title             : {data.get('title')}")
            print(f"  ML Predicted Sev  : {data.get('severity')}")
            print(f"  Fuzzy Risk Level  : {data.get('risk')} (Score: {data.get('riskScore')})")
            print(f"  Anomaly Detected  : {data.get('anomalyDetected')}")
            print(f"  Topology Bound    : Project={data.get('projectId')}, App={data.get('applicationId')}, Env={data.get('environmentId')}")

            gh_src = data.get("githubSourceEvidence") or {}
            print("\nGitHub Source Investigation:")
            print(f"  Status            : {gh_src.get('status')}")
            print(f"  Matched File      : {gh_src.get('file_path')}")
            print(f"  Matched Line      : {gh_src.get('target_line')}")
            print(f"  Deployment Commit : {gh_src.get('deployment_commit')}")
            print(f"  Message           : {gh_src.get('message')}")

            if gh_src.get("source_lines"):
                print("\nSource Context Code Window:")
                for line in gh_src["source_lines"]:
                    marker = ">> " if line.get("is_target") else "   "
                    print(f"  {marker}{line.get('line_number'):4d} | {line.get('content')}")

            rca = data.get("rootCauseCandidates") or []
            if rca:
                print("\nTop Root Cause:")
                print(f"  Category          : {rca[0].get('category')}")
                print(f"  Score             : {rca[0].get('score'):.2f}")
                print(f"  Explanation       : {rca[0].get('explanation')}")

            print("=" * 65)
            return data

    except urllib.error.HTTPError as e:
        err_content = e.read().decode("utf-8")
        print(f"[ERROR] HTTP {e.code}: {e.reason}")
        print(f"Details: {err_content}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to send telemetry: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send real runtime error telemetry to IntelliIncident")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base URL of IntelliIncident backend")
    parser.add_argument("--api-key", required=True, help="Environment API key (ii_live_...)")
    parser.add_argument("--commit-sha", default=None, help="Deployed Git commit SHA")
    parser.add_argument("--service", default="PaymentGateway", help="Service name")
    parser.add_argument("--file", default="backend/app/main.py", help="Relative file path in repository")
    parser.add_argument("--line", type=int, default=25, help="Line number where exception occurred")

    args = parser.parse_args()
    send_telemetry(
        api_url=args.url,
        api_key=args.api_key,
        service=args.service,
        commit_sha=args.commit_sha,
        file_path=args.file,
        target_line=args.line,
    )
