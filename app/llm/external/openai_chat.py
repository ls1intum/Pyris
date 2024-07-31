import logging
import time
from datetime import datetime
from typing import Literal, Any, Sequence, Union, Dict, Type, Callable

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_core.tools import BaseTool
from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageParam
from openai.types.chat.completion_create_params import ResponseFormat
from pydantic.v1 import BaseModel as LegacyBaseModel

from ...common.message_converters import (
    map_str_to_role,
    map_role_to_str,
    convert_iris_message_to_langchain_message,
)
from app.domain.data.text_message_content_dto import TextMessageContentDTO
from ...domain import PyrisMessage
from ...domain.data.image_message_content_dto import ImageMessageContentDTO
from ...domain.data.json_message_content_dto import JsonMessageContentDTO
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

        openai_message = {
            "role": map_role_to_str(message.sender),
            "content": openai_content,
        }
        openai_messages.append(openai_message)
    return openai_messages


def convert_to_iris_message(message: str) -> PyrisMessage:
    """
    Convert a ChatCompletionMessage to a PyrisMessage
    """
    return PyrisMessage(
        sender=map_str_to_role("assistant"),
        contents=[TextMessageContentDTO(textContent=message)],
        send_at=datetime.now(),
    )


class OpenAIChatModel(ChatModel):
    model: str
    api_key: str
    _client: ChatOpenAI | AzureChatOpenAI

    def chat(
        self, messages: list[PyrisMessage], arguments: CompletionArguments
    ) -> PyrisMessage:
        print("Sending messages to OpenAI", messages)
        # noinspection PyTypeChecker
        retries = 5
        backoff_factor = 2
        initial_delay = 1

        for attempt in range(retries):
            try:
                if arguments.response_format == "JSON":
                    response = self._client.invoke(
                        model=self.model,
                        input=[
                            convert_iris_message_to_langchain_message(m)
                            for m in messages
                        ],
                        temperature=arguments.temperature,
                        max_tokens=arguments.max_tokens,
                        response_format=ResponseFormat(type="json_object"),
                    )
                else:
                    response = self._client.invoke(
                        model=self.model,
                        input=[
                            convert_iris_message_to_langchain_message(m)
                            for m in messages
                        ],
                        temperature=arguments.temperature,
                        max_tokens=arguments.max_tokens,
                    )
                return convert_to_iris_message(response.content)
            except Exception as e:
                wait_time = initial_delay * (backoff_factor**attempt)
                logging.warning(f"Exception on attempt {attempt + 1}: {e}")
                logging.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        logging.error("Failed to interpret image after several attempts.")

    def bind_tools(
        self,
        tools: Sequence[
            Union[Dict[str, Any], Type[LegacyBaseModel], Callable, BaseTool]
        ],
    ):
        return self._client.bind_tools(tools)


class DirectOpenAIChatModel(OpenAIChatModel):

    type: Literal["openai_chat"]

    def model_post_init(self, __context: Any) -> None:
        self._client = ChatOpenAI(api_key=self.api_key)

    def __str__(self):
        return f"OpenAIChat('{self.model}')"

    def bind_tools(
        self,
        tools: Sequence[
            Union[Dict[str, Any], Type[LegacyBaseModel], Callable, BaseTool]
        ],
    ):
        return self._client.bind_tools(tools)


class AzureOpenAIChatModel(OpenAIChatModel):

    type: Literal["azure_chat"]
    endpoint: str
    azure_deployment: str
    api_version: str

    def model_post_init(self, __context: Any) -> None:
        self._client = AzureChatOpenAI(
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
    ) -> Runnable[LanguageModelInput, BaseMessage]:
        return self._client.bind_tools(tools)

    def __str__(self):
        return f"AzureChat('{self.model}')"
