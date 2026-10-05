import difflib
import hashlib
import math
import os
import re
import time
import webbrowser
from pathlib import Path

import pyautogui
import pytesseract


# ============================================================
# TESSERACT CONFIGURATION
# ============================================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# ============================================================
# WEB / URL
# ============================================================

# "spotify:search:ishq", "ms-settings:display", "mailto:a@b.c" ...
# (a colon followed by a digit is a port, e.g. localhost:8000)
_APP_LINK_RE = re.compile(r"^[a-z][a-z0-9+.\-]*:(?!\d)", re.IGNORECASE)


def open_url(url):

    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL must be a non-empty string.")

    url = url.strip()

    lowered = url.lower()

    if (
        _APP_LINK_RE.match(url)
        and not lowered.startswith(("http://", "https://", "file:"))
        and hasattr(os, "startfile")
    ):
        # Hand app links to Windows (opens Spotify, Settings, ...).
        try:
            os.startfile(url)
        except OSError as error:
            raise ValueError(
                f"Windows could not open '{url}'. "
                f"Is the app installed? ({error})"
            )

        return f"Opened {url}."

    webbrowser.open(url)

    return f"Opened {url}."


def open_website(website):
    if not isinstance(website, str) or not website.strip():
        raise ValueError("Website must be a non-empty string.")

    website = website.strip()

    if not website.startswith(("http://", "https://")):
        website = f"https://{website}"

    webbrowser.open(website)

    return f"Opened {website}."


# ============================================================
# KEYBOARD
# ============================================================

def type_text(text):
    if not isinstance(text, str):
        raise TypeError("Text must be a string.")

    pyautogui.write(
        text,
        interval=0.01,
    )

    return "Typed the requested text."


def press_key(key):
    if not isinstance(key, str) or not key.strip():
        raise ValueError("Key must be a non-empty string.")

    key = key.strip()

    pyautogui.press(key)

    return f"Pressed {key}."


def hotkey(keys):
    if not isinstance(keys, str) or not keys.strip():
        raise ValueError("Keys must be a non-empty string.")

    parts = [
        part.strip()
        for part in keys.lower().split("+")
        if part.strip()
    ]

    if not parts:
        raise ValueError("Invalid keyboard shortcut.")

    pyautogui.hotkey(*parts)

    return f"Pressed {keys}."


# ============================================================
# MOUSE
# ============================================================

def move_mouse(x, y):
    x = int(x)
    y = int(y)

    pyautogui.moveTo(
        x,
        y,
        duration=0.15,
    )

    return f"Moved mouse to ({x}, {y})."


def click_mouse(x=None, y=None, button="left"):
    if x is not None and y is not None:
        pyautogui.moveTo(
            int(x),
            int(y),
            duration=0.15,
        )

    button = str(button).lower().strip()

    if button not in {
        "left",
        "right",
        "middle",
    }:
        raise ValueError(
            "Button must be left, right, or middle."
        )

    pyautogui.click(
        button=button
    )

    return f"Clicked the {button} mouse button."


# ============================================================
# TIMING
# ============================================================

def wait(seconds):
    seconds = float(seconds)

    if seconds < 0:
        raise ValueError(
            "Seconds cannot be negative."
        )

    time.sleep(seconds)

    return f"Waited {seconds:g} seconds."


# ============================================================
# SCREEN
# ============================================================

def get_screen_size():
    width, height = pyautogui.size()

    return f"Screen size is {width} by {height}."


