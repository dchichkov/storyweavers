#!/usr/bin/env python3
"""
storyworlds/worlds/muscular_cranapple_quest_inner_monologue_dialogue_rhyming.py
===============================================================================

A small rhyming storyworld about a muscular hero, a cranapple, and a quest.

Seed tale premise:
- A muscular little squirrel wants a special cranapple for a rhyme contest.
- The cranapple rolls away, so the squirrel follows clues, thinks aloud, and talks
  with a helper.
- The quest ends when strength is used gently and the cranapple is shared.

World model:
- Physical meters track tiredness, distance, fruit freshness, and pulled weight.
- Emotional memes track hope, worry, pride, and relief.
- The story is driven by state changes, not a frozen paragraph.

Narrative instruments:
- Quest: the hero must search for the cranapple.
- Inner Monologue: the hero thinks in rhyme while deciding what to do.
- Dialogue: a helper speaks, and the hero answers.

Style:
- Rhyming, child-facing, concrete, and complete.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    plural: bool = False
    owner: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    rel: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "squirrel-girl"}
        male = {"boy", "squirrel-boy", "squirrel"}
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
    kind: str
    trails: list[str] = field(default_factory=list)
    hideouts: list[str] = field(default_factory=list)
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
class Quest:
    id: str
    goal: str
    quest_word: str
    clue: str
    action: str
    rhyme_end: str
    risky: bool = True
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
class Relic:
    id: str
    label: str
    phrase: str
    freshness: str
    sweetness: str
    region: str = "basket"
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
class Helper:
    id: str
    type: str
    label: str
    line: str
    counsel: str
    rhyme: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def hero_mood_line(hero: Entity) -> str:
    if hero.memes.get("hope", 0) >= THRESHOLD and hero.memes.get("worry", 0) >= THRESHOLD:
        return "He felt a tug in his chest, both hopeful and pressed."
    if hero.memes.get("relief", 0) >= THRESHOLD:
        return "He felt light as a feather, as if all the clouds had fled together."
    return "He kept his brave little beat, with dust on his feet."


def quest_intro(world: World, hero: Entity, relic: Relic, quest: Quest) -> None:
    world.say(
        f"{hero.id} was muscular and merry, a squirrel quick and wary. "
        f"He wanted the {relic.label}, a cranapple bright and grand, "
        f"for a rhyme contest in the land."
    )
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(
        f"{hero.id} set out on a {quest.quest_word}, with strong little paws and a steady stride. "
        f"{hero.pronoun().capitalize()} would not quit, not even after the cranapple slid."
    )


def find_clue(world: World, hero: Entity, quest: Quest) -> None:
    hero.meters["distance"] = hero.meters.get("distance", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"Near a mossy stump, {hero.id} found a clue: "
        f"{quest.clue}. The trail went up, then down, then through."
    )


def inner_monologue(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["thoughtful"] = hero.memes.get("thoughtful", 0) + 1
    world.say(
        f'He whispered inside, "I am strong, I am small, I can climb any wall. '
        f'If I move with care, I will win this fair."'
    )
    world.say(
        f"{hero.id} did not rush and did not boast; he looked for the path that helped the most."
    )


def dialogue(world: World, hero: Entity, helper: Helper, quest: Quest) -> None:
    world.say(f'{helper.label} said, "{helper.line}"')
    world.say(f'{hero.id} answered, "I hear your tune; I will be back with the cranapple soon."')
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1


def risky_pull(world: World, hero: Entity, relic: Relic, quest: Quest) -> None:
    hero.meters["pull"] = hero.meters.get("pull", 0) + 1
    hero.meters["tired"] = hero.meters.get("tired", 0) + 1
    if hero.meters["pull"] >= THRESHOLD and relic.freshness != "safe":
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        world.say(
            f"{hero.id} tried to tug the cranapple fast, but the stem bent with a crack. "
            f"The shiny fruit could bruise if he used too much force."
        )


def careful_fix(world: World, hero: Entity, relic: Relic, helper: Helper) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["worry"] = 0.0
    relic.freshness = "safe"
    world.say(
        f"{hero.id} slowed his pull, then used a soft hold and a gentle goal. "
        f"{helper.label} nodded, and the cranapple came free whole."
    )


def ending(world: World, hero: Entity, relic: Relic, quest: Quest, helper: Helper) -> None:
    world.say(
        f"At last, {hero.id} held the cranapple high, red as a sunset in the sky. "
        f"{hero.pronoun().capitalize()} shared it with {helper.label}, and both of them laughed clear and bright."
    )
    world.say(
        f"The quest was done, the rhyme had won, and the little muscular squirrel went home under the moonlight."
    )


SETTINGS = {
    "orchard": Place(
        name="the orchard",
        kind="outdoor",
        trails=["moss", "root", "lane"],
        hideouts=["barrel", "branch", "bush"],
    ),
    "meadow": Place(
        name="the meadow",
        kind="outdoor",
        trails=["daisy", "hill", "brook"],
        hideouts=["rock", "reed", "nest"],
    ),
}

QUESTS = {
    "cranapple_quest": Quest(
        id="cranapple_quest",
        goal="find the cranapple",
        quest_word="quest",
        clue="a red peel near the roots",
        action="search",
        rhyme_end="bright and light",
    )
}

RELICS = {
    "cranapple": Relic(
        id="cranapple",
        label="cranapple",
        phrase="a bright cranapple",
        freshness="fresh",
        sweetness="tart-sweet",
    )
}

HELPERS = {
    "crow": Helper(
        id="crow",
        type="bird",
        label="Crow",
        line="Take the slow road; the fruit will stay whole if your paws are bold but mellow.",
        counsel="care is the key",
        rhyme="slow and low",
    ),
    "mouse": Helper(
        id="mouse",
        type="mouse",
        label="Mouse",
        line="A gentle grip is quicker than a clumsy slip.",
        counsel="slow down",
        rhyme="soft and light",
    ),
}

HERO_NAMES = ["Milo", "Pip", "Toby", "Nico", "Fenn", "Otis", "Bram", "Kip"]


@dataclass
class StoryParams:
    place: str
    quest: str
    relic: str
    helper: str
    name: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming quest storyworld with a muscular hero and a cranapple.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("--relic", choices=sorted(RELICS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--name")
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


def _valid_combo(place: str, quest: str, relic: str, helper: str) -> bool:
    return place in SETTINGS and quest in QUESTS and relic in RELICS and helper in HELPERS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        (p, q, r, h)
        for p in SETTINGS
        for q in QUESTS
        for r in RELICS
        for h in HELPERS
    ]
    combos = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
        and (getattr(args, "relic", None) is None or c[2] == getattr(args, "relic", None))
        and (getattr(args, "helper", None) is None or c[3] == getattr(args, "helper", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, relic, helper = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    return StoryParams(place=place, quest=quest, relic=relic, helper=helper, name=name)


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(SETTINGS, params.place)
    quest = _safe_lookup(QUESTS, params.quest)
    relic = _safe_lookup(RELICS, params.relic)
    helper = _safe_lookup(HELPERS, params.helper)

    world = World(place)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="squirrel",
        label=params.name,
        meters={"distance": 0.0, "tired": 0.0, "pull": 0.0},
        memes={"hope": 0.0, "worry": 0.0, "pride": 0.0, "relief": 0.0},
    ))
    rel = world.add(Entity(
        id=relic.id,
        type="thing",
        label=relic.label,
        phrase=relic.phrase,
    ))

    quest_intro(world, hero, rel, quest)
    world.para()
    find_clue(world, hero, quest)
    inner_monologue(world, hero, quest)
    dialogue(world, hero, helper, quest)
    risky_pull(world, hero, rel, quest)
    careful_fix(world, hero, rel, helper)
    world.para()
    ending(world, hero, rel, quest, helper)

    world.facts.update(hero=hero, relic=rel, quest=quest, helper=helper, place=place)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    quest = _safe_fact(world, f, "quest")
    relic = _safe_fact(world, f, "relic")
    helper = _safe_fact(world, f, "helper")
    return [
        f'Write a rhyming story for a young child about a muscular squirrel on a {quest.quest_word} for a {relic.label}.',
        f'Tell a gentle quest story with inner monologue and dialogue where {hero.id} learns to be strong and careful.',
        f'Write a short rhyming adventure ending with a shared {relic.label} and a happy homecoming.',
        f'Use the words "muscular" and "{relic.label}" in a story with a clue, a helper, and a safe finish.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    quest = _safe_fact(world, f, "quest")
    relic = _safe_fact(world, f, "relic")
    helper = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"What was {hero.id} looking for on the quest?",
            answer=f"{hero.id} was looking for the {relic.label}. The whole quest was about finding that shiny cranapple and bringing it home safely.",
        ),
        QAItem(
            question=f"Why did {hero.id} slow down instead of pulling hard?",
            answer=f"{hero.id} slowed down because a hard pull could bruise the {relic.label}. Using a gentle hold kept the fruit fresh and safe.",
        ),
        QAItem(
            question=f"Who helped {hero.id} on the quest?",
            answer=f"{helper.label} helped {hero.id}. The helper gave calm advice, and that advice pointed {hero.id} toward the safe way to finish the quest.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and the cranapple?",
            answer=f"The story ended with {hero.id} sharing the {relic.label} with {helper.label}. The quest was finished, and everyone felt glad and proud.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or journey to find something important or to finish a special goal.",
        ),
        QAItem(
            question="What does it mean to be muscular?",
            answer="Being muscular means having strong muscles that can help you lift, pull, run, or carry things.",
        ),
        QAItem(
            question="What is a cranapple?",
            answer="A cranapple is a made-up fruit name in this storyworld. It sounds like a fruit that is bright, round, and tasty.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the little voice a character thinks in their head when they are deciding what to do.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is when characters speak to each other in the story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
place(orchard).
place(meadow).
quest(cranapple_quest).
relic(cranapple).
helper(crow).
helper(mouse).

valid(P,Q,R,H) :- place(P), quest(Q), relic(R), helper(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for r in RELICS:
        lines.append(asp.fact("relic", r))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid())
    python_set = set((p, q, r, h) for p in SETTINGS for q in QUESTS for r in RELICS for h in HELPERS)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


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
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid()
        print(f"{len(vals)} compatible combinations:")
        for p, q, r, h in vals:
            print(f"  {p:8} {q:15} {r:10} {h}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in SETTINGS:
            for q in QUESTS:
                for r in RELICS:
                    for h in HELPERS:
                        params = StoryParams(place=p, quest=q, relic=r, helper=h, name="Milo")
                        samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
