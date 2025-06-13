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

    async def initialize_session(
        self,
        websocket,
        model: str = "gpt-4o-mini-transcribe",
        silence_duration_ms: int = 2000,
    ) -> None:
        # 転写専用セッションでは、接続時に自動的にセッションが作成される
        # 初期化レスポンスを待機
        try:
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"Initialization response: {response_data}")
            
            if response_data.get("type") == "error":
                raise Exception(f"OpenAI API error: {response_data}")
            elif response_data.get("type") == "transcription_session.created":
                print("Transcription session created successfully")
                
                # 転写を有効にするためのセッション更新
                update_message = {
                    "type": "transcription_session.update",
                    "session": {
                        "turn_detection": {
                            "type": "server_vad",
                            "threshold": 0.5,
                            "prefix_padding_ms": 300,
                            "silence_duration_ms": silence_duration_ms,
                        },
                        "input_audio_transcription": {
                            "model": model,
                            "language": "ja",
                        }
                    }
                }
                await websocket.send(json.dumps(update_message))
                print("Sent transcription enable message")
                
        except Exception as e:
            print(f"Error during initialization: {e}")
            raise

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
