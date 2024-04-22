from typing import Optional

from ...domain.status.status_update_dto import StatusUpdateDTO


class CompetencyExtractionStatusUpdateDTO(StatusUpdateDTO):
    result: Optional[str] = None
