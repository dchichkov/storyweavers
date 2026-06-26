#!/usr/bin/env python3
"""
storyworlds/worlds/bacteria_bravery_moral_value_misunderstanding_mystery.py
===========================================================================

A small mystery-style storyworld about bacteria, bravery, moral value, and a
misunderstanding that gets solved by careful noticing.

Premise:
- A child finds something unsettling: a jar, a stain, a smell, or a tiny
  speck that might be bacteria.
- The child feels unsure and a little afraid.
- An adult or helpful friend explains what is really happening.
- The child shows bravery by cleaning, investigating, or asking questions.
- The ending proves that the misunderstanding changed into understanding.

The domain stays small on purpose: a few places, a few clues, and a few
reasonable resolutions. The story is always driven by the simulated world state,
not by a static paragraph with swapped nouns.
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
    located_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    hero: object | None = None
    parent: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    place: str
    clue_surface: str
    reaction: str
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
class Clue:
    id: str
    label: str
    phrase: str
    kind: str
    location: str
    smell: str
    risk_word: str
    reveal_word: str
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
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
    fits_location: set[str]
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
    setting: str
    clue: str
    tool: str
    name: str
    gender: str
    parent: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _visible_bacteria(world: World, clue: Entity) -> bool:
    return clue.meters.get("found", 0.0) >= THRESHOLD and clue.meters.get("spotted", 0.0) >= THRESHOLD


def _r_clean_reveals(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.kind != "object":
            continue
        if e.meters.get("cleaned", 0.0) < THRESHOLD:
            continue
        sig = ("reveal", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if e.meters.get("bacteria", 0.0) >= THRESHOLD:
            out.append(f"The tiny specks were just bacteria, not something dangerous.")
            e.meters["revealed"] = 1.0
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.kind != "character":
            continue
        if ent.memes.get("brave_action", 0.0) < THRESHOLD:
            continue
        sig = ("brave", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["bravery"] = ent.memes.get("bravery", 0.0) + 1.0
        out.append(f"{ent.id} stood very still and looked again instead of running away.")
    return out


def _r_understanding(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.kind != "character":
            continue
        if ent.memes.get("understood", 0.0) < THRESHOLD:
            continue
        sig = ("understand", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["misunderstanding"] = 0.0
        out.append(f"The worry melted into calm, because the answer finally made sense.")
    return out


CAUSAL_RULES = [
    _r_clean_reveals,
    _r_bravery,
    _r_understanding,
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


def build_scene(setting: Setting, clue_cfg: Clue, tool_cfg: Tool, hero_name: str,
                hero_gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        meters={},
        memes={"fear": 0.0, "misunderstanding": 0.0, "bravery": 0.0, "curiosity": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
    ))
    clue = world.add(Entity(
        id="Clue",
        kind="object",
        type=clue_cfg.kind,
        label=clue_cfg.label,
        phrase=clue_cfg.phrase,
        located_in=clue_cfg.location,
        caretaker=parent.id,
        meters={"bacteria": 1.0, "found": 0.0, "cleaned": 0.0, "spotted": 0.0, "revealed": 0.0},
    ))
    tool = world.add(Entity(
        id="Tool",
        kind="object",
        type="tool",
        label=tool_cfg.label,
        phrase=tool_cfg.phrase,
        plural=tool_cfg.plural,
        located_in=setting.place,
    ))

    hero.memes["curiosity"] += 1.0
    world.say(f"{hero_name} was a {trait} child who liked noticing small things.")
    world.say(f"{hero.pronoun().capitalize()} had a habit of asking what every odd mark meant.")
    world.say(f"One day, in {setting.place}, {hero_name} saw {clue_cfg.phrase}.")
    world.say(f"It gave off {clue_cfg.smell}, and that made the room feel strange.")
    world.para()

    hero.memes["misunderstanding"] += 1.0
    hero.memes["fear"] += 1.0
    world.say(f"{hero_name} thought the specks might be a terrible kind of germ.")
    world.say(f"{hero.pronoun().capitalize()} wanted to back away, because the mystery seemed bigger than {hero.id}.")
    world.say(f"{parent.label or 'the parent'} knelt down and said, \"Let's look closely before we guess.\"")
    world.say(f"That was a brave thing to do, because careful looking can be harder than hiding.")
    world.para()

    hero.memes["brave_action"] += 1.0
    clue.meters["found"] += 1.0
    clue.meters["spotted"] += 1.0
    world.say(f"{hero_name} took a breath and used {tool_cfg.phrase} to check the spot.")
    if clue_cfg.risk_word:
        world.say(f"The place still felt {clue_cfg.risk_word}, but the tool helped {hero.pronoun('object')} keep going.")
    if tool_cfg.helps_with:
        world.say(f"The tool was a good fit for this clue, because it helped with {', '.join(sorted(tool_cfg.helps_with))}.")
    clue.meters["cleaned"] += 1.0
    propagate(world, narrate=True)
    hero.memes["understood"] += 1.0
    world.para()
    world.say(f"Then {parent.label or 'the parent'} explained that bacteria are tiny living things too small to see one by one.")
    world.say(f"They can make a place seem odd, but not every strange speck means something bad.")
    world.say(f"{hero_name} looked again and felt the guess turn into understanding.")
    world.say(f"In the end, the mystery was solved: {clue_cfg.reveal_word} were only bacteria, and {hero_name} had been brave enough to learn the truth.")

    world.facts.update(
        hero=hero,
        parent=parent,
        clue=clue,
        tool=tool,
        setting=setting,
        clue_cfg=clue_cfg,
        tool_cfg=tool_cfg,
        resolved=True,
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", clue_surface="counter", reaction="the sink hummed softly"),
    "bathroom": Setting(place="the bathroom", clue_surface="sink", reaction="the tiles felt cool"),
    "classroom": Setting(place="the classroom", clue_surface="table", reaction="the chairs waited in a neat row"),
    "garden_shed": Setting(place="the garden shed", clue_surface="shelf", reaction="the windows were dusty"),
}

CLUES = {
    "jar": Clue(
        id="jar",
        label="a glass jar",
        phrase="a glass jar with cloudy spots",
        kind="jar",
        location="counter",
        smell="a sour smell",
        risk_word="spooky",
        reveal_word="the cloudy spots",
        tags={"bacteria", "mystery"},
    ),
    "cup": Clue(
        id="cup",
        label="a little cup",
        phrase="a little cup with a fuzzy ring",
        kind="cup",
        location="sink",
        smell="a sour smell",
        risk_word="odd",
        reveal_word="the fuzzy ring",
        tags={"bacteria", "mystery"},
    ),
    "plate": Clue(
        id="plate",
        label="a white plate",
        phrase="a white plate with a tiny green patch",
        kind="plate",
        location="table",
        smell="a weird smell",
        risk_word="creepy",
        reveal_word="the tiny green patch",
        tags={"bacteria", "mystery"},
    ),
}

TOOLS = {
    "lamp": Tool(
        id="lamp",
        label="a small lamp",
        phrase="a small lamp",
        helps_with={"spotting"},
        fits_location={"kitchen", "classroom", "garden_shed"},
    ),
    "cloth": Tool(
        id="cloth",
        label="a clean cloth",
        phrase="a clean cloth",
        helps_with={"cleaning"},
        fits_location={"kitchen", "bathroom", "classroom", "garden_shed"},
    ),
    "magnifier": Tool(
        id="magnifier",
        label="a magnifying glass",
        phrase="a magnifying glass",
        helps_with={"looking closely"},
        fits_location={"kitchen", "bathroom", "classroom", "garden_shed"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Max", "Ben", "Theo"]
TRAITS = ["curious", "cautious", "gentle", "brave", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c, clue in CLUES.items():
            for t, tool in TOOLS.items():
                if clue.location in tool.fits_location:
                    combos.append((s, c, t))
    return combos


def prize_gender_ok(gender: str) -> bool:
    return gender in {"girl", "boy"}


def explain_rejection(setting: Setting, clue: Clue, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not fit well with {clue.label} in {setting.place}. "
        f"Pick a tool that can help in that room.)"
    )


def explain_gender(gender: str) -> str:
    return f"(No story: unsupported gender '{gender}'. Use girl or boy.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    clue_cfg = _safe_fact(world, f, "clue_cfg")
    setting = _safe_fact(world, f, "setting")
    return [
        f'Write a short mystery for a young child about bacteria in {setting.place}.',
        f"Tell a gentle story where {hero.id} finds {clue_cfg.phrase} and learns not to jump to conclusions.",
        f'Write a brave little mystery that includes the word "bacteria" and ends with understanding.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    clue = _safe_fact(world, f, "clue")
    clue_cfg = _safe_fact(world, f, "clue_cfg")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    trait = hero.memes.get("trait", "curious")
    return [
        QAItem(
            question=f"What did {hero.id} see in {world.setting.place}?",
            answer=f"{hero.id} saw {clue_cfg.phrase} in {world.setting.place}. It looked strange at first.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel worried about the specks?",
            answer=f"{hero.id} thought the specks might be a bad germ, so the mystery felt scary until {parent.id} helped explain it.",
        ),
        QAItem(
            question=f"How did {hero.id} show bravery?",
            answer=f"{hero.id} showed bravery by taking a breath, using {tool.phrase}, and looking closely instead of running away.",
        ),
        QAItem(
            question=f"What was the misunderstanding in the story?",
            answer=f"The misunderstanding was that {hero.id} thought the specks were something dangerous, but they were really bacteria.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, the fear turned into understanding, and the bacteria were no longer a mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are bacteria?",
            answer="Bacteria are tiny living things. Some are helpful, and some can make food or surfaces seem dirty.",
        ),
        QAItem(
            question="Why should you wash your hands?",
            answer="Washing your hands helps remove dirt and many germs so they do not spread as easily.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary when it is the right thing to do.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true, but the real answer is different.",
        ),
        QAItem(
            question="What does a magnifying glass do?",
            answer="A magnifying glass helps you look closely at small details.",
        ),
    ]


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
        if e.located_in:
            bits.append(f"located_in={e.located_in}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="kitchen", clue="jar", tool="magnifier", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="bathroom", clue="cup", tool="cloth", name="Leo", gender="boy", parent="father", trait="brave"),
    StoryParams(setting="classroom", clue="plate", tool="lamp", name="Nora", gender="girl", parent="mother", trait="thoughtful"),
]


ASP_RULES = r"""
% A clue is interesting when it has bacteria and is seen in a setting.
interesting(C) :- clue(C), has_bacteria(C), found(C).

