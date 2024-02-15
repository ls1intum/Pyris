from llm.wrapper.model import LanguageModel
from llm.wrapper.openai_completion import (
    DirectOpenAICompletionModel,
    AzureOpenAICompletionModel,
)
from llm.wrapper.openai_chat import DirectOpenAIChatModel, AzureOpenAIChatModel
from llm.wrapper.openai_embeddings import (
    DirectOpenAIEmbeddingModel,
    AzureOpenAIEmbeddingModel,
)
from llm.wrapper.ollama import OllamaModel

type AnyLLM = (
    DirectOpenAICompletionModel
    | AzureOpenAICompletionModel
    | DirectOpenAIChatModel
    | AzureOpenAIChatModel
    | DirectOpenAIEmbeddingModel
    | AzureOpenAIEmbeddingModel
    | OllamaModel
)
