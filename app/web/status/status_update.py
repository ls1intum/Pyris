from typing import Any

import requests
from abc import ABC, abstractmethod

from ...domain.tutor_chat.tutor_chat_status_update_dto import TutorChatStatusUpdateDTO
import logging

logger = logging.getLogger(__name__)


class StatusCallback(ABC):
    url: str

    def __init__(self, url: str):
        self.url = url

    @abstractmethod
    def on_status_update(self, status: Any):
        pass


class TutorChatStatusCallback(StatusCallback):
    def __init__(self, run_id: str, base_url: str):
        url = f"{base_url}/api/public/pyris/pipelines/tutor-chat/runs/{run_id}/status"
        self.run_id = run_id
        super().__init__(url)

    def on_status_update(self, status: TutorChatStatusUpdateDTO):
        try:
            requests.post(
                self.url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.run_id}",
                },
                json=status.dict(by_alias=True),
            ).raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending status update: {e}")
