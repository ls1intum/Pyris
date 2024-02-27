from pydantic import BaseModel

from domain.status.stage_state_dto import StageStateDTO


class StageDTO(BaseModel):
    name: str
    weight: int
    state: StageStateDTO
    message: str
