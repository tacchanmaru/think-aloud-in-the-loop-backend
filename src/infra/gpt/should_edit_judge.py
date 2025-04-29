from src.infra.gpt.gpt_response import GptResponse


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
                        あなたはユーザーの発話が、画面上のテキスト（商品説明文）に対する感想やフィードバックを含んでいるかを判定するAIアシスタントです。

                        画面上のテキストに対するフィードバックを含んでいると考えられる場合は "Yes"としてください。
                        ex. 「読みづらい」「情報が足りない」「文章が硬いなー」

                        一方で、雑音や関係ない話は "No" としてください。
                        ex. 咳払い・意味のない言葉・話題の逸脱

                        「Yes」または「No」のどちらか一語で返答してください。
                        """,  # noqa: E501, RUF001
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
