from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from hot_trigger.models import AnalysisArtifact, DecisionArtifact, TriggerEvent


class ConsoleAndFileAction:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)

    def emit(self, events: list[TriggerEvent], analyses: list[AnalysisArtifact], decisions: list[DecisionArtifact]) -> Path:
        now = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        run_dir = self.output_dir / now
        run_dir.mkdir(parents=True, exist_ok=True)

        payload = {
            "events": [x.model_dump(mode="json") for x in events],
            "analyses": [x.model_dump(mode="json") for x in analyses],
            "decisions": [x.model_dump(mode="json") for x in decisions],
        }
        json_path = run_dir / "result.json"
        with json_path.open("w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False, indent=2)

        md_path = run_dir / "result.md"
        with md_path.open("w", encoding="utf-8") as fp:
            fp.write("# hot-trigger run result\n\n")
            for d in decisions:
                fp.write(f"## Event {d.event_id}\n")
                fp.write(f"- Ride score: **{d.ride_score}**\n")
                fp.write(f"- Verdict: **{d.verdict.value}**\n")
                fp.write("- Rationale:\n")
                for item in d.rationale:
                    fp.write(f"  - {item}\n")
                fp.write(f"- Suggested comment: {d.suggested_comment}\n")
                fp.write("- Suggested post outline:\n")
                for line in d.suggested_post_outline:
                    fp.write(f"  - {line}\n")
                fp.write("\n")

        print(f"[hot-trigger] decisions={len(decisions)} output={run_dir}")
        for d in decisions:
            print(f"- {d.event_id} => {d.verdict.value} ({d.ride_score})")

        return run_dir
