import json

import websockets


class TranscriptionClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.ws_url = "wss://api.openai.com/v1/realtime?intent=transcription"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1",
        }

    async def connect(self):  # noqa: ANN201
        return await websockets.connect(self.ws_url, additional_headers=self.headers)

    async def initialize_session(self, websocket, model: str = "gpt-4o-mini-transcribe") -> None:  # noqa: ANN001
        init_message = {
            "type": "transcription_session.update",
            "session": {
                "input_audio_transcription": {
                    "model": model,
                    "language": "ja",
                },
            },
        }
        await websocket.send(json.dumps(init_message))

    async def receive_loop(self, websocket) -> None:  # noqa: ANN001
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("type") == "conversation.item.input_audio_transcription.delta":
                print(data.get("delta", ""), end="", flush=True)
            elif data.get("type") == "conversation.item.input_audio_transcription.completed":
                print("\nUser: ", end="", flush=True)

    async def parse_response(self, raw: str) -> dict:
        data = json.loads(raw)
        if data.get("type") == "conversation.item.input_audio_transcription.delta":
            return {"type": "delta", "text": data.get("delta", "")}
        if data.get("type") == "conversation.item.input_audio_transcription.completed":
            return {"type": "completed", "text": data.get("transcript", "")}
        return {"type": "unknown", "text": ""}
