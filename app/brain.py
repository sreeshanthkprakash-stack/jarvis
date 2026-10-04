import json

import re
from urllib.parse import quote_plus



# pyrefly: ignore [missing-import]

from openai import BadRequestError, OpenAI



# pyrefly: ignore [missing-import]
from app.config import (

    MODEL,

    MODEL_API_KEY,

    MODEL_BASE_URL,

    MODEL_TEMPERATURE,

    MODEL_MAX_TOKENS,

)



# pyrefly: ignore [missing-import]
from app.memory import (

    ConversationMemory,

    PersistentMemory,

)



# pyrefly: ignore [missing-import]
from app import config as _config



# ============================================================

# SPEED TUNABLES

# Override any of these in app/config.py if you want to.

# ============================================================



# Messages (not turns) sent to the model in normal chat.

HISTORY_MESSAGES = getattr(_config, "HISTORY_MESSAGES", 12)



# Messages kept in RAM in total (older ones are dropped).

STORED_MESSAGES_CAP = getattr(_config, "STORED_MESSAGES_CAP", 40)



# Print the reply token-by-token as it is generated.

STREAM_REPLIES = getattr(_config, "STREAM_REPLIES", True)



# Max long-term memory items injected into one chat prompt.

MEMORY_MAX_ITEMS = getattr(_config, "MEMORY_MAX_ITEMS", 8)



# Facts that are always worth including when memory is large.

ALWAYS_INCLUDE_KEYS = {"name", "user_name", "preferred_name"}



_STOPWORDS = {

    "the", "and", "for", "are", "but", "not", "you", "your", "with",

    "this", "that", "what", "how", "can", "please", "jarvis", "have",

    "has", "was", "were", "will", "would", "could", "should", "about",

    "from", "into", "than", "then", "them", "they", "their", "there",

    "when", "where", "which", "who", "why", "tell", "give", "show",

}





