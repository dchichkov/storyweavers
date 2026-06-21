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


DATACLASS_CLASS_RE = re.compile(
    r"(?ms)^@dataclass(?:\([^)\n]*\))?\nclass (?P<name>\w+)(?:\([^)]*\))?:\n(?P<body>.*?)(?=^@dataclass(?:\([^)\n]*\))?\nclass |^class |^def |^[A-Z][A-Z0-9_]*(?::[^=]*)?\s*=|\Z)"
)
FIELD_RE = re.compile(r"^    (?P<name>[A-Za-z_]\w*)\s*:", re.MULTILINE)
KEYWORD_CALL_RE = re.compile(r"(?P<class>\b[A-Z]\w*)\((?P<args>[^()\n]*(?:\n[^()]*)?)\)")
KEYWORD_RE = re.compile(r"(?P<name>[A-Za-z_]\w*)\s*=\s*(?P<value>[^,\n)]+)")


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


def _top_level_block_bounds(source: str, class_name: str) -> tuple[int, int] | None:
    lines = source.splitlines(keepends=True)
    class_line = None
    for i, line in enumerate(lines):
        if line.startswith(f"class {class_name}") or line.startswith(f"class {class_name}("):
            class_line = i
            break
    if class_line is None:
        return None

    start = class_line
    if start > 0 and lines[start - 1].strip() == "@dataclass":
        start -= 1

    end = len(lines)
    for j in range(class_line + 1, len(lines)):
        line = lines[j]
        if not line.strip():
            continue
        if not line.startswith((" ", "\t")) and (
            line.startswith("@dataclass")
            or line.startswith("class ")
            or line.startswith("def ")
            or re.match(r"[A-Z][A-Z0-9_]+\s*=", line)
        ):
            end = j
            break
    return sum(len(x) for x in lines[:start]), sum(len(x) for x in lines[:end])


def move_storyparams_before_first_use(source: str) -> str:
    bounds = _top_level_block_bounds(source, "StoryParams")
    if bounds is None:
        return source
    start, end = bounds
    first_use = source.find("StoryParams(")
    if first_use == -1 or first_use > start:
        return source
    block = source[start:end].rstrip() + "\n\n"
    remaining = source[:start] + source[end:]
    insert_at = remaining.find("StoryParams(")
    if insert_at == -1:
        return source
    lines = remaining.splitlines(keepends=True)
    pos = 0
    line_index = 0
    for i, line in enumerate(lines):
        next_pos = pos + len(line)
        if next_pos > insert_at:
            line_index = i
            break
        pos = next_pos
    while line_index > 0 and (lines[line_index].startswith((" ", "\t")) or not lines[line_index].strip()):
        line_index -= 1
    line_start = sum(len(line) for line in lines[:line_index])
    return remaining[:line_start] + block + remaining[line_start:]


def add_dataclass_common_properties(source: str) -> str:
    def repl(match: re.Match[str]) -> str:
        text = match.group(0)
        body = match.group("body")
        additions: list[str] = []
        fields = {m.group("name") for m in FIELD_RE.finditer(body)}
        if "label_word" not in text and ({"id", "label", "name", "type"} & fields):
            additions.append(
                "    @property\n"
                "    def label_word(self) -> str:\n"
                "        return str(getattr(self, \"label\", None) or getattr(self, \"name\", None) or getattr(self, \"id\", None) or getattr(self, \"type\", self.__class__.__name__.lower()))\n"
            )
        if "def phrase(self)" not in text and "phrase" not in fields and ({"id", "label", "name", "type"} & fields):
            additions.append(
                "    @property\n"
                "    def phrase(self) -> str:\n"
                "        return str(getattr(self, \"_phrase\", None) or getattr(self, \"label_word\", None) or getattr(self, \"label\", None) or getattr(self, \"id\", self.__class__.__name__.lower()))\n"
                "\n"
                "    @phrase.setter\n"
                "    def phrase(self, value: str) -> None:\n"
                "        object.__setattr__(self, \"_phrase\", value)\n"
            )
        if "meters" not in fields and "def meters(self)" not in text:
            additions.append(
                "    @property\n"
                "    def meters(self):\n"
                "        if not hasattr(self, \"_meters\"):\n"
                "            object.__setattr__(self, \"_meters\", __import__(\"collections\").defaultdict(float))\n"
                "        return self._meters\n"
            )
        if "memes" not in fields and "def memes(self)" not in text:
            additions.append(
                "    @property\n"
                "    def memes(self):\n"
                "        if not hasattr(self, \"_memes\"):\n"
                "            object.__setattr__(self, \"_memes\", __import__(\"collections\").defaultdict(float))\n"
                "        return self._memes\n"
            )
        if "tags" not in fields and "def tags(self)" not in text:
            additions.append(
                "    @property\n"
                "    def tags(self):\n"
                "        if not hasattr(self, \"_tags\"):\n"
                "            object.__setattr__(self, \"_tags\", set())\n"
                "        return self._tags\n"
            )
        if not additions:
            return text
        return text.rstrip() + "\n" + "\n".join(additions) + "\n\n"

    return DATACLASS_CLASS_RE.sub(repl, source)


