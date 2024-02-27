from datetime import datetime
from pydantic import BaseModel


class BuildLogEntryDTO(BaseModel):
    timestamp: datetime
    message: str
