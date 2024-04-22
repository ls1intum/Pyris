from typing import Optional, Any

from ...domain.status.status_update_dto import StatusUpdateDTO


class ChatStatusUpdateDTO(StatusUpdateDTO):
    result: Optional[Any] = None
