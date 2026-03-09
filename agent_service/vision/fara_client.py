from __future__ import annotations

import json
import re
from typing import Any

import httpx

from agent_service.config import settings


class FaraClient:
    def __init__(self, base_url: str | None = None, model_name: str | None = None) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model_name = model_name or settings.fara_model_name

    def _call_generate(self, prompt: str, json_mode: bool, screenshot_b64: str | None = None) -> str:
        payload = {"model": self.model_name, "prompt": prompt, "stream": False}
        if screenshot_b64:
            payload["images"] = [screenshot_b64]
        if json_mode:
            payload["format"] = "json"

        with httpx.Client(timeout=settings.fara_timeout_seconds) as client:
            response = client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return str(data.get("response", "")).strip()

    def predict_action(self, goal: str, screenshot_b64: str) -> dict[str, Any]:
        prompt = (
            "You are a desktop action model."
            " Analyze the screenshot and return JSON only with keys: action,x,y,text,reason."
            " action must be one of: click,type,none."
            " If there is a clear next action, avoid returning none."
            f" Goal: {goal}."
        )
        try:
            response_text = self._call_generate(prompt, json_mode=True, screenshot_b64=screenshot_b64)
            parsed = self._extract_json_object(response_text)
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
        except Exception as exc:
            return {"action": "none", "reason": f"vision-error:{exc}"}
        return {"action": "none", "reason": "vision-fallback-no-op"}

    def describe_screen(self, question: str, screenshot_b64: str) -> str:
        prompt = (
            "You are a vision assistant. Answer briefly."
            f" Question: {question}."
        )
        try:
            response_text = self._call_generate(prompt, json_mode=False, screenshot_b64=screenshot_b64)
            return response_text or "No description produced."
        except Exception:
            return "Vision model unavailable; unable to describe screen."
    @staticmethod
    def _extract_json_object(text: str) -> dict[str, Any] | None:
        text = text.strip()
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        # Try to recover from wrapped output (markdown/tool tags/mixed text).
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None
        snippet = match.group(0)
        try:
            parsed = json.loads(snippet)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return None
        return None
