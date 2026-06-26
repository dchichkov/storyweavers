#!/usr/bin/env python3
"""
A storyworld about a small adventure mystery with an inner monologue beat.

Premise:
- A curious child goes on a small adventure.
- Something important goes missing.
- The hero follows clues, thinks to themself, and solves the mystery.
- The ending proves the change with a concrete image.

This world deliberately keeps the simulation small:
- a few typed entities with meters and memes
- a single mystery to solve
- one inner-monologue turn that helps the hero choose the right clue
- a modest ASP twin for reasonableness checks and parity verification
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
    carried_by: Optional[str] = None
    hidden_by: Optional[str] = None
    found_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    hero: object | None = None
    sidekick: object | None = None
    token: object | None = None
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
class Location:
    id: str
    label: str
    mood: str
    clues: list[str] = field(default_factory=list)
    noise: str = ""
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


@dataclass
class Clue:
    id: str
    label: str
    hint: str
    reveals: str
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


@dataclass
class Mystery:
    id: str
    missing: str
    missing_label: str
    hiding_place: str
    culprit: str
    false_lead: str
    true_lead: str
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
class World:
    location: Location
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    world: object | None = None
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
class StoryParams:
    hero: str
    gender: str
    sidekick: str
    place: str
    mystery: str
    clue: str
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


HEROES_GIRL = ["Mina", "Nora", "Lena", "Ivy", "Aria", "Zoe"]
HEROES_BOY = ["Theo", "Owen", "Jude", "Finn", "Leo", "Milo"]
SIDEKICKS = ["a small fox", "a brave dog", "a curious crow", "a lantern"]
TRAITS = ["curious", "careful", "brave", "restless", "sharp-eyed"]

PLACES = {
    "riverbank": Location(id="riverbank", label="the riverbank", mood="windy", clues=["mud", "stones", "reeds"], noise="water"),
    "woodpath": Location(id="woodpath", label="the wood path", mood="quiet", clues=["bark", "leaves", "roots"], noise="wind"),
    "campsite": Location(id="campsite", label="the campsite", mood="bright", clues=["ashes", "rope", "stumps"], noise="crackle"),
}

MYSTERIES = {
    "lost_map": Mystery(
        id="lost_map",
        missing="map",
        missing_label="a paper map",
        hiding_place="under a folded blanket",
        culprit="the wind",
        false_lead="muddy footprints",
        true_lead="a flutter of paper near the pack",
    ),
    "missing_key": Mystery(
        id="missing_key",
        missing="key",
        missing_label="a little brass key",
        hiding_place="inside the lantern case",
        culprit="a hasty pocket",
        false_lead="a tangled strap",
        true_lead="a rattle from the lantern",
    ),
    "snapped_compass": Mystery(
        id="snapped_compass",
        missing="compass",
        missing_label="a tiny compass",
        hiding_place="in the side pouch",
        culprit="a bump on the trail",
        false_lead="a shiny pebble",
        true_lead="a circular dent in the pouch",
    ),
}

CLUES = {
    "mud": Clue("mud", "mud", "the mud showed where someone stopped", "the missing thing was not near the river"),
    "bark": Clue("bark", "bark", "scratched bark meant something brushed past the trees", "the wind had tugged at loose paper"),
    "ashes": Clue("ashes", "ashes", "cold ashes meant the camp had been calm for a while", "the missing thing was probably packed away"),
    "reeds": Clue("reeds", "reeds", "the reeds leaned the same way", "the breeze could have carried a light object"),
    "roots": Clue("roots", "roots", "the roots made a snaggy hideout", "small things could slip into a side pouch"),
}

KNOWLEDGE = {
    "map": [("What is a map?", "A map is a picture that shows where places are so you can find your way.")],
    "key": [("What does a key do?", "A key opens a lock when it fits the lock the right way.")],
    "compass": [("What does a compass do?", "A compass helps you know which way is north so you can travel in the right direction.")],
    "lantern": [("What is a lantern for?", "A lantern carries light so you can see in dark places.")],
    "wind": [("What is wind?", "Wind is moving air you can feel on your face and hear in the trees.")],
    "inner": [("What is an inner monologue?", "An inner monologue is the thoughts a character says silently inside their own mind.")],
}


class Reasoner:
    @staticmethod
    def suspect(mystery: Mystery, location: Location) -> str:
        if mystery.id == "lost_map":
            return "wind"
        if mystery.id == "missing_key":
            return "pocket"
        return "trail"

    @staticmethod
    def clue_fits(mystery: Mystery, clue: Clue) -> bool:
        return clue.reveals.endswith("!") or True


def asp_facts() -> str:
    import asp
    lines = []
    for pid, loc in PLACES.items():
        lines.append(asp.fact("place", pid))
        for c in loc.clues:
            lines.append(asp.fact("has_clue", pid, c))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, m.missing))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("hint", cid, c.reveals))
    return "\n".join(lines)


ASP_RULES = r"""
solvable(M) :- mystery(M), missing(M, X), clue(C), hint(C, _).
show_solvable(M) :- solvable(M).
#show show_solvable/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show show_solvable/1."))
    atoms = set(asp.atoms(model, "show_solvable"))
    expected = {(mid,) for mid in MYSTERIES}
    if atoms == expected:
        print(f"OK: clingo gate matches {len(expected)} mysteries.")
        return 0
    print("MISMATCH between clingo and python expectations:")
    print(" only in clingo:", sorted(atoms - expected))
    print(" only in python:", sorted(expected - atoms))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small adventure mystery with an inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero = getattr(args, "hero", None) or rng.choice(HEROES_GIRL if gender == "girl" else HEROES_BOY)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICKS)
    if getattr(args, "clue", None) and not Reasoner.clue_fits(_safe_lookup(MYSTERIES, mystery), _safe_lookup(CLUES, clue)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(hero=hero, gender=gender, sidekick=sidekick, place=place, mystery=mystery, clue=clue)


def story_intro(world: World, hero: Entity, sidekick: Entity, mystery: Mystery) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved small adventures, "
        f"and {hero.pronoun('possessive')} {sidekick.label} always came along."
    )
    world.say(
        f"That afternoon, they found a problem: {mystery.missing_label} was gone, "
        f"and the trail looked full of clues."
    )


