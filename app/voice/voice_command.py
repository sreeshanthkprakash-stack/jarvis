# pyrefly: ignore [missing-import]
from app.voice.wake_word import WakeWordDetector
# pyrefly: ignore [missing-import]
from app.voice.speech_to_text import SpeechToText
# pyrefly: ignore [missing-import]
from app.voice.text_to_speech import TextToSpeech

# pyrefly: ignore [missing-import]
from app.brain import JarvisBrain
# pyrefly: ignore [missing-import]
from app.config import SYSTEM_PROMPT
# pyrefly: ignore [missing-import]
from app.router import JarvisRouter


def main():

    print("=" * 50)
    print("        JARVIS VOICE SYSTEM")
    print("=" * 50)

    brain = JarvisBrain(
        SYSTEM_PROMPT
    )

    router = JarvisRouter(
        brain
    )

    wake_word = WakeWordDetector()
    stt = SpeechToText()
    tts = TextToSpeech()

    print()
    print("JARVIS voice system ready.")
    print("Say: Hey Jarvis")
    print("Say 'exit' to stop.")
    print("=" * 50)

    while True:

        # ----------------------------------------------------
        # WAIT FOR WAKE WORD
        # ----------------------------------------------------

        wake_word.listen()

        print("\nJARVIS: Yes?")

        # Don't speak Yes? yet.
        # We first want to make sure the command is captured.

        # ----------------------------------------------------
        # SPEECH TO TEXT
        # ----------------------------------------------------

        command = stt.listen_and_transcribe(
            seconds=5
        )

        if not command:
            print("JARVIS: I didn't hear a command.")
            tts.speak("I didn't hear a command.")
            continue

        print(f"You: {command}")

        # ----------------------------------------------------
        # EXIT
        # ----------------------------------------------------

        if command.lower() in {
            "exit",
            "quit",
            "stop",
            "shutdown",
        }:
            tts.speak("Shutting down.")
            break

        # ----------------------------------------------------
        # ROUTER
        # ----------------------------------------------------

        print("JARVIS: ", end="", flush=True)

        response = router.handle(command)

        # ----------------------------------------------------
        # SPEAK RESPONSE
        # ----------------------------------------------------

        if isinstance(response, str) and response.strip():

            tts.speak(
                response.strip()
            )

        print()


if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:
        print("\nJARVIS: Shutting down.")

    except Exception as error:
        print(
            f"\nJARVIS ERROR: {error}"
        )