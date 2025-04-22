from dataclasses import dataclass
from typing import Optional

from src.infra.gpt.gpt_response import GptResponse


@dataclass
class ProductDescriptionResult:
    description: str
    error_message: str | None = None


class ProductDescriptionGenerator:
    def __init__(self) -> None:
        self.client = GptResponse()

    def __call__(self, image_base64: str) -> ProductDescriptionResult:
        """画像から商品説明文を生成します。

        Args:
            image_base64 (str): Base64エンコードされた画像データ

        Returns:
            ProductDescriptionResult: 生成された商品説明文と、エラーが発生した場合のエラーメッセージ

        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": """
                            あなたはメルカリの商品説明文を生成するAIアシスタントです。
                            提供された商品画像を分析し、魅力的な商品説明文を生成してください。

                            以下の点に注意して説明文を生成してください：
                            1. 商品の主要な特徴を簡潔に説明
                            2. 商品の状態や品質に関する情報を含める
                            3. 適度に絵文字を使用し、読みやすさを確保
                            4. 商品のサイズや材質など、重要な詳細情報を含める
                            5. メルカリの商品説明として適切な丁寧さを保つ
                            6. 購入を検討している人が知りたい情報を優先的に記載

                            出力は商品説明文のみとし、余計な説明は含めないでください。
                            """,
                        },
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                            },
                        },
                        {
                            "type": "text",
                            "text": "この商品の説明文を生成してください。",
                        },
                    ],
                },
            ]
            description = self.client(messages)
            return ProductDescriptionResult(description=description)

        except Exception as e:
            return ProductDescriptionResult(
                description="",
                error_message=f"商品説明文の生成中にエラーが発生しました: {e!s}",
            )
