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
                        あなたは、テキスト編集の履歴から、ユーザー個人の文章の特徴や好みを抽出するAIアシスタントです。
                        与えられた編集履歴を分析し、このユーザーの文章に対する個人的な好みや特徴を箇条書きで整理してください。

                        以下の点に注意して特徴を抽出してください：
                        1. ユーザーが好む表現方法や文体の特徴
                        2. 重視する情報の種類や詳しさの程度
                        3. 避けたい表現や嫌がる要素
                        4. 文章構成や見た目に関する好み
                        5. 最新のフィードバックほど重視して特徴を更新する
                        6. 3-5個程度の箇条書きに収める

                        注意：一般的な文章作成の指針（情報を落とさない、スタイルを維持するなど）は含めず、
                        あくまでこのユーザー固有の文章に対する個人的な特徴や好みのみを抽出してください。

                        出力形式：
                        ・具体的で詳細な説明を好む
                        ・カジュアルな表現よりもフォーマルな表現を使用する
                        ・商品の状態に関する情報を重視する
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
