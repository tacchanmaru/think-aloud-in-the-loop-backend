import asyncio
from dataclasses import dataclass
from typing import List, Optional

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


@dataclass
class TextState:
    original_text: str
    current_text: str
    history: list[dict]  # {"utterance": str, "edit_plan": str, "modified_text": str}


# グローバルな状態管理
text_state: TextState | None = None


class TextUpdate(BaseModel):
    text: str


@app.post("/api/display-text")
async def update_display_text(text_update: TextUpdate) -> dict:
    global text_state
    text_state = TextState(
        original_text=text_update.text,
        current_text=text_update.text,
        history=[],
    )
    return {"status": "success"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    LOGGER.info("New WebSocket connection accepted")

    global text_state
    if not text_state:
        LOGGER.warning("No text has been set, closing connection")
        await websocket.close(code=1000, reason="No text has been set")
        return

    transcriber = None
    openai_ws = None
    streamer = None

    try:
        LOGGER.info("Initializing transcription client...")
        transcriber = TranscriptionClient(api_key=API_KEY)
        openai_ws = await transcriber.connect()
        await transcriber.initialize_session(openai_ws)
        LOGGER.info("Transcription client initialized successfully")

        loop = asyncio.get_running_loop()

        LOGGER.info("Starting audio streamer...")
        streamer = AudioStreamer(
            samplerate=SAMPLING_RATE,
            blocksize=BLOCK_SIZE,
            channels=CHANNELS,
        )
        LOGGER.info("Audio streamer started")

        modifier = ModifyText()

        async def receive_and_modify() -> None:
            if not text_state:  # 型チェックのため再確認
                return

            accumulated_utterance = ""
            while True:
                try:
                    LOGGER.debug("Waiting for audio data...")
                    response = await openai_ws.recv()
                    data = await transcriber.parse_response(str(response))

                    if data["type"] == "delta":
                        pass  # 何もしない

                    elif data["type"] == "completed":
                        utterance = data["text"]
                        if accumulated_utterance:
                            utterance = f"{accumulated_utterance} {utterance}"
                            accumulated_utterance = ""

                        LOGGER.info(f"Combined transcription: {utterance}")
                        LOGGER.info("Applying text modification...")
                        modified, edit_plan = modifier(
                            text_state.current_text,
                            utterance,
                        )

                        if modified == text_state.current_text:  # should_editがFalseの場合
                            LOGGER.info("No changes needed, continuing...")
                            accumulated_utterance = utterance
                            continue

                        # 履歴を更新
                        text_state.history.append(
                            {
                                "utterance": utterance,
                                "edit_plan": edit_plan,
                                "modified_text": modified,
                            },
                        )
                        text_state.current_text = modified

                        # 完了時の結果をフロントエンドに送信
                        LOGGER.info("Sending results to frontend...")
                        LOGGER.info(f"Edit plan: {edit_plan}")
                        LOGGER.info(f"Modified text: {modified}")
                        await websocket.send_json(
                            {
                                "type": "completed",
                                "utterance": utterance,
                                "edit_plan": edit_plan,
                                "modified_text": modified,
                                "original_text": text_state.original_text,
                                "history": text_state.history,
                            },
                        )
                        LOGGER.info("Results sent to frontend")

                except Exception as e:
                    LOGGER.error(f"Error in receive_and_modify: {e}")
                    raise

        LOGGER.info("Starting audio processing...")
        with streamer.start(openai_ws, loop):
            await receive_and_modify()

    except WebSocketDisconnect:
        LOGGER.info("WebSocket connection was disconnected by the client")
    except Exception as e:
        LOGGER.error(f"Error occurred: {e}")
        await websocket.close(code=1011, reason=str(e))
    finally:
        # Cleanup resources
        try:
            LOGGER.info("Cleaning up resources...")
            if openai_ws:
                await openai_ws.close()
            await websocket.close()
            LOGGER.info("Cleanup completed successfully")
        except Exception as e:
            LOGGER.error(f"Error during cleanup: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
