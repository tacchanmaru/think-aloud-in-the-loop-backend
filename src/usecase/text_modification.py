from dataclasses import dataclass
from typing import Optional

from src.infra.gpt.gpt_response import GptResponse


@dataclass
class TextModificationResult:
    should_edit: bool
    edit_plan: str | None = None
    modified_text: str | None = None


class ShouldEditJudge:
    def __init__(self) -> None:
        self.client = GptResponse()

    def __call__(self, text: str, utterance: str) -> bool:
        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": """
                        あなたはユーザーの発話が、画面上のテキストに対する感想・フィードバックを含んでいるかを判定するAIアシスタントです。
                        まず、画面上のテキストを読んだ上で指示に従がってください。

                        ユーザーは、明確な改善方法を示すこともあれば、何らかの不満や指摘を示すことがありますが、明確な指示が無い場合についても、議論の触発材としての修正方針を考えようと思います。
                        いずれにせよ、画面上のテキストを読んだ上でそれに対するフィードバックを含んでいる場合は "Yes" としてください。
                        ex. 「読みづらい」「情報が足りない」「文章が硬いなー」

                        一方で、雑音や関係ない話（例: 咳払い・意味のない言葉・話題の逸脱）などは "No" としてください。

                        「Yes」または「No」のどちらか一語で返答してください。
                        """,
                    },
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"画面上のテキスト: {text}"},
                    {"type": "text", "text": f"ユーザーの発話: {utterance}"},
                ],
            },
        ]
        result = self.client(messages)
        return "yes" in result.lower()


class EditPlanGenerator:
    def __init__(self) -> None:
        self.client = GptResponse()

    def __call__(self, text: str, utterance: str) -> str:
        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": """
                        あなたはメルカリの商品説明文を改善するAIアシスタントです。
                        まず、画面上のテキストを読んだ上で指示に従がってください。

                        ユーザーが提供する元の商品説明文と、その改善に関するフィードバックに基づいて、どのような修正を行うべきかを自然言語で説明してください。

                        明確な指示がある場合は、それに従い、そうで無い場合についても、議論の触発材になればいいので、修正の方向性を考えてみてください。
                        修正そのものはこの時点では行わず、あくまで修正方針だけを出力してください。

                        修正方針は読みやすいように簡潔にしてください。
                        出力形式の例：「〇〇な修正を加えてみるのはどうでしょうか？」
                        """,
                    },
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"画面上のテキスト: {text}"},
                    {"type": "text", "text": f"ユーザーの発話: {utterance}"},
                ],
            },
        ]
        return self.client(messages)


class TextModifier:
    def __init__(self) -> None:
        self.client = GptResponse()

    def __call__(self, text: str, edit_plan: str) -> str:
        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": """
                        あなたはメルカリの商品説明文を改善するAIアシスタントです。
                        ユーザーが提供する元の商品説明文と、修正方針に基づいて、商品説明文を修正してください。
                        
                        修正の際には以下のガイドラインに従ってください：
                        1. 修正方針を忠実に反映する
                        2. 商品の魅力が伝わる表現を心がける
                        3. 簡潔かつ明確な文章を作成する
                        4. メルカリの商品説明として適切な丁寧さを保つ
                        
                        修正した文章のみを返してください。説明や理由は含めないでください。
                        """,
                    },
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"修正方針: {edit_plan}"},
                    {"type": "text", "text": f"元のテキスト: {text}"},
                ],
            },
        ]
        return self.client(messages)


class TextModificationUseCase:
    def __init__(self) -> None:
        self.judge = ShouldEditJudge()
        self.plan_generator = EditPlanGenerator()
        self.modifier = TextModifier()

    def judge_and_plan(self, text: str, utterance: str) -> TextModificationResult:
        """判定と修正計画の生成を行います。"""
        should_edit = self.judge(text, utterance)
        if not should_edit:
            return TextModificationResult(should_edit=False)

        edit_plan = self.plan_generator(text, utterance)
        return TextModificationResult(should_edit=True, edit_plan=edit_plan)

    def apply_modification(self, text: str, edit_plan: str) -> str:
        """修正計画に基づいてテキストを修正します。"""
        return self.modifier(text, edit_plan)
