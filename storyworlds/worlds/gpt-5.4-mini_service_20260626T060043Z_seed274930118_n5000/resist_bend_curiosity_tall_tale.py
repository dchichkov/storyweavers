#!/usr/bin/env python3
"""
A tiny tall-tale story world about Curiosity, a stubborn bend, and the choice to
resist a tempting shortcut.
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
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)
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
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    strain: str
    risk_region: str
    weather: str
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
class Gear:
    id: str
    label: str
    phrase: str
    protects_from: set[str]
    covers: set[str]
    prep: str
    tail: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather = ""

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

    def clone(self) -> "World":
        import copy

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.weather = self.weather
        return w


SETTINGS = {
    "hill": Place("the hill", outdoors=True, affords={"kite", "goat"}),
    "harbor": Place("the harbor", outdoors=True, affords={"boat", "kite"}),
    "canyon": Place("the canyon", outdoors=True, affords={"goat", "rope"}),
    "fairground": Place("the fairground", outdoors=True, affords={"kite", "rope"}),
}

CHALLENGES = {
    "kite": Challenge(
        id="kite",
        verb="fly the kite",
        gerund="flying the kite",
        rush="dash after the kite",
        strain="tug at the line until it hummed like a fiddle string",
        risk_region="hands",
        weather="windy",
        keyword="kite",
        tags={"wind", "curiosity"},
    ),
    "goat": Challenge(
        id="goat",
        verb="follow the goat trail",
        gerund="following the goat trail",
        rush="climb after the goat",
        strain="lean over the ridge to peek at the path",
        risk_region="feet",
        weather="sunny",
        keyword="goat",
        tags={"goat", "curiosity"},
    ),
    "boat": Challenge(
        id="boat",
        verb="sail the little boat",
        gerund="sailing the little boat",
        rush="jump into the skiff",
        strain="reach over the side to chase the driftwood",
        risk_region="torso",
        weather="misty",
        keyword="boat",
        tags={"water", "curiosity"},
    ),
    "rope": Challenge(
        id="rope",
        verb="cross the rope bridge",
        gerund="crossing the rope bridge",
        rush="race onto the bridge",
        strain="bounce on the boards like a drum",
        risk_region="feet",
        weather="blustery",
        keyword="rope",
        tags={"bridge", "curiosity"},
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="wool gloves",
        phrase="a pair of wool gloves",
        protects_from={"wind"},
        covers={"hands"},
        prep="slip on wool gloves first",
        tail="put on the wool gloves",
    ),
    Gear(
        id="boots",
        label="sturdy boots",
        phrase="sturdy boots",
        protects_from={"drop"},
        covers={"feet"},
        prep="lace up the sturdy boots",
        tail="laced up the sturdy boots",
    ),
    Gear(
        id="vest",
        label="a life vest",
        phrase="a bright life vest",
        protects_from={"water"},
        covers={"torso"},
        prep="buckle on a life vest first",
        tail="buckled on the life vest",
    ),
]

CURIOUS_NAMES = ["Milo", "Tess", "Wren", "Pip", "Nell", "Ollie"]
TRAITS = ["curious", "bold", "restless", "bright-eyed"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    name: str
    trait: str
    seed: Optional[int] = None
    params: object | None = None
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


def reasonableness_gate(place: str, challenge: str) -> bool:
    return challenge in _safe_lookup(SETTINGS, place).affords


def ASP_RULES() -> str:
    return r"""
place(P) :- setting(P).
challenge(C) :- challenge_kind(C).
affords(hill,kite). affords(hill,goat). affords(harbor,boat). affords(harbor,kite).
affords(canyon,goat). affords(canyon,rope). affords(fairground,kite). affords(fairground,rope).
valid(P,C) :- affords(P,C).
#show valid/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
        for c in sorted(_safe_lookup(SETTINGS, p).affords):
            lines.append(asp.fact("affords", p, c))
    for c in CHALLENGES:
        lines.append(asp.fact("challenge_kind", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES()}\n{show}\n"


def asp_valid() -> set[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid/2."))
    return set(asp.atoms(model, "valid"))


def asp_verify() -> int:
    py = {(p, c) for p in SETTINGS for c in _safe_lookup(SETTINGS, p).affords}
    cl = asp_valid()
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} pairs).")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about Curiosity and a bend.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--name")
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
    combos = [(p, c) for p in SETTINGS for c in _safe_lookup(SETTINGS, p).affords]
    if getattr(args, "place", None):
        combos = [x for x in combos if x[0] == getattr(args, "place", None)]
    if getattr(args, "challenge", None):
        combos = [x for x in combos if x[1] == getattr(args, "challenge", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, challenge = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(CURIOUS_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, name=name, trait=trait)


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.memes['trait_word']} little {hero.type} who had one "
        f"big habit: whenever a mystery glimmered in the distance, {hero.pronoun()} "
        f"wanted to know what was behind it."
    )
    world.say(
        f"In the middle of the tall tale country, folks said Curiosity could make a broom bend, "
        f"a fence grin, and a cloud stop to listen."
    )