def _field_line(name: str, value: str) -> str:
    stripped = value.strip()
    if stripped in {"True", "False"} or name.startswith(("can_", "is_", "has_", "safe", "unsafe")):
        return f"    {name}: bool = False\n"
    if stripped.startswith("{"):
        return f"    {name}: set[str] = field(default_factory=set)\n"
    if stripped.startswith("["):
        return f"    {name}: list = field(default_factory=list)\n"
    if re.fullmatch(r"-?\d+", stripped):
        return f"    {name}: int = 0\n"
    if re.fullmatch(r"-?\d+(?:\.\d+)?", stripped):
        return f"    {name}: float = 0.0\n"
    if stripped.startswith(("\"", "'")):
        return f"    {name}: str = \"\"\n"
    return f"    {name}: object | None = None\n"


def add_missing_keyword_fields(source: str) -> str:
    blocks: dict[str, tuple[int, int, set[str], str]] = {}
    for match in DATACLASS_CLASS_RE.finditer(source):
        fields = {m.group("name") for m in FIELD_RE.finditer(match.group("body"))}
        blocks[match.group("name")] = (match.start(), match.end(), fields, match.group(0))

    missing: dict[str, dict[str, str]] = {}
    for call in KEYWORD_CALL_RE.finditer(source):
        class_name = call.group("class")
        if class_name not in blocks:
            continue
        _start, _end, fields, _block = blocks[class_name]
        for kw in KEYWORD_RE.finditer(call.group("args")):
            name = kw.group("name")
            if name not in fields and not re.search(rf"def {re.escape(name)}\(", _block):
                missing.setdefault(class_name, {})[name] = kw.group("value")

    if not missing:
        return source

    def repl(match: re.Match[str]) -> str:
        class_name = match.group("name")
        if class_name not in missing:
            return match.group(0)
        text = match.group(0)
        lines = "".join(_field_line(name, value) for name, value in sorted(missing[class_name].items()))
        body_start = text.find(match.group("body"))
        body = match.group("body")
        method_match = re.search(r"^    (?:@|def )", body, flags=re.MULTILINE)
        if method_match:
            insert_at = body_start + method_match.start()
            return text[:insert_at] + lines + text[insert_at:]
        return text.rstrip() + "\n" + lines + "\n"

    return DATACLASS_CLASS_RE.sub(repl, source)


def add_known_default_fields(source: str) -> str:
    defaults = {
        "value_bonus: float": "value_bonus: float = 1.0",
        "confidence_bonus: float": "confidence_bonus: float = 1.0",
        "cost_bonus: float": "cost_bonus: float = 1.0",
    }
    for old, new in defaults.items():
        source = re.sub(rf"^    {re.escape(old)}\s*$", f"    {new}", source, flags=re.MULTILINE)
    return source


def bound_propagate_loops(source: str) -> str:
    return source.replace(
        "    changed = True\n    while changed:\n",
        "    changed = True\n    for _ in range(len(globals().get(\"CAUSAL_RULES\", [])) + 4):\n",
    )


def repair_source(source: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    repaired = source
    for name, fn in (
        ("world_get_placeholder", add_world_get_placeholder),
        ("snapshot_entity_loops", snapshot_entity_loops),
        ("normalize_fired_guards", normalize_fired_guards),
        ("entity_tags", add_entity_tags),
        ("entity_phrase", add_entity_phrase_property),
        ("storyparams_order", move_storyparams_before_first_use),
        ("missing_keyword_fields", add_missing_keyword_fields),
        ("dataclass_common_properties", add_dataclass_common_properties),
        ("known_default_fields", add_known_default_fields),
        ("bound_propagate_loops", bound_propagate_loops),
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
