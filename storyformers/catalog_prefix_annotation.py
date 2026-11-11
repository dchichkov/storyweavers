"""Sparse catalog annotation for one causal last word, with local references."""

from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
import re

from .annotation import MODEL, POS, compact, fingerprint, story_tokens
from .neuron_spec import TYPES, check_value
from .positions import add_positions
from .prefix_annotation import prefix_request as legacy_request, prefix_blocks


ROOT = Path(__file__).resolve().parent
REVIEWED = ROOT / "runs/catalog_annotation_20261107/prompts"
PROMPT = ROOT / "prompts/annotate_prefix_catalog_v2.txt"
EXAMPLES = ROOT / "data/prefix_catalog_examples_v2.json"
VERSION = "storyformers-prefix-catalog-v2"
META = {"_references", "_evidence", "_feedback", "_new_attributes"}
TABLES = {"e": "entities", "ev": "events", "p": "propositions", "s": "scopes", "q": "scopes"}
ID = re.compile(r"(ev|e|p|s|q)([1-9]\d*)(?:_([a-z][a-z0-9_]*))?")
STATUSES = {"asserted", "attributed_claim", "candidate"}


@lru_cache(maxsize=1)
def registry():
    result = {r["key"]: r for r in map(json.loads, (ROOT / "catalog/attributes.jsonl").read_text().splitlines())}
    for row in json.loads((REVIEWED / "catalog_overrides.json").read_text()):
        result[row["key"]].update(row)
    for row in json.loads((REVIEWED / "extension_registry_v4.json").read_text()):
        result[row["key"]] = row
    return result


def validate_record(text, row, *, definitions=None):
    spans = story_tokens(text)
    if not spans or spans[-1]["kind"] != "word" or not isinstance(row, dict):
        raise ValueError("expected one JSON object for a word-ended prefix")
    target = spans[-1]
    if type(row.get("index")) is not int or row["index"] != target["index"] or row.get("token") != target["token"]:
        raise ValueError("last-word index/token differs from supplied prefix")
    if row.get("pos") not in POS or not isinstance(row.get("lemma"), str) or not row["lemma"].strip():
        raise ValueError("every word needs contextual POS and a nonempty lemma")
    if not isinstance(row.get("scope_id"), str):
        raise ValueError("every word needs a scope_id, normally s0")
    definitions = dict(registry() if definitions is None else definitions)
    extensions = row.get("_new_attributes", [])
    if not isinstance(extensions, list):
        raise ValueError("_new_attributes must be a list")
    for definition in extensions:
        if (not isinstance(definition, dict) or
                not {"key", "type", "description", "scope", "reason", "example_value"} <= definition.keys() or
                not isinstance(definition["key"], str) or not re.fullmatch(r"[a-z][a-z0-9_]*", definition["key"]) or
                definition["key"] in definitions or definition["type"] not in TYPES):
            raise ValueError("new fields need a distinct name and complete typed definition")
        check_value(definition["example_value"], definition)
        definitions[definition["key"]] = definition
    for key, value in row.items():
        if key in META or key in {"index", "token"}:
            continue
        if key not in definitions:
            raise ValueError(f"unregistered feature: {key}")
        check_value(value, definitions[key])
        if value is not None and "values" in definitions[key] and value not in definitions[key]["values"]:
            raise ValueError(f"unsupported value for {key}")

    references = row.get("_references", {})
    if not isinstance(references, dict) or references.keys() - set(TABLES.values()):
        raise ValueError("_references contains unknown tables")

    def anchored(identifier):
        match = ID.fullmatch(identifier) if isinstance(identifier, str) else None
        if not match:
            raise ValueError(f"invalid reference ID: {identifier}")
        kind, number, suffix = match.groups()
        at = int(number) - 1
        if (not 0 <= at < len(spans) or (kind != "q" and spans[at]["kind"] != "word")
                or (kind == "e" and suffix)):
            raise ValueError(f"reference must be anchored in the available prefix: {identifier}")
        return TABLES[kind]

    for table, entries in references.items():
        if not isinstance(entries, dict):
            raise ValueError("reference tables must be JSON objects")
        for identifier, entry in entries.items():
            if identifier == "s0" and table == "scopes":
                continue
            if anchored(identifier) != table or not isinstance(entry, dict):
                raise ValueError("reference is in the wrong table or has no record")
    if row["scope_id"] != "s0" and (anchored(row["scope_id"]) != "scopes" or
                                     row["scope_id"] not in references.get("scopes", {})):
        raise ValueError("current scope needs a registered prefix-local scope")
    nonspace = [span for span in spans if span["kind"] != "space"]

    def visit(value):
        if isinstance(value, str):
            if ID.fullmatch(value):
                table = anchored(value)
                if value not in references.get(table, {}):
                    raise ValueError(f"missing local reference: {value}")
            elif re.fullmatch(r"t[1-9]\d*", value) and int(value[1:]) > len(nonspace):
                raise ValueError("token anchor points beyond the prefix")
        elif isinstance(value, dict):
            if "assertion_status" in value and value["assertion_status"] not in STATUSES:
                raise ValueError("invalid nested assertion_status")
            for key in ("event_type", "factuality"):
                if key in value and value[key] is not None and value[key] not in definitions[key]["values"]:
                    raise ValueError(f"unsupported nested value for {key}")
            for key, child in value.items():
                visit(key)
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit({k: v for k, v in row.items() if k not in {"_new_attributes", "_feedback"}})
    for field in ("patients", "instruments"):
        if field in row and (not isinstance(row[field], list) or
                            any(not isinstance(v, str) or not re.fullmatch(r"e[1-9]\d*", v) for v in row[field])):
            raise ValueError(f"{field} must be entity ID arrays")
    for field in ("_evidence", "_feedback"):
        if field in row and not isinstance(row[field], list):
            raise ValueError(f"{field} must be a list")
    for evidence in row.get("_evidence", []):
        if (not isinstance(evidence, dict) or not isinstance(evidence.get("note"), str) or
                not isinstance(evidence.get("indices"), list) or
                any(type(i) is not int or not 0 <= i < len(spans) for i in evidence["indices"])):
            raise ValueError("evidence needs a note and prefix-local span indices")
    for field in ("entity_id", "actor_id", "recipient_id"):
        if row.get(field) is not None and row[field] not in references.get("entities", {}):
            raise ValueError(f"unregistered {field}")
    if row.get("entity_id"):
        entity = references["entities"][row["entity_id"]]
        if row.get("entity_name") != entity.get("name") or row.get("entity") != entity.get("type"):
            raise ValueError("entity feature and reference record disagree")
    if row.get("event_id"):
        if row["event_id"] not in references.get("events", {}):
            raise ValueError("unregistered event_id")
        event = references["events"][row["event_id"]]
        if row.get("event") != event.get("event"):
            raise ValueError("event feature and reference record disagree")
        if row.get("role") == "action" and not row["event_id"].startswith(f"ev{target['index'] + 1}_") and row["event_id"] != f"ev{target['index'] + 1}":
            raise ValueError("action event must be anchored to the current trigger")
    # Require finite JSON for all metadata as well as catalog fields.
    json.dumps(row, allow_nan=False)
    return deepcopy(row)


