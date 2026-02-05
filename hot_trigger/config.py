from __future__ import annotations

from pathlib import Path
from typing import Any

from hot_trigger import yaml_compat
from pydantic import BaseModel, Field, ValidationError


class TriggerConfig(BaseModel):
    enabled: bool = True
    min_jump: int = 5
    min_spike: float = 30.0
    keywords: list[str] = Field(default_factory=list)
    cooldown_minutes: int = 60


class LLMConfig(BaseModel):
    provider: str = "openai_compatible"
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    api_key_env: str = "OPENAI_API_KEY"
    timeout_seconds: float = 20.0


class OutputConfig(BaseModel):
    directory: str = "output"


class SourceConfig(BaseModel):
    platform: str = "xhs"
    snapshot_file: str | None = None


class AppConfig(BaseModel):
    source: SourceConfig
    triggers: TriggerConfig = Field(default_factory=TriggerConfig)
    llm: LLMConfig
    output: OutputConfig = Field(default_factory=OutputConfig)


def load_config(path: str | Path) -> AppConfig:
    with Path(path).open("r", encoding="utf-8") as fp:
        payload: dict[str, Any] = yaml_compat.safe_load(fp.read()) or {}
    try:
        return AppConfig.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid config: {exc}") from exc
