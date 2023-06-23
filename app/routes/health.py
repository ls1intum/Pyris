from fastapi import APIRouter, Depends

from app.dependencies import PermissionsValidator
from app.models.dtos import LLMModel, LLMStatus, ModelStatus

router = APIRouter()


@router.get("/api/v1/health", dependencies=[Depends(PermissionsValidator())])
def check_health():
    result = []
    for model in LLMModel:
        result.append(ModelStatus(model=model, status=LLMStatus.UP))

    return result
