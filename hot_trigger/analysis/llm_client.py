from __future__ import annotations

import os
from typing import Any, Protocol

from hot_trigger.config import LLMConfig


class LLMClient(Protocol):
    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]: ...


class OpenAICompatibleClient:
    def __init__(self, cfg: LLMConfig):
        self.cfg = cfg
        api_key = os.getenv(cfg.api_key_env)
        if not api_key:
            raise ValueError(f"Missing LLM API key env: {cfg.api_key_env}")
        self._headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        try:
            import httpx
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise RuntimeError("httpx is required for LLM calls") from exc

        payload = {
            "model": self.cfg.model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        with httpx.Client(timeout=self.cfg.timeout_seconds) as client:
            resp = client.post(f"{self.cfg.base_url}/chat/completions", headers=self._headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        content = data["choices"][0]["message"]["content"]
        if isinstance(content, list):
            text = "".join(part.get("text", "") for part in content if isinstance(part, dict))
        else:
            text = content
        import json

        return json.loads(text)
