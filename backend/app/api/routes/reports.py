import datetime
from fastapi import APIRouter, HTTPException

from backend.app.schemas.report import IncidentReportResponse
from backend.app.services.incident_service import IncidentService

router = APIRouter(tags=["Reports"])
incident_service = IncidentService()

@router.get("/reports/{incident_id}", response_model=IncidentReportResponse)
async def get_incident_report(incident_id: str):
    incident = incident_service.get_incident_details(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    report_id = f"REP-{incident_id}-{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}"
    summary_title = f"Root Cause Analysis & Incident Post-Mortem: {incident['title']}"

    return {
        "incident": incident,
        "generatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "reportId": report_id,
        "summaryTitle": summary_title,
    }
