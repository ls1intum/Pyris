from datetime import datetime


class IrisImage:
    prompt: str
    base64: str
    url: str | None
    timestamp: datetime
    _raw_data: any

    def __init__(
        self,
        prompt: str,
        base64: str,
        url: str,
        timestamp: datetime,
        raw_data: any = None,
    ):
        self.prompt = prompt
        self.base64 = base64
        self.url = url
        self.timestamp = timestamp
        self._raw_data = raw_data
