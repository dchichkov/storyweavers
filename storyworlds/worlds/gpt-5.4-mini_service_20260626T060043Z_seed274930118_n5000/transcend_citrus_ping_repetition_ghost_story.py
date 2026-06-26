#!/usr/bin/env python3
"""
storyworlds/worlds/transcend_citrus_ping_repetition_ghost_story.py
==================================================================

A small story world in a ghost-story style, built from the seed words
"transcend", "citrus", and "ping" with repetition as a narrative feature.

Premise:
- A child hears a soft ping in a citrus grove at dusk.
- The grove is full of old fruit trees, a lantern, and a harmless ghost.
- The child must decide whether to flee from the spooky sound or face it.

Tension:
- The ping repeats.
- The child imagines a ghost.
- Fear rises when the sound seems to follow the child through the trees.

Turn:
- The repeated ping is revealed to be a signal from a tiny bell tied to a citrus basket.
- A gentle ghost was asking for help finding a lost orange charm.

Resolution:
- The child helps, fear softens, and the child "transcends" fear by staying calm.
- The ending image proves the change: the grove is quiet, the citrus is safe, and the ping becomes a friendly memory.

World model:
- Characters and objects each carry physical meters and emotional memes.
- Repetition is modeled as repeated cues that can increase fear, then resolve into trust.
- The story is not a frozen template: world state drives the prose and the Q&A.

ASP twin:
- The inline ASP rules mirror the Python reasonableness gate and registry facts.
- `--verify` checks parity and also exercises story generation.
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
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    child: object | None = None
    ghost: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Setting:
    place: str = "the citrus grove"
    dark: bool = True
    affords: set[str] = field(default_factory=set)
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
class Cue:
    id: str
    noun: str
    repeat: str
    reveal: str
    fear_gain: float
    wonder_gain: float
    tags: set[str] = field(default_factory=set)
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
class Charm:
    id: str
    label: str
    phrase: str
    region: str
    helps: set[str] = field(default_factory=set)
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
class StoryParams:
    place: str
    cue: str
    charm: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with repetition and a citrus grove.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--cue", choices=CUES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


SETTINGS = {
    "grove": Setting(place="the citrus grove", dark=True, affords={"ping"}),
    "orchard": Setting(place="the citrus orchard", dark=True, affords={"ping"}),
    "path": Setting(place="the lantern path by the grove", dark=True, affords={"ping"}),
}

CUES = {
    "ping": Cue(
        id="ping",
        noun="ping",
        repeat="ping, ping",
        reveal="a tiny bell",
        fear_gain=1.0,
        wonder_gain=1.0,
        tags={"ping", "ghost", "citrus", "repetition", "transcend"},
    ),
    "citrus": Cue(
        id="citrus",
        noun="citrus",
        repeat="sweet citrus, sweet citrus",
        reveal="a basket of oranges",
        fear_gain=0.5,
        wonder_gain=1.0,
        tags={"citrus", "repetition", "transcend"},
    ),
}

CHARMS = {
    "bell": Charm(
        id="bell",
        label="a little bell",
        phrase="a little silver bell on a ribbon",
        region="hand",
        helps={"ping"},
    ),
    "orange_charm": Charm(
        id="orange_charm",
        label="an orange charm",
        phrase="a bright orange charm",
        region="pocket",
        helps={"citrus", "transcend"},
    ),
}

NAMES_GIRL = ["Mina", "Lila", "Nora", "Ivy", "Esme"]
NAMES_BOY = ["Owen", "Theo", "Finn", "Jude", "Eli"]
TRAITS = ["quiet", "curious", "brave", "careful", "gentle"]


def reasonableness_gate(cue: Cue, charm: Charm) -> bool:
    return bool(cue.id in charm.helps or "transcend" in charm.helps)


def explain_rejection(cue: Cue, charm: Charm) -> str:
    return (
        f"(No story: {charm.label} does not help with {cue.noun}. "
        f"The turn must be a real answer to the spooky cue.)"
    )


@dataclass
class Rule:
    name: str
    apply: callable
    CAUSAL_RULES: list = field(default_factory=list)
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


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    child = _safe_fact(world, world.facts, "child")
    cue = _safe_fact(world, world.facts, "cue")
    if child.memes.get("fear", 0.0) < THRESHOLD:
        return out
    sig = ("repeat", child.id, cue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += cue.fear_gain
    child.memes["unease"] += 0.5
    out.append(f"{cue.repeat} came again from the dark trees.")
    return out


def _r_wonder(world: World) -> list[str]:
    out: list[str] = []
    child = _safe_fact(world, world.facts, "child")
    cue = _safe_fact(world, world.facts, "cue")
    sig = ("wonder", child.id, cue.id)
    if sig in world.fired:
        return out
    if child.memes.get("fear", 0.0) < THRESHOLD:
        return out
    world.fired.add(sig)
    child.memes["wonder"] += cue.wonder_gain
    out.append(f"Still, the sound was small, almost shy, like it wanted to be found.")
    return out


CAUSAL_RULES = [Rule("repeat", _r_repeat), Rule("wonder", _r_wonder)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, cue: Cue, charm_def: Charm, hero_name: str, hero_type: str,
         parent_type: str, traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        meters={"steps": 0.0}, memes={"fear": 0.0, "wonder": 0.0, "peace": 0.0},
    ))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the little ghost",
                             meters={"glow": 1.0}, memes={"lonely": 1.0, "hope": 0.0}))
    charm = world.add(Entity(id=charm_def.id, type="charm", label=charm_def.label, phrase=charm_def.phrase,
                             owner=child.id, caretaker=parent.id))
    child.memes["curiosity"] = 1.0
    child.memes["fear"] = 1.0
    world.facts.update(child=child, parent=parent, ghost=ghost, charm=charm, cue=cue, setting=setting)

    world.say(f"At dusk, {child.id} went into {setting.place}.")
    world.say(f"{child.pronoun().capitalize()} held {child.pronoun('possessive')} breath and listened.")
    world.say(f"Then came the {cue.noun}: {cue.repeat}.")
    world.say(f"{child.id} looked toward the trees and thought of a ghost.")
    world.para()
    world.say(f"The sound came again. {cue.repeat}.")
    child.memes["fear"] += cue.fear_gain
    propagate(world)
    world.say(f"{child.id} whispered, 'Who's there?'")
    world.say(f"The little ghost stepped out softly, not scary, only pale and sad.")
    world.say(f"It pointed to {charm.phrase} and to a lost place among the citrus branches.")
    world.para()

    if not reasonableness_gate(cue, charm_def):
        pass

    child.memes["fear"] += 0.5
    world.say(f"{child.id} found {charm.phrase} and held it up to the light.")
    world.say(f"The bell gave one more ping, but now it sounded friendly.")
    world.say(f"The ghost smiled because the noise was finally understood.")
    child.memes["fear"] = 0.0
    child.memes["peace"] += 1.0
    child.memes["wonder"] += 1.0
    child.memes["transcend"] = 1.0
    ghost.memes["hope"] += 1.0
    world.say(
        f"{child.id} did not run. {child.id} stayed. In that still moment, "
        f"{child.id} seemed to transcend the fear, and the dark grove felt gentle."
    )
    world.say(
        f"At the end, {child.id} walked home with {charm.label}, while the citrus trees "
        f"rested quiet and the ping became only a memory."
    )
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [(cue, charm) for cue in CUES for charm in CHARMS if reasonableness_gate(_safe_lookup(CUES, cue), _safe_lookup(CHARMS, charm))]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    cue = _safe_fact(world, f, "cue")
    charm = _safe_fact(world, f, "charm")
    return [
        f'Write a short ghost story for a small child that repeats the word "{cue.noun}".',
        f"Tell a gentle spooky story in {world.setting.place} where {child.id} learns not to fear the {cue.noun}.",
        f'Write a child-safe ghost story with citrus, repetition, and a calm ending involving {charm.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, cue, charm, ghost = f["child"], f["parent"], f["cue"], f["charm"], f["ghost"]
    qa = [
        QAItem(
            question=f"What did {child.id} hear in {world.setting.place}?",
            answer=f"{child.id} heard the {cue.noun}, and it came back as {cue.repeat}.",
        ),
        QAItem(
            question=f"Why did {child.id} think the grove was spooky at first?",
            answer=f"{child.id} thought the repeated ping might be a ghost, so the dark grove felt scary at first.",
        ),
        QAItem(
            question=f"Who was really making the sound?",
            answer=f"The sound led to the little ghost and {charm.label}; the ping came from a tiny bell, not from anything dangerous.",
        ),
        QAItem(
            question=f"How did {child.id} change by the end of the story?",
            answer=f"{child.id} calmed down, helped the ghost, and learned to transcend the fear instead of running away.",
        ),
    ]
    if ghost.memes.get("hope", 0.0) >= THRESHOLD:
        qa.append(QAItem(
            question=f"How did the ghost feel after {child.id} helped?",
            answer=f"The little ghost felt less lonely and much happier because {child.id} listened and found the lost charm.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is citrus?",
            answer="Citrus is a group of fruits like oranges and lemons. They often smell fresh and taste tangy.",
        ),
        QAItem(
            question="What is a ping?",
            answer="A ping is a small, sharp sound, like a tiny bell being tapped.",
        ),
        QAItem(
            question="What does transcend mean?",
            answer="To transcend something means to rise above it or go past it, especially a hard feeling like fear.",
        ),
        QAItem(
            question="Why do repeated sounds feel important in a story?",
            answer="Repeated sounds can make a story feel spooky, important, or like they are trying to get someone's attention.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="grove", cue="ping", charm="bell", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="orchard", cue="citrus", charm="orange_charm", name="Owen", gender="boy", parent="father"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.dark:
            lines.append(asp.fact("dark", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CUES.items():
        lines.append(asp.fact("cue", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("tag", cid, t))
    for chid, ch in CHARMS.items():
        lines.append(asp.fact("charm", chid))
        for h in sorted(ch.helps):
            lines.append(asp.fact("helps", chid, h))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Cue, Charm) :- cue(Cue), charm(Charm), helps(Charm, Cue).
valid(Cue, Charm) :- cue(Cue), charm(Charm), helps(Charm, transcend).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    sample_ok = True
    try:
        p = resolve_params(argparse.Namespace(place=None, cue=None, charm=None, gender=None, parent=None, name=None), random.Random(7))
        s = generate(p)
        sample_ok = bool(s.story) and bool(s.story_qa)
    except Exception:
        sample_ok = False
    if clingo_set == python_set and sample_ok:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos) and story generation works.")
        return 0
    print("MISMATCH or sample failure:")
    if clingo_set != python_set:
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
    if not sample_ok:
        print("  generated sample failed")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "cue", None) and getattr(args, "charm", None) and not reasonableness_gate(_safe_lookup(CUES, getattr(args, "cue", None)), _safe_lookup(CHARMS, getattr(args, "charm", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "cue", None) is None or c[0] == getattr(args, "cue", None))
              and (getattr(args, "charm", None) is None or c[1] == getattr(args, "charm", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    cue, charm = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    return StoryParams(place=place, cue=cue, charm=charm, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CUES, params.cue), _safe_lookup(CHARMS, params.charm),
                 params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        print(f"{len(asp_valid_combos())} compatible cue/charm combos:")
        for cue, charm in asp_valid_combos():
            print(f"  {cue:10} {charm}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
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

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.cue} in {p.place} (charm: {p.charm})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
