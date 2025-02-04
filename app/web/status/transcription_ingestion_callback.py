from typing import List

from .status_update import StatusCallback
from ...domain.ingestion.ingestion_status_update_dto import IngestionStatusUpdateDTO
from ...domain.status.stage_state_dto import StageStateEnum
from ...domain.status.stage_dto import StageDTO
import logging

logger = logging.getLogger(__name__)


class TranscriptionIngestionStatus(StatusCallback):
    """
    Callback class for updating the status of a Lecture Transcription ingestion Pipeline run.
    """

    def __init__(
        self,
        run_id: str,
        base_url: str,
        initial_stages: List[StageDTO] = None,
        lecture_id: int = None,
    ):
        url = f"{base_url}/api/public/pyris/webhooks/ingestion/transcriptions/runs/{run_id}/status"

        current_stage_index = len(initial_stages) if initial_stages else 0
        stages = initial_stages or []
        stages += [
            StageDTO(
                weight=10,
                state=StageStateEnum.NOT_STARTED,
                name="Remove old transcription",
            ),
            StageDTO(
                weight=20,
                state=StageStateEnum.NOT_STARTED,
                name="Chunk transcription",
            ),
            StageDTO(
                weight=50,
                state=StageStateEnum.NOT_STARTED,
                name="Summarize transcription",
            ),
            StageDTO(
                weight=20,
                state=StageStateEnum.NOT_STARTED,
                name="Ingest transcription",
            ),
        ]
        status = IngestionStatusUpdateDTO(stages=stages, id=lecture_id)
        stage = stages[current_stage_index]
        super().__init__(url, run_id, status, stage, current_stage_index)
