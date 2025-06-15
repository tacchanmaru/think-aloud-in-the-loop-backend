from textwrap import dedent

from src.infra.gpt.gpt_response import GptResponse
from src.usecase.text_modification_types import TextModificationHistory


class HistorySummarizer:
    def __init__(self) -> None:
        self.client = GptResponse(model="gpt-4.1-mini")

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
                        あなたは、テキスト編集の履歴から、ユーザー個人の文章の特徴や好みを抽出するAIアシスタントです。
                        与えられた編集履歴を分析し、このユーザーの文章に対する個人的な好みや特徴を箇条書きで整理してください。

                        以下の点に注意して特徴を抽出してください：
                        1. 元文章の内容や情報量を踏まえた上で、ユーザーの発話から読み取れる個人的な好み
                        2. ユーザーが好む表現方法や文体の特徴
                        3. 重視する情報の種類や詳しさの程度（元文章との比較で判断）
                        4. 避けたい表現や嫌がる要素
                        5. 文章構成や見た目に関する好み
                        6. 最新のフィードバックほど重視して特徴を更新する
                        7. 3-5個程度の箇条書きに収める

                        重要：
                        - ユーザーの発話を最も重視し、AIが推論した計画は参考程度に留める
                        - 元文章のコンテキストを考慮して、相対的な好みの強度を判断する
                        - 一般的な文章作成の指針は含めず、このユーザー固有の特徴のみを抽出する

                        出力形式：
                        ・具体的で詳細な説明を好む
                        ・カジュアルな表現よりもフォーマルな表現を使用する
                        ・商品の状態に関する情報を重視する
                        """),  # noqa: E501, RUF001
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
                            [
                                f"- 元文章: {h.original_text}\n  発話: {h.utterance}\n  計画: {h.edit_plan}\n  修正後: {h.modified_text}\n"
                                for h in history
                            ],  # noqa: E501
                        ),
                    },
                ],
            },
        ]
        return self.client(messages)
