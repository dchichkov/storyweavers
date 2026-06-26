#!/usr/bin/env python3
"""
storyworlds/worlds/hoagie_colonial_fettuccine_foreshadowing_rhyming_story.py
=============================================================================

A standalone story world for a tiny rhyming tale with foreshadowing.

Premise:
- A child wants to carry a hoagie to a colonial-style picnic dinner.
- A small clue appears early: the fettuccine sauce is getting wobbly.
- The child notices the hint, fixes the problem with a tray and napkin,
  and the hoagie arrives safe and neat.

The world is small on purpose:
- one child
- one parent/helper
- one food parcel (the hoagie)
- one noodle dish (the fettuccine)
- one setting with a gentle historical flavor

The story is written in a rhyming, sing-song style with a clear setup,
foreshadowing, turn, and resolution.
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


def _safe_lookup(mapping, key):
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    held_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    fettuccine: object | None = None
    hoagie: object | None = None
    parent: object | None = None
    tray: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "care": 0.0, "warmth": 0.0, "risk": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "hope": 0.0, "pride": 0.0, "foresight": 0.0}

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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str
    mood: str
    colonial: bool = False
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
class Food:
    id: str
    label: str
    phrase: str
    smell: str
    risk_kind: str
    rhyme: str
    carried_in: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    covers: set[str]
    helps_with: set[str]
    rhyme: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def rhyme_pair(a: str, b: str) -> str:
    return f"{a} and {b}"


def setting_line(setting: Setting) -> str:
    if setting.colonial:
        return f"{setting.place.capitalize()} stood neat in a colonial lane, with old brick walls and a tidy refrain."
    return f"{setting.place.capitalize()} felt warm and bright, like a little song in the afternoon light."


def food_line(food: Food) -> str:
    return f"{food.label.capitalize()} smelled rich and nice, with {food.smell} twirling like a spoonful of spice."


def forecast_risk(world: World, child: Entity, food: Food) -> bool:
    sim = world.copy()
    child_sim = sim.get(child.id)
    child_sim.meters["risk"] += 1
    if food.id == "hoagie" and sim.entities.get("tray") and sim.entities["tray"].held_by == child.id:
        return False
    return True


def _rule_spill(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    hoagie = world.get("hoagie")
    if child.meters["risk"] < THRESHOLD:
        return out
    if hoagie.held_by != child.id:
        return out
    if "tray" in world.entities and world.get("tray").held_by == child.id:
        return out
    sig = ("spill", hoagie.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hoagie.meters["mess"] += 1
    child.memes["worry"] += 1
    out.append("The hoagie would wobble and drip, a messy little slip.")
    return out


def _rule_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    fettuccine = world.get("fettuccine")
    if fettuccine.meters["mess"] < THRESHOLD:
        return out
    sig = ("foreshadow", fettuccine.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["foresight"] += 1
    out.append("The saucy noodle clue was there, a hint the child should care.")
    return out


CAUSAL_RULES = [_rule_foreshadow, _rule_spill]


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


def prepare(world: World, child: Entity, parent: Entity) -> None:
    world.say(f"{child.id} was small and spry, with a smile that could light the sky.")
    world.say(f"{child.id} loved a rhyme and a tune, and hummed them most of the noon.")
    world.say(f"{parent.id} was gentle and kind, with a patient, planning mind.")


def introduce_foods(world: World, hoagie: Entity, fettuccine: Entity) -> None:
    world.say(f"The {hoagie.label} was stacked up high, like a tiny tower reaching the sky.")
    world.say(food_line(hoagie))
    world.say(f"The {fettuccine.label} waited near, creamy and twisty and bright to the ear.")
    world.say(food_line(fettuccine))


def foreshadow(world: World, child: Entity, fettuccine: Entity) -> None:
    fettuccine.meters["mess"] += 1
    world.say("But on the spoon there shone one streak, a silky smudge, a saucy peek.")
    propagate(world, narrate=True)
    child.memes["worry"] += 1


def want_to_carry(world: World, child: Entity, hoagie: Entity) -> None:
    child.memes["hope"] += 1
    child.meters["risk"] += 1
    world.say(f"{child.id} wanted to carry the {hoagie.label} with a grin, so the picnic could begin.")


def parent_warns(world: World, parent: Entity, child: Entity, hoagie: Entity) -> None:
    if forecast_risk(world, child, hoagie):
        world.say(
            f'"Careful," said {parent.id}, "for a tilt or a slip could send that {hoagie.label} on a messy trip."'
        )
    else:
        world.say(f'"Careful," said {parent.id}, but {child.id} had already found a safer way to proceed."')


def child_notices_clue(world: World, child: Entity, fettuccine: Entity) -> None:
    if fettuccine.meters["mess"] >= THRESHOLD:
        world.say(f"{child.id} saw the noodle gleam and guessed the tray might wobble in the stream.")
        child.memes["foresight"] += 1


def fix_with_tray(world: World, child: Entity, parent: Entity, tray: Entity, hoagie: Entity) -> None:
    tray.held_by = child.id
    hoagie.held_by = child.id
    child.meters["risk"] = 0
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1)
    world.say(f"{child.id} lifted a tray so neat, and set the hoagie safe and sweet.")
    world.say(f"With napkin tucked and fingers steady, {child.id} made the little feast all ready.")
    world.say(f"{parent.id} smiled wide, for the careful plan was now on their side.")


def resolve(world: World, child: Entity, hoagie: Entity, fettuccine: Entity) -> None:
    hoagie.meters["mess"] = 0
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    world.say(
        f"In the end, the {hoagie.label} stayed clean and bright, and the fettuccine sat just right."
    )
    world.say(
        f"{child.id} carried the lunch with a merry swing; that little clue had helped everything."
    )


@dataclass
class StoryParams:
    place: str
    child_name: str
    parent_name: str
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


SETTINGS = {
    "colonial_house": Setting(place="the colonial house", mood="calm", colonial=True),
    "garden_path": Setting(place="the garden path", mood="soft", colonial=False),
    "market_square": Setting(place="the market square", mood="busy", colonial=True),
}


def tell(setting: Setting, child_name: str, parent_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="boy", label=child_name))
    parent = world.add(Entity(id=parent_name, kind="character", type="mother", label=parent_name))
    hoagie = world.add(Entity(id="hoagie", type="thing", label="hoagie", phrase="a tall, tasty hoagie", owner=child.id, held_by=child.id))
    fettuccine = world.add(Entity(id="fettuccine", type="thing", label="fettuccine", phrase="a bowl of fettuccine", owner=parent.id))
    tray = world.add(Entity(id="tray", type="thing", label="tray", phrase="a flat wooden tray", owner=parent.id, held_by=None, protective=True, covers={"hands"}))

    world.facts.update(child=child, parent=parent, hoagie=hoagie, fettuccine=fettuccine, tray=tray)

    world.say(setting_line(setting))
    world.para()
    prepare(world, child, parent)
    introduce_foods(world, hoagie, fettuccine)
    world.para()
    foreshadow(world, child, fettuccine)
    want_to_carry(world, child, hoagie)
    parent_warns(world, parent, child, hoagie)
    child_notices_clue(world, child, fettuccine)
    fix_with_tray(world, child, parent, tray, hoagie)
    resolve(world, child, hoagie, fettuccine)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    return [
        f'Write a short rhyming story for a young child about {child.id}, a hoagie, and a clue that appears before a small spill.',
        f"Tell a gentle colonial-style story where {child.id} carries a hoagie, notices a foreshadowing hint from fettuccine, and fixes the problem.",
        "Write a kid-friendly rhyming tale with foreshadowing, a tray, and a picnic lunch that stays neat.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    parent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    hoagie = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hoagie")
    fettuccine = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "fettuccine")
    return [
        QAItem(
            question=f"What did {child.id} want to carry to the picnic?",
            answer=f"{child.id} wanted to carry the hoagie, because it looked tasty and tall and neat.",
        ),
        QAItem(
            question=f"What early clue hinted that something could get messy?",
            answer=f"The fettuccine had a saucy smudge, which foreshadowed that the lunch might wobble if nobody was careful.",
        ),
        QAItem(
            question=f"How did {child.id} keep the hoagie safe?",
            answer=f"{child.id} used a tray and a napkin, so the hoagie stayed steady while {parent.id} watched with a smile.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hoagie?",
            answer="A hoagie is a sandwich with filling inside a long roll.",
        ),
        QAItem(
            question="What is fettuccine?",
            answer="Fettuccine is a kind of flat pasta, often served with sauce.",
        ),
        QAItem(
            question="What does foreshadowing mean in a story?",
            answer="Foreshadowing is when a story gives a little clue early on about something that may happen later.",
        ),
        QAItem(
            question="What makes a story rhyme?",
            answer="A rhyming story uses words that sound alike at the ends, which makes it fun to hear.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
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
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id}: {', '.join(bits) if bits else 'quiet'}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="colonial_house", child_name="Milo", parent_name="Mama"),
    StoryParams(place="garden_path", child_name="Nina", parent_name="Mother"),
    StoryParams(place="market_square", child_name="Eli", parent_name="Mom"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming story world with foreshadowing.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--name", dest="child_name")
    ap.add_argument("--parent")
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
    place = getattr(args, "place", None) or rng.choice(sorted(SETTINGS))
    child_name = getattr(args, "child_name", None) or rng.choice(["Milo", "Nina", "Eli", "Ava", "Leo", "Ruby"])
    parent_name = getattr(args, "parent", None) or rng.choice(["Mama", "Mother", "Mom", "Papa"])
    return StoryParams(place=place, child_name=child_name, parent_name=parent_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.child_name, params.parent_name)
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


ASP_RULES = r"""
place(colonial_house). place(garden_path). place(market_square).
child(milo). child(nina). child(eli). child(ava). child(leo). child(ruby).
parent(mama). parent(mother). parent(mom). parent(papa).

foreshadowing :- clue(_).
safe_story :- foreshadowing, fixed(_).

#show foreshadowing/0.
#show safe_story/0.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    lines.append(asp.fact("food", "hoagie"))
    lines.append(asp.fact("food", "fettuccine"))
    lines.append(asp.fact("instrument", "foreshadowing"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show foreshadowing/0.\n#show safe_story/0."))
    atoms = {(s.name, len(s.arguments)) for s in model}
    if ("foreshadowing", 0) in atoms:
        print("OK: ASP program includes foreshadowing.")
        return 0
    print("MISMATCH: ASP program did not derive foreshadowing.")
    return 1


def asp_list() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show foreshadowing/0.\n#show safe_story/0."))
    return [str(atom) for atom in model]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show foreshadowing/0.\n#show safe_story/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("\n".join(asp_list()))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
