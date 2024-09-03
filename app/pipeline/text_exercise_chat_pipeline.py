import logging
from datetime import datetime
from typing import Optional

from app.llm import CapabilityRequestHandler, RequirementList, CompletionArguments
from app.pipeline import Pipeline
from domain import PyrisMessage, IrisMessageRole
from domain.data.text_message_content_dto import TextMessageContentDTO
from domain.text_exercise_chat_pipeline_execution_dto import (
    TextExerciseChatPipelineExecutionDTO,
)
from pipeline.prompts.text_exercise_chat_prompts import system_prompt
from web.status.status_update import TextExerciseChatCallback

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

        prompt = system_prompt(
            exercise_name=dto.exercise.name,
            course_name=dto.exercise.course.name,
            course_description=dto.exercise.course.description,
            problem_statement=dto.exercise.problem_statement,
            start_date=str(dto.exercise.start_date),
            end_date=str(dto.exercise.end_date),
            current_date=str(datetime.now()),
            current_answer=dto.current_answer,
        )
        prompt = PyrisMessage(
            sender=IrisMessageRole.SYSTEM,
            contents=[TextMessageContentDTO(text_content=prompt)],
        )

        # done building prompt

        response = self.request_handler.chat(
            [prompt], CompletionArguments(temperature=0.4)
        )
        response = response.contents[0].text_content

        self.callback.done(response)