class JarvisBrain:



    def __init__(self, system_prompt, tool_registry=None):



        # ======================================================

        # GROQ API CLIENT (OpenAI-compatible)

        # ======================================================



        if not MODEL_API_KEY:

            raise RuntimeError(

                "GROQ_API_KEY is missing. Create a .env file in the "

                "project root containing:  GROQ_API_KEY=your_key_here"

            )



        self.client = OpenAI(

            base_url=MODEL_BASE_URL,

            api_key=MODEL_API_KEY,

            timeout=30,

            max_retries=2,

        )



        # ======================================================

        # SHORT-TERM CONVERSATION MEMORY

        # ======================================================



        self.memory = ConversationMemory(

            system_prompt

        )



        # ======================================================

        # LONG-TERM PERSISTENT MEMORY

        # ======================================================



        self.persistent_memory = PersistentMemory()



        self.system_prompt = system_prompt



        # ======================================================

        # TOOL REGISTRY

        # ======================================================



        self.tool_registry = tool_registry



    # ==========================================================

    # TOOL REGISTRY

    # ==========================================================



    def set_tool_registry(self, tool_registry):



        self.tool_registry = tool_registry



    def get_tool_descriptions(self):



        if not self.tool_registry:

            return {}



        return self.tool_registry.descriptions()



    def get_tool_schemas(self):



        if not self.tool_registry:

            return {}



        return self.tool_registry.schemas()



    # ==========================================================

    # PERSISTENT MEMORY CONTEXT

    # ==========================================================



    @staticmethod

    def _words(text):



        words = set()



        for word in re.findall(r"[a-z0-9]+", str(text).lower()):



            if len(word) <= 2 or word in _STOPWORDS:

                continue



            # Very light plural handling: "shortcuts" \~ "shortcut".

            if len(word) > 3 and word.endswith("s"):

                word = word[:-1]



            words.add(word)



        return words



    def _select_relevant_memory(self, data, query):



        facts = data.get("facts", {}) or {}

        preferences = data.get("preferences", {}) or {}

        notes = data.get("notes", []) or []



        items = []



        for key, value in facts.items():

            items.append(("facts", key, value))



        for key, value in preferences.items():

            items.append(("preferences", key, value))



        for note in notes:

            items.append(("notes", None, note))



        # Small memory: just send everything (same as before).

        if len(items) <= MEMORY_MAX_ITEMS:

            chosen = items



        else:



            query_words = self._words(query)



            scored = []



            for index, (section, key, value) in enumerate(items):



                text = f"{key or ''} {value}"



                score = len(query_words & self._words(text))



                if key in ALWAYS_INCLUDE_KEYS:

                    score += 100



                if score > 0:

                    scored.append((score, index))



            # Best score first; for ties prefer the newest item.

            scored.sort(key=lambda pair: (-pair[0], -pair[1]))



            keep = {

                index for _, index

                in scored[:MEMORY_MAX_ITEMS]

            }



            chosen = [

                item for index, item in enumerate(items)

                if index in keep

            ]



        selected = {

            "facts": {},

            "preferences": {},

            "notes": [],

        }



        for section, key, value in chosen:



            value = str(value)



            if len(value) > 200:

                value = value[:200] + "..."



            if section == "notes":

                selected["notes"].append(value)

            else:

                selected[section][key] = value



        return selected



    def get_memory_context(self, query=None):



        memory_data = self.persistent_memory.get_all()



        # No query -> old behaviour (everything).

        if query is None:

            selected = memory_data



        else:

            selected = self._select_relevant_memory(

                memory_data,

                query,

            )



        if not (

            selected.get("facts")

            or selected.get("preferences")

            or selected.get("notes")

        ):

            return ""



        return (

            "\n\nJARVIS MEMORY (use only if relevant):\n"

            + json.dumps(

                selected,

                ensure_ascii=False,

            )

        )



    # ==========================================================

    # SAFE JSON RESPONSE

    # ==========================================================



    def _create_json(self, **kwargs):

        """

        Chat call that wants a JSON reply.



        Tries Groq's JSON mode first. If the chosen model rejects

        response_format (HTTP 400), remember that and retry without it.

        The prompts already demand JSON, and _parse_json_response()

        handles code fences, so this still works.

        """



        if getattr(self, "_json_mode", True):



            try:



                return self.client.chat.completions.create(

                    response_format={"type": "json_object"},

                    **kwargs,

                )



            except BadRequestError as error:



                text = str(error).lower()



                if "response_format" not in text and "json" not in text:

                    raise



                self._json_mode = False



        return self.client.chat.completions.create(**kwargs)



    def _parse_json_response(self, content):



        if not content:

            raise ValueError(

                "The model returned an empty response."

            )



        content = content.strip()



        # ------------------------------------------------------

        # Remove markdown code fences if model adds them

        # ------------------------------------------------------



        if content.startswith("```"):



            lines = content.splitlines()



            if lines:

                lines = lines[1:]



            if lines and lines[-1].strip() == "```":

                lines = lines[:-1]



            content = "\n".join(lines).strip()



        # ------------------------------------------------------

        # Remove accidental <think> blocks

        # ------------------------------------------------------



        if "<think>" in content:



            end = content.find("</think>")



            if end != -1:

                content = (

                    content[end + len("</think>"):]

                    .strip()

                )



        # ------------------------------------------------------

        # Parse JSON

        # ------------------------------------------------------



        return json.loads(content)



    # ==========================================================

    # MEMORY EXTRACTION

    # ==========================================================



    def extract_memory(self, user_input):



        memory_prompt = """

You are JARVIS's long-term memory extraction system.



Analyze the user's message and determine whether it contains

stable, useful information that should be remembered for future

conversations.



Remember things such as:



- personal facts

- preferences

- useful user-specific information

- recurring choices

- important long-term context



Do NOT remember:



- temporary requests

- ordinary questions

- general knowledge

- instructions that only apply to the current request

- casual conversation with no useful long-term information



Create a concise semantic key and value.



Examples:



User:

"My name is Alex"



Result:

{

    "should_remember": true,

    "key": "name",

    "value": "Alex"

}



User:

"I prefer Python"



Result:

{

    "should_remember": true,

    "key": "preferred_programming_language",

    "value": "Python"

}



User:

"I like dark mode"



Result:

{

    "should_remember": true,

    "key": "preferred_theme",

    "value": "dark mode"

}



User:

"What's the weather?"



Result:

{

    "should_remember": false,

    "key": "",

    "value": ""

}



Return ONLY valid JSON.

Do not use markdown.

Do not explain anything.

"""



        response = self._create_json(

            model=MODEL,

            messages=[

                {

                    "role": "system",

                    "content": memory_prompt,

                },

                {

                    "role": "user",

                    "content": user_input,

                },

            ],

            temperature=0,

            max_tokens=128,

        )



        content = (

            response

            .choices[0]

            .message

            .content

        )



        return self._parse_json_response(

            content

        )



    # ==========================================================

    # UPDATE MEMORY

    # ==========================================================



    def update_memory_from_message(

        self,

        user_input,

    ):



        try:



            result = self.extract_memory(

                user_input

            )



            if not result.get(

                "should_remember"

            ):

                return



            key = result.get(

                "key",

                "",

            ).strip()



            value = result.get(

                "value",

                "",

            ).strip()



            if key and value:



                self.persistent_memory.remember_fact(

                    key,

                    value,

                )



        except Exception as error:



            print(

                f"\nJARVIS memory warning: {error}"

            )



    # ==========================================================

    # NORMAL AI CONVERSATION

    # ==========================================================



    def _cap_stored_history(self):



        messages = self.memory.messages



        if len(messages) > STORED_MESSAGES_CAP + 1:



            self.memory.messages = (

                [messages[0]]

                + messages[-STORED_MESSAGES_CAP:]

            )



    @staticmethod

    def _strip_think(content):



        content = (content or "").strip()



        if "<think>" in content:



            end = content.find("</think>")



            if end != -1:

                content = content[end + len("</think>"):].strip()



        return content



    def ask(self, user_input):



        # ------------------------------------------------------

        # Add user message to short-term memory

        # ------------------------------------------------------



        self.memory.add_user(

            user_input

        )



        self._cap_stored_history()



        # ------------------------------------------------------

        # System prompt + only the memory that matters now

        # ------------------------------------------------------



        system_content = (

            self.system_prompt

            + self.get_memory_context(user_input)

        )



        # ------------------------------------------------------

        # Only the most recent messages go to the model

        # ------------------------------------------------------



        history = [

            dict(message)

            for message in self.memory.get_messages()

            if message.get("role") != "system"

        ][-HISTORY_MESSAGES:]



        messages = [

            {

                "role": "system",

                "content": system_content,

            }

        ] + history



        # ------------------------------------------------------

        # Generate

        # ------------------------------------------------------



        if STREAM_REPLIES:

            return self._ask_streaming(messages)



        return self._ask_blocking(messages)



    # ----------------------------------------------------------

    # Blocking reply (original behaviour)

    # ----------------------------------------------------------



    def _ask_blocking(self, messages):



        response = self.client.chat.completions.create(

            model=MODEL,

            messages=messages,

            temperature=MODEL_TEMPERATURE,

            max_tokens=MODEL_MAX_TOKENS,

            stream=False,

        )



        content = self._strip_think(

            response.choices[0].message.content

        )



        if not content:

            content = "I couldn't generate a response."



        self.memory.add_assistant(content)



        return content



    # ----------------------------------------------------------

    # Streaming reply: prints tokens as they arrive.

    #

    # main.py / voice_command.py only print the returned value

    # when it is truthy, so after printing we return "" to avoid

    # showing the answer twice.

    # ----------------------------------------------------------



    def _ask_streaming(self, messages):



        stream = self.client.chat.completions.create(

            model=MODEL,

            messages=messages,

            temperature=MODEL_TEMPERATURE,

            max_tokens=MODEL_MAX_TOKENS,

            stream=True,

        )



        shown = []

        state = "start"   # start -> (think ->) stream

        buffer = ""



        def emit(text):



            if not text:

                return



            print(text, end="", flush=True)

            shown.append(text)



        try:



            for chunk in stream:



                if not chunk.choices:

                    continue



                piece = getattr(

                    chunk.choices[0].delta,

                    "content",

                    None,

                )



                if not piece:

                    continue



                if state == "stream":

                    emit(piece)

                    continue



                buffer += piece



                # Decide whether the reply begins with <think>.

                if state == "start":



                    probe = buffer.lstrip()



                    if probe.startswith("<think>"):

                        state = "think"



                    elif "<think>".startswith(probe):

                        # Could still turn into <think>; wait.

                        continue



                    else:

                        state = "stream"

                        emit(probe)

                        buffer = ""

                        continue



                # Hide a reasoning block entirely.

                if state == "think":



                    end = buffer.find("</think>")



                    if end != -1:

                        state = "stream"

                        emit(

                            buffer[end + len("</think>"):]

                            .lstrip()

                        )

                        buffer = ""



            # Very short replies may still be buffered.

            if state == "start" and buffer.strip():

                emit(buffer.strip())



        except Exception:



            partial = "".join(shown).strip()



            if partial:

                self.memory.add_assistant(partial)



            raise



        finally:



            close = getattr(stream, "close", None)



            if callable(close):

                try:

                    close()

                except Exception:

                    pass



        content = "".join(shown).strip()



        # Nothing visible was produced: let the caller print this.

        if not content:



            content = "I couldn't generate a response."



            self.memory.add_assistant(content)



            return content



        self.memory.add_assistant(content)



        # Return the complete generated response.

        return content



    # ==========================================================

    # INTENT RESPONSE SCHEMA

    # ==========================================================



    def build_intent_schema(self):



        return {

            "type": "object",

            "properties": {

                "action": {

                    "type": "string"

                },

                "arguments": {

                    "type": "string"

                },

                "response": {

                    "type": "string"

                },

            },

            "required": [

                "action",

                "arguments",

                "response",

            ],

            "additionalProperties": False,

        }



    # ==========================================================

    # COMPACT INTENT PROMPT (built once, then cached)

    #

    # The text never changes between calls, so the model server

    # can reuse its cached processing of this prefix.

    # ==========================================================



    @staticmethod

    def _short_description(text, limit=90):



        text = " ".join(str(text).split())



        cut = text.find(". ")



        if cut != -1:

            text = text[:cut + 1]



        if len(text) > limit:

            text = text[:limit - 3].rstrip() + "..."



        return text



    def _tool_line(self, name, description, parameters):



        params = []



        if isinstance(parameters, dict):



            for param_name, spec in parameters.items():



                param_type = (

                    spec.get("type", "string")

                    if isinstance(spec, dict)

                    else "string"

                )



                params.append(f"{param_name}: {param_type}")



        return (

            f"- {name}({', '.join(params)}): "

            f"{self._short_description(description)}"

        )



    @staticmethod

    def _example(user, action, arguments):



        return (

            f'User: "{user}"\n'

            "Return: "

            + json.dumps(

                {

                    "action": action,

                    "arguments": json.dumps(arguments),

                    "response": "",

                },

                ensure_ascii=False,

            )

        )



    def _get_intent_prompt(self):



        descriptions = self.get_tool_descriptions()

        schemas = self.get_tool_schemas()



        cache_key = tuple(descriptions.keys())



        cached = getattr(self, "_intent_prompt_cache", None)



        if cached and cached[0] == cache_key:

            return cached[1]



        if descriptions:



            tools_text = "\n".join(

                self._tool_line(

                    name,

                    description,

                    schemas.get(name, {}),

                )

                for name, description in descriptions.items()

            )



        else:



            tools_text = "No local tools are currently available."



        examples = "\n\n".join(

            [

                self._example(

                    "open vs code",

                    "open_application",

                    {"application": "vs code"},

                ),

                self._example(

                    "remember that my name is Alex",

                    "remember_fact",

                    {"key": "name", "value": "Alex"},

                ),

                self._example(

                    "what is quantum physics?",

                    "AI_QUERY",

                    {},

                ),

                self._example(

                    "open Chrome and go to google.com",

                    "run_actions",

                    {

                        "actions": [

                            {

                                "action": "open_application",

                                "arguments": {"application": "Chrome"},

                            },

                            {

                                "action": "wait",

                                "arguments": {"seconds": 2},

                            },

                            {

                                "action": "hotkey",

                                "arguments": {"keys": "ctrl+l"},

                            },

                            {

                                "action": "type_text",

                                "arguments": {"text": "https://google.com"},

                            },

                            {

                                "action": "press_key",

                                "arguments": {"key": "enter"},

                            },

                        ]

                    },

                ),
                self._example(

                    "open YouTube and play Ishq",

                    "run_actions",

                    {

                        "actions": [

                            {

                                "action": "open_url",

                                "arguments": {

                                    "url": "https://www.youtube.com/results?search_query=Ishq"

                                },

                            },

                            {

                                "action": "wait",

                                "arguments": {"seconds": 3},

                            },

                            {

                                "action": "computer_click_target",

                                "arguments": {

                                    "target": "Ishq",

                                    "position": "first",

                                },

                            },

                        ]

                    },

                ),

            ]

        )



        prompt = (

            "You are JARVIS's intent engine. Choose the local tool "

            "that matches the user's request, or AI_QUERY.\n\n"

            "Return ONLY a JSON object with keys "

            '"action", "arguments", "response".\n\n'

            "Rules:\n"

            "1. Use a listed tool when the request clearly matches it. "

            "Never invent tool names.\n"

            "2. Use the exact parameter names shown; copy user-provided "

            "values exactly.\n"

            '3. "arguments" is a JSON-encoded STRING. Use "{}" when the '

            "tool has no parameters or for AI_QUERY.\n"

            "4. Use AI_QUERY for questions, explanations, conversation, "

            "coding, writing and reasoning. Do not answer yourself; "

            '"response" is always "".\n'

            "5. If the request needs several steps, use run_actions with "

            '{"actions":[{"action":<tool>,"arguments":{...}}]}. Nested '

            "arguments are plain objects. Only use listed tools, no "

            "nested run_actions, no AI_QUERY inside. Add a wait step "

            "after opening an app or page. Never use run_actions for a "

            "request one tool can do.\n"

            "6. Prefer open_url for a real URL or domain. After opening "

            "a browser, use hotkey, type_text and press_key.\n"

            "7. Prefer local computer tools over AI_QUERY whenever they "

            "can do the job.\n"

            "8. Commands that control a browser, website, media player, "

            "or desktop UI are computer tasks, not AI_QUERY. If the user "

            "asks to open a site and then search, click, play, watch, "

            "download, or select something, use run_actions.\n"

            "9. For a multi-step browser task, first navigate/search, then "

            "wait for the page, then use a computer_click_target or "

            "computer_click_spatial action when the next target must be "

            "found visually. Do not assume screen coordinates.\n\n"

            "Tools:\n"

            f"{tools_text}\n\n"

            "Examples:\n\n"

            f"{examples}\n"

        )



        self._intent_prompt_cache = (cache_key, prompt)



        return prompt



    # ==========================================================

    # INTENT UNDERSTANDING

    # ==========================================================



    def _local_media_intent(self, user_input):
        """
        Handle common YouTube media commands deterministically.

        These requests are computer-control tasks, not knowledge queries.
        Search results are opened first, then the ComputerAgent is asked to
        click the requested title using OCR.
        """
        if not isinstance(user_input, str):
            return None

        text = " ".join(user_input.strip().split())
        if not text:
            return None

        lower = text.lower()

        # Only take this path when YouTube is explicitly involved.
        if "youtube" not in lower:
            return None

        # Examples:
        #   open youtube and play ishq
        #   open youtube, search for ishq and play it
        #   play ishq on youtube
        patterns = [
            r"(?:open|launch|go\s+to)\s+youtube(?:\s+(?:and|then|,)\s*)?"
            r"(?:search\s+(?:for\s+)?)?"
            r"(?:and\s+)?(?:play|listen\s+to|watch)\s+(.+)$",
            r"(?:play|listen\s+to|watch)\s+(.+?)\s+on\s+youtube$",
        ]

        media_query = None

        for pattern in patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                media_query = match.group(1).strip(" .?!")
                break

        if not media_query:
            return None

        if not media_query:
            return None

        # Go directly to YouTube search results. This is more reliable than
        # asking the model to invent a sequence of browser keystrokes.
        search_url = (
            "https://www.youtube.com/results?search_query="
            + quote_plus(media_query)
        )

        return {
            "action": "run_actions",
            "arguments": {
                "actions": [
                    {
                        "action": "open_url",
                        "arguments": {"url": search_url},
                    },
                    {
                        "action": "wait",
                        "arguments": {"seconds": 3},
                    },
                    {
                        "action": "computer_click_target",
                        "arguments": {
                            "target": media_query,
                            "position": "first",
                        },
                    },
                ]
            },
            "response": "",
        }

    def understand(self, user_input):

        local_media = self._local_media_intent(user_input)
        if local_media is not None:
            return local_media

        recent_messages = (

            self.memory

            .get_messages()[-6:]

        )



        tool_descriptions = (

            self.get_tool_descriptions()

        )



        intent_prompt = self._get_intent_prompt()



        # ------------------------------------------------------

        # Build messages

        # ------------------------------------------------------



        messages = [

            {

                "role": "system",

                "content": intent_prompt,

            }

        ]



        # ------------------------------------------------------

        # Add recent conversation

        # ------------------------------------------------------



        for message in recent_messages:



            role = message.get(

                "role"

            )



            content = message.get(

                "content"

            )



            if role in {

                "user",

                "assistant",

            }:



                messages.append(

                    {

                        "role": role,

                        "content": str(content or "")[:400],

                    }

                )



        # ------------------------------------------------------

        # Current request

        # ------------------------------------------------------



        messages.append(

            {

                "role": "user",

                "content": user_input,

            }

        )



        # ------------------------------------------------------

        # Ask the Groq model

        # ------------------------------------------------------



        response = self._create_json(

            model=MODEL,

            messages=messages,

            temperature=0,

            max_tokens=256,

        )



        content = (

            response

            .choices[0]

            .message

            .content

        )



        # ------------------------------------------------------

        # Parse JSON

        # ------------------------------------------------------



        try:



            result = self._parse_json_response(

                content

            )



        except Exception:



            return {

                "action": "AI_QUERY",

                "arguments": {},

                "response": "",

            }



        # ------------------------------------------------------

        # Validate result

        # ------------------------------------------------------



        valid_actions = set(

            tool_descriptions.keys()

        )



        valid_actions.add(

            "AI_QUERY"

        )



        action = result.get(

            "action"

        )



        if action not in valid_actions:



            return {

                "action": "AI_QUERY",

                "arguments": {},

                "response": "",

            }



        # ------------------------------------------------------

        # Decode arguments

        # ------------------------------------------------------



        raw_arguments = result.get(

            "arguments",

            "{}",

        )



        if not isinstance(

            raw_arguments,

            str,

        ):



            raw_arguments = "{}"



        try:



            arguments = json.loads(

                raw_arguments

            )



        except Exception:



            arguments = {}



        if not isinstance(

            arguments,

            dict,

        ):



            arguments = {}



        # ------------------------------------------------------

        # Validate run_actions

        # ------------------------------------------------------



        if action == "run_actions":



            actions = arguments.get(

                "actions"

            )



            if not isinstance(

                actions,

                list,

            ):



                return {

                    "action": "AI_QUERY",

                    "arguments": {},

                    "response": "",

                }



            for item in actions:



                if not isinstance(

                    item,

                    dict,

                ):



                    return {

                        "action": "AI_QUERY",

                        "arguments": {},

                        "response": "",

                    }



                nested_action = item.get(

                    "action"

                )



                nested_arguments = item.get(

                    "arguments",

                    {},

                )



                # Never allow recursive automation.

                if nested_action == "run_actions":



                    return {

                        "action": "AI_QUERY",

                        "arguments": {},

                        "response": "",

                    }



                # Every nested action must exist.

                if nested_action not in valid_actions:



                    return {

                        "action": "AI_QUERY",

                        "arguments": {},

                        "response": "",

                    }



                # AI_QUERY cannot run inside automation.

                if nested_action == "AI_QUERY":



                    return {

                        "action": "AI_QUERY",

                        "arguments": {},

                        "response": "",

                    }



                if not isinstance(

                    nested_arguments,

                    dict,

                ):



                    return {

                        "action": "AI_QUERY",

                        "arguments": {},

                        "response": "",

                    }



        # ------------------------------------------------------

        # Return normalized intent

        # ------------------------------------------------------



        return {

            "action": action,

            "arguments": arguments,

            "response": result.get(

                "response",

                "",

            ),

        }