def simulate(world: World, hero: Entity, challenge: Challenge, gear: Gear | None) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"One bright day at {world.place.name}, {hero.id} spotted a {challenge.keyword} "
        f"and felt that old Curiosity tugging at {hero.pronoun('possessive')} sleeve."
    )
    world.say(
        f"{hero.id} wanted to {challenge.verb}, but {hero.pronoun('possessive')} legs "
        f"wanted a safer way."
    )
    hero.memes["desire"] += 1
    if gear:
        world.say(
            f"{hero.pronoun('possessive').capitalize()} grown-up held up {gear.phrase} and said, "
            f'"First we {gear.prep}, then we can go."'
        )
        hero.memes["resist"] += 1
        world.say(
            f"{hero.id} took a deep breath and chose to resist the wild hurry of the moment."
        )
        hero.worn_by = hero.id
    else:
        pass
    hero.meters[challenge.id] = 1.0
    if challenge.id == "kite":
        hero.meters["wind"] = 1.0
    if challenge.id == "boat":
        hero.meters["water"] = 1.0


def ending(world: World, hero: Entity, challenge: Challenge, gear: Gear) -> None:
    if challenge.id == "kite":
        world.say(
            f"Then {hero.id} let the kite rise high as a flag, while the wool gloves kept "
            f"{hero.pronoun('possessive')} fingers warm enough to hold on."
        )
    elif challenge.id == "goat":
        world.say(
            f"Then {hero.id} followed the goat trail one careful step at a time, and the "
            f"sturdy boots kept the stones from pinching {hero.pronoun('possessive')} feet."
        )
    elif challenge.id == "boat":
        world.say(
            f"Then {hero.id} sailed the little boat without leaning too far, and the life vest "
            f"kept the tall water from worrying the rest of {hero.pronoun('object')}."
        )
    else:
        world.say(
            f"Then {hero.id} crossed the rope bridge with the steady hush of {gear.label}, "
            f"and the boards bent but did not break the day."
        )
    world.say(
        f"The whole tall-tale sky seemed to nod: Curiosity had not been chased away; it had "
        f"been taught to bend kindly instead of snapping at the first pull."
    )


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type="child"))
    hero.memes["trait_word"] = params.trait
    hero.memes["curiosity"] = 0.0
    hero.memes["resist"] = 0.0
    challenge = _safe_lookup(CHALLENGES, params.challenge)
    gear = next(g for g in GEAR if challenge.tags & g.protects_from or (
        challenge.id == "boat" and g.id == "vest") or (challenge.id == "goat" and g.id == "boots") or
        (challenge.id == "kite" and g.id == "gloves") or (challenge.id == "rope" and g.id == "boots"))
    world.weather = challenge.weather
    intro(world, hero)
    world.para()
    simulate(world, hero, challenge, gear)
    world.para()
    ending(world, hero, challenge, gear)
    world.facts = {"hero": hero, "challenge": challenge, "gear": gear, "place": world.place}
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, challenge = f["hero"], f["challenge"]
    return [
        f'Write a short tall tale for a child named {hero.id} about Curiosity and the word "{challenge.keyword}".',
        f"Tell a story where {hero.id} wants to {challenge.verb} but learns to resist the wild urge and choose a safer way.",
        f"Create a playful, exaggerated story set at {world.place.name} that ends with {hero.id} successfully {challenge.gerund}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, challenge, gear = f["hero"], f["challenge"], f["gear"]
    return [
        QAItem(
            question=f"What made {hero.id} want to go closer to the {challenge.keyword}?",
            answer=f"Curiosity did. {hero.id} saw the {challenge.keyword} and wanted to find out what the tall-tale fuss was about.",
        ),
        QAItem(
            question=f"How did {hero.id} resist the hurry before {challenge.verb}?",
            answer=f"{hero.id} took a deep breath, listened to the grown-up, and used {gear.label} to choose a safer way first.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{hero.id} was still curious, but {hero.id} had learned to bend that curiosity into careful action instead of wild rushing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to learn, look, and ask questions about something new.",
        ),
        QAItem(
            question="What does it mean to resist something?",
            answer="To resist means to hold back from doing it right away, especially when you want to pause and choose more carefully.",
        ),
        QAItem(
            question="What does it mean when something bends?",
            answer="When something bends, it changes shape a little without breaking, like a branch in the wind or a board under a careful step.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"  {e.id:10} kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def valid_combos() -> list[tuple[str, str]]:
    return [(p, c) for p in SETTINGS for c in _safe_lookup(SETTINGS, p).affords]


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES()}\n{show}\n"


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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid place/challenge pairs:")
        for p, c in combos:
            print(f"  {p:10} {c}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for i, (place, challenge) in enumerate(valid_combos()):
            params = StoryParams(
                place=place,
                challenge=challenge,
                name=_safe_lookup(CURIOUS_NAMES, i % len(CURIOUS_NAMES)),
                trait=_safe_lookup(TRAITS, i % len(TRAITS)),
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "challenge", None):
        combos = [c for c in combos if c[1] == getattr(args, "challenge", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, challenge = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(CURIOUS_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, name=name, trait=trait)


if __name__ == "__main__":
    main()
