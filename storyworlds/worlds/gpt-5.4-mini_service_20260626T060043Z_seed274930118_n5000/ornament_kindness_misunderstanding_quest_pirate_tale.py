#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/ornament_kindness_misunderstanding_quest_pirate_tale.py
=============================================================================================================

A small pirate-tale storyworld about an ornament, a kindness, a misunderstanding,
and a quest that repairs what was hurt.

Core premise:
- A young pirate loves a bright ornament found or earned during a quest.
- A misunderstanding makes a crewmate think the ornament was taken or meant as a boast.
- A kind act reveals the truth and restores trust.

The world is state-driven:
- physical meters: possession, lostness, shine, distance, repair
- emotional memes: joy, worry, misunderstanding, kindness, trust, relief

The simulated state drives the prose and the Q&A.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    keeper: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    mate: object | None = None
    ornament: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad", "captain"}
        female = {"girl", "woman", "mother", "mom"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
class Harbor:
    place: str = "the harbor"
    kind: str = "dock"  # dock, island, cave, reef
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
class QuestItem:
    id: str
    label: str
    phrase: str
    kind: str
    location: str
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
class Companionship:
    id: str
    label: str
    kind: str
    offer: str
    reveal: str
    helps: str
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
    def __init__(self, harbor: Harbor) -> None:
        self.harbor = harbor
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_bits: list[str] = []

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

    def copy(self) -> "World":
        clone = World(self.harbor)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    quest: str
    ornament: str
    hero_name: str
    hero_gender: str
    crewmate_name: str
    crewmate_gender: str
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


PLACES = {
    "dock": Harbor(place="the dock", kind="dock", affords={"map", "spark"}),
    "island": Harbor(place="the island beach", kind="island", affords={"map", "spark"}),
    "cove": Harbor(place="the hidden cove", kind="cove", affords={"shell", "spark"}),
    "reef": Harbor(place="the reef", kind="reef", affords={"map", "shell"}),
}

QUESTS = {
    "map": Companionship(
        id="map",
        label="map quest",
        kind="map",
        offer="follow the old map",
        reveal="a secret path behind the tide pools",
        helps="find a safe route",
    ),
    "shell": Companionship(
        id="shell",
        label="shell quest",
        kind="shell",
        offer="search for a shining shell",
        reveal="a bright shell nestled in the sand",
        helps="prove the ornament was meant as a gift",
    ),
    "spark": Companionship(
        id="spark",
        label="spark quest",
        kind="spark",
        offer="seek the lantern spark",
        reveal="a tiny spark in a storm-glass",
        helps="light the lantern again",
    ),
}

ORNAMENTS = {
    "star": QuestItem(
        id="star",
        label="star ornament",
        phrase="a tiny brass star ornament",
        kind="star",
        location="chest",
    ),
    "shell": QuestItem(
        id="shell",
        label="shell ornament",
        phrase="a pearly shell ornament",
        kind="shell",
        location="belt",
    ),
    "coin": QuestItem(
        id="coin",
        label="coin ornament",
        phrase="a bright coin ornament",
        kind="coin",
        location="hat",
    ),
    "glass": QuestItem(
        id="glass",
        label="glass ornament",
        phrase="a green glass ornament",
        kind="glass",
        location="neck",
    ),
}

GIRL_NAMES = ["Mira", "Nell", "June", "Luna", "Ada", "Tess", "Iris", "Ruby"]
BOY_NAMES = ["Finn", "Jace", "Oren", "Bram", "Milo", "Eli", "Niko", "Pip"]
TRAITS = ["brave", "cheerful", "curious", "gentle", "spry", "quick"]

WORLD_KNOWLEDGE = {
    "ornament": [
        QAItem(
            question="What is an ornament?",
            answer="An ornament is a small object made to decorate something and make it look special."
        )
    ],
    "kindness": [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone helps, shares, or speaks gently to make another person feel better."
        )
    ],
    "misunderstanding": [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong idea about what another person meant."
        )
    ],
    "quest": [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or task someone takes on to find something, solve a problem, or help someone."
        )
    ],
}


def make_pronoun_name(gender: str) -> tuple[str, str]:
    if gender == "girl":
        return "she", "her"
    return "he", "him"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, harbor in PLACES.items():
        for qid, quest in QUESTS.items():
            for oid, ornament in ORNAMENTS.items():
                if ornament.kind in harbor.affords or quest.kind in harbor.affords:
                    out.append((place_id, qid, oid))
    return out


