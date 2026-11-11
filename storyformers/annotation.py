"""Lossless token scaffolding, shared few-shot prompt, and annotation contracts.

These are full-story offline teacher labels, not causal runtime features.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

from .latents import TOKEN_PATTERN


ROOT = Path(__file__).resolve().parent
PROMPT = ROOT / "prompts" / "annotate_v2.txt"
EXAMPLES = ROOT / "data" / "annotation_examples.json"
MODEL = "gpt-6-luna"
VERSION = "storyformers-annotation-v2"
POS = ["n", "v", "adj", "adv", "pron", "det", "adp", "conj", "num", "part", "intj", "unknown"]
EVENT_TYPES = ["obtain", "transfer", "repair", "move", "perceive", "speak", "feel", "state", "other"]
ROLES = ["actor", "action", "patient", "instrument", "recipient", "location", "modifier", "other"]
FACTUALITY = ["asserted", "negated", "desired", "hypothetical", "reported"]
NULL_FIELDS = ["lemma", "entity", "entity_id", "entity_name", "event", "event_id", "event_type",
               "actor", "actor_id", "recipient_id", "role", "factuality", "location"]
LIST_FIELDS = ["patients", "instruments", "attributes"]
FIELDS = {"index", "token", "pos", *NULL_FIELDS, *LIST_FIELDS}
SPAN_PATTERN = re.compile(TOKEN_PATTERN.pattern + r"|\s+|.", re.UNICODE)


def compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value):
    return hashlib.sha256(compact(value).encode()).hexdigest()


def story_tokens(story: str) -> list[dict]:
    """Unicode character offsets, preserving every character including whitespace."""
    rows = []
    for index, match in enumerate(SPAN_PATTERN.finditer(story)):
        token = match.group()
        kind = "space" if token.isspace() else "word" if any(c.isalnum() for c in token) else "punct"
        rows.append(dict(index=index, token=token, start=match.start(), end=match.end(), kind=kind))
    assert "".join(row["token"] for row in rows) == story
    return rows


def empty_annotation(index: int, token: str, **labels) -> dict:
    """Convenience for authored examples; live responses must supply every field."""
    return dict(index=index, token=token, **{
        **dict.fromkeys(NULL_FIELDS), **{field: [] for field in LIST_FIELDS},
        "pos": "unknown", **labels,
    })


def object_schema(properties):
    return dict(type="object", properties=properties, required=list(properties), additionalProperties=False)


def annotation_schema():
    nullable = {"type": ["string", "null"]}
    properties = {"index": {"type": "integer"}, "token": {"type": "string"},
                  **{field: deepcopy(nullable) for field in NULL_FIELDS}}
    properties.update({"pos": {"type": "string", "enum": POS},
                       "event_type": {"enum": [*EVENT_TYPES, None]},
                       "role": {"enum": [*ROLES, None]},
                       "factuality": {"enum": [*FACTUALITY, None]},
                       "patients": {"type": "array", "items": {"type": "string"}},
                       "instruments": {"type": "array", "items": {"type": "string"}},
                       "attributes": {"type": "array", "items": object_schema({
                           "name": {"type": "string"}, "value": {"type": "string"}})}})
    # Explicit types keep this valid both as JSON Schema and for Structured Outputs.
    for field in ("event_type", "role", "factuality"):
        properties[field]["type"] = ["string", "null"]
    return object_schema({"annotations": {"type": "array", "items": object_schema(properties)}})


def story_payload(story: str):
    return {"story": story, "words": [row for row in story_tokens(story) if row["kind"] == "word"]}


def validate_annotations(story: str, payload: dict) -> list[dict]:
    """Reject omissions/rewrites, broken IDs and malformed labels; add exact gaps."""
    if not isinstance(payload, dict) or set(payload) != {"annotations"} or not isinstance(payload["annotations"], list):
        raise ValueError("expected an object containing only an annotations list")
    spans = story_tokens(story)
    words = [row for row in spans if row["kind"] == "word"]
    annotations = payload["annotations"]
    if len(annotations) != len(words):
        raise ValueError(f"expected {len(words)} word annotations, received {len(annotations)}")
    entities, events = {}, {}
    for word, row in zip(words, annotations):
        if not isinstance(row, dict) or set(row) != FIELDS:
            raise ValueError("annotation fields do not match the versioned schema")
        if type(row["index"]) is not int or row["index"] != word["index"] or row["token"] != word["token"]:
            raise ValueError(f"token changed, missing, duplicated or reordered at index {word['index']}")
        if row["pos"] not in POS:
            raise ValueError("unknown POS label")
        for field in NULL_FIELDS:
            value = row[field]
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{field} must be a nonempty string or null")
        for field, choices in (("event_type", EVENT_TYPES), ("role", ROLES), ("factuality", FACTUALITY)):
            if row[field] is not None and row[field] not in choices:
                raise ValueError(f"unknown {field}")
        for field in LIST_FIELDS:
            if not isinstance(row[field], list):
                raise ValueError(f"{field} must be a list")
        for field in ("patients", "instruments"):
            if any(not isinstance(x, str) for x in row[field]) or len(set(row[field])) != len(row[field]):
                raise ValueError(f"{field} must contain unique entity IDs")
        attribute_names = []
        for attribute in row["attributes"]:
            if (not isinstance(attribute, dict) or set(attribute) != {"name", "value"}
                    or any(not isinstance(v, str) or not v.strip() for v in attribute.values())):
                raise ValueError("attributes require nonempty name/value strings")
            attribute_names.append(attribute["name"])
        if len(set(attribute_names)) != len(attribute_names):
            raise ValueError("duplicate attribute name")
        entity_values = [row[field] for field in ("entity_id", "entity", "entity_name")]
        if any(v is not None for v in entity_values):
            if any(v is None for v in entity_values) or not re.fullmatch(r"e[1-9]\d*", row["entity_id"]):
                raise ValueError("entity mentions need eN ID, type and canonical name")
            identity = (row["entity"], row["entity_name"])
            if row["entity_id"] in entities and entities[row["entity_id"]] != identity:
                raise ValueError("entity type/name drift within a story")
            entities[row["entity_id"]] = identity
        if row["event_id"] is not None and not re.fullmatch(r"ev[1-9]\d*", row["event_id"]):
            raise ValueError("event IDs must have form evN")
        if row["role"] == "action":
            if row["event"] is None:
                raise ValueError("action roles require an event label")
            if any(row[field] is None for field in ("event_id", "event_type", "factuality")):
                raise ValueError("event triggers require ID, type and factuality")
            if row["event_id"] in events:
                raise ValueError("each event must have exactly one action trigger")
            events[row["event_id"]] = row["event"]
        elif any(row[field] is not None for field in ("event_type", "factuality", "actor", "actor_id", "recipient_id")) or row["patients"] or row["instruments"]:
            raise ValueError("event arguments require an event trigger")
        if (row["event"] is None) != (row["event_id"] is None):
            raise ValueError("event labels and IDs must both be set or both be null")
        if (row["actor"] is None) != (row["actor_id"] is None):
            raise ValueError("actor and actor_id must both be set or both be null")
    for row in annotations:
        references = [row["actor_id"], row["recipient_id"], *row["patients"], *row["instruments"]]
        if any(ref not in entities for ref in references if ref is not None):
            raise ValueError("event references an entity with no token mention")
        if row["actor_id"] is not None and row["actor"] != entities[row["actor_id"]][1]:
            raise ValueError("actor spelling does not match its canonical entity name")
        if row["event_id"] is not None and row["event_id"] not in events:
            raise ValueError("event link has no annotated trigger")
        if row["event_id"] is not None and row["event"] != events[row["event_id"]]:
            raise ValueError("participant event label differs from its action trigger")
        if row["location"] is not None:
            if row["entity_id"] is None:
                raise ValueError("location requires an identified entity mention")
            if row["location"] not in {name for _kind, name in entities.values()}:
                raise ValueError("location must match a mentioned holder or place's canonical name")
            if row["location"] == row["entity_name"]:
                raise ValueError("an entity cannot be its own location")
    by_index = {row["index"]: row for row in annotations}
    result = []
    for span in spans:
        row = by_index.get(span["index"])
        if row is None:
            row = empty_annotation(span["index"], span["token"], pos=span["kind"])
        result.append({**deepcopy(row), "start": span["start"], "end": span["end"], "kind": span["kind"]})
    return result


def shared_prefix(prompt_file: Path = PROMPT, examples_file: Path = EXAMPLES) -> str:
    examples = json.loads(Path(examples_file).read_text(encoding="utf-8"))
    if not isinstance(examples, list) or len(examples) < 3:
        raise ValueError("provide at least three complete annotation examples")
    parts = [Path(prompt_file).read_text(encoding="utf-8").strip()]
    for i, example in enumerate(examples, 1):
        validate_annotations(example["story"], example["response"])
        parts.extend([f"\nEXAMPLE {i} INPUT\n" + compact(story_payload(example["story"])),
                      f"EXAMPLE {i} OUTPUT\n" + compact(example["response"])])
    return "\n".join(parts) + "\n\nAnnotate the next supplied story using exactly this contract.\n"


def annotation_request(story: str, *, prefix: str | None = None, reasoning="low",
                       max_output_tokens=32000) -> dict:
    if not story.strip():
        raise ValueError("story must contain text")
    prefix = shared_prefix() if prefix is None else prefix
    body = dict(model=MODEL, service_tier="flex", reasoning={"effort": reasoning}, store=False,
                max_output_tokens=max_output_tokens,
                text={"format": {"type": "json_schema", "name": "storyformers_annotations_v2",
                                 "strict": True, "schema": annotation_schema()}})
    body["prompt_cache_key"] = VERSION + ":" + fingerprint([prefix, MODEL, body["reasoning"], body["text"]])[:24]
    body["prompt_cache_options"] = {"mode": "explicit", "ttl": "30m"}
    body["input"] = [
        {"role": "developer", "content": [{"type": "input_text", "text": prefix,
                                             "prompt_cache_breakpoint": {"mode": "explicit"}}]},
        {"role": "user", "content": compact(story_payload(story))},
    ]
    return body


def sdk_kwargs(body):
    """SDK 2.43 predates prompt_cache_options; preserve it as API extra_body."""
    result = deepcopy(body)
    result["extra_body"] = {"prompt_cache_options": result.pop("prompt_cache_options")}
    return result
