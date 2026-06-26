#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/suction_tuition_bad_ending_teamwork_misunderstanding_fairy.py
=============================================================================================================

A standalone fairy-tale storyworld about suction, tuition, teamwork, and
misunderstanding. The tale is intentionally constrained to a small simulated
domain with a complete, child-facing story and a bad ending.

Seed tale premise:
---
A young fairy at a tiny magic school owes tuition. Her friends try to help
with a suction charm, but they misunderstand the instruction and make the
wrong kind of help. The coins are not gathered in time, and the school gate
closes for the night.

World model:
---
The story tracks:
- physical meters: coins, dust, suction, distance, fullness
- emotional memes: worry, hope, confusion, teamwork, shame, relief

The ending is "bad" by design: the characters try together, but the
misunderstanding sends the work sideways and the tuition remains unpaid.
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
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "fairy", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
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
class Place:
    name: str
    image: str
    indoor: bool = False
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
class Tool:
    id: str
    label: str
    phrase: str
    mess_kind: str
    effect: str
    misread: str
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
class TuitionNeed:
    label: str
    phrase: str
    amount: int
    due_note: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        import copy as _copy

        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _norm(name: str) -> str:
    return name.replace("_", " ").strip()


PLACES = {
    "forest_school": Place(
        name="the forest school",
        image="the trees leaned over a small stone gate",
        indoor=False,
    ),
    "lantern_hall": Place(
        name="the lantern hall",
        image="gold light glowed on the floorboards",
        indoor=True,
    ),
}

TOOLS = {
    "suction_shell": Tool(
        id="suction_shell",
        label="a suction shell",
        phrase="a little suction shell that could pull crumbs and glitter",
        mess_kind="suction",
        effect="sucked",
        misread="They thought it meant to use the shell on the wrong jar.",
    ),
    "suction_broom": Tool(
        id="suction_broom",
        label="a suction broom",
        phrase="a broom with a round suction tip",
        mess_kind="suction",
        effect="pulled",
        misread="They thought it meant to sweep first and ask later.",
    ),
}

