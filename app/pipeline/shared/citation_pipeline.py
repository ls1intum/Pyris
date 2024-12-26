import logging
import os
from asyncio.log import logger
from enum import Enum
from typing import List, Union

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import Runnable

from app.llm import CapabilityRequestHandler, RequirementList, CompletionArguments
from app.common.PipelineEnum import PipelineEnum
from app.llm.langchain import IrisLangchainChatModel
from app.pipeline import Pipeline
from app.vector_database.faq_schema import FaqSchema

from app.vector_database.lecture_schema import LectureSchema

class InformationType(str, Enum):
    PARAGRAPHS = "PARAGRAPHS"
    FAQS = "FAQS"


class CitationPipeline(Pipeline):
    """A generic reranker pipeline that can be used to rerank a list of documents based on a question"""

    llm: IrisLangchainChatModel
    pipeline: Runnable
    prompt_str: str
    prompt: ChatPromptTemplate

    def __init__(self):
        super().__init__(implementation_id="citation_pipeline")
        request_handler = CapabilityRequestHandler(
            requirements=RequirementList(
                gpt_version_equivalent=4.25,
                context_length=16385,
            )
        )
        self.llm = IrisLangchainChatModel(
            request_handler=request_handler,
            completion_args=CompletionArguments(temperature=0, max_tokens=4000),
        )
        dirname = os.path.dirname(__file__)
        prompt_file_path = os.path.join(dirname, "..", "prompts", "citation_prompt.txt")
        with open(prompt_file_path, "r") as file:
            self.prompt_str = file.read()
        self.pipeline = self.llm | StrOutputParser()
        self.tokens = []

    def __repr__(self):
        return f"{self.__class__.__name__}(llm={self.llm})"

    def __str__(self):
        return f"{self.__class__.__name__}(llm={self.llm})"


    def create_formatted_lecture_string(self, paragraphs):
        """
        Create a formatted string from the data
        """
        formatted_string = ""
        for i, paragraph in enumerate(paragraphs):
            lct = "Lecture: {}, Unit: {}, Page: {}, Link: {},\nContent:\n---{}---\n\n".format(
                paragraph.get(LectureSchema.LECTURE_NAME.value),
                paragraph.get(LectureSchema.LECTURE_UNIT_NAME.value),
                paragraph.get(LectureSchema.PAGE_NUMBER.value),
                paragraph.get(LectureSchema.LECTURE_UNIT_LINK.value) or "No link available",
                paragraph.get(LectureSchema.PAGE_TEXT_CONTENT.value),
            )
            formatted_string += lct

        return formatted_string.replace("{", "{{").replace("}", "}}")

    def create_formatted_faq_string(self, faqs):
        """
        Create a formatted string from the data
        """
        formatted_string = ""
        for i, faq in enumerate(faqs):
            faq = "Question: {}, Answer: {}".format(
                faq.get(FaqSchema.QUESTION_ANSWER.value),
                faq.get(FaqSchema.QUESTION_TITLE.value),
            )
            formatted_string += faq

        return formatted_string.replace("{", "{{").replace("}", "}}")


    def __call__(
        self,
        information: Union[List[dict], List[str]],
        answer: str,
        information_type: InformationType = InformationType.PARAGRAPHS,
        **kwargs,
    ) -> str:
        """
        Runs the pipeline
            :param information: List of information which can be list of dicts or list of strings. Used to augment the response
            :param query: The query
            :return: Selected file content
        """
        paras = ""

        if information_type == InformationType.FAQS:
            paras = self.create_formatted_faq_string(information)
        if information_type == InformationType.PARAGRAPHS:
            paras = self.create_formatted_lecture_string(information)

        try:
            self.default_prompt = PromptTemplate(
                template=self.prompt_str,
                input_variables=["Answer", "Paragraphs"],
            )
            response = (self.default_prompt | self.pipeline).invoke(
                {"Answer": answer, "Paragraphs": paras}
            )
            self._append_tokens(self.llm.tokens, PipelineEnum.IRIS_CITATION_PIPELINE)
            if response == "!NONE!":
                return answer
            return response
        except Exception as e:
            logger.error("citation pipeline failed", e)
            raise e
