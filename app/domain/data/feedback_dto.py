from pydantic import BaseModel, Field


class FeedbackDTO(BaseModel):
    text: str
    test_case_name: str = Field(alias="testCaseName")
    credits: float
