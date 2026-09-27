from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class GitHubRateLimit(BaseModel):
    limit: int = 60
    remaining: int = 60
    reset_at: Optional[int] = None
    used: int = 0

class GitHubStatusResponse(BaseModel):
    configured: bool
    authenticated: bool
    reachable: bool
    owner: str
    repo: str
    default_branch: str
    api_url: str
    rate_limit: Optional[GitHubRateLimit] = None
    message: Optional[str] = None

class GitHubRepository(BaseModel):
    full_name: str
    owner: str
    name: str
    description: Optional[str] = None
    default_branch: str = 'main'
    is_private: bool = False
    html_url: str
    stars_count: int = 0
    forks_count: int = 0
    open_issues_count: int = 0

class GitHubCommitAuthor(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    date: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None

class GitHubCommitSummary(BaseModel):
    sha: str
    short_sha: str
    message: str
    author: GitHubCommitAuthor
    committed_at: Optional[str] = None
    html_url: str

class GitHubChangedFile(BaseModel):
    filename: str
    status: str
    additions: int = 0
    deletions: int = 0
    changes: int = 0
    blob_url: Optional[str] = None
    raw_url: Optional[str] = None
    patch: Optional[str] = None

class GitHubCommitDetail(GitHubCommitSummary):
    stats: Dict[str, int] = Field(default_factory=lambda: {'total': 0, 'additions': 0, 'deletions': 0})
    files: List[GitHubChangedFile] = Field(default_factory=list)

class GitHubFileContent(BaseModel):
    path: str
    name: str
    size: int
    sha: str
    html_url: Optional[str] = None
    encoding: Optional[str] = None
    content: Optional[str] = None
    decoded_content: Optional[str] = None
    is_binary: bool = False
