import asyncio
import base64
import time

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
processing_flags: dict[str, bool] = {}  # 処理中フラグを管理する辞書を追加
utterance_buffers: dict[str, list[str]] = {}  # 完了した発話を格納するバッファ
last_complete_times: dict[str, float] = {}  # 最後の完了時刻を記録
last_delta_times: dict[str, float] = {}  # 最後のdelta受信時刻を記録


async def process_single_utterance(
    user_id: str,
    utterance: str,
    text_state: TextState,
    text_modification_usecase: TextModificationUseCase,
    websocket: WebSocket,
) -> bool:
    """単一の発話を処理する共通関数.

    Returns:
        bool: 修正が実行されたかどうか

    """
    try:
        LOGGER.info(f"Processing utterance for user {user_id}: {utterance}")

        # 処理開始をフロントエンドに通知
        await websocket.send_json(
            {
                "type": "processing_started",
                "utterance": utterance,
            },
        )

        # 判断・計画・修正を一つのステップで実行
        LOGGER.info(f"[{user_id}] Running judge_and_plan_and_modify in a separate thread...")
        result = await asyncio.to_thread(
            text_modification_usecase.judge_and_plan_and_modify,
            text_state.current_text,
            utterance,
            text_state.history_summary,
            image_data.get(user_id),
        )
        LOGGER.info(f"[{user_id}] judge_and_plan_and_modify finished.")

        if not result.should_edit:
            LOGGER.info(f"No changes needed for user {user_id}")
            await websocket.send_json(
                {
                    "type": "no_edit_needed",
                    "utterance": utterance,
                    "original_text": text_state.original_text,
                    "history_summary": text_state.history_summary,
                },
            )
            return False

        modified_text = result.modified_text
        if not modified_text or not result.plan:
            LOGGER.warning(f"No modified text or plan generated for user {user_id}")
            return False

        # 履歴を更新
        text_state.history.append(
            TextModificationHistory(
                utterance=utterance,
                edit_plan=result.plan,
                original_text=text_state.current_text,
                modified_text=modified_text,
            ),
        )
        text_state.current_text = modified_text

        # 修正結果をフロントエンドに送信
        await websocket.send_json(
            {
                "type": "text_modified",
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
        try:
            LOGGER.info(f"[{user_id}] Running update_history_summary in a separate thread...")
            new_summary = await asyncio.to_thread(
                text_modification_usecase.update_history_summary,
                text_state.history,
            )
            text_state.history_summary = new_summary
            LOGGER.info(f"[{user_id}] Updated constraints: {text_state.history_summary}")
        except Exception as e:
            LOGGER.error(f"Error updating history summary for user {user_id}: {e}")

        return True

    except Exception as e:
        LOGGER.error(f"Error processing utterance for user {user_id}: {e}")
        raise


def should_process_buffer(user_id: str) -> bool:
    """バッファを処理するべきかどうかを判定"""
    buffer = utterance_buffers.get(user_id, [])

    # 3つ以上溜まっている場合は処理
    if len(buffer) >= 3:
        return True

    # バッファが空の場合は処理しない
    if not buffer:
        return False

    # 最後のdeltaから2秒以上経過している場合は処理
    last_delta_time = last_delta_times.get(user_id, 0)
    current_time = time.time()

    return current_time - last_delta_time >= 2.0


def get_utterances_to_process(user_id: str) -> list[str]:
    """処理対象の発話を取得し、バッファから削除"""
    buffer = utterance_buffers.get(user_id, [])

    # バッファにあるものを全て取得
    utterances_to_process = buffer.copy()
    utterance_buffers[user_id] = []

    return utterances_to_process


async def check_and_process_buffered_utterances(
    user_id: str,
    text_state: TextState,
    text_modification_usecase: TextModificationUseCase,
    websocket: WebSocket,
) -> None:
    """バッファに溜まった発話があれば処理を開始"""
    # 処理中の場合は何もしない（同時実行を防ぐ）
    if processing_flags.get(user_id, False):
        LOGGER.debug(f"Processing already in progress for user {user_id}, skipping buffer check")
        return

    # 処理条件をチェック
    if not should_process_buffer(user_id):
        return

    # 処理対象の発話を取得
    utterances_to_process = get_utterances_to_process(user_id)
    if not utterances_to_process:
        return

    LOGGER.info(f"Processing buffered utterances for user {user_id}: {utterances_to_process}")

    # 複数の発話を結合
    combined_utterance = "".join(utterances_to_process)

    # 新しい処理を開始
    processing_flags[user_id] = True

    try:
        # 共通の処理関数を使用
        await process_single_utterance(
            user_id,
            combined_utterance,
            text_state,
            text_modification_usecase,
            websocket,
        )

    except Exception as e:
        LOGGER.error(f"Error processing buffered utterances for user {user_id}: {e}")
    finally:
        # 処理完了フラグをリセット
        processing_flags[user_id] = False


async def periodic_buffer_check(
    user_id: str,
    text_state: TextState,
    text_modification_usecase: TextModificationUseCase,
    websocket: WebSocket,
) -> None:
    """定期的にバッファをチェックして処理するタスク"""
    while True:
        try:
            await asyncio.sleep(0.1)  # 0.1秒ごとにチェック
            await check_and_process_buffered_utterances(
                user_id,
                text_state,
                text_modification_usecase,
                websocket,
            )
        except Exception as e:
            LOGGER.error(f"Error in periodic buffer check for user {user_id}: {e}")
            break


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

    global text_states, processing_flags, utterance_buffers, last_complete_times, last_delta_times
    if user_id not in text_states:
        LOGGER.warning(f"No text has been set for user {user_id}, closing connection")
        await websocket.close(code=1000, reason="No text has been set")
        return

    text_state = text_states[user_id]
    processing_flags[user_id] = False  # 初期状態は非処理中
    utterance_buffers[user_id] = []  # 発話バッファを初期化
    last_complete_times[user_id] = time.time()  # 最後の完了時刻を初期化
    last_delta_times[user_id] = time.time()  # 最後のdelta時刻を初期化

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

        # 定期バッファチェックタスクを開始
        buffer_check_task = asyncio.create_task(
            periodic_buffer_check(
                user_id,
                text_state,
                text_modification_usecase,
                websocket,
            ),
        )

        async def receive_and_modify() -> None:
            if not text_state:  # 型チェックのため再確認
                return

            # 音声処理開始
            LOGGER.info("Starting to receive audio transcriptions...")
            await asyncio.sleep(0.1)  # 短い初期化待機

            while True:
                try:
                    LOGGER.debug(f"Waiting for audio data from user {user_id}...")
                    response = await openai_ws.recv()
                    data = await transcriber.parse_response(str(response))

                    if data["type"] == "delta":
                        # delta受信時刻を記録
                        last_delta_times[user_id] = time.time()
                        LOGGER.debug(f"Delta received for user {user_id}")

                    elif data["type"] == "completed":
                        current_utterance = data["text"]
                        LOGGER.info(
                            f"Transcription completed for user {user_id}: {current_utterance}",
                        )

                        # 音声認識結果をフロントエンドに送信
                        await websocket.send_json(
                            {
                                "type": "transcription_completed",
                                "utterance": current_utterance,
                            },
                        )

                        # 発話をバッファに追加
                        if current_utterance.strip():  # 空文字列でない場合のみ追加
                            utterance_buffers[user_id].append(current_utterance)
                            last_complete_times[user_id] = time.time()
                            LOGGER.info(
                                f"Added utterance to buffer for user {user_id}. Buffer size: {len(utterance_buffers[user_id])}",
                            )

                except Exception as e:
                    LOGGER.error(f"Error in receive_and_modify for user {user_id}: {e}")
                    # エラー時にも処理完了フラグをリセット
                    processing_flags[user_id] = False
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
            # バックグラウンドタスクをキャンセル
            if "buffer_check_task" in locals():
                buffer_check_task.cancel()
                try:
                    await buffer_check_task
                except asyncio.CancelledError:
                    pass
            if streamer:
                streamer.stop()
            if openai_ws:
                try:
                    await openai_ws.close()
                except Exception:
                    pass
            try:
                await websocket.close()
            except Exception:
                pass
            LOGGER.info(f"Cleanup completed successfully for user {user_id}")
        except Exception as e:
            LOGGER.error(f"Error during cleanup for user {user_id}: {e}")


@app.post("/api/generate-description")
async def generate_description(
    file: UploadFile = File(...),
    user_id: str = Form(...),
) -> dict:
    """画像から商品説明文を生成するエンドポイント.

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
