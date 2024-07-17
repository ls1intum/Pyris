from typing import List, Optional

from pydantic import BaseModel

from ...domain.status.stage_dto import StageDTO


class StatusUpdateDTO(BaseModel):
    stages: List[StageDTO]
