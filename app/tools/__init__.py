# pyrefly: ignore [missing-import]
from app.tool_registry import ToolRegistry


# ============================================================
# SYSTEM TOOLS
# ============================================================

# pyrefly: ignore [missing-import]
from app.tools.system import (
    get_time,
    get_date,
    get_system_info,
    lock_computer,
    sleep_computer,
    volume_up,
    volume_down,
    mute_volume,
    take_screenshot,
    get_clipboard,
    set_clipboard,
)


# ============================================================
# APPLICATION TOOLS
# ============================================================

# pyrefly: ignore [missing-import]
from app.tools.apps import (
    open_application,
    close_application,
)


# ============================================================
# COMPUTER CONTROL TOOLS
# ============================================================

# pyrefly: ignore [missing-import]
from app.tools.computer import (
    open_url,
    open_website,
    type_text,
    press_key,
    hotkey,
    move_mouse,
    click_mouse,
    wait,
    get_screen_size,
    take_screen_capture,

    # Basic OCR
    find_text_on_screen,
    click_text_on_screen,
    observe_screen,

    # Multiple OCR matches
    find_all_text_on_screen,
    find_topmost_text_on_screen,
    find_bottommost_text_on_screen,
    click_topmost_text_on_screen,

    # Spatial OCR relationships
    find_text_below,
    find_text_above,
    find_text_left_of,
    find_text_right_of,
    click_text_below,
    click_text_above,
    click_text_left_of,
    click_text_right_of,
    describe_screen,
)


# ============================================================
# MEMORY TOOLS
# ============================================================

# pyrefly: ignore [missing-import]
from app.tools.memory import (
    remember_fact,
    get_fact,
    forget_fact,
    remember_preference,
    get_preference,
    forget_preference,
    add_note,
    get_notes,
    clear_notes,
    list_memory,
)


# ============================================================
# AUTOMATION
# ============================================================

# pyrefly: ignore [missing-import]
from app.tools.automation import (
    register_automation_tools,
)


# ============================================================
# TOOL REGISTRATION
# ============================================================

