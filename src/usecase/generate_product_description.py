from dataclasses import dataclass

from src.infra.gpt.personal_style_extractor import PersonalStyleExtractor
from src.infra.gpt.product_description_generator import ProductDescriptionGenerator as InfraGenerator


@dataclass
class ProductDescriptionResult:
    description: str
    error_message: str | None = None


class ProductDescriptionGenerator:
    def __init__(self) -> None:
        self.generator = InfraGenerator()
        self.style_extractor = PersonalStyleExtractor()

    def __call__(
        self,
        image_base64: str,
        history_summary: str | None = None,
    ) -> ProductDescriptionResult:
        """画像から商品説明文を生成します.

        Args:
            image_base64: Base64エンコードされた画像データ
            history_summary: ユーザーの文章修正履歴から抽出された個人的特徴（オプション）

        Returns:
            ProductDescriptionResult: 生成された商品説明文と、エラーが発生した場合のエラーメッセージ

        """
        try:
            # 履歴サマリーから個人スタイルを抽出（存在する場合のみ）
            personal_style = None
            if history_summary and history_summary.strip():
                personal_style = self.style_extractor(history_summary)

            # 商品説明文を生成
            description = self.generator(image_base64, personal_style)
            return ProductDescriptionResult(description=description)

        except Exception as e:  # noqa: BLE001
            return ProductDescriptionResult(
                description="",
                error_message=f"商品説明文の生成中にエラーが発生しました: {e!s}",
            )
