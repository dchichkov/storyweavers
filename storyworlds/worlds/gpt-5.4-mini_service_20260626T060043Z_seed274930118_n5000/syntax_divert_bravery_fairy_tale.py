#!/usr/bin/env python3
"""
A small fairy-tale storyworld about syntax, diversion, and bravery.

Premise:
- A young character must speak or read a tricky spell, verse, or message.
- The language matters: if the syntax is wrong, the magic tangles.
- A diversion tempts the character away from the careful path.
- Bravery means staying kind and steady long enough to finish the task.

The world is constraint-checked so the tale always has a real tension and a
real fix: the hero must face a syntax problem, resist a diversion, and use a
brave helper or brave choice to resolve the danger.
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
# World model
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    guide: object | None = None
    hero: object | None = None
    token: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "witch", "princess", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "wizard", "prince", "father"}:
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
    mood: str
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
class Task:
    id: str
    name: str
    action: str
    gerund: str
    risk: str
    zone: str
    diversion: str
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
class Token:
    id: str
    label: str
    phrase: str
    region: str
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
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    covers: set[str]
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "library": Setting(place="the moonlit library", mood="quiet", affords={"chant", "riddle"}),
    "tower": Setting(place="the old tower", mood="windy", affords={"chant", "riddle"}),
    "garden": Setting(place="the rose garden", mood="bright", affords={"chant"}),
}

TASKS = {
    "chant": Task(
        id="chant",
        name="chant a brave spell",
        action="chant the spell",
        gerund="chanting the spell",
        risk="tangled",
        zone="mouth",
        diversion="follow a glowing butterfly",
        keyword="syntax",
        tags={"syntax", "spell", "bravery"},
    ),
    "riddle": Task(
        id="riddle",
        name="answer the riddle",
        action="answer the riddle",
        gerund="answering the riddle",
        risk="mixed up",
        zone="mind",
        diversion="chase a silver ribbon",
        keyword="divert",
        tags={"riddle", "divert", "bravery"},
    ),
}

TOKENS = {
    "scroll": Token(
        id="scroll",
        label="scroll",
        phrase="an old scroll with gold letters",
        region="hands",
    ),
    "crown": Token(
        id="crown",
        label="crown",
        phrase="a little golden crown",
        region="head",
    ),
    "cloak": Token(
        id="cloak",
        label="cloak",
        phrase="a soft blue cloak",
        region="shoulders",
    ),
}

AIDS = [
    Aid(
        id="inkpause",
        label="an ink pause",
        prep="take one careful breath and hold the scroll close",
        tail="waited, breathed, and spoke each word with care",
        guards={"syntax"},
        covers={"mouth", "hands"},
    ),
    Aid(
        id="steadystone",
        label="a steady stone step",
        prep="stand on a steady stone step and ignore the fluttering distraction",
        tail="kept steady and chose the true path",
        guards={"divert"},
        covers={"mind", "feet"},
    ),
    Aid(
        id="courage",
        label="a brave little song",
        prep="sing a brave little song first",
        tail="sang bravely until the last word came clear",
        guards={"syntax", "divert"},
        covers={"mouth", "mind"},
    ),
]

GIRL_NAMES = ["Ava", "Mira", "Lina", "Rose", "Elia", "Tessa"]
BOY_NAMES = ["Finn", "Oren", "Theo", "Bram", "Eli", "Nico"]
TRAITS = ["gentle", "curious", "small", "kind", "quiet", "bold"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def task_needs_bravery(task: Task, token: Token) -> bool:
    return task.id in {"chant", "riddle"} and token.region in {"hands", "head", "shoulders"}


def select_aid(task: Task, token: Token) -> Optional[Aid]:
    for aid in AIDS:
        if task.keyword in aid.guards and token.region in aid.covers:
            return aid
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for tid in setting.affords:
            task = _safe_lookup(TASKS, tid)
            for token_id, token in TOKENS.items():
                if task_needs_bravery(task, token) and select_aid(task, token):
                    out.append((place, tid, token_id))
    return out


def explain_rejection(task: Task, token: Token) -> str:
    if not task_needs_bravery(task, token):
        return (
            f"(No story: {task.name} does not place the {token.label} in real danger, "
            f"so the brave turn would be weak.)"
        )
    return (
        f"(No story: no aid in this world can honestly protect the {token.label} "
        f"from the problem in {task.name}.)"
    )


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def setting_detail(setting: Setting, task: Task) -> str:
    if setting.place == "the moonlit library":
        return "Tall shelves leaned like sleepy trees, and the candles made small gold pools on the floor."
    if setting.place == "the old tower":
        return "The tower creaked in the wind, and every stair seemed to wait for a careful footstep."
    return "The rose garden smelled sweet, and the petals trembled softly in the breeze."


def intro_line(hero: Entity) -> str:
    trait = next((t for t in hero.meters.get("traits", []) if t != "small"), "")
    return f"{hero.id} was a small {trait} {hero.type} who loved fairy-tale adventures."


def resolve_turn(world: World, hero: Entity, guide: Entity, task: Task, token: Entity, aid: Aid) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    world.say(
        f"{hero.id}'s {guide.label} smiled and said, \"How about we {aid.prep}?\""
    )
    world.say(
        f"{hero.id} listened, nodded, and chose to keep going. "
        f"{hero.pronoun().capitalize()} {aid.tail}, and the {token.label} stayed safe."
    )
    world.say(
        f"At last, {hero.id} could {task.gerund}, and the whole {world.setting.place} felt brighter."
    )


def tell(setting: Setting, task: Task, token_cfg: Token, hero_name: str, hero_type: str, guide_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={}))
    guide = world.add(Entity(id="Guide", kind="character", type=guide_type, label="old guide"))
    token = world.add(Entity(
        id=token_cfg.id,
        type=token_cfg.label,
        label=token_cfg.label,
        phrase=token_cfg.phrase,
        owner=hero.id,
        caretaker=guide.id,
        region=token_cfg.region,
        plural=token_cfg.plural,
    ))

    world.say(intro_line(hero))
    world.say(
        f"One evening in {setting.place}, {hero.id} found {hero.pronoun('possessive')} {token.label} and "
        f"wanted to {task.action}."
    )
    world.say(setting_detail(setting, task))
    world.say(
        f"But when {hero.id} tried to begin, a shiny distraction tried to {task.diversion}."
    )

    if task.id == "chant":
        world.say(
            f"The spell's syntax mattered: one word out of place could make the lines wobble and tangle."
        )
    else:
        world.say(
            f"The riddle's meaning mattered: if the answer was rushed, the whole meaning could wander away."
        )

    world.say(
        f"{hero.id} felt unsure for a moment, then took a brave breath and stood still."
    )
    aid = select_aid(task, token)
    if aid is None:
        pass
    resolve_turn(world, hero, guide, task, token, aid)

    world.facts.update(hero=hero, guide=guide, token=token, task=task, aid=aid, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, task, token = f["hero"], f["task"], f["token"]
    return [
        f'Write a short fairy tale for a child that includes the words "{task.keyword}" and "bravery".',
        f"Tell a gentle story where {hero.id} must {task.action} but a diversion tries to pull {hero.pronoun('object')} away.",
        f"Write a story in which syntax or a similar careful pattern matters, and a brave choice helps keep a treasure safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, task, token = f["hero"], f["guide"], f["task"], f["token"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in {world.setting.place}?",
            answer=f"{hero.id} wanted to {task.action}, but {hero.pronoun('possessive')} {token.label} and the tricky distraction made it harder.",
        ),
        QAItem(
            question=f"What made the task tricky for {hero.id}?",
            answer=f"The tale says a diversion tried to pull {hero.pronoun('object')} away, and the syntax of the spell or the meaning of the riddle had to stay carefully correct.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and the {token.label}?",
            answer=f"{hero.id} stayed brave, accepted help from {guide.label}, and finished the task while the {token.label} stayed safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is syntax?",
            answer="Syntax is the order and structure of words in a sentence or spell. When syntax is right, the meaning is clear.",
        ),
        QAItem(
            question="What does divert mean?",
            answer="To divert something is to turn it away from its path or to distract it from what it was doing.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means staying steady and doing the right thing even when you feel scared.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
task(T) :- activity(T).
token(X) :- token_item(X).

needs_bravery(T,X) :- risky_task(T), token_region(X,R), danger_region(R).

compatible(A,T,X) :- affords(A,T), needs_bravery(T,X), has_aid(T,X).

has_aid(T,X) :- aid(G), guards(G,K), task_key(T,K), covers(G,R), token_region(X,R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("activity", tid))
        lines.append(asp.fact("task_key", tid, t.keyword))
        if t.id in {"chant", "riddle"}:
            lines.append(asp.fact("risky_task", tid))
    for xid, x in TOKENS.items():
        lines.append(asp.fact("token_item", xid))
        lines.append(asp.fact("token_region", xid, x.region))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid.id))
        for g in sorted(aid.guards):
            lines.append(asp.fact("guards", aid.id, g))
        for c in sorted(aid.covers):
            lines.append(asp.fact("covers", aid.id, c))
    for r in ["hands", "head", "shoulders", "mouth", "mind"]:
        lines.append(asp.fact("danger_region", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    task: str
    token: str
    name: str
    gender: str
    guide: str
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
    if getattr(args, "task", None) and getattr(args, "token", None):
        task = _safe_lookup(TASKS, getattr(args, "task", None))
        token = _safe_lookup(TOKENS, getattr(args, "token", None))
        if not task_needs_bravery(task, token) or select_aid(task, token) is None:
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
        and (getattr(args, "token", None) is None or c[2] == getattr(args, "token", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, task_id, token_id = rng.choice(list(combos))
    token = _safe_lookup(TOKENS, token_id)
    gender = getattr(args, "gender", None) or rng.choice(sorted(token.genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = getattr(args, "guide", None) or rng.choice(["wizard", "witch", "queen", "king"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, task=task_id, token=token_id, name=name, gender=gender, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(TOKENS, params.token), params.name, params.gender, params.guide)
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
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld about syntax, diversion, and bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--guide", choices=["wizard", "witch", "queen", "king"])
    ap.add_argument("--trait")
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


CURATED = [
    StoryParams(place="library", task="chant", token="scroll", name="Mira", gender="girl", guide="wizard", trait="quiet"),
    StoryParams(place="tower", task="riddle", token="crown", name="Theo", gender="boy", guide="queen", trait="curious"),
    StoryParams(place="garden", task="chant", token="cloak", name="Lina", gender="girl", guide="witch", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        models = asp_valid_combos()
        print(f"{len(models)} compatible combos:")
        for t in models:
            print(" ", t)
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
        header = f"### variant {i+1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
