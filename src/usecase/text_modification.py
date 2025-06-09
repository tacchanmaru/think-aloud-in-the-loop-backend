import json

from src.infra.gpt.edit_plan_generator import EditPlanGenerator
from src.infra.gpt.history_summarizer import HistorySummarizer
from src.infra.gpt.text_modifier import TextModifier
from src.usecase.text_modification_types import (
    TextModificationHistory,
    TextModificationResult,
)


class TextModificationUseCase:
    def __init__(self) -> None:
        self.plan_generator = EditPlanGenerator(model="gpt-4.1-mini")
        self.modifier = TextModifier()
        self.history_summarizer = HistorySummarizer()

    def judge_and_plan(
        self,
        text: str,
        utterance: str,
        history_summary: str,
    ) -> TextModificationResult:
        """判定と修正計画の生成を行う."""
        result = self.plan_generator(text, utterance, history_summary)
        try:
            parsed_result = json.loads(result)
            # should_editの値に基づいて結果を返す
            return TextModificationResult(
                should_edit=parsed_result["should_edit"] == "yes",
                edit_plan=parsed_result["content"]
                if parsed_result["should_edit"] == "yes"
                else None,
            )
        except (json.JSONDecodeError, KeyError):
            # JSONパースに失敗した場合や必要なキーが存在しない場合は修正不要として扱う
            return TextModificationResult(should_edit=False)

    def apply_modification(
        self,
        text: str,
        edit_plan: str,
        history_context: str,
        image_base64: str | None = None,
    ) -> str:
        """修正計画に基づいてテキストを修正する."""
        return self.modifier(text, edit_plan, history_context, image_base64)

    def update_history_summary(self, history: list[TextModificationHistory]) -> str:
        """履歴のサマリーを生成する."""
        return self.history_summarizer(history)
