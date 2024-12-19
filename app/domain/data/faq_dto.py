from pydantic import BaseModel, Field


class FaqDTO(BaseModel):
    faq_id: int = Field(alias="faqId")
    course_id: int = Field(alias="courseId")
    questionTitle: str = Field(alias="questionTitle")
    questionAnswer: str = Field(alias="questionAnswer"),
    course_name: str = Field(default="", alias="courseName")
    course_description: str = Field(default="", alias="courseDescription")



