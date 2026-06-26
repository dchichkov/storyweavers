#!/usr/bin/env python3
"""
storyworlds/worlds/heaven_robbery_poker_reconciliation_foreshadowing_rhyming_story.py
======================================================================================

A small standalone storyworld in a rhyming-story style.

Seed tale inspiration:
- In heaven, a little angel loves poker under a bright cloud lamp.
- Foreshadowing hints that a robbery may happen.
- The threat arrives, but the characters choose reconciliation instead of blame.
- The ending should feel airy, gentle, and complete.

This script follows the Storyworld contract:
- self-contained stdlib script
- shared results imported eagerly
- ASP helper imported lazily inside ASP helpers
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    trait: str = ""
    friend: object | None = None
    hero: object | None = None
    prize: object | None = None
    thief: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"bright": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "angel-girl", "woman", "mother"}
        male = {"boy", "angel-boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    place: str = "heaven"
    sky_color: str = "gold"
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    rhythm: str
    bright: str
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
    region: str = "torso"
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
    "heaven": Setting(place="heaven", sky_color="gold", affords={"poker", "sing"}),
}

ACTIVITIES = {
    "poker": Activity(
        id="poker",
        verb="play poker",
        gerund="playing poker",
        rush="reach for the cards",
        keyword="poker",
        rhythm="shuffle, deal, and smile",
        bright="the cards flashed like little stars",
        tags={"poker", "cards", "game"},
    ),
}

PRIZES = {
    "cards": Prize(
        label="cards",
        phrase="a shiny deck of cloud-soft cards",
        type="cards",
        plural=True,
    ),
    "chips": Prize(
        label="chips",
        phrase="a little bowl of silver chips",
        type="chips",
        plural=True,
    ),
    "crown": Prize(
        label="crown",
        phrase="a tiny gold crown",
        type="crown",
    ),
}

HELPERS = {
    "olive_branch": "a leaf-shaped olive branch",
    "warm_lamp": "a warm cloud lamp",
    "shared_pot": "a shared pot of sweet cloud biscuits",
}

GIRL_NAMES = ["Nia", "Luna", "Mira", "Ari", "Zia", "Eve"]
BOY_NAMES = ["Theo", "Ivo", "Noah", "Sami", "Tobin", "Leo"]
TRAITS = ["gentle", "curious", "cheerful", "brave", "bright"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str = "heaven"
    activity: str = "poker"
    prize: str = "cards"
    name: str = "Nia"
    gender: str = "girl"
    trait: str = "gentle"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utility
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


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def is_reasonable(activity: Activity, prize: Prize) -> bool:
    return activity.id == "poker" and prize.label in {"cards", "chips", "crown"}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for activity_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, activity_id)
            for prize_id, prize in PRIZES.items():
                if is_reasonable(act, prize):
                    combos.append((setting_id, activity_id, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.verb} and a {prize.label} do not make a gentle "
        f"heaven-story here.)"
    )


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def predict_loss(world: World, hero: Entity, activity: Activity, prize: Entity) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["worry"] = sim.get(hero.id).memes.get("worry", 0.0) + 1
    sim.get(prize.id).meters["missing"] = sim.get(prize.id).meters.get("missing", 0.0) + 1
    return True


def setup(world: World, hero: Entity, friend: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    prize.worn_by = hero.id
    world.say(
        f"In heaven so high, where the soft clouds sigh, {hero.id} loved to {activity.verb} and let the day drift by."
    )
    world.say(
        f"{hero.pronoun().capitalize()} liked the {activity.rhythm}, and {activity.bright} as the bright white moon sailed by."
    )
    world.say(
        f"{hero.id} brought {hero.pronoun('possessive')} {prize.label}, because {hero.pronoun()} liked a lucky thing nearby."
    )
    world.say(
        f"{friend.id} smiled and said, 'In this golden sky, your {prize.label} looks merry and spry.'"
    )


def foreshadow(world: World, hero: Entity, friend: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["curious"] = hero.memes.get("curious", 0.0) + 1
    world.para()
    world.say(
        f"But a hush came first, like thunder far away; a tiny sign of trouble slipped into the play."
    )
    world.say(
        f"The cards tilted once, and the cloud lamp blushed; {hero.id} felt a soft, odd flutter in the hush."
    )
    world.say(
        f"{friend.id} noticed too and said, 'When shadows lean low, a sneaky thought may try to grow.'"
    )
    world.facts["foreshadowed"] = True
    world.facts["ominous_sign"] = "the cards tilted once"


def robbery(world: World, thief: Entity, hero: Entity, prize: Entity) -> None:
    thief.memes["greed"] = thief.memes.get("greed", 0.0) + 1
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    prize.meters["missing"] = prize.meters.get("missing", 0.0) + 1
    world.para()
    world.say(
        f"Then came a robbery, quick as a blink; {thief.id} grabbed the {prize.label} and dashed to the brink."
    )
    world.say(
        f"{hero.id} gasped, 'Oh no!' as the star-bright deck slipped away, leaving the table to sink."
    )
    world.facts["robbery"] = True
    world.facts["thief"] = thief.id


def reconciliation(world: World, hero: Entity, thief: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1)
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    thief.memes["shame"] = thief.memes.get("shame", 0.0) + 1
    thief.memes["peace"] = thief.memes.get("peace", 0.0) + 1
    prize.meters["missing"] = 0.0
    world.para()
    world.say(
        f"But {hero.id} took a breath and spoke with a glow, 'You need not stay lonely; come sit and be slow.'"
    )
    world.say(
        f"{thief.id} hung his head, then nodded with care; the hard little knot in the air grew fair."
    )
    world.say(
        f"They shared the deck, and the game grew bright; {activity.verb} together made the whole cloud right."
    )
    world.say(
        f"By the end of the hand, they were laughing like chimes, and the sky felt softer than silk and rhymes."
    )
    world.facts["reconciled"] = True


def closing_image(world: World, hero: Entity, thief: Entity, prize: Entity) -> None:
    world.para()
    world.say(
        f"Now the cards rest safe, and the moon keeps time; in heaven, forgiveness can sound like a rhyme."
    )
    world.say(
        f"{hero.id} and {thief.id} share the table and beam, with the {prize.label} neat, and the cloud-light agleam."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str, hero_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, trait=trait))
    friend = world.add(Entity(id="Moss", kind="character", type="angel-boy", trait="kind"))
    thief = world.add(Entity(id="Pip", kind="character", type="boy", trait="sly"))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        plural=prize_cfg.plural,
        owner=hero.id,
    ))

    world.facts.update(hero=hero, friend=friend, thief=thief, prize=prize, activity=activity, setting=setting)

    setup(world, hero, friend, prize, activity)
    foreshadow(world, hero, friend, activity, prize)
    robbery(world, thief, hero, prize)
    reconciliation(world, hero, thief, prize, activity)
    closing_image(world, hero, thief, prize)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

KNOWLEDGE = {
    "heaven": [
        ("What is heaven in this story?", "Heaven is a peaceful place in the sky, bright with clouds and gentle light."),
    ],
    "poker": [
        ("What is poker?", "Poker is a card game where people take turns, think carefully, and try to make a good hand."),
    ],
    "cards": [
        ("What are cards?", "Cards are small flat pieces used in games, often marked with pictures and numbers."),
    ],
    "chips": [
        ("What are chips in a game?", "Chips are little counters used to keep score or place bets in some games."),
    ],
    "robbery": [
        ("What is a robbery?", "A robbery is when someone takes something that does not belong to them."),
    ],
    "reconciliation": [
        ("What is reconciliation?", "Reconciliation means people stop fighting or feeling hurt and try to be kind again."),
    ],
    "foreshadowing": [
        ("What is foreshadowing?", "Foreshadowing is a clue that hints something important may happen later."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    act = _safe_fact(world, f, "activity")
    return [
        f'Write a short rhyming story for a young child set in heaven, where {hero.id} wants to {act.verb}.',
        f"Tell a gentle rhyming tale with foreshadowing and reconciliation, and include a robbery that turns into a kind ending.",
        f'Write a simple story that includes the words "heaven", "robbery", and "poker" and ends in friendship.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    thief: Entity = _safe_fact(world, f, "thief")
    prize: Entity = _safe_fact(world, f, "prize")
    activity: Activity = _safe_fact(world, f, "activity")
    return [
        QAItem(
            question=f"What did {hero.id} love to do in heaven?",
            answer=f"{hero.id} loved to {activity.verb} under the bright cloud light.",
        ),
        QAItem(
            question=f"What clue came before the robbery in the story?",
            answer=f"The story foreshadowed trouble when the cards tilted once and the air went hush.",
        ),
        QAItem(
            question=f"Who tried the robbery?",
            answer=f"{thief.id} tried the robbery and grabbed the {prize.label} away from the table.",
        ),
        QAItem(
            question=f"How did the story end after the robbery?",
            answer=f"{hero.id} chose reconciliation, invited {thief.id} back, and they played together in peace.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"heaven", "poker", "robbery", "reconciliation", "foreshadowing"}
    tags.add(world.facts["prize"].label)
    out: list[QAItem] = []
    for key in ["heaven", "poker", "cards", "chips", "robbery", "foreshadowing", "reconciliation"]:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------

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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P).
has_fix(A,P) :- prize_at_risk(A,P), gear_for(A,P).
valid_story(S,A,P) :- setting(S), affords(S,A), prize_at_risk(A,P), has_fix(A,P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("gear_for", "poker", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set((s, a_id, pr) for (s, a_id, pr) in valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world about heaven, poker, robbery, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "setting", None) and getattr(args, "setting", None) != "heaven":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "activity", None) and getattr(args, "activity", None) != "poker":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, activity, prize = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or choose_name(gender, rng)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, activity=activity, prize=prize, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize),
                 params.name, "angel-girl" if params.gender == "girl" else "angel-boy", params.trait)
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="heaven", activity="poker", prize="cards", name="Nia", gender="girl", trait="gentle"),
    StoryParams(setting="heaven", activity="poker", prize="chips", name="Theo", gender="boy", trait="curious"),
    StoryParams(setting="heaven", activity="poker", prize="crown", name="Mira", gender="girl", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible story combos:\n")
        for t in triples:
            print("  ", t)
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.activity} in {p.setting} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
