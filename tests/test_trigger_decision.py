from datetime import datetime, timezone

from hot_trigger.config import TriggerConfig
from hot_trigger.decision.engine import DeterministicDecider
from hot_trigger.models import AnalysisArtifact, ContentType, ContentUnit, TrendSnapshot
from hot_trigger.triggers.engine import YAMLDrivenTriggerEngine


def _unit(uid: str, title: str, rank: int, heat: float, tags: list[str]):
    return ContentUnit(
        unit_id=uid,
        title=title,
        rank=rank,
        heat_score=heat,
        content_type=ContentType.text,
        tags=tags,
        raw={},
    )


def test_trigger_engine_generates_events(tmp_path):
    previous = TrendSnapshot(
        timestamp=datetime.now(timezone.utc),
        platform_id="xhs",
        units=[_unit("1", "A", 10, 40, ["效率"])],
    )
    current = TrendSnapshot(
        timestamp=datetime.now(timezone.utc),
        platform_id="xhs",
        units=[_unit("1", "A", 2, 70, ["效率"]), _unit("2", "B AI", 15, 55, ["AI"])],
    )
    engine = YAMLDrivenTriggerEngine(
        TriggerConfig(min_jump=5, min_spike=20, keywords=["AI"], cooldown_minutes=1),
        cooldown_store=tmp_path / "cooldown.json",
    )

    events = engine.evaluate(current=current, previous=previous)

    trigger_ids = {e.trigger_id for e in events}
    assert "new_entry" in trigger_ids
    assert "rank_jump" in trigger_ids
    assert "heat_spike" in trigger_ids
    assert "keyword_match" in trigger_ids


def test_deterministic_decision_output():
    event_unit = _unit("u", "AI效率法", 3, 88, ["AI", "效率"])
    from hot_trigger.models import TriggerEvent

    event = TriggerEvent(
        event_id="e1",
        trigger_id="keyword_match",
        platform_id="xhs",
        unit_id="u",
        occurred_at=datetime.now(timezone.utc),
        delta={"keywords": ["AI"]},
        unit=event_unit,
    )
    analysis = AnalysisArtifact(
        event_id="e1",
        summary="AI效率法爆火",
        why_trending="可执行",
        angles=["模板拆解", "反例对比"],
        audience="职场人",
        risk_flags=[],
        participation_modes=["评论", "二创"],
        model="demo",
    )

    decision = DeterministicDecider().decide(event, analysis)

    assert 0 <= decision.ride_score <= 100
    assert decision.verdict.value in {"GO", "WAIT", "NO"}
