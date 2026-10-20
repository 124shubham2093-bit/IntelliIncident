"""
GitHub Code Intelligence Service for IntelliIncident.
Provides normalized access to GitHub REST API for repository info,
recent commits, commit diffs, and source context for incident evidence correlation.
"""

import base64
from typing import List, Optional, Dict, Any, Tuple
import httpx

from backend.app.core.config import settings
from backend.app.schemas.github import (
    GitHubRateLimit,
    GitHubStatusResponse,
    GitHubRepository,
    GitHubCommitSummary,
    GitHubCommitDetail,
    GitHubCommitAuthor,
    GitHubChangedFile,
    GitHubFileContent,
    GitHubApplicationVerification,
    GitHubSourceLine,
    GitHubSourceLocation,
)

class GitHubError(Exception):
    """Base exception for GitHub API errors."""
    pass

class GitHubConfigError(GitHubError):
    """Raised when GitHub repository configuration is missing or invalid."""
    pass

class GitHubAuthError(GitHubError):
    """Raised when GitHub authentication fails (401)."""
    pass

class GitHubRateLimitError(GitHubError):
    """Raised when GitHub API rate limit is exceeded or access is forbidden (403)."""
    pass

class GitHubNotFoundError(GitHubError):
    """Raised when a repository, commit, or file is not found (404)."""
    pass

class GitHubUnavailableError(GitHubError):
    """Raised when GitHub API is unreachable, times out, or has server errors."""
    pass


