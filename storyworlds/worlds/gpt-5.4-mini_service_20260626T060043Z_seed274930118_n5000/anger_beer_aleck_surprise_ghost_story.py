#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/anger_beer_aleck_surprise_ghost_story.py
===============================================================================================================

A small ghost-story world about a spooky house, a nervous child, and a
surprise that turns anger into a safer feeling.

The seed words are built into the premise:
- anger
- beer
- aleck
- Surprise

The story model tracks a child, a ghostly setting, a drink that should not be
spilled, and an emotional turn from anger to surprise.
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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    ghost: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "ghost"}
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
class Setting:
    place: str = "the old house"
    mood: str = "spooky"
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    shock: str
    risk: str
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
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    gender: str
    parent: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "old_house": Setting(place="the old house", mood="spooky", affords={"spill", "anger"}),
    "cellar": Setting(place="the cellar", mood="dark", affords={"spill", "anger"}),
    "attic": Setting(place="the attic", mood="dusty", affords={"spill", "anger"}),
}

ACTIONS = {
    "spill": Action(
        id="spill",
        verb="peek at the bottle",
        gerund="peeking at the bottle",
        rush="reach for the bottle",
        shock="splashed beer",
        risk="a sticky surprise",
        keyword="beer",
        tags={"beer", "spill", "surprise"},
    ),
    "anger": Action(
        id="anger",
        verb="snap at the noise",
        gerund="snapping at the noise",
        rush="shout back",
        shock="a sharp surprise",
        risk="more anger",
        keyword="anger",
        tags={"anger", "ghost", "surprise"},
    ),
}

PRIZES = {
    "beer": Prize(label="beer", phrase="a cold bottle of beer", type="beer"),
    "lantern": Prize(label="lantern", phrase="a little brass lantern", type="lantern"),
    "key": Prize(label="key", phrase="an old iron key", type="key"),
}

BOY_NAMES = ["Aleck", "Ned", "Pip", "Milo", "Toby"]
GIRL_NAMES = ["Mina", "Ivy", "June", "Nora", "Pia"]
TRAITS = ["brave", "nervous", "curious", "small", "quiet"]


def prize_at_risk(action: Action, prize: Prize) -> bool:
    return prize.label == "beer" or action.id == "anger"


def select_fix(action: Action, prize: Prize) -> Optional[str]:
    if prize.label == "beer" and action.id == "spill":
        return "set the bottle on the high shelf"
    if action.id == "anger":
        return "turn on the lantern and tell a story"
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for act in ACTIONS:
            for prize in PRIZES:
                if prize_at_risk(_safe_lookup(ACTIONS, act), _safe_lookup(PRIZES, prize)) and select_fix(_safe_lookup(ACTIONS, act), _safe_lookup(PRIZES, prize)):
                    out.append((place, act, prize))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost story world with anger, beer, Aleck, and Surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or "boy"
    name = getattr(args, "name", None) or ("Aleck" if gender == "boy" else rng.choice(GIRL_NAMES))
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, action=action, prize=prize, name=name, gender=gender, parent=parent)


def _predict(world: World, hero: Entity, action: Action, prize: Entity) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["anger"] += 1
    if prize.label == "beer":
        prize.meters["spilled"] = 1
    return {"spilled": prize.label == "beer", "anger": 1}


