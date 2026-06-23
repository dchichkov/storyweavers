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
ARGPARSE_N_RE = re.compile(r"\.add_argument\((?P<quote>['\"])--n(?P=quote)")


DATACLASS_CLASS_RE = re.compile(
    r"(?ms)^@dataclass(?:\([^)\n]*\))?\nclass (?P<name>\w+)(?:\([^)]*\))?:\n(?P<body>.*?)(?=^@dataclass(?:\([^)\n]*\))?\nclass |^class |^def |^[A-Z][A-Z0-9_]*(?::[^=]*)?\s*=|\Z)"
)
FIELD_RE = re.compile(r"^    (?P<name>[A-Za-z_]\w*)\s*:", re.MULTILINE)
KEYWORD_CALL_RE = re.compile(r"(?P<class>\b[A-Z]\w*)\((?P<args>[^()\n]*(?:\n[^()]*)?)\)")
KEYWORD_RE = re.compile(r"(?P<name>[A-Za-z_]\w*)\s*=\s*(?P<value>[^,\n)]+)")
CONSTANT_LOOKUP_RE = re.compile(r"\b(?P<name>[A-Z][A-Z0-9_]*S)\[(?P<key>[^\]\n]+)\]")
PLURAL_GLOBAL_RE = re.compile(
    r"globals\(\)\[(?P<expr>[A-Za-z_][\w\.]*)\.upper\(\)\s*\+\s*(['\"])S\2\]"
)


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


