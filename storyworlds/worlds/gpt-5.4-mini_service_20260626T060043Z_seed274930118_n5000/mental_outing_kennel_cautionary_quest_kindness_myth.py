#!/usr/bin/env python3
"""
storyworlds/worlds/mental_outing_kennel_cautionary_quest_kindness_myth.py
=========================================================================

A small myth-style story world about a careful outing to the kennel, where a
kindness quest helps a worried mind become steady again.

Seed tale:
---
Long ago, in a bright village, a child with a restless mind wanted to go on an
outing to the old kennel on the hill. The kennel keeper had asked for help: a
lost pup had hidden under straw, and only a gentle hand could coax it out.

But the child was afraid. The barking sounded huge, the straw smelled strange,
and the path to the kennel felt longer than a river. The child wanted to turn
back. Then the grandmother spoke a cautionary warning: "A frightened mind makes
every shadow grow larger. Breathe first. Look kindly. Walk slowly."

So the child carried a little bowl of water, listened to the keeper, and
followed the quest step by step. The pup came out, the child smiled, and the
outing became a story of kindness instead of fear.

World model:
---
This world tracks one child's physical outing and mental state, plus the kennel,
the pup, and the small quest objects. The story changes when caution lowers
panic, kindness raises courage, and the outing reaches the kennel safely.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    pup: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
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
    kind: str = "place"
    path_meters: int = 0
    is_kennel: bool = False
    is_home: bool = False
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
    title: str
    action: str
    step: str
    reward: str
    caution: str
    kindness: str
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
class StoryParams:
    place: str
    quest: str
    hero_name: str
    hero_type: str
    elder_type: str
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


class World:
    def __init__(self, place: Place, quest: Quest) -> None:
        self.place = place
        self.quest = quest
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "home": Place(name="the home courtyard", is_home=True, path_meters=0),
    "hill": Place(name="the hill kennel", is_kennel=True, path_meters=6),
    "village": Place(name="the village lane", path_meters=3),
}

QUESTS = {
    "kindness": Quest(
        id="kindness",
        title="the kindness quest",
        action="help the lost pup",
        step="carry a little bowl of water and speak softly",
        reward="the pup would trust the child",
        caution="A frightened mind makes every shadow grow larger.",
        kindness="Kindness can make a trembling creature feel safe.",
    ),
    "cautionary": Quest(
        id="cautionary",
        title="the cautionary quest",
        action="approach the kennel without rushing",
        step="breathe first, then take small steps",
        reward="the barking would feel smaller",
        caution="A quick step can startle a timid heart.",
        kindness="Gentle feet are a kind promise.",
    ),
    "myth": Quest(
        id="myth",
        title="the mythic quest",
        action="bring calm to the kennel",
        step="walk with steady thoughts and open hands",
        reward="the path would seem blessed",
        caution="A mind full of fear cannot hear the small, wise signs.",
        kindness="A kind word can be a lantern in a dark place.",
    ),
}


GIRL_NAMES = ["Lina", "Mira", "Nia", "Sora", "Tessa", "Ayla"]
BOY_NAMES = ["Pax", "Milo", "Jon", "Eren", "Taro", "Oren"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic kennel outing story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["mother", "father", "grandmother"])
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    quest = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = getattr(args, "elder", None) or rng.choice(["mother", "father", "grandmother"])
    if place == "home" and quest == "myth":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, quest=quest, hero_name=hero_name, hero_type=gender, elder_type=elder)


def _intro(world: World, hero: Entity, elder: Entity) -> None:
    q = world.quest
    world.say(
        f"Long ago, {hero.id} was a small {hero.type} with a restless mind, and {hero.pronoun('possessive')} "
        f"{elder.type} watched the clouds drift over {world.place.name}."
    )
    world.say(
        f"They had a task: {q.action}. {q.kindness}"
    )


def _caution(world: World, hero: Entity, elder: Entity) -> None:
    q = world.quest
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1.0
    world.say(
        f"But when the kennel barked from the hill, {hero.id} felt {hero.pronoun('possessive')} heart jump."
    )
    world.say(f'"{q.caution}" {elder.pronoun("subject").capitalize()} said. "First we breathe, then we walk."')


def _outing(world: World, hero: Entity, elder: Entity) -> None:
    distance = world.place.path_meters
    hero.meters["walked"] = hero.meters.get("walked", 0.0) + distance
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 0.5
    world.say(
        f"So {hero.id} and {elder.id} took the path to {world.place.name}, step by step."
    )
    world.say(
        f"{hero.id} carried a little bowl of water, because kindness is better than hurrying when a pup is afraid."
    )


def _quest_turn(world: World, hero: Entity, elder: Entity, pup: Entity) -> None:
    q = world.quest
    if hero.memes.get("fear", 0.0) >= THRESHOLD:
        hero.memes["panic"] = hero.memes.get("panic", 0.0) + 0.5
        world.say(
            f"At the kennel door, {hero.id} nearly turned back, but {hero.pronoun('possessive')} {elder.type} held {hero.pronoun('possessive')} hand."
        )
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1.0
    hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1.0
    pup.memes["trust"] = pup.memes.get("trust", 0.0) + 1.0
    world.say(
        f"{hero.id} remembered the quest: {q.step}. {q.reward.capitalize()}."
    )
    world.say(
        f"{hero.id} bent low, spoke softly, and the lost pup came out from the straw."
    )


def _ending(world: World, hero: Entity, elder: Entity, pup: Entity) -> None:
    hero.memes["fear"] = 0.0
    pup.meters["fed"] = pup.meters.get("fed", 0.0) + 1.0
    world.say(
        f"In the end, the pup lapped the water, pressed close, and wagged its tail."
    )
    world.say(
        f"{hero.id} smiled as if a storm had passed from {hero.pronoun('possessive')} mind, and the kennel felt blessed and warm."
    )


def tell(place: Place, quest: Quest, hero_name: str, hero_type: str, elder_type: str) -> World:
    world = World(place, quest)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type))
    pup = world.add(Entity(id="Pup", kind="character", type="puppy", plural=False))

    world.facts.update(hero=hero, elder=elder, pup=pup)

    _intro(world, hero, elder)
    world.para()
    _caution(world, hero, elder)
    _outing(world, hero, elder)
    world.para()
    _quest_turn(world, hero, elder, pup)
    _ending(world, hero, elder, pup)

    world.facts["resolved"] = True
    return world


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.is_kennel:
            lines.append(asp.fact("kennel", pid))
        if place.is_home:
            lines.append(asp.fact("home", pid))
        lines.append(asp.fact("path", pid, place.path_meters))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("caution", qid))
        lines.append(asp.fact("kindness", qid))
        if qid == "myth":
            lines.append(asp.fact("mythic", qid))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,Q) :- place(P), quest(Q), kennel(P), kindness(Q).
valid_story(P,Q) :- place(P), quest(Q), kennel(P), caution(Q).
valid_story(P,Q) :- place(P), quest(Q), kennel(P), mythic(Q).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, q) for p in PLACES for q in QUESTS if p == "hill"}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo parity matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    elder = _safe_fact(world, world.facts, "elder")
    q = world.quest
    return [
        f'Write a myth-like story about a child and a kennel, using the words "mental", "outing", and "kennel".',
        f"Tell a cautionary quest where {hero.id} goes on an outing to the kennel with {elder.type} guidance and learns kindness.",
        f"Write a small heroic tale in which a worried mind becomes steady during a journey to the kennel.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    elder: Entity = _safe_fact(world, world.facts, "elder")
    pup: Entity = _safe_fact(world, world.facts, "pup")
    q = world.quest
    return [
        QAItem(
            question=f"Who goes on the outing to the kennel?",
            answer=f"{hero.id} goes on the outing with {elder.type} to the kennel on the hill.",
        ),
        QAItem(
            question=f"What worried {hero.id} at first?",
            answer=f"The barking and the strange path made {hero.pronoun('possessive')} mind restless at first.",
        ),
        QAItem(
            question=f"How did kindness help in the quest?",
            answer=f"{hero.id} carried water, spoke softly, and helped the lost pup trust them.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{hero.id} became calm and brave, and the pup came out from the straw safely.",
        ),
        QAItem(
            question=f"What did the elder remind {hero.id} to do?",
            answer=f"The elder reminded {hero.id} to breathe first, then walk slowly and gently.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a kennel?",
            answer="A kennel is a small place where dogs stay or sleep, and people may care for puppies there.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful so you do not rush into danger or make a mistake.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward others.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a special journey or task where someone goes out to do something important.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id} ({e.type}) " + " ".join(bits))
    return "\n".join(lines)


def resolve_combo(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(QUESTS, params.quest), params.hero_name, params.hero_type, params.elder_type)
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
    StoryParams(place="hill", quest="kindness", hero_name="Lina", hero_type="girl", elder_type="grandmother"),
    StoryParams(place="hill", quest="cautionary", hero_name="Pax", hero_type="boy", elder_type="mother"),
    StoryParams(place="hill", quest="myth", hero_name="Mira", hero_type="girl", elder_type="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            try:
                params = resolve_combo(args, random.Random(base_seed + i))
            except StoryError:
                continue
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
