from enum import Enum
from typing import List

from pydantic import BaseModel


class StateDTO(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


class StageDTO(BaseModel):
    name: str
    weight: int
    state: StateDTO
    message: str


class ExerciseTutorChatStatusDTO(BaseModel):
    stages: List[StageDTO]
    result: str

    def __init__(self, stages: List[StageDTO], result: str):
        super().__init__(stages=stages, result=result)
        self.stages = stages
        self.result = result
