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
                        ユーザーの発話が、画面上のテキストに対する感想・フィードバックを含んでいるかを判定してください。
                        雑音や関係ない話（例: 咳払い・意味のない言葉・話題の逸脱）などは "No" としてください.
                        ユーザーは、明確な改善を示すこともあれば、何らかの不満点などを示すこともあると思いますが、いずれにせよ、画面上のテキストに対するフィードバックを含んでいるかどうかを判定してください。
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
                        以下に、ユーザーが画面上のテキストに対して行った発話内容が与えられます。
                        まず、画面上のテキストの内容を読んだ上で、ユーザーの発話の内容に基づいて、どのような修正を行うべきかを自然言語で説明してください。
                        明確な指示がある場合は、それに従い、そうで無い場合についても、議論の触発材になればいいので、修正の方向性を考えてみてください。
                        修正そのものはこの時点では行わず、あくまで修正方針だけを出力してください。
                        出力形式：「〇〇な修正を加えてみるのはどうでしょうか？」
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
                        以下の指示に従って、画面上のテキストを修正してください。
                        修正されたテキストだけを出力してください。
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

    def __call__(self, text: str, utterance: str) -> str:
        if not self._should_edit(text, utterance):
            return text
        edit_plan = self._plan_edit(text, utterance)
        print(f"📝 修正方針: {edit_plan}")
        return self._apply_edit(text, edit_plan)