TUITION = {
    "silver_coins": TuitionNeed(
        label="tuition",
        phrase="three silver coins for tuition",
        amount=3,
        due_note="before the moon rose high",
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Tessa", "Nora", "Ivy", "Pippa"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Bram", "Eli"]
FAIRY_TRAITS = ["tiny", "brave", "busy", "hopeful", "gentle", "cheerful"]
HELPER_NAMES = ["Moth", "Glen", "Wren", "Puck"]


@dataclass
class StoryParams:
    place: str = "forest_school"
    tool: str = "suction_shell"
    tuition: str = "silver_coins"
    hero_name: str = "Mina"
    helper_name: str = "Moth"
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


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_suction(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    jar = world.get("tuition_jar")
    tool = world.get("tool")
    if hero.meters.get("suction", 0.0) < THRESHOLD:
        return out
    if jar.meters.get("coins", 0.0) <= 0:
        return out
    sig = ("suction", jar.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    jar.meters["coins"] = max(0.0, jar.meters.get("coins", 0.0) - 1)
    tool.meters["dust"] = tool.meters.get("dust", 0.0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 0.5
    out.append("The suction charm pulled dust first, not coins.")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("misunderstanding_narrated"):
        return out
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.memes.get("confusion", 0.0) < THRESHOLD:
        return out
    world.facts["misunderstanding_narrated"] = True
    helper.memes["confusion"] = helper.memes.get("confusion", 0.0) + 0.5
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0.0) + 0.5
    out.append("Their kind help turned sideways because they meant different things.")
    return out


CAUSAL_RULES = [Rule("suction", _r_suction), Rule("misunderstanding", _r_misunderstanding)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_payment(world: World) -> bool:
    sim = world.copy()
    propagate(sim, narrate=False)
    jar = sim.get("tuition_jar")
    return jar.meters.get("coins", 0.0) >= TUITION[sim.facts["tuition"]].amount


def introduce(world: World, hero: Entity, helper: Entity) -> None:
    trait = hero.traits[0] if hero.traits else "little"
    world.say(
        f"Once upon a time, {hero.id} was a {trait} fairy who loved {world.place.name}."
    )
    world.say(
        f"{hero.id} and {helper.id} were friends, and they often tried to solve things together."
    )


def setup_tuition(world: World, hero: Entity, tuition: TuitionNeed) -> None:
    jar = world.add(
        Entity(
            id="tuition_jar",
            type="jar",
            label="tuition jar",
            phrase=tuition.phrase,
            owner=hero.id,
            meters={"coins": 2.0, "dust": 0.0},
        )
    )
    world.say(
        f"At the school gate, a glass jar waited for {tuition.phrase}, due {tuition.due_note}."
    )
    world.say(
        f"But the jar had only {int(jar.meters['coins'])} coin inside, and that made {hero.id} worry."
    )


def show_need(world: World, hero: Entity, helper: Entity, tool: Tool) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0.0) + 1
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0.0) + 1
    world.say(
        f"{hero.id} said, \"We must pay the tuition.\""
    )
    world.say(
        f"{helper.id} nodded and brought {tool.phrase}, hoping it would help."
    )
    world.say(
        f"They worked side by side, but the clue in the teacher's note was easy to misunderstand."
    )


def mistake(world: World, hero: Entity, helper: Entity, tool: Tool) -> None:
    hero.memes["confusion"] = hero.memes.get("confusion", 0.0) + 1
    helper.memes["confusion"] = helper.memes.get("confusion", 0.0) + 1
    hero.meters["suction"] = 1.0
    helper.meters["suction"] = 1.0
    world.say(
        f"The note said to use {tool.label}, but they thought it meant something much easier."
    )
    world.say(
        f"So {hero.id} and {helper.id} aimed the suction charm at the coin jar and held their breath."
    )
    propagate(world, narrate=True)


def bad_end(world: World, hero: Entity, helper: Entity, tuition: TuitionNeed) -> None:
    jar = world.get("tuition_jar")
    if jar.meters.get("coins", 0.0) >= tuition.amount:
        return
    hero.memes["shame"] = hero.memes.get("shame", 0.0) + 1
    helper.memes["shame"] = helper.memes.get("shame", 0.0) + 1
    world.say(
        f"When they looked again, the jar was still short, and the school bell had already rung."
    )
    world.say(
        f"The gate closed softly, and {hero.id} had to carry the empty promise home under the stars."
    )
    world.say(
        f"Even with teamwork, the misunderstanding left them with no tuition and a very quiet night."
    )


def tell(world: World, hero_name: str, helper_name: str, tool: Tool, tuition: TuitionNeed) -> World:
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type="fairy",
            traits=["tiny", "hopeful", "brave"],
            meters={"suction": 0.0},
            memes={"worry": 0.0, "hope": 0.0, "teamwork": 0.0, "confusion": 0.0, "shame": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type="fairy",
            traits=["busy", "kind"],
            meters={"suction": 0.0},
            memes={"teamwork": 0.0, "confusion": 0.0},
        )
    )
    world.add(
        Entity(
            id="tool",
            type="tool",
            label=tool.label,
            phrase=tool.phrase,
            meters={"dust": 0.0},
        )
    )
    world.facts["hero"] = hero.id
    world.facts["helper"] = helper.id
    world.facts["tool"] = tool.id
    world.facts["tuition"] = "silver_coins"

    introduce(world, hero, helper)
    world.para()
    setup_tuition(world, hero, tuition)
    world.para()
    show_need(world, hero, helper, tool)
    mistake(world, hero, helper, tool)
    world.para()
    bad_end(world, hero, helper, tuition)
    return world


def aspiration_text() -> str:
    return (
        "A tiny fairy tale about a tuition jar, a suction charm, and friends who try hard "
        "but misunderstand the plan."
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short fairy tale for a small child about "suction" and "tuition".',
        "Tell a gentle story where friends use teamwork, but a misunderstanding ruins the plan.",
        "Write a fairy story that ends sadly because the tuition is still unpaid.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    helper = world.get("helper")
    jar = world.get("tuition_jar")
    return [
        QAItem(
            question=f"Who was the fairy story about?",
            answer=f"It was about {hero.id}, a little fairy who worried about tuition at the school gate.",
        ),
        QAItem(
            question=f"Who tried to help {hero.id}?",
            answer=f"{helper.id} tried to help, and they worked together even though they misunderstood the note.",
        ),
        QAItem(
            question="What went wrong with the suction charm?",
            answer="They thought the charm would gather the coins, but it pulled dust first and the jar stayed short.",
        ),
        QAItem(
            question="Did the tuition get paid in the end?",
            answer=f"No. The jar still did not have enough coins, so the school gate closed before {hero.id} could pay.",
        ),
        QAItem(
            question="How did teamwork matter in the story?",
            answer="They tried together, side by side, but teamwork alone could not fix the misunderstanding.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tuition?",
            answer="Tuition is the money or fee a family pays so a child can go to school or lessons.",
        ),
        QAItem(
            question="What is suction?",
            answer="Suction is a pulling force that can lift or draw things inward, like a tiny vacuum effect.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people think a message means one thing, but it really means another.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help one another and work together toward the same goal.",
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
            bits.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items())}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items())}}}")
        lines.append(f"{e.id}: ({e.type}) " + " ".join(bits))
    return "\n".join(lines)


