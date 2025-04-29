from dataclasses import dataclass

from src.infra.gpt.gpt_response import GptResponse


@dataclass
class TextModificationHistory:
    utterance: str
    edit_plan: str
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


class HistorySummarizer:
    def __init__(self) -> None:
        self.client = GptResponse()

    def __call__(self, history: list[TextModificationHistory]) -> str:
        if not history:
            return ""

        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": """
                        あなたは、テキスト編集の履歴から、テキストの望ましい状態に関する条件を抽出するAIアシスタントです。
                        与えられた編集履歴を分析し、ユーザーが求めている本質的な条件や制約を箇条書きで整理してください。

                        以下の点に注意して条件を生成してください：
                        1. 単なる変更の履歴ではなく、その変更から読み取れる望ましい状態を記述
                        2. 相反する変更がある場合は、その背後にある本質的なバランスを見出す
                        3. 具体的な変更内容ではなく、満たすべき条件として一般化する
                        4. 最新のフィードバックほど重視して条件を更新する
                        5. 3-5個程度の箇条書きに収める

                        出力形式：
                        ・〇〇すぎず××すぎない、バランスの取れた表現を使用する
                        ・△△な要素は必ず含める
                        ・□□に関する情報は詳しく記載する

                        例：
                        入力履歴：
                        - 「絵文字を使って」
                        - 「絵文字が多いな」
                        - 「絵文字が1個も無くなっちゃったから使って」
                        - 「絵文字が多いって」

                        出力例：
                        ・絵文字は適度に使用し、読みやすさとカジュアルさのバランスを取る
                        ・文章の要所に絵文字を配置し、視認性を確保する
                        ・過度な装飾は避け、シンプルさを保つ
                        """,
                    },
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "編集履歴:\n"
                        + "\n".join(
                            [f"- 発話: {h.utterance}\n  計画: {h.edit_plan}" for h in history],
                        ),
                    },
                ],
            },
        ]
        return self.client(messages)


class EditPlanGenerator:
    def __init__(self) -> None:
        self.client = GptResponse()

    def __call__(self, text: str, utterance: str, history_summary: str = "") -> str:
        history_context = (
            f"\n\n現在の編集における制約条件:\n{history_summary}" if history_summary else ""
        )

        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": f"""
                        あなたはメルカリの商品説明文を改善するAIアシスタントです。
                        まず、画面上のテキストを読んだ上で指示に従がってください。

                        ユーザーが提供する元の商品説明文と、その改善に関するフィードバックに基づいて、どのような修正を行うべきかを自然言語で説明してください。{history_context}

                        明確な指示がある場合は、それに従い、そうで無い場合についても、議論の触発材になればいいので、修正の方向性を考えてみてください。
                        修正そのものはこの時点では行わず、あくまで修正方針だけを出力してください。

                        以下の点に注意して修正方針を決定してください：
                        1. ユーザーの意図を正確に理解し、それに沿った修正を提案する
                        2. 制約条件が提示されている場合は、それらを考慮してバランスの取れた修正を提案する
                        3. 以前の編集を否定するフィードバックの場合でも、極端な変更は避け、バランスを重視する
                        4. 一貫性のある改善を目指し、制約条件に沿った修正を行う

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
        self.history_summarizer = HistorySummarizer()

    def judge_and_plan(
        self,
        text: str,
        utterance: str,
        history: list[TextModificationHistory],
    ) -> TextModificationResult:
        """判定と修正計画の生成を行います。"""
        should_edit = self.judge(text, utterance)
        if not should_edit:
            return TextModificationResult(should_edit=False)

        # 履歴のサマリーを生成
        history_summary = self.history_summarizer(history)

        # 履歴を考慮した修正計画を生成
        edit_plan = self.plan_generator(text, utterance, history_summary)
        return TextModificationResult(should_edit=True, edit_plan=edit_plan)

    def apply_modification(self, text: str, edit_plan: str) -> str:
        """修正計画に基づいてテキストを修正します。"""
        return self.modifier(text, edit_plan)
