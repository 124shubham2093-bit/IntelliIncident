'''
Deterministic Stack Trace Parser for IntelliIncident.
Extracts structured file path, line number, column, and function name
from Python and JavaScript/TypeScript error traces. Normalizes file paths
to repository-relative paths for GitHub code investigation.
'''

import os
import re
from typing import Optional, List, Dict, Any
from backend.app.schemas.github import GitHubSourceLocation

# Common Python traceback frame: File "path/to/file.py", line 42, in function_name
PYTHON_FRAME_RE = re.compile(
    r'File\s+["\'](?P<file>[^"\']+)["\'],\s+line\s+(?P<line>\d+)(?:,\s+in\s+(?P<func>[^\n\r]+))?',
    re.IGNORECASE,
)

# Common JS/TS stack frame:
# at processPayment (src/api/payment.ts:42:17)
# at src/api/payment.ts:42:17
# at async processPayment (src/api/payment.ts:42:17)
JS_FRAME_WITH_COL_RE = re.compile(
    r'^\s*at\s+(?:(?:async\s+)?(?P<func>[^\(\s]+)\s+\()?(?P<file>[^\s\(\):]+):(?P<line>\d+):(?P<col>\d+)\)?',
    re.MULTILINE,
)

JS_FRAME_NO_COL_RE = re.compile(
    r'^\s*at\s+(?:(?:async\s+)?(?P<func>[^\(\s]+)\s+\()?(?P<file>[^\s\(\):]+):(?P<line>\d+)\)?',
    re.MULTILINE,
)

IGNORED_FRAME_MARKERS = [
    "<string>",
    "<stdin>",
    "<frozen ",
    "site-packages/",
    "dist-packages/",
    "lib/python",
    "lib64/python",
    "node_modules/",
    "node:internal",
    "internal/process",
    "internal/modules",
]


def normalize_file_path(raw_path: str, repo_files: Optional[List[str]] = None) -> str:
    '''
    Normalize raw file path from stack trace to a repository-relative path.
    Converts backslashes, removes drive letters, leading slashes, and
    strips absolute machine prefixes.
    '''
    if not raw_path:
        return ""

    # Replace backslashes with forward slashes
    path = raw_path.replace("\\", "/").strip()

    # Remove URI scheme if present
    if path.startswith("file:///"):
        path = path[8:]
    elif path.startswith("file://"):
        path = path[7:]

    # Remove Windows drive letter if present, e.g. "C:/" or "c:/"
    if re.match(r"^[a-zA-Z]:/", path):
        path = path[3:]

    # Strip leading slash
    path = path.lstrip("/")

    # If repo_files list provided, try to match suffixes
    if repo_files:
        path_lower = path.lower()
        for rf in repo_files:
            rf_clean = rf.replace("\\", "/").lstrip("/")
            if path_lower.endswith(rf_clean.lower()):
                return rf_clean

    # Try heuristic stripping for common deployment roots:
    # /app/backend/..., /var/app/..., /home/.../repo/..., /usr/src/app/...
    for prefix in ["app/", "var/app/", "usr/src/app/", "workspace/", "project/"]:
        if path.startswith(prefix):
            path = path[len(prefix):]
            break

    return path.lstrip("/")


def _is_framework_frame(path: str) -> bool:
    norm = path.replace("\\", "/").lower()
    return any(marker in norm for marker in IGNORED_FRAME_MARKERS)


def parse_stack_trace(
    stack_trace: str,
    repo_files: Optional[List[str]] = None,
) -> Optional[GitHubSourceLocation]:
    '''
    Parse a Python or JavaScript/TypeScript stack trace.
    Returns the most specific/deepest application source location.
    If no application frame can be identified, returns None.
    '''
    if not stack_trace or not isinstance(stack_trace, str) or len(stack_trace.strip()) < 5:
        return None

    frames: List[Dict[str, Any]] = []

    # 1. Check Python frames
    for match in PYTHON_FRAME_RE.finditer(stack_trace):
        raw_file = match.group("file")
        raw_line = match.group("line")
        func = match.group("func")
        if raw_file and raw_line:
            try:
                line_no = int(raw_line)
                frames.append({
                    "raw_file": raw_file,
                    "line": line_no,
                    "col": None,
                    "func": func.strip() if func else None,
                })
            except ValueError:
                continue

    # 2. Check JS/TS frames if no Python frames found
    if not frames:
        for match in JS_FRAME_WITH_COL_RE.finditer(stack_trace):
            raw_file = match.group("file")
            raw_line = match.group("line")
            col = match.group("col")
            func = match.group("func")
            if raw_file and raw_line:
                try:
                    frames.append({
                        "raw_file": raw_file,
                        "line": int(raw_line),
                        "col": int(col) if col else None,
                        "func": func.strip() if func else None,
                    })
                except ValueError:
                    continue

    if not frames:
        for match in JS_FRAME_NO_COL_RE.finditer(stack_trace):
            raw_file = match.group("file")
            raw_line = match.group("line")
            func = match.group("func")
            if raw_file and raw_line:
                try:
                    frames.append({
                        "raw_file": raw_file,
                        "line": int(raw_line),
                        "col": None,
                        "func": func.strip() if func else None,
                    })
                except ValueError:
                    continue

    if not frames:
        return None

    # Filter out framework frames if any application frame exists
    app_frames = [f for f in frames if not _is_framework_frame(f["raw_file"])]
    target_frame = app_frames[-1] if app_frames else frames[-1]

    norm_path = normalize_file_path(target_frame["raw_file"], repo_files=repo_files)
    if not norm_path:
        return None

    return GitHubSourceLocation(
        file_path=norm_path,
        line_number=target_frame["line"],
        column_number=target_frame["col"],
        function_name=target_frame["func"],
    )
