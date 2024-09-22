from pydantic import BaseModel, Field

from domain import PipelineExecutionDTO, PyrisMessage
from domain.data.text_exercise_dto import TextExerciseDTO


class TextExerciseChatPipelineExecutionDTO(BaseModel):
    execution: PipelineExecutionDTO
    exercise: TextExerciseDTO
    conversation: list[PyrisMessage] = Field(default=[])
    current_submission: str = Field(alias="currentSubmission", default="")
