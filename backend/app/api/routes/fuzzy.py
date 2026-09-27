from fastapi import APIRouter

from backend.app.schemas.fuzzy import FuzzyInputValues, FuzzyRiskResult
from backend.app.fuzzy.fuzzy_engine import FuzzyRiskEngine

router = APIRouter(tags=["Fuzzy Risk"])
fuzzy_engine = FuzzyRiskEngine()

@router.post("/fuzzy-risk", response_model=FuzzyRiskResult)
async def evaluate_fuzzy_risk(inputs: FuzzyInputValues):
    result = fuzzy_engine.evaluate(inputs.model_dump())
    return result
