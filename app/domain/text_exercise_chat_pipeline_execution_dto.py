from pydantic import BaseModel, Field

from domain import PipelineExecutionDTO
from domain.data.text_exercise_dto import TextExerciseDTO


class TextExerciseChatPipelineExecutionDTO(BaseModel):
    execution: PipelineExecutionDTO
    exercise: TextExerciseDTO
    current_answer: str = Field(alias="currentAnswer")
