from typing import List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from weaviate import WeaviateClient

from app.common.PipelineEnum import PipelineEnum
from app.domain.lecture.lecture_unit_dto import LectureUnitDTO
from app.llm import CapabilityRequestHandler, RequirementList, CompletionArguments
from app.llm.langchain import IrisLangchainChatModel
from app.pipeline import Pipeline
from app.pipeline.prompts.lecture_unit_summary_prompt import lecture_unit_summary_prompt


class LectureUnitSummaryPipeline(Pipeline):
    llm: IrisLangchainChatModel
    pipeline: Runnable
    prompt: ChatPromptTemplate

    def __init__(
            self,
            client: WeaviateClient,
            lecture_unit_dto: LectureUnitDTO,
            lecture_unit_segment_summaries: List[str]
    ) -> None:
        super().__init__()
        self.client = client
        self.lecture_unit_dto = lecture_unit_dto
        self.lecture_unit_segment_summaries = lecture_unit_segment_summaries

        request_handler = CapabilityRequestHandler(
            requirements=RequirementList(
                gpt_version_equivalent=4.5,
                context_length=16385,
                privacy_compliance=True,
            )
        )
        completion_args = CompletionArguments(temperature=0, max_tokens=2000)

        self.llm = IrisLangchainChatModel(
            request_handler=request_handler, completion_args=completion_args
        )
        self.pipeline = self.llm | StrOutputParser()
        self.tokens = []

    def __call__(self, *args, **kwargs):
        lecture_unit_segment_text = ""
        for summary in self.lecture_unit_segment_summaries:
            lecture_unit_segment_text += f"{summary}\n"

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    lecture_unit_summary_prompt (
                        self.lecture_unit_dto,
                        lecture_unit_segment_text
                    ),
                ),
            ]
        )
        formatted_prompt = self.prompt.format_messages()
        self.prompt = ChatPromptTemplate.from_messages(formatted_prompt)
        try:
            response = (self.prompt | self.pipeline).invoke({})
            self._append_tokens(
                self.llm.tokens, PipelineEnum.IRIS_LECTURE_SUMMARY_PIPELINE
            )
            return response
        except Exception as e:
            raise e