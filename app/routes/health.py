from fastapi import APIRouter, Depends

from app.dependencies import PermissionsValidator
from app.models.dtos import LLMModel, LLMStatus, ModelStatus
from app.services.guidance_wrapper import GuidanceWrapper
from app.services.circuit_breaker import CircuitBreaker

router = APIRouter()


@router.get("/api/v1/health", dependencies=[Depends(PermissionsValidator())])
def checkhealth():
    result = []

    for model in LLMModel:
        circuit_status = CircuitBreaker.get_status(
            func=GuidanceWrapper(model=model).is_up,
            cache_key=model,
        )
        status = (
            LLMStatus.UP
            if circuit_status == CircuitBreaker.Status.CLOSED
            else LLMStatus.DOWN
        )
        result.append(ModelStatus(model=model, status=status))

    return result
