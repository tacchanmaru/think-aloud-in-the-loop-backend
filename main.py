import asyncio

from src.infra.gpt.modify_text import ModifyText
from src.infra.sounddevice.audio_streamer import AudioStreamer
from src.infra.ws_transcriber.ws_transcriber import TranscriptionClient
from src.lib.env import ENV

SAMPLING_RATE = 24000
BLOCK_SIZE = 2048
CHANNELS = 1
API_KEY = ENV.get("OPENAI_API_KEY")  # あなたのAPIキー

# 画面上に表示されている仮のテキスト（固定でも可、将来的には更新可能）
DISPLAY_TEXT = """
シンプル無地トートバッグ

商品の説明

【商品名】
シンプル無地トートバッグ

【サイズ】
約30cm×35cm（持ち手含まず）

【特徴】
・ナチュラルな生成りカラー
・丈夫なキャンバス素材
・エコバッグや普段使いに最適

【状態】
新品未使用

【注意事項】
・自宅保管のため、気になる方はご遠慮ください
・折りたたんで発送いたします

"""


async def main():
    transcriber = TranscriptionClient(api_key=API_KEY)
    websocket = await transcriber.connect()
    await transcriber.initialize_session(websocket)

    loop = asyncio.get_running_loop()

    streamer = AudioStreamer(
        samplerate=SAMPLING_RATE,
        blocksize=BLOCK_SIZE,
        channels=CHANNELS,
    )

    modifier = ModifyText()  # ← 修正ユースケースを初期化

    # transcription を受け取りながら text を修正して表示
    async def receive_and_modify():
        buffer = ""
        i = 0
        while True:
            response = await websocket.recv()
            data = await transcriber.parse_response(response)

            # delta で発話途中の文字をバッファに貯める
            if data["type"] == "delta":
                buffer += data["text"]

            # completed で1ターンの発話が完了したら、text修正
            elif data["type"] == "completed":
                utterance = data["text"]
                print(f"\n🗣️ 発話内容: {utterance}")
                if i == 0:
                    modified = modifier(DISPLAY_TEXT, utterance)
                else:
                    modified = modifier(modified, utterance)
                i += 1
                print(f"📝 修正後のテキスト:\n{modified}\n")
                buffer = ""

    with streamer.start(websocket, loop):
        print("🎙️ リアルタイム文字起こしを開始します（Ctrl+Cで停止）")
        try:
            await receive_and_modify()
        except KeyboardInterrupt:
            print("🔚 終了します。")


if __name__ == "__main__":
    asyncio.run(main())
