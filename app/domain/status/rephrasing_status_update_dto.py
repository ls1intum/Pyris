from app.domain.data.competency_dto import Competency
from app.domain.status.status_update_dto import StatusUpdateDTO


class RephrasingStatusUpdateDTO(StatusUpdateDTO):
    result: str = ""
