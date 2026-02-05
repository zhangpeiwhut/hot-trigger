from __future__ import annotations

from pathlib import Path

from hot_trigger.adapters.xhs import XHSTrendSource
from hot_trigger.analysis.analyzer import LLMAnalyzer
from hot_trigger.analysis.llm_client import OpenAICompatibleClient
from hot_trigger.config import AppConfig
from hot_trigger.decision.engine import DeterministicDecider
from hot_trigger.pipeline import HotTriggerPipeline
from hot_trigger.triggers.engine import YAMLDrivenTriggerEngine


def build_source(config: AppConfig):
    if config.source.platform == "xhs":
        return XHSTrendSource(snapshot_file=config.source.snapshot_file)
    raise ValueError(f"Unsupported platform: {config.source.platform}")


def build_pipeline(config: AppConfig) -> HotTriggerPipeline:
    source = build_source(config)
    trigger_engine = YAMLDrivenTriggerEngine(config=config.triggers)
    llm_client = OpenAICompatibleClient(config.llm)
    analyzer = LLMAnalyzer(llm_client, config.llm)
    decider = DeterministicDecider()
    return HotTriggerPipeline(source=source, trigger_engine=trigger_engine, analyzer=analyzer, decider=decider)


def snapshot_state_path(output_dir: str, platform_id: str) -> Path:
    return Path(output_dir) / f"last_snapshot_{platform_id}.json"
