from datetime import datetime
from pydantic import BaseModel


class BuildLogEntryDTO(BaseModel):
    timestamp: datetime
    message: str

    def __str__(self):
        return f"{self.timestamp}: {self.message}"
