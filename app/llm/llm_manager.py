from common import Singleton
from llm.wrapper import LlmWrapperInterface


class LlmManagerEntry:
    id: str
    llm: LlmWrapperInterface

    def __init__(self, id: str, llm: LlmWrapperInterface):
        self.id = id
        self.llm = llm


class LlmManager(metaclass=Singleton):
    llms: list[LlmManagerEntry]

    def __init__(self):
        self.llms = []

    def get_llm_by_id(self, llm_id):
        for llm in self.llms:
            if llm.id == llm_id:
                return llm

    def add_llm(self, id: str, llm: LlmWrapperInterface):
        self.llms.append(LlmManagerEntry(id, llm))