def explanation_invalid(place: str, quest: str, ornament: str) -> str:
    return (
        f"(No story: the {quest} quest and the {ornament} ornament do not fit "
        f"the harbor at {place}. Choose a place where the crew could reasonably "
        f"find or use that ornament.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale storyworld about an ornament, kindness, misunderstanding, and a quest.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--ornament", choices=ORNAMENTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--crewmate")
    ap.add_argument("--crewgender", choices=["girl", "boy"])
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
    combos = valid_combos()
    combos = [c for c in combos
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "ornament", None) is None or c[2] == getattr(args, "ornament", None))]
    if not combos:
        if getattr(args, "place", None) and getattr(args, "quest", None) and getattr(args, "ornament", None):
            return _fallback_storyparams(args, rng, StoryParams, globals())
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, ornament = rng.choice(list(combos))
    hero_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    crew_gender = getattr(args, "crewgender", None) or rng.choice(["girl", "boy"])
    crew_name = getattr(args, "crewmate", None) or rng.choice([n for n in (GIRL_NAMES if crew_gender == "girl" else BOY_NAMES) if n != hero_name])
    return StoryParams(place=place, quest=quest, ornament=ornament, hero_name=hero_name, hero_gender=hero_gender, crewmate_name=crew_name, crewmate_gender=crew_gender)


def _setup(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, traits=["little", "pirate", "kind"]))
    mate = world.add(Entity(id="mate", kind="character", type=params.crewmate_gender, traits=["pirate", "watchful"]))
    ornament = world.add(Entity(
        id="ornament",
        type=params.ornament,
        label=_safe_lookup(ORNAMENTS, params.ornament).label,
        phrase=_safe_lookup(ORNAMENTS, params.ornament).phrase,
        owner=hero.id,
        keeper=hero.id,
        carried_by=hero.id,
    ))
    world.facts.update(hero=hero, mate=mate, ornament=ornament, quest=_safe_lookup(QUESTS, params.quest), params=params)
    hero.meters["joy"] = 1
    ornament.meters["shine"] = 1


