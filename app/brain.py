
import json


# pyrefly: ignore [missing-import]
from groq import Groq


# pyrefly: ignore [missing-import]
from app.config import GROQ_API_KEY, MODEL


# pyrefly: ignore [missing-import]
from app.memory import ConversationMemory, PersistentMemory


class JarvisBrain:

    def __init__(self, system_prompt, tool_registry=None):

        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is missing from your .env file."
            )

        self.client = Groq(
            api_key=GROQ_API_KEY
        )

        # ------------------------------------------------------
        # Short-term conversation memory
        # ------------------------------------------------------

        self.memory = ConversationMemory(
            system_prompt
        )

        # ------------------------------------------------------
        # Long-term persistent memory
        # ------------------------------------------------------

        self.persistent_memory = PersistentMemory()

        self.system_prompt = system_prompt

        # ------------------------------------------------------
        # Tool registry
        # ------------------------------------------------------

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

    def get_memory_context(self):

        memory_data = self.persistent_memory.get_all()

        return (
            "\n\nJARVIS MEMORY:\n"
            f"{json.dumps(memory_data, indent=2, ensure_ascii=False)}"
        )

    # ==========================================================
    # MEMORY EXTRACTION
    #
    # Kept available, but NOT automatically called during
    # normal AI conversations.
    # ==========================================================

    def extract_memory(self, user_input):

        response = self.client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """
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
"I live in Delhi"

Result:
{
    "should_remember": true,
    "key": "location",
    "value": "Delhi"
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

User:
"Explain quantum physics"

Result:
{
    "should_remember": false,
    "key": "",
    "value": ""
}

Return JSON only.
""",
                },
                {
                    "role": "user",
                    "content": user_input,
                },
            ],
            temperature=0,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "memory_extraction",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "should_remember": {
                                "type": "boolean"
                            },
                            "key": {
                                "type": "string"
                            },
                            "value": {
                                "type": "string"
                            },
                        },
                        "required": [
                            "should_remember",
                            "key",
                            "value",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
        )

        content = response.choices[0].message.content

        return json.loads(content)

    def update_memory_from_message(self, user_input):

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
                ""
            ).strip()

            value = result.get(
                "value",
                ""
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

    def ask(self, user_input):

        # Add user message to short-term memory
        self.memory.add_user(
            user_input
        )

        # Do NOT automatically extract memory here.
        #
        # Memory is handled through the memory tools.

        messages = self.memory.get_messages().copy()

        # Inject persistent memory into system prompt
        messages[0] = {
            "role": "system",
            "content": (
                self.system_prompt
                + self.get_memory_context()
            ),
        }

        # Generate AI response
        stream = self.client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            stream=True,
        )

        full_response = ""

        for chunk in stream:

            if not chunk.choices:
                continue

            text = chunk.choices[0].delta.content

            if text:

                print(
                    text,
                    end="",
                    flush=True,
                )

                full_response += text

        print()

        # Save assistant response
        self.memory.add_assistant(
            full_response
        )

        return None

    # ==========================================================
    # GROQ INTENT RESPONSE SCHEMA
    #
    # Groq requires the TOP LEVEL to be an object.
    #
    # {
    #     "action": "...",
    #     "arguments": "...",
    #     "response": "..."
    # }
    #
    # arguments is a JSON STRING containing the actual arguments.
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
    # INTENT UNDERSTANDING
    # ==========================================================

    def understand(self, user_input):

        recent_messages = (
            self.memory.get_messages()[-6:]
        )

        tool_descriptions = (
            self.get_tool_descriptions()
        )

        tool_schemas = (
            self.get_tool_schemas()
        )

        # ------------------------------------------------------
        # Tool descriptions
        # ------------------------------------------------------

        if tool_descriptions:

            tools_text = "\n".join(
                f"- {name}: {description}"
                for name, description
                in tool_descriptions.items()
            )

        else:

            tools_text = (
                "No local tools are currently available."
            )

        # ------------------------------------------------------
        # Tool schemas
        # ------------------------------------------------------

        schemas_text = json.dumps(
            tool_schemas,
            indent=2,
            ensure_ascii=False,
        )

        # ------------------------------------------------------
        # Intent prompt
        # ------------------------------------------------------

        messages = [
            {
                "role": "system",
                "content": f"""
You are JARVIS's intent engine.

Your job is to understand the user's request and select
the correct local capability.

Most simple requests use one local tool.

If a request requires multiple computer operations,
use the "run_actions" tool to compose multiple existing
tools into one ordered sequence.

Available local capabilities:

{tools_text}

Their exact parameter schemas are:

{schemas_text}

There is also a special action:

AI_QUERY

Use AI_QUERY when the request should be answered
conversationally by JARVIS instead of being executed
by a local tool.

Rules:

1. Select a local tool when the request clearly corresponds
   to one of the registered tools.

2. Use AI_QUERY for normal questions, explanations,
   conversations, coding, writing, reasoning, and requests
   that do not correspond to a local tool.

3. Never invent a tool.

4. Use the exact parameter names defined by the selected
   tool schema.

5. Preserve user-provided values accurately.

6. The "arguments" field MUST be a JSON-encoded string.

7. If the selected tool has no parameters, arguments must be:

"{{}}"

8. If AI_QUERY is selected, arguments must be:

"{{}}"

9. The "response" field must always be an empty string.

10. Do not answer the user's question yourself.

11. Return JSON only.

12. Use "run_actions" when the user's request requires
    multiple local actions.

13. Every action inside "run_actions" MUST use an existing
    registered tool.

14. Execute actions in the exact order required by the user.

15. Never invent action names inside "run_actions".

16. Do not use "run_actions" for a simple request that can
    be completed by one local tool.

17. Do not use AI_QUERY when the user's request can be
    performed by the available local computer tools.

18. For computer automation, prefer the existing local
    primitives such as:

    open_application
    close_application
    open_url
    open_website
    type_text
    press_key
    hotkey
    move_mouse
    click_mouse
    wait
    get_screen_size
    take_screen_capture

19. "run_actions" must contain an "actions" array.

20. Each item in the "actions" array must have this form:

{{
    "action": "existing_tool_name",
    "arguments": {{}}
}}

21. Do not put "run_actions" inside another "run_actions".

22. Use short, reliable action sequences.

23. Add a "wait" action when an application or webpage
    needs time to open before the next action.

24. When opening a website, prefer "open_url" when the user
    provides an actual URL or domain.

25. When interacting with a browser after opening it,
    use keyboard and mouse primitives rather than inventing
    browser-specific tools.

Examples:

User:

"open vs code"

Return:

{{
    "action": "open_application",
    "arguments": "{{\\\\"application\\\\": \\\\"vs code\\\\"}}",
    "response": ""
}}

User:

"copy hello world"

Return:

{{
    "action": "set_clipboard",
    "arguments": "{{\\\\"text\\\\": \\\\"hello world\\\\"}}",
    "response": ""
}}

User:

"remember that my name is Alex"

Return:

{{
    "action": "remember_fact",
    "arguments": "{{\\\\"key\\\\": \\\\"name\\\\", \\\\"value\\\\": \\\\"Alex\\\\"}}",
    "response": ""
}}

User:

"what is quantum physics?"

Return:

{{
    "action": "AI_QUERY",
    "arguments": "{{}}",
    "response": ""
}}

User:

"open Chrome and go to google.com"

Return:

{{
    "action": "run_actions",
    "arguments": "{{\\\\"actions\\\\":[{{\\\\"action\\\\":\\\\"open_application\\\\",\\\\"arguments\\\\":{{\\\\"application\\\\":\\\\"Chrome\\\\"}}}},{{\\\\"action\\\\":\\\\"wait\\\\",\\\\"arguments\\\\":{{\\\\"seconds\\\\":2}}}},{{\\\\"action\\\\":\\\\"hotkey\\\\",\\\\"arguments\\\\":{{\\\\"keys\\\\":\\\\"ctrl+l\\\\"}}}},{{\\\\"action\\\\":\\\\"type_text\\\\",\\\\"arguments\\\\":{{\\\\"text\\\\":\\\\"https://google.com\\\\"}}}},{{\\\\"action\\\\":\\\\"press_key\\\\",\\\\"arguments\\\\":{{\\\\"key\\\\":\\\\"enter\\\\"}}}}]}}",
    "response": ""
}}

User:

"open Notepad and type hello JARVIS"

Return:

{{
    "action": "run_actions",
    "arguments": "{{\\\\"actions\\\\":[{{\\\\"action\\\\":\\\\"open_application\\\\",\\\\"arguments\\\\":{{\\\\"application\\\\":\\\\"Notepad\\\\"}}}},{{\\\\"action\\\\":\\\\"wait\\\\",\\\\"arguments\\\\":{{\\\\"seconds\\\\":2}}}},{{\\\\"action\\\\":\\\\"type_text\\\\",\\\\"arguments\\\\":{{\\\\"text\\\\":\\\\"hello JARVIS\\\\"}}}}]}}",
    "response": ""
}}
""",
            }
        ]

        # ------------------------------------------------------
        # Conversation context
        # ------------------------------------------------------

        messages.extend(
            recent_messages
        )

        # ------------------------------------------------------
        # Current user request
        # ------------------------------------------------------

        messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        # ------------------------------------------------------
        # Dynamic schema
        # ------------------------------------------------------

        intent_schema = (
            self.build_intent_schema()
        )

        # ------------------------------------------------------
        # Groq structured output
        # ------------------------------------------------------

        response = self.client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "jarvis_intent",
                    "strict": True,
                    "schema": intent_schema,
                },
            },
        )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        result = json.loads(
            content
        )

        # ------------------------------------------------------
        # Validate action
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

        except json.JSONDecodeError:

            arguments = {}

        if not isinstance(
            arguments,
            dict,
        ):
            arguments = {}

        # ------------------------------------------------------
        # Additional validation for run_actions
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

                # AI_QUERY cannot be executed as part of
                # a local computer sequence.
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
