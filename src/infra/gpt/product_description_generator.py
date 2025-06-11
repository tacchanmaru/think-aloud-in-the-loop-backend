from textwrap import dedent

from src.infra.gpt.gpt_response import GptResponse


class ProductDescriptionGenerator:
    def __init__(self) -> None:
        self.client = GptResponse(model="gpt-4.1")

    def __call__(self, image_base64: str, personal_style: str | None = None) -> str:
        """画像から商品説明文を生成する.

        Args:
            image_base64: Base64エンコードされた画像データ
            personal_style: 個人の文章スタイルの好み（オプション）

        Returns:
            生成された商品説明文

        """
        # 個人スタイルがある場合とない場合でプロンプトを分ける
        if personal_style and personal_style.strip():
            # 個人化されたプロンプト
            system_prompt = dedent(f"""
            あなたはフリマアプリの商品説明文を生成するAIアシスタントです。
            提供された商品画像を分析し、以下の個人の文章スタイルの好みに合わせて商品説明文を生成してください。

            【このユーザーの文章スタイルの好み】
            {personal_style}

            以下に示す例のスタイルを基本として、上記の個人的好みを反映させてください。

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
            """)
        else:
            # 標準プロンプト
            system_prompt = dedent("""
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
            """)

        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": system_prompt,
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
        return self.client(messages)