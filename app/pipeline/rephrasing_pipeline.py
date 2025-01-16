import logging
from typing import Optional

from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
)

from app.common.PipelineEnum import PipelineEnum
from app.common.pyris_message import PyrisMessage, IrisMessageRole
from app.domain.data.text_message_content_dto import TextMessageContentDTO
from app.domain.data.competency_dto import Competency
from app.domain.rephrasing_pipeline_execution_dto import RephrasingPipelineExecutionDTO
from app.llm import CapabilityRequestHandler, RequirementList, CompletionArguments
from app.pipeline import Pipeline
from app.pipeline.prompts.faq_rephrasal import system_prompt_faq
from app.web.status.status_update import  RephrasingCallback

logger = logging.getLogger(__name__)


class RephrasingPipeline(Pipeline):
    callback: RephrasingCallback
    request_handler: CapabilityRequestHandler
    output_parser: PydanticOutputParser

    def __init__(self, callback: Optional[RephrasingCallback] = None):
        super().__init__(
            implementation_id="rephrasing_pipeline_reference_impl"
        )
        self.callback = callback
        self.request_handler = CapabilityRequestHandler(
            requirements=RequirementList(
                gpt_version_equivalent=4.5,
                context_length=16385,
            )
        )
        self.output_parser = PydanticOutputParser(pydantic_object=Competency)
        self.tokens = []

    def __call__(
        self,
        dto: RephrasingPipelineExecutionDTO,
        prompt: Optional[ChatPromptTemplate] = None,
        **kwargs,
    ):
        if not dto.to_be_rephrased:
            raise ValueError("You need to provide a text to rephrase")

        #
        prompt = system_prompt_faq.format(
            rephrased_text=dto.to_be_rephrased,
        )
        prompt = PyrisMessage(
            sender=IrisMessageRole.SYSTEM,
            contents=[TextMessageContentDTO(text_content=prompt)],
        )

        response = self.request_handler.chat(
            [prompt], CompletionArguments(temperature=0.4)
        )
        self._append_tokens(
            response.token_usage, PipelineEnum.IRIS_REPHRASING_PIPELINE
        )
        response = response.contents[0].text_content
        final_result = response
        logging.info(f"Final rephrased text: {final_result}")
        self.callback.done(final_result=final_result, tokens=self.tokens)
