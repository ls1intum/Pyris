import logging

from fastapi import APIRouter, status, Response
from app.domain import (
    TutorChatPipelineExecutionDTO,
)
from app.pipeline.chat.tutor_chat_pipeline import TutorChatPipeline
from app.web.status.status_update import TutorChatStatusCallback

router = APIRouter(prefix="/api/v1/pipelines", tags=["pipelines"])
logger = logging.getLogger(__name__)


@router.post("/tutor-chat/{variant}/run", status_code=status.HTTP_202_ACCEPTED)
def run_pipeline(variant: str, dto: TutorChatPipelineExecutionDTO):
    callback = TutorChatStatusCallback(
        run_id=dto.settings.authentication_token, base_url=dto.settings.artemis_base_url
    )
    pipeline = TutorChatPipeline(callback=callback)
    pipeline(dto=dto)


@router.get("/{feature}")
def get_pipeline(feature: str):
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)
