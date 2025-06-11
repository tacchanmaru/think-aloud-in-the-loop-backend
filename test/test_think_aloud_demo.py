import base64
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infra.gpt.think_aloud_example import ThinkAloudExampleGenerator


def main():
    """ThinkAloudExampleGeneratorの動作確認デモ"""
    generator = ThinkAloudExampleGenerator()

    # ferret.jpegを読み込んでbase64エンコード
    ferret_path = Path("test/ferret.jpeg")
    with open(ferret_path, "rb") as f:
        image_data = f.read()
    image_base64 = base64.b64encode(image_data).decode("utf-8")

    # テストデータ（例で提供されたもの）
    current_text = """ふわふわの白いイタチのぬいぐるみ。黒いしっぽとつぶらな瞳がかわいらしいデザインです。

- 種類: イタチのぬいぐるみ
- カラー: ホワイト（しっぽは黒）
- 特徴: ふわふわ素材、可愛い表情
- サイズ: 約20cm（目安）

ご覧いただきありがとうございます。"""

    edit_plan = """商品の詳細や使用感、状態（新品・中古）、素材感、購入時期やブランド情報があればそれも加え、説明文をより具体的で魅力的にする。また、現状の情報は保持しつつ、説明文全体にもう少し肉付けする。"""

    modified_text = """ふわふわの白いイタチのぬいぐるみです。黒いしっぽとつぶらな瞳がかわいらしく、お部屋のインテリアやお子様へのプレゼントにもぴったりのデザインです。

- 種類: イタチのぬいぐるみ
- カラー: ホワイト（しっぽは黒）
- 特徴: ふわふわで肌触りの良い素材、可愛い表情、しっかりとした自立型
- サイズ: 約20cm（目安）
- ブランド情報: 不明ですが、しっかりとした作りです
- 素材感: とても柔らかく抱きしめたくなるような手触りです
- 購入時期: 約1年前に購入し、主に棚の上で飾っていました
- 状態: 目立つ汚れや傷はなく、きれいな状態です（中古品）

ご覧いただきありがとうございます。
お探しの方、ぜひご検討ください。"""

    second_edit_plan = """商品の魅力をより引き立てるため、親しみやすく丁寧な表現に整え、使用感や素材感、状態の良さを強調します。箇条書きの項目はそのまま維持し、情報をわかりやすく整理しつつ、おすすめポイントや使い道をより魅力的に伝える表現を追加します。"""

    second_modified_text = """ふわふわの白いイタチのぬいぐるみです。黒いしっぽとつぶらな瞳がとても愛らしく、見ているだけで癒されます。お部屋のインテリアとしてはもちろん、お子様へのプレゼントにも最適なデザインです。

- 種類: イタチのぬいぐるみ
- カラー: ホワイト（しっぽは黒）
- 特徴: ふわふわで肌触りの良い高品質素材、可愛い表情、安定感のある自立型、思わず抱きしめたくなる可愛らしさ
- サイズ: 約20cm（目安）
- ブランド情報: 不明ですが、縫製や作りがしっかりしていて安心感があります
- 素材感: とても柔らかく、優しい手触りで抱き心地も抜群です
- 購入時期: 約1年前に新品で購入し、主に棚の上でディスプレイしていました
- 状態: 目立った汚れや傷はなく、全体的にきれいな状態です（あくまで中古品となります）
- おすすめポイント: ぬいぐるみ好きの方や動物好きのお子様にも大変おすすめです。インテリアや撮影小物としても活躍します

ご覧いただきありがとうございます。
お探しの方、ご質問等ございましたらお気軽にコメントください。ぜひご検討いただけますと幸いです。"""

    print("=" * 80)
    print("ThinkAloudExampleGenerator 動作確認デモ")
    print("=" * 80)

    # 1. 初期状態での思考発話例生成
    print("\n1. 初期状態での思考発話例生成")
    print("-" * 40)
    print("現在の文章:")
    print(current_text)
    print("\n生成された思考発話例:")
    try:
        examples = generator(
            current_text=current_text,
            image_base64=image_base64,
        )
        for i, example in enumerate(examples, 1):
            print(f"  {i}. {example}")
    except Exception as e:
        print(f"エラー: {e}")

    # 2. 第1回修正後の思考発話例生成
    print("\n\n2. 第1回修正後の思考発話例生成")
    print("-" * 40)
    print("修正前の文章:")
    print(current_text[:100] + "...")
    print("\n提案内容:")
    print(edit_plan)
    print("\n修正後の文章:")
    print(modified_text[:100] + "...")
    print("\n生成された思考発話例:")
    try:
        examples = generator(
            current_text=current_text,
            modified_text=modified_text,
            edit_plan=edit_plan,
            image_base64=image_base64,
        )
        for i, example in enumerate(examples, 1):
            print(f"  {i}. {example}")
    except Exception as e:
        print(f"エラー: {e}")

    # 3. 第2回修正後の思考発話例生成
    print("\n\n3. 第2回修正後の思考発話例生成")
    print("-" * 40)
    print("修正前の文章:")
    print(modified_text[:100] + "...")
    print("\n提案内容:")
    print(second_edit_plan)
    print("\n修正後の文章:")
    print(second_modified_text[:100] + "...")
    print("\n生成された思考発話例:")
    try:
        examples = generator(
            current_text=modified_text,
            modified_text=second_modified_text,
            edit_plan=second_edit_plan,
            image_base64=image_base64,
        )
        for i, example in enumerate(examples, 1):
            print(f"  {i}. {example}")
    except Exception as e:
        print(f"エラー: {e}")

    # 4. 画像なしでの動作確認
    print("\n\n4. 画像なしでの思考発話例生成")
    print("-" * 40)
    print("生成された思考発話例:")
    try:
        examples = generator(
            current_text=current_text,
            modified_text=modified_text,
            edit_plan=edit_plan,
        )
        for i, example in enumerate(examples, 1):
            print(f"  {i}. {example}")
    except Exception as e:
        print(f"エラー: {e}")

    print("\n" + "=" * 80)
    print("デモ完了")
    print("=" * 80)


if __name__ == "__main__":
    main()
