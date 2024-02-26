from typing import List, Any, Optional

from pydantic import BaseModel, field_validator, Field

from ..domain import (
    Course,
    ProgrammingExercise,
    IrisMessage,
    ProgrammingSubmission,
)


class SettingsDTO(BaseModel):
    allowedModels: list[str]

    def __str__(self):
        return f"SettingsDTO(allowedModels={self.allowedModels})"


class PipelineExecutionDTO(BaseModel):
    settings: SettingsDTO
    question: Optional[IrisMessage] = None
    chat_history: Optional[List[IrisMessage]] = Field(alias="chatHistory")
    course: Optional[Course] = None
    exercise: Optional[ProgrammingExercise] = None
    latest_submission: Optional[ProgrammingSubmission] = Field(alias="latestSubmission")


class BaseChatPipelineExecutionDTO(PipelineExecutionDTO):
    question: IrisMessage
    chat_history: List[IrisMessage] = Field(alias="chatHistory")


class ExercisePipelineExecutionDTO(BaseChatPipelineExecutionDTO):
    course: Course
    latest_submission: ProgrammingSubmission = Field(alias="latestSubmission")
    exercise: ProgrammingExercise


class ExerciseExecutionDTOWrapper(BaseModel):
    """Workaround to allow pydantic to validate the type of the DTO."""

    dto: Any

    @classmethod
    @field_validator("dto")
    def validate_dto(cls, value):
        if issubclass(type(value), PipelineExecutionDTO):
            return value
        raise TypeError(
            "Wrong type for 'dto', must be subclass of PipelineExecutionDTO"
        )

    def __str__(self):
        return f"ExecutionDTOWrapper(execution={self.execution})"
