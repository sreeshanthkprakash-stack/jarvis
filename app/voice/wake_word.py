import queue
import sys

import numpy as np
import sounddevice as sd
from openwakeword.model import Model


SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 1280

# Your microphone
MICROPHONE_DEVICE = 1

# Built-in OpenWakeWord model
WAKE_WORD = "hey_jarvis"

# Detection threshold
THRESHOLD = 0.5


class WakeWordDetector:

    def __init__(self):
        print("Loading wake-word model...")

        self.model = Model(
            wakeword_model_paths=[],
            vad_threshold=0
        )

        self.audio_queue = queue.Queue()

        print("Wake-word model loaded.")
        print(f"Available models: {list(self.model.models.keys())}")
        print(f"Listening for: {WAKE_WORD}")

    def _audio_callback(self, indata, frames, time, status):

        if status:
            print(f"\nAudio status: {status}", file=sys.stderr)

        audio = indata[:, 0].copy()

        self.audio_queue.put(audio)

    def listen(self):

        print()
        print("=" * 50)
        print("JARVIS Wake Word Detector")
        print("=" * 50)
        print(f"Say: {WAKE_WORD}")
        print("Listening...")
        print("Press Ctrl+C to stop.")
        print("=" * 50)

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            device=MICROPHONE_DEVICE,
            channels=CHANNELS,
            dtype="int16",
            callback=self._audio_callback,
        ):

            while True:

                audio = self.audio_queue.get()

                audio = np.asarray(
                    audio,
                    dtype=np.int16
                )

                prediction = self.model.predict(audio)

                score = prediction.get(WAKE_WORD, 0.0)

                if score >= THRESHOLD:

                    print()
                    print(
                        f"Wake word detected! "
                        f"score={score:.2f}"
                    )

                    return True


if __name__ == "__main__":

    detector = WakeWordDetector()

    try:

        while True:

            detector.listen()

            print("JARVIS: Yes?")

    except KeyboardInterrupt:

        print()
        print("JARVIS wake-word detector stopped.")