def take_screen_capture(
    path="data/screen.png"
):
    screenshot = pyautogui.screenshot()

    output_path = Path(path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    screenshot.save(output_path)

    return f"Screen captured to {output_path}."


# ============================================================
# OCR HELPERS
# ============================================================

def _normalize_ocr_text(text):
    if not isinstance(text, str):
        return ""

    return " ".join(
        text.lower().split()
    )


# Screens wider than this are shrunk before OCR (coordinates are scaled
# back, so nothing else changes). 1080p screens are left alone.
# 0 = never shrink.   Override: JARVIS_OCR_MAX_WIDTH in .env
try:
    _OCR_MAX_WIDTH = int(os.getenv("JARVIS_OCR_MAX_WIDTH", "1920"))
except ValueError:
    _OCR_MAX_WIDTH = 1920

# Result of the last OCR run, keyed by the exact pixels of the screen.
# Identical screen -> identical text, so OCR is skipped.
_ocr_cache = {"key": None, "data": None, "time": 0.0, "epoch": -1, "fingerprint": None, "size": None}

# Counts mouse/keyboard actions. A cached OCR result is only trusted while
# no action has happened since it was made.
_input_epoch = [0]


def _count_input(function):

    def wrapper(*args, **kwargs):
        _input_epoch[0] += 1
        return function(*args, **kwargs)

    wrapper._jarvis_wrapped = True
    wrapper.__wrapped__ = function

    return wrapper


for _name in (
    "click", "doubleClick", "rightClick", "middleClick", "moveTo",
    "moveRel", "drag", "dragTo", "scroll", "write", "typewrite",
    "press", "hotkey", "keyDown", "keyUp",
):
    _function = getattr(pyautogui, _name, None)

    if callable(_function) and not getattr(_function, "_jarvis_wrapped", False):
        setattr(pyautogui, _name, _count_input(_function))

# Size and a 64x36 thumbnail of the last captured screen.
_screen_info = {"size": None, "fingerprint": None}


def _fingerprint(image):
    """Tiny grayscale thumbnail used to tell if the screen changed."""

    small = image.convert("L").resize((64, 36))

    return list(small.getdata())


def _fingerprint_distance(a, b):
    """Average brightness difference (0-255) between two thumbnails."""

    if not a or not b or len(a) != len(b):
        return 255.0

    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def _ocr_debug():
    try:
        # pyrefly: ignore [missing-import]
        from app import config
        return bool(getattr(config, "DEBUG_TIMING", False))
    except Exception:
        return False


def _copy_ocr_data(data):
    return {key: list(values) for key, values in data.items()}


def _get_ocr_data():
    """
    Capture the current screen and run
    local Tesseract OCR.

    No external API is used.

    Speed-ups (results are identical):
    - same screen as last time -> reuse the previous OCR result
    - grayscale image (smaller to encode, same text)
    - very large screens are shrunk, then coordinates scaled back
    """

    from PIL import Image

    started = time.perf_counter()

    screenshot = pyautogui.screenshot()

    _screen_info["size"] = screenshot.size
    _screen_info["fingerprint"] = _fingerprint(screenshot)

    key = (
        screenshot.size,
        hashlib.md5(screenshot.tobytes()).hexdigest(),
    )

    captured = time.perf_counter()

    now = time.perf_counter()

    cached = _ocr_cache["data"] is not None

    same_pixels = cached and _ocr_cache["key"] == key

    # A blinking text cursor changes a few pixels between two reads of
    # an otherwise unchanged screen. If nothing was clicked or typed
    # since, and the last read was moments ago, it is still the same screen.
    looks_same = (
        cached
        and _ocr_cache["size"] == screenshot.size
        and _ocr_cache["epoch"] == _input_epoch[0]
        and now - _ocr_cache["time"] < 1.0
        and _fingerprint_distance(
            _ocr_cache["fingerprint"],
            _screen_info["fingerprint"],
        ) < 1.5
    )

    if same_pixels or looks_same:

        if _ocr_debug():
            print(
                f"[ocr] same screen, reused result "
                f"({captured - started:.2f}s)",
                flush=True,
            )

        return _copy_ocr_data(_ocr_cache["data"])

    image = screenshot.convert("L")
    scale = 1.0

    if _OCR_MAX_WIDTH and image.width > _OCR_MAX_WIDTH:

        scale = _OCR_MAX_WIDTH / image.width

        image = image.resize(
            (
                _OCR_MAX_WIDTH,
                max(1, round(image.height * scale)),
            ),
            Image.Resampling.LANCZOS,
        )

    data = pytesseract.image_to_data(
        image,
        output_type=pytesseract.Output.DICT,
        config="--psm 11",
    )

    if scale != 1.0:

        inverse = 1.0 / scale

        for field in ("left", "top", "width", "height"):

            try:
                data[field] = [
                    int(round(float(value) * inverse))
                    for value in data[field]
                ]
            except (KeyError, TypeError, ValueError):
                pass

    _ocr_cache["key"] = key
    _ocr_cache["data"] = _copy_ocr_data(data)
    _ocr_cache["time"] = time.perf_counter()
    _ocr_cache["epoch"] = _input_epoch[0]
    _ocr_cache["fingerprint"] = _screen_info["fingerprint"]
    _ocr_cache["size"] = screenshot.size

    if _ocr_debug():
        print(
            f"[ocr] capture {captured - started:.2f}s | "
            f"recognise {time.perf_counter() - captured:.2f}s"
            + (f" | shrunk x{scale:.2f}" if scale != 1.0 else ""),
            flush=True,
        )

    return data


def _build_ocr_words(ocr_data):
    words = []

    count = len(
        ocr_data["text"]
    )

    for index in range(count):

        raw_text = ocr_data["text"][index]

        text = _normalize_ocr_text(
            raw_text
        )

        if not text:
            continue

        try:
            confidence = float(
                ocr_data["conf"][index]
            )
        except (
            TypeError,
            ValueError,
        ):
            confidence = -1

        if confidence < 30:
            continue

        left = int(
            ocr_data["left"][index]
        )

        top = int(
            ocr_data["top"][index]
        )

        width = int(
            ocr_data["width"][index]
        )

        height = int(
            ocr_data["height"][index]
        )

        if width <= 0 or height <= 0:
            continue

        words.append(
            {
                "text": text,
                "confidence": confidence,
                "left": left,
                "top": top,
                "width": width,
                "height": height,
            }
        )

    return words


# ============================================================
# SCREEN OBSERVATION
# ============================================================

def observe_screen():
    """
    Capture the current screen and return
    grouped visible OCR elements.

    No external API or Groq call is used.
    """

    ocr_data = _get_ocr_data()

    words = _build_ocr_words(
        ocr_data
    )

    elements = _group_ocr_words(
        words
    )

    screen_width, screen_height = (
        pyautogui.size()
    )

    return {
        "screen_size": {
            "width": screen_width,
            "height": screen_height,
        },
        "elements": elements,
    }


def _group_ocr_words(words):
    """
    Group nearby OCR words into visible text blocks.

    This is still completely local.
    No AI/API call is made.
    """

    if not words:
        return []

    sorted_words = sorted(
        words,
        key=lambda word: (
            word["top"],
            word["left"],
        ),
    )

    groups = []

    for word in sorted_words:

        word_left = word["left"]
        word_top = word["top"]

        word_right = (
            word["left"] + word["width"]
        )

        word_bottom = (
            word["top"] + word["height"]
        )

        placed = False

        for group in groups:

            group_left = group["left"]
            group_top = group["top"]
            group_right = group["right"]
            group_bottom = group["bottom"]

            vertical_overlap = (
                min(
                    word_bottom,
                    group_bottom,
                )
                - max(
                    word_top,
                    group_top,
                )
            )

            word_height = word["height"]

            same_line = (
                vertical_overlap
                >= word_height * 0.4
            )

            horizontal_gap = (
                word_left - group_right
            )

            close_enough = (
                -20
                <= horizontal_gap
                <= 80
            )

            if same_line and close_enough:

                group["words"].append(
                    word
                )

                group["left"] = min(
                    group["left"],
                    word_left,
                )

                group["top"] = min(
                    group["top"],
                    word_top,
                )

                group["right"] = max(
                    group["right"],
                    word_right,
                )

                group["bottom"] = max(
                    group["bottom"],
                    word_bottom,
                )

                group["text"] = " ".join(
                    item["text"]
                    for item in group["words"]
                )

                placed = True
                break

        if not placed:

            groups.append(
                {
                    "words": [word],
                    "text": word["text"],
                    "left": word_left,
                    "top": word_top,
                    "right": word_right,
                    "bottom": word_bottom,
                }
            )

    elements = []

    for group in groups:

        left = group["left"]
        top = group["top"]
        right = group["right"]
        bottom = group["bottom"]

        width = right - left
        height = bottom - top

        center_x = (
            left + right
        ) // 2

        center_y = (
            top + bottom
        ) // 2

        confidence = sum(
            word["confidence"]
            for word in group["words"]
        ) / len(group["words"])

        elements.append(
            {
                "text": group["text"],
                "confidence": round(
                    confidence,
                    1,
                ),
                "x": center_x,
                "y": center_y,
                "left": left,
                "top": top,
                "width": width,
                "height": height,
            }
        )

    return elements


# ============================================================
# OCR TEXT SEARCH
# ============================================================

def _find_ocr_match(text, words):
    target = _normalize_ocr_text(
        text
    )

    if not target:
        return None

    target_words = target.split()

    # --------------------------------------------------------
    # SINGLE-WORD EXACT MATCH
    # --------------------------------------------------------

    if len(target_words) == 1:

        for word in words:

            if word["text"] == target:
                return [word]

        return None

    # --------------------------------------------------------
    # MULTI-WORD EXACT CONSECUTIVE MATCH
    # --------------------------------------------------------

    target_count = len(
        target_words
    )

    for start_index in range(
        len(words)
    ):

        candidate = words[
            start_index:
            start_index + target_count
        ]

        if len(candidate) != target_count:
            continue

        candidate_text = " ".join(
            word["text"]
            for word in candidate
        )

        if candidate_text == target:
            return candidate

    return None


def _get_match_center(
    matched_words
):
    left = min(
        word["left"]
        for word in matched_words
    )

    top = min(
        word["top"]
        for word in matched_words
    )

    right = max(
        word["left"]
        + word["width"]
        for word in matched_words
    )

    bottom = max(
        word["top"]
        + word["height"]
        for word in matched_words
    )

    center_x = (
        left + right
    ) // 2

    center_y = (
        top + bottom
    ) // 2

    return center_x, center_y


# ============================================================
# OCR SPATIAL SEARCH
# ============================================================

def find_all_text_on_screen(text):
    """
    Find every exact occurrence of text
    on the current screen.

    Returns a list of matching elements
    with coordinates.

    Completely local.
    No API call is made.
    """

    if not isinstance(
        text,
        str,
    ) or not text.strip():
        raise ValueError(
            "Text must be a non-empty string."
        )

    ocr_data = _get_ocr_data()

    words = _build_ocr_words(
        ocr_data
    )

    target = _normalize_ocr_text(
        text
    )

    if not target:
        return []

    target_words = target.split()

    matches = []

    # --------------------------------------------------------
    # SINGLE WORD
    # --------------------------------------------------------

    if len(target_words) == 1:

        for word in words:

            if word["text"] != target:
                continue

            center_x = (
                word["left"]
                + word["width"] // 2
            )

            center_y = (
                word["top"]
                + word["height"] // 2
            )

            matches.append(
                {
                    "text": text,
                    "x": center_x,
                    "y": center_y,
                    "left": word["left"],
                    "top": word["top"],
                    "width": word["width"],
                    "height": word["height"],
                    "confidence": round(
                        word["confidence"],
                        1,
                    ),
                }
            )

        return matches

    # --------------------------------------------------------
    # MULTI-WORD PHRASE
    # --------------------------------------------------------

    target_count = len(
        target_words
    )

    for start_index in range(
        len(words)
    ):

        candidate = words[
            start_index:
            start_index + target_count
        ]

        if len(candidate) != target_count:
            continue

        candidate_text = " ".join(
            word["text"]
            for word in candidate
        )

        if candidate_text != target:
            continue

        left = min(
            word["left"]
            for word in candidate
        )

        top = min(
            word["top"]
            for word in candidate
        )

        right = max(
            word["left"]
            + word["width"]
            for word in candidate
        )

        bottom = max(
            word["top"]
            + word["height"]
            for word in candidate
        )

        center_x = (
            left + right
        ) // 2

        center_y = (
            top + bottom
        ) // 2

        confidence = sum(
            word["confidence"]
            for word in candidate
        ) / len(candidate)

        matches.append(
            {
                "text": text,
                "x": center_x,
                "y": center_y,
                "left": left,
                "top": top,
                "width": right - left,
                "height": bottom - top,
                "confidence": round(
                    confidence,
                    1,
                ),
            }
        )

    return matches


def find_topmost_text_on_screen(text):
    """
    Find the topmost exact occurrence of text.

    Completely local.
    No API call is made.
    """

    matches = find_all_text_on_screen(
        text
    )

    if not matches:
        return None

    return min(
        matches,
        key=lambda item: item["y"],
    )


def find_bottommost_text_on_screen(text):
    """
    Find the bottommost exact occurrence of text.

    Completely local.
    No API call is made.
    """

    matches = find_all_text_on_screen(
        text
    )

    if not matches:
        return None

    return max(
        matches,
        key=lambda item: item["y"],
    )


def click_topmost_text_on_screen(text):
    """
    Find and click the topmost exact occurrence
    of text.

    Completely local.
    No API call is made.
    """

    match = find_topmost_text_on_screen(
        text
    )

    if match is None:
        return (
            f"Could not find "
            f"'{text}' on the screen."
        )

    pyautogui.moveTo(
        match["x"],
        match["y"],
        duration=0.15,
    )

    pyautogui.click()

    return (
        f"Clicked topmost '{text}' "
        f"at ({match['x']}, {match['y']})."
    )


# ============================================================
# SPATIAL RELATIONSHIP HELPERS
# ============================================================

def _horizontal_overlap(
    first,
    second,
):
    """
    Determine whether two screen elements
    overlap horizontally.
    """

    first_left = first["left"]
    first_right = (
        first["left"]
        + first["width"]
    )

    second_left = second["left"]
    second_right = (
        second["left"]
        + second["width"]
    )

    return (
        min(
            first_right,
            second_right,
        )
        > max(
            first_left,
            second_left,
        )
    )


def _vertical_overlap(
    first,
    second,
):
    """
    Determine whether two screen elements
    overlap vertically.
    """

    first_top = first["top"]
    first_bottom = (
        first["top"]
        + first["height"]
    )

    second_top = second["top"]
    second_bottom = (
        second["top"]
        + second["height"]
    )

    return (
        min(
            first_bottom,
            second_bottom,
        )
        > max(
            first_top,
            second_top,
        )
    )


def _find_reference_element(
    text,
    elements,
):
    """
    Find the first exact matching screen element.
    """

    target = _normalize_ocr_text(
        text
    )

    for element in elements:

        if (
            _normalize_ocr_text(
                element["text"]
            )
            == target
        ):
            return element

    return None


def _find_candidate_elements(
    text,
    elements,
):
    """
    Find all exact matching screen elements.
    """

    target = _normalize_ocr_text(
        text
    )

    return [
        element
        for element in elements
        if (
            _normalize_ocr_text(
                element["text"]
            )
            == target
        )
    ]


def _observe_ocr_elements():
    """
    Capture one screen and return its
    OCR elements.

    This guarantees that spatial comparisons
    use the same screenshot.

    Completely local.
    No API call is made.
    """

    observation = observe_screen()

    return observation[
        "elements"
    ]


# ============================================================
# FIND TEXT BELOW
# ============================================================

def find_text_below(
    reference_text,
    target_text,
):
    """
    Find the closest exact target text
    below a reference text.

    Both elements must be horizontally
    aligned.

    Completely local.
    No API call is made.
    """

    elements = _observe_ocr_elements()

    reference = _find_reference_element(
        reference_text,
        elements,
    )

    if reference is None:
        return None

    candidates = []

    for element in _find_candidate_elements(
        target_text,
        elements,
    ):

        if element["y"] <= reference["y"]:
            continue

        if not _horizontal_overlap(
            reference,
            element,
        ):
            continue

        distance = (
            element["top"]
            - (
                reference["top"]
                + reference["height"]
            )
        )

        candidates.append(
            (
                distance,
                element,
            )
        )

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda item: item[0],
    )[1]


