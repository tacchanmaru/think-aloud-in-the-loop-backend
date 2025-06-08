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
                        "text": """
                        あなたはフリマアプリの商品説明文を改善するAIアシスタントです。
                        ユーザーが提供する元の商品説明文と、修正方針に基づいて、商品説明文を修正してください。

                        修正の際には以下のガイドラインに従ってください：
                        1. 元の文章に含まれていた情報はなるべく落とさないようにする
                        2. 文章のスタイル（箇条書き、空行の使い方、文体など）は基本的に維持する
                        3. 修正方針で特段指示がある場合のみ、情報の圧縮やスタイルの変更を行う
                        4. 修正方針を忠実に反映するようにする
                        5. フリマアプリの商品説明として適切な表現を心がける
                        6. 画像が提供されている場合は、画像の内容と説明文の整合性を確認する
                        7. 制約条件が提示されている場合は、それらを考慮してバランスの取れた修正を行う

                        # 注意点
                        個人がリユースとして出品する一点物の商品の説明文章です。
                        店舗での販売でないので、サイズ展開やカラー展開など、他の商品が存在することを前提とした表現や説明になることはありません。

                        修正した文章のみを返してください。説明や理由は含めないでください。
                        """,  # noqa: RUF001
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