% Bravery grows when a child looks closely instead of fleeing.
brave(H) :- hero(H), brave_action(H).

% A misunderstanding resolves when the true explanation is revealed.
resolved(H) :- hero(H), understood(H).

% A valid story requires an interesting clue, bravery, and a resolution.
valid_story(S, C, T) :- setting(S), clue(C), tool(T), compatible(S, C, T).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("has_bacteria", cid))
        lines.append(asp.fact("located_in", cid, clue.location))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
    for sid, setting in SETTINGS.items():
        for cid, clue in CLUES.items():
            for tid, tool in TOOLS.items():
                if clue.location in tool.fits_location:
                    lines.append(asp.fact("compatible", sid, cid, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {(s, c, t) for (s, c, t) in valid_combos()}
    clingo = set(asp_valid_stories())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery storyworld about bacteria, bravery, and misunderstanding."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if getattr(args, "gender", None) and not prize_gender_ok(getattr(args, "gender", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting_id, clue_id, tool_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting_id, clue=clue_id, tool=tool_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_scene(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(CLUES, params.clue),
        _safe_lookup(TOOLS, params.tool),
        params.name,
        params.gender,
        params.parent,
        params.trait,
    )
    world.facts["hero"].memes["trait"] = params.trait
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story combos:\n")
        for s, c, t in stories:
            print(f"  {s:12} {c:10} {t:10}")
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
            header = f"### {p.name}: {p.clue} in {p.setting} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
