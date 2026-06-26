#!/usr/bin/env python3
"""
storyworlds/worlds/neck_tidal_pool_surprise_nursery_rhyme.py
=============================================================

A tiny story world in a nursery-rhyme style: a child at a tidal pool,
a neck-worn treasure, and a small surprise that turns worry into wonder.

The world is intentionally small and constraint-checked. The child wants to
lean close to the tide pool to look for a surprise under the rocks, but the
neck-worn treasure could be splashed and spoiled. A simple, compatible fix
keeps the treasure safe and lets the child enjoy the surprise.

This world uses two numeric dimensions on entities:
- meters: physical conditions like wetness, salt, and splash
- memes: feelings like joy, worry, surprise, and calm
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    child: object | None = None
    necklace: object | None = None
    parent: object | None = None
    scarf: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the tidal pool"
    sight: str = "the tide was leaving little windows of water behind"
    affords: set[str] = field(default_factory=lambda: {"peek", "search"})
    SETTING: object | None = None
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = "surprise"
    ACTIVITY: object | None = None
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
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    PRIZE: object | None = None
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
    GEAR: object | None = None
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


ACTIVITY = Activity(
    id="peek",
    verb="peek under the rocks",
    gerund="peeking under rocks",
    rush="lean too close to the tide",
    mess="wet",
    soil="wet and salty",
    zone={"neck", "torso"},
    keyword="surprise",
)

SETTING = Setting()

PRIZE = Prize(
    label="shell necklace",
    phrase="a bright shell necklace with a blue string",
    type="necklace",
    region="neck",
)

GEAR = Gear(
    id="tuck",
    label="a soft scarf",
    covers={"neck"},
    guards={"wet"},
    prep="tuck the shell necklace safely under a soft scarf first",
    tail="tucked the necklace under the soft scarf",
)

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora"]
BOY_NAMES = ["Pip", "Finn", "Noah", "Leo", "Theo", "Max"]
TRAITS = ["tiny", "brave", "curious", "cheery", "bouncy"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    if activity.mess in GEAR.guards and prize.region in GEAR.covers:
        return GEAR
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    if prize_at_risk(ACTIVITY, PRIZE) and select_gear(ACTIVITY, PRIZE):
        return [(SETTING.place, ACTIVITY.id, "necklace")]
    return []


def explain_rejection() -> str:
    return "(No story: this tidal-pool surprise only works if the necklace is truly at risk and the scarf can cover the neck.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A nursery-rhyme story world about a tidal pool surprise and a treasure at the neck."
    )
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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


@dataclass
class StoryParams:
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, trait=trait)


def _init_entity_meters() -> dict[str, float]:
    return {"wet": 0.0, "salt": 0.0, "joy": 0.0, "worry": 0.0, "surprise": 0.0, "calm": 0.0}


def _init_entity_memes() -> dict[str, float]:
    return {"joy": 0.0, "worry": 0.0, "surprise": 0.0, "calm": 0.0, "curiosity": 0.0}


def _do_peek(world: World, child: Entity, prize: Entity, narrate: bool = True) -> None:
    world.zone = set(ACTIVITY.zone)
    child.meters["curiosity"] += 1
    child.memes["surprise"] += 1
    child.meters["wet"] += 1
    if narrate:
        world.say(f"{child.id} peeped and peered, where the little tide pools twinkled clear.")


def _soak(world: World) -> list[str]:
    out: list[str] = []
    for child in world.characters():
        if child.meters["wet"] < THRESHOLD:
            continue
        for item in world.worn_items(child):
            if item.protective or item.region not in world.zone or world.covered(child, item.region):
                continue
            sig = ("soak", child.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] = item.meters.get("wet", 0.0) + 1
            item.meters["salt"] = item.meters.get("salt", 0.0) + 1
            child.memes["worry"] += 1
            out.append(f"{item.label.capitalize()} got wet and salty.")
    return out


def propagate(world: World, narrate: bool = True) -> None:
    lines = _soak(world)
    if narrate:
        for line in lines:
            world.say(line)


def tell(name: str, gender: str, trait: str) -> World:
    world = World(SETTING)
    child = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        meters=_init_entity_meters(),
        memes=_init_entity_memes(),
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type="mother",
        label="the parent",
        meters=_init_entity_meters(),
        memes=_init_entity_memes(),
    ))
    necklace = world.add(Entity(
        id="Necklace",
        type="necklace",
        label="shell necklace",
        phrase="a bright shell necklace with a blue string",
        owner=child.id,
        caretaker=parent.id,
        region="neck",
        meters=_init_entity_meters(),
        memes=_init_entity_memes(),
    ))

    child.memes["curiosity"] += 1
    necklace.worn_by = child.id

    world.say(f"At the tidal pool, {name} was a {trait} little {gender} with a shell necklace.")
    world.say("The tide went out, the tide came near, and tiny pools flashed like mirrors there.")
    world.say(f"{name} loved to listen for a surprise, for the tide pool kept such merry secrets.")

    world.para()
    world.say(f"{name} wanted to {ACTIVITY.verb}, and the {SETTING.sight}.")
    world.say(f"But {name}'s {parent_label(parent)} worried that {PRIZE.label} might get {ACTIVITY.soil}.")

    child.memes["worry"] += 1
    _do_peek(world, child, necklace)
    world.say(f"{name} leaned in close, and a little wave kissed {name}'s neck and shoulders.")
    propagate(world, narrate=True)

    world.para()
    gear = select_gear(ACTIVITY, PRIZE)
    if gear is None:
        gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))

    if child.memes["worry"] >= THRESHOLD:
        world.say(f"Then {parent_label(parent)} smiled and said, '{gear.prep}.'")
        scarf = world.add(Entity(
            id="Scarf",
            type="scarf",
            label="soft scarf",
            protective=True,
            covers=set(gear.covers),
            meters=_init_entity_meters(),
            memes=_init_entity_memes(),
        ))
        scarf.worn_by = child.id
        necklace.worn_by = child.id
        child.memes["worry"] = 0.0
        child.memes["joy"] += 1
        child.memes["calm"] += 1
        world.say(f"{name} nodded, and {name} {gear.tail}.")
        world.say(
            f"Then {name} peered under the rocks, and there was the surprise: "
            f"a tiny crab in a shiny shell, clapping its little claws."
        )
        world.say(
            f"{name} laughed a bright laugh. The shell necklace stayed dry enough, "
            f"and the tide pool stayed merry."
        )
    world.facts.update(
        child=child,
        parent=parent,
        necklace=necklace,
        gear=gear,
        trait=trait,
    )
    return world


def parent_label(parent: Entity) -> str:
    return "mom" if parent.type == "mother" else "dad"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    return [
        "Write a short nursery-rhyme story about a tidal pool surprise and a treasure at the neck.",
        f"Tell a gentle rhyme where {child.id} leans near the tidal pool, worries about a shell necklace, and finds a surprise.",
        "Make a child-friendly story with tide, rocks, a soft scarf, and a happy little ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    necklace = _safe_fact(world, f, "necklace")
    gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {child.id}, a small child at the tidal pool, and {parent_label(parent)} beside {child.pronoun('object')}.",
        ),
        QAItem(
            question=f"What treasure did {child.id} wear on {child.pronoun('possessive')} neck?",
            answer=f"{child.id} wore a shell necklace with a blue string on {child.pronoun('possessive')} neck.",
        ),
        QAItem(
            question=f"What helped keep the shell necklace safe?",
            answer=f"A soft scarf helped keep the shell necklace safe by covering the neck from the wet splash.",
        ),
        QAItem(
            question=f"What was the surprise at the end?",
            answer="A tiny crab in a shiny shell was the surprise at the end.",
        ),
        QAItem(
            question=f"How did {child.id} feel after the surprise?",
            answer=f"{child.id} felt happy and calm, because the necklace stayed safe and the little crab made everyone laugh.",
        ),
        QAItem(
            question=f"Why did {parent_label(parent)} worry at first?",
            answer=f"{parent_label(parent).capitalize()} worried because the shell necklace could get wet and salty when {child.id} leaned close to the tide pool.",
        ),
        QAItem(
            question=f"What did the soft scarf cover?",
            answer="The soft scarf covered the neck.",
        ),
    ]


KNOWLEDGE = [
    QAItem(
        question="What is a tidal pool?",
        answer="A tidal pool is a small pool of seawater left behind when the tide goes out.",
    ),
    QAItem(
        question="What is a surprise?",
        answer="A surprise is something you do not expect, so it can make you gasp, smile, or laugh.",
    ),
    QAItem(
        question="What does a scarf do?",
        answer="A scarf is soft cloth you wear around your neck to keep it warm or to cover it.",
    ),
    QAItem(
        question="Why can sea water feel salty?",
        answer="Sea water feels salty because it has salt in it.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(activity, prize) :- zone(activity, R), worn_on(prize, R).
compatible_gear(activity, prize) :- at_risk(activity, prize), gear(G), guards(G, wet), covers(G, R), worn_on(prize, R).
valid_story(name, gender, trait) :- child(name, gender), trait_ok(trait).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("activity", ACTIVITY.id))
    for r in sorted(ACTIVITY.zone):
        lines.append(asp.fact("zone", ACTIVITY.id, r))
    lines.append(asp.fact("mess", ACTIVITY.id, ACTIVITY.mess))
    lines.append(asp.fact("prize", "necklace"))
    lines.append(asp.fact("worn_on", "necklace", PRIZE.region))
    lines.append(asp.fact("gear", GEAR.id))
    for c in sorted(GEAR.covers):
        lines.append(asp.fact("covers", GEAR.id, c))
    for g in sorted(GEAR.guards):
        lines.append(asp.fact("guards", GEAR.id, g))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("child", "any", g))
    for t in TRAITS:
        lines.append(asp.fact("trait_ok", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show at_risk/2.\n#show compatible_gear/2."))
    return sorted(set(asp.atoms(model, "at_risk")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show compatible_gear/2.\n"))
    clingo = {("the tidal pool", ACTIVITY.id, "necklace")} if asp.atoms(model, "compatible_gear") else set()
    if py == clingo:
        print("OK: clingo gate matches Python reasonableness gate.")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("python:", sorted(py))
    print("clingo:", sorted(clingo))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender, params.trait)
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
    StoryParams(name="Pip", gender="boy", trait="curious"),
    StoryParams(name="Lily", gender="girl", trait="bouncy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible_gear/2."))
        return

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show compatible_gear/2.\n#show at_risk/2."))
        print(facts := asp.atoms(model, "compatible_gear"))
        print(facts)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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
            header = f"### {p.name}: tidal pool surprise"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
