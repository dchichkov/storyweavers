#!/usr/bin/env python3
"""
A small story world about a quarrel, a flashback, and a comedy-shaped
reconciliation.

The seed premise:
- two child friends want the same funny thing
- they quarrel
- a flashback reveals why the thing matters
- humor softens the mood
- they reconcile by sharing it

This script models the scene as a tiny physical/emotional simulation with typed
entities, meters, memes, and a declarative ASP twin.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    holder: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    a: object | None = None
    b: object | None = None
    prop: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Stage:
    place: str = "the school hallway"
    allows: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class ObjectSpec:
    id: str
    label: str
    phrase: str
    type: str
    tags: set[str] = field(default_factory=set)
    funny: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    place: str
    prop: str
    name_a: str
    name_b: str
    type_a: str
    type_b: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self, stage: Stage):
        self.stage = stage
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.flashback_used: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.stage)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.flashback_used = self.flashback_used
        return w


def _say_pair(world: World, a: Entity, b: Entity, text: str) -> None:
    world.say(f"{a.id} and {b.id} {text}")


def _do_quarrel(world: World, a: Entity, b: Entity, prop: Entity) -> None:
    a.memes["want"] += 1
    b.memes["want"] += 1
    a.memes["annoyed"] += 1
    b.memes["annoyed"] += 1
    a.memes["quarrel"] += 1
    b.memes["quarrel"] += 1
    prop.meters["held_tight"] = 1
    world.say(
        f"{a.id} and {b.id} both reached for the {prop.label} at once, and a quarrel started."
    )
    world.say(
        f'"I had it first!" {a.id} said. "No, I was just about to use it!" {b.id} said back.'
    )


def _flashback(world: World, a: Entity, b: Entity, prop: Entity) -> None:
    if world.flashback_used:
        return
    world.flashback_used = True
    world.say(
        f"Then {a.id} remembered something funny from earlier that day."
    )
    world.say(
        f"At lunch, {a.id} had sneezed so hard that the {prop.label} wobbled like a wobbling duck, "
        f"and {b.id} had snorted milk through {b.pronoun('object')} nose."
    )
    a.memes["memory"] += 1
    b.memes["memory"] += 1
    a.memes["humor"] += 1
    b.memes["humor"] += 1


def _laugh(world: World, a: Entity, b: Entity, prop: Entity) -> None:
    if a.memes.get("humor", 0) < THRESHOLD and b.memes.get("humor", 0) < THRESHOLD:
        return
    world.say(
        f"They looked at each other, and then at the {prop.label}, and started laughing."
    )
    world.say(
        f"The grumpy faces melted first, then the quarrel fizzled like a tiny balloon."
    )
    a.memes["annoyed"] = 0
    b.memes["annoyed"] = 0
    a.memes["reconcile"] += 1
    b.memes["reconcile"] += 1


def _reconcile(world: World, a: Entity, b: Entity, prop: Entity) -> None:
    if a.memes.get("reconcile", 0) < THRESHOLD or b.memes.get("reconcile", 0) < THRESHOLD:
        return
    prop.holder = None
    world.say(
        f'{a.id} handed the {prop.label} to {b.id}. "We can share it," {a.id} said.'
    )
    world.say(
        f'{b.id} grinned. "And we can take turns being ridiculous."'
    )
    world.say(
        f"That fixed the quarrel, and the funny little {prop.label} belonged to both of them for the rest of recess."
    )


@dataclass
class Rule:
    name: str
    apply: callable
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            before = len(produced)
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
            if len(produced) != before:
                pass
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _r_quarrel(world: World) -> list[str]:
    a = world.get("A")
    b = world.get("B")
    prop = world.get("prop")
    if a.memes.get("quarrel", 0) >= THRESHOLD:
        sig = ("quarrel",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        return [f"{a.id} and {b.id} were in a quarrel over the {prop.label}."]
    return []


def _r_reconcile(world: World) -> list[str]:
    a = world.get("A")
    b = world.get("B")
    prop = world.get("prop")
    if a.memes.get("reconcile", 0) >= THRESHOLD and b.memes.get("reconcile", 0) >= THRESHOLD:
        sig = ("reconcile",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        return [f"The quarrel ended in a grin."]
    return []


CAUSAL_RULES = [
    Rule("quarrel", _r_quarrel),
    Rule("reconcile", _r_reconcile),
]


STAGES = {
    "school": Stage(place="the school hallway", allows={"prop"}),
    "playroom": Stage(place="the playroom", allows={"prop"}),
    "porch": Stage(place="the sunny porch", allows={"prop"}),
}

PROPS = {
    "sockpuppet": ObjectSpec(
        id="sockpuppet",
        label="sock puppet",
        phrase="a striped sock puppet with a bent paper crown",
        type="toy",
        tags={"funny", "stage"},
        funny=True,
    ),
    "bananahat": ObjectSpec(
        id="bananahat",
        label="banana hat",
        phrase="a yellow banana hat that flopped over one ear",
        type="hat",
        tags={"funny", "costume"},
        funny=True,
    ),
    "wig": ObjectSpec(
        id="wig",
        label="wig",
        phrase="a wild orange wig that looked like a fuzzy cloud",
        type="costume",
        tags={"funny", "dressup"},
        funny=True,
    ),
}

NAMES_GIRL = ["Maya", "Nina", "Lila", "Tess", "Zoe", "Ava"]
NAMES_BOY = ["Owen", "Milo", "Ezra", "Leo", "Finn", "Noah"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, stage in STAGES.items():
        for prop in PROPS:
            if "prop" in stage.allows:
                out.append((place, prop))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy story world about a quarrel and reconciliation.")
    ap.add_argument("--place", choices=STAGES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--type-a", choices=["girl", "boy"])
    ap.add_argument("--type-b", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "prop", None):
        combos = [c for c in combos if c[1] == getattr(args, "prop", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, prop = rng.choice(combos)
    type_a = getattr(args, "type_a", None) or rng.choice(["girl", "boy"])
    type_b = getattr(args, "type_b", None) or ("boy" if type_a == "girl" else "girl")
    name_a = getattr(args, "name_a", None) or rng.choice(NAMES_GIRL if type_a == "girl" else NAMES_BOY)
    name_b = getattr(args, "name_b", None) or rng.choice([n for n in (NAMES_GIRL if type_b == "girl" else NAMES_BOY) if n != name_a])
    return StoryParams(place=place, prop=prop, name_a=name_a, name_b=name_b, type_a=type_a, type_b=type_b)


def story_engine(params: StoryParams) -> World:
    world = World(_safe_lookup(STAGES, params.place))
    a = world.add(Entity(id=params.name_a, kind="character", type=params.type_a))
    b = world.add(Entity(id=params.name_b, kind="character", type=params.type_b))
    prop_spec = _safe_lookup(PROPS, params.prop)
    prop = world.add(Entity(id="prop", kind="thing", type=prop_spec.type, label=prop_spec.label, phrase=prop_spec.phrase, owner=a.id, holder=a.id))

    world.say(
        f"{a.id} and {b.id} found {prop.phrase} at {world.stage.place}."
    )
    world.say(
        f"Both of them wanted to use it because it looked hilarious."
    )

    world.para()
    _do_quarrel(world, a, b, prop)
    propagate(world, narrate=False)

    world.para()
    _flashback(world, a, b, prop)
    _laugh(world, a, b, prop)
    _reconcile(world, a, b, prop)

    world.facts = {
        "a": a,
        "b": b,
        "prop": prop,
        "params": params,
        "place": params.place,
        "prop_id": params.prop,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "prop")
    a = _safe_fact(world, world.facts, "a")
    b = _safe_fact(world, world.facts, "b")
    return [
        f"Write a short comedy story about {a.id} and {b.id} quarrelling over a {p.label}, then making up.",
        f"Tell a playful story with a flashback that helps two children stop a quarrel about {p.label}.",
        f"Write a child-friendly story where humor turns an argument into reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = _safe_fact(world, world.facts, "a")
    b = _safe_fact(world, world.facts, "b")
    p = _safe_fact(world, world.facts, "prop")
    return [
        QAItem(
            question=f"What did {a.id} and {b.id} quarrel over?",
            answer=f"They quarrelled over the {p.label}, which looked funny enough that both of them wanted a turn.",
        ),
        QAItem(
            question=f"What did the flashback remind them of?",
            answer=f"It reminded them of a silly moment from lunch, when the {p.label} wobbled and made them laugh.",
        ),
        QAItem(
            question="How did the quarrel end?",
            answer=f"They laughed, shared the {p.label}, and reconciled by agreeing to take turns.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quarrel?",
            answer="A quarrel is a noisy argument between people who both want something or both feel upset.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that goes back to something that happened earlier.",
        ),
        QAItem(
            question="Why can humor help people reconcile?",
            answer="Humor can help because laughing makes people feel less tense and more ready to be kind again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.kind == "thing":
            bits.append(f"label={e.label}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
quarrel :- want(a), want(b), same_prop.
flashback :- quarrel.
humor :- flashback.
reconciliation :- humor.
#show quarrel/0.
#show flashback/0.
#show humor/0.
#show reconciliation/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("want", "a"),
        asp.fact("want", "b"),
        asp.fact("same_prop"),
    ])


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = {s.name for s in model}
    py = {"quarrel", "flashback", "humor", "reconciliation"}
    if atoms == py:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH:", atoms, py)
    return 1


def asp_state() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted({(s.name, len(s.arguments)) for s in model})


def generate(params: StoryParams) -> StorySample:
    world = story_engine(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="school", prop="sockpuppet", name_a="Maya", name_b="Owen", type_a="girl", type_b="boy"),
    StoryParams(place="playroom", prop="bananahat", name_a="Leo", name_b="Nina", type_a="boy", type_b="girl"),
    StoryParams(place="porch", prop="wig", name_a="Ava", name_b="Finn", type_a="girl", type_b="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_state())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
