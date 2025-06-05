import os
import requests
from typing import List, Dict, Optional
from utils.logger_utils import safe_log

# === Model Config ===
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:instruct")  # Use "llama3.2" or similar tag if renamed locally
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/v1")

# === In-memory context (optional, not required by Ollama itself) ===
conversation_memory: Dict[str, List[Dict]] = {}


def chat_with_agent(prompt: str,
                    model: str = OLLAMA_MODEL,
                    msg_history: Optional[List[Dict]] = None,
                    logging=safe_log) -> List[Dict]:
    """
    Full conversation loop with a model using Ollama.
    Appends messages to history and logs each step.
    """
    if msg_history is None:
        msg_history = []

    logging(f"Prompting model `{model}`")
    logging(prompt)

    # Compose the message list
    messages = [{"role": "system", "content": "You are a helpful coding assistant."}]
    messages.extend(msg_history)
    messages.append({"role": "user", "content": prompt})

    try:
        response = requests.post(
            f"{OLLAMA_API_URL}/chat/completions",
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1024
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        output = data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        output = f"[OLLAMA ERROR]: {e}"

    logging(f"Model `{model}` response:")
    logging(output)

    # Save full history
    msg_history.append({"role": "user", "content": prompt})
    msg_history.append({"role": "assistant", "content": output})
    return msg_history


def get_response_from_llm(msg: str,
                          client=None,
                          model: str = OLLAMA_MODEL,
                          system_message: str = "",
                          print_debug: bool = False,
                          msg_history: Optional[List[Dict]] = None) -> (str, dict):
    """
    One-shot interface. Returns just the final response.
    """
    if print_debug:
        safe_log(f"[{model}] One-shot input: {msg}")

    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    if msg_history:
        messages.extend(msg_history)
    messages.append({"role": "user", "content": msg})

    try:
        response = requests.post(
            f"{OLLAMA_API_URL}/chat/completions",
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.5,
                "max_tokens": 1024
            },
            timeout=60
        )
        response.raise_for_status()
        output = response.json()["choices"][0]["message"]["content"].strip()
        return output, {}
    except Exception as e:
        return f"[OLLAMA ERROR]: {str(e)}", {}


def summarize_messages(client,
                       model: str,
                       messages: List[Dict],
                       system_message: str = "") -> str:
    """
    Create a condensed version of the conversation to save context.
    """
    content = "\n".join(
        f"{m['role']}: {m['content']}" for m in messages if m['role'] in ("user", "assistant")
    )
    summary_prompt = (
        "Summarize the following conversation while preserving key decisions and logic:\n\n" + content
    )

    summary, _ = get_response_from_llm(
        summary_prompt,
        model=model,
        system_message="You are a summarizer that condenses long dialogues into essential summaries for continued work."
    )
    return summary
