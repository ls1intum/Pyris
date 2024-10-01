class LLMTokenCount:

    model_info: str
    num_input_tokens: int
    num_output_tokens: int

    def __init__(self, model_info: str, num_input_tokens: int, num_output_tokens: int):
        self.model_info = model_info
        self.num_input_tokens = num_input_tokens
        self.num_output_tokens = num_output_tokens

    def __str__(self):
        return f"{self.model_info}: {self.num_input_tokens} in, {self.num_output_tokens} out"
