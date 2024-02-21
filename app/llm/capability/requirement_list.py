class RequirementList:
    """A class to represent the requirements you want to match against"""

    cost: float | None
    gpt_version_equivalent: float | None
    speed: float | None
    context_length: int | None
    vendor: str | None
    privacy_compliance: bool | None
    self_hosted: bool | None
    image_recognition: bool | None
    json_mode: bool | None

    def __init__(
        self,
        cost: float | None = None,
        gpt_version_equivalent: float | None = None,
        speed: float | None = None,
        context_length: int | None = None,
        vendor: str | None = None,
        privacy_compliance: bool | None = None,
        self_hosted: bool | None = None,
        image_recognition: bool | None = None,
        json_mode: bool | None = None,
    ) -> None:
        self.cost = cost
        self.gpt_version_equivalent = gpt_version_equivalent
        self.speed = speed
        self.context_length = context_length
        self.vendor = vendor
        self.privacy_compliance = privacy_compliance
        self.self_hosted = self_hosted
        self.image_recognition = image_recognition
        self.json_mode = json_mode
