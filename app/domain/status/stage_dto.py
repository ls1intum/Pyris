from typing import Literal

from pydantic import BaseModel

from app.domain.status.stage_state_dto import StageStateDTO


class StageDTO(BaseModel):
    name: str | None = None
    weight: int
    state: Literal[
        StageStateDTO.NOT_STARTED,
        StageStateDTO.IN_PROGRESS,
        StageStateDTO.DONE,
        StageStateDTO.SKIPPED,
        StageStateDTO.ERROR,
    ]
    message: str | None = None
