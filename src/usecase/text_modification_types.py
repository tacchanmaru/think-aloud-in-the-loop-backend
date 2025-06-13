from dataclasses import dataclass
from typing import Literal


@dataclass
class TextModificationInstruction:
    line: int
    command: Literal["add", "delete", "modify"]
    text: str


@dataclass
class TextModificationJSON:
    should_edit: Literal["yes", "no"]
    content: list[TextModificationInstruction]


@dataclass
class TextModificationHistory:
    utterance: str
    edit_plan: str
    original_text: str
    modified_text: str


@dataclass
class TextState:
    original_text: str
    current_text: str
    history: list[TextModificationHistory]
    history_summary: str = ""


@dataclass
class TextModificationResult:
    should_edit: bool
    edit_plan: str | None = None
    modified_text: str | None = None
