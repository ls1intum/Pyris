from enum import Enum

from pydantic import BaseModel


class ProgrammingLanguageEnum(str, Enum):
    JAVA = "JAVA"
    PYTHON = "PYTHON"
    C = "C"
    HASKELL = "HASKELL"
    KOTLIN = "KOTLIN"
    VHDL = "VHDL"
    ASSEMBLER = "ASSEMBLER"
    SWIFT = "SWIFT"
    OCAML = "OCAML"
    EMPTY = "EMPTY"


class ProgrammingExercise(BaseModel):
    id: int
    name: str
    programmingLanguage: ProgrammingLanguageEnum
    templateRepositoryCommitHash: str
    solutionRepositoryCommitHash: str
    testsRepositoryCommitHash: str
    problemStatement: str
    startDate: str
    endDate: str
    isPracticeModeEnabled: bool
