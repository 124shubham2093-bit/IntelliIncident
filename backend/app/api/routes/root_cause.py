from typing import List
from fastapi import APIRouter, HTTPException

from backend.app.schemas.root_cause import RootCauseCandidate
from backend.app.services.incident_service import IncidentService

router = APIRouter(tags=["Root Cause Analysis"])
incident_service = IncidentService()

@router.get("/root-cause/{incident_id}", response_model=List[RootCauseCandidate])
async def get_root_cause(incident_id: str):
    details = await incident_service.get_incident_details(incident_id)
    if not details:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return details["rootCauseCandidates"]
