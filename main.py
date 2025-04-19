import asyncio

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.websockets import WebSocketDisconnect

from src.infra.gpt.modify_text import ModifyText
from src.infra.sounddevice.audio_streamer import AudioStreamer
from src.infra.ws_transcriber.ws_transcriber import TranscriptionClient
from src.lib.env import ENV
from src.lib.logger import LOGGER

app = FastAPI()

# CORSの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なオリジンを指定してください
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SAMPLING_RATE = 24000
BLOCK_SIZE = 2048
CHANNELS = 1
API_KEY = ENV.get("OPENAI_API_KEY")

# 現在のテキストを保持する変数
current_text: str | None = None


class TextUpdate(BaseModel):
    text: str


@app.post("/api/display-text")
async def update_display_text(text_update: TextUpdate):
    global current_text
    current_text = text_update.text
    return {"status": "success"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    if not current_text:
        await websocket.close(code=1000, reason="No text has been set")
        return

    transcriber = TranscriptionClient(api_key=API_KEY)
    openai_ws = await transcriber.connect()
    await transcriber.initialize_session(openai_ws)

    loop = asyncio.get_running_loop()

    streamer = AudioStreamer(
        samplerate=SAMPLING_RATE,
        blocksize=BLOCK_SIZE,
        channels=CHANNELS,
    )

    modifier = ModifyText()

    async def receive_and_modify():
        buffer = ""
        i = 0
        while True:
            response = await openai_ws.recv()
            data = await transcriber.parse_response(response)

            if data["type"] == "delta":
                buffer += data["text"]

            elif data["type"] == "completed":
                utterance = data["text"]
                if i == 0:
                    modified, edit_plan = modifier(current_text, utterance)
                else:
                    modified, edit_plan = modifier(modified, utterance)
                i += 1

                # 完了時の結果をフロントエンドに送信
                LOGGER.info(f"utterance: {utterance}")
                LOGGER.info(f"edit_plan: {edit_plan}")
                LOGGER.info(f"modified: {modified}")
                await websocket.send_json(
                    {
                        "type": "completed",
                        "utterance": utterance,
                        "edit_plan": edit_plan,
                        "modified_text": modified,
                    },
                )
                buffer = ""

    with streamer.start(openai_ws, loop):
        try:
            await receive_and_modify()
        except WebSocketDisconnect:
            print("WebSocket接続が切断されました")
        except Exception as e:
            print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
