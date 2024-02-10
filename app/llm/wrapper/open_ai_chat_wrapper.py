from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from domain import IrisMessage
from llm import CompletionArguments
from llm.wrapper import LlmChatCompletionWrapperInterface


def convert_to_open_ai_messages(
    messages: list[IrisMessage],
) -> list[ChatCompletionMessageParam]:
    return [
        ChatCompletionMessageParam(role=message.role, content=message.message_text)
        for message in messages
    ]


def convert_to_iris_message(message: ChatCompletionMessageParam) -> IrisMessage:
    return IrisMessage(role=message.role, message_text=message.content)


class OpenAIChatCompletionWrapper(LlmChatCompletionWrapperInterface):

    def __init__(self, model: str, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def chat_completion(
        self, messages: list[any], arguments: CompletionArguments
    ) -> any:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=convert_to_open_ai_messages(messages),
        )
        return response
