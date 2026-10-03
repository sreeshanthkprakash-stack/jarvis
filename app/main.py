# pyrefly: ignore [missing-import]

# pyrefly: ignore [missing-import]
from app.brain import JarvisBrain

# pyrefly: ignore [missing-import]
from app.config import SYSTEM_PROMPT
# pyrefly: ignore [missing-import]
from app.router import JarvisRouter


def main():
    print("=" * 50)
    print("             JARVIS v1")
    print("        Online and ready.")
    print("=" * 50)
    print("Type 'exit' to shut down.\n")

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
    # MAIN COMMAND LOOP
    # --------------------------------------------------------

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

            if user_input.lower() in {
                "exit",
                "quit",
                "shutdown",
            }:
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
            # DISPLAY LOCAL TOOL RESPONSE
            #
            # brain.ask() handles its own streamed output.
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


if __name__ == "__main__":
    main()