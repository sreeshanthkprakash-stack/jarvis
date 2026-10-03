def remember_fact(memory, key, value):
    key = str(key).strip()
    value = str(value).strip()

    if not key or not value:
        return "I need both the information and its value."

    if memory.remember_fact(key, value):
        return "I'll remember that."

    return "I couldn't save that to memory."


def get_fact(memory, key):
    key = str(key).strip()

    if not key:
        return "I need to know what information you want me to retrieve."

    value = memory.get_fact(key)

    if value is None:
        return f"I don't have anything stored for '{key}'."

    return value


def forget_fact(memory, key):
    key = str(key).strip()

    if not key:
        return "I need to know what you want me to forget."

    if memory.forget_fact(key):
        return f"I've forgotten '{key}'."

    return f"I don't have anything stored for '{key}'."


def remember_preference(memory, key, value):
    key = str(key).strip()
    value = str(value).strip()

    if not key or not value:
        return "I need both the preference and its value."

    if memory.remember_preference(key, value):
        return "I'll remember that preference."

    return "I couldn't save that preference."


def get_preference(memory, key):
    key = str(key).strip()

    if not key:
        return "I need to know which preference you want me to retrieve."

    value = memory.get_preference(key)

    if value is None:
        return f"I don't have a preference stored for '{key}'."

    return value


def forget_preference(memory, key):
    key = str(key).strip()

    if not key:
        return "I need to know which preference you want me to forget."

    if memory.forget_preference(key):
        return f"I've forgotten that preference."

    return f"I don't have a preference stored for '{key}'."


def add_note(memory, note):
    note = str(note).strip()

    if not note:
        return "I need some text for the note."

    if memory.add_note(note):
        return "Note saved."

    return "I couldn't save the note."


def get_notes(memory):
    notes = memory.get_notes()

    if not notes:
        return "There are no saved notes."

    return notes


def clear_notes(memory):
    memory.clear_notes()
    return "All saved notes have been cleared."


def list_memory(memory):
    data = memory.get_all()

    facts = data.get("facts", {})
    preferences = data.get("preferences", {})
    notes = data.get("notes", [])

    if not facts and not preferences and not notes:
        return "I don't have any stored memory yet."

    parts = []

    for key, value in facts.items():
        display_key = key.replace("_", " ")
        parts.append(f"your {display_key} is {value}")

    for key, value in preferences.items():
        display_key = key.replace("_", " ")
        parts.append(f"your {display_key} is {value}")

    for note in notes:
        parts.append(f"you noted that {note}")

    if len(parts) == 1:
        return f"I remember that {parts[0]}."

    if len(parts) == 2:
        return f"I remember that {parts[0]} and {parts[1]}."

    return (
        "I remember that "
        + ", ".join(parts[:-1])
        + ", and "
        + parts[-1]
        + "."
    )