import numpy as np
from openwakeword.model import Model

# pyrefly: ignore [missing-import]
from app.voice.mic import MicStream

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

        print("Wake-word model loaded.")
        print(f"Available models: {list(self.model.models.keys())}")

    # ---------------------------------------------------------
    def reset(self):
        """Forget recent audio so Jarvis's own voice can't re-trigger."""

        try:
            reset = getattr(self.model, "reset", None)

            if callable(reset):
                reset()

            buffers = getattr(self.model, "prediction_buffer", None)

            if isinstance(buffers, dict):
                for buffer in buffers.values():
                    buffer.clear()

        except Exception:
            pass

    # ---------------------------------------------------------
    def listen(self, mic=None):
        """
        Block until the wake word is heard.

        Reads from the shared mic WITHOUT closing it, so the next
        words ("...open Chrome") are still waiting in the buffer.
        """

        own = mic is None

        if own:
            mic = MicStream()
            mic.start()

        print(f"\nListening for '{WAKE_WORD.replace('_', ' ')}'... (Ctrl+C to stop)")

        try:
            while True:

                audio = mic.read(timeout=1.0)

                if audio is None:
                    continue

                audio = np.asarray(audio, dtype=np.int16)

                prediction = self.model.predict(audio)
                score = prediction.get(WAKE_WORD, 0.0)

                if score >= THRESHOLD:
                    print(f"Wake word detected! score={score:.2f}")
                    return True

        finally:
            if own:
                mic.stop()


if __name__ == "__main__":

    detector = WakeWordDetector()

    with MicStream() as mic:

        try:
            while True:
                detector.listen(mic)
                detector.reset()
                print("JARVIS: Yes?")
        except KeyboardInterrupt:
            print("\nJARVIS wake-word detector stopped.")
