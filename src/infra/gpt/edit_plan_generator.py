from src.infra.gpt.gpt_response import GptResponse


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
                        "text": """
                        あなたはメルカリの商品説明文を改善するAIアシスタントです。

                        ユーザーが提供する元の商品説明文と、それに関する感想を含む発話に基づいて、どのような修正を行うべきかを解釈した上で、修正方針を出力してください。
                        明確な指示が無い場合についても、議論の触発材になればいいので、修正の方向性を考えてみてください。

                        以下の点に注意して修正方針を決定してください：
                        1. ユーザーの意図を正確に理解し、それに沿った修正を提案する
                        2. 制約条件が提示されている場合は、それらを考慮してバランスの取れた修正を提案する
                        3. 以前の編集を否定するフィードバックの場合でも、極端な変更は避け、バランスを重視する
                        4. 一貫性のある改善を目指し、制約条件に沿った修正を行う

                        修正そのものはこの時点では行わず、あくまで修正方針だけを出力してください。
                        修正方針は読みやすいように簡潔にしてください。
                        出力形式の例：「〇〇な修正を加えてみるのはどうでしょうか？」
                        """,  # noqa: E501, RUF001
                    },
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"画面上のテキスト: {text}"},
                    {"type": "text", "text": f"ユーザーの発話: {utterance}"},
                    {"type": "text", "text": f"制約条件: {history_context}"},
                ],
            },
        ]
        return self.client(messages)