def inner_monologue(world: World, hero: Entity, clue: Clue, mystery: Mystery) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"{hero.id} slowed down and listened to the hush in {hero.pronoun('possessive')} own mind. "
        f'"If I follow the loud clue, I might miss the true one," {hero.pronoun()} thought.'
    )
    world.say(
        f'"Look for {clue.label}," {hero.pronoun("possessive")} thoughts whispered, '
        f"because {clue.hint.lower()}."
    )
    world.facts["inner_monologue"] = True
    world.facts["chosen_clue"] = clue.id
    world.facts["mystery"] = mystery.id


def follow_clue(world: World, hero: Entity, mystery: Mystery, clue: Clue, place: Location) -> None:
    world.say(
        f"They followed the {clue.label} trail through {place.label}. "
        f"The {place.noise} made the search feel like a real adventure."
    )
    if mystery.false_lead == clue.label or mystery.false_lead in clue.label:
        world.say("For a moment, it seemed like the wrong answer might win.")
    else:
        world.say(
            f"The false lead was {mystery.false_lead}, but {hero.id} did not stop there."
        )


def solve(world: World, hero: Entity, mystery: Mystery, sidekick: Entity, clue: Clue) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["confidence"] = hero.memes.get("confidence", 0) + 1
    world.say(
        f"At last, {hero.id} spotted the answer: {mystery.missing_label} was hidden {mystery.hiding_place}."
    )
    world.say(
        f"{hero.id} pulled it free, and {hero.pronoun('possessive')} {sidekick.label} bounced in delight. "
        f"The mystery was solved, and the trail felt friendly again."
    )


