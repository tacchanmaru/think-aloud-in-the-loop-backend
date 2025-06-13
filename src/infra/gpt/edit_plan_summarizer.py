from textwrap import dedent

from src.infra.gpt.gpt_response import GptResponse


class EditPlanSummarizer:
    def __init__(self, model: str = "gpt-4.1-nano") -> None:
        self.client = GptResponse(model=model)

    def __call__(self, edit_plan: str) -> str:
        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": dedent("""
                        あなたは編集計画を分かりやすく要約するAIアシスタントです。
                        
                        編集計画の内容を受け取り、ユーザーが直感的に理解できるよう、
                        どのような変更が行われるのかを1行で簡潔に要約してください。
                        
                        # 要約のポイント
                        - 具体的な変更内容を明確に
                        - 専門用語は使わず、一般的な言葉で
                        - 箇条書き形式で簡潔に
                        - 「〜を修正」「〜を追加」「〜を改善」などの動詞を使用
                        
                        # 出力例
                        - 商品の詳細情報を追加
                        - 文章の読みやすさを改善
                        - 不要な表現を削除
                        
                        # 出力形式
                        箇条書き形式（- で始まる）で出力してください。JSON形式や説明文は不要です。
                        """),
                    },
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"編集計画: {edit_plan}"},
                ],
            },
        ]
        return self.client(messages)