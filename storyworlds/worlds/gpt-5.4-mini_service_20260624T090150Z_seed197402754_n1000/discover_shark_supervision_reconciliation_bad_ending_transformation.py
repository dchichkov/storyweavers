#!/usr/bin/env python3
"""
A pirate-tale storyworld about a curious child pirate, a discovered shark, adult
supervision, reconciliation after a bad ending, and a final transformation.

The world is intentionally small and classical:
- A child pirate wants to discover something exciting at sea.
- A shark makes the adventure dangerous.
- A supervising captain warns them.
- The child disobeys, causing a bad ending for the treasure.
- A reconciliation follows, and the child changes how they behave.

The prose is driven by simulated state, not a frozen template.
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


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"          # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pirate", "captain"}
        if self.type in female and self.type not in {"pirate"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    sea: str
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
class Discovery:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    danger: str
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
    location: str   # deck | mast | chest | map
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
class SupervisionGear:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.seen_shark = False
        self.bad_ending = False
        self.transformed = False

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
        clone = World(self.setting)
        import copy as _copy
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.seen_shark = self.seen_shark
        clone.bad_ending = self.bad_ending
        clone.transformed = self.transformed
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "harbor": Setting(place="the harbor", sea="the blue sea", affords={"discover", "sail"}),
    "island": Setting(place="the island shore", sea="the green sea", affords={"discover", "sail"}),
    "cove": Setting(place="the cove", sea="the dark sea", affords={"discover", "sail"}),
}

DISCOVERIES = {
    "shark": Discovery(
        id="shark",
        verb="discover the shark",
        gerund="discovering the shark",
        rush="run to the rail to look closer",
        keyword="shark",
        danger="the shark's fins and teeth",
        tags={"shark", "sea"},
    ),
    "glowfish": Discovery(
        id="glowfish",
        verb="discover the glowfish",
        gerund="discovering the glowfish",
        rush="lean over the water for a better look",
        keyword="glowfish",
        danger="the sudden splash",
        tags={"sea"},
    ),
}

PRIZES = {
    "map": Prize(label="map", phrase="a curled treasure map", type="map", location="chest"),
    "compass": Prize(label="compass", phrase="a brass compass", type="compass", location="belt"),
    "flag": Prize(label="flag", phrase="a bright ship flag", type="flag", location="mast"),
}

GEAR = [
    SupervisionGear(
        id="spyglass",
        label="a spyglass",
        prep="take the spyglass and keep watch together",
        tail="stood together at the rail with the spyglass",
        protects={"shark"},
    ),
    SupervisionGear(
        id="lifeline",
        label="a rope lifeline",
        prep="tie on a rope lifeline before leaning over",
        tail="kept the rope lifeline tied tight",
        protects={"shark", "sea"},
    ),
    SupervisionGear(
        id="lamp",
        label="a lantern lamp",
        prep="hold up a lantern lamp and stay close",
        tail="walked back under the lantern lamp",
        protects={"dark"},
    ),
]

GIRL_NAMES = ["Mina", "Ivy", "Tess", "Nia", "Ruby", "Luna"]
BOY_NAMES = ["Kai", "Finn", "Jace", "Owen", "Reef", "Nico"]
TRAITS = ["curious", "brave", "stubborn", "cheerful", "spirited"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    discovery: str
    prize: str
    name: str
    gender: str
    captain: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Rule helpers
# ---------------------------------------------------------------------------
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


THRESHOLD = 1.0


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for disc_id in setting.affords:
            for prize_id in PRIZES:
                if disc_id == "shark" and prize_id in {"map", "compass"}:
                    combos.append((place, disc_id, prize_id))
                if disc_id == "glowfish":
                    combos.append((place, disc_id, prize_id))
    return combos


def prize_at_risk(discovery: Discovery, prize: Prize) -> bool:
    return discovery.id == "shark" and prize.location in {"chest", "belt", "mast"}


def select_gear(discovery: Discovery, prize: Prize) -> Optional[SupervisionGear]:
    if discovery.id != "shark":
        return None
    for gear in GEAR:
        if "shark" in gear.protects:
            return gear
    return None


def explain_rejection(discovery: Discovery, prize: Prize) -> str:
    return (
        f"(No story: the {discovery.id} discovery does not honestly threaten the "
        f"{prize.label} in a way supervision can fix.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: the chosen role does not fit the requested {gender}.)"


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def predict_badrisk(world: World, hero: Entity, discovery: Discovery, prize_id: str) -> dict:
    sim = world.copy()
    _do_discover(sim, sim.get(hero.id), discovery, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "broken": bool(prize and prize.meters.get("broken", 0) >= THRESHOLD),
        "shark_seen": sim.seen_shark,
    }


def _do_discover(world: World, actor: Entity, discovery: Discovery, narrate: bool = True) -> None:
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0) + 1
    world.seen_shark = discovery.id == "shark"
    if discovery.id == "shark":
        actor.meters["fear"] = actor.meters.get("fear", 0) + 1
    if narrate:
        world.say(f"{actor.id} wanted to {discovery.verb}.")


def _apply_bad_ending(world: World, hero: Entity, prize: Entity) -> None:
    if hero.memes.get("reckless", 0) < THRESHOLD:
        return
    prize.meters["broken"] = prize.meters.get("broken", 0) + 1
    world.bad_ending = True


def _apply_transformation(world: World, hero: Entity) -> None:
    if hero.memes.get("reconciled", 0) >= THRESHOLD:
        hero.memes["grown"] = hero.memes.get("grown", 0) + 1
        world.transformed = True


def tell(setting: Setting, discovery: Discovery, prize_cfg: Prize, hero_name: str,
         hero_gender: str, captain_type: str, trait: str) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type="girl" if hero_gender == "girl" else "boy",
        traits=["little", trait, "pirate"],
    ))
    captain = world.add(Entity(
        id="Captain", kind="character", type=captain_type, label="the captain",
        traits=["steady", "watchful"],
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=captain.id,
    ))

    # Act 1
    world.say(f"{hero.id} was a little {trait} pirate who loved the sea.")
    world.say(f"{hero.id} dreamed of {discovery.gerund} near {setting.sea}.")
    world.say(f"One morning, {hero.id}'s {captain.label_word} showed {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} loved that {prize.label} and kept it close.")

    # Act 2
    world.para()
    world.say(f"At {setting.place}, the water moved strangely.")
    _do_discover(world, hero, discovery, narrate=False)
    world.say(f"Then {hero.id} spotted a fin in the waves and gasped.")
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(f"{hero.id} wanted to {discovery.verb}, but {hero.pronoun('possessive')} {captain.label_word} warned {hero.pronoun('object')} to stay close.")
    hero.memes["warned"] = hero.memes.get("warned", 0) + 1
    world.say(f'"The shark is near," {hero.pronoun("possessive")} {captain.label_word} said. "Keep under my supervision."')
    hero.memes["reckless"] = hero.memes.get("reckless", 0) + 1
    world.say(f"But {hero.id} tried to {discovery.rush}.")
    _apply_bad_ending(world, hero, prize)
    if world.bad_ending:
        world.say(f"The rope snapped loose, and the {prize.label} fell into the water.")
        world.say(f"That was a bad ending for the treasure.")
    else:
        world.say(f"The sea stayed calm for a breath, but the warning still mattered.")

    # Act 3
    world.para()
    hero.memes["sad"] = hero.memes.get("sad", 0) + 1
    world.say(f"{hero.id} looked ashamed and listened at last.")
    hero.memes["reconciled"] = hero.memes.get("reconciled", 0) + 1
    world.say(f"{hero.id} said sorry to {hero.pronoun('possessive')} {captain.label_word}.")
    gear = select_gear(discovery, prize)
    if gear:
        world.say(f"Together they chose {gear.label} and a safer plan.")
        world.say(f"{hero.id} and {hero.pronoun('possessive')} {captain.label_word} {gear.prep}.")
        hero.memes["transformed"] = hero.memes.get("transformed", 0) + 1
        _apply_transformation(world, hero)
        world.say(
            f"In the end, {hero.id} still loved the sea, but now {hero.pronoun()} listened "
            f"when the grown-up watched over the deck."
        )
        world.say(
            f"{hero.id} looked smaller than the shark, yet braver in a better way."
        )

    world.facts.update(
        hero=hero,
        captain=captain,
        prize=prize,
        discovery=discovery,
        gear=gear,
        bad_ending=world.bad_ending,
        transformed=world.transformed,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Story content / prompts / QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, captain, disc, prize = f["hero"], f["captain"], f["discovery"], f["prize"]
    return [
        f'Write a pirate tale for a young child about a {hero.id} who wants to {disc.verb} under supervision.',
        f"Tell a short story where {hero.id} sees a shark, listens to {captain.label_word}, and keeps the {prize.label} safe.",
        f'Write a gentle sea adventure using the words "discover", "shark", and "supervision".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, prize, disc = f["hero"], f["captain"], f["prize"], f["discovery"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at the sea?",
            answer=f"{hero.id} wanted to {disc.verb} while sailing near {world.setting.place}.",
        ),
        QAItem(
            question=f"Who kept {hero.id} under supervision?",
            answer=f"{hero.id}'s {captain.label_word} kept {hero.id} under supervision so the child would stay safe.",
        ),
        QAItem(
            question=f"What treasure did {hero.id} love?",
            answer=f"{hero.id} loved the {prize.label} and wanted to keep {prize.it()} safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shark?",
            answer="A shark is a big fish that lives in the sea. Some sharks can look scary because they have sharp fins and teeth.",
        ),
        QAItem(
            question="What does supervision mean?",
            answer="Supervision means a grown-up stays nearby to watch, guide, and keep someone safe.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people make peace again after a problem and start being friendly once more.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a new kind of self or a new way of acting.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(D, P) :- discovery(D), prize(P), D = shark, prize_loc(P, chest).
prize_at_risk(D, P) :- discovery(D), prize(P), D = shark, prize_loc(P, belt).
prize_at_risk(D, P) :- discovery(D), prize(P), D = shark, prize_loc(P, mast).

compatible(D, P) :- prize_at_risk(D, P), gear(G), protects(G, shark).

valid_story(S, D, P) :- setting(S), discovery(D), prize(P), compatible(D, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for did, d in DISCOVERIES.items():
        lines.append(asp.fact("discovery", did))
        for t in sorted(d.tags):
            lines.append(asp.fact("tag", did, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_loc", pid, p.location))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for t in sorted(g.protects):
            lines.append(asp.fact("protects", g.id, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld: discovery, shark, supervision, reconciliation, bad ending, transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--discovery", choices=DISCOVERIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=["captain", "father", "mother"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "discovery", None) and getattr(args, "prize", None):
        disc, prize = _safe_lookup(DISCOVERIES, getattr(args, "discovery", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(disc, prize) and select_gear(disc, prize)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in {"girl", "boy"}:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "discovery", None) is None or c[1] == getattr(args, "discovery", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, disc_id, prize_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    captain = getattr(args, "captain", None) or "captain"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, discovery=disc_id, prize=prize_id, name=name,
                       gender=gender, captain=captain, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(DISCOVERIES, params.discovery),
        _safe_lookup(PRIZES, params.prize),
        params.name,
        params.gender,
        params.captain,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  seen_shark={world.seen_shark} bad_ending={world.bad_ending} transformed={world.transformed}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, discovery, prize) combos:\n")
        for s, d, p in combos:
            print(f"  {s:8} {d:10} {p}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="harbor", discovery="shark", prize="map", name="Mina", gender="girl", captain="captain", trait="curious"),
            StoryParams(place="island", discovery="shark", prize="compass", name="Kai", gender="boy", captain="captain", trait="brave"),
            StoryParams(place="cove", discovery="shark", prize="flag", name="Nia", gender="girl", captain="mother", trait="stubborn"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.name}: {p.discovery} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
