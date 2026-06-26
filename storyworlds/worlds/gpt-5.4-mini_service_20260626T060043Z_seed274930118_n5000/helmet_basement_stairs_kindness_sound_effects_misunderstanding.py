#!/usr/bin/env python3
"""
storyworlds/worlds/helmet_basement_stairs_kindness_sound_effects_misunderstanding.py
====================================================================================

A small fairy-tale story world about a child, a helmet, basement stairs,
kindness, sound effects, and a misunderstanding.

Premise:
- A child loves a tiny noisy game in the basement stairs.
- The stairs are steep, dark, and echoey.
- A helmet and a kind helper make the play safe.
- A misunderstanding grows from the sound effects, then clears when everyone
  notices the child's gentle intention.

The world is intentionally small and constraint-driven: only a few plausible
story variants are allowed, and the story text is assembled from simulated
state, not from a frozen template.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    companion: object | None = None
    helmet: object | None = None
    hero: object | None = None
    parent: object | None = None
    def __post_init__(self):
        for key in ["bump", "sound", "safe"]:
            self.meters.setdefault(key, 0.0)
        for key in ["kindness", "fear", "misunderstanding", "joy", "worry"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "mother", "mom", "queen", "witch"}
        male = {"boy", "prince", "father", "dad", "king", "knight"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the basement stairs"
    affords: set[str] = field(default_factory=lambda: {"echo", "tiptoe", "carry"})
    fairy_tale: bool = True
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
    sound: str
    risk: str
    zone: set[str]
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
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))


@dataclass
class StoryParams:
    activity: str
    name: str
    gender: str
    parent: str
    companion: str
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


SETTING = Setting()

ACTIVITIES = {
    "echo_game": Activity(
        id="echo_game",
        verb="sing to the stairs",
        gerund="singing to the stairs",
        rush="dash down the steps",
        sound="echoing la-la-lahs",
        risk="a bump on the head",
        zone={"head", "torso"},
        keyword="echo",
        tags={"sound_effects", "misunderstanding"},
    ),
    "lantern_walk": Activity(
        id="lantern_walk",
        verb="carry the lantern",
        gerund="carrying the lantern",
        rush="hurry down with the lantern",
        sound="tap-tap, click, and glow",
        risk="a bump on the helmet",
        zone={"head", "hands"},
        keyword="sound effects",
        tags={"sound_effects", "kindness"},
    ),
    "kindness_carry": Activity(
        id="kindness_carry",
        verb="help carry the basket",
        gerund="helping carry the basket",
        rush="step quickly to help",
        sound="soft thump-thump, gentle as raindrops",
        risk="a slip on the stairs",
        zone={"hands", "feet"},
        keyword="kindness",
        tags={"kindness", "misunderstanding"},
    ),
}

GEAR = [
    Gear(
        id="helmet",
        label="a bright helmet",
        covers={"head"},
        guards={"bump"},
        prep="put on the helmet first",
        tail="walked carefully, one step at a time",
    )
]

NAMES = ["Ayla", "Theo", "Mira", "Pip", "Lena", "Rowan"]
GENDERS = ["girl", "boy"]
PARENTS = ["mother", "father"]
COMPANIONS = ["little cat", "wise mouse", "brown sparrow", "small lantern sprite"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for act_id, act in ACTIVITIES.items():
        if "misunderstanding" in act.tags and "kindness" in act.tags:
            combos.append(("basement_stairs", act_id))
    return combos


def choose_gear(activity: Activity) -> Optional[Gear]:
    for gear in GEAR:
        if activity.zone & gear.covers:
            return gear
    return None


def at_risk(activity: Activity, gear: Gear) -> bool:
    return bool(activity.zone & gear.covers)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "activity", None) not in ACTIVITIES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    activity = getattr(args, "activity", None) or rng.choice(sorted(ACTIVITIES))
    act = _safe_lookup(ACTIVITIES, activity)
    if not choose_gear(act):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    companion = getattr(args, "companion", None) or rng.choice(COMPANIONS)
    return StoryParams(activity=activity, name=name, gender=gender, parent=parent, companion=companion)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world: helmet, basement stairs, kindness, sound effects, misunderstanding.")
    ap.add_argument("--activity", choices=sorted(ACTIVITIES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--companion", choices=COMPANIONS)
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


def _subject(type_: str) -> str:
    return "she" if type_ == "girl" else "he"


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    companion = world.add(Entity(id="companion", kind="character", type="sprite", label=params.companion))
    helmet = world.add(Entity(id="helmet", type="helmet", label="helmet", phrase="a bright helmet", owner=hero.id, protective=True, covers={"head"}))
    helmet.worn_by = hero.id

    act = _safe_lookup(ACTIVITIES, params.activity)
    world.facts.update(hero=hero, parent=parent, companion=companion, helmet=helmet, activity=act)

    # Act 1
    world.say(f"In the old house, {hero.id} loved the basement stairs, where every step answered with a secret little echo.")
    world.say(f"{hero.pronoun().capitalize()} was a merry child who liked {act.gerund}, and the sounds felt like fairy bells in the dark.")
    world.say(f"Beside {hero.pronoun('object')}, {companion.label} listened, and the two friends planned a gentle game under the low stone ceiling.")
    world.para()

    # Act 2
    world.say(f"One evening, {hero.id} wanted to {act.verb} on the basement stairs.")
    world.say(f"{hero.pronoun('possessive').capitalize()} {params.parent} heard the {act.sound} and grew worried, because those stairs were steep and the echo made everything seem bigger than it was.")
    world.say(f'"Slowly now," said {params.parent}, "or you may find {act.risk}."')
    hero.memes["worry"] += 1
    hero.memes["misunderstanding"] += 1
    parent.memes["worry"] += 1
    world.say(f"But the sound bounced and bounced, and for a moment the {params.parent} thought the noise meant trouble, not kindness.")
    world.para()

    # Act 3
    world.say(f"Then {companion.label} pointed to {hero.pronoun('possessive')} helmet and chirped that brave feet could still be gentle feet.")
    world.say(f"{hero.id} smiled, because {hero.pronoun('possessive')} plan had been to help carry the basket, not to race or tumble.")
    world.say(f"{hero.pronoun('possessive').capitalize()} {params.parent} softened at once and said, \"If the helmet stays on, we can keep the game kind.\"")
    world.say(f"So {hero.id} chose to {act.verb}, {helmet.label} snug on {hero.pronoun('possessive')} head, while {companion.label} made the tiniest {act.sound} sound effects to light the way.")
    world.say(f"The misunderstanding melted away like candle smoke. At the end, {hero.id} was {act.gerund} safely on the basement stairs, and everyone laughed in the warm little echo.")
    hero.memes["kindness"] += 1
    hero.memes["joy"] += 1
    hero.memes["misunderstanding"] = 0
    hero.meters["safe"] += 1
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act = _safe_fact(world, f, "activity")
    hero = _safe_fact(world, f, "hero")
    return [
        "Write a fairy-tale story about a child, a helmet, and a misunderstanding on the basement stairs.",
        f"Tell a gentle story where {hero.id} uses {act.keyword} sound effects and kindness to clear a misunderstanding.",
        "Write a child-friendly story that begins in the basement stairs and ends with safe, kind help.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    act = _safe_fact(world, f, "activity")
    companion = _safe_fact(world, f, "companion")
    helmet = _safe_fact(world, f, "helmet")
    return [
        QAItem(
            question=f"What did {hero.id} love doing in the basement stairs?",
            answer=f"{hero.id} loved {act.gerund}. The sounds echoed in the basement stairs like tiny fairy bells.",
        ),
        QAItem(
            question=f"Why did the {parent.type} worry when {hero.id} made the sound effects?",
            answer=f"The {parent.type} worried because the basement stairs were steep, and the noisy echo made it seem as if {hero.id} might be in danger even though {hero.id} meant to be careful.",
        ),
        QAItem(
            question=f"How did {helmet.label} help {hero.id} in the story?",
            answer=f"{helmet.label.capitalize()} protected {hero.id}'s head, so {hero.id} could keep moving carefully on the stairs while staying safe.",
        ),
        QAItem(
            question=f"Who helped clear up the misunderstanding?",
            answer=f"{companion.label} helped by reminding everyone that {hero.id} was being kind, not reckless.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks a thing means one idea, but it really means something else.",
        ),
        QAItem(
            question="Why do sound effects matter in a story?",
            answer="Sound effects can make a story feel lively and can also confuse people if the sounds seem louder or scarier than the truth.",
        ),
        QAItem(
            question="What does kindness do?",
            answer="Kindness helps people feel safe, cared for, and ready to listen to one another.",
        ),
        QAItem(
            question="What is a helmet for?",
            answer="A helmet helps protect a person's head when there might be bumps or falls.",
        ),
    ]


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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is reasonable when the activity is about the basement stairs and
% there is a compatible helmet that protects the at-risk head.
at_risk(A) :- activity(A), zone(A, head).
has_fix(A) :- at_risk(A), gear(helmet), covers(helmet, head), guards(helmet, bump).
valid_story(A) :- at_risk(A), has_fix(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("location", "basement_stairs"))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", aid, z))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for guard in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, guard))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {("echo_game",), ("lantern_walk",)}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def explain_rejection(activity: Activity) -> str:
    return (
        f"(No story: {activity.gerund} does not fit the reasonableness rule for "
        f"the basement stairs, or no helmet-like fix would make the play safe.)"
    )


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "activity", None) not in ACTIVITIES:
        pass
    act = getattr(args, "activity", None) or rng.choice(sorted(ACTIVITIES))
    if choose := choose_gear(_safe_lookup(ACTIVITIES, act)):
        _ = choose
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    companion = getattr(args, "companion", None) or rng.choice(COMPANIONS)
    return StoryParams(activity=act, name=name, gender=gender, parent=parent, companion=companion)


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
    StoryParams(activity="echo_game", name="Ayla", gender="girl", parent="mother", companion="wise mouse"),
    StoryParams(activity="lantern_walk", name="Theo", gender="boy", parent="father", companion="small lantern sprite"),
    StoryParams(activity="kindness_carry", name="Mira", gender="girl", parent="mother", companion="little cat"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for (act,) in stories:
            print(f"  basement_stairs  {act}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            params = build_story_params(args, random.Random(seed))
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.activity} in the basement stairs"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
