from __future__ import annotations

import json
from typing import Any

import httpx

from agent_service.config import settings


class FaraClient:
    def __init__(self, base_url: str | None = None, model_name: str | None = None) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model_name = model_name or settings.fara_model_name

    def _call_generate(self, prompt: str, json_mode: bool) -> str:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
        }
        if json_mode:
            payload["format"] = "json"
        with httpx.Client(timeout=30) as client:
            response = client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return str(data.get("response", "")).strip()

    def predict_action(self, goal: str, screenshot_b64: str) -> dict[str, Any]:
        prompt = (
            "You are a desktop action model. Return JSON with keys action,x,y,text,reason."
            f" Goal: {goal}. Screenshot bytes base64 length: {len(screenshot_b64)}"
        )
        try:
            response_text = self._call_generate(prompt, json_mode=True)
            parsed = json.loads(response_text)
            if isinstance(parsed, dict):
                if "action" in parsed:
                    return parsed
                if "name" in parsed and "coordinate" in parsed:
                    coordinate = parsed.get("coordinate") or [0, 0]
                    action_name = str(parsed.get("name", "")).lower()
                    if "click" in action_name:
                        return {
                            "action": "click",
                            "x": int(coordinate[0]),
                            "y": int(coordinate[1]),
                            "reason": "normalized-from-fara",
                        }
        except Exception:
            pass
        return {"action": "none", "reason": "vision-fallback-no-op"}

    def describe_screen(self, question: str, screenshot_b64: str) -> str:
        prompt = (
            "You are a vision assistant. Answer briefly."
            f" Question: {question}. Screenshot bytes base64 length: {len(screenshot_b64)}"
        )
        try:
            response_text = self._call_generate(prompt, json_mode=False)
            return response_text or "No description produced."
        except Exception:
            return "Vision model unavailable; unable to describe screen."
