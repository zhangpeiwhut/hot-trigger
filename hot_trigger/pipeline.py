from __future__ import annotations

import json
from pathlib import Path

from hot_trigger.models import AnalysisArtifact, DecisionArtifact, TrendSnapshot
from hot_trigger.protocols import Analyzer, Decider, TrendSource, TriggerEngine


class PipelineResult(dict):
    snapshot: TrendSnapshot
    analyses: list[AnalysisArtifact]
    decisions: list[DecisionArtifact]


class HotTriggerPipeline:
    def __init__(self, source: TrendSource, trigger_engine: TriggerEngine, analyzer: Analyzer, decider: Decider):
        self.source = source
        self.trigger_engine = trigger_engine
        self.analyzer = analyzer
        self.decider = decider

    def run(self, previous_snapshot: TrendSnapshot | None = None) -> dict:
        current = self.source.fetch_snapshot()
        events = self.trigger_engine.evaluate(current=current, previous=previous_snapshot)
        analyses: list[AnalysisArtifact] = []
        decisions: list[DecisionArtifact] = []

        for event in events:
            analysis = self.analyzer.analyze(event)
            decision = self.decider.decide(event, analysis)
            analyses.append(analysis)
            decisions.append(decision)

        return {
            "snapshot": current,
            "events": events,
            "analyses": analyses,
            "decisions": decisions,
        }


def load_snapshot(path: Path) -> TrendSnapshot | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)
    return TrendSnapshot.model_validate(data)


def save_snapshot(path: Path, snapshot: TrendSnapshot) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        json.dump(snapshot.model_dump(mode="json"), fp, ensure_ascii=False, indent=2)
