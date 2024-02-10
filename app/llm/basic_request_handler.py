from domain import IrisMessage
from llm import LlmManager
from llm import RequestHandlerInterface, CompletionArguments
from llm.wrapper import LlmCompletionWrapperInterface, LlmChatCompletionWrapperInterface, LlmEmbeddingWrapperInterface

type BasicRequestHandlerModel = str


class BasicRequestHandler(RequestHandlerInterface):
    model: BasicRequestHandlerModel
    llm_manager: LlmManager

    def __init__(self, model: BasicRequestHandlerModel):
        self.model = model
        self.llm_manager = LlmManager()

    def completion(self, prompt: str, arguments: CompletionArguments) -> str:
        llm = self.llm_manager.get_llm_by_id(self.model).llm
        if isinstance(llm, LlmCompletionWrapperInterface):
            return llm.completion(prompt, arguments)
        else:
            raise NotImplementedError

    def chat_completion(self, messages: list[IrisMessage], arguments: CompletionArguments) -> IrisMessage:
        llm = self.llm_manager.get_llm_by_id(self.model).llm
        if isinstance(llm, LlmChatCompletionWrapperInterface):
            return llm.chat_completion(messages, arguments)
        else:
            raise NotImplementedError

    def create_embedding(self, text: str) -> list[float]:
        llm = self.llm_manager.get_llm_by_id(self.model).llm
        if isinstance(llm, LlmEmbeddingWrapperInterface):
            return llm.create_embedding(text)
        else:
            raise NotImplementedError
