import os
import json
import urllib.request
from boros.adapters.base_adapter import BaseAdapter

class GeminiAdapter(BaseAdapter):
    """Google Gemini adapter via REST API."""

    def __init__(self, config):
        self.config = config
        self.model = config.get("model", "gemini-1.5-pro")

    def complete(self, messages: list, tools: list = None, system: str = None) -> dict:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set in environment")

        contents = []
        if system:
            contents.append({"role": "user", "parts": [{"text": f"[System Instructions]\n{system}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})

        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            text = msg.get("content", "")
            if isinstance(text, list):
                text = " ".join(b.get("text", str(b)) for b in text)
            contents.append({"role": role, "parts": [{"text": str(text)}]})

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={api_key}"
        payload = json.dumps({"contents": contents}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())

        text_out = ""
        try:
            text_out = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            text_out = str(data)

        return {
            "content": [{"type": "text", "text": text_out}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 0, "output_tokens": 0}
        }

    @property
    def supports_tools(self):
        return False
