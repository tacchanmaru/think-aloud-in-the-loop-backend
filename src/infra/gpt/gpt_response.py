from openai import OpenAI

from src.lib.env import ENV


class GptResponse:
    def __init__(
        self,
        model: str = "gpt-4.1",
        api_key: str = ENV.get("OPENAI_API_KEY"),
    ) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def __call__(self, messages: list) -> str:
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )

        if completion.choices[0].message.content is None:
            msg = "Completion message is None."
            raise ValueError(msg)
        return completion.choices[0].message.content
