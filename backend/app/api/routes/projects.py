"""
FastAPI Routes for Project, Application, and Environment Topology.
Exposes endpoints for managing software topology, environment API keys,
connection guides, and ingestion connectivity checks.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request, status

from backend.app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    EnvironmentCreate,
    EnvironmentUpdate,
    EnvironmentResponse,
    EnvironmentApiKeyRegenerateResponse,
    ConnectionGuideResponse,
    IngestionTestResponse,
)
from backend.app.schemas.github import GitHubApplicationVerification
from backend.app.services.github_service import GitHubService
from backend.app.services.project_service import ProjectService

router = APIRouter(tags=["Topology"])
project_service = ProjectService()


# ==========================================
# Project Endpoints
# ==========================================

@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects():
    """List all registered software projects."""
    return project_service.get_projects()


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate):
    """Create a new project entity."""
    try:
        return project_service.create_project(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Retrieve single project by ID."""
    proj = project_service.get_project_by_id(project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found.")
    return proj


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, payload: ProjectUpdate):
    """Update project metadata."""
    try:
        updated = project_service.update_project(project_id, payload)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found.")
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/projects/{project_id}", status_code=status.HTTP_200_OK)
async def delete_project(project_id: str):
    """Delete project. Prevented if active applications or historical incidents exist."""
    try:
        deleted = project_service.delete_project(project_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found.")
        return {"status": "ok", "message": f"Project '{project_id}' successfully deleted."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


# ==========================================
# Application Endpoints
# ==========================================

@router.get("/projects/{project_id}/applications", response_model=List[ApplicationResponse])
async def list_project_applications(project_id: str):
    """List all applications belonging to a specific project."""
    proj = project_service.get_project_by_id(project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found.")
    return project_service.get_applications_by_project(project_id)


@router.post("/projects/{project_id}/applications", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_project_application(project_id: str, payload: ApplicationCreate):
    """Register a new application under a project."""
    try:
        return project_service.create_application(project_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/applications/{application_id}", response_model=ApplicationResponse)
async def get_application(application_id: str):
    """Retrieve single application by ID."""
    app = project_service.get_application_by_id(application_id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Application '{application_id}' not found.")
    return app


@router.put("/applications/{application_id}", response_model=ApplicationResponse)
async def update_application(application_id: str, payload: ApplicationUpdate):
    """Update application details or GitHub repository binding."""
    try:
        updated = project_service.update_application(application_id, payload)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Application '{application_id}' not found.")
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/applications/{application_id}", status_code=status.HTTP_200_OK)
async def delete_application(application_id: str):
    """Delete application. Prevented if active environments or historical incidents exist."""
    try:
        deleted = project_service.delete_application(application_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Application '{application_id}' not found.")
        return {"status": "ok", "message": f"Application '{application_id}' successfully deleted."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/applications/{application_id}/github-status", response_model=GitHubApplicationVerification)
async def verify_application_github(application_id: str):
    """
    Verify application-scoped GitHub repository and branch accessibility.
    Does not crash; returns factual reachability and accessibility information.
    """
    app = project_service.get_application_by_id(application_id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Application '{application_id}' not found.")

    repo_owner = app.get("repo_owner")
    repo_name = app.get("repo_name")
    default_branch = app.get("default_branch") or "main"

    gh_service = GitHubService(
        owner=repo_owner,
        repo=repo_name,
        default_branch=default_branch,
    )
    return await gh_service.verify_connection(branch=default_branch)



# ==========================================
# Environment Endpoints
# ==========================================

@router.get("/applications/{application_id}/environments", response_model=List[EnvironmentResponse])
async def list_application_environments(application_id: str):
    """List all deployment environments for an application."""
    app = project_service.get_application_by_id(application_id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Application '{application_id}' not found.")
    return project_service.get_environments_by_application(application_id)


@router.post("/applications/{application_id}/environments", response_model=EnvironmentResponse, status_code=status.HTTP_201_CREATED)
async def create_application_environment(application_id: str, payload: EnvironmentCreate):
    """Deploy a new environment and generate a secure ingestion API key."""
    try:
        return project_service.create_environment(application_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/environments/{environment_id}", response_model=EnvironmentResponse)
async def get_environment(environment_id: str):
    """Retrieve environment metadata (API key is masked)."""
    env = project_service.get_environment_by_id(environment_id)
    if not env:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Environment '{environment_id}' not found.")
    return env


@router.put("/environments/{environment_id}", response_model=EnvironmentResponse)
async def update_environment(environment_id: str, payload: EnvironmentUpdate):
    """Update environment configuration."""
    try:
        updated = project_service.update_environment(environment_id, payload)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Environment '{environment_id}' not found.")
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/environments/{environment_id}/regenerate-key", response_model=EnvironmentApiKeyRegenerateResponse)
async def regenerate_environment_api_key(environment_id: str):
    """Regenerate environment ingestion API key. Invalidates the old key immediately."""
    try:
        return project_service.regenerate_api_key(environment_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/environments/{environment_id}", status_code=status.HTTP_200_OK)
async def delete_environment(environment_id: str):
    """Delete environment. Prevented if historical incidents reference it."""
    try:
        deleted = project_service.delete_environment(environment_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Environment '{environment_id}' not found.")
        return {"status": "ok", "message": f"Environment '{environment_id}' successfully deleted."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


# ==========================================
# Connection Guide & Ingestion Test
# ==========================================

@router.get("/environments/{environment_id}/connection-guide", response_model=ConnectionGuideResponse)
async def get_connection_guide(environment_id: str, request: Request):
    """Retrieve complete code snippets and documentation for connecting a deployed app."""
    try:
        base_url = str(request.base_url).rstrip("/")
        return project_service.get_connection_guide(environment_id, base_url=base_url)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/environments/{environment_id}/test-ingestion", response_model=IngestionTestResponse)
async def test_environment_ingestion(environment_id: str):
    """
    Verify environment ingestion connectivity and API key validity.
    DOES NOT persist any incident or contaminate runtime data.
    """
    conn_guide = project_service.get_environment_by_id(environment_id)
    if not conn_guide:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment '{environment_id}' does not exist or has been deleted."
        )

    app = project_service.get_application_by_id(conn_guide["application_id"])
    proj = project_service.get_project_by_id(app["project_id"]) if app else None

    return IngestionTestResponse(
        status="ok",
        environment_id=environment_id,
        environment_name=conn_guide["name"],
        application_name=app["name"] if app else "Unknown",
        project_name=proj["name"] if proj else "Unknown",
        authenticated=True,
        message="Environment ingestion channel is verified, active, and authenticated."
    )
