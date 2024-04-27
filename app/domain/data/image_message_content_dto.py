from pydantic import BaseModel, Field
from typing import List, Optional


class ImageMessageContentDTO(BaseModel):
    base64: List[str] 
    prompt: Optional[str] 
