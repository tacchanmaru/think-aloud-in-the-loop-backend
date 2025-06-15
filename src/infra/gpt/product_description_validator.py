from textwrap import dedent

from src.infra.gpt.gpt_response import GptResponse


class ProductDescriptionValidator:
    def __init__(self, model: str = "gpt-4.1-nano") -> None:
        self.gpt_response = GptResponse(model=model)

    def __call__(self, text: str) -> bool:
        """商品説明文として適切かどうかを判定する."""
        messages = [
            {
                "role": "system",
                "content": dedent("""
                あなたは商品説明文の品質をチェックする専門家です。
                与えられたテキストが商品の説明文として適切かどうかを判定してください。
                基本的には「yes」と回答してください。
                
                商品説明文として関係の無い内容（主に編集指示（例："空行", "二行目に", "行目を", "追加する", "変更する"など））
                が含まれてしまっている場合は「no」と回答してください。

                回答は「yes」または「no」のみでお願いします。
                """),  # noqa: E501, RUF001
            },
            {
                "role": "user",
                "content": f"以下のテキストを評価してください:\n\n{text}",
            },
        ]

        response = self.gpt_response(messages)
        print(f"response: {response}")
        return response.strip().lower() == "yes"
