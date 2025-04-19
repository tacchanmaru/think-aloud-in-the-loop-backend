from src.infra.gpt.gpt_response import GptResponse


class ModifyText:
    def __init__(
        self,
    ) -> None:
        self.client = GptResponse()

    def _should_edit(self, text: str, utterance: str) -> bool:
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

    def _plan_edit(self, text: str, utterance: str) -> str:
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

    def _apply_edit(self, text: str, edit_plan: str) -> str:
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

    def __call__(self, text: str, utterance: str) -> tuple[str, str]:
        if not self._should_edit(text, utterance):
            return text, ""
        edit_plan = self._plan_edit(text, utterance)
        modified = self._apply_edit(text, edit_plan)
        return modified, edit_plan
