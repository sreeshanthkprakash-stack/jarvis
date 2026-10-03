# pyrefly: ignore [missing-import]
from app.voice.wake_word import WakeWordDetector
# pyrefly: ignore [missing-import]
from app.voice.speech_to_text import SpeechToText
# pyrefly: ignore [missing-import]
from app.router import JarvisRouter
# pyrefly: ignore [missing-import]
from app.brain import JarvisBrain
# pyrefly: ignore [missing-import]
from app.config import SYSTEM_PROMPT


def main():
    print("Starting JARVIS...")

    # --------------------------------------------------------
    # INITIALIZE BRAIN
    # --------------------------------------------------------

    brain = JarvisBrain(
        SYSTEM_PROMPT
    )

    # --------------------------------------------------------
    # INITIALIZE ROUTER
    # --------------------------------------------------------

    router = JarvisRouter(
        brain
    )

    # --------------------------------------------------------
    # INITIALIZE VOICE
    # --------------------------------------------------------

    wake_word = WakeWordDetector()
    stt = SpeechToText()

    print()
    print("=" * 50)
    print("        JARVIS VOICE SYSTEM")
    print("=" * 50)
    print("Say: Hey Jarvis")
    print("Say 'exit' to stop.")
    print("=" * 50)

    # --------------------------------------------------------
    # VOICE LOOP
    # --------------------------------------------------------

    while True:

        # Wait for wake word
        wake_word.listen()

        print("JARVIS: Yes?")

        # Listen for command
        command = stt.listen_and_transcribe(
            seconds=5
        )

        if not command:
            print("JARVIS: I didn't hear a command.")
            continue

        print(f"You: {command}")

        # Exit
        if command.lower() in {
            "exit",
            "quit",
            "stop",
            "shutdown",
        }:
            print("JARVIS: Shutting down.")
            break

        # Send command through existing router
        print("JARVIS: ", end="", flush=True)

        response = router.handle(
            command
        )

        if response:
            print(response)

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