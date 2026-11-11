"""Lossless assembly of manually authored full-story annotations; no semantic tagger."""

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))
from storyformers.annotation import POS, EVENT_TYPES, FACTUALITY
from storyformers.neuron_spec import check_value

CATALOG = ROOT.parents[1] / "catalog" / "attributes.jsonl"
ASSERTION_STATUSES = {"asserted", "attributed_claim", "candidate"}
EXTENSIONS = [{"key": "event_bindings", "type": "array", "scope": "current word occurrence",
               "description": "All event-role memberships of this word occurrence, retaining correlated event_id, role and scope_id when one mention participates in several predicates.",
               "reason": "The catalog's singular event_id/role cannot retain multiple event memberships. This differs from event_role_conflict, which diagnoses incompatible roles.",
               "example_value": [{"event_id": "ev1", "role": "actor", "scope_id": "s0"}]}]


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


class Annotation:
    def __init__(self, story_id, prompt_version="v0"):
        self.story_id, self.prompt_version = story_id, prompt_version
        self.input = ROOT / "inputs" / story_id
        self.output = ROOT / "annotations" / story_id
        self.output.mkdir(parents=True, exist_ok=True)
        self.story = (self.input / "story.txt").read_text()
        self.rows = json.loads((self.input / "tokens.json").read_text())
        self.words = [r for r in self.rows if r["kind"] == "word"]
        self.paragraphs = json.loads((self.input / "paragraphs.json").read_text())
        for w, row in enumerate(self.words):
            row.update(word_index=w, scope_id="s0")
        for row in self.rows:
            if row["kind"] != "word":
                row["pos"] = row["kind"]
        self.entities, self.events, self.propositions = {}, {}, {}
        self.scopes = {"s0": {"kind": "narration", "parent": None, "description": "Narrator's story world; events still retain local time and factuality."}}
        self.extensions = deepcopy(EXTENSIONS)
        self.evidence = []
        self.tagged = set()

    def anchor(self, word):
        """Catalog tN: one-based nonspace token position (punctuation included)."""
        index = self.words[word]["index"]
        return f"t{sum(row['kind'] != 'space' for row in self.rows[:index + 1])}"

    def tag(self, paragraph, tags, lemmas=None):
        """One explicit POS per word, authored in paragraph order; no defaults."""
        words = self.paragraphs[paragraph]["words"]
        tags = tags.split() if isinstance(tags, str) else tags
        if len(words) != len(tags):
            raise ValueError(f"P{paragraph}: {len(words)} words but {len(tags)} POS tags")
        lemmas = lemmas or {}
        for word, pos in zip(words, tags):
            w = word["w"]
            if pos not in POS:
                raise ValueError(f"P{paragraph}/w{w}: invalid POS {pos}")
            if w in self.tagged:
                raise ValueError(f"w{w} tagged twice")
            self.tagged.add(w)
            surface = self.words[w]["token"]
            self.words[w].update(pos=pos, lemma=lemmas.get(w, lemmas.get(surface, surface.casefold())))

    def feature(self, words, *, evidence=None, note=None, **fields):
        words = [words] if isinstance(words, int) else list(words)
        for w in words:
            self.words[w].update(deepcopy(fields))
        if evidence is not None or note:
            self.evidence.append({"words": words, "fields": list(fields), "support_words": list(evidence or words), "note": note})

    def entity(self, eid, name, kind, mentions, **metadata):
        if eid in self.entities:
            raise ValueError(f"duplicate entity {eid}")
        mentions = list(mentions)
        self.entities[eid] = {"name": name, "type": kind, "mentions": mentions, **metadata}
        self.feature(mentions, entity_id=eid, entity_name=name, entity=kind)

    def scope(self, sid, words, *, kind, parent="s0", holder_id=None, description=""):
        if sid in self.scopes:
            raise ValueError(f"duplicate scope {sid}")
        words = list(words)
        self.scopes[sid] = dict(kind=kind, parent=parent, holder_id=holder_id, words=words, description=description)
        fields = {"scope_id": sid}
        if kind == "quotation":
            fields["quotation_scope_id"] = sid
            if holder_id:
                fields["speaker_id"] = holder_id
        self.feature(words, **fields)

    def proposition(self, pid, text, support, *, scope_id="s0", **metadata):
        if pid in self.propositions:
            raise ValueError(f"duplicate proposition {pid}")
        self.propositions[pid] = dict(text=text, support_words=list(support), scope_id=scope_id, **metadata)

    def event(self, eid, trigger, label, *, type="other", actor=None, patients=(),
              instruments=(), recipient=None, factuality="asserted", scope=None, roles=None,
              support=None, primary=None, **fields):
        if eid in self.events:
            raise ValueError(f"duplicate event {eid}")
        scope = scope or self.words[trigger]["scope_id"]
        primary = self.words[trigger].get("role") != "action" if primary is None else primary
        if primary and scope != self.words[trigger]["scope_id"]:
            raise ValueError(f"{eid}: assign trigger w{trigger} to scope {scope} before creating the event")
        if not primary and fields:
            raise ValueError("Use an explicit correlated feature bundle for secondary-event attributes")
        data = dict(event_id=eid, trigger=trigger, event=label, event_type=type,
                    actor_id=actor, patients=list(patients), instruments=list(instruments),
                    recipient_id=recipient, factuality=factuality, scope_id=scope,
                    support_words=list(support or [trigger]))
        self.events[eid] = data
        patch = {k: deepcopy(data[k]) for k in ("event_id", "event", "event_type", "patients", "instruments", "factuality")}
        if actor:
            patch.update(actor_id=actor, actor=self.entities[actor]["name"])
        if recipient:
            patch["recipient_id"] = recipient
        if primary:
            # Remove old participant/trigger scalars before setting one coherent
            # primary event. Additional events stay in their complete registry.
            for key in ("actor_id", "actor", "recipient_id", "patients", "instruments", "event_type", "factuality"):
                self.words[trigger].pop(key, None)
            self.feature(trigger, role="action", **patch, **fields)
        self._binding(trigger, eid, "action", scope)
        for role, words in (roles or {}).items():
            for w in words:
                self._binding(w, eid, role, scope)
                if "event_id" not in self.words[w]:
                    self.feature(w, event_id=eid, event=label, role=role)

    def _binding(self, word, eid, role, scope):
        binding = {"event_id": eid, "role": role, "scope_id": scope}
        if binding not in self.words[word].setdefault("event_bindings", []):
            self.words[word]["event_bindings"].append(binding)

    def mention_event(self, eid, words, *, role="reference", note=""):
        """A later reference to the same event does not create another event."""
        event = self.events[eid]
        words = [words] if isinstance(words, int) else list(words)
        for word in words:
            self._binding(word, eid, role, self.words[word]["scope_id"])
            if "event_id" not in self.words[word] or (role == "action" and self.words[word].get("role") != "action"):
                for key in ("actor_id", "actor", "recipient_id", "patients", "instruments", "event_type", "factuality"):
                    self.words[word].pop(key, None)
                self.feature(word, event_id=eid, event=event["event"], role=role if role != "reference" else "other")
                if role == "action":
                    fields = {key: deepcopy(event[key]) for key in ("event_type", "patients", "instruments", "factuality")}
                    if event["actor_id"]:
                        fields.update(actor_id=event["actor_id"], actor=self.entities[event["actor_id"]]["name"])
                    if event["recipient_id"]:
                        fields["recipient_id"] = event["recipient_id"]
                    self.feature(word, **fields)
            event.setdefault("mentions", []).append({"word": word, "scope_id": self.words[word]["scope_id"], "role": role, "note": note})

    def extension(self, key, type, description, scope, reason, example_value):
        self.extensions.append(dict(key=key, type=type, description=description, scope=scope,
                                    reason=reason, example_value=example_value))

    def use_extension(self, key):
        """Reuse an agreed trial definition instead of inventing a naming alias."""
        if any(item["key"] == key for item in self.extensions):
            return
        registry = json.loads((ROOT / "prompts" / f"extension_registry_{self.prompt_version}.json").read_text())
        definitions = {item["key"]: item for item in registry}
        if key not in definitions:
            raise ValueError(f"No agreed trial definition for {key}; propose a new extension explicitly")
        self.extensions.append(deepcopy(definitions[key]))

    def save(self, feedback):
        if self.tagged != set(range(len(self.words))):
            raise ValueError(f"untagged words: {sorted(set(range(len(self.words))) - self.tagged)}")
        write_json(self.output / "entities.json", self.entities)
        write_json(self.output / "events.json", self.events)
        write_json(self.output / "scopes.json", self.scopes)
        write_json(self.output / "propositions.json", self.propositions)
        write_json(self.output / "evidence.json", self.evidence)
        write_json(self.output / "new_attributes.json", self.extensions)
        write_json(self.output / "feedback.json", feedback)
        (self.output / "annotations.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in self.rows))
        write_json(self.output / "metadata.json", dict(story_id=self.story_id, prompt_version=self.prompt_version,
                   mode="whole_story_retrospective", annotation_schema="catalog-whole-story-annotation-v1",
                   source_sha256=hashlib.sha256(self.story.encode()).hexdigest(), semantic_authoring="agent_manual",
                   structural_authoring="deterministic_tokenization_and_positions", sparse=True,
                   missing_means="unknown_or_not_annotated", catalog_attribute_count=1024,
                   anchor_conventions={"word_index": "zero_based_words_only", "index": "zero_based_all_lossless_tokens", "tN": "one_based_nonspace_tokens_including_punctuation", "evidence_and_support_words": "word_index"},
                   prompt_sha256=hashlib.sha256((ROOT / "prompts" / f"annotate_{self.prompt_version}.md").read_bytes()).hexdigest(),
                   catalog_overrides_sha256=hashlib.sha256((ROOT / "prompts" / "catalog_overrides.json").read_bytes()).hexdigest()))
        report = validate(self.story_id)
        write_json(self.output / "validation.json", report)
        if report["errors"]:
            raise ValueError("; ".join(report["errors"][:20]))
        print(json.dumps({k: report[k] for k in ("story_id", "words", "events", "entities", "distinct_features", "errors")}))


def validate(story_id):
    folder = ROOT / "annotations" / story_id
    load = lambda name: json.loads((folder / f"{name}.json").read_text())
    rows = [json.loads(line) for line in (folder / "annotations.jsonl").read_text().splitlines()]
    source = json.loads((ROOT / "inputs" / story_id / "tokens.json").read_text())
    entities, events, scopes, propositions = (load(k) for k in ("entities", "events", "scopes", "propositions"))
    registry = {a["key"]: a for a in map(json.loads, CATALOG.read_text().splitlines())}
    errors = []
    for definition in load("new_attributes"):
        if definition["key"] in registry:
            errors.append(f"extension collides with registered field {definition['key']}")
        registry[definition["key"]] = definition
    for definition in json.loads((ROOT / "prompts" / "catalog_overrides.json").read_text()):
        registry[definition["key"]].update(definition)
    structural = {"token", "index", "start", "end", "kind", "position", "word_index"}
    if len(rows) != len(source):
        errors.append("token count changed")
    words = [r for r in rows if r["kind"] == "word"]
    for row, original in zip(rows, source):
        if any(row.get(k) != original[k] for k in original):
            errors.append(f"structural token changed at {original['index']}")
        if row["kind"] != "word":
            if set(row) != set(original) | {"pos"} or row["pos"] != row["kind"]:
                errors.append(f"nonsynthetic gap at {row['index']}")
            continue
        if row.get("pos") not in POS or not isinstance(row.get("lemma"), str):
            errors.append(f"missing lexical annotation at {row['index']}")
        if row.get("scope_id") not in scopes:
            errors.append(f"unknown scope at {row['index']}")
        for key, value in row.items():
            if key in structural:
                continue
            if key not in registry:
                errors.append(f"unregistered feature {key}")
                continue
            try:
                check_value(value, registry[key])
                if value is not None and "values" in registry[key] and value not in registry[key]["values"]:
                    errors.append(f"word {row['word_index']}/{key}: unsupported enum value")
            except (ValueError, TypeError) as exc:
                errors.append(f"word {row['word_index']}/{key}: {exc}")
            if registry[key]["type"] == "entity_ref" and value is not None and value not in entities:
                errors.append(f"unbound entity {value}")
            if key == "assertion_status" and (not isinstance(value, str) or value not in ASSERTION_STATUSES):
                errors.append(f"word {row['word_index']}: unsupported assertion_status {value}")
            if key == "attributes" and isinstance(value, list):
                if any(not isinstance(item, dict) or not isinstance(item.get("name"), str)
                       or not isinstance(item.get("value"), str) for item in value):
                    errors.append(f"word {row['word_index']}: attributes require name/string-value pairs")
            def links(value):
                if isinstance(value, str):
                    if re.fullmatch(r"e[1-9]\d*", value) and value not in entities:
                        errors.append(f"word {row['word_index']}/{key}: unbound nested entity {value}")
                    if re.fullmatch(r"ev[1-9]\d*", value) and value not in events:
                        errors.append(f"word {row['word_index']}/{key}: unbound nested event {value}")
                    if re.fullmatch(r"p[1-9]\d*", value) and value not in propositions:
                        errors.append(f"word {row['word_index']}/{key}: unbound proposition {value}")
                    if re.fullmatch(r"(?:s|q)[0-9]+", value) and value not in scopes:
                        errors.append(f"word {row['word_index']}/{key}: unbound nested scope {value}")
                elif isinstance(value, (dict, list)):
                    if (isinstance(value, dict) and "assertion_status" in value
                            and (not isinstance(value["assertion_status"], str) or value["assertion_status"] not in ASSERTION_STATUSES)):
                        errors.append(f"word {row['word_index']}/{key}: unsupported nested assertion_status {value['assertion_status']}")
                    for child in value.values() if isinstance(value, dict) else value:
                        links(child)
            links(value)
        if row.get("entity_id") in entities:
            entity = entities[row["entity_id"]]
            if row.get("entity_name") != entity["name"] or row.get("entity") != entity["type"]:
                errors.append(f"entity drift at word {row['word_index']}")
        for binding in row.get("event_bindings", []):
            if binding.get("event_id") not in events or binding.get("scope_id") not in scopes:
                errors.append(f"unbound event membership at word {row['word_index']}")
        if row.get("event_id") is not None:
            event = events.get(row["event_id"])
            if event is None or row.get("event") != event["event"]:
                errors.append(f"invalid primary event at word {row['word_index']}")
            if not any(b["event_id"] == row["event_id"] for b in row.get("event_bindings", [])):
                errors.append(f"primary event lacks membership at word {row['word_index']}")
            if row.get("role") == "action" and event is not None:
                if row.get("actor_id") != event["actor_id"] or row.get("recipient_id") != event["recipient_id"]:
                    errors.append(f"primary event participant drift at word {row['word_index']}")
        for field in ("patients", "instruments"):
            if any(value not in entities for value in row.get(field, [])):
                errors.append(f"word {row['word_index']}: {field} must contain registered entity IDs")
        if row.get("actor_id") and row.get("actor") != entities.get(row["actor_id"], {}).get("name"):
            errors.append(f"actor display name mismatch at word {row['word_index']}")
    for w, row in enumerate(words):
        if row.get("word_index") != w:
            errors.append("word ordinals changed")
    for eid, event in events.items():
        if not re.fullmatch(r"ev[1-9]\d*", eid) or event["event_type"] not in EVENT_TYPES or event["factuality"] not in FACTUALITY:
            errors.append(f"invalid event {eid}")
        if event["scope_id"] not in scopes or not 0 <= event["trigger"] < len(words):
            errors.append(f"invalid event anchor {eid}")
            continue
        if not any(b["event_id"] == eid and b["role"] == "action" for b in words[event["trigger"]].get("event_bindings", [])):
            errors.append(f"missing event trigger {eid}")
        if words[event["trigger"]].get("event_id") == eid and words[event["trigger"]]["scope_id"] != event["scope_id"]:
            errors.append(f"{eid}: trigger/event scope mismatch")
        if any(type(w) is not int or not 0 <= w < len(words) for w in event["support_words"]):
            errors.append(f"{eid}: evidence outside story")
        for ref in [event["actor_id"], event["recipient_id"], *event["patients"], *event["instruments"]]:
            if ref is not None and ref not in entities:
                errors.append(f"{eid}: unbound participant {ref}")
    for eid, entity in entities.items():
        if not re.fullmatch(r"e[1-9]\d*", eid) or not entity["mentions"]:
            errors.append(f"invalid/unmentioned entity {eid}")
        for w in entity["mentions"]:
            if not 0 <= w < len(words) or words[w].get("entity_id") != eid:
                errors.append(f"{eid}: incorrect mention {w}")
    for sid, scope in scopes.items():
        if scope.get("parent") is not None and scope["parent"] not in scopes:
            errors.append(f"{sid}: unbound parent scope")
        if scope.get("holder_id") is not None and scope["holder_id"] not in entities:
            errors.append(f"{sid}: unbound holder")
        if any(type(w) is not int or not 0 <= w < len(words) for w in scope.get("words", [])):
            errors.append(f"{sid}: scope word outside story")
        ancestors, current = set(), sid
        while current in scopes:
            if current in ancestors:
                errors.append(f"{sid}: scope parent cycle")
                break
            ancestors.add(current)
            current = scopes[current].get("parent")
    for pid, proposition in propositions.items():
        if proposition["scope_id"] not in scopes or any(type(w) is not int or not 0 <= w < len(words) for w in proposition["support_words"]):
            errors.append(f"{pid}: unbound proposition scope/evidence")
    for evidence in load("evidence"):
        if any(type(w) is not int or not 0 <= w < len(words) for w in evidence["words"] + evidence["support_words"]):
            errors.append("evidence outside story")
    counts = Counter(key for row in words for key in row if key not in structural)
    semantic = [sum(key not in structural | {"pos", "lemma", "scope_id", "clause_id"} for key in row) for row in words]
    return dict(story_id=story_id, errors=errors, words=len(words), tokens=len(rows), entities=len(entities),
                events=len(events), scopes=len(scopes), propositions=len(propositions), distinct_features=len(counts),
                feature_counts=dict(counts.most_common()), words_with_semantic_features=sum(n > 0 for n in semantic),
                max_features_per_word=max((len(r) - len(structural & set(r)) for r in words), default=0),
                limitation="Shape, type and link validation only; semantic judgments require reading the story and annotations.")
