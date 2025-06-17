from textwrap import dedent

from src.infra.gpt.gpt_response import GptResponse


class TextModifier:
    def __init__(self) -> None:
        self.client = GptResponse(model="gpt-4.1-mini")

    def __call__(
        self,
        text: str,
        edit_plan: str,
        history_context: str,
        image_base64: str | None = None,
    ) -> str:
        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": dedent("""
                        あなたはフリマアプリの商品説明文を改善するAIアシスタントです。
                        ユーザーが提供する行番号付きの商品説明文と、修正方針に基づいて、部分的な修正指示を出力してください。

                        ## 出力形式
                        以下のJSON形式で出力してください：

                        {
                            "should_edit": "no" または "yes",
                            "content": [
                                {
                                    "line": 行番号（数値）,
                                    "command": "add" | "delete" | "modify",
                                    "text": "追加・変更する内容（deleteの場合は空文字列）"
                                }
                            ]
                        }

                        should_editが"no"の場合はcontentは空配列にしてください。
                        should_editが"yes"の場合は修正指示をcontentに配列で含めてください。

                        ## 修正方針
                        1. 修正方針を忠実に反映するようにする
                        2. 必要最小限の修正のみを行い、変更不要な行には言及しない
                        3. フリマアプリの商品説明として適切な表現を心がける
                        4. 特段指示がない限りは、文章のスタイル（箇条書き、文体など、最後に挨拶文があることなど）は基本的に維持する
                        5. 画像の内容と説明文の整合性を確認する
                        6. 制約条件が提示されている場合は、それらを考慮してバランスの取れた修正を行う
                        7. 一度の変更で文章を長くし過ぎると、ユーザーが読むのが辛くなってしまうので、修正は控えめでお願いします。
                        8. 「短くして」「長い」などの指示がある場合は、各文に対して、少し思い切って、短く言い換えたり、細かい情報を削除したりする

                        ## 注意点
                        - 個人がリユースとして出品する一点物の商品の説明文章です
                        - 店舗での販売でないので、サイズ展開やカラー展開など、他の商品が存在することを前提とした表現や説明になることはありません
                        - JSON形式のみを返してください。説明や理由は含めないでください
                        - 一度の変更で文章を長くし過ぎると、ユーザーが読むのが辛くなってしまうので、修正は控えめでお願いします。

                        ## 例
                        入力テキスト:
                        1: 美品のワンピース
                        2: サイズM
                        3: 着用回数少なめ

                        修正方針: もっと詳しく状態を説明し、色の情報を追加

                        出力例:
                        {
                            "should_edit": "yes",
                            "content": [
                                {
                                    "line": 3,
                                    "command": "modify",
                                    "text": "着用回数3回程度、目立った汚れや傷はありません"
                                },
                                {
                                    "line": 2,
                                    "command": "add",
                                    "text": "色：ネイビー"
                                }
                            ]
                        }
                        """),  # noqa: E501, RUF001
                    },
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"修正方針: {edit_plan}"},
                    {"type": "text", "text": f"元のテキスト: {text}"},
                    {"type": "text", "text": f"制約条件: {history_context}"},
                ]
                + (
                    [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                            },
                        },
                    ]
                    if image_base64
                    else []
                ),
            },
        ]
        return self.client(messages)
