class CompletionArguments:
    """Arguments for the completion request"""

    def __init__(self, max_tokens: int, temperature: float, stop: list[str]):
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.stop = stop