def register_tools(registry: ToolRegistry):

    memory = registry.memory


    # ========================================================
    # SYSTEM TOOLS
    # ========================================================

    registry.register(
        "get_time",
        get_time,
        "Get the current local time.",
        {},
    )

    registry.register(
        "get_date",
        get_date,
        "Get the current local date.",
        {},
    )

    registry.register(
        "get_system_info",
        get_system_info,
        "Get information about the computer system.",
        {},
    )

    registry.register(
        "lock_computer",
        lock_computer,
        "Lock the Windows computer.",
        {},
    )

    registry.register(
        "sleep_computer",
        sleep_computer,
        "Put the Windows computer to sleep.",
        {},
    )

    registry.register(
        "volume_up",
        volume_up,
        "Increase the system volume.",
        {},
    )

    registry.register(
        "volume_down",
        volume_down,
        "Decrease the system volume.",
        {},
    )

    registry.register(
        "mute_volume",
        mute_volume,
        "Mute or unmute the system volume.",
        {},
    )

    registry.register(
        "take_screenshot",
        take_screenshot,
        "Take a screenshot of the current screen.",
        {},
    )

    registry.register(
        "get_clipboard",
        get_clipboard,
        "Read the current clipboard contents.",
        {},
    )

    registry.register(
        "set_clipboard",
        set_clipboard,
        "Set text in the Windows clipboard.",
        {
            "text": {
                "type": "string",
                "description": (
                    "The text to place in the clipboard."
                ),
            }
        },
    )


    # ========================================================
    # APPLICATION TOOLS
    # ========================================================

    registry.register(
        "open_application",
        open_application,
        "Find and open an installed Windows application.",
        {
            "application": {
                "type": "string",
                "description": (
                    "The application name to open."
                ),
            }
        },
    )

    registry.register(
        "close_application",
        close_application,
        "Find and close a running Windows application.",
        {
            "application": {
                "type": "string",
                "description": (
                    "The application name to close."
                ),
            }
        },
    )


    # ========================================================
    # COMPUTER CONTROL TOOLS
    # ========================================================

    registry.register(
        "open_url",
        open_url,
        "Open a URL in the default web browser.",
        {
            "url": {
                "type": "string",
                "description": "The URL to open.",
            }
        },
    )

    registry.register(
        "open_website",
        open_website,
        "Open a website in the default web browser.",
        {
            "website": {
                "type": "string",
                "description": (
                    "The website name or URL to open."
                ),
            }
        },
    )

    registry.register(
        "type_text",
        type_text,
        "Type text into the currently focused application.",
        {
            "text": {
                "type": "string",
                "description": "The text to type.",
            }
        },
    )

    registry.register(
        "press_key",
        press_key,
        "Press a keyboard key.",
        {
            "key": {
                "type": "string",
                "description": (
                    "The keyboard key to press."
                ),
            }
        },
    )

    registry.register(
        "hotkey",
        hotkey,
        "Press a keyboard shortcut.",
        {
            "keys": {
                "type": "string",
                "description": (
                    "Keyboard shortcut such as "
                    "ctrl+l or alt+f4."
                ),
            }
        },
    )

    registry.register(
        "move_mouse",
        move_mouse,
        "Move the mouse to a screen coordinate.",
        {
            "x": {
                "type": "integer",
                "description": (
                    "Horizontal screen coordinate."
                ),
            },
            "y": {
                "type": "integer",
                "description": (
                    "Vertical screen coordinate."
                ),
            },
        },
    )

    registry.register(
        "click_mouse",
        click_mouse,
        "Click the mouse, optionally at a screen coordinate.",
        {
            "x": {
                "type": "integer",
                "description": (
                    "Horizontal screen coordinate."
                ),
            },
            "y": {
                "type": "integer",
                "description": (
                    "Vertical screen coordinate."
                ),
            },
            "button": {
                "type": "string",
                "description": (
                    "Mouse button: left, right, or middle."
                ),
            },
        },
    )

    registry.register(
        "wait",
        wait,
        "Wait for an application or webpage to load.",
        {
            "seconds": {
                "type": "number",
                "description": (
                    "Number of seconds to wait."
                ),
            }
        },
    )

    registry.register(
        "get_screen_size",
        get_screen_size,
        "Get the current screen resolution.",
        {},
    )

    registry.register(
        "take_screen_capture",
        take_screen_capture,
        "Capture the current screen.",
        {
            "path": {
                "type": "string",
                "description": (
                    "Path where the screen capture "
                    "should be saved."
                ),
            }
        },
    )


    # ========================================================
    # SCREEN OBSERVATION / OCR
    # ========================================================

    registry.register(
        "observe_screen",
        observe_screen,
        (
            "Observe the current computer screen locally "
            "using OCR. Returns visible text, approximate "
            "coordinates, confidence, and screen dimensions. "
            "No external API is used."
        ),
        {},
    )

    registry.register(
        "find_text_on_screen",
        find_text_on_screen,
        (
            "Use local OCR to find visible text on the "
            "current screen and return its approximate "
            "location. No external API is used."
        ),
        {
            "text": {
                "type": "string",
                "description": (
                    "Visible text to find on the screen."
                ),
            }
        },
    )

    registry.register(
        "click_text_on_screen",
        click_text_on_screen,
        (
            "Use local OCR to find visible text on the "
            "current screen and click it with the mouse. "
            "No external API is used."
        ),
        {
            "text": {
                "type": "string",
                "description": (
                    "Visible text to click on the screen."
                ),
            }
        },
    )

    registry.register(
        "find_all_text_on_screen",
        find_all_text_on_screen,
        (
            "Find every exact occurrence of visible text "
            "on the current screen using local OCR. "
            "Returns text, coordinates, dimensions, "
            "and confidence. No external API is used."
        ),
        {
            "text": {
                "type": "string",
                "description": "Exact visible text to find.",
            },
        },
    )

    registry.register(
        "find_topmost_text_on_screen",
        find_topmost_text_on_screen,
        (
            "Find the topmost exact occurrence of visible "
            "text on the current screen using local OCR "
            "and screen coordinates. No external API is used."
        ),
        {
            "text": {
                "type": "string",
                "description": "Exact visible text to find.",
            },
        },
    )

    registry.register(
        "find_bottommost_text_on_screen",
        find_bottommost_text_on_screen,
        (
            "Find the bottommost exact occurrence of visible "
            "text on the current screen using local OCR "
            "and screen coordinates. No external API is used."
        ),
        {
            "text": {
                "type": "string",
                "description": "Exact visible text to find.",
            },
        },
    )

    registry.register(
        "click_topmost_text_on_screen",
        click_topmost_text_on_screen,
        (
            "Find and click the topmost exact occurrence "
            "of visible text using local OCR and coordinates. "
            "No external API is used."
        ),
        {
            "text": {
                "type": "string",
                "description": "Exact visible text to click.",
            },
        },
    )


    # ========================================================
    # SPATIAL OCR RELATIONSHIPS
    # ========================================================

    registry.register(
        "find_text_below",
        find_text_below,
        (
            "Find visible text located below a reference "
            "text element using local OCR and screen "
            "coordinates. No external API is used."
        ),
        {
            "reference_text": {
                "type": "string",
                "description": (
                    "Visible text to use as the reference."
                ),
            },
            "target_text": {
                "type": "string",
                "description": (
                    "Visible text to find below the reference."
                ),
            },
        },
    )

    registry.register(
        "find_text_above",
        find_text_above,
        (
            "Find visible text located above a reference "
            "text element using local OCR and screen "
            "coordinates. No external API is used."
        ),
        {
            "reference_text": {
                "type": "string",
                "description": (
                    "Visible text to use as the reference."
                ),
            },
            "target_text": {
                "type": "string",
                "description": (
                    "Visible text to find above the reference."
                ),
            },
        },
    )

    registry.register(
        "find_text_left_of",
        find_text_left_of,
        (
            "Find visible text located left of a reference "
            "text element using local OCR and screen "
            "coordinates. No external API is used."
        ),
        {
            "reference_text": {
                "type": "string",
                "description": (
                    "Visible text to use as the reference."
                ),
            },
            "target_text": {
                "type": "string",
                "description": (
                    "Visible text to find left of the reference."
                ),
            },
        },
    )

    registry.register(
        "find_text_right_of",
        find_text_right_of,
        (
            "Find visible text located right of a reference "
            "text element using local OCR and screen "
            "coordinates. No external API is used."
        ),
        {
            "reference_text": {
                "type": "string",
                "description": (
                    "Visible text to use as the reference."
                ),
            },
            "target_text": {
                "type": "string",
                "description": (
                    "Visible text to find right of the reference."
                ),
            },
        },
    )

    registry.register(
        "click_text_below",
        click_text_below,
        (
            "Find and click visible text located below "
            "a reference text element using local OCR. "
            "No external API is used."
        ),
        {
            "reference_text": {
                "type": "string",
                "description": (
                    "Visible text to use as the reference."
                ),
            },
            "target_text": {
                "type": "string",
                "description": (
                    "Visible text to click below the reference."
                ),
            },
        },
    )

    registry.register(
        "click_text_above",
        click_text_above,
        (
            "Find and click visible text located above "
            "a reference text element using local OCR. "
            "No external API is used."
        ),
        {
            "reference_text": {
                "type": "string",
                "description": (
                    "Visible text to use as the reference."
                ),
            },
            "target_text": {
                "type": "string",
                "description": (
                    "Visible text to click above the reference."
                ),
            },
        },
    )

    registry.register(
        "click_text_left_of",
        click_text_left_of,
        (
            "Find and click visible text located left "
            "of a reference text element using local OCR. "
            "No external API is used."
        ),
        {
            "reference_text": {
                "type": "string",
                "description": (
                    "Visible text to use as the reference."
                ),
            },
            "target_text": {
                "type": "string",
                "description": (
                    "Visible text to click left of the reference."
                ),
            },
        },
    )

    registry.register(
        "click_text_right_of",
        click_text_right_of,
        (
            "Find and click visible text located right "
            "of a reference text element using local OCR. "
            "No external API is used."
        ),
        {
            "reference_text": {
                "type": "string",
                "description": (
                    "Visible text to use as the reference."
                ),
            },
            "target_text": {
                "type": "string",
                "description": (
                    "Visible text to click right of the reference."
                ),
            },
        },
    )


    # ========================================================
    # MEMORY TOOLS
    # ========================================================

    registry.register(
        "remember_fact",
        lambda key, value: remember_fact(
            memory,
            key,
            value,
        ),
        "Store a long-term fact about the user.",
        {
            "key": {
                "type": "string",
                "description": (
                    "The semantic name of the fact."
                ),
            },
            "value": {
                "type": "string",
                "description": (
                    "The value to remember."
                ),
            },
        },
    )

    registry.register(
        "get_fact",
        lambda key: get_fact(
            memory,
            key,
        ),
        "Retrieve a stored fact.",
        {
            "key": {
                "type": "string",
                "description": (
                    "The semantic name of the fact."
                ),
            },
        },
    )

    registry.register(
        "forget_fact",
        lambda key: forget_fact(
            memory,
            key,
        ),
        "Forget a stored fact.",
        {
            "key": {
                "type": "string",
                "description": (
                    "The semantic name of the fact."
                ),
            },
        },
    )

    registry.register(
        "remember_preference",
        lambda key, value: remember_preference(
            memory,
            key,
            value,
        ),
        "Store a long-term user preference.",
        {
            "key": {
                "type": "string",
                "description": (
                    "The semantic name of the preference."
                ),
            },
            "value": {
                "type": "string",
                "description": (
                    "The preference value."
                ),
            },
        },
    )

    registry.register(
        "get_preference",
        lambda key: get_preference(
            memory,
            key,
        ),
        "Retrieve a stored user preference.",
        {
            "key": {
                "type": "string",
                "description": (
                    "The semantic name of the preference."
                ),
            },
        },
    )

    registry.register(
        "forget_preference",
        lambda key: forget_preference(
            memory,
            key,
        ),
        "Forget a stored user preference.",
        {
            "key": {
                "type": "string",
                "description": (
                    "The semantic name of the preference."
                ),
            },
        },
    )

    registry.register(
        "add_note",
        lambda note: add_note(
            memory,
            note,
        ),
        "Save a note to long-term memory.",
        {
            "note": {
                "type": "string",
                "description": "The note text to save.",
            },
        },
    )

    registry.register(
        "get_notes",
        lambda: get_notes(memory),
        "Retrieve all saved notes.",
        {},
    )

    registry.register(
        "clear_notes",
        lambda: clear_notes(memory),
        "Delete all saved notes.",
        {},
    )

    registry.register(
        "list_memory",
        lambda: list_memory(memory),
        "List all stored facts, preferences, and notes.",
        {},
    )

    registry.register(
        "describe_screen",
        describe_screen,
        description=(
            "Observe the current Windows screen using local OCR "
            "and return visible text elements with their "
            "screen coordinates and confidence."
        ),
        parameters={},
    )

    # ========================================================
    # GENERIC AUTOMATION
    # ========================================================

    register_automation_tools(registry)