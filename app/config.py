import os
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# GROQ API (cloud) -- the only model backend
# ============================================================
# Put your key in a file named .env in the project root:
#
#     GROQ_API_KEY=your_key_here
#
# Never paste the key into this file (it could end up on GitHub).

MODEL_BASE_URL = "https://api.groq.com/openai/v1"

MODEL_API_KEY = os.getenv("GROQ_API_KEY", "")

# Groq rotates its model list. If this name stops working, set
# GROQ_MODEL in .env to a current one from console.groq.com/docs/models
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

MODEL_TEMPERATURE = 0.2

MODEL_MAX_TOKENS = 300


# ============================================================
# JARVIS SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are JARVIS, a personal AI assistant running on a Windows PC.

Underlying model:
- OpenAI GPT-OSS 120B
- Running in the cloud through the Groq API

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
"I am JARVIS, powered by GPT-OSS 120B running through the Groq API."
"""