# ============================================================
# FIND TEXT ABOVE
# ============================================================

def find_text_above(
    reference_text,
    target_text,
):
    """
    Find the closest exact target text
    above a reference text.

    Completely local.
    No API call is made.
    """

    elements = _observe_ocr_elements()

    reference = _find_reference_element(
        reference_text,
        elements,
    )

    if reference is None:
        return None

    candidates = []

    for element in _find_candidate_elements(
        target_text,
        elements,
    ):

        if element["y"] >= reference["y"]:
            continue

        if not _horizontal_overlap(
            reference,
            element,
        ):
            continue

        distance = (
            reference["top"]
            - (
                element["top"]
                + element["height"]
            )
        )

        candidates.append(
            (
                distance,
                element,
            )
        )

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda item: item[0],
    )[1]


# ============================================================
# FIND TEXT LEFT
# ============================================================

def find_text_left_of(
    reference_text,
    target_text,
):
    """
    Find the closest exact target text
    to the left of a reference text.

    Completely local.
    No API call is made.
    """

    elements = _observe_ocr_elements()

    reference = _find_reference_element(
        reference_text,
        elements,
    )

    if reference is None:
        return None

    candidates = []

    for element in _find_candidate_elements(
        target_text,
        elements,
    ):

        if element["x"] >= reference["x"]:
            continue

        if not _vertical_overlap(
            reference,
            element,
        ):
            continue

        distance = (
            reference["left"]
            - (
                element["left"]
                + element["width"]
            )
        )

        candidates.append(
            (
                distance,
                element,
            )
        )

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda item: item[0],
    )[1]


