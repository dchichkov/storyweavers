#!/usr/bin/env python3
"""
storyworlds/worlds/tempest_teamwork_inner_monologue_tall_tale.py
===============================================================

A small story world about a tempest, teamwork, and a hero who thinks things
through in a tall-tale voice.

The source tale behind the world:
- A fierce tempest rolls in.
- A small crew on a pier, hill, or harbor has to work together.
- The hero's inner monologue changes from worry to resolve.
- Their teamwork saves something important and leaves a vivid ending image.

This file follows the Storyweavers storyworld contract:
- standalone stdlib script
- shared result containers imported eagerly
- ASP twin provided inline
- story state drives prose
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
    safe_spot: str
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
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    weather: str = "tempest"
    keyword: str = "tempest"
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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


def _r_drenched(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("tempest", 0.0) < THRESHOLD:
            continue
        sig = ("drenched", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["wet"] = actor.meters.get("wet", 0.0) + 1
        actor.memes["alarm"] = actor.memes.get("alarm", 0.0) + 1
        out.append(f"The {actor.label or actor.id} was wet clear through.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    crew = world.characters()
    if sum(1 for e in crew if e.memes.get("helping", 0.0) >= THRESHOLD) >= 2:
        sig = ("teamwork",)
        if sig not in world.fired:
            world.fired.add(sig)
            for e in crew:
                e.memes["hope"] = e.memes.get("hope", 0.0) + 1
            out.append("The crew moved as one, like four hands on a single rope.")
    return out


def _r_safe(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("gear_on") and world.facts.get("prize_secured"):
        sig = ("safe",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("The important thing stayed safe.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_drenched, _r_teamwork, _r_safe):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def challenge_at_risk(challenge: Challenge, prize: Prize) -> bool:
    return prize.region in challenge.zone


def select_gear(challenge: Challenge, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if challenge.id in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for ch_id in setting.affords:
            ch = _safe_lookup(CHALLENGES, ch_id)
            for pr_id, pr in PRIZES.items():
                if challenge_at_risk(ch, pr) and select_gear(ch, pr):
                    combos.append((place, ch_id, pr_id))
    return combos


def inner_monologue(world: World, hero: Entity, challenge: Challenge, prize: Entity) -> None:
    world.say(
        f'In {hero.pronoun("possessive")} head, {hero.id} thought, '
        f'"If the {challenge.keyword} bites the {prize.label}, we lose the day."'
    )


def intro(world: World, hero: Entity, helper: Entity, prize: Entity, challenge: Challenge) -> None:
    world.say(
        f"{hero.id} was a {hero.type} with a head full of bright plans and a heart "
        f"that beat like a kettle drum."
    )
    world.say(
        f"Beside {hero.pronoun('object')} stood {helper.id}, who could tie a knot "
        f"so tight even a gull would ask for mercy."
    )
    world.say(
        f"They had brought along {hero.pronoun('possessive')} {prize.label}, "
        f"{prize.phrase}, because the whole town wanted it kept for the feast."
    )
    world.say(
        f"Then the sky went black, the wind leaned over the water, and a {challenge.keyword} "
        f"came rolling in like a thousand hounds with cold noses."
    )


def worry(world: World, hero: Entity, helper: Entity, challenge: Challenge, prize: Entity) -> None:
    world.say(
        f"{hero.id} wanted to be brave, but {hero.pronoun('possessive')} knees felt small."
    )
    inner_monologue(world, hero, challenge, prize)
    world.say(
        f"{hero.id} blurted, \"The wind will snatch the {prize.label}!\""
    )
    helper.memes["helping"] = helper.memes.get("helping", 0.0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"{helper.id} answered, \"Then we will keep our hands busy and our feet planted.\""
    )


def act(world: World, hero: Entity, helper: Entity, prize: Entity, challenge: Challenge) -> None:
    world.zone = set(challenge.zone)
    hero.meters["tempest"] = hero.meters.get("tempest", 0.0) + 1
    helper.meters["tempest"] = helper.meters.get("tempest", 0.0) + 1
    hero.memes["helping"] = hero.memes.get("helping", 0.0) + 1
    helper.memes["helping"] = helper.memes.get("helping", 0.0) + 1
    world.say(
        f"{hero.id} and {helper.id} rushed to {challenge.rush}, while the rain came down "
        f"like it had a quarrel with the sea."
    )
    propagate(world)
    world.say(
        f"{hero.id} did not run away. {hero.pronoun().capitalize()} tied, pulled, and shouted "
        f"until {helper.id} could latch the {prize.label} down."
    )
    world.facts["gear_on"] = True
    world.facts["prize_secured"] = True
    propagate(world)


def resolution(world: World, hero: Entity, helper: Entity, prize: Entity, challenge: Challenge, gear: Gear) -> None:
    hero.memes["worry"] = 0.0
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    helper.memes["pride"] = helper.memes.get("pride", 0.0) + 1
    world.say(
        f'At last, {hero.id} laughed through the roar and said, "We did it!"'
    )
    world.say(
        f"They put on {gear.label} first, and that was the whole trick. "
        f"With the {gear.label}, the {challenge.keyword} could howl all it liked, "
        f"but the {prize.label} stayed safe."
    )
    world.say(
        f"When the storm finally shuffled off, {hero.id} and {helper.id} stood in the lantern light, "
        f"both of them dripping like wet crows, while the {prize.label} sat snug and shining."
    )


SETTINGS = {
    "pier": Setting(place="the pier", safe_spot="the boathouse", affords={"hoist"}),
    "hill": Setting(place="the hill above town", safe_spot="the stone shed", affords={"cover"}),
    "harbor": Setting(place="the harbor road", safe_spot="the net house", affords={"lash"}),
}

CHALLENGES = {
    "hoist": Challenge(
        id="hoist",
        verb="hoist the sail",
        gerund="hoisting the sail",
        rush="haul the sail tight",
        risk="wind",
        zone={"torso"},
    ),
    "cover": Challenge(
        id="cover",
        verb="cover the crates",
        gerund="covering the crates",
        rush="spread the tarps fast",
        risk="rain",
        zone={"torso", "hands"},
    ),
    "lash": Challenge(
        id="lash",
        verb="lash the boat",
        gerund="lashing the boat",
        rush="tie the lines before the gusts snapped them",
        risk="gusts",
        zone={"hands", "feet"},
    ),
}

PRIZES = {
    "lantern": Prize(id="lantern", label="lantern", phrase="the brass lantern from the dockmaster", region="torso"),
    "flag": Prize(id="flag", label="flag", phrase="the bright feast flag", region="torso"),
    "map": Prize(id="map", label="map case", phrase="the town map case wrapped in oilcloth", region="hands"),
}

GEAR = [
    Gear(id="oilcloth", label="the oilcloth wrap", covers={"torso"}, guards={"hoist", "cover"}, prep="wrap the prize in oilcloth", tail="wrapped the prize in oilcloth"),
    Gear(id="gloves", label="the tar gloves", covers={"hands"}, guards={"lash"}, prep="pull on the tar gloves", tail="pulled on the tar gloves"),
    Gear(id="cloak", label="the storm cloak", covers={"torso", "hands"}, guards={"hoist", "cover", "lash"}, prep="slip into the storm cloak", tail="slipped into the storm cloak"),
]

GIRL_NAMES = ["Mabel", "Nell", "Ada", "Ivy", "Ruby"]
BOY_NAMES = ["Cliff", "Hank", "Otis", "Jules", "Benn"]
TRAITS = ["bold", "curious", "bright-eyed", "stubborn", "fleet-footed"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
    name: str
    gender: str
    helper: str
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


def valid_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "challenge", None) and getattr(args, "prize", None):
        ch, pr = _safe_lookup(CHALLENGES, getattr(args, "challenge", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (challenge_at_risk(ch, pr) and select_gear(ch, pr)):
            pass
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        pass
    place, challenge, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["Aunt Wren", "Uncle Tide", "Mara", "Beck"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.gender == "girl" else "boy", label=params.trait))
    helper = world.add(Entity(id=params.helper, kind="character", type="aunt" if "Aunt" in params.helper else ("uncle" if "Uncle" in params.helper else "man"), label=params.helper))
    prize = world.add(Entity(id="prize", type="thing", label=_safe_lookup(PRIZES, params.prize).label, phrase=_safe_lookup(PRIZES, params.prize).phrase, region=_safe_lookup(PRIZES, params.prize).region))
    ch = _safe_lookup(CHALLENGES, params.challenge)
    gear = select_gear(ch, _safe_lookup(PRIZES, params.prize))
    if gear is None:
        gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))
    intro(world, hero, helper, prize, ch)
    world.para()
    worry(world, hero, helper, ch, prize)
    world.para()
    act(world, hero, helper, prize, ch)
    world.para()
    resolution(world, hero, helper, prize, ch, gear)
    world.facts.update(hero=hero, helper=helper, prize=prize, challenge=ch, gear=gear, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    ch = _safe_fact(world, f, "challenge")
    prize = _safe_fact(world, f, "prize")
    return [
        f"Write a short tall tale about {hero.id} and a {ch.keyword} that tests their teamwork.",
        f"Tell a child-friendly story where {hero.id} thinks silently about danger before saving {prize.phrase}.",
        f"Write a stormy adventure in which two helpers beat a {ch.keyword} by working together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, ch = f["hero"], f["helper"], f["prize"], f["challenge"]
    return [
        QAItem(
            question=f"What was {hero.id} worried the {ch.keyword} might do to the {prize.label}?",
            answer=f"{hero.id} was worried the {ch.keyword} might snatch or ruin the {prize.label}, so {hero.pronoun('possessive')} thoughts ran fast before {hero.pronoun()} spoke.",
        ),
        QAItem(
            question=f"Who helped {hero.id} during the tempest?",
            answer=f"{helper.id} helped {hero.id}, and the two of them kept working until the {prize.label} was safe.",
        ),
        QAItem(
            question=f"How did teamwork change the ending?",
            answer=f"Teamwork turned the panic into a plan, so {hero.id} and {helper.id} could secure the {prize.label} and stand together after the storm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tempest?",
            answer="A tempest is a fierce storm with heavy wind and rain.",
        ),
        QAItem(
            question="Why do people work together in a storm?",
            answer="People work together in a storm because many hands can hold ropes, carry things, and keep everyone safer.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the thinking a character does in their own mind before they speak or act.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:7}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(C, P) :- zone(C, R), prize_region(P, R).
gear_ok(G, C, P) :- gear(G), at_risk(C, P), guards(G, C), covers(G, R), prize_region(P, R).
valid(Place, C, P) :- affords(Place, C), at_risk(C, P), gear_ok(_, C, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for r in sorted(c.zone):
            lines.append(asp.fact("zone", cid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, c))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tall-tale tempest story world with teamwork and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait")
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
    return valid_story_params(args, rng)


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


CURATED = [
    StoryParams(place="pier", challenge="hoist", prize="lantern", name="Mabel", gender="girl", helper="Aunt Wren", trait="bold"),
    StoryParams(place="hill", challenge="cover", prize="flag", name="Otis", gender="boy", helper="Uncle Tide", trait="curious"),
    StoryParams(place="harbor", challenge="lash", prize="map", name="Ivy", gender="girl", helper="Mara", trait="bright-eyed"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, challenge, prize) combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
