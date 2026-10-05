import math
import os
import time
from collections import deque

import numpy as np
from faster_whisper import WhisperModel

# pyrefly: ignore [missing-import]
from app.voice.mic import (
    BLOCK_SECONDS,
    SAMPLE_RATE,
    MicStream,
    rms,
)

# ============================================================
# SETTINGS  (override with JARVIS_* variables in .env)
# ============================================================

# "base.en" is ~3x faster than "small". If it mishears you, try
# JARVIS_WHISPER_MODEL=small.en  (still English-only, still faster
# than the old multilingual "small").
WHISPER_MODEL = os.getenv("JARVIS_WHISPER_MODEL", "base.en")

LANGUAGE = "en"

# Hints Whisper toward the words you actually say to Jarvis.
INITIAL_PROMPT = (
    "Commands for a computer assistant called Jarvis: open Chrome, "
    "search Google, YouTube, WhatsApp, Notepad, VS Code, volume up, "
    "volume down, lock the computer, close it."
)

# ---- end-of-speech detection (all in 80 ms blocks) ----------
END_SILENCE_MS = 800            # silence that ends a command
NO_SPEECH_TIMEOUT_S = 5.0       # give up if nothing is said
MAX_UTTERANCE_S = 12.0          # hard cap on one command
START_BLOCKS = 2                # loud blocks in a row = speech began
PREROLL_BLOCKS = 4              # keep audio just before speech began
MIN_SPEECH_BLOCKS = 3           # shorter than this = a click/cough
STALL_READS = 5                 # mic gave nothing this many times

# Never treat anything quieter than this as speech (int16 units).
MIN_RMS = float(os.getenv("JARVIS_VAD_RMS", "300"))
NOISE_RATIO = 3.0               # threshold = noise floor x 3

END_SILENCE_BLOCKS = math.ceil(END_SILENCE_MS / 1000 / BLOCK_SECONDS)
NO_SPEECH_BLOCKS = math.ceil(NO_SPEECH_TIMEOUT_S / BLOCK_SECONDS)
MAX_BLOCKS = math.ceil(MAX_UTTERANCE_S / BLOCK_SECONDS)

# Phrases Whisper invents out of silence/noise.
_HALLUCINATIONS = {
    "you", "thank you", "thanks", "thanks for watching", "bye",
    "okay", "so", "the", "uh", "um",
}


class SpeechToText:

    def __init__(self):

        print("Loading speech-to-text model...")

        self.model = WhisperModel(
            WHISPER_MODEL,
            device="cpu",
            compute_type="int8",
        )

        # Loudness above which a block counts as speech.
        self.threshold = MIN_RMS

        print(f"Speech-to-text ready ({WHISPER_MODEL}).")

    # ---------------------------------------------------------
    # SETUP
    # ---------------------------------------------------------
    def warm_up(self):
        """First transcription has one-time overhead; pay it now."""

        silence = np.zeros(SAMPLE_RATE // 2, dtype=np.float32)

        try:
            segments, _ = self.model.transcribe(
                silence,
                language=LANGUAGE,
                beam_size=1,
            )
            list(segments)
        except Exception as error:
            print(f"Speech warm-up skipped: {error}")

    def calibrate(self, mic, seconds=1.0):
        """
        Measure room noise once, so the 'is someone talking' threshold
        fits this microphone and room.  Stay quiet for a second.
        """

        if os.getenv("JARVIS_VAD_RMS"):
            self.threshold = MIN_RMS      # user fixed it manually
            return self.threshold

        mic.flush()

        levels = []
        wanted = int(seconds / BLOCK_SECONDS)
        misses = 0

        while len(levels) < wanted and misses < STALL_READS:

            block = mic.read(timeout=1.0)

            if block is None:
                misses += 1
                continue

            levels.append(rms(block))

        if levels:
            noise = float(np.median(levels))
            self.threshold = max(MIN_RMS, noise * NOISE_RATIO)

        print(f"Mic noise level {self.threshold / NOISE_RATIO:.0f}, "
              f"speech threshold {self.threshold:.0f}.")

        return self.threshold

    # ---------------------------------------------------------
    # RECORD UNTIL THE USER STOPS TALKING
    # ---------------------------------------------------------
    def record_utterance(self, mic):
        """
        Read blocks from the shared mic until the speaker pauses.

        Returns float32 audio, or None if nobody spoke.
        """

        threshold = self.threshold
        keep_threshold = threshold * 0.6     # softer word endings count

        preroll = deque(maxlen=PREROLL_BLOCKS)
        collected = []

        started = False
        loud_run = 0
        speech_blocks = 0
        silence_run = 0
        total = 0
        misses = 0

        while True:

            block = mic.read(timeout=1.0)

            if block is None:
                misses += 1
                if misses >= STALL_READS:
                    break
                continue

            misses = 0
            total += 1
            level = rms(block)

            # ------------- waiting for speech to begin -------------
            if not started:

                preroll.append(block)

                if level > threshold:
                    loud_run += 1
                else:
                    loud_run = 0

                if loud_run >= START_BLOCKS:
                    started = True
                    collected = list(preroll)
                    speech_blocks = loud_run
                    silence_run = 0

                elif total >= NO_SPEECH_BLOCKS:
                    return None

                continue

            # ------------------- inside speech --------------------
            collected.append(block)

            if level > keep_threshold:
                silence_run = 0
                speech_blocks += 1
            else:
                silence_run += 1

            if silence_run >= END_SILENCE_BLOCKS:

                if speech_blocks >= MIN_SPEECH_BLOCKS:
                    break

                # too short: it was a click, keep waiting
                started = False
                loud_run = 0
                collected = []
                preroll.clear()

                if total >= NO_SPEECH_BLOCKS:
                    return None

                continue

            if len(collected) >= MAX_BLOCKS:
                break

        if not started or speech_blocks < MIN_SPEECH_BLOCKS:
            return None

        audio = np.concatenate(collected).astype(np.float32) / 32768.0

        return audio

    # ---------------------------------------------------------
    # TRANSCRIBE
    # ---------------------------------------------------------
    def transcribe(self, audio):

        segments, info = self.model.transcribe(
            audio,
            language=LANGUAGE,
            beam_size=1,
            vad_filter=True,
            condition_on_previous_text=False,
            without_timestamps=True,
            initial_prompt=INITIAL_PROMPT,
        )

        text = " ".join(
            segment.text.strip()
            for segment in segments
        ).strip()

        # Whisper sometimes "hears" a short phrase in pure noise.
        seconds = len(audio) / SAMPLE_RATE
        plain = "".join(
            ch for ch in text.lower() if ch.isalpha() or ch == " "
        ).strip()

        if seconds < 2.5 and plain in _HALLUCINATIONS:
            return ""

        return text

    # ---------------------------------------------------------
    # CONVENIENCE
    # ---------------------------------------------------------
    def listen_and_transcribe(self, mic=None):

        own = mic is None

        if own:
            mic = MicStream()
            mic.start()

        try:
            print("\nListening...")
            audio = self.record_utterance(mic)

            if audio is None:
                return ""

            return self.transcribe(audio)

        finally:
            if own:
                mic.stop()


if __name__ == "__main__":

    stt = SpeechToText()

    with MicStream() as mic:

        stt.warm_up()
        stt.calibrate(mic)

        try:
            while True:
                started = time.perf_counter()
                text = stt.listen_and_transcribe(mic)
                print(f"You: {text}   ({time.perf_counter() - started:.1f}s)")

                if text.lower().strip(" .!?") in {"exit", "quit", "stop"}:
                    break

        except KeyboardInterrupt:
            print("\nSpeech-to-text stopped.")