# ============================================================
# FIND TEXT RIGHT
# ============================================================

def find_text_right_of(
    reference_text,
    target_text,
):
    """
    Find the closest exact target text
    to the right of a reference text.

    Completely local.
    No API call is made.
    """

    elements = _observe_ocr_elements()

    reference = _find_reference_element(
        reference_text,
        elements,
    )

    if reference is None:
        return None

    candidates = []

    for element in _find_candidate_elements(
        target_text,
        elements,
    ):

        if element["x"] <= reference["x"]:
            continue

        if not _vertical_overlap(
            reference,
            element,
        ):
            continue

        distance = (
            element["left"]
            - (
                reference["left"]
                + reference["width"]
            )
        )

        candidates.append(
            (
                distance,
                element,
            )
        )

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda item: item[0],
    )[1]


# ============================================================
# GENERIC ELEMENT CLICK
# ============================================================

def _click_element(
    element,
    description,
):
    """
    Click the center of an OCR element.
    """

    if element is None:
        return (
            f"Could not find "
            f"{description}."
        )

    pyautogui.moveTo(
        element["x"],
        element["y"],
        duration=0.15,
    )

    pyautogui.click()

    return (
        f"Clicked {description} "
        f"at "
        f"({element['x']}, {element['y']})."
    )


# ============================================================
# CLICK TEXT BELOW
# ============================================================

