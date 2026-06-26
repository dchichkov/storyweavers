#!/usr/bin/env python3
"""
storyworlds/worlds/stripe_dim_happen_dodo_kindness_magic_mystery.py
====================================================================

A small mystery story world about a dim striped clue, a dodo, and a little
act of kindness that reveals a bit of magic.

Premise:
- A child notices something strange in a quiet setting.
- A dodo-shaped clue seems to "happen" again and again around a stripe-dim
  object.
- Kindness and a small bit of magic help the characters solve the mystery.

The world is deliberately tiny and classical:
- entities have physical meters and emotional memes
- the story is driven by world state, not by a fixed paragraph template
- the mystery resolves when the hidden clue is treated gently and the right
  object is restored to its place
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden: bool = False
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue_ent: object | None = None
    helper: object | None = None
    hero: object | None = None
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
class Place:
    name: str
    indoors: bool = True
    hush: str = ""
    clues: set[str] = field(default_factory=set)
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


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    clue_kind: str
    reveal: str
    risk: str
    magical: bool = False
    stripe_dim: bool = False
    kinds: set[str] = field(default_factory=set)
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
    clue: str
    hero_name: str
    hero_type: str
    helper_type: str
    trait: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


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


def _rule_dim(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters.get("dim", 0.0) < THRESHOLD:
            continue
        sig = ("dim", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["mystery"] = e.memes.get("mystery", 0.0) + 1
        out.append(f"The room felt dimmer around {e.label or e.type}.")
    return out


def _rule_kindness(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.characters() if e.kind == "character"), None)
    clue = world.entities.get("clue")
    if not hero or not clue:
        return out
    if hero.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    sig = ("kindness", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.hidden = False
    clue.meters["noticed"] = 1.0
    out.append(f"{hero.id} looked again, this time gently, and noticed the clue.")
    return out


def _rule_magic(world: World) -> list[str]:
    out: list[str] = []
    clue = world.entities.get("clue")
    dodo = world.entities.get("dodo")
    if not clue or not dodo:
        return out
    if clue.meters.get("noticed", 0.0) < THRESHOLD:
        return out
    if dodo.meters.get("still", 0.0) < THRESHOLD:
        return out
    sig = ("magic", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.meters["magic"] = clue.meters.get("magic", 0.0) + 1
    out.append("A tiny bit of magic shimmered through the stripes.")
    return out


CAUSAL_RULES = [
    Rule("dim", _rule_dim),
    Rule("kindness", _rule_kindness),
    Rule("magic", _rule_magic),
]


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


def is_reasonable(place: Place, clue: Clue) -> bool:
    return clue.id in place.clues


def intro(world: World, hero: Entity, helper: Entity, clue: Clue) -> None:
    world.say(
        f"{hero.id} was a little {hero.trait if hasattr(hero, 'trait') else 'curious'} "
        f"{hero.type} who liked quiet rooms and careful looking."
    )
    world.say(
        f"Near the back of {world.place.name}, {helper.label} kept watch over "
        f"{clue.phrase}."
    )


def setup_mystery(world: World, hero: Entity, helper: Entity, clue: Clue) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    clue.hidden = True
    clue.meters["dim"] = 1.0 if clue.stripe_dim else 0.0
    clue.meters["risk"] = 1.0
    helper.meters["still"] = 1.0
    world.say(
        f"One afternoon, {hero.id} noticed something strange: "
        f"{clue.phrase} looked {clue.label} and half lost in shadow."
    )


def hint_happen(world: World, clue: Clue) -> None:
    world.say(
        f"Every time {hero_word(world)} stepped closer, the little mystery seemed to "
        f"happen again, as if the stripes were trying to say something."
    )


def hero_word(world: World) -> str:
    return next(e.id for e in world.characters() if e.kind == "character")


def question(world: World, hero: Entity, helper: Entity, clue: Clue) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"{hero.id} whispered, \"What is happening here?\" "
        f"{helper.label} only blinked beside the {clue.label}."
    )


def kind_action(world: World, hero: Entity, helper: Entity, clue: Clue) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    world.say(
        f"Instead of tugging, {hero.id} used kindness: {hero.pronoun('subject').capitalize()} "
        f"held out {hero.pronoun('possessive')} hand and waited."
    )
    propagate(world, narrate=True)


def reveal(world: World, hero: Entity, helper: Entity, clue: Clue) -> None:
    if clue.meters.get("magic", 0.0) < THRESHOLD:
        return
    world.say(
        f"Then the stripes brightened, and the answer arrived in a soft little flash."
    )
    world.say(
        f"{helper.label} had been carrying {clue.phrase} all along, and it was "
        f"meant to be returned to its place."
    )
    world.say(
        f"{hero.id} gently set it down, and the room felt calm again."
    )


def ending(world: World, hero: Entity, helper: Entity, clue: Clue) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["worry"] = 0.0
    clue.hidden = False
    world.say(
        f"In the end, {hero.id} smiled at the quiet room. "
        f"The stripe-dim mystery had happened, been noticed, and been kindly put right."
    )


def tell(place: Place, clue: Clue, hero_name: str, hero_type: str, helper_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=[trait, "gentle"]))
    hero.trait = trait
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label="the helper", traits=["patient"]))
    clue_ent = world.add(Entity(
        id="clue",
        type="thing",
        label=clue.label,
        phrase=clue.phrase,
        owner="helper",
        caretaker="helper",
        hidden=True,
    ))
    world.add(Entity(id="dodo", type="bird", label="the dodo", phrase="a small dodo statue"))
    intro(world, hero, helper, clue)
    world.para()
    setup_mystery(world, hero, helper, clue)
    hint_happen(world, clue)
    question(world, hero, helper, clue)
    world.para()
    kind_action(world, hero, helper, clue)
    reveal(world, hero, helper, clue)
    ending(world, hero, helper, clue)
    world.facts.update(hero=hero, helper=helper, clue=clue, clue_ent=clue_ent, place=place)
    return world


PLACES = {
    "gallery": Place(
        name="the quiet gallery",
        indoors=True,
        hush="soft footsteps",
        clues={"stripe_dim_dodo"},
    ),
    "library": Place(
        name="the old library",
        indoors=True,
        hush="whispers",
        clues={"stripe_dim_dodo"},
    ),
    "atrium": Place(
        name="the sunlit atrium",
        indoors=True,
        hush="glowing windows",
        clues={"stripe_dim_dodo"},
    ),
}

CLUES = {
    "stripe_dim_dodo": Clue(
        id="stripe_dim_dodo",
        label="stripe-dim",
        phrase="a stripe-dim case with a tiny dodo emblem",
        clue_kind="mystery",
        reveal="the emblem opens a hidden note",
        risk="it can be missed in the shadows",
        magical=True,
        stripe_dim=True,
        kinds={"stripe-dim", "happen", "dodo", "kindness", "magic", "mystery"},
    ),
}

NAMES_GIRL = ["Mina", "Lina", "Nora", "Ivy", "Aria", "Mira"]
NAMES_BOY = ["Owen", "Theo", "Eli", "Noah", "Finn", "Jude"]
TRAITS = ["curious", "careful", "quiet", "brave"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, clue_id) for place in PLACES for clue_id in CLUES if is_reasonable(_safe_lookup(PLACES, place), _safe_lookup(CLUES, clue_id))]


def explain_rejection(place: Place, clue: Clue) -> str:
    return f"(No story: {clue.label} does not fit this place's mystery shelf.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery story world with stripe-dim, happen, dodo, kindness, and magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["woman", "man"])
    ap.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "clue", None):
        if not is_reasonable(_safe_lookup(PLACES, getattr(args, "place", None)), _safe_lookup(CLUES, getattr(args, "clue", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, clue = rng.choice(combos)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    hero_type = gender
    helper_type = getattr(args, "helper", None) or rng.choice(["woman", "man"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, clue=clue, hero_name=hero_name, hero_type=hero_type, helper_type=helper_type, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    clue = _safe_fact(world, f, "clue")
    return [
        f'Write a short mystery story for a young child using the words "stripe-dim", "happen", and "dodo".',
        f"Tell a gentle mystery about {hero.id}, a {hero.type}, who notices {clue.phrase} in {world.place.name}.",
        f"Write a child-facing story where kindness and magic help explain why the little clue keeps seeming to happen again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    clue = _safe_fact(world, f, "clue")
    return [
        QAItem(
            question=f"What did {hero.id} notice in {world.place.name}?",
            answer=f"{hero.id} noticed {clue.phrase}, which looked stripe-dim and a little mysterious.",
        ),
        QAItem(
            question=f"What did {hero.id} do instead of grabbing the clue?",
            answer=f"{hero.id} showed kindness and waited gently, which helped the mystery become clear.",
        ),
        QAItem(
            question=f"Who helped solve the mystery?",
            answer=f"{helper.label} and {hero.id} solved it together, with a little magic revealing that the clue belonged back in its place.",
        ),
        QAItem(
            question=f"Why did the mystery seem to happen again and again?",
            answer=f"It seemed to happen again because the stripe-dim clue was easy to miss in the dim light until someone looked carefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward someone or something.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is something surprising and impossible in real life, like a tiny shimmer that helps reveal a secret.",
        ),
        QAItem(
            question="What is a dodo?",
            answer="A dodo was a bird that lived a long time ago. In stories, dodos can be used as funny or curious clues.",
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
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    clue = _safe_lookup(CLUES, params.clue)
    world = tell(place, clue, params.hero_name, params.hero_type, params.helper_type, params.trait)
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


ASP_RULES = r"""
place_ok(P,C) :- place(P), clue(C), fits(P,C).

valid_story(P,C) :- place_ok(P,C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for c in sorted(p.clues):
            lines.append(asp.fact("fits", pid, c))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.magical:
            lines.append(asp.fact("magical", cid))
        if c.stripe_dim:
            lines.append(asp.fact("stripe_dim", cid))
        for k in sorted(c.kinds):
            lines.append(asp.fact("kind", cid, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def CURATED() -> list[StoryParams]:
    return [
        StoryParams(place="gallery", clue="stripe_dim_dodo", hero_name="Mina", hero_type="girl", helper_type="woman", trait="curious"),
        StoryParams(place="library", clue="stripe_dim_dodo", hero_name="Owen", hero_type="boy", helper_type="man", trait="careful"),
    ]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
            header = f"### {p.hero_name}: {p.clue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
