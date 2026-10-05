"""
One microphone stream shared by the wake-word detector and the
speech-to-text recorder.

Why: opening/closing the mic between "Hey Jarvis" and the command
takes time and drops the first words. A single always-open stream
fixes both.
"""

import os
import queue

import numpy as np
import sounddevice as sd

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# Load .env early so JARVIS_* settings work for every voice module.
load_dotenv()

SAMPLE_RATE = 16000
BLOCK_SIZE = 1280          # 80 ms per block (what openWakeWord expects)
BLOCK_SECONDS = BLOCK_SIZE / SAMPLE_RATE


def _env_int(name, default):
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


# Which microphone to use. To list devices:  python -m sounddevice
# Override without editing code:  JARVIS_MIC=3  in .env
MICROPHONE_DEVICE = _env_int("JARVIS_MIC", 1)


class MicStream:

    def __init__(
        self,
        device=MICROPHONE_DEVICE,
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        max_blocks=400,        # ~32 s of audio kept at most
    ):
        self.device = device
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.queue = queue.Queue(maxsize=max_blocks)
        self._stream = None

    # ---------------------------------------------------------
    def _callback(self, indata, frames, time_info, status):

        block = indata[:, 0].copy()

        try:
            self.queue.put_nowait(block)
        except queue.Full:
            # drop the oldest block, keep the newest
            try:
                self.queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.queue.put_nowait(block)
            except queue.Full:
                pass

    def start(self):

        if self._stream is not None:
            return

        self._stream = sd.InputStream(
            samplerate=self.samplerate,
            blocksize=self.blocksize,
            device=self.device,
            channels=1,
            dtype="int16",
            callback=self._callback,
        )

        self._stream.start()

    def stop(self):

        stream, self._stream = self._stream, None

        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass

    # ---------------------------------------------------------
    def read(self, timeout=1.0):
        """Next audio block (int16 numpy array), or None on timeout."""

        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def flush(self):
        """Throw away buffered audio (e.g. Jarvis's own voice)."""

        while True:
            try:
                self.queue.get_nowait()
            except queue.Empty:
                return

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc):
        self.stop()


def rms(block):
    """Loudness of an int16 block."""

    block = np.asarray(block, dtype=np.float32)

    if block.size == 0:
        return 0.0

    return float(np.sqrt(np.mean(block * block)))
