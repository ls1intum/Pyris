from fastapi import APIRouter, Depends

from app.dependencies import TokenValidator
from config import settings, APIKeyConfig
from models.dtos import LLMModelResponse

router = APIRouter(tags=["models"])


@router.get(
    "/api/v1/models", dependencies=[Depends(TokenValidator())]
)
def send_message(api_key_config: APIKeyConfig = Depends(TokenValidator())) -> list[LLMModelResponse]:
    llm_ids = api_key_config.llm_access

    # Convert the result of this to a list of LLMModelResponse
    return [LLMModelResponse(id=key, name=config.name, description=config.description) for key, config in
            settings.pyris.llms.items() if key in llm_ids]
