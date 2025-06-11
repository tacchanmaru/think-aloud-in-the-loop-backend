from textwrap import dedent

from src.infra.gpt.gpt_response import GptResponse


class PersonalStyleExtractor:
    def __init__(self) -> None:
        self.client = GptResponse()

    def __call__(self, history_summary: str) -> str:
        """履歴サマリーから個人の文章スタイルの好みを抽出する.

        Args:
            history_summary: ユーザーの文章修正履歴から抽出された個人的特徴

        Returns:
            商品説明文生成に活用できる個人的な文章スタイルの好み

        """
        if not history_summary.strip():
            return ""

        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": dedent("""
                        あなたは、ユーザーの一つの商品に対する個人的な文章に対する好みの特徴から、
                        あらゆる商品（衣類、雑貨、本、電子機器など）の説明文生成に活用できる汎用的な文章スタイルの好みを抽出するAIアシスタントです。

                        与えられた特定の商品に対する個人的特徴を分析し、商品の種類やカテゴリに依存しない
                        このユーザー固有の文章スタイルや表現の好みを整理してください。

                        出力形式：
                        商品説明文生成時に参考にできる、具体的で実用的な指針として整理してください。
                        箇条書きで3-5項目程度にまとめ、直接プロンプトに組み込める形式で出力してください。
                        """),  # noqa: RUF001
                    },
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"個人的特徴:\n{history_summary}",
                    },
                ],
            },
        ]
        return self.client(messages)
