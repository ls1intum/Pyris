import logging
from datetime import datetime
from typing import Optional

from app.llm import CapabilityRequestHandler, RequirementList, CompletionArguments
from app.pipeline import Pipeline
from app.domain import PyrisMessage, IrisMessageRole
from app.domain.text_exercise_chat_pipeline_execution_dto import (
    TextExerciseChatPipelineExecutionDTO,
)
from app.pipeline.prompts.text_exercise_chat_prompts import (
    fmt_system_prompt,
    fmt_rejection_prompt,
    fmt_guard_prompt,
)
from app.web.status.status_update import TextExerciseChatCallback

logger = logging.getLogger(__name__)


class TextExerciseChatPipeline(Pipeline):
    callback: TextExerciseChatCallback
    request_handler: CapabilityRequestHandler

    def __init__(self, callback: Optional[TextExerciseChatCallback] = None):
        super().__init__(implementation_id="text_exercise_chat_pipeline_reference_impl")
        self.callback = callback
        self.request_handler = CapabilityRequestHandler(
            requirements=RequirementList(context_length=8000)
        )

    def __call__(
        self,
        dto: TextExerciseChatPipelineExecutionDTO,
        **kwargs,
    ):
        if not dto.exercise:
            raise ValueError("Exercise is required")

        should_respond = self.guard(dto)
        self.callback.done("Responding" if should_respond else "Rejecting")

        if should_respond:
            response = self.respond(dto)
        else:
            response = self.reject(dto)

        self.callback.done(final_result=response)

    def guard(self, dto: TextExerciseChatPipelineExecutionDTO) -> bool:
        guard_prompt = fmt_guard_prompt(
            exercise_name=dto.exercise.title,
            course_name=dto.exercise.course.name,
            course_description=dto.exercise.course.description,
            problem_statement=dto.exercise.problem_statement,
            user_input=dto.current_submission,
        )
        guard_prompt = PyrisMessage(
            sender=IrisMessageRole.SYSTEM,
            contents=[{"text_content": guard_prompt}],
        )
        response = self.request_handler.chat([guard_prompt], CompletionArguments())
        response = response.contents[0].text_content
        return "yes" in response.lower()

    def respond(self, dto: TextExerciseChatPipelineExecutionDTO) -> str:
        system_prompt = fmt_system_prompt(
            exercise_name=dto.exercise.title,
            course_name=dto.exercise.course.name,
            course_description=dto.exercise.course.description,
            problem_statement=dto.exercise.problem_statement,
            start_date=str(dto.exercise.start_date),
            end_date=str(dto.exercise.end_date),
            current_date=str(datetime.now()),
            current_submission=dto.current_submission,
        )
        system_prompt = PyrisMessage(
            sender=IrisMessageRole.SYSTEM,
            contents=[{"text_content": system_prompt}],
        )
        prompts = [system_prompt] + dto.conversation

        response = self.request_handler.chat(
            prompts, CompletionArguments(temperature=0.4)
        )
        return response.contents[0].text_content

    def reject(self, dto: TextExerciseChatPipelineExecutionDTO) -> str:
        rejection_prompt = fmt_rejection_prompt(
            exercise_name=dto.exercise.title,
            course_name=dto.exercise.course.name,
            course_description=dto.exercise.course.description,
            problem_statement=dto.exercise.problem_statement,
            user_input=dto.current_submission,
        )
        rejection_prompt = PyrisMessage(
            sender=IrisMessageRole.SYSTEM,
            contents=[{"text_content": rejection_prompt}],
        )
        response = self.request_handler.chat(
            [rejection_prompt], CompletionArguments(temperature=0.4)
        )
        return response.contents[0].text_content
