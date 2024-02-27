from typing import List

from pydantic import BaseModel, Field

from domain.data.course_dto import CourseDTO
from domain.data.message_dto import MessageDTO
from domain.data.programming_exercise_dto import ProgrammingExerciseDTO
from domain.data.user_dto import UserDTO
from domain.data.submission_dto import SubmissionDTO


class TutorChatPipelineExecutionDTO(BaseModel):
    latest_submission: SubmissionDTO = Field(alias="latestSubmission")
    exercise: ProgrammingExerciseDTO
    course: CourseDTO
    chat_history: List[MessageDTO] = Field(alias="chatHistory")
    user: UserDTO
