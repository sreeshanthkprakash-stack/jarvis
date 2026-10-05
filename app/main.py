# pyrefly: ignore [missing-import]
import argparse
import re

# pyrefly: ignore [missing-import]
from app.brain import JarvisBrain

# pyrefly: ignore [missing-import]
from app.config import SYSTEM_PROMPT
# pyrefly: ignore [missing-import]
from app.router import JarvisRouter


TEXT_EXIT_WORDS = {
    "exit",
    "quit",
    "shutdown",
}

# Whisper adds punctuation/capitals ("Exit."), so voice commands are
# normalised before being compared with this set.
VOICE_EXIT_WORDS = {
    "exit",
    "quit",
    "stop",
    "shutdown",
    "shut down",
}

# Long answers are printed in full but only the start is spoken.
MAX_SPOKEN_CHARS = 400


# ============================================================
# SHARED HELPERS
# ============================================================

def build_router():
    """Create the brain + router (this is also where the model warms up)."""

    brain = JarvisBrain(
        SYSTEM_PROMPT
    )

    return JarvisRouter(
        brain
    )


def speakable(text):
    """Clean a response so the TTS engine doesn't read symbols or URLs."""

    text = str(text)

    text = re.sub(r"https?://\S+", "a link", text)
    text = re.sub(r"[*_`#>|~]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) > MAX_SPOKEN_CHARS:

        cut = text[:MAX_SPOKEN_CHARS]
        end = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))

        text = cut[: end + 1] if end > 80 else cut

    return text


def ready_beep():
    """Short beep = 'I'm listening now' (Windows only, silent elsewhere)."""

    try:
        import winsound

        winsound.Beep(880, 80)

    except Exception:
        pass


# ============================================================
# TEXT LOOP  (python -m app.main)
# ============================================================

def run_text(router):

    print("Type 'exit' to shut down.\n")

    while True:

        try:
            user_input = input(
                "You: "
            ).strip()

            # Ignore empty input.
            if not user_input:
                continue

            # ------------------------------------------------
            # EXIT COMMANDS
            # ------------------------------------------------

            if user_input.lower() in TEXT_EXIT_WORDS:
                print(
                    "\nJARVIS: Shutting down. Goodbye."
                )
                break

            # ------------------------------------------------
            # PROCESS COMMAND
            # ------------------------------------------------

            print(
                "\nJARVIS: ",
                end="",
                flush=True,
            )

            response = router.handle(
                user_input
            )

            # ------------------------------------------------
            # DISPLAY RESPONSE
            # ------------------------------------------------

            if response:
                print(response)

            print()

        except KeyboardInterrupt:
            print(
                "\n\nJARVIS: Shutting down."
            )
            break

        except Exception as error:
            print(
                f"\n\nJARVIS ERROR: {error}\n"
            )


# ============================================================
# VOICE LOOP  (python -m app.main --voice)
#
#   wake word -> record until silence -> transcribe
#             -> router -> print + speak the reply -> repeat
# ============================================================

def run_voice(router):

    # Imported here so typed mode works even if the audio
    # libraries (sounddevice, openwakeword, ...) aren't installed.
    # pyrefly: ignore [missing-import]
    from app.voice.wake_word import WakeWordDetector
    # pyrefly: ignore [missing-import]
    from app.voice.speech_to_text import SpeechToText
    # pyrefly: ignore [missing-import]
    from app.voice.text_to_speech import TextToSpeech

    wake_word = WakeWordDetector()
    stt = SpeechToText()
    tts = TextToSpeech()

    print()
    print("JARVIS voice system ready.")
    print("Say: Hey Jarvis   (then speak your command after the beep)")
    print("Say 'exit' or press Ctrl+C to stop.")
    print("=" * 50)

    while True:

        try:

            # ------------------------------------------------
            # 1. WAIT FOR WAKE WORD
            # ------------------------------------------------

            wake_word.listen()

            ready_beep()
            print("\nJARVIS: Yes?")

            # ------------------------------------------------
            # 2. LISTEN (stops by itself when you stop talking)
            # ------------------------------------------------

            command = stt.listen_and_transcribe()

            if not command:
                print("JARVIS: I didn't hear a command.")
                tts.speak("I didn't hear a command.")
                continue

            print(f"You: {command}")

            # ------------------------------------------------
            # 3. EXIT
            # ------------------------------------------------

            normalised = re.sub(r"[^\w\s]", "", command).strip().lower()

            if normalised in VOICE_EXIT_WORDS:
                print("JARVIS: Shutting down.")
                tts.speak("Shutting down.")
                break

            # ------------------------------------------------
            # 4. THINK / ACT
            # ------------------------------------------------

            print("JARVIS: ", end="", flush=True)

            response = router.handle(command)

            # ------------------------------------------------
            # 5. SHOW + SPEAK THE REPLY
            # ------------------------------------------------

            if isinstance(response, str) and response.strip():

                print(response.strip())

                spoken = speakable(response)

                if spoken:
                    tts.speak(spoken)

            print()

        except KeyboardInterrupt:
            print("\n\nJARVIS: Shutting down.")
            break

        except Exception as error:
            print(f"\n\nJARVIS ERROR: {error}\n")

            try:
                tts.speak("Sorry, something went wrong.")
            except Exception:
                pass


# ============================================================
# ENTRY POINT
# ============================================================

def main(voice=None):

    if voice is None:

        parser = argparse.ArgumentParser(description="JARVIS")
        parser.add_argument(
            "--voice",
            action="store_true",
            help="use wake word + microphone + spoken replies",
        )
        voice = parser.parse_args().voice

    print("=" * 50)
    print("             JARVIS v1")
    print("        Voice mode" if voice else "        Text mode")
    print("=" * 50)

    router = build_router()

    if voice:
        run_voice(router)
    else:
        run_text(router)


if __name__ == "__main__":
    main()
