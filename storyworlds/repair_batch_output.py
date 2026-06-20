#!/usr/bin/env python3
"""Apply known storyworld batch repairs to a downloaded Batch output JSONL.

The first 1k Batch API run was repaired in materialized files. This script lets
us replay those fixes against the original downloaded JSONL so the repaired
artifact can be materialized again without redoing the same manual pass. It does
not synthesize replacement stories for broken worlds: remaining failures should
stay visible until they receive real repairs.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from openai_batch_world_factory import (
    EMIT_TOOL_NAME,
    ROOT,
    extract_python_source,
    manifest_targets,
    safe_target_path,
)


ENTITY_LOOP_RE = re.compile(r"for (\w+) in world\.entities\.values\(\):")
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rewrite emitted Python in a storyworld Batch output JSONL."
    )
    parser.add_argument("output_jsonl", type=Path, help="original downloaded Batch output JSONL")
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="matching storyworld batch manifest",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="path for the repaired Batch output JSONL",
    )
    parser.add_argument(
        "--overlay-from-worlds",
        action="store_true",
        help="replace each row's source with the current materialized target file when it exists",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report planned changes without writing --out",
    )
    return parser


def add_world_get_placeholder(source: str) -> str:
    pattern = (
        "    def get(self, eid: str) -> Entity:\n"
        "        return self.entities[eid]\n"
    )
    replacement = (
        "    def get(self, eid: str) -> Entity:\n"
        "        if eid not in self.entities:\n"
        "            label = str(eid).replace(\"_\", \" \")\n"
        "            self.entities[eid] = Entity(str(eid), label=label)\n"
        "        return self.entities[eid]\n"
    )
    return source.replace(pattern, replacement)


def snapshot_entity_loops(source: str) -> str:
    return ENTITY_LOOP_RE.sub(r"for \1 in list(world.entities.values()):", source)


def normalize_fired_guards(source: str) -> str:
    names = set(re.findall(r"world\.fired\.add\(\([\"']([^\"']+)[\"'],\)\)", source))
    for name in sorted(names, key=len, reverse=True):
        quoted = re.escape(name)
        source = re.sub(
            rf"([\"']){quoted}\1\s+not\s+in\s+world\.fired",
            f"(\"{name}\",) not in world.fired",
            source,
        )
        source = re.sub(
            rf"([\"']){quoted}\1\s+in\s+world\.fired",
            f"(\"{name}\",) in world.fired",
            source,
        )
    return source


def add_entity_tags(source: str) -> str:
    if "class Entity:" not in source or "tags: set[str]" in source:
        return source
    marker = "    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))\n"
    if marker not in source:
        return source
    return source.replace(marker, marker + "    tags: set[str] = field(default_factory=set)\n", 1)


def add_entity_phrase_property(source: str) -> str:
    if "class Entity:" not in source or "def phrase(self)" in source:
        return source
    marker = "    def __str__(self) -> str:\n        return self.label or self.id\n"
    if marker not in source:
        return source
    addition = marker + (
        "\n"
        "    @property\n"
        "    def phrase(self) -> str:\n"
        "        return getattr(self, \"_phrase\", None) or self.label or self.id.replace(\"_\", \" \")\n"
        "\n"
        "    @phrase.setter\n"
        "    def phrase(self, value: str) -> None:\n"
        "        object.__setattr__(self, \"_phrase\", value)\n"
    )
    return source.replace(marker, addition, 1)


def repair_source(source: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    repaired = source
    for name, fn in (
        ("world_get_placeholder", add_world_get_placeholder),
        ("snapshot_entity_loops", snapshot_entity_loops),
        ("normalize_fired_guards", normalize_fired_guards),
        ("entity_tags", add_entity_tags),
        ("entity_phrase", add_entity_phrase_property),
    ):
        new_source = fn(repaired)
        if new_source != repaired:
            changes.append(name)
            repaired = new_source
    return repaired, changes


def set_source(row: dict[str, Any], source: str, target: str) -> bool:
    body = row.get("response", {}).get("body") or {}
    for item in body.get("output", []):
        if item.get("type") == "custom_tool_call" and item.get("name") == EMIT_TOOL_NAME:
            item["input"] = source.rstrip() + "\n"
            return True

    text_items: list[dict[str, Any]] = []
    for item in body.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                text_items.append(content)
    if not text_items:
        return False
    payload = {"path": target, "content": source.rstrip() + "\n"}
    text_items[0]["text"] = json.dumps(payload, ensure_ascii=False)
    return True


def main() -> int:
    args = build_parser().parse_args()
    targets = manifest_targets(args.manifest)

    counts = {
        "rows": 0,
        "unknown": 0,
        "missing_source": 0,
        "mechanical": 0,
        "overlay": 0,
        "unchanged": 0,
    }
    change_kinds: dict[str, int] = {}
    rows: list[dict[str, Any]] = []

    with args.output_jsonl.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            counts["rows"] += 1
            custom_id = row.get("custom_id", "")
            target = targets.get(custom_id)
            if target is None:
                counts["unknown"] += 1
                rows.append(row)
                continue

            source, source_kind = extract_python_source(row, target)
            if source is None:
                print(f"line {line_number}: skip {custom_id}: {source_kind}")
                counts["missing_source"] += 1
                rows.append(row)
                continue

            original = source
            source, changes = repair_source(source)
            if changes:
                counts["mechanical"] += 1
                for change in changes:
                    change_kinds[change] = change_kinds.get(change, 0) + 1

            if args.overlay_from_worlds:
                try:
                    path = safe_target_path(target)
                except ValueError:
                    path = ROOT / target
                if path.exists():
                    overlay = path.read_text(encoding="utf-8")
                    if overlay.rstrip() != source.rstrip():
                        source = overlay
                        counts["overlay"] += 1

            if source.rstrip() == original.rstrip():
                counts["unchanged"] += 1
            elif not set_source(row, source, target):
                raise SystemExit(f"Could not update source for {custom_id} ({target})")
            rows.append(row)

    print(json.dumps({"counts": counts, "mechanical_changes": change_kinds}, indent=2))
    if args.dry_run:
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
