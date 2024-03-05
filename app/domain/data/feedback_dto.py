from pydantic import BaseModel, Field


class FeedbackDTO(BaseModel):
    text: str
    test_case_name: str = Field(alias="testCaseName")
    credits: float

    def __str__(self):
        return f"{self.test_case_name}: {self.text} ({self.credits} credits)"