class GitHubService:
    """
    Service client for interacting with the GitHub REST API.
    Normalizes responses into Pydantic models for safe consumption by IntelliIncident.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        default_branch: Optional[str] = None,
        api_url: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
        timeout: float = 3.0,
    ):
        self.token = token if token is not None else settings.GITHUB_TOKEN
        self.owner = owner if owner is not None else settings.GITHUB_REPO_OWNER
        self.repo = repo if repo is not None else settings.GITHUB_REPO_NAME
        self.default_branch = default_branch if default_branch is not None else settings.GITHUB_DEFAULT_BRANCH
        self.api_url = (api_url if api_url is not None else settings.GITHUB_API_URL).rstrip("/")
        self._client = client
        self.timeout = timeout

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "IntelliIncident-App",
        }
        if self.token and self.token.strip():
            headers["Authorization"] = f"Bearer {self.token.strip()}"
        return headers

    @staticmethod
    def _parse_rate_limit(headers: httpx.Headers) -> Optional[GitHubRateLimit]:
        limit = headers.get("x-ratelimit-limit")
        remaining = headers.get("x-ratelimit-remaining")
        reset_at = headers.get("x-ratelimit-reset")
        used = headers.get("x-ratelimit-used")
        if limit is not None and remaining is not None:
            try:
                lim_int = int(limit)
                rem_int = int(remaining)
                used_int = int(used) if used is not None else (lim_int - rem_int)
                return GitHubRateLimit(
                    limit=lim_int,
                    remaining=rem_int,
                    reset_at=int(reset_at) if reset_at else None,
                    used=used_int,
                )
            except (ValueError, TypeError):
                return None
        return None

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[httpx.Response, Any]:
        if not self.owner or not self.repo:
            raise GitHubConfigError("GitHub repository owner or name is not configured.")

        url = f"{self.api_url}{endpoint}"
        headers = self._get_headers()

        try:
            if self._client:
                resp = await self._client.request(
                    method, url, headers=headers, params=params, timeout=self.timeout
                )
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.request(
                        method, url, headers=headers, params=params
                    )
        except (httpx.ConnectError, httpx.NetworkError) as e:
            raise GitHubUnavailableError(f"Unable to connect to GitHub API: {str(e)}")
        except httpx.TimeoutException as e:
            raise GitHubUnavailableError(f"GitHub API request timed out after {self.timeout}s: {str(e)}")
        except httpx.RequestError as e:
            raise GitHubUnavailableError(f"GitHub API request error: {str(e)}")

        if resp.status_code == 401:
            raise GitHubAuthError("GitHub authentication failed. Token may be invalid or expired.")
        elif resp.status_code == 403:
            rl = self._parse_rate_limit(resp.headers)
            if rl and rl.remaining == 0:
                raise GitHubRateLimitError(f"GitHub API rate limit exceeded. Limit resets at {rl.reset_at}.")
            raise GitHubRateLimitError("GitHub API access forbidden or rate limit reached.")
        elif resp.status_code == 404:
            raise GitHubNotFoundError(f"GitHub resource not found at {endpoint}.")
        elif resp.status_code >= 500:
            raise GitHubUnavailableError(f"GitHub API remote server error: HTTP {resp.status_code}.")
        elif resp.status_code >= 400:
            raise GitHubError(f"GitHub API error: HTTP {resp.status_code}.")

        try:
            data = resp.json()
        except Exception as e:
            raise GitHubError(f"Malformed JSON in GitHub response: {str(e)}")

        return resp, data

    async def get_status(self) -> GitHubStatusResponse:
        """
        Verify configuration, reachability, and rate limit status of the GitHub integration.
        Does NOT raise exceptions for remote errors; returns structured status safely.
        Never returns or logs GITHUB_TOKEN.
        """
        is_configured = bool(self.owner and self.repo)
        has_token = bool(self.token and self.token.strip())

        if not is_configured:
            return GitHubStatusResponse(
                configured=False,
                authenticated=has_token,
                reachable=False,
                owner=self.owner or "",
                repo=self.repo or "",
                default_branch=self.default_branch,
                api_url=self.api_url,
                message="GitHub repository owner or name not configured.",
            )

        try:
            resp, data = await self._request("GET", f"/repos/{self.owner}/{self.repo}")
            rate_limit = self._parse_rate_limit(resp.headers)
            return GitHubStatusResponse(
                configured=True,
                authenticated=has_token,
                reachable=True,
                owner=self.owner,
                repo=self.repo,
                default_branch=data.get("default_branch", self.default_branch),
                api_url=self.api_url,
                rate_limit=rate_limit,
                message="GitHub integration operational and repository verified.",
            )
        except GitHubAuthError:
            return GitHubStatusResponse(
                configured=True,
                authenticated=False,
                reachable=True,
                owner=self.owner,
                repo=self.repo,
                default_branch=self.default_branch,
                api_url=self.api_url,
                message="GitHub authentication failed. Token is invalid or expired.",
            )
        except GitHubRateLimitError as e:
            return GitHubStatusResponse(
                configured=True,
                authenticated=has_token,
                reachable=True,
                owner=self.owner,
                repo=self.repo,
                default_branch=self.default_branch,
                api_url=self.api_url,
                message=str(e),
            )
        except GitHubNotFoundError:
            return GitHubStatusResponse(
                configured=True,
                authenticated=has_token,
                reachable=True,
                owner=self.owner,
                repo=self.repo,
                default_branch=self.default_branch,
                api_url=self.api_url,
                message=f"Repository {self.owner}/{self.repo} not found.",
            )
        except GitHubUnavailableError as e:
            return GitHubStatusResponse(
                configured=True,
                authenticated=has_token,
                reachable=False,
                owner=self.owner,
                repo=self.repo,
                default_branch=self.default_branch,
                api_url=self.api_url,
                message=f"GitHub API unreachable: {str(e)}",
            )
        except Exception as e:
            return GitHubStatusResponse(
                configured=True,
                authenticated=has_token,
                reachable=False,
                owner=self.owner,
                repo=self.repo,
                default_branch=self.default_branch,
                api_url=self.api_url,
                message=f"GitHub status check error: {str(e)}",
            )

    async def verify_connection(self, branch: Optional[str] = None) -> GitHubApplicationVerification:
        """
        Verify an application's GitHub repository connection.
        Verifies repository reachability, access permissions, and configured branch accessibility.
        Returns factual, structured status without raising exceptions.
        """
        target_branch = branch or self.default_branch or "main"
        if not self.owner or not self.repo:
            return GitHubApplicationVerification(
                connected=False,
                repository_accessible=False,
                branch_accessible=False,
                owner=self.owner or "",
                repo=self.repo or "",
                branch=target_branch,
                default_branch=self.default_branch,
                message="GitHub repository owner or name is not configured for this application.",
            )

        repo_accessible = False
        default_branch = self.default_branch
        rate_limit = None

        # 1. Verify Repository
        try:
            resp, data = await self._request("GET", f"/repos/{self.owner}/{self.repo}")
            rate_limit = self._parse_rate_limit(resp.headers)
            repo_accessible = True
            default_branch = data.get("default_branch", self.default_branch)
        except GitHubNotFoundError:
            return GitHubApplicationVerification(
                connected=False,
                repository_accessible=False,
                branch_accessible=False,
                owner=self.owner,
                repo=self.repo,
                branch=target_branch,
                default_branch=self.default_branch,
                message=f"Repository '{self.owner}/{self.repo}' not found or access denied.",
            )
        except GitHubAuthError:
            return GitHubApplicationVerification(
                connected=False,
                repository_accessible=False,
                branch_accessible=False,
                owner=self.owner,
                repo=self.repo,
                branch=target_branch,
                default_branch=self.default_branch,
                message="GitHub authentication failed. Token may be invalid or expired.",
            )
        except GitHubRateLimitError as e:
            return GitHubApplicationVerification(
                connected=False,
                repository_accessible=False,
                branch_accessible=False,
                owner=self.owner,
                repo=self.repo,
                branch=target_branch,
                default_branch=self.default_branch,
                message=str(e),
            )
        except GitHubUnavailableError as e:
            return GitHubApplicationVerification(
                connected=False,
                repository_accessible=False,
                branch_accessible=False,
                owner=self.owner,
                repo=self.repo,
                branch=target_branch,
                default_branch=self.default_branch,
                message=f"GitHub API unreachable: {str(e)}",
            )
        except Exception as e:
            return GitHubApplicationVerification(
                connected=False,
                repository_accessible=False,
                branch_accessible=False,
                owner=self.owner,
                repo=self.repo,
                branch=target_branch,
                default_branch=self.default_branch,
                message=f"Repository verification failed: {str(e)}",
            )

        # 2. Verify Branch
        try:
            b_resp, _ = await self._request("GET", f"/repos/{self.owner}/{self.repo}/branches/{target_branch}")
            rate_limit = self._parse_rate_limit(b_resp.headers) or rate_limit
            branch_accessible = True
        except GitHubNotFoundError:
            return GitHubApplicationVerification(
                connected=False,
                repository_accessible=True,
                branch_accessible=False,
                owner=self.owner,
                repo=self.repo,
                branch=target_branch,
                default_branch=default_branch,
                rate_limit=rate_limit,
                message=f"Repository '{self.owner}/{self.repo}' is accessible, but branch '{target_branch}' was not found.",
            )
        except Exception as e:
            return GitHubApplicationVerification(
                connected=False,
                repository_accessible=True,
                branch_accessible=False,
                owner=self.owner,
                repo=self.repo,
                branch=target_branch,
                default_branch=default_branch,
                rate_limit=rate_limit,
                message=f"Branch verification failed: {str(e)}",
            )

        return GitHubApplicationVerification(
            connected=True,
            repository_accessible=True,
            branch_accessible=True,
            owner=self.owner,
            repo=self.repo,
            branch=target_branch,
            default_branch=default_branch,
            rate_limit=rate_limit,
            message=f"GitHub repository '{self.owner}/{self.repo}' and branch '{target_branch}' verified successfully.",
        )

    async def get_repository(self) -> GitHubRepository:
        """Retrieve normalized repository details."""
        _, data = await self._request("GET", f"/repos/{self.owner}/{self.repo}")
        if not isinstance(data, dict):
            raise GitHubError("Unexpected response format for repository.")

        owner_login = data.get("owner", {}).get("login", self.owner) if isinstance(data.get("owner"), dict) else self.owner

        return GitHubRepository(
            full_name=data.get("full_name", f"{self.owner}/{self.repo}"),
            owner=owner_login,
            name=data.get("name", self.repo),
            description=data.get("description"),
            default_branch=data.get("default_branch", self.default_branch),
            is_private=bool(data.get("private", False)),
            html_url=data.get("html_url", f"https://github.com/{self.owner}/{self.repo}"),
            stars_count=data.get("stargazers_count", 0),
            forks_count=data.get("forks_count", 0),
            open_issues_count=data.get("open_issues_count", 0),
        )

    async def get_commits(
        self,
        limit: int = 30,
        ref: Optional[str] = None,
    ) -> List[GitHubCommitSummary]:
        """Retrieve normalized recent commits list, optionally filtered by branch/ref."""
        params: Dict[str, Any] = {"per_page": min(max(1, limit), 100)}
        if ref:
            params["sha"] = ref

        _, data = await self._request("GET", f"/repos/{self.owner}/{self.repo}/commits", params=params)
        if not isinstance(data, list):
            raise GitHubError("Unexpected response format for commits list.")

        summaries = []
        for item in data:
            if not isinstance(item, dict):
                continue
            sha = item.get("sha", "")
            commit_dict = item.get("commit", {}) if isinstance(item.get("commit"), dict) else {}
            author_dict = commit_dict.get("author", {}) if isinstance(commit_dict.get("author"), dict) else {}
            gh_author = item.get("author", {}) if isinstance(item.get("author"), dict) else {}

            author = GitHubCommitAuthor(
                name=author_dict.get("name"),
                email=author_dict.get("email"),
                date=author_dict.get("date"),
                username=gh_author.get("login") if gh_author else None,
                avatar_url=gh_author.get("avatar_url") if gh_author else None,
            )

            summaries.append(
                GitHubCommitSummary(
                    sha=sha,
                    short_sha=sha[:7] if sha else "",
                    message=commit_dict.get("message", ""),
                    author=author,
                    committed_at=author_dict.get("date"),
                    html_url=item.get("html_url", f"https://github.com/{self.owner}/{self.repo}/commit/{sha}"),
                )
            )
        return summaries

    async def get_commit(self, sha: str) -> GitHubCommitDetail:
        """Retrieve detailed information for a single commit, including file diffs."""
        if not sha:
            raise GitHubError("Commit SHA must be provided.")

        _, data = await self._request("GET", f"/repos/{self.owner}/{self.repo}/commits/{sha}")
        if not isinstance(data, dict):
            raise GitHubError("Unexpected response format for commit detail.")

        full_sha = data.get("sha", sha)
        commit_dict = data.get("commit", {}) if isinstance(data.get("commit"), dict) else {}
        author_dict = commit_dict.get("author", {}) if isinstance(commit_dict.get("author"), dict) else {}
        gh_author = data.get("author", {}) if isinstance(data.get("author"), dict) else {}

        author = GitHubCommitAuthor(
            name=author_dict.get("name"),
            email=author_dict.get("email"),
            date=author_dict.get("date"),
            username=gh_author.get("login") if gh_author else None,
            avatar_url=gh_author.get("avatar_url") if gh_author else None,
        )

        stats_dict = data.get("stats", {}) if isinstance(data.get("stats"), dict) else {}
        stats = {
            "total": stats_dict.get("total", 0),
            "additions": stats_dict.get("additions", 0),
            "deletions": stats_dict.get("deletions", 0),
        }

        files: List[GitHubChangedFile] = []
        raw_files = data.get("files", [])
        if isinstance(raw_files, list):
            for f in raw_files:
                if isinstance(f, dict):
                    files.append(
                        GitHubChangedFile(
                            filename=f.get("filename", ""),
                            status=f.get("status", "modified"),
                            additions=f.get("additions", 0),
                            deletions=f.get("deletions", 0),
                            changes=f.get("changes", 0),
                            blob_url=f.get("blob_url"),
                            raw_url=f.get("raw_url"),
                            patch=f.get("patch"),
                        )
                    )

        return GitHubCommitDetail(
            sha=full_sha,
            short_sha=full_sha[:7] if full_sha else "",
            message=commit_dict.get("message", ""),
            author=author,
            committed_at=author_dict.get("date"),
            html_url=data.get("html_url", f"https://github.com/{self.owner}/{self.repo}/commit/{full_sha}"),
            stats=stats,
            files=files,
        )

    async def get_file(self, path: str, ref: Optional[str] = None) -> GitHubFileContent:
        """
        Retrieve repository file contents at an optional commit ref/branch.
        Safely decodes base64-encoded UTF-8 file content. If binary, sets is_binary=True.
        """
        clean_path = path.strip().lstrip("/")
        if not clean_path:
            raise GitHubError("File path must not be empty.")

        params: Dict[str, Any] = {}
        if ref:
            params["ref"] = ref

        _, data = await self._request("GET", f"/repos/{self.owner}/{self.repo}/contents/{clean_path}", params=params)

        if isinstance(data, list):
            raise GitHubError(f"Path '{clean_path}' is a directory, not a file.")

        if not isinstance(data, dict):
            raise GitHubError("Unexpected response format for file content.")

        encoding = data.get("encoding")
        raw_content = data.get("content")
        decoded_content: Optional[str] = None
        is_binary = False

        if encoding == "base64" and raw_content:
            try:
                cleaned_b64 = raw_content.replace("\n", "").replace("\r", "").strip()
                decoded_bytes = base64.b64decode(cleaned_b64)
                try:
                    decoded_content = decoded_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    is_binary = True
                    decoded_content = None
            except Exception:
                decoded_content = None
        elif raw_content and not encoding:
            decoded_content = raw_content

        return GitHubFileContent(
            path=data.get("path", clean_path),
            name=data.get("name", clean_path.split("/")[-1]),
            size=data.get("size", 0),
            sha=data.get("sha", ""),
            html_url=data.get("html_url"),
            encoding=encoding,
            content=raw_content,
            decoded_content=decoded_content,
            is_binary=is_binary,
        )

    async def get_source_context(
        self,
        path: str,
        line: int,
        ref: Optional[str] = None,
        window: int = 5,
    ) -> Tuple[Optional[List[GitHubSourceLine]], Optional[str], str]:
        """
        Fetch file at path and ref (deployment commit SHA).
        Extract a surrounding window of lines around `line` (1-indexed).
        Returns (source_lines, raw_snippet, status).
        Possible statuses: "MATCHED", "FILE_NOT_FOUND", "GITHUB_UNAVAILABLE", "BINARY_FILE", "UNRESOLVED"
        """
        try:
            file_content = await self.get_file(path=path, ref=ref)
        except GitHubNotFoundError:
            return None, None, "FILE_NOT_FOUND"
        except (GitHubUnavailableError, GitHubAuthError, GitHubRateLimitError):
            return None, None, "GITHUB_UNAVAILABLE"
        except Exception:
            return None, None, "UNRESOLVED"

        if file_content.is_binary or not file_content.decoded_content:
            return None, None, "BINARY_FILE"

        lines = file_content.decoded_content.splitlines()
        total_lines = len(lines)
        if total_lines == 0:
            return [], "", "MATCHED"

        # 1-indexed target line clamped within bounds
        target_idx = max(1, min(line, total_lines))
        start_idx = max(1, target_idx - window)
        end_idx = min(total_lines, target_idx + window)

        source_lines: List[GitHubSourceLine] = []
        raw_parts: List[str] = []
        for i in range(start_idx, end_idx + 1):
            line_str = lines[i - 1]
            is_target = (i == target_idx)
            source_lines.append(
                GitHubSourceLine(
                    line_number=i,
                    content=line_str,
                    is_target=is_target,
                )
            )
            marker = ">" if is_target else " "
            raw_parts.append(f"{marker} {i:4d} | {line_str}")

        return source_lines, "\n".join(raw_parts), "MATCHED"
