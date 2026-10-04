import pyttsx3


class TextToSpeech:

    def __init__(self):
        print("Loading text-to-speech...")

        self.rate = 175
        self.volume = 1.0

        print("Text-to-speech ready.")

    def speak(self, text):

        if not text:
            return

        engine = pyttsx3.init()

        engine.setProperty(
            "rate",
            self.rate
        )

        engine.setProperty(
            "volume",
            self.volume
        )

        engine.say(text)
        engine.runAndWait()

        engine.stop()


if __name__ == "__main__":

    tts = TextToSpeech()

    try:
        while True:

            text = input("Say something: ").strip()

            if text.lower() in {
                "exit",
                "quit",
                "stop",
            }:
                break

            tts.speak(text)

    except KeyboardInterrupt:
        pass