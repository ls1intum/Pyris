from typing import List, Optional, Any

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import (
    BaseChatModel,
)
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult

from domain import IrisMessage
from llm import RequestHandlerInterface, CompletionArguments


def convert_iris_message_to_base_message(iris_message: IrisMessage) -> BaseMessage:
    return BaseMessage(content=iris_message.text, role=iris_message.role)


def convert_base_message_to_iris_message(base_message: BaseMessage) -> IrisMessage:
    return IrisMessage(text=base_message.content, role=base_message.role)


class IrisLangchainChatModel(BaseChatModel):
    """Custom langchain chat model for our own request handler"""

    request_handler: RequestHandlerInterface

    def __init__(self, request_handler: RequestHandlerInterface, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.request_handler = request_handler

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any
    ) -> ChatResult:
        iris_message = self.request_handler.chat_completion(
            messages, CompletionArguments(stop=stop)
        )
        base_message = convert_iris_message_to_base_message(iris_message)
        return ChatResult(generations=[base_message])

    @property
    def _llm_type(self) -> str:
        return "Iris"
