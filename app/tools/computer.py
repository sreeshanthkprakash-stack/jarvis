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

def open_url(url):
    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL must be a non-empty string.")

    url = url.strip()

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


def _get_ocr_data():
    """
    Capture the current screen and run
    local Tesseract OCR.

    No external API is used.
    """

    screenshot = pyautogui.screenshot()

    return pytesseract.image_to_data(
        screenshot,
        output_type=pytesseract.Output.DICT,
        config="--psm 11",
    )


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