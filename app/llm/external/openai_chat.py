import json
import logging
import time
from datetime import datetime
from typing import Literal, Any, Sequence, Union, Dict, Type, Callable, Optional

from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from openai import (
    OpenAI,
    APIError,
    APITimeoutError,
    RateLimitError,
    InternalServerError,
    ContentFilterFinishReasonError,
)
from openai.lib.azure import AzureOpenAI
from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageParam
from openai.types.chat.completion_create_params import ResponseFormat
from pydantic import Field
from pydantic.v1 import BaseModel as LegacyBaseModel

from ...common.message_converters import map_str_to_role, map_role_to_str
from app.domain.data.text_message_content_dto import TextMessageContentDTO
from ...domain import PyrisMessage
from ...domain.data.image_message_content_dto import ImageMessageContentDTO
from ...domain.data.json_message_content_dto import JsonMessageContentDTO
from ...domain.data.tool_call_dto import ToolCallDTO
from ...domain.data.tool_message_content_dto import ToolMessageContentDTO
from ...domain.pyris_message import PyrisAIMessage
from ...llm import CompletionArguments
from ...llm.external.model import ChatModel


def convert_to_open_ai_messages(
    messages: list[PyrisMessage],
) -> list[ChatCompletionMessageParam]:
    """
    Convert a list of PyrisMessage to a list of ChatCompletionMessageParam
    """
    openai_messages = []
    for message in messages:
        openai_content = []
        for content in message.contents:
            if message.sender == "TOOL":
                match content:
                    case ToolMessageContentDTO():
                        openai_messages.append(
                            {
                                "role": "tool",
                                "content": content.tool_content,
                                "tool_call_id": content.tool_call_id,
                            }
                        )
                    case _:
                        pass
            else:
                match content:
                    case ImageMessageContentDTO():
                        openai_content.append(
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{content.base64}",
                                    "detail": "high",
                                },
                            }
                        )
                    case TextMessageContentDTO():
                        openai_content.append(
                            {"type": "text", "text": content.text_content}
                        )
                    case JsonMessageContentDTO():
                        openai_content.append(
                            {
                                "type": "json_object",
                                "json_object": content.json_content,
                            }
                        )
                    case _:
                        pass

                if isinstance(message, PyrisAIMessage) and message.tool_calls:
                    openai_message = {
                        "role": map_role_to_str(message.sender),
                        "content": openai_content,
                        "tool_calls": [
                            {
                                "id": tool.id,
                                "type": tool.type,
                                "function": {
                                    "name": tool.function.name,
                                    "arguments": json.dumps(tool.function.arguments),
                                },
                            }
                            for tool in message.tool_calls
                        ],
                    }
                else:
                    openai_message = {
                        "role": map_role_to_str(message.sender),
                        "content": openai_content,
                    }
                openai_messages.append(openai_message)
    return openai_messages


def convert_to_iris_message(message: ChatCompletionMessage) -> PyrisMessage:
    """
    Convert a ChatCompletionMessage to a PyrisMessage
    """
    if message.tool_calls:
        return PyrisAIMessage(
            tool_calls=[
                ToolCallDTO(
                    id=tc.id,
                    type=tc.type,
                    function={
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                )
                for tc in message.tool_calls
            ],
            contents=[TextMessageContentDTO(textContent="")],
            send_at=datetime.now(),
        )
    else:
        return PyrisMessage(
            sender=map_str_to_role(message.role),
            contents=[TextMessageContentDTO(textContent=message.content)],
            send_at=datetime.now(),
        )


class OpenAIChatModel(ChatModel):
    model: str
    api_key: str
    tools: Optional[
        Sequence[Union[Dict[str, Any], Type[LegacyBaseModel], Callable, BaseTool]]
    ] = Field(default_factory=list, alias="tools")
    _client: OpenAI

    def chat(
        self, messages: list[PyrisMessage], arguments: CompletionArguments
    ) -> PyrisMessage:
        # noinspection PyTypeChecker
        retries = 5
        backoff_factor = 2
        initial_delay = 1
        # Maximum wait time: 1 + 2 + 4 + 8 + 16 = 31 seconds

        messages = convert_to_open_ai_messages(messages)

        for attempt in range(retries):
            try:
                if arguments.response_format == "JSON":
                    if self.tools:
                        response = self._client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            temperature=arguments.temperature,
                            max_tokens=arguments.max_tokens,
                            response_format=ResponseFormat(type="json_object"),
                            tools=self.tools,
                        )
                    else:
                        response = self._client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            temperature=arguments.temperature,
                            max_tokens=arguments.max_tokens,
                            response_format=ResponseFormat(type="json_object"),
                        )
                else:
                    if self.tools:
                        response = self._client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            temperature=arguments.temperature,
                            max_tokens=arguments.max_tokens,
                            tools=self.tools,
                        )
                    else:
                        response = self._client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            temperature=arguments.temperature,
                            max_tokens=arguments.max_tokens,
                        )
                choice = response.choices[0]
                if choice.finish_reason == "content_filter":
                    # I figured that an openai error would be automatically raised if the content filter activated,
                    # but it seems that that is not the case.
                    # We don't want to retry because the same message will likely be rejected again.
                    # Raise an exception to trigger the global error handler and report a fatal error to the client.
                    raise ContentFilterFinishReasonError()
                return convert_to_iris_message(choice.message)
            except (
                APIError,
                APITimeoutError,
                RateLimitError,
            ):
                wait_time = initial_delay * (backoff_factor**attempt)
                logging.exception(f"OpenAI error on attempt {attempt + 1}:")
                logging.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        raise Exception(f"Failed to get response from OpenAI after {retries} retries")

    def bind_tools(
        self,
        tools: Sequence[
            Union[Dict[str, Any], Type[LegacyBaseModel], Callable, BaseTool]
        ],
    ):
        self.tools = tools


class DirectOpenAIChatModel(OpenAIChatModel):
    type: Literal["openai_chat"]

    def model_post_init(self, __context: Any) -> None:
        self._client = OpenAI(api_key=self.api_key)

    def __str__(self):
        return f"OpenAIChat('{self.model}')"

    def bind_tools(
        self,
        tools: Sequence[
            Union[Dict[str, Any], Type[LegacyBaseModel], Callable, BaseTool]
        ],
    ):
        self.tools = [convert_to_openai_tool(tool) for tool in tools]


class AzureOpenAIChatModel(OpenAIChatModel):
    type: Literal["azure_chat"]
    endpoint: str
    azure_deployment: str
    api_version: str

    def model_post_init(self, __context: Any) -> None:
        self._client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            azure_deployment=self.azure_deployment,
            api_version=self.api_version,
            api_key=self.api_key,
        )

    def bind_tools(
        self,
        tools: Sequence[
            Union[Dict[str, Any], Type[LegacyBaseModel], Callable, BaseTool]
        ],
    ):
        self.tools = [convert_to_openai_tool(tool) for tool in tools]

    def __str__(self):
        return f"AzureChat('{self.model}')"
