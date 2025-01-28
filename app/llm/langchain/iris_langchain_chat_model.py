import logging
from logging import Logger
from typing import List, Optional, Any, Sequence, Union, Dict, Type, Callable

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import LanguageModelInput
from langchain_core.language_models.chat_models import (
    BaseChatModel,
)
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from langchain_core.outputs.chat_generation import ChatGeneration
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.common.PipelineEnum import PipelineEnum
from app.common.token_usage_dto import TokenUsageDTO
from ...common.message_converters import (
    convert_langchain_message_to_iris_message,
    convert_iris_message_to_langchain_message,
)
from ...llm import RequestHandler, CompletionArguments


class IrisLangchainChatModel(BaseChatModel):
    """Custom langchain chat model for our own request handler"""

    request_handler: RequestHandler
    completion_args: CompletionArguments
    tokens: TokenUsageDTO = None
    logger: Logger = logging.getLogger(__name__)
    tools: Optional[
        Sequence[Union[Dict[str, Any], Type[BaseModel], Callable, BaseTool]]
    ] = Field(default_factory=list, alias="tools")

    def __init__(
        self,
        request_handler: RequestHandler,
        completion_args: Optional[CompletionArguments] = CompletionArguments(stop=None),
        **kwargs: Any,
    ) -> None:
        super().__init__(
            request_handler=request_handler, completion_args=completion_args, **kwargs
        )

    def bind_tools(
        self,
        tools: Sequence[Union[Dict[str, Any], Type[BaseModel], Callable, BaseTool]],
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, BaseMessage]:
        """Bind a sequence of tools to the request handler for function calling support.

        Args:
            tools: Sequence of tools that can be one of:
                  - Dict describing the tool
                  - Pydantic BaseModel
                  - Callable function
                  - BaseTool instance
            **kwargs: Additional arguments passed to the request handler

        Returns:
            self: Returns this instance as a Runnable

        Raises:
            ValueError: If tools sequence is empty or contains invalid tool types
        """
        if not tools:
            raise ValueError("At least one tool must be provided")

        self.tools = tools
        return self

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        iris_messages = [convert_langchain_message_to_iris_message(m) for m in messages]
        self.completion_args.stop = stop
        iris_message = self.request_handler.chat(
            iris_messages, self.completion_args, self.tools
        )
        base_message = convert_iris_message_to_langchain_message(iris_message)
        chat_generation = ChatGeneration(message=base_message)
        self.tokens = TokenUsageDTO(
            model=iris_message.token_usage.model_info,
            numInputTokens=iris_message.token_usage.num_input_tokens,
            costPerMillionInputToken=iris_message.token_usage.cost_per_input_token,
            numOutputTokens=iris_message.token_usage.num_output_tokens,
            costPerMillionOutputToken=iris_message.token_usage.cost_per_output_token,
            pipeline=PipelineEnum.NOT_SET,
        )
        return ChatResult(generations=[chat_generation])

    @property
    def _llm_type(self) -> str:
        return "Iris"
