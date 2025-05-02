from src.infra.gpt.gpt_response import GptResponse


class EditPlanGenerator:
    def __init__(self) -> None:
        self.client = GptResponse(model="gpt-4.1-mini")

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

                        ユーザーが提供する元の商品説明文と、それに関する感想を含む発話に基づいて、以下の2つの判断を行ってください：

                        1. まず、その発話が商品説明文に対するフィードバックを含んでいるかを判断してください。
                           - 具体的な変更指示だけでなく、「読みづらい」「情報が足りない」などのフィードバックの場合でも、修正を検討します。
                           - 咳払いや意味のない言葉、関係のない話題など、明らかにフィードバックでないものの場合は、修正は不要です。
                           - 商品説明文をそのまま読んでいるだけの場合なども想定されますが、その場合は修正は不要です。

                        2. 修正が必要と判断した場合は、どのような修正を行うべきかの方針を決定してください。
                           - 議論の触発材になればいいので、ユーザーの意図を何らかの方向で解釈し、それに沿った修正を提案する
                           - 制約条件が提示されている場合は、それらを考慮してバランスの取れた修正を提案する

                        # 出力形式
                        ・修正が不要な場合は「no」とだけ出力してください。（他の文字を出力すると判定ができません。）
                        ・修正が必要な場合は「〇〇な修正を行います。」といった具合に修正方針のみを出力してください。（修正された商品説明文の出力ではないです。）
                        """,  # noqa: E501, RUF001
                    },
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"元の商品説明文: {text}"},
                    {"type": "text", "text": f"ユーザーの発話: {utterance}"},
                    {"type": "text", "text": f"制約条件: {history_context}"},
                ],
            },
        ]
        return self.client(messages)
