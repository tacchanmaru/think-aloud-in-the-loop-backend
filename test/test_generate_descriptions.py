import base64
import os
import sys
from pathlib import Path

# プロジェクトルートをsys.pathに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infra.gpt.product_description_generator import ProductDescriptionGenerator


def main():
    """testディレクトリ内のすべてのJPEG画像に対して商品説明文を生成する"""
    generator = ProductDescriptionGenerator()
    
    # testディレクトリのパス
    test_dir = Path(__file__).parent
    
    # JPEG画像を取得
    jpeg_files = list(test_dir.glob("*.jpeg"))
    
    print(f"Found {len(jpeg_files)} JPEG images in test directory")
    print("-" * 80)
    
    # 3つずつ処理
    for i in range(0, len(jpeg_files), 3):
        batch = jpeg_files[i:i+3]
        print(f"\n=== バッチ {i//3 + 1} ({len(batch)}枚) ===")
        
        for jpeg_file in batch:
            print(f"\n処理中: {jpeg_file.name}")
            print("=" * 50)
            
            try:
                # 画像をBase64エンコード
                with open(jpeg_file, "rb") as f:
                    image_data = f.read()
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                # 商品説明文を生成
                description = generator(image_base64)
                
                print(f"【{jpeg_file.name}の商品説明文】")
                print(description)
                print("-" * 80)
                
            except Exception as e:
                print(f"エラーが発生しました: {e}")
                print("-" * 80)


if __name__ == "__main__":
    main()