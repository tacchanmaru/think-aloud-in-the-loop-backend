import asyncio
import base64

from fastapi import FastAPI, File, Form, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.websockets import WebSocketDisconnect

from src.infra.sounddevice.audio_streamer import AudioStreamer
from src.infra.ws_transcriber.ws_transcriber import TranscriptionClient
from src.lib.env import ENV
from src.lib.logger import LOGGER
from src.usecase.generate_product_description import ProductDescriptionGenerator
from src.usecase.text_modification import (
    TextModificationUseCase,
)
from src.usecase.text_modification_types import (
    TextModificationHistory,
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

# グローバルな状態管理
text_states: dict[str, TextState] = {}
image_data: dict[str, str] = {}  # 新しい辞書を追加して画像データを保存


class TextUpdate(BaseModel):
    text: str
    user_id: str
    image_base64: str | None = None


@app.post("/api/display-text")
async def update_display_text(text_update: TextUpdate) -> dict:
    try:
        global text_states, image_data
        text_states[text_update.user_id] = TextState(
            original_text=text_update.text,
            current_text=text_update.text,
            history=[],
            history_summary="",
        )
        if text_update.image_base64:
            image_data[text_update.user_id] = text_update.image_base64
        LOGGER.info(f"Updating display text for user: {text_update.user_id}")
        return {"status": "success"}
    except Exception as e:
        LOGGER.error(f"Error updating display text: {e!s}")
        return {
            "status": "error",
            "message": str(e),
        }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    LOGGER.info("New WebSocket connection accepted")

    # Get user_id from query parameters
    user_id = websocket.query_params.get("user_id")
    if not user_id:
        LOGGER.warning("No user_id provided, closing connection")
        await websocket.close(code=1000, reason="No user_id provided")
        return

    LOGGER.info(f"WebSocket connection established for user: {user_id}")

    global text_states
    if user_id not in text_states:
        LOGGER.warning(f"No text has been set for user {user_id}, closing connection")
        await websocket.close(code=1000, reason="No text has been set")
        return

    text_state = text_states[user_id]

    transcriber = None
    openai_ws = None
    streamer = None

    try:
        LOGGER.info(f"Initializing transcription client for user {user_id}...")
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
                    LOGGER.debug(f"Waiting for audio data from user {user_id}...")
                    response = await openai_ws.recv()
                    data = await transcriber.parse_response(str(response))

                    if data["type"] == "delta":
                        pass  # 何もしない

                    elif data["type"] == "completed":
                        utterance = data["text"]
                        LOGGER.info(f"Transcription completed for user {user_id}: {utterance}")
                        LOGGER.info("Judging and planning text modification...")

                        # 判断と計画を生成
                        result = text_modification_usecase.judge_and_plan(
                            text_state.current_text,
                            utterance,
                            text_state.history_summary,  # 履歴サマリーを渡す
                        )

                        if not result.should_edit:  # should_editがFalseの場合
                            LOGGER.info(f"No changes needed for user {user_id}, continuing...")
                            await websocket.send_json(
                                {
                                    "type": "no_edit_needed",
                                    "utterance": utterance,
                                    "edit_plan": "修正は行いません。",
                                    "original_text": text_state.original_text,
                                    "history_summary": text_state.history_summary,
                                },
                            )
                            continue

                        if not result.edit_plan:  # edit_planがNoneの場合
                            LOGGER.warning(
                                f"No edit plan generated for user {user_id}, continuing...",
                            )
                            continue

                        # 修正計画をフロントエンドに送信
                        LOGGER.info(f"Edit plan for user {user_id}: {result.edit_plan}")
                        LOGGER.info(
                            f"Current constraints for user {user_id}:\n{text_state.history_summary}",
                        )
                        await websocket.send_json(
                            {
                                "type": "edit_plan",
                                "utterance": utterance,
                                "edit_plan": result.edit_plan,
                                "original_text": text_state.original_text,
                                "history_summary": text_state.history_summary,
                            },
                        )
                        LOGGER.info(f"Edit plan sent to frontend for user {user_id}")

                        # 修正を適用
                        LOGGER.info(f"Applying modification for user {user_id}...")
                        modified_text = text_modification_usecase.apply_modification(
                            text_state.current_text,
                            result.edit_plan,
                            text_state.history_summary,  # 履歴サマリーを渡す
                            image_data.get(user_id),  # 画像データを渡す
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

                        # 修正結果をフロントエンドに送信
                        LOGGER.info(f"Modified text for user {user_id}: {modified_text}")
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
                        LOGGER.info(f"Modification results sent to frontend for user {user_id}")

                        # history_summaryを更新
                        text_state.history_summary = (
                            text_modification_usecase.update_history_summary(
                                text_state.history,
                            )
                        )
                        LOGGER.info(
                            f"Updated constraints for user {user_id}:\n{text_state.history_summary}",
                        )

                except Exception as e:
                    LOGGER.error(f"Error in receive_and_modify for user {user_id}: {e}")
                    raise

        LOGGER.info(f"Starting audio processing for user {user_id}...")
        with streamer.start(openai_ws, loop):
            await receive_and_modify()

    except WebSocketDisconnect:
        LOGGER.info(f"WebSocket connection was disconnected by the client for user {user_id}")
    except Exception as e:
        LOGGER.error(f"Error occurred for user {user_id}: {e}")
        await websocket.close(code=1011, reason=str(e))
    finally:
        # Cleanup resources
        try:
            LOGGER.info(f"Cleaning up resources for user {user_id}...")
            if streamer:
                streamer.stop()
            if openai_ws and not openai_ws.closed:
                await openai_ws.close()
            if not websocket.client_state.disconnected:
                await websocket.close()
            LOGGER.info(f"Cleanup completed successfully for user {user_id}")
        except Exception as e:
            LOGGER.error(f"Error during cleanup for user {user_id}: {e}")


@app.post("/api/generate-description")
async def generate_description(
    file: UploadFile = File(...),
    user_id: str = Form(...),
) -> dict:
    """画像から商品説明文を生成するエンドポイント

    Args:
        file (UploadFile): アップロードされた画像ファイル
        user_id (str): ユーザーID

    Returns:
        dict: 生成された商品説明文とエラー情報（存在する場合）を含む辞書

    """
    try:
        LOGGER.info(f"Starting product description generation for user: {user_id}")

        # 画像データをBase64エンコード
        contents = await file.read()
        base64_image = base64.b64encode(contents).decode()

        # 商品説明文を生成
        generator = ProductDescriptionGenerator()
        result = generator(base64_image)

        if result.error_message:
            LOGGER.error(f"Error generating description for user {user_id}: {result.error_message}")
            return {
                "success": False,
                "error": result.error_message,
            }

        LOGGER.info(f"Product description generated successfully for user: {user_id}")
        return {
            "success": True,
            "description": result.description,
        }

    except Exception as e:
        error_message = f"Error processing image: {e!s}"
        LOGGER.error(f"Error for user {user_id}: {error_message}")
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