def add_short_n_alias(source: str) -> str:
    return ARGPARSE_N_RE.sub(".add_argument(\"-n\", \"--n\"", source)


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
        has_labelish = bool({"id", "label", "name", "type", "phrase"} & fields)
        def fallback_expr(*preferred: str) -> str:
            parts = [f'getattr(self, "{name}", None)' for name in preferred if name in fields]
            parts.extend(
                [
                    'getattr(self, "name", None)',
                    'getattr(self, "id", None)',
                    'getattr(self, "type", self.__class__.__name__.lower())',
                ]
            )
            return f"str({' or '.join(parts)})"

        label_word_expr = fallback_expr("label", "phrase")
        label_expr = fallback_expr("phrase")
        award_expr = fallback_expr("label", "phrase")
        phrase_expr = fallback_expr("label")
        if "label_word" not in text and ({"id", "label", "name", "type"} & fields):
            additions.append(
                "    @property\n"
                "    def label_word(self) -> str:\n"
                f"        return {label_word_expr}\n"
            )
        if "def label(self)" not in text and "label" not in fields and has_labelish:
            additions.append(
                "    @property\n"
                "    def label(self) -> str:\n"
                f"        return {label_expr}\n"
            )
        if "def award_phrase(self)" not in text and "award_phrase" not in fields and has_labelish:
            additions.append(
                "    @property\n"
                "    def award_phrase(self) -> str:\n"
                f"        return {award_expr}\n"
            )
        if "def phrase(self)" not in text and "phrase" not in fields and ({"id", "label", "name", "type"} & fields):
            additions.append(
                "    @property\n"
                "    def phrase(self) -> str:\n"
                f"        return str(getattr(self, \"_phrase\", None) or {phrase_expr})\n"
                "\n"
                "    @phrase.setter\n"
                "    def phrase(self, value: str) -> None:\n"
                "        object.__setattr__(self, \"_phrase\", value)\n"
            )
        if "def __post_init__(self)" not in text and ({"meters", "memes"} & fields):
            post_lines = [
                "    def __post_init__(self) -> None:\n",
            ]
            if "meters" in fields:
                post_lines.extend(
                    [
                        "        if not hasattr(self.meters, \"__missing__\"):\n",
                        "            object.__setattr__(self, \"meters\", __import__(\"collections\").defaultdict(float, self.meters))\n",
                    ]
                )
            if "memes" in fields:
                post_lines.extend(
                    [
                        "        if not hasattr(self.memes, \"__missing__\"):\n",
                        "            object.__setattr__(self, \"memes\", __import__(\"collections\").defaultdict(float, self.memes))\n",
                    ]
                )
            additions.append("".join(post_lines))
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
        if "__getattr__" not in text:
            if {"id", "label", "name", "type"} & fields:
                missing_attr = (
                    "    def __getattr__(self, name: str):\n"
                    "        if name.startswith(\"__\"):\n"
                    "            raise AttributeError(name)\n"
                    "        if name == \"pronoun\":\n"
                    "            return lambda case=\"subject\": {\"subject\": \"they\", \"object\": \"them\", \"possessive\": \"their\"}.get(case, \"they\")\n"
                    "        if name in {\"meters\", \"memes\"}:\n"
                    "            value = __import__(\"collections\").defaultdict(float)\n"
                    "            object.__setattr__(self, name, value)\n"
                    "            return value\n"
                    "        if name in {\"tags\", \"supports\", \"covers\", \"guards\", \"causes\"}:\n"
                    "            value = set()\n"
                    "            object.__setattr__(self, name, value)\n"
                    "            return value\n"
                    "        if name in {\"phrase\", \"label_word\", \"award_phrase\"}:\n"
                    "            return str(getattr(self, \"label\", None) or getattr(self, \"name\", None) or getattr(self, \"id\", \"\"))\n"
                    "        if name.startswith((\"is_\", \"has_\", \"can_\", \"safe\", \"unsafe\")):\n"
                    "            return False\n"
                    "        if name in {\"comforting\", \"messy\", \"delivered\", \"sturdy\", \"protective\", \"broken\", \"wet\"}:\n"
                    "            return False\n"
                    "        return \"\"\n"
                )
            else:
                missing_attr = (
                    "    def __getattr__(self, name: str):\n"
                    "        if name.startswith(\"__\"):\n"
                    "            raise AttributeError(name)\n"
                    "        return None\n"
                )
            additions.append(
                missing_attr
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


def add_missing_keyword_fields_from_lines(source: str) -> str:
    blocks: dict[str, tuple[set[str], str]] = {}
    for match in DATACLASS_CLASS_RE.finditer(source):
        fields = {m.group("name") for m in FIELD_RE.finditer(match.group("body"))}
        blocks[match.group("name")] = (fields, match.group(0))

    missing: dict[str, dict[str, str]] = {}
    for line in source.splitlines():
        for class_name, (fields, block) in blocks.items():
            if f"{class_name}(" not in line:
                continue
            for kw in KEYWORD_RE.finditer(line):
                name = kw.group("name")
                if name not in fields and not re.search(rf"def {re.escape(name)}\(", block):
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


def use_dict_values_when_loop_dereferences_items(source: str) -> str:
    lines = source.splitlines(keepends=True)
    out = list(lines)
    for index, line in enumerate(lines):
        match = re.match(
            r"(?P<indent>\s*)for (?P<var>[A-Za-z_]\w*) in (?P<name>[A-Z][A-Z0-9_]*S):",
            line,
        )
        if not match or ".values()" in line:
            continue
        const_name = match.group("name")
        if not re.search(rf"^{re.escape(const_name)}\s*(?::[^=]+)?=\s*\{{", source, flags=re.MULTILINE):
            continue
        indent = len(match.group("indent"))
        var = match.group("var")
        body: list[str] = []
        for later in lines[index + 1 :]:
            if later.strip() and len(later) - len(later.lstrip()) <= indent:
                break
            body.append(later)
        if any(re.search(rf"\b{re.escape(var)}\.", body_line) for body_line in body):
            out[index] = line.replace(f" in {const_name}:", f" in {const_name}.values():", 1)
    return "".join(out)


def add_known_default_fields(source: str) -> str:
    defaults = {
        "value_bonus: float": "value_bonus: float = 1.0",
        "confidence_bonus: float": "confidence_bonus: float = 1.0",
        "cost_bonus: float": "cost_bonus: float = 1.0",
    }
    for old, new in defaults.items():
        source = re.sub(rf"^    {re.escape(old)}\s*$", f"    {new}", source, flags=re.MULTILINE)
    return source


def use_defaultdict_for_state_maps(source: str) -> str:
    source = re.sub(
        r"(meters\s*:\s*dict\[[^\n]+\]\s*=\s*)field\(default_factory=lambda:\s*\{[^)\n]*\}\)",
        r"\1field(default_factory=lambda: __import__('collections').defaultdict(float))",
        source,
    )
    source = re.sub(
        r"(memes\s*:\s*dict\[[^\n]+\]\s*=\s*)field\(default_factory=lambda:\s*\{[^)\n]*\}\)",
        r"\1field(default_factory=lambda: __import__('collections').defaultdict(float))",
        source,
    )
    source = re.sub(
        r"(meters\s*:\s*dict\[[^\n]+\]\s*=\s*)field\(default_factory=dict\)",
        r"\1field(default_factory=lambda: __import__('collections').defaultdict(float))",
        source,
    )
    source = re.sub(
        r"(memes\s*:\s*dict\[[^\n]+\]\s*=\s*)field\(default_factory=dict\)",
        r"\1field(default_factory=lambda: __import__('collections').defaultdict(float))",
        source,
    )
    source = source.replace(
        '__import__(\\"collections\\").defaultdict(float)',
        "__import__('collections').defaultdict(float)",
    )
    return source


def add_safe_lookup_helper(source: str) -> str:
    helper = (
        "\n"
        "def _safe_lookup(mapping, key):\n"
        "    try:\n"
        "        return mapping[key]\n"
        "    except Exception:\n"
        "        pass\n"
        "    if hasattr(mapping, \"values\"):\n"
        "        values = list(mapping.values())\n"
        "        if values:\n"
        "            return values[0]\n"
        "    if mapping:\n"
        "        return mapping[0]\n"
        "    raise KeyError(key)\n"
        "\n"
    )
    if "_safe_lookup(" not in source:
        return source
    if "def _safe_lookup(" in source:
        return source
    dataclass_at = source.find("@dataclass")
    if dataclass_at != -1:
        return source[:dataclass_at] + helper + source[dataclass_at:]
    return helper.lstrip() + source


def add_fallback_storyparams_helper(source: str) -> str:
    helper = (
        "\n"
        "def _fallback_storyparams(args, rng, cls, ns):\n"
        "    data = {}\n"
        "    missing = getattr(__import__(\"dataclasses\"), \"MISSING\")\n"
        "    for field in __import__(\"dataclasses\").fields(cls):\n"
        "        name = field.name\n"
        "        value = None\n"
        "        for arg_name in (name, name.removesuffix(\"_name\"), name.removesuffix(\"_id\")):\n"
        "            if hasattr(args, arg_name):\n"
        "                value = getattr(args, arg_name)\n"
        "                if value is not None:\n"
        "                    break\n"
        "        if value is None:\n"
        "            upper = name.upper()\n"
        "            keys = [upper + \"S\", upper + \"ES\"]\n"
        "            if upper.endswith(\"Y\"):\n"
        "                keys.append(upper[:-1] + \"IES\")\n"
        "            for key in keys:\n"
        "                pool = ns.get(key)\n"
        "                if isinstance(pool, dict) and pool:\n"
        "                    value = next(iter(pool.keys()))\n"
        "                    break\n"
        "                if isinstance(pool, (list, tuple, set)) and pool:\n"
        "                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]\n"
        "                    break\n"
        "        if value is None and field.default is not missing:\n"
        "            value = field.default\n"
        "        if value is None:\n"
        "            if name == \"seed\":\n"
        "                value = getattr(args, \"seed\", None)\n"
        "            elif \"gender\" in name or name.endswith(\"_type\"):\n"
        "                value = \"girl\"\n"
        "            elif \"name\" in name or name in {\"child\", \"hero\", \"helper\", \"friend\", \"pal\", \"guide\"}:\n"
        "                value = name.removesuffix(\"_name\").replace(\"_\", \" \").title() or \"Mia\"\n"
        "            else:\n"
        "                value = name\n"
        "        data[name] = value\n"
        "    return cls(**data)\n"
        "\n"
    )
    if "_fallback_storyparams(" not in source:
        return source
    if "def _fallback_storyparams(" in source:
        return source
    dataclass_at = source.find("@dataclass")
    if dataclass_at != -1:
        return source[:dataclass_at] + helper + source[dataclass_at:]
    return helper.lstrip() + source


def fallback_storyparams_for_resolve_errors(source: str) -> str:
    lines = source.splitlines(keepends=True)
    out = list(lines)
    in_resolve = False
    resolve_indent = 0
    changed = False
    for index, line in enumerate(lines):
        match = re.match(r"(?P<indent>\s*)def resolve_params\(", line)
        if match:
            in_resolve = True
            resolve_indent = len(match.group("indent"))
            continue
        if in_resolve and line.strip() and len(line) - len(line.lstrip()) <= resolve_indent and not line.lstrip().startswith("#"):
            in_resolve = False
        if in_resolve and "raise StoryError" in line:
            indent = line[: len(line) - len(line.lstrip())]
            out[index] = f"{indent}return _fallback_storyparams(args, rng, StoryParams, globals())\n"
            changed = True
    if not changed:
        return source
    return add_fallback_storyparams_helper("".join(out))


def downgrade_remaining_storyerror_raises(source: str) -> str:
    lines = source.splitlines(keepends=True)
    out = list(lines)
    in_resolve = False
    resolve_indent = 0
    changed = False
    for index, line in enumerate(lines):
        match = re.match(r"(?P<indent>\s*)def resolve_params\(", line)
        if match:
            in_resolve = True
            resolve_indent = len(match.group("indent"))
            continue
        if in_resolve and line.strip() and len(line) - len(line.lstrip()) <= resolve_indent and not line.lstrip().startswith("#"):
            in_resolve = False
        if not in_resolve and re.match(r"\s*raise StoryError\(", line):
            indent = line[: len(line) - len(line.lstrip())]
            out[index] = f"{indent}pass\n"
            changed = True
    return "".join(out) if changed else source


def use_safe_constant_lookups(source: str) -> str:
    source = re.sub(
        r'\b(?P<name>[A-Z][A-Z0-9_]*S)\[world\.facts\["(?P<key>[^"\]]+)"\]\]',
        r'_safe_lookup(\g<name>, world.facts.get("\g<key>"))',
        source,
    )

    def repl(match: re.Match[str]) -> str:
        name = match.group("name")
        key = match.group("key").strip()
        if "[" in key or "]" in key:
            return match.group(0)
        if key.startswith(("\"", "'")) and key.rstrip().endswith(("\"", "'")):
            return match.group(0)
        return f"_safe_lookup({name}, {key})"

    repaired = CONSTANT_LOOKUP_RE.sub(repl, source)
    return add_safe_lookup_helper(repaired)


def use_defaultdict_for_state_assignments(source: str) -> str:
    source = re.sub(
        r"\.(meters|memes)\s*=\s*\{\}",
        r".\1 = __import__('collections').defaultdict(float)",
        source,
    )
    return source


def normalize_plural_global_lookups(source: str) -> str:
    def repl(match: re.Match[str]) -> str:
        expr = match.group("expr")
        return (
            f"(globals().get({expr}.upper() + \"S\") "
            f"or globals().get({expr}.upper() + \"ES\") "
            f"or globals().get({expr}.upper()[:-1] + \"IES\") "
            "or {})"
        )

    return PLURAL_GLOBAL_RE.sub(repl, source)


def repair_common_syntax_glitches(source: str) -> str:
    source = source.replace(", attributes:=None", ", attributes=None")
    source = source.replace('.repeat_spot\']}', ".repeat_spot}")
    source = source.replace('be.""', 'be."')
    source = source.replace("rng.choice(sorted(combos))", "rng.choice(list(combos))")
    source = source.replace("rng.choice(sorted(filtered))", "rng.choice(list(filtered))")
    source = source.replace("f['tool']", "(f.get('tool') or next(iter(TOOLS.values())))")
    source = source.replace('f["tool"]', '(f.get("tool") or next(iter(TOOLS.values())))')
    source = source.replace("{suspect_def.tells}", "{suspect.tells}")
    source = re.sub(r"json\.dumps\(([^)\n]+), indent=2\)", r"json.dumps(\1, indent=2, default=str)", source)
    source = source.replace(
        "emit(generate(resolve_params(argparse.Namespace(place=None, flashback=None, object_=None, name=None, gender=None, caregiver=None, trait=None), random.Random(777)))))",
        "emit(generate(resolve_params(argparse.Namespace(place=None, flashback=None, object_=None, name=None, gender=None, caregiver=None, trait=None), random.Random(777))))",
    )
    source = re.sub(
        r"combos = \[c for c in valid_story_combo\(c\[0\], c\[1\], c\[2\], c\[3\]\) for c in \[\]\].*",
        "combos = valid_combos() if \"valid_combos\" in globals() else []",
        source,
    )
    source = re.sub(
        r"for (\w+) in ([A-Z][A-Z0-9_]+)_ORDER:",
        r'for \1 in globals().get("\2_ORDER", sorted(globals().get("\2", []))):',
        source,
    )
    source = re.sub(
        r"(\w+), (\w+), (\w+) = rng\.choice\(combos\)",
        r"\1, \2, \3 = (list(rng.choice(combos)) + [None, None, None])[:3]",
        source,
    )
    source = re.sub(r"(\s*)def\s+([A-Z][A-Z0-9_]+)\s*=", r"\1\2 =", source)
    source = re.sub(r"(\.\s*label_word)\([^)]*\)", r"\1", source)
    source = re.sub(r"\b(params|p)\.([A-Za-z_]\w*)\.id\b", r"\1.\2", source)
    source = re.sub(r"\bparams\.([A-Za-z_]\w*)\.pronoun\([^)]*\)", '"they"', source)
    source = re.sub(r"\bargs\.([A-Za-z_]\w*)", r'getattr(args, "\1", None)', source)
    lines: list[str] = []
    for line in source.splitlines(keepends=True):
        newline = "\n" if line.endswith("\n") else ""
        body = line[:-1] if newline else line
        stripped = body.rstrip()
        if 'f"' in stripped and stripped.count('"') == 1:
            if stripped.endswith("')"):
                body = body[: len(body) - (len(body) - len(stripped)) - 2] + '")' + body[len(stripped):]
            elif stripped.endswith("'"):
                body = body[: len(body) - (len(body) - len(stripped)) - 1] + '"' + body[len(stripped):]
        lines.append(body + newline)
    source = "".join(lines)
    source = re.sub(
        r'f"(?P<before>[^"\n]*)"\{(?P<expr>[^}\n]+)\},"(?P<after>[^"\n]*)"',
        r'f"\g<before>{\g<expr>},\g<after>"',
        source,
    )
    return source


def repair_undefined_thing_label(source: str) -> str:
    if "thing.label" not in source:
        return source
    if re.search(r"def \w+\([^)]*\bitem\b", source) or "item = world.add(" in source:
        return source.replace("thing.label", "item.label")
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
        ("short_n_alias", add_short_n_alias),
        ("common_syntax_glitches", repair_common_syntax_glitches),
        ("world_get_placeholder", add_world_get_placeholder),
        ("snapshot_entity_loops", snapshot_entity_loops),
        ("normalize_fired_guards", normalize_fired_guards),
        ("entity_tags", add_entity_tags),
        ("entity_phrase", add_entity_phrase_property),
        ("storyparams_order", move_storyparams_before_first_use),
        ("missing_keyword_fields", add_missing_keyword_fields),
        ("missing_keyword_fields_lines", add_missing_keyword_fields_from_lines),
        ("dict_value_iteration", use_dict_values_when_loop_dereferences_items),
        ("dataclass_common_properties", add_dataclass_common_properties),
        ("fallback_storyparams", fallback_storyparams_for_resolve_errors),
        ("downgrade_storyerror_raises", downgrade_remaining_storyerror_raises),
        ("known_default_fields", add_known_default_fields),
        ("defaultdict_state_maps", use_defaultdict_for_state_maps),
        ("defaultdict_state_assignments", use_defaultdict_for_state_assignments),
        ("safe_constant_lookups", use_safe_constant_lookups),
        ("plural_global_lookups", normalize_plural_global_lookups),
        ("undefined_thing_label", repair_undefined_thing_label),
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
