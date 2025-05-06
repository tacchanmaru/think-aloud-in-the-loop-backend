from dataclasses import dataclass

from src.infra.gpt.gpt_response import GptResponse


@dataclass
class ProductDescriptionResult:
    description: str
    error_message: str | None = None


class ProductDescriptionGenerator:
    def __init__(self) -> None:
        self.client = GptResponse(model="gpt-4.1")

    def __call__(self, image_base64: str) -> ProductDescriptionResult:
        """画像から商品説明文を生成します.

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
                            あなたはフリマアプリの商品説明文を生成するAIアシスタントです。
                            提供された商品画像を分析し、シンプルな商品説明文を生成してください。

                            以下に示す例のスタイルを参考に商品説明文を生成してください。

                            [例]
                            ロゴデザインのブラックバックパック、ストレッチコード付きで機能的。

                            - ブランド: Supreme
                            - カラー: ブラック
                            - デザイン: ロゴ入り
                            - スタイル: バックパック
                            - 特徴: ストレッチコード付き

                            ご覧いただきありがとうございます。

                            [例]
                            ちいかわのかわいいアクリルスタンド、約16cmのサイズでデスクや棚に最適。

                            - キャラクター名: ちいかわ
                            - スタンドタイプ: アクリルスタンド
                            - デザイン: かわいいキャラクターのイラスト
                            - サイズ: 約16cm

                            ご覧いただきありがとうございます。

                            [例]
                            UNIVERSITYロゴが特徴的なグレーのクルーネックスウェット。

                            - 色: グレー
                            - デザイン: UNIVERSITYロゴ入り
                            - スタイル: クルーネック
                            - 素材: コットン混紡
                            - サイズ: Lサイズ

                            ご覧いただきありがとうございます。

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

        except Exception as e:  # noqa: BLE001
            return ProductDescriptionResult(
                description="",
                error_message=f"商品説明文の生成中にエラーが発生しました: {e!s}",
            )
