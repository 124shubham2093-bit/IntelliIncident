"""
GitHub Code Intelligence Routes for IntelliIncident.
Exposes endpoints for repository status, metadata, commit history, diffs, and source context.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.schemas.github import (
    GitHubStatusResponse,
    GitHubRepository,
    GitHubCommitSummary,
    GitHubCommitDetail,
    GitHubFileContent,
)
from backend.app.services.github_service import (
    GitHubService,
    GitHubError,
    GitHubConfigError,
    GitHubAuthError,
    GitHubRateLimitError,
    GitHubNotFoundError,
    GitHubUnavailableError,
)

router = APIRouter(prefix="/github", tags=["GitHub"])
github_service = GitHubService()


@router.get("/status", response_model=GitHubStatusResponse)
async def get_github_status():
    """
    Check configuration, API reachability, and rate limit status of the GitHub integration.
    Safe endpoint that never crashes and never exposes GITHUB_TOKEN.
    """
    try:
        return await github_service.get_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to check GitHub status: {str(e)}",
        )


@router.get("/repo", response_model=GitHubRepository)
async def get_repository_info():
    """
    Retrieve repository metadata (name, owner, default branch, visibility, stars, description).
    """
    try:
        return await github_service.get_repository()
    except GitHubAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except GitHubRateLimitError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except GitHubNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (GitHubConfigError, GitHubUnavailableError) as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except GitHubError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/commits", response_model=List[GitHubCommitSummary])
async def get_recent_commits(
    limit: int = Query(30, ge=1, le=100, description="Max number of commits to retrieve"),
    ref: Optional[str] = Query(None, description="Branch name or commit SHA to inspect"),
):
    """
    Retrieve recent commits list with normalized author, message, and timestamp metadata.
    """
    try:
        return await github_service.get_commits(limit=limit, ref=ref)
    except GitHubAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except GitHubRateLimitError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except GitHubNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (GitHubConfigError, GitHubUnavailableError) as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except GitHubError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/commits/{sha}", response_model=GitHubCommitDetail)
async def get_commit_detail(sha: str):
    """
    Retrieve detailed commit information, including changed files, additions, deletions, and patches.
    """
    try:
        return await github_service.get_commit(sha=sha)
    except GitHubAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except GitHubRateLimitError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except GitHubNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (GitHubConfigError, GitHubUnavailableError) as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except GitHubError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/files/{path:path}", response_model=GitHubFileContent)
async def get_file_content(
    path: str,
    ref: Optional[str] = Query(None, description="Optional commit SHA or branch ref to fetch file at"),
):
    """
    Retrieve repository file content at a specific path and revision.
    Safely returns decoded text for source context or flags binary files.
    """
    try:
        return await github_service.get_file(path=path, ref=ref)
    except GitHubAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except GitHubRateLimitError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except GitHubNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (GitHubConfigError, GitHubUnavailableError) as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except GitHubError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
