import asyncio
import base64
from dataclasses import dataclass

from fastapi import FastAPI, File, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.websockets import WebSocketDisconnect

from src.infra.sounddevice.audio_streamer import AudioStreamer
from src.infra.ws_transcriber.ws_transcriber import TranscriptionClient
from src.lib.env import ENV
from src.lib.logger import LOGGER
from src.usecase.generate_product_description import ProductDescriptionGenerator
from src.usecase.text_modification import (
    TextModificationHistory,
    TextModificationUseCase,
    TextState,
)

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


class TextUpdate(BaseModel):
    text: str


@app.post("/api/display-text")
async def update_display_text(text_update: TextUpdate) -> dict:
    global text_state
    text_state = TextState(
        original_text=text_update.text,
        current_text=text_update.text,
        history=[],
        history_summary="",
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

        text_modification_usecase = TextModificationUseCase()

        async def receive_and_modify() -> None:
            if not text_state:  # 型チェックのため再確認
                return

            while True:
                try:
                    LOGGER.debug("Waiting for audio data...")
                    response = await openai_ws.recv()
                    data = await transcriber.parse_response(str(response))

                    if data["type"] == "delta":
                        pass  # 何もしない

                    elif data["type"] == "completed":
                        utterance = data["text"]
                        LOGGER.info(f"Transcription completed: {utterance}")
                        LOGGER.info("Judging and planning text modification...")

                        # まず判定と修正計画の生成を行う
                        result = text_modification_usecase.judge_and_plan(
                            text_state.current_text,
                            utterance,
                            text_state.history,
                        )

                        if not result.should_edit:  # should_editがFalseの場合
                            LOGGER.info("No changes needed, continuing...")
                            continue

                        if not result.edit_plan:  # edit_planがNoneの場合
                            LOGGER.warning("No edit plan generated, continuing...")
                            continue

                        # 修正計画をフロントエンドに送信
                        LOGGER.info(f"Edit plan: {result.edit_plan}")
                        LOGGER.info(f"Current constraints:\n{text_state.history_summary}")
                        await websocket.send_json(
                            {
                                "type": "edit_plan",
                                "utterance": utterance,
                                "edit_plan": result.edit_plan,
                                "original_text": text_state.original_text,
                                "history_summary": text_state.history_summary,
                            },
                        )
                        LOGGER.info("Edit plan sent to frontend")

                        # 修正を適用
                        LOGGER.info("Applying modification...")
                        modified_text = text_modification_usecase.apply_modification(
                            text_state.current_text,
                            result.edit_plan,
                        )

                        # 履歴を更新
                        text_state.history.append(
                            TextModificationHistory(
                                utterance=utterance,
                                edit_plan=result.edit_plan,
                                modified_text=modified_text,
                            ),
                        )
                        text_state.current_text = modified_text

                        # history_summaryを更新
                        text_state.history_summary = text_modification_usecase.history_summarizer(
                            text_state.history,
                        )
                        LOGGER.info(f"Updated constraints:\n{text_state.history_summary}")

                        # 修正結果をフロントエンドに送信
                        LOGGER.info(f"Modified text: {modified_text}")
                        await websocket.send_json(
                            {
                                "type": "modification_complete",
                                "utterance": utterance,
                                "modified_text": modified_text,
                                "original_text": text_state.original_text,
                                "history": [
                                    {
                                        "utterance": h.utterance,
                                        "edit_plan": h.edit_plan,
                                        "modified_text": h.modified_text,
                                    }
                                    for h in text_state.history
                                ],
                                "history_summary": text_state.history_summary,
                            },
                        )
                        LOGGER.info("Modification results sent to frontend")

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
            if streamer:
                streamer.stop()
            if openai_ws and not openai_ws.closed:
                await openai_ws.close()
            if not websocket.client_state.disconnected:
                await websocket.close()
            LOGGER.info("Cleanup completed successfully")
        except Exception as e:
            LOGGER.error(f"Error during cleanup: {e}")


@app.post("/api/generate-description")
async def generate_description(file: UploadFile = File(...)) -> dict:
    """画像から商品説明文を生成するエンドポイント

    Args:
        file (UploadFile): アップロードされた画像ファイル

    Returns:
        dict: 生成された商品説明文とエラー情報（存在する場合）を含む辞書

    """
    try:
        LOGGER.info("Starting product description generation...")

        # 画像データをBase64エンコード
        contents = await file.read()
        base64_image = base64.b64encode(contents).decode()

        # 商品説明文を生成
        generator = ProductDescriptionGenerator()
        result = generator(base64_image)

        if result.error_message:
            LOGGER.error(f"Error generating description: {result.error_message}")
            return {
                "success": False,
                "error": result.error_message,
            }

        LOGGER.info("Product description generated successfully")
        return {
            "success": True,
            "description": result.description,
        }

    except Exception as e:
        error_message = f"Error processing image: {e!s}"
        LOGGER.error(error_message)
        return {
            "success": False,
            "error": error_message,
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
