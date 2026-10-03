import re
import time
from urllib.parse import quote_plus

# pyrefly: ignore [missing-import]
from app.tool_registry import ToolRegistry
# pyrefly: ignore [missing-import]
from app.tools import register_tools
# pyrefly: ignore [missing-import]
from app.computer_agent import ComputerAgent


class JarvisRouter:

    def __init__(self, brain):
        self.brain = brain
        self.last_opened_application = None

        self.registry = ToolRegistry(
            memory=self.brain.persistent_memory
        )

        register_tools(self.registry)

        self.computer_agent = ComputerAgent(
            self.registry,
            self.brain,
        )

        self.brain.set_tool_registry(
            self.registry
        )

    # ============================================================
    # MAIN ROUTER
    # ============================================================

    def handle(self, user_input):

        if not isinstance(
            user_input,
            str,
        ):
            return ""

        user_input = user_input.strip()

        if not user_input:
            return ""

        # --------------------------------------------------------
        # LOCAL COMPOUND COMPUTER COMMAND
        # --------------------------------------------------------
        # Compound commands MUST be checked before the generic
        # click parser. Otherwise a command such as:
        #
        #     click Search and type AI agents
        #
        # would be interpreted as one giant OCR target.

        compound_result = self.local_compound_intent(
            user_input
        )

        if compound_result is not None:

            action, arguments = compound_result

            return self.execute(
                action,
                arguments,
            )

        # --------------------------------------------------------
        # LOCAL UI
        # --------------------------------------------------------

        ui_result = self.local_ui_intent(
            user_input
        )

        if ui_result is not None:

            action, arguments = ui_result

            return self.execute(
                action,
                arguments,
            )

        # --------------------------------------------------------
        # LOCAL DETERMINISTIC COMMAND
        # --------------------------------------------------------

        local_result = self.local_intent(
            user_input
        )

        if local_result is not None:

            action, arguments = local_result

            return self.execute(
                action,
                arguments,
            )

        # --------------------------------------------------------
        # AI INTENT ENGINE
        # --------------------------------------------------------

        if self.is_local_computer_command(user_input):
            return self.execute_local_computer_command(user_input)

        decision = self.brain.understand(
            user_input
        )

        if not isinstance(
            decision,
            dict,
        ):
            return "I couldn't understand that request."

        action = decision.get(
            "action"
        )

        arguments = decision.get(
            "arguments",
            {},
        )

        if not isinstance(
            arguments,
            dict,
        ):
            arguments = {}

        # --------------------------------------------------------
        # AI QUERY
        # --------------------------------------------------------

        if action == "AI_QUERY":

            return self.brain.ask(
                user_input
            )

        # --------------------------------------------------------
        # REGISTERED TOOL
        # --------------------------------------------------------

        return self.execute(
            action,
            arguments,
        )

    # ============================================================
    # LOCAL COMPUTER GOAL
    # ============================================================

    def execute_computer_goal(
        self,
        goal,
        actions,
    ):

        return self.computer_agent.execute_goal(
            goal=goal,
            actions=actions,
        )

    # ============================================================
    # LOCAL UI INTENT
    # ============================================================

    def local_ui_intent(
        self,
        user_input,
    ):

        if not isinstance(
            user_input,
            str,
        ):
            return None

        original = user_input.strip()

        if not original:
            return None

        # --------------------------------------------------------
        # MUST BEGIN WITH CLICK
        # --------------------------------------------------------

        match = re.match(
            r"^click\s+(.+)$",
            original,
            re.IGNORECASE,
        )

        if not match:
            return None

        target = match.group(
            1
        ).strip()

        if not target:
            return None

        # --------------------------------------------------------
        # POSITIONAL CLICK
        #
        # click topmost Search
        # click bottommost Search
        # click leftmost Search
        # click rightmost Search
        # --------------------------------------------------------

        position_match = re.match(
            r"^(topmost|bottommost|leftmost|rightmost)\s+(.+)$",
            target,
            re.IGNORECASE,
        )

        if position_match:

            position = (
                position_match.group(
                    1
                )
                .lower()
                .strip()
            )

            target = (
                position_match.group(
                    2
                )
                .strip()
            )

            if not target:
                return None

            return (
                "computer_click_target",
                {
                    "target": target,
                    "position": position,
                },
            )

        # --------------------------------------------------------
        # SPATIAL CLICK
        #
        # click below Settings
        # click above Login
        # click left of Search
        # click right of Menu
        # --------------------------------------------------------

        spatial_match = re.match(
            r"^(below|above|left\s+of|right\s+of)\s+(.+)$",
            target,
            re.IGNORECASE,
        )

        if spatial_match:

            relationship = (
                spatial_match.group(
                    1
                )
                .lower()
                .strip()
            )

            reference_text = (
                spatial_match.group(
                    2
                )
                .strip()
            )

            if not reference_text:
                return None

            relationship = relationship.replace(
                " ",
                "_",
            )

            return (
                "computer_click_spatial",
                {
                    "relationship": relationship,
                    "reference_text": reference_text,
                },
            )

        # --------------------------------------------------------
        # NORMAL CLICK
        # --------------------------------------------------------

        return (
            "computer_click_target",
            {
                "target": target,
                "position": "first",
            },
        )

    # ============================================================
    # OCR NORMALIZATION
    # ============================================================

    def _normalize_ocr_text(
        self,
        text,
    ):

        if text is None:
            return ""

        text = str(
            text
        ).lower().strip()

        text = re.sub(
            r"[^a-z0-9]+",
            " ",
            text,
        )

        return " ".join(
            text.split()
        )

    # ============================================================
    # FIND OCR ELEMENT
    # ============================================================

    def _find_ocr_element(
        self,
        elements,
        text,
    ):

        """
        Strict OCR matching.

        IMPORTANT:
        Only exact normalized OCR matches are accepted.

        This prevents:

            Search

        from matching unrelated OCR such as:

            search'))
            searching
            print(search_result)
        """

        target = self._normalize_ocr_text(
            text
        )

        if not target:
            return None

        matches = []

        for element in elements:

            if not isinstance(
                element,
                dict,
            ):
                continue

            value = self._normalize_ocr_text(
                element.get(
                    "text",
                    "",
                )
            )

            if not value:
                continue

            # ----------------------------------------------------
            # STRICT EXACT MATCH
            # ----------------------------------------------------

            if value == target:

                matches.append(
                    element
                )

        # --------------------------------------------------------
        # NO EXACT MATCH
        # --------------------------------------------------------

        if not matches:
            return None

        # Prefer highest-confidence exact match.

        matches.sort(
            key=lambda item: float(
                item.get(
                    "confidence",
                    0,
                )
                or 0
            ),
            reverse=True,
        )

        return matches[0]

    # ============================================================
    # SELECT SPATIAL CANDIDATE
    # ============================================================

    def _select_spatial_candidate(
        self,
        elements,
        reference,
        relationship,
    ):

        rx = reference.get(
            "x"
        )

        ry = reference.get(
            "y"
        )

        if rx is None or ry is None:
            return None

        rleft = reference.get(
            "left"
        )

        rtop = reference.get(
            "top"
        )

        rwidth = (
            reference.get(
                "width",
                0,
            )
            or 0
        )

        rheight = (
            reference.get(
                "height",
                0,
            )
            or 0
        )

        rright = (
            rleft + rwidth
            if rleft is not None
            else rx
        )

        rbottom = (
            rtop + rheight
            if rtop is not None
            else ry
        )

        candidates = []

        for element in elements:

            if not isinstance(
                element,
                dict,
            ):
                continue

            if element is reference:
                continue

            x = element.get(
                "x"
            )

            y = element.get(
                "y"
            )

            if x is None or y is None:
                continue

            left = element.get(
                "left"
            )

            top = element.get(
                "top"
            )

            width = (
                element.get(
                    "width",
                    0,
                )
                or 0
            )

            height = (
                element.get(
                    "height",
                    0,
                )
                or 0
            )

            right = (
                left + width
                if left is not None
                else x
            )

            bottom = (
                top + height
                if top is not None
                else y
            )

            # ----------------------------------------------------
            # BELOW
            # ----------------------------------------------------

            if relationship == "below":

                if y <= ry:
                    continue

                overlap = (
                    left is not None
                    and rleft is not None
                    and left <= rright
                    and right >= rleft
                )

                primary = y - ry
                secondary = abs(
                    x - rx
                )

            # ----------------------------------------------------
            # ABOVE
            # ----------------------------------------------------

            elif relationship == "above":

                if y >= ry:
                    continue

                overlap = (
                    left is not None
                    and rleft is not None
                    and left <= rright
                    and right >= rleft
                )

                primary = ry - y
                secondary = abs(
                    x - rx
                )

            # ----------------------------------------------------
            # LEFT
            # ----------------------------------------------------

            elif relationship == "left_of":

                if x >= rx:
                    continue

                overlap = (
                    top is not None
                    and rtop is not None
                    and top <= rbottom
                    and bottom >= rtop
                )

                primary = rx - x
                secondary = abs(
                    y - ry
                )

            # ----------------------------------------------------
            # RIGHT
            # ----------------------------------------------------

            elif relationship == "right_of":

                if x <= rx:
                    continue

                overlap = (
                    top is not None
                    and rtop is not None
                    and top <= rbottom
                    and bottom >= rtop
                )

                primary = x - rx
                secondary = abs(
                    y - ry
                )

            else:
                continue

            # ----------------------------------------------------
            # OVERLAPPING ELEMENTS GET PRIORITY
            # ----------------------------------------------------

            score = (
                0 if overlap else 1,
                primary,
                secondary,
            )

            candidates.append(
                (
                    score,
                    element,
                )
            )

        if not candidates:
            return None

        candidates.sort(
            key=lambda item: item[0]
        )

        return candidates[0][1]

    # ============================================================
    # RAW SPATIAL CLICK
    # ============================================================

    def _click_spatial_element(
        self,
        reference_text,
        relationship,
    ):

        screen = self.computer_agent.observe()

        if not isinstance(
            screen,
            dict,
        ):

            return {
                "success": False,
                "message": (
                    "Could not observe the screen."
                ),
            }

        elements = screen.get(
            "elements",
            [],
        )

        if not isinstance(
            elements,
            list,
        ):

            return {
                "success": False,
                "message": (
                    "Screen observation contained "
                    "no OCR elements."
                ),
            }

        # --------------------------------------------------------
        # FIND EXACT REFERENCE
        # --------------------------------------------------------

        reference = self._find_ocr_element(
            elements,
            reference_text,
        )

        if reference is None:

            return {
                "success": False,
                "message": (
                    f"Could not find reference "
                    f"'{reference_text}' on the screen."
                ),
            }

        # --------------------------------------------------------
        # FIND SPATIAL CANDIDATE
        # --------------------------------------------------------

        candidate = (
            self._select_spatial_candidate(
                elements,
                reference,
                relationship,
            )
        )

        if candidate is None:

            return {
                "success": False,
                "message": (
                    f"Could not find an element "
                    f"{relationship.replace('_', ' ')} "
                    f"'{reference_text}'."
                ),
                "reference": reference,
            }

        x = candidate.get(
            "x"
        )

        y = candidate.get(
            "y"
        )

        if x is None or y is None:

            return {
                "success": False,
                "message": (
                    "Selected element has no "
                    "screen coordinates."
                ),
                "reference": reference,
                "candidate": candidate,
            }

        # --------------------------------------------------------
        # ACTUAL MOUSE CLICK
        # --------------------------------------------------------

        result = self.registry.execute(
            "click_mouse",
            {
                "x": x,
                "y": y,
                "button": "left",
            },
        )

        return {
            "success": True,
            "relationship": relationship,
            "reference": reference,
            "candidate": candidate,
            "click": {
                "x": x,
                "y": y,
            },
            "result": result,
        }

    # ============================================================
    # LOCAL COMPOUND COMPUTER COMMANDS
    # ============================================================

    def local_compound_intent(
        self,
        user_input,
    ):

        if not isinstance(
            user_input,
            str,
        ):
            return None

        original = user_input.strip()

        if not original:
            return None

        text = self.normalize(
            original
        )

        if " and " not in text:
            return None

        # --------------------------------------------------------
        # CLICK + TYPE
        # --------------------------------------------------------
        # Example:
        #     click Search and type AI agents
        #
        # This must be converted into two independent local
        # computer actions. The generic click parser must never
        # receive the entire sentence as an OCR target.

        match = re.match(
            r"^click\s+(.+?)\s+and\s+(?:type|write)\s+(.+)$",
            original,
            re.IGNORECASE,
        )

        if match:

            target = match.group(1).strip()
            content = match.group(2).strip()

            if target and content:

                return (
                    "run_actions",
                    {
                        "actions": [
                            {
                                "action": "click_text_on_screen",
                                "arguments": {
                                    "text": target,
                                },
                            },
                            {
                                "action": "type_text",
                                "arguments": {
                                    "text": content,
                                },
                            },
                        ],
                    },
                )

        # --------------------------------------------------------
        # CLICK + PRESS
        # --------------------------------------------------------
        # Example:
        #     click Search and press Enter

        match = re.match(
            r"^click\s+(.+?)\s+and\s+press\s+(.+)$",
            original,
            re.IGNORECASE,
        )

        if match:

            target = match.group(1).strip()
            key = match.group(2).strip()

            if target and key:

                return (
                    "run_actions",
                    {
                        "actions": [
                            {
                                "action": "click_text_on_screen",
                                "arguments": {
                                    "text": target,
                                },
                            },
                            {
                                "action": "press_key",
                                "arguments": {
                                    "key": key,
                                },
                            },
                        ],
                    },
                )

        # --------------------------------------------------------
        # SEARCH + CLICK / OPEN
        # --------------------------------------------------------
        # Example:
        #     search cats and click on cats
        #     search cats and open cats
        #
        # Search first, wait for the page, then use exact OCR
        # matching for the requested visible target.

        match = re.match(
            r"^search(?:\s+for)?\s+(.+?)\s+and\s+(?:click(?:\s+on)?|open)\s+(.+)$",
            original,
            re.IGNORECASE,
        )

        if match:

            query = match.group(1).strip()
            target = match.group(2).strip()

            if query and target:

                search_url = (
                    "https://www.google.com/search?q="
                    + quote_plus(query)
                )

                return (
                    "run_actions",
                    {
                        "actions": [
                            {
                                "action": "open_url",
                                "arguments": {
                                    "url": search_url,
                                },
                            },
                            {
                                "action": "wait",
                                "arguments": {
                                    "seconds": 2,
                                },
                            },
                            {
                                "action": "click_text_on_screen",
                                "arguments": {
                                    "text": target,
                                },
                            },
                        ],
                    },
                )

        # --------------------------------------------------------
        # OPEN + TYPE
        # --------------------------------------------------------

        match = re.match(
            r"^open\s+(.+?)\s+and\s+"
            r"(?:type|write)\s+(.+)$",
            original,
            re.IGNORECASE,
        )

        if match:

            application = (
                match.group(1).strip()
            )

            content = (
                match.group(2).strip()
            )

            application = (
                self.clean_application_name(
                    application
                )
            )

            if application and content:

                return (
                    "run_actions",
                    {
                        "actions": [
                            {
                                "action":
                                    "open_application",
                                "arguments": {
                                    "application":
                                        application,
                                },
                            },
                            {
                                "action": "wait",
                                "arguments": {
                                    "seconds": 1.5,
                                },
                            },
                            {
                                "action": "type_text",
                                "arguments": {
                                    "text": content,
                                },
                            },
                        ],
                    },
                )

        # --------------------------------------------------------
        # OPEN + PRESS
        # --------------------------------------------------------

        match = re.match(
            r"^open\s+(.+?)\s+and\s+"
            r"press\s+(.+)$",
            original,
            re.IGNORECASE,
        )

        if match:

            application = (
                match.group(1).strip()
            )

            key = (
                match.group(2).strip()
            )

            application = (
                self.clean_application_name(
                    application
                )
            )

            if application and key:

                return (
                    "run_actions",
                    {
                        "actions": [
                            {
                                "action":
                                    "open_application",
                                "arguments": {
                                    "application":
                                        application,
                                },
                            },
                            {
                                "action": "wait",
                                "arguments": {
                                    "seconds": 1.5,
                                },
                            },
                            {
                                "action": "press_key",
                                "arguments": {
                                    "key": key,
                                },
                            },
                        ],
                    },
                )

        # --------------------------------------------------------
        # OPEN + GO TO URL
        # --------------------------------------------------------

        match = re.match(
            r"^open\s+(.+?)\s+and\s+"
            r"(?:go\s+to|navigate\s+to|visit)\s+(.+)$",
            original,
            re.IGNORECASE,
        )

        if match:

            application = (
                match.group(1).strip()
            )

            destination = (
                match.group(2).strip()
            )

            application = (
                self.clean_application_name(
                    application
                )
            )

            if application and destination:

                url = self.normalize_url(
                    destination
                )

                if url:

                    return (
                        "run_actions",
                        {
                            "actions": [
                                {
                                    "action":
                                        "open_application",
                                    "arguments": {
                                        "application":
                                            application,
                                    },
                                },
                                {
                                    "action": "wait",
                                    "arguments": {
                                        "seconds": 1.5,
                                    },
                                },
                                {
                                    "action": "hotkey",
                                    "arguments": {
                                        "keys": "ctrl+l",
                                    },
                                },
                                {
                                    "action": "type_text",
                                    "arguments": {
                                        "text": url,
                                    },
                                },
                                {
                                    "action": "press_key",
                                    "arguments": {
                                        "key": "enter",
                                    },
                                },
                            ],
                        },
                    )

        # --------------------------------------------------------
        # OPEN + WAIT
        # --------------------------------------------------------

        match = re.match(
            r"^open\s+(.+?)\s+and\s+wait$",
            original,
            re.IGNORECASE,
        )

        if match:

            application = (
                match.group(1).strip()
            )

            application = (
                self.clean_application_name(
                    application
                )
            )

            if application:

                return (
                    "run_actions",
                    {
                        "actions": [
                            {
                                "action":
                                    "open_application",
                                "arguments": {
                                    "application":
                                        application,
                                },
                            },
                            {
                                "action": "wait",
                                "arguments": {
                                    "seconds": 2,
                                },
                            },
                        ],
                    },
                )

        return None

    # ============================================================
    # URL NORMALIZATION
    # ============================================================

    def normalize_url(
        self,
        value,
    ):

        if not isinstance(
            value,
            str,
        ):
            return None

        value = value.strip()

        if not value:
            return None

        if re.match(
            r"^https?://",
            value,
            re.IGNORECASE,
        ):
            return value

        if re.match(
            r"^(www\.)?[a-z0-9-]+"
            r"(\.[a-z0-9-]+)+"
            r"([/?#].*)?$",
            value,
            re.IGNORECASE,
        ):
            return "https://" + value

        return None

    # ============================================================
    # DETERMINISTIC LOCAL INTENT
    # ============================================================

    def local_intent(
        self,
        user_input,
    ):

        if not isinstance(
            user_input,
            str,
        ):
            return None

        text = self.normalize(
            user_input
        )

        # --------------------------------------------------------
        # SCREEN OBSERVATION
        # --------------------------------------------------------

        if text in {
            "what's on my screen",
            "what is on my screen",
            "show me what's on my screen",
            "show me what is on my screen",
            "describe my screen",
            "describe the screen",
            "what do you see",
        }:
            return (
                "describe_screen",
                {},
            )

        # --------------------------------------------------------
        # MEMORY
        # --------------------------------------------------------

        memory_result = (
            self.extract_memory_command(
                text,
                user_input,
            )
        )

        if memory_result is not None:
            return memory_result

        # --------------------------------------------------------
        # TIME
        # --------------------------------------------------------

        if self.is_time_request(
            text
        ):

            return (
                "get_time",
                {},
            )

        # --------------------------------------------------------
        # DATE
        # --------------------------------------------------------

        if self.is_date_request(
            text
        ):

            return (
                "get_date",
                {},
            )

        # --------------------------------------------------------
        # SYSTEM INFO
        # --------------------------------------------------------

        if self.is_system_info_request(
            text
        ):

            return (
                "get_system_info",
                {},
            )

        # --------------------------------------------------------
        # LOCK
        # --------------------------------------------------------

        if self.matches_command(
            text,
            {
                "lock computer",
                "lock pc",
                "lock my computer",
                "lock my pc",
            },
        ):

            return (
                "lock_computer",
                {},
            )

        # --------------------------------------------------------
        # SLEEP
        # --------------------------------------------------------

        if self.matches_command(
            text,
            {
                "sleep computer",
                "sleep pc",
                "put computer to sleep",
                "put pc to sleep",
            },
        ):

            return (
                "sleep_computer",
                {},
            )

        # --------------------------------------------------------
        # VOLUME UP
        # --------------------------------------------------------

        if self.matches_command(
            text,
            {
                "volume up",
                "increase volume",
                "turn volume up",
            },
        ):

            return (
                "volume_up",
                {},
            )

        # --------------------------------------------------------
        # VOLUME DOWN
        # --------------------------------------------------------

        if self.matches_command(
            text,
            {
                "volume down",
                "decrease volume",
                "turn volume down",
            },
        ):

            return (
                "volume_down",
                {},
            )

        # --------------------------------------------------------
        # MUTE
        # --------------------------------------------------------

        if self.matches_command(
            text,
            {
                "mute",
                "mute volume",
                "mute computer",
            },
        ):

            return (
                "mute_volume",
                {},
            )

        # --------------------------------------------------------
        # SCREENSHOT
        # --------------------------------------------------------

        if self.matches_command(
            text,
            {
                "take screenshot",
                "screenshot",
                "capture screen",
                "capture screenshot",
            },
        ):

            return (
                "take_screenshot",
                {},
            )

        # --------------------------------------------------------
        # CLIPBOARD READ
        # --------------------------------------------------------

        if self.matches_command(
            text,
            {
                "get clipboard",
                "read clipboard",
                "show clipboard",
            },
        ):

            return (
                "get_clipboard",
                {},
            )

        # --------------------------------------------------------
        # CLIPBOARD WRITE
        # --------------------------------------------------------

        clipboard_text = (
            self.extract_clipboard_command(
                text,
                user_input,
            )
        )

        if clipboard_text is not None:

            return (
                "set_clipboard",
                {
                    "text": clipboard_text,
                },
            )

        # --------------------------------------------------------
        # SIMPLE WEB SEARCH
        # --------------------------------------------------------

        search_query = (
            self.extract_search_command(
                user_input
            )
        )

        if search_query:

            search_url = (
                "https://www.google.com/search?q="
                + quote_plus(search_query)
            )

            return (
                "open_url",
                {
                    "url": search_url,
                },
            )

        # --------------------------------------------------------
        # URL / WEBSITE
        # --------------------------------------------------------

        url = self.extract_url_command(
            user_input
        )

        if url:

            return (
                "open_url",
                {
                    "url": url,
                },
            )

        # --------------------------------------------------------
        # OPEN APPLICATION
        # --------------------------------------------------------

        if not self.is_compound_computer_request(
            text
        ):

            application = (
                self.extract_application_command(
                    text,
                    user_input,
                    "open",
                )
            )

            if application:

                return (
                    "open_application",
                    {
                        "application": application,
                    },
                )

        # --------------------------------------------------------
        # CLOSE APPLICATION
        # --------------------------------------------------------

        application = (
            self.extract_application_command(
                text,
                user_input,
                "close",
            )
        )

        if application:

            referenced_application = (
                self.get_referenced_application(
                    application.lower().strip()
                )
            )

            if referenced_application:
                application = referenced_application

            return (
                "close_application",
                {
                    "application": application,
                },
            )

        return None

    # ============================================================
    # SEARCH COMMANDS
    # ============================================================

    def extract_search_command(
        self,
        user_input,
    ):

        if not isinstance(
            user_input,
            str,
        ):
            return None

        original_text = (
            user_input.strip()
        )

        if not original_text:
            return None

        lowered = (
            original_text.lower()
        )

        google_prefixes = (
            "search google for ",
            "search google ",
            "search on google for ",
            "search on google ",
        )

        for prefix in google_prefixes:

            if lowered.startswith(
                prefix
            ):

                query = (
                    original_text[
                        len(prefix):
                    ].strip()
                )

                if query:
                    return query

        prefixes = (
            "search for ",
            "search ",
            "look up ",
            "lookup ",
            "google ",
        )

        for prefix in prefixes:

            if lowered.startswith(
                prefix
            ):

                query = (
                    original_text[
                        len(prefix):
                    ].strip()
                )

                if query:
                    return query


        return None

    # ============================================================
    # COMPOUND REQUEST DETECTION
    # ============================================================

    def is_compound_computer_request(
        self,
        text,
    ):

        if not isinstance(
            text,
            str,
        ):
            return False

        text = (
            text.strip().lower()
        )

        if " and " not in text:
            return False

        computer_action_words = {
            "open",
            "close",
            "type",
            "write",
            "press",
            "click",
            "move",
            "go",
            "navigate",
            "visit",
            "search",
            "paste",
            "wait",
        }

        words = set(
            text.split()
        )

        return bool(
            words.intersection(
                computer_action_words
            )
        )

    # ============================================================
    # MEMORY COMMANDS
    # ============================================================

    def extract_memory_command(
        self,
        normalized_text,
        original_text,
    ):

        text = (
            normalized_text.strip()
        )

        # --------------------------------------------------------
        # REMEMBER FACT
        # --------------------------------------------------------

        remember_prefixes = [
            "remember that ",
            "remember ",
        ]

        for prefix in remember_prefixes:

            if not text.startswith(
                prefix
            ):
                continue

            content = (
                original_text[
                    len(prefix):
                ].strip()
            )

            if not content:
                return None

            match = re.match(
                r"^(.+?)\s+is\s+(.+)$",
                content,
                re.IGNORECASE,
            )

            if match:

                key = (
                    match.group(
                        1
                    ).strip()
                )

                value = (
                    match.group(
                        2
                    ).strip()
                )

                key = re.sub(
                    r"^my\s+",
                    "",
                    key,
                    flags=re.IGNORECASE,
                ).strip()

                if key and value:

                    return (
                        "remember_fact",
                        {
                            "key": key,
                            "value": value,
                        },
                    )

            return None

        # --------------------------------------------------------
        # GET FACT
        # --------------------------------------------------------

        get_patterns = [
            r"^what is my (.+)$",
            r"^what's my (.+)$",
            r"^tell me my (.+)$",
            r"^do you remember my (.+)$",
        ]

        for pattern in get_patterns:

            match = re.fullmatch(
                pattern,
                text,
                re.IGNORECASE,
            )

            if not match:
                continue

            key = (
                match.group(
                    1
                ).strip()
            )

            key = key.rstrip(
                "?.!,;:"
            ).strip()

            if key:

                return (
                    "get_fact",
                    {
                        "key": key,
                    },
                )

        # --------------------------------------------------------
        # FORGET FACT
        # --------------------------------------------------------

        forget_patterns = [
            r"^forget my (.+)$",
            r"^forget (.+)$",
            r"^remove my (.+) from memory$",
        ]

        for pattern in forget_patterns:

            match = re.fullmatch(
                pattern,
                text,
                re.IGNORECASE,
            )

            if not match:
                continue

            key = (
                match.group(
                    1
                ).strip()
            )

            key = re.sub(
                r"^my\s+",
                "",
                key,
                flags=re.IGNORECASE,
            ).strip()

            key = key.rstrip(
                "?.!,;:"
            ).strip()

            if key:

                return (
                    "forget_fact",
                    {
                        "key": key,
                    },
                )

        # --------------------------------------------------------
        # LIST MEMORY
        # --------------------------------------------------------

        memory_commands = {
            "what do you remember about me",
            "what do you remember",
            "what do you know about me",
            "show my memory",
            "show what you remember",
            "show my memories",
            "list my memory",
            "list my memories",
        }

        if text in memory_commands:

            return (
                "list_memory",
                {},
            )

        return None

    # ============================================================
    # TIME
    # ============================================================

    def is_time_request(
        self,
        text,
    ):

        if not isinstance(
            text,
            str,
        ):
            return False

        text = (
            text.lower().strip()
        )

        patterns = [
            r"^what time is it$",
            r"^what's the time$",
            r"^what is the time$",
            r"^what is the current time$",
            r"^what's the current time$",
            r"^current time$",
            r"^tell me the time$",
            r"^tell me current time$",
            r"^time$",
            r"^time please$",
            r"^what time is it now$",
            r"^what's the time now$",
            r"^what time$",
            r"^tell me what time it is$",
        ]

        return any(
            re.fullmatch(
                pattern,
                text,
                re.IGNORECASE,
            )
            for pattern in patterns
        )

    # ============================================================
    # DATE
    # ============================================================

    def is_date_request(
        self,
        text,
    ):

        if not isinstance(
            text,
            str,
        ):
            return False

        words = set(
            text.split()
        )

        if "date" not in words:
            return False

        allowed_words = {
            "what",
            "is",
            "the",
            "current",
            "today",
            "todays",
            "date",
            "please",
        }

        return words.issubset(
            allowed_words
        )

    # ============================================================
    # SYSTEM INFORMATION
    # ============================================================

    def is_system_info_request(
        self,
        text,
    ):

        if not isinstance(
            text,
            str,
        ):
            return False

        patterns = [
            r"^system info$",
            r"^system information$",
            r"^computer info$",
            r"^computer information$",
            r"^system details$",
            r"^computer details$",
        ]

        return any(
            re.fullmatch(
                pattern,
                text,
                re.IGNORECASE,
            )
            for pattern in patterns
        )

    # ============================================================
    # APPLICATION REFERENCES
    # ============================================================

    def get_referenced_application(
        self,
        text,
    ):

        reference_words = {
            "it",
            "that",
            "this",
            "the app",
            "the application",
        }

        if text in reference_words:
            return self.last_opened_application

        return None

    # ============================================================
    # URL / WEBSITE COMMANDS
    # ============================================================

    def extract_url_command(
        self,
        user_input,
    ):

        if not isinstance(
            user_input,
            str,
        ):
            return None

        original_text = (
            user_input.strip()
        )

        if not original_text:
            return None

        lowered = (
            original_text.lower()
        )

        prefixes = (
            "open website ",
            "go to website ",
            "visit website ",
            "navigate to website ",
            "open ",
            "go to ",
            "navigate to ",
            "visit ",
        )

        for prefix in prefixes:

            if not lowered.startswith(
                prefix
            ):
                continue

            value = (
                original_text[
                    len(prefix):
                ].strip()
            )

            if not value:
                return None

            if re.match(
                r"^https?://",
                value,
                re.IGNORECASE,
            ):
                return value

            if re.match(
                r"^(www\.)?[a-z0-9-]+"
                r"(\.[a-z0-9-]+)+"
                r"([/?#].*)?$",
                value,
                re.IGNORECASE,
            ):
                return "https://" + value

        return None

    # ============================================================
    # APPLICATION COMMANDS
    # ============================================================

    def extract_application_command(
        self,
        normalized_text,
        original_text,
        command,
    ):

        prefixes = [
            f"{command} ",
            f"{command} the ",
            f"{command} my ",
        ]

        application = None

        for prefix in prefixes:

            if normalized_text.startswith(
                prefix
            ):

                application = (
                    original_text[
                        len(prefix):
                    ].strip()
                )

                break

        if not application:
            return None

        application = (
            self.clean_application_name(
                application
            )
        )

        return application or None

    # ============================================================
    # CLEAN APPLICATION NAME
    # ============================================================

    def clean_application_name(
        self,
        application,
    ):

        if not isinstance(
            application,
            str,
        ):
            return ""

        application = (
            application.strip()
        )

        suffixes = [
            " for me",
            " to me",
            " please",
            " now",
        ]

        changed = True

        while changed:

            changed = False

            lowered = (
                application.lower()
            )

            for suffix in suffixes:

                if lowered.endswith(
                    suffix
                ):

                    application = (
                        application[
                            :len(application)
                            - len(suffix)
                        ].strip()
                    )

                    changed = True

                    break

        return application

    # ============================================================
    # CLIPBOARD COMMAND
    # ============================================================

    def extract_clipboard_command(
        self,
        normalized_text,
        original_text,
    ):

        prefixes = [
            "copy ",
            "put in clipboard ",
            "set clipboard ",
        ]

        for prefix in prefixes:

            if normalized_text.startswith(
                prefix
            ):

                text = (
                    original_text[
                        len(prefix):
                    ].strip()
                )

                if text:
                    return text

        return None

    # ============================================================
    # GENERAL HELPERS
    # ============================================================

    def normalize(
        self,
        text,
    ):

        if not isinstance(
            text,
            str,
        ):
            return ""

        text = (
            text.lower().strip()
        )

        text = re.sub(
            r"[-_.]",
            " ",
            text,
        )

        return " ".join(
            text.split()
        )

    def matches_command(
        self,
        text,
        commands,
    ):

        return text in commands

    # ============================================================
    # TOOL EXECUTION
    # ============================================================

    def execute(
        self,
        action,
        arguments=None,
    ):

        if arguments is None:
            arguments = {}

        if not isinstance(
            arguments,
            dict,
        ):
            arguments = {}

        # ========================================================
        # GENERIC TARGET CLICK
        # ========================================================

        if action == "computer_click_target":

            target = arguments.get(
                "target"
            )

            position = arguments.get(
                "position",
                "first",
            )

            if not target:

                return (
                    "I couldn't determine "
                    "what to click."
                )

            computer_action = {
                "action":
                    "computer_click_target",

                "arguments": {
                    "target": target,
                    "position": position,
                },
            }

            try:

                result = (
                    self.computer_agent.act_with_recovery(
                        computer_action,
                        expected_text=None,
                        wait_seconds=0.5,
                        max_retries=1,
                    )
                )

                if not isinstance(
                    result,
                    dict,
                ):

                    return (
                        f"Clicked '{target}'."
                    )

                if result.get(
                    "success",
                    False,
                ):

                    if result.get(
                        "recovered",
                        False,
                    ):

                        return (
                            f"Clicked '{target}' "
                            f"after a local retry."
                        )

                    return (
                        f"Clicked '{target}'."
                    )

                if result.get(
                    "action_performed",
                    False,
                ):

                    return (
                        f"Clicked '{target}', but "
                        f"the screen did not visibly change."
                    )

                return (
                    f"I couldn't successfully "
                    f"click '{target}'."
                )

            except Exception as error:

                return (
                    f"I couldn't click "
                    f"'{target}'. "
                    f"Error: {error}"
                )

        # ========================================================
        # GENERIC SPATIAL CLICK
        # ========================================================

        if action == "computer_click_spatial":

            relationship = arguments.get(
                "relationship"
            )

            if relationship is None:

                relationship = arguments.get(
                    "relation"
                )

            reference_text = (
                arguments.get(
                    "reference_text"
                )
            )

            valid_relationships = {
                "below",
                "above",
                "left_of",
                "right_of",
            }

            if relationship not in valid_relationships:

                return (
                    "I couldn't determine "
                    "the spatial relationship."
                )

            if not reference_text:

                return (
                    "I couldn't determine "
                    "the reference element."
                )

            try:

                # ------------------------------------------------
                # FIRST ATTEMPT
                # ------------------------------------------------

                before = (
                    self.computer_agent.observe()
                )

                result = (
                    self._click_spatial_element(
                        reference_text=reference_text,
                        relationship=relationship,
                    )
                )

                if not isinstance(
                    result,
                    dict,
                ):

                    return result

                if not result.get(
                    "success",
                    False,
                ):

                    return result

                # ------------------------------------------------
                # WAIT FOR UI RESPONSE
                # ------------------------------------------------

                self.computer_agent.wait(
                    0.5
                )

                after = (
                    self.computer_agent.observe()
                )

                changed = (
                    self.computer_agent.screen_changed(
                        before,
                        after,
                    )
                )

                # ------------------------------------------------
                # VERIFIED
                # ------------------------------------------------

                if changed:

                    return {
                        "success": True,
                        "verified": True,
                        "recovered": False,
                        "relationship": relationship,
                        "reference_text": reference_text,
                        "result": result,
                    }

                # ------------------------------------------------
                # LOCAL RECOVERY
                # ------------------------------------------------

                candidate = result.get(
                    "candidate",
                    {},
                )

                target_text = ""

                if isinstance(
                    candidate,
                    dict,
                ):

                    target_text = candidate.get(
                        "text",
                        "",
                    )

                if target_text:

                    recovery = (
                        self.computer_agent.recover_spatial_click(
                            relationship=relationship,
                            reference_text=reference_text,
                            target_text=target_text,
                            wait_seconds=0.5,
                        )
                    )

                    if (
                        isinstance(
                            recovery,
                            dict,
                        )
                        and recovery.get(
                            "success",
                            False,
                        )
                    ):

                        return {
                            "success": True,
                            "verified": True,
                            "recovered": True,
                            "relationship": relationship,
                            "reference_text": reference_text,
                            "result": recovery,
                        }

                # ------------------------------------------------
                # CLICK PERFORMED BUT NO VISIBLE CHANGE
                # ------------------------------------------------

                return {
                    "success": True,
                    "verified": False,
                    "recovered": False,
                    "relationship": relationship,
                    "reference_text": reference_text,
                    "result": result,
                    "message": (
                        "The click was performed, but "
                        "no OCR-visible screen change "
                        "was detected."
                    ),
                }

            except Exception as error:

                return (
                    "I couldn't perform the "
                    "spatial click. "
                    f"Error: {error}"
                )

        # ========================================================
        # SCREEN OBSERVATION
        # ========================================================

        if action == "describe_screen":

            try:

                result = self.registry.execute(
                    "describe_screen",
                    {},
                )

                if not isinstance(
                    result,
                    dict,
                ):
                    return (
                        "I couldn't inspect the screen."
                    )

                if not result.get(
                    "success",
                    False,
                ):
                    return result.get(
                        "message",
                        "I couldn't inspect the screen.",
                    )

                elements = result.get(
                    "elements",
                    [],
                )

                if not isinstance(
                    elements,
                    list,
                ):
                    elements = []

                if not elements:
                    return (
                        "I don't see any readable "
                        "text on the screen."
                    )

                lines = []

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

                    x = element.get("x")
                    y = element.get("y")

                    if (
                        x is not None
                        and y is not None
                    ):
                        lines.append(
                            f"- {text} "
                            f"at ({x}, {y})"
                        )
                    else:
                        lines.append(
                            f"- {text}"
                        )

                if not lines:
                    return (
                        "I don't see any readable "
                        "text on the screen."
                    )

                return (
                    "I can currently see:\n"
                    + "\n".join(lines)
                )

            except Exception as error:

                return (
                    "I couldn't inspect the screen. "
                    f"Error: {error}"
                )

        # ========================================================
        # NORMAL REGISTERED TOOLS
        # ========================================================

        if hasattr(
            self.registry,
            "has",
        ):

            tool_exists = (
                self.registry.has(
                    action
                )
            )

        elif hasattr(
            self.registry,
            "has_tool",
        ):

            tool_exists = (
                self.registry.has_tool(
                    action
                )
            )

        else:

            tool_exists = (
                action
                in getattr(
                    self.registry,
                    "tools",
                    {},
                )
            )

        if not tool_exists:

            error_message = (
                f"I don't have a tool called "
                f"'{action}'."
            )

            try:

                self.brain.memory.add_assistant(
                    error_message
                )

            except Exception:
                pass

            return error_message

        try:

            result = (
                self.registry.execute(
                    action,
                    arguments,
                )
            )

            # ----------------------------------------------------
            # REMEMBER LAST OPENED APPLICATION
            # ----------------------------------------------------

            if (
                action == "open_application"
                and isinstance(
                    arguments,
                    dict,
                )
            ):

                application = (
                    arguments.get(
                        "application"
                    )
                )

                if application:

                    self.last_opened_application = (
                        str(
                            application
                        ).strip()
                    )

            # ----------------------------------------------------
            # RUN_ACTIONS MAY CONTAIN OPEN_APPLICATION
            # ----------------------------------------------------

            if (
                action == "run_actions"
                and isinstance(
                    arguments,
                    dict,
                )
            ):

                actions = (
                    arguments.get(
                        "actions",
                        [],
                    )
                )

                if isinstance(
                    actions,
                    list,
                ):

                    for sequence_action in actions:

                        if not isinstance(
                            sequence_action,
                            dict,
                        ):
                            continue

                        sequence_name = (
                            sequence_action.get(
                                "action"
                            )
                        )

                        sequence_arguments = (
                            sequence_action.get(
                                "arguments",
                                {},
                            )
                        )

                        if (
                            sequence_name
                            == "open_application"
                            and isinstance(
                                sequence_arguments,
                                dict,
                            )
                        ):

                            application = (
                                sequence_arguments.get(
                                    "application"
                                )
                            )

                            if application:

                                self.last_opened_application = (
                                    str(
                                        application
                                    ).strip()
                                )

            # ----------------------------------------------------
            # STORE TOOL RESULT
            # ----------------------------------------------------

            if result is not None:

                try:

                    self.brain.memory.add_assistant(
                        str(result)
                    )

                except Exception:
                    pass

            return result

        except Exception as error:

            error_message = (
                f"I couldn't execute {action}. "
                f"Error: {error}"
            )

            try:

                self.brain.memory.add_assistant(
                    error_message
                )

            except Exception:
                pass

            return error_message