"""Independent last-word annotation contract; every request sees only its prefix."""

from copy import deepcopy
import json
from pathlib import Path
import re

from .annotation import (EVENT_TYPES, FACTUALITY, FIELDS, LIST_FIELDS, MODEL, NULL_FIELDS,
                         POS, ROLES, annotation_schema, compact, empty_annotation, fingerprint, story_tokens)
from .positions import add_positions


ROOT = Path(__file__).resolve().parent
PROMPT = ROOT / "prompts" / "annotate_prefix_v1.txt"
EXAMPLES = ROOT / "data" / "prefix_annotation_examples.json"
VERSION = "storyformers-prefix-annotation-v1"
TAIL = "\nEND OF SUPPLIED PREFIX. Return one JSON record for its last word only."


def record_schema():
    return annotation_schema()["properties"]["annotations"]["items"]


def prefix_blocks(text):
    """Append-only word-ended blocks; exact tokens and span IDs travel together.

    Spaces/punctuation before a word accompany that word's block. No separator
    after the final word or later punctuation is exposed in its request.
    """
    blocks, pending = [], []
    for span in story_tokens(text):
        pending.append(compact(span))
        if span["kind"] == "word":
            blocks.append(dict(type="input_text", text="\n".join(pending) + "\n",
                               prompt_cache_breakpoint={"mode": "explicit"}))
            pending = []
    return blocks


def request_prefix(body):
    """Decode the literal prefix from a frozen request, without consulting a story."""
    return "".join(json.loads(line)["token"] for block in body["input"][1]["content"][:-1]
                   for line in block["text"].splitlines())


def validate_record(text, row):
    spans = story_tokens(text)
    if not spans or spans[-1]["kind"] != "word":
        raise ValueError("a last-word prefix must end at a word boundary")
    word = spans[-1]
    if not isinstance(row, dict) or set(row) != FIELDS:
        raise ValueError("expected exactly one annotation object with the versioned fields")
    if type(row["index"]) is not int or row["index"] != word["index"] or row["token"] != word["token"]:
        raise ValueError("last-word index or exact token differs from the prefix")
    if row["pos"] not in POS:
        raise ValueError("unknown POS label")
    for field in NULL_FIELDS:
        if row[field] is not None and (not isinstance(row[field], str) or not row[field].strip()):
            raise ValueError(f"{field} must be a nonempty string or null")
    for field, choices in (("event_type", EVENT_TYPES), ("role", ROLES), ("factuality", FACTUALITY)):
        if row[field] is not None and row[field] not in choices:
            raise ValueError(f"unknown {field}")
    for field in LIST_FIELDS:
        if not isinstance(row[field], list):
            raise ValueError(f"{field} must be a list")
    for field in ("patients", "instruments"):
        values = row[field]
        if any(not isinstance(value, str) for value in values) or len(set(values)) != len(values):
            raise ValueError(f"{field} must contain unique entity IDs")
    names = []
    for attribute in row["attributes"]:
        if (not isinstance(attribute, dict) or set(attribute) != {"name", "value"}
                or any(not isinstance(value, str) or not value.strip() for value in attribute.values())
                or not re.fullmatch(r"[a-z][a-z0-9_]*", attribute["name"])):
            raise ValueError("attributes require snake_case names and nonempty string values")
        names.append(attribute["name"])
    if len(set(names)) != len(names):
        raise ValueError("duplicate attribute name")
    entity = [row[field] for field in ("entity_id", "entity", "entity_name")]
    if any(value is not None for value in entity) and any(value is None for value in entity):
        raise ValueError("entity ID, type and canonical name must be supplied together")
    if (row["actor"] is None) != (row["actor_id"] is None):
        raise ValueError("actor and actor_id must be supplied together")
    if (row["event"] is None) != (row["event_id"] is None):
        raise ValueError("event and event_id must be supplied together")
    for field, prefix in (("entity_id", "e"), ("actor_id", "e"), ("recipient_id", "e"), ("event_id", "ev")):
        values = [row[field]]
        if field == "entity_id":
            values += row["patients"] + row["instruments"]
        for value in values:
            if value is None:
                continue
            match = re.fullmatch(prefix + r"([1-9]\d*)", value)
            at = int(match[1]) - 1 if match else -1
            if not 0 <= at < len(spans) or spans[at]["kind"] != "word":
                raise ValueError("ID must refer to a word span already present in the prefix")
    if row["role"] == "action":
        if any(row[field] is None for field in ("event", "event_id", "event_type", "factuality")):
            raise ValueError("an action requires an event, ID, type and factuality")
        if row["event_id"] != f"ev{word['index'] + 1}":
            raise ValueError("a trigger's event ID must be anchored to its own word span")
    elif (any(row[field] is not None for field in ("event_type", "factuality", "actor", "actor_id", "recipient_id"))
          or row["patients"] or row["instruments"]):
        raise ValueError("event argument fields belong only on action triggers")
    elif row["event_id"] is not None and int(row["event_id"][2:]) - 1 >= word["index"]:
        raise ValueError("participants may link only to a preceding event trigger")
    if row["location"] is not None and (row["entity_id"] is None or row["location"] == row["entity_name"]):
        raise ValueError("location requires an entity and cannot be that same entity")
    for field in ("entity_name", "actor", "location"):
        if row[field] is not None and not re.search(r"(?<!\w)" + re.escape(row[field]) + r"(?!\w)", text):
            raise ValueError(f"{field} must name something already mentioned in the prefix")
    return deepcopy(row)


