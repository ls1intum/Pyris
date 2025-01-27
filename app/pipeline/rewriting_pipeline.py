import logging
from typing import Literal, Optional

from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
)

from app.common.PipelineEnum import PipelineEnum
from app.common.pyris_message import PyrisMessage, IrisMessageRole
from app.domain.data.text_message_content_dto import TextMessageContentDTO
from app.domain.rewriting_pipeline_execution_dto import RewritingPipelineExecutionDTO
from app.llm import CapabilityRequestHandler, RequirementList, CompletionArguments
from app.pipeline import Pipeline
from app.pipeline.prompts.rewriting_prompts import faq_system_prompt, problem_statement_system_prompt
from app.web.status.status_update import  RewritingCallback

logger = logging.getLogger(__name__)


class RewritingPipeline(Pipeline):
    callback: RewritingCallback
    request_handler: CapabilityRequestHandler
    output_parser: PydanticOutputParser
    variant: Literal["faq", "problem_statement"]

    def __init__(self, callback: RewritingCallback, variant: Literal["faq", "problem_statement"]):
        super().__init__(
            implementation_id="rewriting_pipeline_reference_impl"
        )
        self.callback = callback
        self.request_handler = CapabilityRequestHandler(
            requirements=RequirementList(
                gpt_version_equivalent=4.5,
                context_length=16385,
            )
        )
        self.tokens = []
        self.variant = variant

    def __call__(
        self,
        dto: RewritingPipelineExecutionDTO,
        prompt: Optional[ChatPromptTemplate] = None,
        **kwargs,
    ):
        if not dto.to_be_rewritten:
            raise ValueError("You need to provide a text to rewrite")

        variant_prompts = {
            "faq": faq_system_prompt,
            "problem_statement": problem_statement_system_prompt,
        }
        print(variant_prompts[self.variant])
        prompt = variant_prompts[self.variant].format(
            rewritten_text=dto.to_be_rewritten,
        )
        prompt = PyrisMessage(
            sender=IrisMessageRole.SYSTEM,
            contents=[TextMessageContentDTO(text_content=prompt)],
        )

        response = self.request_handler.chat(
            [prompt], CompletionArguments(temperature=0.4)
        )
        self._append_tokens(response.token_usage, PipelineEnum.IRIS_REWRITING_PIPELINE)
        response = response.contents[0].text_content
        
        # remove ``` from start and end if exists
        if response.startswith("```") and response.endswith("```"):
            response = response[3:-3]
            if response.startswith("markdown"):
                response = response[8:]
            response = response.strip()
        
        final_result = response
        self.callback.done(final_result=final_result, tokens=self.tokens)
