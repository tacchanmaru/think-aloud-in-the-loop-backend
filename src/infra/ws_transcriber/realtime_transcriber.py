"""gpt-4o-realtime-preview-2025-06-03を使用したリアルタイム転写クライアント."""

import json
import time
from typing import Any

import websockets

from src.lib.logger import LOGGER


class RealtimeTranscriptionClient:
    """gpt-4o-realtime-preview-2025-06-03を使用したリアルタイム転写クライアント."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.ws_url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2025-06-03"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1",
        }
        self.session_id: str | None = None

    async def connect(self) -> Any:
        """既存のTranscriptionClient.connect()と同じインターフェース."""
        try:
            LOGGER.info("🔌 Realtime APIに接続中...")
            websocket = await websockets.connect(self.ws_url, additional_headers=self.headers)
            LOGGER.info("✅ Realtime API接続成功")
            return websocket
        except Exception as e:
            LOGGER.error(f"❌ Realtime API接続失敗: {e}")
            raise

    async def initialize_session(
        self,
        websocket: Any,
        model: str = "gpt-4o-transcribe",
        silence_duration_ms: int = 500,
    ) -> None:
        """既存のTranscriptionClient.initialize_session()と同じインターフェース."""
        try:
            # セッション作成の確認
            response = await websocket.recv()
            response_data = json.loads(response)
            LOGGER.info(f"Initial response: {response_data.get('type', 'unknown')}")

            if response_data.get("type") == "error":
                raise Exception(f"OpenAI API error: {response_data}")

            if response_data.get("type") == "session.created":
                self.session_id = response_data.get("session", {}).get("id")
                LOGGER.info(f"✅ セッション作成成功: {self.session_id}")

                # 日本語リアルタイム転写用の設定
                update_message = {
                    "type": "session.update",
                    "session": {
                        "modalities": ["text"],
                        "input_audio_format": "pcm16",
                        "temperature": 0.6,
                        "tool_choice": "none",
                        "instructions": "あなたは日本語の音声転写アシスタントです。日本語の音声を正確に文字起こししてください。",  # noqa: E501
                        "input_audio_transcription": {
                            "model": model,  # 最新の高精度モデル
                            "language": "ja",
                        },
                        "turn_detection": {
                            "type": "server_vad",
                            "threshold": 0.5,
                            "silence_duration_ms": silence_duration_ms,
                            "prefix_padding_ms": 300,
                        },
                    },
                }

                await websocket.send(json.dumps(update_message))
                LOGGER.info("📤 リアルタイム転写設定を送信")

                # 設定更新の確認
                update_response = await websocket.recv()
                update_data = json.loads(update_response)

                if update_data.get("type") == "session.updated":
                    turn_detection = update_data.get("session", {}).get("turn_detection", {})
                    LOGGER.info("🎌 日本語リアルタイム転写設定完了:")
                    LOGGER.info(f"   - 無音検出時間: {turn_detection.get('silence_duration_ms')}ms")
                    LOGGER.info(f"   - 検出閾値: {turn_detection.get('threshold')}")
                    LOGGER.info(f"   - バッファ時間: {turn_detection.get('prefix_padding_ms')}ms")
                else:
                    LOGGER.warning(f"⚠️ 設定更新レスポンス: {update_data}")

        except Exception as e:
            LOGGER.error(f"❌ セッション初期化失敗: {e}")
            raise

    async def parse_response(self, raw: str) -> dict[str, Any]:
        """既存のTranscriptionClient.parse_response()と同じインターフェース."""
        try:
            data = json.loads(raw)
            response_type = data.get("type", "")

            # Deltaレスポンス: リアルタイム部分転写
            if response_type == "conversation.item.input_audio_transcription.delta":
                delta_text = data.get("delta", "")
                LOGGER.debug(f"⚡ Delta: '{delta_text}'")
                return {"type": "delta", "text": delta_text, "timestamp": time.time()}

            # 完了レスポンス: 最終転写結果
            if response_type == "conversation.item.input_audio_transcription.completed":
                transcript = data.get("transcript", "")
                LOGGER.info(f"✅ 転写完了: '{transcript}'")
                return {"type": "completed", "text": transcript, "timestamp": time.time()}

            # VAD状態監視
            if response_type == "input_audio_buffer.speech_started":
                LOGGER.debug("🎤 音声検出開始")
                return {"type": "speech_started", "text": "", "timestamp": time.time()}

            if response_type == "input_audio_buffer.speech_stopped":
                LOGGER.debug("🔇 音声検出終了")
                return {"type": "speech_stopped", "text": "", "timestamp": time.time()}

            # エラーハンドリング
            if response_type == "error":
                error_msg = data.get("error", {}).get("message", "不明なエラー")
                LOGGER.error(f"❌ API エラー: {error_msg}")
                return {"type": "error", "text": "", "error": error_msg, "timestamp": time.time()}

            # その他のレスポンス
            LOGGER.debug(f"📄 その他のレスポンス: {response_type}")
            return {
                "type": "unknown",
                "text": "",
                "raw_type": response_type,
                "timestamp": time.time(),
            }

        except json.JSONDecodeError as e:
            LOGGER.error(f"❌ JSON解析エラー: {e}")
            return {
                "type": "error",
                "text": "",
                "error": f"JSON解析エラー: {e}",
                "timestamp": time.time(),
            }
        except Exception as e:
            LOGGER.error(f"❌ レスポンス解析エラー: {e}")
            return {
                "type": "error",
                "text": "",
                "error": f"解析エラー: {e}",
                "timestamp": time.time(),
            }

    async def receive_loop(self, websocket: Any) -> None:
        """既存のTranscriptionClient.receive_loop()と同じインターフェース."""
        LOGGER.info("👂 レスポンス受信ループ開始")

        while True:
            try:
                response = await websocket.recv()
                parsed = await self.parse_response(str(response))

                if parsed["type"] == "delta":
                    print(parsed["text"], end="", flush=True)
                elif parsed["type"] == "completed":
                    print(f"\nUser: {parsed['text']}")
                elif parsed["type"] == "error":
                    LOGGER.error(f"エラー: {parsed.get('error', '不明')}")
                    break

            except Exception as e:
                LOGGER.error(f"❌ 受信ループエラー: {e}")
                break


# 後方互換性のためのエイリアス
TranscriptionClient = RealtimeTranscriptionClient