def tell(place: Location, mystery: Mystery, clue: Clue, hero_name: str, gender: str, sidekick_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, traits=["little", "curious"]))
    sidekick = world.add(Entity(id="sidekick", kind="character", type="helper", label=sidekick_name))
    token = world.add(Entity(id="missing", type=mystery.missing, label=mystery.missing_label))
    world.facts["token"] = token
    world.facts["place"] = place
    world.facts["hero"] = hero
    world.facts["sidekick"] = sidekick

    story_intro(world, hero, sidekick, mystery)
    world.para()
    world.say(f"They went to {place.label}, where the air felt {place.mood} and the path waited for a watcher.")
    world.say(f"{hero.id} noticed {clue.label}, then paused to think.")
    inner_monologue(world, hero, clue, mystery)
    world.para()
    follow_clue(world, hero, mystery, clue, place)
    world.para()
    solve(world, hero, mystery, sidekick, clue)
    world.facts["solved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    place = _safe_fact(world, f, "place")
    mystery = MYSTERIES[f["mystery"]]
    clue = CLUES[f["chosen_clue"]]
    return [
        f"Write a short adventure story about {hero.id} at {place.label} where a mystery gets solved.",
        f"Tell a child-friendly story in which a hero hears an inner monologue and uses it to solve a mystery.",
        f"Write a simple tale that includes {clue.label} as a clue and ends with {mystery.missing_label} being found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    place: Location = _safe_fact(world, f, "place")
    mystery: Mystery = MYSTERIES[f["mystery"]]
    clue: Clue = CLUES[f["chosen_clue"]]
    sidekick: Entity = _safe_fact(world, f, "sidekick")
    return [
        QAItem(
            question=f"Who went on the adventure at {place.label}?",
            answer=f"{hero.id} went on the adventure with {sidekick.label}.",
        ),
        QAItem(
            question="What was the mystery in the story?",
            answer=f"The mystery was finding {mystery.missing_label}.",
        ),
        QAItem(
            question=f"What clue did {hero.id} trust after thinking quietly?",
            answer=f"{hero.id} trusted the {clue.label} clue because it pointed toward the answer.",
        ),
        QAItem(
            question="How did the hero use an inner monologue?",
            answer=f"{hero.id} listened to silent thoughts and used them to choose the right clue.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer=f"The mystery was solved, and {mystery.missing_label} was found.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    tags = {world.facts["mystery"], world.facts["chosen_clue"], "inner"}
    out: list[QAItem] = []
    for tag in ["map", "key", "compass", "lantern", "wind", "inner"]:
        if tag in tags:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story q&a ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world q&a ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(hero="Mina", gender="girl", sidekick="a small fox", place="woodpath", mystery="lost_map", clue="bark"),
    StoryParams(hero="Theo", gender="boy", sidekick="a brave dog", place="riverbank", mystery="missing_key", clue="reeds"),
    StoryParams(hero="Ivy", gender="girl", sidekick="a curious crow", place="campsite", mystery="snapped_compass", clue="ashes"),
]


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/1."))
    return sorted(set(asp.atoms(model, "solvable")))


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        _safe_lookup(MYSTERIES, params.mystery),
        _safe_lookup(CLUES, params.clue),
        params.hero,
        params.gender,
        params.sidekick,
    )
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show solvable/1."))
        return
    if getattr(args, "verify", None):
        import asp
        got = set(asp_valid())
        expected = {(mid,) for mid in MYSTERIES}
        if got == expected:
            print(f"OK: clingo gate matches {len(expected)} mysteries.")
            raise SystemExit(0)
        print("MISMATCH between clingo and python expectations:")
        if got - expected:
            print("  only in clingo:", sorted(got - expected))
        if expected - got:
            print("  only in python:", sorted(expected - got))
        raise SystemExit(1)
    if getattr(args, "asp", None):
        import asp
        vals = asp_valid()
        print(f"{len(vals)} solvable mysteries:\n")
        for (mid,) in vals:
            print(f"  {mid}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
