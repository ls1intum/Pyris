from typing import List, Type, Any, Optional

from pydantic import BaseModel, field_validator, ConfigDict

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
    chat_history: Optional[List[IrisMessage]] = None
    course: Optional[Course] = None
    exercise: Optional[ProgrammingExercise] = None
    latest_submission: Optional[ProgrammingSubmission] = None


class BaseChatPipelineExecutionDTO(PipelineExecutionDTO):
    question: IrisMessage
    chat_history: List[IrisMessage]


class ExercisePipelineExecutionDTO(BaseChatPipelineExecutionDTO):
    course: Course
    latest_submission: ProgrammingSubmission
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
