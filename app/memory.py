import json
import os


# Longest message kept in conversation memory. Tool results (screen
# text, clipboard, file contents...) can be huge; the user still sees
# them in full, but only this much is re-sent to the model later.
MAX_MESSAGE_CHARS = 1200


def _clip(message):

    message = str(message)

    if len(message) <= MAX_MESSAGE_CHARS:
        return message

    return message[:MAX_MESSAGE_CHARS].rstrip() + " ...[truncated]"


class ConversationMemory:
    def __init__(self, system_prompt):
        self.messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

    def add_user(self, message):
        self.messages.append(
            {
                "role": "user",
                "content": _clip(message)
            }
        )

    def add_assistant(self, message):
        self.messages.append(
            {
                "role": "assistant",
                "content": _clip(message)
            }
        )

    def get_messages(self):
        return self.messages

    def clear(self):
        system_message = self.messages[0]

        self.messages = [
            system_message
        ]


class PersistentMemory:

    def __init__(self, path="data/memory.json"):

        self.path = path

        self.data = {
            "facts": {},
            "preferences": {},
            "notes": []
        }

        self.load()

    # =====================================
    # LOAD
    # =====================================

    def load(self):

        if not os.path.exists(self.path):

            self.save()

            return

        try:

            with open(
                self.path,
                "r",
                encoding="utf-8"
            ) as file:

                loaded = json.load(file)

                if not isinstance(loaded, dict):
                    return

                # Preserve the expected structure.
                if isinstance(
                    loaded.get("facts"),
                    dict
                ):
                    self.data["facts"] = (
                        loaded["facts"]
                    )

                if isinstance(
                    loaded.get("preferences"),
                    dict
                ):
                    self.data["preferences"] = (
                        loaded["preferences"]
                    )

                if isinstance(
                    loaded.get("notes"),
                    list
                ):
                    self.data["notes"] = (
                        loaded["notes"]
                    )

        except (
            json.JSONDecodeError,
            OSError
        ):

            print(
                "JARVIS: Memory file could not "
                "be loaded. Starting with empty memory."
            )

    # =====================================
    # SAVE
    # =====================================

    def save(self):

        directory = os.path.dirname(
            self.path
        )

        if directory:

            os.makedirs(
                directory,
                exist_ok=True
            )

        with open(
            self.path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.data,
                file,
                indent=4,
                ensure_ascii=False
            )

    # =====================================
    # FACTS
    # =====================================

    def remember_fact(
        self,
        key,
        value
    ):

        key = str(key).strip()
        value = str(value).strip()

        if not key or not value:
            return False

        self.data["facts"][key] = value

        self.save()

        return True

    def get_fact(self, key):

        key = str(key).strip()

        return self.data["facts"].get(key)

    def forget_fact(self, key):

        key = str(key).strip()

        if key not in self.data["facts"]:
            return False

        del self.data["facts"][key]

        self.save()

        return True

    # =====================================
    # PREFERENCES
    # =====================================

    def remember_preference(
        self,
        key,
        value
    ):

        key = str(key).strip()
        value = str(value).strip()

        if not key or not value:
            return False

        self.data["preferences"][key] = value

        self.save()

        return True

    def get_preference(self, key):

        key = str(key).strip()

        return self.data[
            "preferences"
        ].get(key)

    def forget_preference(self, key):

        key = str(key).strip()

        if (
            key
            not in self.data["preferences"]
        ):
            return False

        del self.data["preferences"][key]

        self.save()

        return True

    # =====================================
    # NOTES
    # =====================================

    def add_note(self, note):

        note = str(note).strip()

        if not note:
            return False

        self.data["notes"].append(note)

        self.save()

        return True

    def get_notes(self):

        return self.data["notes"]

    def clear_notes(self):

        self.data["notes"] = []

        self.save()

    # =====================================
    # ALL MEMORY
    # =====================================

    def get_all(self):

        return self.data

    # =====================================
    # MEMORY SUMMARY
    # =====================================

    def get_summary(self):

        facts = self.data["facts"]
        preferences = self.data["preferences"]
        notes = self.data["notes"]

        return {
            "facts": facts.copy(),
            "preferences": preferences.copy(),
            "notes": notes.copy()
        }

    # =====================================
    # CLEAR EVERYTHING
    # =====================================

    def clear(self):

        self.data = {
            "facts": {},
            "preferences": {},
            "notes": []
        }

        self.save()