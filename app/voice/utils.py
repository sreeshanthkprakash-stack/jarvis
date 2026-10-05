"""Small, dependency-free helpers shared by the voice modules."""

import re

EXIT_WORDS = {"exit", "quit", "stop", "shutdown", "shut down", "goodbye"}

_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_MARKDOWN_RE = re.compile(r"[`*_#>|~]+")
_WAKE_RE = re.compile(r"^\s*(?:hey|hi|ok|okay)?[\s,]*jarvis\b[\s,.!?:;-]*", re.IGNORECASE)


def clean_for_speech(text, limit=420):
    """
    Make a reply comfortable to hear:
    - no spoken URLs or markdown symbols
    - no walls of text (cut at a sentence end near `limit`)
    """

    text = str(text or "")
    text = _URL_RE.sub("link", text)
    text = _MARKDOWN_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) <= limit:
        return text

    cut = text[:limit]

    # prefer ending on a full sentence
    ends = [cut.rfind(mark) for mark in (". ", "! ", "? ")]
    best = max(ends)

    if best >= limit // 2:
        return cut[: best + 1].strip()

    return cut.rsplit(" ", 1)[0].strip() + "..."


def strip_wake_phrase(text):
    """'Hey Jarvis, open Chrome' -> 'open Chrome'."""

    return _WAKE_RE.sub("", str(text or "")).strip()


def is_exit_command(text):
    """Whisper adds punctuation/capitals: 'Exit.' must still match."""

    cleaned = re.sub(r"[^a-z ]", "", str(text or "").lower()).strip()
    return cleaned in EXIT_WORDS
