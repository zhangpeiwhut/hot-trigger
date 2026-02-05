from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hot_trigger.models import ContentType, ContentUnit, TrendSnapshot
from hot_trigger.protocols import TrendSource


class XHSTrendSource(TrendSource):
    def __init__(self, snapshot_file: str | None = None):
        self._snapshot_file = snapshot_file

    @property
    def platform_id(self) -> str:
        return "xhs"

    def fetch_snapshot(self) -> TrendSnapshot:
        rows = self._load_rows()
        units = [self._to_unit(row) for row in rows]
        return TrendSnapshot(
            timestamp=datetime.now(timezone.utc),
            platform_id=self.platform_id,
            units=units,
        )

    def _load_rows(self) -> list[dict[str, Any]]:
        if not self._snapshot_file:
            return [
                {
                    "title": "春季通勤穿搭合集",
                    "url": "https://xhs.example/post/1",
                    "rank": 3,
                    "heat_score": 86.0,
                    "text": "7套早八通勤look，显瘦+有质感",
                    "author": "小周穿搭",
                    "tags": ["春季穿搭", "通勤", "ootd"],
                    "content_type": "image",
                },
                {
                    "title": "打工人健康午餐挑战",
                    "url": "https://xhs.example/post/2",
                    "rank": 12,
                    "heat_score": 61.0,
                    "text": "15分钟高蛋白午餐，办公室也能做",
                    "author": "轻食实验室",
                    "tags": ["健康饮食", "午餐", "效率"],
                    "content_type": "video",
                },
            ]
        with Path(self._snapshot_file).open("r", encoding="utf-8") as fp:
            data = json.load(fp)
            if isinstance(data, dict):
                data = data.get("units", [])
            return data

    def _to_unit(self, row: dict[str, Any]) -> ContentUnit:
        title = str(row.get("title", ""))
        author = str(row.get("author", ""))
        source = f"{title}|{author}|{self.platform_id}"
        unit_id = row.get("unit_id") or hashlib.md5(source.encode("utf-8")).hexdigest()
        ctype = str(row.get("content_type", "text"))

        return ContentUnit(
            unit_id=unit_id,
            title=title,
            url=row.get("url"),
            rank=row.get("rank"),
            heat_score=row.get("heat_score"),
            content_type=ContentType(ctype),
            text_payload=row.get("text_payload") or row.get("text"),
            media_payload=row.get("media_payload"),
            author=row.get("author"),
            tags=row.get("tags") or [],
            raw=row,
        )
