from llm.wrapper.model import LanguageModel
from llm.wrapper.openai_completion import NativeOpenAICompletionModel, AzureOpenAICompletionModel
from llm.wrapper.openai_chat import NativeOpenAIChatModel, AzureOpenAIChatModel
from llm.wrapper.openai_embeddings import NativeOpenAIEmbeddingModel, AzureOpenAIEmbeddingModel
from llm.wrapper.ollama import OllamaModel

type AnyLLM = (
        NativeOpenAICompletionModel
        | AzureOpenAICompletionModel
        | NativeOpenAIChatModel
        | AzureOpenAIChatModel
        | NativeOpenAIEmbeddingModel
        | AzureOpenAIEmbeddingModel
        | OllamaModel
)
