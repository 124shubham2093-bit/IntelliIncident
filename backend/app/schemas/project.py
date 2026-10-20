"""
Pydantic Schemas for Project, Application, and Environment Topology Foundation.
Defines domain data transfer objects for project hierarchy, API key management,
and telemetry connection guides.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ==========================================
# Project Schemas
# ==========================================

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    slug: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    slug: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    application_count: int = 0
    created_at: str
    updated_at: str


# ==========================================
# Application Schemas
# ==========================================

class ApplicationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    slug: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = None
    language: str = Field(..., min_length=1, max_length=50)  # e.g., "python", "typescript", "go", "java"
    framework: Optional[str] = None  # e.g., "fastapi", "react", "express", "spring"
    repo_owner: Optional[str] = None
    repo_name: Optional[str] = None
    default_branch: str = "main"


class ApplicationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    slug: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = None
    language: Optional[str] = None
    framework: Optional[str] = None
    repo_owner: Optional[str] = None
    repo_name: Optional[str] = None
    default_branch: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: str
    project_id: str
    name: str
    slug: str
    description: Optional[str] = None
    language: str
    framework: Optional[str] = None
    repo_owner: Optional[str] = None
    repo_name: Optional[str] = None
    default_branch: str = "main"
    environment_count: int = 0
    created_at: str
    updated_at: str


# ==========================================
# Environment Schemas
# ==========================================

class EnvironmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)  # e.g., "production", "staging", "canary"
    slug: Optional[str] = Field(None, min_length=1, max_length=80)
    endpoint_url: Optional[str] = None
    current_commit: Optional[str] = None
    is_production: bool = False


class EnvironmentUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    endpoint_url: Optional[str] = None
    current_commit: Optional[str] = None
    is_production: Optional[bool] = None


class EnvironmentResponse(BaseModel):
    id: str
    application_id: str
    name: str
    slug: str
    api_key_preview: str  # Masked e.g. "ii_live_...a8f2"
    api_key: Optional[str] = None  # Populated only on create or regenerate
    endpoint_url: Optional[str] = None
    current_commit: Optional[str] = None
    is_production: bool = False
    created_at: str
    updated_at: str


class EnvironmentApiKeyRegenerateResponse(BaseModel):
    id: str
    api_key: str
    api_key_preview: str
    message: str = "Store this key securely. It will not be fully displayed again."


# ==========================================
# Connection Guide Schemas
# ==========================================

class ConnectionSnippet(BaseModel):
    language: str
    title: str
    code: str


class ConnectionGuideResponse(BaseModel):
    environment_id: str
    environment_name: str
    application_id: str
    application_name: str
    project_id: str
    project_name: str
    ingestion_endpoint: str
    api_key_preview: str
    curl_snippet: str
    python_snippet: str
    node_snippet: str
    github_actions_snippet: str
    explanation: str


class IngestionTestResponse(BaseModel):
    status: str  # "ok"
    environment_id: str
    environment_name: str
    application_name: str
    project_name: str
    authenticated: bool
    message: str
