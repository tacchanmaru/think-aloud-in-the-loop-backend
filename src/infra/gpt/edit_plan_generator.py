from textwrap import dedent

from src.infra.gpt.gpt_response import GptResponse


class EditPlanGenerator:
    def __init__(self, model: str = "gpt-4.1-mini") -> None:
        self.client = GptResponse(model=model)

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
                        "text": dedent("""
                        あなたはフリマアプリの商品説明文を改善するAIアシスタントです。

                        ユーザーが提供する元の商品説明文と、それに関する感想を含む発話に基づいて、以下の2つの判断を行ってください：

                        1. まず、その発話が商品説明文に対するフィードバックを含んでいるかを判断してください。
                           - 具体的な変更指示だけでなく、「読みづらい」「情報が足りない」などのフィードバックの場合でも、修正を検討します。
                           - 咳払いや意味のない言葉、関係のない話題など、明らかにフィードバックでないものの場合は、修正は不要です。
                           - 商品説明文をそのまま読んでいるだけの場合なども想定されますが、その場合は修正は不要です。

                        2. 修正が必要と判断した場合は、どのような修正を行うべきかの方針を決定してください。
                           - 元の文章に含まれていた情報はなるべく落とさないようにする
                           - 文章のスタイル（箇条書き、空行の使い方など）は基本的に維持する
                           - ユーザーから特段指示がある場合のみ、情報の圧縮やスタイルの変更を提案する
                           - 制約条件が提示されている場合は、それらを考慮してバランスの取れた修正を提案する

                        # 注意点
                        個人がリユースとして出品する一点物の商品の説明文章です。
                        店舗での販売でないので、サイズ展開やカラー展開など、他の商品が存在することを前提とした表現や説明になることはありません。

                        # 出力形式
                        以下のJSONフォーマットで出力してください：
                        {
                            "should_edit": "no" または "yes",
                            "content": should_editが"no"の場合は空文字列、"yes"の場合は修正方針（ユーザーが直感的に確認しやすいようになるべく短くシンプルに）
                        }
                        """),  # noqa: E501, RUF001
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
