from textwrap import dedent

from src.infra.gpt.gpt_response import GptResponse
from src.usecase.text_modification_types import TextModificationHistory


class HistorySummarizer:
    def __init__(self) -> None:
        self.client = GptResponse()

    def __call__(self, history: list[TextModificationHistory]) -> str:
        if not history:
            return ""

        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": dedent("""
                        あなたは、テキスト編集の履歴から、テキストの望ましい状態に関する条件を抽出するAIアシスタントです。
                        与えられた編集履歴を分析し、ユーザーが求めている本質的な条件や制約を箇条書きで整理してください。

                        以下の点に注意して条件を生成してください：
                        1. 単なる変更の履歴ではなく、その変更から読み取れる望ましい状態を記述
                        2. 相反する変更がある場合は、その背後にある本質的なバランスを見出す
                        3. 具体的な変更内容ではなく、満たすべき条件として一般化する
                        4. 最新のフィードバックほど重視して条件を更新する
                        5. 3-5個程度の箇条書きに収める

                        出力形式：
                        ・〇〇すぎず××すぎない、バランスの取れた表現を使用する
                        ・△△な要素は必ず含める
                        ・□□に関する情報は詳しく記載する
                        """),  # noqa: RUF001
                    },
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "編集履歴:\n"
                        + "\n".join(
                            [f"- 発話: {h.utterance}\n  計画: {h.edit_plan}" for h in history],
                        ),
                    },
                ],
            },
        ]
        return self.client(messages)