def tell(setting: Setting, action: Action, prize_cfg: Prize, hero_name: str, hero_gender: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, meters={}, memes={"fear": 1}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent", meters={}, memes={}))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    ghost = world.add(Entity(id="Ghost", kind="character", type="ghost", label="the ghost", meters={}, memes={"mystery": 1}))

    world.say(f"{hero.id} lived in {setting.place}, where everything felt a little spooky.")
    world.say(f"{hero.id} was a {('boy' if hero_gender == 'boy' else 'girl')} who had a private worry about {prize.label}.")
    world.say(f"One evening, {hero.id} and {hero.pronoun('possessive')} {parent_type} heard the ghost whisper near the stairs.")
    world.say(f"{hero.id} felt anger climb up fast, because the sound made {hero.pronoun('object')} jump.")
    world.para()

    world.say(f"{hero.id} wanted to {action.verb}, but the room was dark and full of shadows.")
    world.say(f"The ghost made a surprise sound, and {hero.id} nearly {action.rush}.")
    pred = _predict(world, hero, action, prize)
    world.facts["pred"] = pred
    world.facts["action"] = action
    world.facts["prize"] = prize
    world.facts["hero"] = hero
    world.facts["parent"] = parent

    if prize.label == "beer":
        world.say(f"Then the bottle tipped. The beer made a sticky surprise on the floor.")
    else:
        world.say(f"Then the little problem grew into a bigger surprise.")
    hero.memes["anger"] += 1
    world.para()

    fix = select_fix(action, prize)
    if fix is None:
        pass

    hero.memes["surprise"] += 1
    hero.memes["anger"] = 0
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent_type} did not yell back.")
    world.say(f"Instead, {hero.pronoun('possessive')} {parent_type} smiled and said, '{fix}.'")
    world.say(f"{hero.id} blinked at the bright lantern light with Surprise, and the ghost stopped sounding scary.")
    world.say(f"In the end, {hero.id} was still in {setting.place}, but the anger had gone quiet and the air felt kinder.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    action = _safe_fact(world, f, "action")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short ghost story for a young child that includes the words "anger", "beer", "Aleck", and "Surprise".',
        f"Tell a spooky but gentle story about {hero.id} in {world.setting.place} where a ghost makes {hero.id} feel anger, and a surprise changes the mood.",
        f"Write a child-friendly story where someone named Aleck worries about {prize.label} and learns a calmer way to respond to a ghostly surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    prize = _safe_fact(world, f, "prize")
    action = _safe_fact(world, f, "action")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, who lives in {world.setting.place} and gets caught up in a spooky surprise.",
        ),
        QAItem(
            question=f"What made {hero.id} feel angry?",
            answer=f"{hero.id} felt angry when the ghost made a surprise noise and the room felt dark and jumpy.",
        ),
        QAItem(
            question=f"What happened to the beer?",
            answer=f"The beer tipped over and made a sticky surprise on the floor.",
        ),
        QAItem(
            question=f"How did the parent help?",
            answer=f"{hero.id}'s {parent.type} helped by offering a calmer plan: {select_fix(action, prize)}.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, the anger had gone quiet, and {hero.id} felt surprised in a safer, calmer way.",
        ),
    ]


KNOWLEDGE = {
    "beer": [
        QAItem(
            question="What is beer?",
            answer="Beer is a drink made by grown-ups. It is not for children, and it should be kept safely out of the way.",
        )
    ],
    "ghost": [
        QAItem(
            question="What is a ghost in a story?",
            answer="In a story, a ghost is often a spooky character that can be mysterious or silly, depending on the tale.",
        )
    ],
    "anger": [
        QAItem(
            question="What is anger?",
            answer="Anger is a strong feeling that can make a person want to shout, stomp, or argue.",
        )
    ],
    "surprise": [
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected. It can make someone gasp, blink, or smile big.",
        )
    ],
    "lantern": [
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives off light, which can make a dark place feel less scary.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["action"].tags)
    out: list[QAItem] = []
    for tag in ["beer", "ghost", "anger", "surprise", "lantern"]:
        if tag in tags or tag == "surprise":
            out.extend(KNOWLEDGE.get(tag, []))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,A,R) :- place(P), action(A), prize(R), valid(P,A,R).
valid(P,A,R) :- place(P), action(A), prize(R), risk(A,R), fix(A,R).
risk(spill,beer).
risk(anger,beer).
risk(anger,lantern).
fix(spill,beer).
fix(anger,beer).
fix(anger,lantern).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    lines.append(asp.fact("risk", "spill", "beer"))
    lines.append(asp.fact("risk", "anger", "beer"))
    lines.append(asp.fact("risk", "anger", "lantern"))
    lines.append(asp.fact("fix", "spill", "beer"))
    lines.append(asp.fact("fix", "anger", "beer"))
    lines.append(asp.fact("fix", "anger", "lantern"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:  # pragma: no cover
        print(f"ASP unavailable: {e}")
        return 1
    models = asp.solve(asp_program("#show valid/3."), models=1)
    clingo_set = set(asp.atoms(models[0], "valid")) if models else set()
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("only ASP:", sorted(clingo_set - py_set))
    print("only Python:", sorted(py_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="old_house", action="spill", prize="beer", name="Aleck", gender="boy", parent="mother"),
    StoryParams(place="cellar", action="anger", prize="lantern", name="Aleck", gender="boy", parent="father"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.parent)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.name}: {p.action} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
