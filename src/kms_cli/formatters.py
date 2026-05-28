from __future__ import annotations

import json
from typing import Any


def format_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def format_detail(data: dict[str, Any]) -> str:
    return format_json(data)


def format_records(data: dict[str, Any], *, title: str) -> str:
    records = _extract_records(data)
    if not records:
        return f"{title}: 无数据"

    lines = [f"{title}:"]
    for record in records:
        if isinstance(record, dict):
            record_id = _pick(
                record,
                "id",
                "faqId",
                "faq_id",
                "channelId",
                "channel_id",
                "knowledgeId",
                "knowledge_base_id",
            )
            name = _pick(record, "name", "title")
            if record_id and name:
                lines.append(f"- {record_id}\t{name}")
            elif name:
                lines.append(f"- {name}")
            else:
                lines.append(f"- {format_json(record)}")
        else:
            lines.append(f"- {record}")
    return "\n".join(lines)


def _extract_records(data: dict[str, Any]) -> list[Any]:
    for key in ("items", "records", "data", "list"):
        value = data.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            nested = _extract_records(value)
            if nested:
                return nested
    return []


def _pick(record: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = record.get(key)
        if value is not None:
            return str(value)
    return ""
