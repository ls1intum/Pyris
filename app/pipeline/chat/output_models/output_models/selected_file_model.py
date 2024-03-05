from pydantic.v1 import BaseModel as V1BaseModel, Field as V1Field


class SelectedFile(V1BaseModel):
    selected_file: str = V1Field(
        description="Name/Path of the selected file from the list of files according to the feedbacks",
    )
