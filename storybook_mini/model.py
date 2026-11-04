"""Content is data. Execute it once, before any realization switches are used."""
from copy import deepcopy
from dataclasses import asdict, dataclass, field
import hashlib
import json


@dataclass(frozen=True)
class Entity:
    id: str
    noun: str
    name: str = ""
    pronoun: str = "it"
    # Entities are physical carriers, including places and props.
    state: dict = field(default_factory=dict)
    memes: dict = field(default_factory=dict)
    short_noun: str = ""
    number: str = "singular"
    mass: bool = False
    definite: bool = False


@dataclass(frozen=True)
class Proposition:
    """Content of a wish or utterance. Mentioning it does not execute it."""
    predicate: str
    subject: str
    object: str = ""
    target: str = ""
    value: str = ""
    tense: str = "present"
    negative: bool = False


@dataclass(frozen=True)
class Fact:
    id: str
    scene: str
    predicate: str
    subject: str
    object: str = ""
    target: str = ""
    value: str = ""
    cause: str = ""
    cue: str = ""
    requires: tuple = ()       # (entity id, state key, expected value)
    effects: tuple = ()        # (entity id, state key, new value)
    meme_deltas: tuple = ()    # (carrier id, concept, numeric delta)
    goal: Proposition = None
    speech: Proposition = None
    listener: str = ""
    tense: str = "past"
    negative: bool = False
    contrast: str = ""
    topic: str = ""
    paragraph_break: bool = False
    companion: str = ""


@dataclass(frozen=True)
class Story:
    id: str
    title: str
    entities: tuple[Entity, ...]
    facts: tuple[Fact, ...]


@dataclass(frozen=True)
class Snapshot:
    story: Story
    history: tuple[dict, ...]
    final_state: dict
    fingerprint: str


def simulate(story: Story) -> Snapshot:
    """Validate grounded references, causal order and explicit action contracts.

    This is a small authored transition model, not a general physics/planning
    engine. Ablations never get to change or re-execute its content.
    """
    entities = {e.id: e for e in story.entities}
    if len(entities) != len(story.entities):
        raise ValueError("Duplicate entity id")
    if not story.facts:
        raise ValueError("A narrative stream must contain facts")
    for e in story.entities:
        if not e.id or not e.noun or e.number not in {"singular", "plural"}:
            raise ValueError(f"Invalid entity: {e.id}")
        if e.pronoun not in {"she", "he", "it", "they"}:
            raise ValueError(f"Unsupported pronoun: {e.pronoun}")
        if any(not 0 <= v <= 1 for v in e.memes.values()):
            raise ValueError(f"{e.id}: initial concept magnitude outside [0, 1]")
        owner = e.state.get("owner")
        if owner and owner not in entities:
            raise ValueError(f"{e.id}: ungrounded owner {owner}")
    state = {e.id: {"physical": deepcopy(e.state), "memes": deepcopy(e.memes)}
             for e in story.entities}
    seen, history = set(), []
    for f in story.facts:
        if f.id in seen:
            raise ValueError(f"Duplicate fact: {f.id}")
        for ref in (f.subject, f.object, f.target, f.listener, f.companion):
            if ref and ref not in entities:
                raise ValueError(f"{f.id}: ungrounded entity {ref}")
        if not f.subject:
            raise ValueError(f"{f.id}: missing physical carrier")
        if f.cause and f.cause not in seen:
            raise ValueError(f"{f.id}: cause must precede its consequence")
        if f.contrast and f.contrast not in seen:
            raise ValueError(f"{f.id}: contrast must refer to preceding content")
        if f.cause and f.contrast:
            raise ValueError(f"{f.id}: conflicting rhetorical relations")
        if (f.predicate == "be" or f.negative) and (f.effects or f.meme_deltas):
            raise ValueError(f"{f.id}: observations and negated events cannot change the world")
        if f.tense not in {"past", "present", "past_perfect", "future"}:
            raise ValueError(f"{f.id}: unsupported tense")
        if f.speech and (f.predicate != "say" or f.value or not f.listener):
            raise ValueError(f"{f.id}: structured speech needs say, a listener, and no opaque quote")
        if f.goal and (f.predicate != "want" or f.goal.subject != f.subject):
            raise ValueError(f"{f.id}: a want must bind its goal to its physical subject")
        for embedded in (f.goal, f.speech):
            if embedded:
                for ref in (embedded.subject, embedded.object, embedded.target):
                    if ref and ref not in entities:
                        raise ValueError(f"{f.id}: ungrounded embedded entity {ref}")
                if not embedded.subject or embedded.tense not in {"past", "present", "past_perfect", "future"}:
                    raise ValueError(f"{f.id}: invalid embedded proposition")
        before = deepcopy(state)
        for eid, key, expected in f.requires:
            if eid not in state or state[eid]["physical"].get(key) != expected:
                raise ValueError(f"{f.id}: failed precondition {eid}.{key}={expected}")
        for eid, key, value in f.effects:
            if eid not in state:
                raise ValueError(f"{f.id}: effect has no physical carrier: {eid}")
            state[eid]["physical"][key] = value
            if key == "owner" and value not in entities:
                raise ValueError(f"{f.id}: ungrounded new owner {value}")
        for eid, meme, delta in f.meme_deltas:
            if eid not in state or not isinstance(delta, (int, float)):
                raise ValueError(f"{f.id}: invalid embedded concept change")
            magnitude = state[eid]["memes"].get(meme, 0) + delta
            if not 0 <= magnitude <= 1:
                raise ValueError(f"{f.id}: {meme} magnitude outside [0, 1]")
            state[eid]["memes"][meme] = round(magnitude, 6)
        if f.predicate == "feel" and f.value not in state[f.subject]["memes"]:
            raise ValueError(f"{f.id}: emotion has not been embedded in {f.subject}")
        if f.predicate == "be" and ("condition" not in state[f.subject]["physical"] or
                (state[f.subject]["physical"]["condition"] == f.value) == f.negative):
            raise ValueError(f"{f.id}: description contradicts physical state")
        history.append({"fact": asdict(f), "before": before, "after": deepcopy(state)})
        seen.add(f.id)
    payload = {"story": asdict(story), "history": history, "final_state": state}
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return Snapshot(story, tuple(history), state, fingerprint)
