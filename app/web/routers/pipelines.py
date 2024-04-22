import logging
import traceback
from threading import Thread

from fastapi import APIRouter, status, Response, Depends
from app.domain import (
    TutorChatPipelineExecutionDTO,
    CompetencyExtractionPipelineExecutionDTO,
)
from app.pipeline.chat.tutor_chat_pipeline import TutorChatPipeline
from app.web.status.status_update import (
    TutorChatStatusCallback,
    CompetencyExtractionStatusCallback,
)
from app.dependencies import TokenValidator
from app.pipeline.chat.competency_extraction_pipeline import (
    CompetencyExtractionPipeline,
)

router = APIRouter(prefix="/api/v1/pipelines", tags=["pipelines"])
logger = logging.getLogger(__name__)


def run_tutor_chat_pipeline_worker(dto):
    try:
        callback = TutorChatStatusCallback(
            run_id=dto.settings.authentication_token,
            base_url=dto.settings.artemis_base_url,
            initial_stages=dto.initial_stages,
        )
        pipeline = TutorChatPipeline(callback=callback)
        pipeline(dto=dto)
    except Exception as e:
        logger.error(f"Error running tutor chat pipeline: {e}")
        logger.error(traceback.format_exc())


def run_competency_extraction_pipeline_worker(dto):
    try:
        callback = CompetencyExtractionStatusCallback(
            run_id=dto.settings.authentication_token,
            base_url=dto.settings.artemis_base_url,
            initial_stages=dto.initial_stages,
        )
        pipeline = CompetencyExtractionPipeline(callback=callback)
        pipeline(dto=dto)
    except Exception as e:
        logger.error(f"Error running competency extraction pipeline: {e}")
        logger.error(traceback.format_exc())


@router.post(
    "/tutor-chat/{variant}/run",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(TokenValidator())],
)
def run_tutor_chat_pipeline(variant: str, dto: TutorChatPipelineExecutionDTO):
    thread = Thread(target=run_tutor_chat_pipeline_worker, args=(dto,))
    thread.start()


@router.post(
    "/competency-extraction/{variant}/run",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(TokenValidator())],
)
def run_competency_extraction_pipeline(
    variant: str, dto: CompetencyExtractionPipelineExecutionDTO
):
    thread = Thread(target=run_competency_extraction_pipeline_worker, args=(dto,))
    thread.start()


@router.get("/{feature}")
def get_pipeline(feature: str):
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)
