from operator import itemgetter

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable

from ...domain import IrisMessage, IrisMessageRole, ExerciseExecutionDTOWrapper
from ...llm import BasicRequestHandler
from ...llm.langchain import IrisLangchainChatModel
from ..pipeline import Pipeline


class SimpleChatPipeline(Pipeline):
    """A simple chat pipeline that uses our custom langchain chat model for our own request handler"""

    llm: IrisLangchainChatModel
    pipeline: Runnable

    def __repr__(self):
        return f"{self.__class__.__name__}(llm={self.llm})"

    def __str__(self):
        return f"{self.__class__.__name__}(llm={self.llm})"

    def __init__(self):
        super().__init__(implementation_id="simple_chat_pipeline")
        request_handler = BasicRequestHandler("gpt35")
        self.llm = IrisLangchainChatModel(request_handler)
        self.pipeline = {"query": itemgetter("query")} | self.llm | StrOutputParser()

    def __call__(self, wrapper: ExerciseExecutionDTOWrapper, **kwargs) -> IrisMessage:
        """
        Gets a response from the langchain chat model
        """
        dto = wrapper.dto
        query = dto.query
        if query is None:
            raise ValueError("IrisMessage must not be None")
        message = query.text
        response = self.pipeline.invoke({"question": message})
        return IrisMessage(role=IrisMessageRole.ASSISTANT, text=response)