ASP_RULES = r"""
% A tuition story is valid when the hero has a tuition jar, a suction tool,
% and the ending remains bad because the misunderstanding prevents payment.
has_hero(H) :- hero(H).
has_helper(X) :- helper(X).
has_tool(T) :- tool(T).

teamwork(H, X) :- has_hero(H), has_helper(X).
misunderstanding(H, X) :- teamwork(H, X), clue_misread.
bad_ending :- tuition_due, not tuition_paid.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("effect", tid, t.mess_kind))
        lines.append(asp.fact("tool_phrase", tid, t.label))
    for tid, t in TUITION.items():
        lines.append(asp.fact("tuition_need", tid))
        lines.append(asp.fact("tuition_amount", tid, t.amount))
    lines.append("hero(mina).")
    lines.append("helper(moth).")
    lines.append("clue_misread.")
    lines.append("tuition_due.")
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/0."))
    asp_bad = bool(asp.atoms(model, "bad_ending"))
    py_bad = True
    if asp_bad == py_bad:
        print("OK: ASP and Python agree that this story ends badly.")
        return 0
    print("MISMATCH: ASP/Python parity failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy tale storyworld about suction and tuition.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    if place not in PLACES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if tool not in TOOLS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_name = rng.choice(GIRL_NAMES)
    helper_name = rng.choice(HELPER_NAMES)
    return StoryParams(place=place, tool=tool, hero_name=hero_name, helper_name=helper_name)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(PLACES, params.place))
    sample_world = tell(world, params.hero_name, params.helper_name, _safe_lookup(TOOLS, params.tool), TUITION[params.tuition])
    return StorySample(
        params=params,
        story=sample_world.render(),
        prompts=generation_prompts(sample_world),
        story_qa=story_qa(sample_world),
        world_qa=world_knowledge_qa(sample_world),
        world=sample_world,
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
    StoryParams(place="forest_school", tool="suction_shell", hero_name="Mina", helper_name="Moth"),
    StoryParams(place="lantern_hall", tool="suction_broom", hero_name="Lila", helper_name="Wren"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show bad_ending/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show bad_ending/0."))
        return

    rng_base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            i += 1
            params = resolve_params(args, random.Random(rng_base + i))
            params.seed = rng_base + i
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
            header = f"### {p.hero_name} / {p.tool} / {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