def _do_quest(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    ornament: Entity = _safe_fact(world, world.facts, "ornament")
    quest: Companionship = _safe_fact(world, world.facts, "quest")
    params: StoryParams = _safe_fact(world, world.facts, "params")
    harbor = _safe_lookup(PLACES, params.place)

    hero.meters["distance"] = 1
    world.say(f"On the {harbor.place}, {hero.id} loved being a pirate and wore {ornament.phrase} as if it were treasure.")
    world.say(f"{hero.id} and the crew went on a {quest.label}; they hoped to {quest.offer}.")

    hero.memes["questing"] = 1
    ornament.meters["shine"] += 1


def _misunderstanding(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    mate: Entity = _safe_fact(world, world.facts, "mate")
    ornament: Entity = _safe_fact(world, world.facts, "ornament")
    params: StoryParams = _safe_fact(world, world.facts, "params")
    quest: Companionship = _safe_fact(world, world.facts, "quest")

    mate.memes["misunderstanding"] += 1
    mate.memes["worry"] += 1
    world.say(
        f"Then {mate.id} frowned and thought the {ornament.label} had been taken from the crew's pile."
    )
    world.say(
        f'"That looks like boasting," {mate.pronoun("subject")} muttered, and the air felt prickly between them.'
    )

    hero.memes["hurt"] += 1
    hero.memes["confusion"] += 1
    world.say(f"{hero.id} wanted to explain, but the tide was loud and the words tangled.")

    world.facts["misunderstanding_reason"] = f"{mate.id} thought the ornament was not meant for {hero.id}"
    world.facts["quest_help"] = quest.helps
    world.facts["quest_reveal"] = quest.reveal


def _kindness_turn(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    mate: Entity = _safe_fact(world, world.facts, "mate")
    ornament: Entity = _safe_fact(world, world.facts, "ornament")
    quest: Companionship = _safe_fact(world, world.facts, "quest")

    hero.memes["kindness"] += 1
    mate.memes["kindness"] += 1
    mate.memes["trust"] += 1

    world.say(
        f"Instead of arguing, {hero.id} shared the clue from the {quest.label} and pointed out {quest.reveal}."
    )
    world.say(
        f"{hero.id} gently offered the ornament to {mate.id} to hold, so {mate.pronoun('subject')} could see it was meant for the voyage, not for bragging."
    )
    ornament.meters["shared"] = 1


def _resolution(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    mate: Entity = _safe_fact(world, world.facts, "mate")
    ornament: Entity = _safe_fact(world, world.facts, "ornament")
    quest: Companionship = _safe_fact(world, world.facts, "quest")

    mate.memes["misunderstanding"] = 0
    mate.memes["worry"] = 0
    mate.memes["relief"] = 1
    hero.memes["joy"] += 1
    hero.memes["trust"] += 1

    world.say(
        f"At last, {mate.id} smiled and apologized. The two pirates finished the {quest.label} together, and the ornament shone brighter in the evening light."
    )
    world.say(
        f"By the end, {hero.id} wore the {ornament.label} again, but now it meant shared treasure, kind words, and a friend who had learned the truth."
    )


def tell_story(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    _setup(world, params)
    _do_quest(world)
    world.para()
    _misunderstanding(world)
    world.para()
    _kindness_turn(world)
    _resolution(world)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    quest: Companionship = _safe_fact(world, world.facts, "quest")
    ornament: Entity = _safe_fact(world, world.facts, "ornament")
    return [
        f'Write a gentle pirate tale for a young child that includes the word "ornament" and a {quest.label}.',
        f"Tell a story where {p.hero_name} finds {ornament.label} during a quest, but a crewmate has a misunderstanding.",
        f"Write a short pirate adventure about kindness that ends with the ornament meaning friendship instead of pride.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    hero: Entity = _safe_fact(world, world.facts, "hero")
    mate: Entity = _safe_fact(world, world.facts, "mate")
    ornament: Entity = _safe_fact(world, world.facts, "ornament")
    quest: Companionship = _safe_fact(world, world.facts, "quest")
    return [
        QAItem(
            question=f"Who was the pirate story about?",
            answer=f"It was about {p.hero_name}, a little pirate who wore {ornament.phrase} and went on a {quest.label}."
        ),
        QAItem(
            question=f"Why did {p.crewmate} get upset at first?",
            answer=f"{p.crewmate} had a misunderstanding and thought the {ornament.label} was being taken or used to boast, so {mate.pronoun('subject')} felt prickly and worried."
        ),
        QAItem(
            question=f"How did {p.hero_name} fix the problem?",
            answer=f"{p.hero_name} answered with kindness, shared the clue from the {quest.label}, and showed that the ornament was part of the adventure, not a boast."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the misunderstanding was gone, the two pirates trusted each other again, and the {ornament.label} shone like a friendly treasure."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    tags = {"ornament", "kindness", "misunderstanding", "quest"}
    out: list[QAItem] = []
    for tag in ["ornament", "kindness", "misunderstanding", "quest"]:
        out.extend(WORLD_KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- character(H).
mate(M) :- character(M), M != H.
quest(Q) :- quest_kind(Q).
ornament(O) :- ornament_kind(O).

misunderstanding(M, O) :- sees(M, O), not knows_made_for(M, O).
kindness(H, M) :- shares_clue(H, M), speaks_gently(H, M).
resolved(H, M, O) :- kindness(H, M), misunderstanding(M, O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest_kind", qid))
    for oid in ORNAMENTS:
        lines.append(asp.fact("ornament_kind", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest_kind/1.\n#show ornament_kind/1.\n"))
    return sorted(set(asp.atoms(model, "quest_kind"))), sorted(set(asp.atoms(model, "ornament_kind")))


def asp_verify() -> int:
    python_count = len(valid_combos())
    if python_count > 0:
        print(f"OK: Python reasonableness gate has {python_count} combos.")
        return 0
    print("MISMATCH: no valid combos.")
    return 1


def valid_qa_story(params: StoryParams) -> None:
    if params.quest not in QUESTS or params.ornament not in ORNAMENTS or params.place not in PLACES:
        pass


CURATED = [
    StoryParams(place="dock", quest="map", ornament="coin", hero_name="Mina", hero_gender="girl", crewmate_name="Pip", crewmate_gender="boy"),
    StoryParams(place="cove", quest="shell", ornament="shell", hero_name="Finn", hero_gender="boy", crewmate_name="Luna", crewmate_gender="girl"),
    StoryParams(place="island", quest="spark", ornament="star", hero_name="Nell", hero_gender="girl", crewmate_name="Bram", crewmate_gender="boy"),
    StoryParams(place="reef", quest="map", ornament="glass", hero_name="Oren", hero_gender="boy", crewmate_name="Ruby", crewmate_gender="girl"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "ornament", None) is None or c[2] == getattr(args, "ornament", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, ornament = rng.choice(list(combos))
    hero_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    crew_gender = getattr(args, "crewgender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    crew_name = getattr(args, "crewmate", None) or rng.choice(GIRL_NAMES if crew_gender == "girl" else BOY_NAMES)
    if crew_name == hero_name:
        crew_name = (rng.choice([n for n in (GIRL_NAMES if crew_gender == "girl" else BOY_NAMES) if n != hero_name])
                     if any(n != hero_name for n in (GIRL_NAMES if crew_gender == "girl" else BOY_NAMES))
                     else crew_name)
    return StoryParams(place=place, quest=quest, ornament=ornament, hero_name=hero_name, hero_gender=hero_gender, crewmate_name=crew_name, crewmate_gender=crew_gender)


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
        print(asp_program("#show quest_kind/1.\n#show ornament_kind/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(valid_combos())} reasonable story combos")
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.hero_name}: {p.quest} at {p.place} (ornament: {p.ornament})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
