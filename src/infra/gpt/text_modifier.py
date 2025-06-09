from textwrap import dedent

from src.infra.gpt.gpt_response import GptResponse


class TextModifier:
    def __init__(self) -> None:
        self.client = GptResponse()

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
                        どの行を修正するかを以下の形式で指示してください：

                        **行の修正:**
                        - "X行目をYに変更"

                        **行の追加:**
                        - "X行目の後にYを追加"

                        **行の削除:**
                        - "X行目を削除"
                        - "X-Y行目を削除"

                        ## 修正方針
                        1. 元の文章に含まれていた情報はなるべく落とさないようにする
                        2. 文章のスタイル（箇条書き、文体など）は基本的に維持する
                        3. 修正方針で特段指示がある場合のみ、情報の圧縮やスタイルの変更を行う
                        4. 修正方針を忠実に反映するようにする
                        5. フリマアプリの商品説明として適切な表現を心がける
                        6. 画像が提供されている場合は、画像の内容と説明文の整合性を確認する
                        7. 制約条件が提示されている場合は、それらを考慮してバランスの取れた修正を行う
                        8. 必要最小限の修正のみを行い、変更不要な行には言及しない

                        ## 注意点
                        - 個人がリユースとして出品する一点物の商品の説明文章です
                        - 店舗での販売でないので、サイズ展開やカラー展開など、他の商品が存在することを前提とした表現や説明になることはありません
                        - 修正指示のみを返してください。説明や理由は含めないでください

                        ## 例
                        入力テキスト:
                        1: 美品のワンピース
                        2: サイズM
                        3: 着用回数少なめ

                        修正方針: もっと詳しく状態を説明し、色の情報を追加

                        出力例:
                        3行目を着用回数3回程度、目立った汚れや傷はありませんに変更
                        2行目の後に色：ネイビーを追加
                        """),  # noqa: RUF001
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
