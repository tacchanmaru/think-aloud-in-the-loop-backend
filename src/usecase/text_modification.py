from src.infra.gpt.edit_plan_generator import EditPlanGenerator
from src.infra.gpt.history_summarizer import HistorySummarizer
from src.infra.gpt.should_edit_judge import ShouldEditJudge
from src.infra.gpt.text_modifier import TextModifier
from src.usecase.text_modification_types import (
    TextModificationHistory,
    TextModificationResult,
)


class TextModificationUseCase:
    def __init__(self) -> None:
        self.judge = ShouldEditJudge()
        self.plan_generator = EditPlanGenerator()
        self.modifier = TextModifier()
        self.history_summarizer = HistorySummarizer()

    def judge_and_plan(
        self,
        text: str,
        utterance: str,
        history: list[TextModificationHistory],
    ) -> TextModificationResult:
        """判定と修正計画の生成を行う."""
        should_edit = self.judge(text, utterance)
        if not should_edit:
            return TextModificationResult(should_edit=False)

        # 履歴のサマリーを生成
        history_summary = self.history_summarizer(history)

        # 履歴を考慮した修正計画を生成
        edit_plan = self.plan_generator(text, utterance, history_summary)
        return TextModificationResult(should_edit=True, edit_plan=edit_plan)

    def apply_modification(self, text: str, edit_plan: str, image_base64: str | None = None) -> str:
        """修正計画に基づいてテキストを修正する."""
        return self.modifier(text, edit_plan, image_base64)
