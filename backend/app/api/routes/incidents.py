from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from backend.app.schemas.incident import Incident, IncidentDetails
from backend.app.services.incident_service import IncidentService

router = APIRouter(tags=["Incidents"])
incident_service = IncidentService()

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

@router.get("/incidents/{incident_id}", response_model=IncidentDetails)
async def get_incident(incident_id: str):
    try:
        incident = incident_service.get_incident_details(incident_id)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return incident
