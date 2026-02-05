from __future__ import annotations

import argparse
import json
from pathlib import Path


from hot_trigger import yaml_compat
from hot_trigger.actions.output import ConsoleAndFileAction
from hot_trigger.bootstrap import build_pipeline, snapshot_state_path
from hot_trigger.config import load_config
from hot_trigger.pipeline import load_snapshot, save_snapshot


def cmd_init(args: argparse.Namespace) -> int:
    target = Path(args.path)
    if target.exists() and not args.force:
        raise SystemExit(f"Config already exists: {target} (use --force to overwrite)")

    template = {
        "source": {"platform": "xhs", "snapshot_file": "examples/xhs_snapshot.json"},
        "triggers": {
            "enabled": True,
            "min_jump": 5,
            "min_spike": 25.0,
            "keywords": ["穿搭", "效率", "AI"],
            "cooldown_minutes": 60,
        },
        "llm": {
            "provider": "openai_compatible",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini",
            "api_key_env": "OPENAI_API_KEY",
            "timeout_seconds": 20,
        },
        "output": {"directory": "output"},
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as fp:
        fp.write(yaml_compat.safe_dump(template, allow_unicode=True, sort_keys=False))
    print(f"Created config: {target}")
    return 0


def _run_pipeline(config_path: str, snapshot_override: str | None = None) -> int:
    config = load_config(config_path)
    if snapshot_override:
        config.source.snapshot_file = snapshot_override

    pipeline = build_pipeline(config)
    state_path = snapshot_state_path(config.output.directory, config.source.platform)
    previous = load_snapshot(state_path)

    result = pipeline.run(previous_snapshot=previous)
    save_snapshot(state_path, result["snapshot"])

    action = ConsoleAndFileAction(config.output.directory)
    action.emit(result["events"], result["analyses"], result["decisions"])

    print(json.dumps({"events": len(result["events"]), "decisions": len(result["decisions"])}, ensure_ascii=False))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    return _run_pipeline(args.config)


def cmd_test(args: argparse.Namespace) -> int:
    return _run_pipeline(args.config, snapshot_override=args.snapshot)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hot-trigger")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Generate a starter config")
    p_init.add_argument("--path", default="config.yaml")
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_run = sub.add_parser("run", help="Run full trigger->analysis->decision pipeline")
    p_run.add_argument("--config", required=True)
    p_run.set_defaults(func=cmd_run)

    p_test = sub.add_parser("test", help="Run pipeline using supplied snapshot json")
    p_test.add_argument("--config", required=True)
    p_test.add_argument("--snapshot", required=True)
    p_test.set_defaults(func=cmd_test)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
