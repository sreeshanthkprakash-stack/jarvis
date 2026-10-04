import os
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# MODEL BACKEND
# ============================================================
# "ollama" (default) -> your LOCAL model, served by Ollama on this PC
# "groq"             -> Groq cloud API
#
# Switch with  JARVIS_BACKEND=groq  in .env  (no code change needed).

BACKEND = os.getenv("JARVIS_BACKEND", "ollama").strip().lower()

LOCAL = BACKEND != "groq"

if LOCAL:
    # Ollama's OpenAI-compatible endpoint. Make sure Ollama is running
    # (the tray app, or `ollama serve`).
    MODEL_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
    MODEL_API_KEY = "ollama"            # ignored by Ollama, but required by the client
    MODEL = os.getenv("OLLAMA_MODEL", "jarvis-qwen-fast")
    MODEL_DISPLAY_NAME = os.getenv("JARVIS_MODEL_NAME", "Qwen3 4B")
    RUNTIME_DESCRIPTION = "locally on this PC through Ollama"
else:
    # Put your key in a file named .env in the project root:
    #     GROQ_API_KEY=your_key_here
    MODEL_BASE_URL = "https://api.groq.com/openai/v1"
    MODEL_API_KEY = os.getenv("GROQ_API_KEY", "")
    # Groq rotates its model list; override with GROQ_MODEL in .env.
    MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    MODEL_DISPLAY_NAME = os.getenv("JARVIS_MODEL_NAME", MODEL)
    RUNTIME_DESCRIPTION = "in the cloud through the Groq API"

MODEL_TEMPERATURE = 0.2

MODEL_MAX_TOKENS = 500


# ============================================================
# JARVIS SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are JARVIS, a personal AI assistant running on a Windows PC.

Underlying model:
- {MODEL_NAME}
- Running {RUNTIME}

Personality:
- Calm
- Intelligent
- Concise
- Professional
- Helpful
- Slightly futuristic

Rules:
- Be truthful.
- Never claim to have performed an action unless a tool actually performed it.
- If you don't know something, say so.
- Keep simple answers concise.
- Normally answer in 1-3 sentences.
- Do not unnecessarily explain things.
- Do not repeat the user's request.
- Do not expose your reasoning.

When asked which model you use, say:
"I am JARVIS, powered by {MODEL_NAME}, running {RUNTIME}."
"""

SYSTEM_PROMPT = (
    SYSTEM_PROMPT
    .replace("{MODEL_NAME}", MODEL_DISPLAY_NAME)
    .replace("{RUNTIME}", RUNTIME_DESCRIPTION)
)


# ============================================================
# SPEED SETTINGS
# ============================================================

# Fail fast instead of freezing for ~90 s on a network stall.
# Local CPU inference can take a while on the first call (model load +
# prompt processing), so allow much longer than the cloud.
CLIENT_TIMEOUT = 120 if LOCAL else 20
CLIENT_RETRIES = 0 if LOCAL else 1

# gpt-oss models on Groq accept "low" | "medium" | "high".
# Lower = faster. Set GROQ_REASONING_EFFORT= (empty) to disable.
# Models that don't support it are detected automatically.
# Local Qwen3: thinking is already switched off in the model's template,
# so nothing to send.
REASONING_EFFORT = "" if LOCAL else os.getenv("GROQ_REASONING_EFFORT", "low")

# True  -> ONE model call decides + answers (native tool calling).
# False -> old behaviour (understand() call, then ask() call).
USE_NATIVE_TOOLS = True

# Max model<->tool rounds for a single request.
AGENT_MAX_STEPS = 4
AGENT_MAX_TOKENS = 300 if LOCAL else 600

# Fewer messages = less to process on each local call.
HISTORY_MESSAGES = 8 if LOCAL else 12

# Ollama's OpenAI endpoint ignores tool_choice; only send it to the cloud.
SEND_TOOL_CHOICE = not LOCAL

# Shorter tool descriptions = smaller prompt = faster local calls.
TOOL_DESC_LIMIT = 110 if LOCAL else 240

# Load the model and prime the prompt cache at startup, so the first
# real command isn't the slow one.
WARM_UP = LOCAL

# Print how long each model call / tool call takes.
DEBUG_TIMING = True

# Only these tools are shown to the model (smaller prompt, fewer
# wrong picks). Everything else stays registered locally.
_CLOUD_TOOLS = [
    "open_application", "close_application",
    "open_url", "search_web",
    "type_text", "press_key", "hotkey", "wait",
    "computer_click_target", "computer_click_spatial",
    "describe_screen",
    "volume_up", "volume_down", "mute_volume", "lock_computer",
    "get_time", "get_date", "get_system_info",
    "take_screenshot", "get_clipboard", "set_clipboard",
    "remember_fact", "list_memory",
]

# A 4B model picks tools more reliably from a short list
# (time/date/system info are handled by the local fast path).
_LOCAL_TOOLS = [
    "open_application", "close_application",
    "open_url", "search_web",
    "type_text", "press_key", "hotkey", "wait",
    "computer_click_target",
    "describe_screen",
    "volume_up", "volume_down", "mute_volume", "lock_computer",
    "remember_fact",
]

AGENT_TOOLS = _LOCAL_TOOLS if LOCAL else _CLOUD_TOOLS

# After ONE call to one of these, return the tool's own message
# and skip the second model call.
SINGLE_SHOT_TOOLS = [
    "volume_up", "volume_down", "mute_volume", "lock_computer",
    "search_web",
]

# Appended to SYSTEM_PROMPT only for the tool-calling path.
AGENT_PROMPT = """

Tool use:
- Use a tool whenever the user wants something done on the computer. Otherwise just answer.
- For multi-step tasks, request all independent steps together, in order. Use wait after opening an app or page.
- To search the web, call search_web with the query. To open a specific website, call open_url.
- Use the exact values the user gave. Never invent app names, URLs or file paths.
- After tools run, reply in one short sentence. If a tool reported an error, say so; never claim success.
- If the request is too ambiguous to act on, ask one short question.
"""