def click_text_below(
    reference_text,
    target_text,
):
    """
    Find and click the closest target text
    below a reference text.

    Completely local.
    No API call is made.
    """

    element = find_text_below(
        reference_text,
        target_text,
    )

    return _click_element(
        element,
        (
            f"'{target_text}' below "
            f"'{reference_text}'"
        ),
    )


# ============================================================
# CLICK TEXT ABOVE
# ============================================================

def click_text_above(
    reference_text,
    target_text,
):
    """
    Find and click the closest target text
    above a reference text.

    Completely local.
    No API call is made.
    """

    element = find_text_above(
        reference_text,
        target_text,
    )

    return _click_element(
        element,
        (
            f"'{target_text}' above "
            f"'{reference_text}'"
        ),
    )


# ============================================================
# CLICK TEXT LEFT
# ============================================================

def click_text_left_of(
    reference_text,
    target_text,
):
    """
    Find and click the closest target text
    to the left of a reference text.

    Completely local.
    No API call is made.
    """

    element = find_text_left_of(
        reference_text,
        target_text,
    )

    return _click_element(
        element,
        (
            f"'{target_text}' left of "
            f"'{reference_text}'"
        ),
    )


# ============================================================
# CLICK TEXT RIGHT
# ============================================================

def click_text_right_of(
    reference_text,
    target_text,
):
    """
    Find and click the closest target text
    to the right of a reference text.

    Completely local.
    No API call is made.
    """

    element = find_text_right_of(
        reference_text,
        target_text,
    )

    return _click_element(
        element,
        (
            f"'{target_text}' right of "
            f"'{reference_text}'"
        ),
    )


