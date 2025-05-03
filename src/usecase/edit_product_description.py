from dataclasses import dataclass

from src.infra.gpt.gpt_response import GptResponse


@dataclass
class ProductDescriptionEditResult:
    edited_description: str
    error_message: str | None = None


class ProductDescriptionEditor:
    def __init__(self) -> None:
        self.client = GptResponse()

    def __call__(
        self,
        prompt: str,
        current_text: str,
        image_base64: str | None = None,
    ) -> ProductDescriptionEditResult:
        """ユーザーのプロンプトに基づいて商品説明文を編集します.

        Args:
            prompt (str): ユーザーからの編集指示
            current_text (str): 現在の商品説明文
            image_base64 (str | None): Base64エンコードされた商品画像データ

        Returns:
            ProductDescriptionEditResult: 編集された商品説明文と、エラーが発生した場合のエラーメッセージ

        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": """
                    あなたはフリマアプリの商品説明文を編集するAIアシスタントです。
                    ユーザーの指示に基づいて、既存の商品説明文を編集してください。
                    また、提供されている商品画像を参考に、画像の内容と説明文の整合性を確認する。

                    # 注意点
                    個人がリユースとして出品する一点物の商品の説明文章です。
                    店舗での販売でないので、サイズ展開やカラー展開など、他の商品が存在することを前提とした表現や説明になることはありません。
                    """,
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"編集指示: {prompt}"},
                        {"type": "text", "text": f"現在の商品説明文: {current_text}"},
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
            edited_description = self.client(messages)
            return ProductDescriptionEditResult(edited_description=edited_description)

        except Exception as e:  # noqa: BLE001
            return ProductDescriptionEditResult(
                edited_description="",
                error_message=f"商品説明文の編集中にエラーが発生しました: {e!s}",
            )