def shared_prefix(prompt_file=PROMPT, examples_file=EXAMPLES):
    examples = json.loads(Path(examples_file).read_text(encoding="utf-8"))
    if not isinstance(examples, list) or len(examples) < 3:
        raise ValueError("provide at least three causal last-word examples")
    parts = [Path(prompt_file).read_text(encoding="utf-8").strip()]
    for index, example in enumerate(examples, 1):
        validate_record(example["prefix"], example["response"])
        records = "".join(block["text"] for block in prefix_blocks(example["prefix"]))
        parts += [f"\nEXAMPLE {index} PREFIX SPANS\n{records}",
                  "EXAMPLE LAST-WORD OUTPUT\n" + compact(example["response"])]
    return "\n".join(parts) + "\n\nAnnotate the last word of the next supplied prefix.\n"


def prefix_request(story, index, *, prefix=None, reasoning="low", max_output_tokens=2048):
    spans = story_tokens(story)
    if type(index) is not int or not 0 <= index < len(spans) or spans[index]["kind"] != "word":
        raise ValueError("choose a word span index; spaces and punctuation are synthesized locally")
    prefix = shared_prefix() if prefix is None else prefix
    blocks = prefix_blocks(story[:spans[index]["end"]])
    body = dict(model=MODEL, service_tier="flex", reasoning={"effort": reasoning}, store=False,
                max_output_tokens=max_output_tokens,
                text={"format": dict(type="json_schema", name="storyformers_prefix_annotation_v1",
                                      strict=True, schema=record_schema())},
                prompt_cache_options={"mode": "explicit", "ttl": "30m"})
    body["prompt_cache_key"] = VERSION + ":" + fingerprint([prefix, MODEL, body["reasoning"], body["text"]])[:24]
    body["input"] = [dict(role="developer", content=[dict(type="input_text", text=prefix,
                        prompt_cache_breakpoint={"mode": "explicit"})]),
                     dict(role="user", content=[*blocks, dict(type="input_text", text=TAIL)])]
    return body


def assemble(story, records):
    """Restore exact local gaps and validate cross-prefix event/entity references."""
    spans, by_index = story_tokens(story), {}
    for row in records:
        index = row.get("index")
        if type(index) is not int or not 0 <= index < len(spans) or index in by_index:
            raise ValueError("duplicate or invalid annotation index")
        by_index[index] = validate_record(story[:spans[index]["end"]], row)
    if set(by_index) != {span["index"] for span in spans if span["kind"] == "word"}:
        raise ValueError("missing last-word annotation")
    for index, row in by_index.items():
        refs = [row["actor_id"], row["recipient_id"], *row["patients"], *row["instruments"]]
        if row["entity_id"] is not None:
            refs.append(row["entity_id"])
        for ref in refs:
            if ref is not None:
                source = by_index.get(int(ref[1:]) - 1)
                if source is None or source["entity_id"] not in (None, ref):
                    raise ValueError("entity reference contradicts its first-mention record")
        if row["event_id"] is not None:
            source = by_index.get(int(row["event_id"][2:]) - 1)
            # An earlier ambiguous word can acquire an interpretation only now.
            # Preserve its unknown record instead of backfilling that information.
            if source is None or (source["event_id"] is not None and
                    (source["role"] != "action" or source["event"] != row["event"])):
                raise ValueError("event reference lacks a consistent prefix-local trigger")
    result = []
    for span in spans:
        annotation = by_index.get(span["index"], empty_annotation(span["index"], span["token"], pos=span["kind"]))
        result.append({**deepcopy(annotation), **span})
    return add_positions(result)
