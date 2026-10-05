import os

# pyrefly: ignore [missing-import]
from app.voice.utils import clean_for_speech

# SAPI speech rate: -10 (slow) .. 10 (fast). Old pyttsx3 175 wpm ~ -1.
try:
    RATE = int(os.getenv("JARVIS_TTS_RATE", "-1"))
except ValueError:
    RATE = -1

# SAPI flags
_ASYNC = 1
_PURGE_BEFORE_SPEAK = 2
_NOT_XML = 16


class TextToSpeech:
    """
    Windows speech through one reusable SAPI voice (pywin32 is already
    a dependency).  The old code created a fresh pyttsx3 engine for
    every sentence, which added a noticeable delay each time.

    If SAPI isn't available, falls back to the old pyttsx3 behaviour.
    """

    def __init__(self):

        print("Loading text-to-speech...")

        self.rate = 175          # only used by the pyttsx3 fallback
        self.volume = 1.0
        self._sapi = None

        try:
            import win32com.client

            self._sapi = win32com.client.Dispatch("SAPI.SpVoice")
            self._sapi.Rate = RATE
            self._sapi.Volume = 100

        except Exception:
            self._sapi = None

        mode = "SAPI" if self._sapi is not None else "pyttsx3"
        print(f"Text-to-speech ready ({mode}).")

    # ---------------------------------------------------------
    def speak(self, text, wait=True):

        text = clean_for_speech(text)

        if not text:
            return

        if self._sapi is not None:

            try:
                self._sapi.Speak(
                    text,
                    _ASYNC | _PURGE_BEFORE_SPEAK | _NOT_XML,
                )

                if wait:
                    self._sapi.WaitUntilDone(-1)

                return

            except Exception:
                # fall through to the fallback below
                pass

        self._speak_pyttsx3(text)

    def stop(self):
        """Cut off speech that is in progress."""

        if self._sapi is not None:
            try:
                self._sapi.Speak("", _ASYNC | _PURGE_BEFORE_SPEAK)
            except Exception:
                pass

    # ---------------------------------------------------------
    def _speak_pyttsx3(self, text):

        import pyttsx3

        engine = pyttsx3.init()
        engine.setProperty("rate", self.rate)
        engine.setProperty("volume", self.volume)
        engine.say(text)
        engine.runAndWait()
        engine.stop()


if __name__ == "__main__":

    tts = TextToSpeech()

    try:
        while True:
            text = input("Say something: ").strip()

            if text.lower() in {"exit", "quit", "stop"}:
                break

            tts.speak(text)

    except KeyboardInterrupt:
        pass
