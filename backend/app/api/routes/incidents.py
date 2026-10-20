from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Header, status

from backend.app.schemas.incident import Incident, IncidentDetails, IncidentCreatePayload
from backend.app.services.incident_service import IncidentService
from backend.app.services.project_service import ProjectService

router = APIRouter(tags=["Incidents"])
incident_service = IncidentService()
project_service = ProjectService()

@router.get("/incidents", response_model=List[Incident])
async def list_incidents(
    search: Optional[str] = Query(None, description="Search term in id, title, service, summary"),
    severity: Optional[str] = Query(None, description="Filter by severity: LOW, MEDIUM, HIGH, CRITICAL"),
    risk: Optional[str] = Query(None, description="Filter by risk: LOW, MEDIUM, HIGH, CRITICAL, VERY_HIGH"),
    service: Optional[str] = Query(None, description="Filter by microservice name"),
    status: Optional[str] = Query(None, description="Filter by status: OPEN, INVESTIGATING, MITIGATED, RESOLVED"),
):
    return incident_service.get_incidents(
        search=search,
        severity=severity,
        risk=risk,
        service=service,
        status=status,
    )

@router.post("/incidents", response_model=IncidentDetails, status_code=status.HTTP_201_CREATED)
async def create_incident(
    payload: IncidentCreatePayload,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    try:
        # Validate ingestion API key when provided by external deployed services
        if x_api_key:
            env_record = project_service.get_environment_by_api_key(x_api_key)
            if not env_record:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid X-API-Key: authentication failed for environment ingestion.",
                )
            # Bind authenticated environment, application, and project
            payload.environment_id = env_record["id"]
            payload.application_id = env_record["application_id"]
            payload.project_id = env_record["project_id"]
            payload.environmentId = env_record["id"]
            payload.applicationId = env_record["application_id"]
            payload.projectId = env_record["project_id"]
            if not payload.environment:
                payload.environment = env_record.get("name") or "production"
            if not payload.commit_sha and not payload.commitSha and env_record.get("current_commit"):
                payload.commit_sha = env_record["current_commit"]

        created = await incident_service.create_incident(payload)
        return created
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to ingest incident: {str(e)}")

@router.get("/incidents/{incident_id}", response_model=IncidentDetails)
async def get_incident(incident_id: str):
    try:
        incident = await incident_service.get_incident_details(incident_id)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return incident
