import asyncio
import base64
import json

import numpy as np

import sounddevice as sd


class AudioStreamer:
    def __init__(self, samplerate: int, blocksize: int, channels: int) -> None:
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.channels = channels
        self.websocket = None
        self.event_loop = None
        self.stream = None

    def start(self, websocket, event_loop) -> sd.InputStream:
        self.websocket = websocket
        self.event_loop = event_loop

        self.stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            blocksize=self.blocksize,
            dtype="float32",
            callback=self._callback,
        )
        return self.stream

    def stop(self) -> None:
        """Stop the audio stream and cleanup resources."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.websocket = None
        self.event_loop = None

    def _callback(self, indata, _frames, _time_info, status) -> None:
        if status:
            print("[SoundDevice Status]", status)

        if not self.websocket or not self.event_loop:
            return

        pcm_data = (indata * 32767).astype(np.int16).tobytes()
        base64_audio = base64.b64encode(pcm_data).decode("utf-8")

        audio_event = {
            "type": "input_audio_buffer.append",
            "audio": base64_audio,
        }

        asyncio.run_coroutine_threadsafe(
            self.websocket.send(json.dumps(audio_event)),
            self.event_loop,
        )
