from abc import ABCMeta, abstractmethod

from llm import CompletionArguments

type LlmWrapperInterface = LlmCompletionWrapperInterface | LlmChatCompletionWrapperInterface | LlmEmbeddingWrapperInterface


class LlmCompletionWrapperInterface(metaclass=ABCMeta):
    """Interface for the llm completion wrappers"""

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'completion') and
                callable(subclass.completion))

    @abstractmethod
    def completion(self, prompt: str, arguments: CompletionArguments) -> str:
        """Create a completion from the prompt"""
        raise NotImplementedError


class LlmChatCompletionWrapperInterface(metaclass=ABCMeta):
    """Interface for the llm chat completion wrappers"""

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'chat_completion') and
                callable(subclass.chat_completion))

    @abstractmethod
    def chat_completion(self, messages: list[any], arguments: CompletionArguments) -> any:
        """Create a completion from the chat messages"""
        raise NotImplementedError


class LlmEmbeddingWrapperInterface(metaclass=ABCMeta):
    """Interface for the llm embedding wrappers"""

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'create_embedding') and
                callable(subclass.create_embedding))

    @abstractmethod
    def create_embedding(self, text: str) -> list[float]:
        """Create an embedding from the text"""
        raise NotImplementedError
