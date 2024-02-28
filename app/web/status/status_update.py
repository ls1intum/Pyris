from typing import Any

import requests
from abc import ABC, abstractmethod

from ...domain.tutor_chat.tutor_chat_status_update_dto import TutorChatStatusUpdateDTO


class StatusCallback(ABC):
    url: str

    def __init__(self, url: str):
        self.url = url

    @abstractmethod
    def on_status_update(self, status: Any):
        pass


class TutorChatStatusCallback(StatusCallback):
    def __init__(self, run_id: str, base_url: str):
        url = f"https://{base_url}/api/v1/public/pyris/pipelines/tutor-chat/runs/{run_id}/status"
        self.run_id = run_id
        super().__init__(url)

    def on_status_update(self, status: TutorChatStatusUpdateDTO):
        requests.post(
            self.url,
            headers={"Content-Type": "application/json", "Authorization": self.run_id},
            json=status.json(by_alias=True),
        )
