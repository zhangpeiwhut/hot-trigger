from __future__ import annotations

from typing import Protocol

from hot_trigger.models import AnalysisArtifact, DecisionArtifact, TrendSnapshot, TriggerEvent


class TrendSource(Protocol):
    @property
    def platform_id(self) -> str: ...

    def fetch_snapshot(self) -> TrendSnapshot: ...


class TriggerEngine(Protocol):
    def evaluate(self, current: TrendSnapshot, previous: TrendSnapshot | None) -> list[TriggerEvent]: ...


class Analyzer(Protocol):
    def analyze(self, event: TriggerEvent) -> AnalysisArtifact: ...


class Decider(Protocol):
    def decide(self, event: TriggerEvent, analysis: AnalysisArtifact) -> DecisionArtifact: ...
