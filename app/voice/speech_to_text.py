import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel


SAMPLE_RATE = 16000
CHANNELS = 1
MICROPHONE_DEVICE = 1

# Start with the small model.
# We can change this later depending on speed/accuracy.
WHISPER_MODEL = "small"


class SpeechToText:

    def __init__(self):
        print("Loading speech-to-text model...")

        self.model = WhisperModel(
            WHISPER_MODEL,
            device="cpu",
            compute_type="int8",
        )

        print("Speech-to-text model ready.")

    def record(self, seconds=5):

        print()
        print(f"Listening for {seconds} seconds...")

        audio = sd.rec(
            int(seconds * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            device=MICROPHONE_DEVICE,
        )

        sd.wait()

        return audio.flatten()

    def transcribe(self, audio):

        segments, info = self.model.transcribe(
            audio,
            language="en",
            beam_size=5,
        )

        text = " ".join(
            segment.text.strip()
            for segment in segments
        )

        return text.strip()

    def listen_and_transcribe(self, seconds=5):

        audio = self.record(seconds)

        text = self.transcribe(audio)

        return text


if __name__ == "__main__":

    stt = SpeechToText()

    try:

        while True:

            text = stt.listen_and_transcribe(5)

            print()
            print(f"You: {text}")

            if text.lower() in {"exit", "quit", "stop"}:
                break

    except KeyboardInterrupt:

        print()
        print("Speech-to-text stopped.")