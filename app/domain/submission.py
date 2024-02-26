from typing import List

from pydantic import BaseModel


class Submission(BaseModel):
    submission_id: str
