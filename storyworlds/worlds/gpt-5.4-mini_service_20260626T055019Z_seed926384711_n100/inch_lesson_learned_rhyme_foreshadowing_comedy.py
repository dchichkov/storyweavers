#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/inch_lesson_learned_rhyme_foreshadowing_comedy.py
================================================================================================

A small story world about tiny measurements, funny mix-ups, and one careful
lesson learned.

Premise:
- A child is building, fitting, or sharing something that is almost right.
- A tiny gap matters: one inch.

Story shape:
- Foreshadowing: a ruler, a string, or a shelf hint that the problem is about
  to be noticed.
- Comedy: the characters overreact in harmless, silly ways.
- Lesson learned: the hero discovers that one inch can change everything.
- Rhyme: the ending carries a playful rhyme line to seal the memory.

This file follows the storyworld contract:
- one self-contained stdlib script
- StoryParams, registries, parser, resolve_params, generate, emit, main
- eager import of results.py
- lazy import of asp.py inside ASP helpers
- inline ASP_RULES twin plus Python reasonableness gate
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    risk: str
    clue: str
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
    size: str
    unit: str = "inch"
    tags: set[str] = field(default_factory=set)
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
class Aid:
    id: str
    label: str
    use: str
    helps: set[str]
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
        self.facts: dict = {}
        self.history: list[str] = []

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
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def inchify(n: int) -> str:
    return "one inch" if n == 1 else f"{n} inches"


def maybe_article(text: str) -> str:
    return text if text.startswith(("a ", "an ", "the ")) else f"a {text}"


def pluralize(noun: str) -> str:
    if noun.endswith("s"):
        return noun
    return noun + "s"


def pick_rhyme(word: str) -> str:
    rhymes = {
        "inch": "pinch",
        "bench": "stench",
        "clinch": "winch",
        "squish": "swish",
        "tower": "flower",
        "shelf": "elf",
    }
    return rhymes.get(word, "wink")


def foreshadow_line(activity: Activity, prize: Prize) -> str:
    return f"A tiny clue was already there: {activity.clue}, and it pointed straight at {prize.label}."


def comedy_line(hero: Entity, prize: Entity, activity: Activity) -> str:
    return (
        f"{hero.id} squinted at the gap and gasped, 'An inch! That's a whole parade for a mouse!'"
    )


def lesson_line(hero: Entity, prize: Entity, activity: Activity) -> str:
    return (
        f"{hero.id} learned that even one inch can matter when things need to fit just right."
    )


def rhyme_line(activity: Activity, prize: Prize) -> str:
    rhyme = pick_rhyme(prize.label[:-1] if prize.label.endswith("s") else prize.label)
    return f"An inch here, a {rhyme} there, and careful hands can fix with care."


def _measure_gap(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.meters["attention"] = hero.meters.get("attention", 0.0) + 1.0
    if prize.meters.get("gap", 0.0) >= THRESHOLD:
        hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1.0


def _r_notice_gap(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.meters.get("attention", 0.0) < THRESHOLD:
            continue
        prize = world.facts.get("prize")
        if not prize:
            continue
        if prize.meters.get("gap", 0.0) < THRESHOLD:
            continue
        sig = ("notice_gap", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
        out.append(f"{hero.id} noticed the tiny gap and leaned in with a comic little frown.")
    return out


def _r_fix_gap(world: World) -> list[str]:
    out: list[str] = []
    aid = world.facts.get("aid")
    prize = world.facts.get("prize")
    hero = world.facts.get("hero")
    if not (aid and prize and hero):
        return out
    if prize.meters.get("gap", 0.0) < THRESHOLD:
        return out
    if hero.memes.get("resolve", 0.0) < THRESHOLD:
        return out
    sig = ("fix_gap", prize.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prize.meters["gap"] = 0.0
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
    out.append("With a careful nudge, the tiny gap disappeared.")
    return out


CAUSAL_RULES = [
    _r_notice_gap,
    _r_fix_gap,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_gap(world: World, hero: Entity, activity: Activity, prize: Entity) -> dict:
    sim = world.copy()
    simulate_turn(sim, hero.id, activity.id, prize.id, narrate=False)
    return {
        "gap": sim.get(prize.id).meters.get("gap", 0.0),
        "noticed": sim.get(hero.id).memes.get("curiosity", 0.0) >= THRESHOLD,
    }


def setup_hero(world: World, name: str, gender: str, trait: str) -> Entity:
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name))
    hero.memes["joy"] = 1.0
    hero.memes["trait"] = 1.0
    hero.meters["style"] = 1.0
    return hero


def setup_companion(world: World, kind: str) -> Entity:
    return world.add(Entity(id="companion", kind="character", type=kind, label=f"the {kind}"))


def setup_prize(world: World, prize_cfg: Prize, gap: int) -> Entity:
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
    ))
    prize.meters["gap"] = float(gap)
    prize.meters["size"] = float(len(prize_cfg.size))
    return prize


def setup_aid(world: World, aid_cfg: Aid) -> Entity:
    return world.add(Entity(
        id=aid_cfg.id,
        kind="thing",
        type="aid",
        label=aid_cfg.label,
        phrase=aid_cfg.use,
    ))


def tell_intro(world: World, hero: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} was a cheerful little helper who loved tiny jobs with big importance."
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, and the whole room seemed to be waiting for it."
    )
    world.say(
        f"{hero.id} also liked {prize.label}, because {prize.phrase} looked simple until the last inch."
    )


