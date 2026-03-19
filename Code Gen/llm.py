import sys
import builtins
def _custom_print(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    builtins.print(*args, **kwargs)
print = _custom_print

import os 
import requests 
from dotenv import load_dotenv 

load_dotenv ()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise EnvironmentError(
        "OPENROUTER_API_KEY environment variable is not set."
    )
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free")


def generate (system_prompt :str ,user_prompt :str )->str :
    """Send a prompt to OpenRouter and return the text response."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 8192,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=300)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise ValueError("Cannot connect to OpenRouter API.")
    except requests.exceptions.Timeout:
        raise ValueError("OpenRouter request timed out.")
    except requests.exceptions.HTTPError as e:
        raise ValueError(f"OpenRouter API error: {e}\\n{response.text}")

    data = response.json()
    try:
        content = data["choices"][0]["message"].get("content")
        if content is None:
            # Sometimes free APIs return None for content if context is too large or filtered
            print(f"\\n[WARNING] OpenRouter returned empty content. Full response: {data}\\n")
            return ""
        return content.strip()
    except (KeyError, IndexError):
        raise ValueError(f"Unexpected response format from OpenRouter: {data}")
