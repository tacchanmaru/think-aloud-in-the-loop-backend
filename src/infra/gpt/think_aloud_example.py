from textwrap import dedent

from src.infra.gpt.gpt_response import GptResponse


class ThinkAloudExampleGenerator:
    def __init__(self) -> None:
        self.client = GptResponse()

    def __call__(
        self,
        current_text: str,
        image_base64: str | None = None,
        modified_text: str | None = None,
        edit_plan: str | None = None,
    ) -> list[str]:
        """思考発話の例を生成する.

        Args:
            current_text: 現在の商品説明文
            image_base64: 商品画像のBase64エンコードデータ（オプション）
            modified_text: 修正後の商品説明文（修正後の場合のみ）
            edit_plan: 編集提案（修正後の場合のみ）

        Returns:
            思考発話の例のリスト（5個程度）

        """  # noqa: RUF002
        # 修正後かどうかで異なるプロンプトを使用
        if modified_text and edit_plan:
            # 修正後の場合
            system_prompt = dedent("""
            あなたはフリマアプリの商品説明文を編集している人です。
            商品説明文が提案に従って修正された状況で、編集者として文章を見て思ったことを、
            短い発話例として5個生成してください。

            文章の変化を踏まえ、以下のような観点で発話例を作成してください：
            1. 変化を評価する発話（良い変化を評価、または改善点を指摘）
            2. さらなる改善を提案する発話（別の観点からの改善提案）
            3. 変化の特徴を強化する発話（同じ方向性でさらに改善）
            4. 変化を少し制御する発話（やりすぎを抑制する提案）

            発話例は以下の特徴を持つようにしてください：
            - 非常に短い発話（5-10語程度）
            - 編集者としての漠然とした感覚や印象を表現
            - 具体的な行動ではなく、感じた違和感や印象を表現
            - 自然で口語的な表現
            - 画像の品質や見た目については言及しない

            例：
            - "なんか長すぎる気がする"
            - "もう少し短くしたい"
            - "情報が足りない感じ"
            - "読みにくい印象"

            必ずJSON形式で返してください。他の文章は一切含めないでください：
            {"examples": ["例1", "例2", "例3", "例4", "例5"]}
            """)  # noqa: RUF001

            user_content: list[dict] = [
                {"type": "text", "text": f"修正前の文章: {current_text}"},
                {"type": "text", "text": f"提案内容: {edit_plan}"},
                {"type": "text", "text": f"修正後の文章: {modified_text}"},
            ]
        else:
            # 初期状態の場合
            system_prompt = dedent("""
            あなたはフリマアプリの商品説明文を編集している人です。
            現在の商品説明文を編集者として見て思ったことを、短い発話例として5個生成してください。

            発話例は以下の特徴を持つようにしてください：
            - 非常に短い発話（5-10語程度）
            - 編集者としての漠然とした感覚や印象を表現
            - 具体的な行動ではなく、感じた違和感や印象を表現
            - 自然で口語的な表現
            - 画像の品質や見た目については言及しない

            例：
            - "なんか物足りない感じ"
            - "もう少し詳しくしたい"
            - "読みやすさが気になる"
            - "情報のバランスが悪い"

            必ずJSON形式で返してください。他の文章は一切含めないでください：
            {"examples": ["例1", "例2", "例3", "例4", "例5"]}
            """)  # noqa: RUF001

            user_content: list[dict] = [
                {"type": "text", "text": f"現在の文章: {current_text}"},
            ]

        # 画像がある場合は追加
        if image_base64:
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}",
                    },
                },
            )

        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": system_prompt}],
            },
            {
                "role": "user",
                "content": user_content,
            },
        ]

        response = self.client(messages)

        # JSONレスポンスをパース（より堅牢な処理）
        try:
            import json
            import re

            # レスポンスからJSONを抽出（前後の余分なテキストを除去）
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                examples = result.get("examples", [])
                if examples and len(examples) >= 3:  # 最低3個の例があることを確認
                    return examples[:5]  # 最大5個まで

            # JSONが見つからない場合やパースに失敗した場合
            msg = "No valid JSON found"
            raise json.JSONDecodeError(msg, response, 0)  # noqa: TRY301

        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            # パースに失敗した場合はデフォルトの改善点重視の例を返す
            import logging

            logging.warning(f"Failed to parse think-aloud response: {e}, response: {response}")  # noqa: G004
            return [
                "もう少し詳しく書きたい",
                "写真と説明を合わせたい",
                "価格の理由を書きたい",
                "サイズ情報を追加したい",
                "もっと魅力的にしたい",
            ]
