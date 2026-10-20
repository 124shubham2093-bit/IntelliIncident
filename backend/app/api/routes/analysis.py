from fastapi import APIRouter, HTTPException

from backend.app.schemas.report import IncidentAnalysis
from backend.app.services.analysis_service import AnalysisService

router = APIRouter(tags=["Analysis"])
analysis_service = AnalysisService()

@router.post("/analyze/{incident_id}", response_model=IncidentAnalysis)
async def analyze_incident(incident_id: str):
    try:
        analysis = await analysis_service.analyze_incident(incident_id)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found for analysis")
    return analysis
