from textwrap import dedent

from src.infra.gpt.gpt_response import GptResponse


class ThinkAloudExampleGenerator:
    def __init__(self) -> None:
        self.client = GptResponse()

    def __call__(
        self,
        current_text: str,
        image_base64: str | None = None,
        original_text: str | None = None,
        modified_text: str | None = None,
    ) -> list[str]:
        """思考発話の例を生成する.

        Args:
            current_text: 現在の商品説明文
            image_base64: 商品画像のBase64エンコードデータ（オプション）
            original_text: 元の商品説明文（修正後の場合のみ）
            modified_text: 修正後の商品説明文（修正後の場合のみ）

        Returns:
            思考発話の例のリスト（5個程度）

        """  # noqa: RUF002
        # 修正後かどうかで異なるプロンプトを使用
        if modified_text and original_text:
            # 修正後の場合
            system_prompt = dedent("""
            あなたはフリマアプリの商品説明文を見ているユーザーです。
            商品説明文が修正された後の状況で、その修正内容や現在の文章について思ったことを、
            短い発話例として5個生成してください。

            発話例は以下の特徴を持つようにしてください：
            1. 非常に短い発話（5-10語程度）
            2. 「〜したい」「〜を加えたい」「〜について書きたい」などの簡潔な表現
            3. 改善点や追加したい内容を端的に表現
            4. 自然で口語的な表現
            5. 具体的で実行可能な改善点を示唆

            例：
            - "目を引くようにしたい"
            - "重量や手触りについても触れたい"

            必ずJSON形式で返してください。他の文章は一切含めないでください：
            {"examples": ["例1", "例2", "例3", "例4", "例5"]}
            """)  # noqa: RUF001

            user_content: list[dict] = [
                {"type": "text", "text": f"元の文章: {original_text}"},
                {"type": "text", "text": f"修正後の文章: {modified_text}"},
                {"type": "text", "text": f"現在の文章: {current_text}"},
            ]
        else:
            # 初期状態の場合
            system_prompt = dedent("""
            あなたはフリマアプリの商品説明文を見ているユーザーです。
            現在の商品説明文について思ったことを、短い発話例として5個生成してください。

            発話例は以下の特徴を持つようにしてください：
            1. 非常に短い発話（5-10語程度）
            2. 「〜したい」「〜を加えたい」「〜について書きたい」などの簡潔な表現
            3. 改善点や追加したい内容を端的に表現
            4. 自然で口語的な表現
            5. 具体的で実行可能な改善点を示唆

            例：
            - "目を引くようにしたい"
            - "重量や手触りについても触れたい"

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
