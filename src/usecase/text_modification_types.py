from dataclasses import dataclass


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