# ============================================================
# SIMPLE TEXT FIND
# ============================================================

def find_text_on_screen(text):
    if not isinstance(
        text,
        str,
    ) or not text.strip():
        raise ValueError(
            "Text must be a non-empty string."
        )

    ocr_data = _get_ocr_data()

    words = _build_ocr_words(
        ocr_data
    )

    matched_words = _find_ocr_match(
        text,
        words,
    )

    if not matched_words:
        return (
            f"Could not find "
            f"'{text}' on the screen."
        )

    center_x, center_y = (
        _get_match_center(
            matched_words
        )
    )

    return (
        f"Found '{text}' at "
        f"({center_x}, {center_y})."
    )


# ============================================================
# OCR CLICK
# ============================================================

def click_text_on_screen(text):
    if not isinstance(
        text,
        str,
    ) or not text.strip():
        raise ValueError(
            "Text must be a non-empty string."
        )

    # IMPORTANT:
    # Take the screenshot and find the target
    # from the SAME screenshot before clicking.

    ocr_data = _get_ocr_data()

    words = _build_ocr_words(
        ocr_data
    )

    matched_words = _find_ocr_match(
        text,
        words,
    )

    if not matched_words:
        return (
            f"Could not find "
            f"'{text}' on the screen."
        )

    center_x, center_y = (
        _get_match_center(
            matched_words
        )
    )

    pyautogui.moveTo(
        center_x,
        center_y,
        duration=0.15,
    )

    pyautogui.click()

    return (
        f"Clicked '{text}' at "
        f"({center_x}, {center_y})."
    )

