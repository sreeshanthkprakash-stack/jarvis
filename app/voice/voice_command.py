import os
import time

# pyrefly: ignore [missing-import]
from app.voice.mic import MicStream
# pyrefly: ignore [missing-import]
from app.voice.wake_word import WakeWordDetector
# pyrefly: ignore [missing-import]
from app.voice.speech_to_text import SpeechToText
# pyrefly: ignore [missing-import]
from app.voice.text_to_speech import TextToSpeech
# pyrefly: ignore [missing-import]
from app.voice.utils import is_exit_command, strip_wake_phrase
# pyrefly: ignore [missing-import]
from app.brain import JarvisBrain
# pyrefly: ignore [missing-import]
from app.config import SYSTEM_PROMPT, DEBUG_TIMING
# pyrefly: ignore [missing-import]
from app.router import JarvisRouter


def beep():
    """Short tone = 'I'm listening, speak now'."""

    if os.getenv("JARVIS_BEEP", "1") == "0":
        return

    try:
        import winsound
        winsound.Beep(880, 70)
    except Exception:
        pass


def run_once(mic, wake_word, stt, tts, router):
    """
    One wake -> listen -> understand -> answer cycle.
    Returns False when the user asked to exit.
    """

    # ----------------------------------------------------
    # WAIT FOR WAKE WORD
    # ----------------------------------------------------
    wake_word.listen(mic)
    beep()

    # ----------------------------------------------------
    # RECORD UNTIL YOU STOP TALKING
    # ----------------------------------------------------
    t0 = time.perf_counter()
    audio = stt.record_utterance(mic)
    t_listen = time.perf_counter() - t0

    if audio is None:
        print("JARVIS: (I didn't catch anything)")
        return True

    # ----------------------------------------------------
    # SPEECH TO TEXT
    # ----------------------------------------------------
    t0 = time.perf_counter()
    command = strip_wake_phrase(stt.transcribe(audio))
    t_stt = time.perf_counter() - t0

    if not command:
        print("JARVIS: (I didn't catch that)")
        return True

    print(f"You: {command}")

    # ----------------------------------------------------
    # EXIT
    # ----------------------------------------------------
    if is_exit_command(command):
        tts.speak("Shutting down.")
        return False

    # ----------------------------------------------------
    # ROUTER
    # ----------------------------------------------------
    print("JARVIS: ", end="", flush=True)

    t0 = time.perf_counter()
    response = router.handle(command)
    t_router = time.perf_counter() - t0

    # ----------------------------------------------------
    # SHOW + SPEAK RESPONSE
    # ----------------------------------------------------
    t_tts = 0.0

    if isinstance(response, str) and response.strip():

        print(response)

        t0 = time.perf_counter()
        tts.speak(response.strip())
        t_tts = time.perf_counter() - t0

    print()

    if DEBUG_TIMING:
        print(
            f"[voice] listened {t_listen:.1f}s | "
            f"transcribed {t_stt:.1f}s | "
            f"handled {t_router:.1f}s | "
            f"spoke {t_tts:.1f}s\n"
        )

    return True


def main():

    print("=" * 50)
    print("        JARVIS VOICE SYSTEM")
    print("=" * 50)

    brain = JarvisBrain(
        SYSTEM_PROMPT
    )

    # Loads (and warms up) the local model.
    router = JarvisRouter(
        brain
    )

    wake_word = WakeWordDetector()
    stt = SpeechToText()
    tts = TextToSpeech()

    with MicStream() as mic:

        stt.warm_up()

        print("\nStay quiet for a second - measuring room noise...")
        stt.calibrate(mic)

        print()
        print("JARVIS voice system ready.")
        print("Say: Hey Jarvis")
        print("Say 'exit' to stop.")
        print("=" * 50)

        try:
            while True:

                try:
                    keep_going = run_once(
                        mic, wake_word, stt, tts, router
                    )

                except Exception as error:
                    # One bad command must not end the voice session.
                    print(f"\nJARVIS ERROR: {error}\n")
                    keep_going = True

                if not keep_going:
                    break

                # Don't let Jarvis's own voice trigger the wake word.
                mic.flush()
                wake_word.reset()

        except KeyboardInterrupt:
            print("\nJARVIS: Shutting down.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nJARVIS: Shutting down.")
    except Exception as error:
        print(
            f"\nJARVIS ERROR: {error}"
        )
