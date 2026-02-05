from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from hot_trigger.config import TriggerConfig
from hot_trigger.models import ContentUnit, TrendSnapshot, TriggerEvent


class YAMLDrivenTriggerEngine:
    def __init__(self, config: TriggerConfig, cooldown_store: Path | None = None):
        self.config = config
        self.cooldown_store = cooldown_store or Path("output/.cooldown.json")
        self._cooldown_map = self._load_cooldown_map()

    def evaluate(self, current: TrendSnapshot, previous: TrendSnapshot | None) -> list[TriggerEvent]:
        if not self.config.enabled:
            return []
        previous_index = {u.unit_id: u for u in previous.units} if previous else {}
        events: list[TriggerEvent] = []

        for unit in current.units:
            old = previous_index.get(unit.unit_id)
            events.extend(self._maybe_new_entry(current.platform_id, unit, old))
            events.extend(self._maybe_rank_jump(current.platform_id, unit, old))
            events.extend(self._maybe_heat_spike(current.platform_id, unit, old))
            events.extend(self._maybe_keyword_match(current.platform_id, unit))

        filtered = [e for e in events if self._is_outside_cooldown(e)]
        self._persist_cooldown(filtered)
        return filtered

    def _maybe_new_entry(self, platform_id: str, unit: ContentUnit, old: ContentUnit | None) -> list[TriggerEvent]:
        if old is not None:
            return []
        return [self._build_event("new_entry", platform_id, unit, {"status": "new"})]

    def _maybe_rank_jump(self, platform_id: str, unit: ContentUnit, old: ContentUnit | None) -> list[TriggerEvent]:
        if not old or unit.rank is None or old.rank is None:
            return []
        jump = old.rank - unit.rank
        if jump >= self.config.min_jump:
            return [self._build_event("rank_jump", platform_id, unit, {"rank_jump": jump, "from": old.rank, "to": unit.rank})]
        return []

    def _maybe_heat_spike(self, platform_id: str, unit: ContentUnit, old: ContentUnit | None) -> list[TriggerEvent]:
        if not old or unit.heat_score is None or old.heat_score in (None, 0):
            return []
        growth = ((unit.heat_score - old.heat_score) / old.heat_score) * 100
        if growth >= self.config.min_spike:
            return [
                self._build_event(
                    "heat_spike",
                    platform_id,
                    unit,
                    {"growth_pct": round(growth, 2), "from": old.heat_score, "to": unit.heat_score},
                )
            ]
        return []

    def _maybe_keyword_match(self, platform_id: str, unit: ContentUnit) -> list[TriggerEvent]:
        if not self.config.keywords:
            return []
        text = " ".join([unit.title, unit.text_payload or "", " ".join(unit.tags)]).lower()
        hits = [kw for kw in self.config.keywords if kw.lower() in text]
        if hits:
            return [self._build_event("keyword_match", platform_id, unit, {"keywords": hits})]
        return []

    def _build_event(self, trigger_id: str, platform_id: str, unit: ContentUnit, delta: dict) -> TriggerEvent:
        occurred_at = datetime.now(timezone.utc)
        seed = f"{trigger_id}:{platform_id}:{unit.unit_id}:{occurred_at.isoformat()}"
        event_id = hashlib.sha1(seed.encode("utf-8")).hexdigest()
        return TriggerEvent(
            event_id=event_id,
            trigger_id=trigger_id,
            platform_id=platform_id,
            unit_id=unit.unit_id,
            occurred_at=occurred_at,
            delta=delta,
            unit=unit,
        )

    def _cooldown_key(self, event: TriggerEvent) -> str:
        return f"{event.platform_id}:{event.unit_id}:{event.trigger_id}"

    def _is_outside_cooldown(self, event: TriggerEvent) -> bool:
        key = self._cooldown_key(event)
        stored = self._cooldown_map.get(key)
        if not stored:
            return True
        last_seen = datetime.fromisoformat(stored)
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=self.config.cooldown_minutes)
        return last_seen < cutoff

    def _load_cooldown_map(self) -> dict[str, str]:
        if not self.cooldown_store.exists():
            return {}
        with self.cooldown_store.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
            return data if isinstance(data, dict) else {}

    def _persist_cooldown(self, events: list[TriggerEvent]) -> None:
        if not events:
            return
        self.cooldown_store.parent.mkdir(parents=True, exist_ok=True)
        for event in events:
            self._cooldown_map[self._cooldown_key(event)] = event.occurred_at.isoformat()
        with self.cooldown_store.open("w", encoding="utf-8") as fp:
            json.dump(self._cooldown_map, fp, ensure_ascii=False, indent=2)