def describe_screen():
    """
    Observe the current screen and return a compact
    description of visible OCR elements.

    This is local-only.
    No Groq/API call is made.
    """

    screen = observe_screen()

    if not isinstance(screen, dict):
        return {
            "success": False,
            "message": "Could not observe the screen.",
        }

    elements = screen.get(
        "elements",
        [],
    )

    if not isinstance(elements, list):
        elements = []

    visible_elements = []

    for element in elements:

        if not isinstance(
            element,
            dict,
        ):
            continue

        text = str(
            element.get(
                "text",
                "",
            )
        ).strip()

        if not text:
            continue

        visible_elements.append(
            {
                "text": text,
                "confidence": element.get(
                    "confidence",
                    0,
                ),
                "x": element.get(
                    "x"
                ),
                "y": element.get(
                    "y"
                ),
                "left": element.get(
                    "left"
                ),
                "top": element.get(
                    "top"
                ),
                "width": element.get(
                    "width"
                ),
                "height": element.get(
                    "height"
                ),
            }
        )

    return {
        "success": True,
        "screen_size": screen.get(
            "screen_size",
            {},
        ),
        "element_count": len(
            visible_elements
        ),
        "elements": visible_elements,
    }


# ============================================================
# SMART TARGETING  (the model decides WHICH match to click)
# ============================================================
#
#   find_on_screen("router.py")  -> every match, with where it is
#   click_match(2)               -> click the one chosen
#   read_screen()                -> what text is visible (to verify)
#
# The old "click X" took the first OCR hit (top-left). With several
# matches that is a guess; here the caller sees them all.

_last_matches = {"query": "", "items": [], "fingerprint": None}

# Mean brightness change above which the screen counts as "different".
_STALE_LEVEL = 5.0


def _region_of(x, y, size):

    width, height = size or (0, 0)

    if not width or not height:
        return "screen"

    fx, fy = x / width, y / height

    if fy < 0.07:
        return "top bar"

    if fy > 0.93:
        return "bottom bar"

    if fx < 0.22:
        return "left panel"

    if fx > 0.78:
        return "right panel"

    return "main area"


def _screen_words():

    words = _build_ocr_words(_get_ocr_data())

    return words, _group_ocr_words(words)


def _find_word_runs(words, target):
    """
    Every occurrence of the target, as runs of consecutive OCR words.
    Exact matches first; for a single longer word, also accept
    words that merely contain it (OCR often glues on punctuation).
    """

    parts = target.split()
    count = len(parts)
    runs = []

    for start in range(len(words) - count + 1):

        window = words[start:start + count]

        if [word["text"] for word in window] == parts:
            runs.append(window)

    if runs or count != 1 or len(parts[0]) < 3:
        return runs

    return [[word] for word in words if parts[0] in word["text"]]


def _nearby_text(cx, cy, words, target, limit=2, radius=450):
    """Short labels next to a match, so the choice can be described."""

    parts = set(target.split())

    scored = []
    seen = set()

    for word in words:

        text = word["text"]

        if len(text) < 3 or text in parts or target in text or text in seen:
            continue

        distance = math.hypot(
            word["left"] + word["width"] / 2 - cx,
            word["top"] + word["height"] / 2 - cy,
        )

        if distance <= radius:
            seen.add(text)
            scored.append((distance, text))

    scored.sort()

    return [text[:20] for _, text in scored[:limit]]


