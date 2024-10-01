from pydantic import BaseModel


class TokenUsageDTO(BaseModel):
    model_info: str
    num_input_tokens: int
    num_output_tokens: int