def shared_prefix(prompt_file=PROMPT, examples_file=EXAMPLES, *, validator=None, definitions=None, extra_definitions=None):
    validator = validate_record if validator is None else validator
    definitions = registry() if definitions is None else definitions
    examples = json.loads(Path(examples_file).read_text())
    if not isinstance(examples, list) or len(examples) < 3:
        raise ValueError("provide at least three causal catalog examples")
    parts = [Path(prompt_file).read_text().strip(), "\nFULL 1,024-FIELD CATALOG (sparse use; examples are definitions, not story facts)"]
    for name in ("core", "linguistic", "world", "mind"):
        parts.append((REVIEWED / f"features_{name}.txt").read_text())
    parts += ["ALLOWED ENUM VALUES (apply inside reference tables too)\n" + compact({
                  key: definition["values"] for key, definition in definitions.items() if "values" in definition}),
              "CATALOG CORRECTIONS\n" + (REVIEWED / "catalog_overrides.json").read_text(),
              "AGREED EXTENSIONS\n" + (REVIEWED / "extension_registry_v4.json").read_text()]
    if extra_definitions:
        parts.append("RECONCILED PREFIX EXTENSIONS\n" + json.dumps(extra_definitions, ensure_ascii=False))
    for i, example in enumerate(examples, 1):
        validator(example["prefix"], example["response"])
        parts += [f"CAUSAL EXAMPLE {i} PREFIX SPANS\n" + "".join(b["text"] for b in prefix_blocks(example["prefix"])),
                  "LAST-WORD JSON\n" + compact(example["response"])]
    return "\n".join(parts) + "\nUse only the following supplied prefix. Return its last-word JSON record.\n"


def prefix_request(story, index, *, prefix=None, reasoning="low", max_output_tokens=4096):
    prefix = shared_prefix() if prefix is None else prefix
    body = legacy_request(story, index, prefix=prefix, reasoning=reasoning, max_output_tokens=max_output_tokens)
    # JSON mode permits genuinely sparse typed dictionaries. Local validation
    # enforces the catalog, instead of requiring 1,024 fields per response.
    body["text"] = {"format": {"type": "json_object"}}
    body["prompt_cache_key"] = VERSION + ":" + fingerprint([prefix, MODEL, body["reasoning"], body["text"]])[:24]
    return body


def assemble(story, records, *, validator=None):
    validator = validate_record if validator is None else validator
    spans, by_index = story_tokens(story), {}
    for row in records:
        index = row.get("index")
        if type(index) is not int or not 0 <= index < len(spans) or index in by_index:
            raise ValueError("duplicate or invalid annotation index")
        checked = validator(story[:spans[index]["end"]], row)
        by_index[index] = {k: v for k, v in checked.items() if k not in META}
    if set(by_index) != {span["index"] for span in spans if span["kind"] == "word"}:
        raise ValueError("missing last-word annotation")
    # Reference snapshots stay with each prefix. Never merge later knowledge
    # into an earlier word or rewrite an earlier table's state.
    return add_positions([{**by_index.get(span["index"], {"pos": span["kind"]}), **span} for span in spans])