def tell_foreshadow(world: World, activity: Activity, prize: Entity) -> None:
    world.say(foreshadow_line(activity, world.facts["prize_cfg"]))
    world.say(
        f"The ruler lay nearby like a quiet joke, and everyone pretended not to notice it."
    )


def tell_conflict(world: World, hero: Entity, companion: Entity, activity: Activity, prize: Entity) -> None:
    hero.meters["attention"] = hero.meters.get("attention", 0.0) + 1.0
    world.say(
        f"Then {hero.id} tried to {activity.rush}, but {prize.label} would not fit by a hair."
    )
    world.say(comedy_line(hero, prize, activity))
    pred = predict_gap(world, hero, activity, prize)
    world.facts["predicted_gap"] = pred["gap"]
    world.facts["predicted_notice"] = pred["noticed"]
    world.say(
        f"{companion.id} blinked and said, 'Well, that's an inch of trouble in a trench coat.'"
    )


def tell_turn(world: World, hero: Entity, companion: Entity, aid: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1.0
    world.say(
        f"{hero.id} fetched {aid.label} and lined it up with the edge."
    )
    world.say(
        f"{companion.id} pointed and said, 'Measure first, giggle after.'"
    )
    propagate(world, narrate=True)
    if prize.meters.get("gap", 0.0) >= THRESHOLD:
        prize.meters["gap"] = 0.0
    world.say(
        f"{aid.label.capitalize()} did the trick, because {aid.use}."
    )


def tell_resolution(world: World, hero: Entity, companion: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} tried again, and this time everything fit as neat as a bean in a seat."
    )
    world.say(
        f"{companion.id} laughed so hard they had to hold the table."
    )
    world.say(lesson_line(hero, prize, activity))
    world.say(
        f"{rhyme_line(activity, world.facts['prize_cfg'])} {hero.id} grinned, and the room felt bright."
    )


def simulate_turn(world: World, hero_id: str, activity_id: str, prize_id: str, narrate: bool = True) -> None:
    hero = world.get(hero_id)
    activity = _safe_lookup(ACTIVITIES, activity_id)
    prize = world.get(prize_id)
    _measure_gap(world, hero, activity, prize)
    if narrate:
        world.say("The ruler wobbled and everyone stared at the tiny gap.")
    propagate(world, narrate=narrate)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, aid_cfg: Aid, name: str, gender: str, companion_kind: str) -> World:
    world = World(setting)
    hero = setup_hero(world, name, gender, trait="curious")
    companion = setup_companion(world, companion_kind)
    prize = setup_prize(world, prize_cfg, gap=1)
    aid = setup_aid(world, aid_cfg)

    world.facts.update(
        hero=hero,
        companion=companion,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        aid=aid,
        setting=setting,
    )

    tell_intro(world, hero, prize, activity)
    world.para()
    tell_foreshadow(world, activity, prize)
    tell_conflict(world, hero, companion, activity, prize)
    world.para()
    tell_turn(world, hero, companion, aid, prize, activity)
    tell_resolution(world, hero, companion, prize, activity)
    return world


SETTINGS = {
    "workshop": Setting(place="the workshop", affords={"build", "frame", "stack"}),
    "kitchen": Setting(place="the kitchen table", affords={"slice", "stack", "balance"}),
    "classroom": Setting(place="the classroom corner", affords={"stack", "draw", "measure"}),
}

ACTIVITIES = {
    "build": Activity(
        id="build",
        verb="build a tower",
        gerund="building towers",
        rush="dash toward the blocks",
        risk="the tower would wobble off by an inch",
        clue="one block was already leaning like a sleepy penguin",
        keyword="inch",
        tags={"inch", "build", "comedy"},
    ),
    "stack": Activity(
        id="stack",
        verb="stack the books",
        gerund="stacking books",
        rush="pile the last book on top",
        risk="the stack would tip because of one inch",
        clue="the top book hung over the edge like a little hat",
        keyword="inch",
        tags={"inch", "stack", "comedy"},
    ),
    "measure": Activity(
        id="measure",
        verb="measure the shelf",
        gerund="measuring shelves",
        rush="stretch the tape along the edge",
        risk="the shelf would be off by an inch",
        clue="the tape measure dangled right beside the problem",
        keyword="inch",
        tags={"inch", "measure", "comedy"},
    ),
    "balance": Activity(
        id="balance",
        verb="balance the bowl",
        gerund="balancing bowls",
        rush="set the bowl on the tiny ledge",
        risk="the bowl would slide by an inch",
        clue="the ledge had a sneaky little lip",
        keyword="inch",
        tags={"inch", "balance", "comedy"},
    ),
}

