from typing import Any

import requests
from abc import ABC, abstractmethod

from domain.status import ExerciseTutorChatStatusDTO


class StatusCallback(ABC):
    url: str

    def __init__(self, url: str):
        self.url = url

    @abstractmethod
    def on_status_update(self, status: Any):
        pass


class TutorChatStatusCallback(StatusCallback):
    def __init__(self, run_id: str):
        url = f"/api/v1/public/pyris/tutorchat/runs/{run_id}/status"
        super().__init__(url)

    def on_status_update(self, status: ExerciseTutorChatStatusDTO):
        requests.post(
            self.url, headers={"Content-Type": "application/json"}, json=status.json()
        )
