from __future__ import annotations

import json

from hot_trigger.analysis.llm_client import LLMClient
from hot_trigger.config import LLMConfig
from hot_trigger.models import AnalysisArtifact, TriggerEvent


class LLMAnalyzer:
    def __init__(self, client: LLMClient, cfg: LLMConfig):
        self.client = client
        self.cfg = cfg

    def analyze(self, event: TriggerEvent) -> AnalysisArtifact:
        system_prompt = (
            "You are a trend analyst. Return strict JSON with keys: "
            "summary, why_trending, angles, audience, risk_flags, participation_modes."
        )
        user_prompt = (
            "Analyze this trigger event and keep output concise in Chinese.\n"
            f"event={json.dumps(event.model_dump(mode='json'), ensure_ascii=False)}"
        )
        data = self.client.complete_json(system_prompt=system_prompt, user_prompt=user_prompt)
        return AnalysisArtifact(
            event_id=event.event_id,
            summary=data.get("summary", ""),
            why_trending=data.get("why_trending", ""),
            angles=[str(v) for v in data.get("angles", [])],
            audience=str(data.get("audience", "")),
            risk_flags=[str(v) for v in data.get("risk_flags", [])],
            participation_modes=[str(v) for v in data.get("participation_modes", [])],
            model=self.cfg.model,
        )