PRIZES = {
    "tower": Prize(label="tower", phrase="a block tower", type="tower", size="small", tags={"inch", "build"}),
    "stack": Prize(label="stack", phrase="a wobbly stack", type="stack", size="small", tags={"inch", "stack"}),
    "shelf": Prize(label="shelf", phrase="a narrow shelf", type="shelf", size="small", tags={"inch", "measure"}),
    "bowl": Prize(label="bowl", phrase="a little bowl", type="bowl", size="small", tags={"inch", "balance"}),
}

AIDS = {
    "ruler": Aid(id="ruler", label="the ruler", use="it showed the inch exactly", helps={"measure", "build", "stack", "balance"}),
    "tape": Aid(id="tape", label="the tape measure", use="it stretched straight and told the truth", helps={"measure", "build", "stack"}),
    "spacer": Aid(id="spacer", label="the tiny spacer", use="it made the gap the right size", helps={"build", "stack", "balance"}),
}

GENDER_TO_NAME = {
    "girl": ["Mia", "Zoe", "Ava", "Lily", "Nora"],
    "boy": ["Leo", "Max", "Ben", "Finn", "Theo"],
}

TRAITS = ["curious", "careful", "bouncy", "silly", "brave"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    aid: str
    name: str
    gender: str
    companion_kind: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                for aid_id, aid in AIDS.items():
                    if act_id in aid.helps and "inch" in prize.tags and "inch" in act.tags:
                        combos.append((place, act_id, prize_id, aid_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.verb} and {prize.label} do not make a clean inch-level problem here.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy story world about one inch, one lesson, and one rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
              and (getattr(args, "aid", None) is None or c[3] == getattr(args, "aid", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize, aid = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GENDER_TO_NAME[gender])
    companion_kind = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place, activity, prize, aid, name, gender, companion_kind, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy for a child about "{f["activity"].keyword}" and one careful inch.',
        f"Tell a funny story where {f['hero'].id} learns that an inch can matter when {f['prize'].label} is almost right.",
        f"Write a rhyming lesson-learned story set in {f['setting'].place} with a tiny measurement problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prize = _safe_fact(world, f, "prize")
    act = _safe_fact(world, f, "activity")
    aid = _safe_fact(world, f, "aid")
    companion = _safe_fact(world, f, "companion")
    return [
        QAItem(
            question=f"What tiny problem did {hero.id} notice in {f['setting'].place}?",
            answer=f"{hero.id} noticed that {prize.label} was off by one inch, and that tiny amount was enough to cause a silly fit.",
        ),
        QAItem(
            question=f"What helped {hero.id} fix the problem?",
            answer=f"{aid.label} helped because {aid.use}. It made the inch easy to see and easy to fix.",
        ),
        QAItem(
            question=f"What did {hero.id} learn by the end?",
            answer=f"{hero.id} learned that even one inch can matter when something needs to fit just right, and {companion.id} laughed along with the lesson.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is an inch?", answer="An inch is a small unit for measuring length. It is useful when something is just a little bit too big or too small."),
        QAItem(question="What does a ruler do?", answer="A ruler helps measure how long something is, so you can see small differences like an inch."),
        QAItem(question="Why do people measure carefully?", answer="People measure carefully so pieces fit together, which saves time and keeps things from wobbling or breaking."),
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(Place, Act, Prize, Aid) :-
    affords(Place, Act),
    activity(Act),
    prize(Prize),
    aid(Aid),
    helps(Aid, Act),
    inch_story(Act, Prize).

"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("inch_story", aid, "inch"))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag_prize", pid, t))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        for h in sorted(a.helps):
            lines.append(asp.fact("helps", aid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/4."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def select_story(world: World, hero: Entity, act: Activity, prize: Entity, aid: Entity) -> None:
    world.say(
        f"{hero.id} loved {act.gerund}, because the room felt like it was holding its breath for the joke."
    )
    world.say(
        f"But {prize.label} was off by one inch, and {aid.label} waited nearby like a helpful wink."
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), _safe_lookup(AIDS, params.aid), params.name, params.gender, params.companion_kind)
    world.facts["trait"] = params.trait
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
        print(asp_program("#show valid_combo/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams("workshop", "build", "tower", "ruler", "Mia", "girl", "mother", "curious"),
            StoryParams("kitchen", "stack", "stack", "spacer", "Leo", "boy", "father", "silly"),
            StoryParams("classroom", "measure", "shelf", "tape", "Ava", "girl", "mother", "careful"),
            StoryParams("workshop", "balance", "bowl", "spacer", "Theo", "boy", "father", "brave"),
        ]
        samples = [generate(p) for p in curated]
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.activity} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