def screen_matches(text, limit=8):
    """
    Find every occurrence of text on screen.

    Returns a list of {id, text, x, y, region, near} and remembers it
    for click_match().
    """

    target = _normalize_ocr_text(text)

    if not target:
        raise ValueError("Text must be a non-empty string.")

    words, elements = _screen_words()

    size = _screen_info["size"] or pyautogui.size()

    items = []

    for run in _find_word_runs(words, target)[:limit]:

        cx, cy = _get_match_center(run)

        items.append(
            {
                "id": len(items) + 1,
                "text": " ".join(word["text"] for word in run),
                "x": cx,
                "y": cy,
                "region": _region_of(cx, cy, size),
                "near": _nearby_text(cx, cy, words, target),
            }
        )

    _last_matches["query"] = str(text).strip()
    _last_matches["items"] = items
    _last_matches["fingerprint"] = _screen_info["fingerprint"]

    # Remember similar words for the "not found" message.
    _last_matches["similar"] = (
        difflib.get_close_matches(
            target,
            sorted({word["text"] for word in words}),
            n=3,
            cutoff=0.7,
        )
        if not items and len(target.split()) == 1
        else []
    )

    return items


def describe_match(item):
    """'top bar, near "config.py", "brain.py"'"""

    near = item.get("near") or []

    if near:
        labels = ", ".join(f'"{label}"' for label in near)
        return f"{item['region']}, near {labels}"

    return item["region"]


def find_on_screen(text):
    """Look for text on screen and list every match and where it is."""

    items = screen_matches(text)

    text = str(text).strip()

    if not items:

        similar = _last_matches.get("similar") or []

        hint = (
            " Similar text on screen: "
            + ", ".join(f'"{word}"' for word in similar)
            + "."
            if similar
            else ""
        )

        return f"I can't see '{text}' on the screen.{hint}"

    if len(items) == 1:
        return (
            f"Found 1 match for '{text}': "
            f"[1] {describe_match(items[0])}. "
            "Call click_match(1) to click it."
        )

    lines = [f"Found {len(items)} matches for '{text}':"]

    for item in items:
        lines.append(f"[{item['id']}] {describe_match(item)}")

    lines.append(
        "Pick the one that fits the request, or ask the user which one."
    )

    return "\n".join(lines)


def _as_bool(value):

    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "1"}

    return bool(value)


def click_match(number, double=False):
    """Click one of the matches listed by the last find_on_screen."""

    try:
        index = int(float(number))
    except (TypeError, ValueError):
        raise ValueError("number must be a match number from find_on_screen.")

    item = next(
        (item for item in _last_matches["items"] if item["id"] == index),
        None,
    )

    if item is None:
        return (
            f"There is no match number {index}. "
            "Call find_on_screen first."
        )

    # Don't click blind if the screen moved since it was read.
    current = _fingerprint(pyautogui.screenshot())

    previous = _last_matches.get("fingerprint")

    if (
        previous is not None
        and _fingerprint_distance(previous, current) > _STALE_LEVEL
    ):
        return (
            "The screen changed since I looked, so I did not click. "
            "Call find_on_screen again."
        )

    pyautogui.moveTo(item["x"], item["y"], duration=0.15)

    if _as_bool(double):
        pyautogui.doubleClick()
        verb = "Double-clicked"
    else:
        pyautogui.click()
        verb = "Clicked"

    return f"{verb} [{index}] '{item['text']}' in the {item['region']}."


def read_screen():
    """
    Visible text grouped by screen area, in reading order.
    Compact on purpose: it is read by a small model.
    """

    _, elements = _screen_words()

    size = _screen_info["size"] or pyautogui.size()

    areas = {
        "top bar": [],
        "left panel": [],
        "main area": [],
        "right panel": [],
        "bottom bar": [],
    }

    budget = {
        "top bar": 250,
        "left panel": 300,
        "main area": 600,
        "right panel": 150,
        "bottom bar": 100,
    }

    for element in elements:

        text = str(element.get("text", "")).strip()

        if len(text) < 2 or not any(ch.isalnum() for ch in text):
            continue

        if element.get("confidence", 100) < 50:
            continue

        areas[
            _region_of(element["x"], element["y"], size)
        ].append(element)

    lines = [f"Screen {size[0]}x{size[1]}. Visible text:"]

    for area, items in areas.items():

        if not items:
            continue

        items.sort(key=lambda e: (round(e["y"] / 18), e["x"]))

        joined = " | ".join(item["text"] for item in items)

        if len(joined) > budget[area]:
            joined = joined[: budget[area]].rsplit(" | ", 1)[0] + " | ..."

        lines.append(f"[{area}] {joined}")

    if len(lines) == 1:
        return "I can't read any text on the screen."

    return "\n".join(lines)
