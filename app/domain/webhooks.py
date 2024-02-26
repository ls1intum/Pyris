from enum import Enum
from typing import List

from pydantic import BaseModel

from domain.submission import Submission


class WebhookTypeEnum(str, Enum):
    UPDATED = "UPDATED"
    DELETED = "DELETED"


class RepositoryWebhookTypeEnum(WebhookTypeEnum):
    EXERCISE = "EXERCISE"
    STUDENT = "STUDENT"


class RepositoryTypeEnum(str, Enum):
    TEMPLATE = "TEMPLATE"
    SOLUTION = "SOLUTION"
    TESTS = "TESTS"


class PipelineExecutionSettingsDTO(BaseModel):
    authenticationToken: str
    allowedModelIdentifiers: List[str]


class PyrisWebhookDTO(BaseModel):
    type: WebhookTypeEnum
    settings: PipelineExecutionSettingsDTO


class UnitItem(BaseModel):
    id: int
    lectureId: int
    releaseDate: str
    name: str
    attachmentVersion: int


class PyrisLectureUnitWebhookDTO(PyrisWebhookDTO):
    courseId: int
    units: List[UnitItem]


class PyrisRepositoryWebhookDTO(PyrisWebhookDTO):
    type: RepositoryWebhookTypeEnum
    commitHash: str


class PyrisRepositoryWebhookDTOWithSubmission(PyrisRepositoryWebhookDTO):
    submission: Submission


class PyrisRepositoryWebhookDTOWithRepositoryType(PyrisRepositoryWebhookDTO):
    repositoryType: RepositoryTypeEnum
