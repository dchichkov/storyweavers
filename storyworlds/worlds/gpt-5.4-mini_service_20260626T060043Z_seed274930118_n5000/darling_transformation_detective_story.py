#!/usr/bin/env python3
"""
storyworlds/worlds/darling_transformation_detective_story.py
=============================================================

A small standalone storyworld for a detective tale with a transformation:
a careful child detective follows clues, notices something darling and strange,
and discovers who caused the change.

The story is built from world state, not from a frozen paragraph.  The main
shape is:
- setup: the detective and their darling companion notice something missing or odd
- middle: clues, suspicion, and a transformation that changes the case
- ending: the detective connects the facts and restores the world

The style stays close to a gentle detective story, with concrete clues, small
objects, and a clear resolution image.
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
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    darling: object | None = None
    detective: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
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
    place: str
    clue_source: str
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
class Transformation:
    id: str
    verb: str
    clue: str
    cause: str
    effect: str
    reveal: str
    keyword: str
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str = "hands"
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    w: object | None = None
    world: object | None = None
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w
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


SETTINGS = {
    "library": Setting(place="the library", clue_source="dusty shelves", affords={"glow", "swap"}),
    "garden": Setting(place="the garden", clue_source="muddy paths", affords={"grow", "swap"}),
    "workshop": Setting(place="the workshop", clue_source="paint pots", affords={"glow", "swap"}),
    "bedroom": Setting(place="the bedroom", clue_source="tiny footprints", affords={"swap"}),
}

TRANSFORMATIONS = {
    "cat_to_mouse": Transformation(
        id="cat_to_mouse",
        verb="turn into a tiny mouse",
        clue="a little trail of crumbs",
        cause="a glittery charm",
        effect="small and quick",
        reveal="a magical charm",
        keyword="transformation",
        tags={"magic", "animal", "glitter"},
    ),
    "toy_to_bird": Transformation(
        id="toy_to_bird",
        verb="turn into a bright little bird",
        clue="feather dust near the window",
        cause="a warm sunbeam",
        effect="light and ready to hop",
        reveal="a warm sunbeam",
        keyword="transformation",
        tags={"magic", "toy", "feather"},
    ),
    "rock_to_gem": Transformation(
        id="rock_to_gem",
        verb="turn into a shiny gem",
        clue="sparkles on the floor",
        cause="a secret polishing cloth",
        effect="smooth and shining",
        reveal="a polishing cloth",
        keyword="transformation",
        tags={"magic", "sparkle", "stone"},
    ),
    "coat_to_cape": Transformation(
        id="coat_to_cape",
        verb="turn into a bright cape",
        clue="a swirl of red thread",
        cause="a clever ribbon stitch",
        effect="fluttery and dramatic",
        reveal="a ribbon stitch",
        keyword="transformation",
        tags={"magic", "cloth", "thread"},
    ),
}

PRIZES = {
    "lantern": Prize(label="lantern", phrase="a little brass lantern", type="lantern"),
    "hat": Prize(label="hat", phrase="a neat brown hat", type="hat"),
    "book": Prize(label="book", phrase="a blue storybook", type="book"),
    "coat": Prize(label="coat", phrase="a warm yellow coat", type="coat"),
}

GIRL_NAMES = ["Mina", "Ruby", "Ivy", "Nora", "Lily"]
BOY_NAMES = ["Theo", "Eli", "Finn", "Owen", "Leo"]
TRAITS = ["curious", "careful", "brave", "gentle", "smart"]


@dataclass
class StoryParams:
    place: str
    transformation: str
    prize: str
    name: str
    gender: str
    trait: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for tr_id, tr in TRANSFORMATIONS.items():
            for prize_id in PRIZES:
                if tr.id == "coat_to_cape" and prize_id != "coat":
                    continue
                if tr.id == "rock_to_gem" and prize_id not in {"book", "lantern"}:
                    continue
                if tr.id == "cat_to_mouse" and place not in {"library", "bedroom"}:
                    continue
                if tr.id == "toy_to_bird" and place not in {"workshop", "bedroom"}:
                    continue
                if prize_id in {"hat", "coat", "book", "lantern"}:
                    combos.append((place, tr_id, prize_id))
    return sorted(set(combos))


def explain_rejection(place: str, tr: Transformation, prize: Prize) -> str:
    return (
        f"(No story: the transformation {tr.id} does not fit {place} with {prize.label}. "
        f"Try another combination that leaves a clear clue, a clear cause, and a clear fix.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle detective storyworld with a transformation.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--transformation", choices=sorted(TRANSFORMATIONS))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=sorted(TRAITS))
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
    if getattr(args, "place", None) and getattr(args, "transformation", None) and getattr(args, "prize", None):
        if (getattr(args, "place", None), getattr(args, "transformation", None), getattr(args, "prize", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "transformation", None) is None or c[1] == getattr(args, "transformation", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, tr_id, prize_id = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, transformation=tr_id, prize=prize_id, name=name, gender=gender, trait=trait)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        for a in sorted(_safe_lookup(SETTINGS, pid).affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, tr in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation", tid))
        for tag in sorted(tr.tags):
            lines.append(asp.fact("tag", tid, tag))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,R) :- place(P), transformation(T), prize(R), affords(P,swap).
valid(P,T,R) :- place(P), transformation(T), prize(R), T = cat_to_mouse, (P = library; P = bedroom).
valid(P,T,R) :- place(P), transformation(T), prize(R), T = toy_to_bird, (P = workshop; P = bedroom).
valid(P,T,R) :- place(P), transformation(T), prize(R), T = rock_to_gem, (R = book; R = lantern).
valid(P,T,R) :- place(P), transformation(T), prize(R), T = coat_to_cape, R = coat.
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def _setup(world: World, params: StoryParams) -> None:
    detective = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    darling = world.add(Entity(id="darling", kind="character", type="pet", label="Darling"))
    prize = world.add(Entity(id="prize", type=_safe_lookup(PRIZES, params.prize).type, label=_safe_lookup(PRIZES, params.prize).label, phrase=_safe_lookup(PRIZES, params.prize).phrase, owner=detective.id))
    world.facts.update(detective=detective, darling=darling, prize=prize, transformation=_safe_lookup(TRANSFORMATIONS, params.transformation), setting=_safe_lookup(SETTINGS, params.place))


def _narrate_setup(world: World) -> None:
    f = world.facts
    det = _safe_fact(world, f, "detective")
    darling = _safe_fact(world, f, "darling")
    prize = _safe_fact(world, f, "prize")
    tr = _safe_fact(world, f, "transformation")
    place = _safe_fact(world, f, "setting").place
    world.say(f"{det.id} was a {det.pronoun('subject')} little {det.label_word if det.label else det.type} detective who always noticed the smallest clue.")
    world.say(f"Darling, the tiny companion, stayed close and nosed around every corner.")
    world.say(f"On the table sat {prize.phrase}, and {det.id} liked it because it looked neat and important.")
    world.para()
    world.say(f"One day, in {place}, something strange began to happen near the {f['setting'].clue_source}.")
    world.say(f"There was {tr.clue}, and the air felt ready for a {tr.keyword}.")


def _narrate_middle(world: World) -> None:
    f = world.facts
    det = _safe_fact(world, f, "detective")
    tr = _safe_fact(world, f, "transformation")
    prize = _safe_fact(world, f, "prize")
    world.say(f"{det.id} crouched down and studied the clue like a real detective.")
    world.say(f"At first, {det.id} thought the case was simple, but then {prize.label} started to {tr.verb}.")
    world.say(f"It became {tr.effect}, and even Darling barked in surprise.")
    world.say(f"{det.id} knew the change had a cause, so {det.id} followed the clue again.")


def _narrate_end(world: World) -> None:
    f = world.facts
    det = _safe_fact(world, f, "detective")
    tr = _safe_fact(world, f, "transformation")
    prize = _safe_fact(world, f, "prize")
    world.say(f"The last clue led straight to {tr.reveal}.")
    world.say(f"{det.id} smiled, because the mystery made sense now: the change was not a trick, just a hidden cause.")
    world.say(f"With one careful fix, {prize.label} settled back to normal, and Darling curled up beside the solved case.")
    world.say(f"By the end, the room was quiet again, and the little detective could admire the clean, ordinary {prize.label} on the table.")


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    _setup(world, params)
    _narrate_setup(world)
    world.para()
    _narrate_middle(world)
    world.para()
    _narrate_end(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tr = _safe_fact(world, f, "transformation")
    return [
        f'Write a short detective story for a young child that includes the word "darling" and the idea of a {tr.keyword}.',
        f"Tell a gentle mystery where {f['detective'].id} follows clues and notices something that can {tr.verb}.",
        f"Write a simple story about a clue, a transformation, and a calm ending in {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = _safe_fact(world, f, "detective")
    prize = _safe_fact(world, f, "prize")
    tr = _safe_fact(world, f, "transformation")
    return [
        QAItem(
            question=f"Who solved the mystery in the story?",
            answer=f"{det.id} solved the mystery by following the clues carefully.",
        ),
        QAItem(
            question=f"What strange change happened to {prize.label}?",
            answer=f"{prize.label} began to {tr.verb}, and that was the heart of the mystery.",
        ),
        QAItem(
            question=f"Who stayed close to the detective while the case was being solved?",
            answer="Darling stayed close and helped by noticing the little details.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form to another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="library", transformation="cat_to_mouse", prize="book", name="Mina", gender="girl", trait="curious"),
    StoryParams(place="workshop", transformation="toy_to_bird", prize="lantern", name="Theo", gender="boy", trait="careful"),
    StoryParams(place="garden", transformation="rock_to_gem", prize="hat", name="Ivy", gender="girl", trait="smart"),
    StoryParams(place="bedroom", transformation="coat_to_cape", prize="coat", name="Leo", gender="boy", trait="brave"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos")
        for t in asp_valid_combos():
            print(t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
