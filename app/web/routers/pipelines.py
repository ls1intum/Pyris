import logging
import traceback
from threading import Thread

from sentry_sdk import capture_exception

from fastapi import APIRouter, status, Response, Depends, Body, Query

from app.domain import (
    ExerciseChatPipelineExecutionDTO,
    CourseChatPipelineExecutionDTO,
    CompetencyExtractionPipelineExecutionDTO,
)
from app.pipeline.chat.exercise_chat_agent_pipeline import ExerciseChatAgentPipeline
from app.web.status.status_update import (
    ExerciseChatStatusCallback,
    CourseChatStatusCallback,
    CompetencyExtractionCallback,
)
from app.pipeline.chat.course_chat_pipeline import CourseChatPipeline
from app.dependencies import TokenValidator
from app.pipeline.competency_extraction_pipeline import CompetencyExtractionPipeline

router = APIRouter(prefix="/api/v1/pipelines", tags=["pipelines"])
logger = logging.getLogger(__name__)


def run_exercise_chat_pipeline_worker(
    dto: ExerciseChatPipelineExecutionDTO, variant: str, event: str | None = None
):
    try:
        callback = ExerciseChatStatusCallback(
            run_id=dto.settings.authentication_token,
            base_url=dto.settings.artemis_base_url,
            initial_stages=dto.initial_stages,
        )
        pipeline = ExerciseChatAgentPipeline(
            callback=callback, variant=variant, event=event
        )
    except Exception as e:
        logger.error(f"Error preparing exercise chat pipeline: {e}")
        logger.error(traceback.format_exc())
        capture_exception(e)
        return

    try:
        pipeline(dto=dto)
    except Exception as e:
        logger.error(f"Error running exercise chat pipeline: {e}")
        logger.error(traceback.format_exc())
        callback.error("Fatal error.", exception=e)


@router.post(
    "/tutor-chat/{variant}/run",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(TokenValidator())],
)
def run_exercise_chat_pipeline(
    variant: str,
    event: str | None = Query(None, description="Event query parameter"),
    dto: ExerciseChatPipelineExecutionDTO = Body(
        description="Exercise Chat Pipeline Execution DTO"
    ),
):
    thread = Thread(
        target=run_exercise_chat_pipeline_worker, args=(dto, variant, event)
    )
    thread.start()


def run_course_chat_pipeline_worker(dto, variant, event):
    try:
        callback = CourseChatStatusCallback(
            run_id=dto.settings.authentication_token,
            base_url=dto.settings.artemis_base_url,
            initial_stages=dto.initial_stages,
        )
        pipeline = CourseChatPipeline(callback=callback, variant=variant, event=event)
    except Exception as e:
        logger.error(f"Error preparing exercise chat pipeline: {e}")
        logger.error(traceback.format_exc())
        capture_exception(e)
        return

    try:
        pipeline(dto=dto)
    except Exception as e:
        logger.error(f"Error running exercise chat pipeline: {e}")
        logger.error(traceback.format_exc())
        callback.error("Fatal error.", exception=e)


@router.post(
    "/course-chat/{variant}/run",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(TokenValidator())],
)
def run_course_chat_pipeline(
    variant: str,
    event: str | None = Query(None, description="Event query parameter"),
    dto: CourseChatPipelineExecutionDTO = Body(
        description="Course Chat Pipeline Execution DTO"
    ),
):
    thread = Thread(target=run_course_chat_pipeline_worker, args=(dto, variant, event))
    thread.start()


def run_competency_extraction_pipeline_worker(
    dto: CompetencyExtractionPipelineExecutionDTO, _variant: str
):
    try:
        callback = CompetencyExtractionCallback(
            run_id=dto.execution.settings.authentication_token,
            base_url=dto.execution.settings.artemis_base_url,
            initial_stages=dto.execution.initial_stages,
        )
        pipeline = CompetencyExtractionPipeline(callback=callback)
    except Exception as e:
        logger.error(f"Error preparing competency extraction pipeline: {e}")
        logger.error(traceback.format_exc())
        capture_exception(e)
        return

    try:
        pipeline(dto=dto)
    except Exception as e:
        logger.error(f"Error running competency extraction pipeline: {e}")
        logger.error(traceback.format_exc())
        callback.error("Fatal error.", exception=e)


@router.post(
    "/competency-extraction/{variant}/run",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(TokenValidator())],
)
def run_competency_extraction_pipeline(
    variant: str, dto: CompetencyExtractionPipelineExecutionDTO
):
    thread = Thread(
        target=run_competency_extraction_pipeline_worker, args=(dto, variant)
    )
    thread.start()


@router.get("/{feature}")
def get_pipeline(feature: str):
    """
    Get the pipeline for the given feature.
    """
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)
