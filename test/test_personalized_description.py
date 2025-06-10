"""個人化された商品説明文生成のテストスクリプト."""

import base64
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.lib.logger import LOGGER
from src.usecase.generate_product_description import ProductDescriptionGenerator


def load_image_as_base64(image_path: str) -> str:
    """画像ファイルをBase64エンコードして読み込む."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def main() -> None:
    """個人化された商品説明文生成のテスト."""
    # ログ設定
    logger = LOGGER

    # テスト画像のパス
    image_path = project_root / "test" / "pom-pom-purin.jpeg"
    if not image_path.exists():
        logger.error(f"Test image not found: {image_path}")
        return

    # 画像をBase64に変換
    logger.info("Loading test image...")
    image_base64 = load_image_as_base64(str(image_path))

    # 商品説明文生成器とスタイル抽出器を初期化
    generator = ProductDescriptionGenerator()
    
    # PersonalStyleExtractorをimport
    from src.infra.gpt.personal_style_extractor import PersonalStyleExtractor
    style_extractor = PersonalStyleExtractor()

    # 指定されたupdate_history_summary
    update_history_summary = """・具体的で詳細な説明を好むが、冗長さや重複は避け、必要な情報のみを簡潔に残す  
・商品の素材感や細部の作り込み（ヒゲや指先など）を重視し、そのリアルさや丁寧さを必ずアピールする  
・商品の状態説明（汚れや傷の有無、コンディション）を重要視しており、明確かつ簡潔な表現を使う  
・温かみや親しみのある一文でまとめつつも、説明部分は短く要点がまとまった文体を好む  
・本文での長い説明より、箇条書きを効果的に使い、見やすく読みやすい構成を意識する"""

    print("=" * 60)
    print("個人化された商品説明文生成のテスト")
    print("=" * 60)

    # 1. 標準版（個人化なし）の文章生成
    print("\n【1. 標準版（個人化なし）の文章生成】")
    print("-" * 40)
    try:
        result_standard = generator(image_base64)
        if result_standard.error_message:
            print(f"エラー: {result_standard.error_message}")
        else:
            print(result_standard.description)
    except Exception as e:
        print(f"標準版生成エラー: {e}")

    print("\n" + "=" * 60)

    # 2. personal_description_styleを生成
    print("\n【2. personal_description_styleの生成】")
    print("-" * 40)
    print(f"入力されたhistory_summary:\n{update_history_summary}")
    print("-" * 40)
    try:
        personal_description_style = style_extractor(update_history_summary)
        print(f"生成されたpersonal_description_style:\n{personal_description_style}")
    except Exception as e:
        print(f"スタイル抽出エラー: {e}")
        return

    print("\n" + "=" * 60)

    # 3. personal_description_styleを使った文章生成
    print("\n【3. personal_description_styleを使った文章生成】")
    print("-" * 40)
    try:
        # 直接infraのProductDescriptionGeneratorを使用してpersonal_styleを渡す
        from src.infra.gpt.product_description_generator import ProductDescriptionGenerator as InfraGenerator
        infra_generator = InfraGenerator()
        result_with_style = infra_generator(image_base64, personal_description_style)
        print(result_with_style)
    except Exception as e:
        print(f"個人スタイル版生成エラー: {e}")

    print("\n" + "=" * 60)
    print("テスト完了")


if __name__ == "__main__":
    main()
