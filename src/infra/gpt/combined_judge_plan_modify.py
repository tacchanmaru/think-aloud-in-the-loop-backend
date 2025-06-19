from textwrap import dedent

from src.infra.gpt.gpt_response import GptResponse
from src.usecase.text_modification_types import TextModificationHistory


class CombinedJudgePlanModify:
    def __init__(self, model: str = "gpt-4.1-mini") -> None:
        self.client = GptResponse(model=model)

    def __call__(
        self,
        text: str,
        utterance: str,
        history_summary: str = "",
        image_base64: str | None = None,
        history: list[TextModificationHistory] | None = None,
    ) -> str:
        history_context = (
            f"\n\n現在の編集における制約条件:\n{history_summary}" if history_summary else ""
        )
        
        # 編集履歴をフォーマット（最新の3つまで）
        history_text = ""
        if history and len(history) > 0:
            recent_history = history[-3:]  # 最新の3つまで
            history_text = "編集履歴:\n" + "\n".join(
                [
                    f"- 元文章: {h.original_text}\n  発話: {h.utterance}\n  計画: {h.edit_plan}\n  修正後: {h.modified_text}\n"
                    for h in recent_history
                ]
            )

        # テキストに行番号を付与（空行はスキップ）
        lines = text.split("\n")
        numbered_lines = []
        for i, line in enumerate(lines):
            if line.strip():  # 空行でない場合のみ行番号を付与
                numbered_lines.append(f"{i + 1}: {line}")
        numbered_text = "\n".join(numbered_lines)

        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": dedent("""
                        あなたはフリマアプリの商品説明文を改善するAIアシスタントです。

                        ユーザーが提供する元の商品説明文と、それに関する感想を含む発話に基づいて、以下の処理を一度に行ってください：

                        ## ステップ1: 修正が必要かの判断
                        その発話が商品説明文に対するフィードバックを含んでいるかを判断してください。
                        - 具体的な変更指示だけでなく、「読みづらい」「情報が足りない」などのフィードバックの場合でも、修正を検討します。
                        - 咳払いや意味のない言葉、関係のない話題など、明らかにフィードバックでないものの場合は、修正は不要です。
                        - 商品説明文をそのまま読んでいるだけの場合なども想定されますが、その場合は修正は不要です。
                        - 「元に戻して」系の発話の場合も修正を検討します。

                        ## ステップ2: 修正指示の生成（修正が必要な場合のみ）
                        修正が必要と判断した場合は、以下の方針で具体的な修正指示を生成してください：
                        - ユーザーから特段指示がない限りは、文章のスタイル（箇条書き、文体など）は基本的に維持する
                        - 制約条件が提示されている場合は、それらを考慮してバランスの取れた修正を提案する
                        - 「元に戻して」系の発話の場合は、履歴から適切な過去の状態や特徴を特定して復元する
                        - 必要最小限の修正のみを行い、変更不要な行には言及しない
                        - フリマアプリの商品説明として適切な表現を心がける
                        - 画像の内容と説明文の整合性を確認する
                        - 一度の変更で文章を長くし過ぎたり、短くしすぎたりすると、ユーザーが読むのが辛くなってしまうので、修正は控えめでお願いします。

                        ## 出力形式
                        以下のJSON形式で出力してください：

                        {
                            "should_edit": "no" または "yes",
                            "plan": "修正方針の説明（ユーザーが直感的に確認しやすいようになるべく短くシンプルに）",
                            "content": [
                                {
                                    "line": 行番号（数値）,
                                    "command": "add" | "delete" | "modify",
                                    "text": "追加・変更する内容（deleteの場合は空文字列）"
                                }
                            ]
                        }

                        should_editが"no"の場合はplanは空文字列、contentは空配列にしてください。
                        should_editが"yes"の場合は修正方針をplanに、修正指示をcontentに配列で含めてください。

                        ## 注意点
                        - JSON形式のみを返してください。説明や理由は含めないでください
                        - 個人が出品する一点物の商品の説明文章なので、他の商品が存在することを前提とした表現や説明になることはありません
                        - 文章として読みやすいようにスタイルには特に気をつけてください
                        1. 箇条書きの中に急に文章が入り込んだり、空行が変なところに入り込んだりしないように注意してください
                        2. 特に箇条書きに変更する際や、箇条書きを追加する際などは、空行が変なところに挟まれたり、順番がおかしくならないように注意してください
                        3. 元の文章に変な空行が含まれていたり、順番がおかしい場合なども、ユーザーの発話に関係なく直していいです。
                        - 重複している項目が無いように注意してください

                        ## 例: 状態項目を箇条書きに追加する場合
                        入力テキスト:
                        1: ふわふわの白いイタチのぬいぐるみです。
                        2: - 種類: イタチのぬいぐるみ
                        3: - カラー: ホワイト（しっぽは黒）
                        4: - サイズ: 約20cm
                        5: 
                        6: 目立った汚れはありません。
                        7: ご覧いただきありがとうございます。

                        ユーザーの発話: 状態も種類などと合わせて箇条書きにして

                        出力例:
                        {
                            "should_edit": "yes",
                            "plan": "状態の情報を箇条書きの項目として追加します。",
                            "content": [
                                {
                                    "line": 5,
                                    "command": "add",
                                    "text": "- 状態: 目立った汚れや傷はなく、美品です"
                                },
                                {
                                    "line": 6,
                                    "command": "delete",
                                    "text": ""
                                }
                            ]
                        }
                        """),  # noqa: E501, RUF001
                    },
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"元の商品説明文: {numbered_text}"},
                    {"type": "text", "text": f"ユーザーの発話: {utterance}"},
                    {"type": "text", "text": f"制約条件: {history_context}"},
                ]
                + ([{"type": "text", "text": history_text}] if history_text else [])
                + (
                    [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                            },
                        },
                    ]
                    if image_base64
                    else []
                ),
            },
        ]
        return self.client(messages)
