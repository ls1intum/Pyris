import logging

from fastapi import APIRouter, status, Response
from app.domain.dtos import (
    PipelineExecutionDTO,
    ExerciseExecutionDTOWrapper,
)
from app.pipeline.chat.tutor_chat_pipeline import TutorChatPipeline

router = APIRouter(prefix="/api/v1/pipelines", tags=["pipelines"])
logger = logging.getLogger(__name__)


@router.post("/{feature}/{variant}/run")
def run_pipeline(feature: str, variant: int, dto: PipelineExecutionDTO):
    match feature:
        case "tutor-chat":
            wrapper = ExerciseExecutionDTOWrapper(dto=dto)
            pipeline = TutorChatPipeline()
            pipeline2 = TutorChatPipeline()
            logger.info(
                f"Singleton check: pipeline is pipeline2 - {pipeline is pipeline2}"
            )
            response = pipeline(wrapper=wrapper)
            return response
        case _:
            return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.get("/{feature}")
def get_pipeline(feature: str):
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)
