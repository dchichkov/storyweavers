#!/usr/bin/env python3
"""
storyworlds/worlds/traction_jaguar_teamwork_ghost_story.py
==========================================================

A small, child-facing story world about a spooky house, a stubborn jaguar,
and teamwork that gives enough traction to carry the day.

Seed impression:
---
A child finds a ghostly jaguar statue stuck on a slick old floor in a quiet,
creaky house. The statue is too heavy to drag safely. A friendly ghost warns
that it will slide and crash. The child and a helper gather a rug, a rope, and
a little courage. Together they make enough traction to move the jaguar to a
safe bright spot, and the house feels less spooky by the end.

World model:
---
- Physical meters track slipperiness, traction, weight shift, and whether the
  jaguar is safely placed.
- Emotional memes track worry, courage, relief, and teamwork.
- The story is generated from state transitions, not a frozen paragraph.

This script follows the Storyweavers world contract:
- self-contained stdlib script under storyworlds/worlds/
- eager import of storyworlds/results.py containers
- lazy import of storyworlds/asp.py inside ASP helpers
- parser, parameter resolution, generation, emission, and main
- inline ASP twin with parity verification
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
    moved_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    eerie: str
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
class Prize:
    label: str
    phrase: str
    type: str
    weight: str
    needs: set[str]
    base_slip: float
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
class Gear:
    id: str
    label: str
    phrase: str
    traction_bonus: float
    prep: str
    tail: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "attic": Setting(place="the attic", eerie="dusty", affords={"pull"}),
    "hall": Setting(place="the long hall", eerie="creaky", affords={"pull"}),
    "basement": Setting(place="the basement", eerie="cold", affords={"pull"}),
    "porch": Setting(place="the porch", eerie="moonlit", affords={"pull"}),
}

PRIZES = {
    "jaguar": Prize(
        label="jaguar",
        phrase="a heavy old jaguar statue",
        type="jaguar",
        weight="heavy",
        needs={"traction", "teamwork"},
        base_slip=1.0,
    ),
    "box": Prize(
        label="box",
        phrase="a dusty painted box with a jaguar on the lid",
        type="box",
        weight="heavy",
        needs={"traction", "teamwork"},
        base_slip=0.8,
    ),
}

GEAR = [
    Gear(
        id="rug",
        label="rug",
        phrase="an old wool rug",
        traction_bonus=1.0,
        prep="lay down an old wool rug first",
        tail="spread the rug under the jaguar",
    ),
    Gear(
        id="gloves",
        label="gloves",
        phrase="soft grip gloves",
        traction_bonus=0.3,
        prep="put on soft grip gloves",
        tail="held the jaguar more firmly",
    ),
    Gear(
        id="rope",
        label="rope",
        phrase="a sturdy rope",
        traction_bonus=0.7,
        prep="loop a sturdy rope around it",
        tail="pulled together on the rope",
    ),
]

GIRL_NAMES = ["Mira", "Luna", "Ivy", "Nora", "Mae", "June"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Ben", "Finn", "Max"]
TRAITS = ["careful", "curious", "brave", "kind", "quiet", "cheerful"]


@dataclass
class StoryParams:
    place: str
    prize: str
    name: str
    gender: str
    helper: str
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


def _m(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mm(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _add_meter(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + delta


def _add_meme(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + delta


def _do_setup(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} {hero.type} who loved quiet places with a little mystery."
    )
    world.say(
        f"In {world.setting.place}, the air was {world.setting.eerie}, and the old room felt like it was listening."
    )
    world.say(
        f"Then {hero.id} found {prize.phrase}. {hero.pronoun('possessive').capitalize()} helper, {helper.id}, "
        f"said, \"That looks like it might need teamwork.\""
    )
    _add_meme(hero, "wonder", 1.0)
    _add_meme(helper, "helpfulness", 1.0)
    prize.moved_by = hero.id


def _predict_slide(world: World, hero: Entity, prize: Entity, traction_bonus: float) -> dict:
    sim = world.copy()
    sim_hero = sim.get(hero.id)
    sim_prize = sim.get(prize.id)
    slip = sim_prize.meters.get("slip", prize.base_slip)
    traction = sim_prize.meters.get("traction", 0.0) + traction_bonus
    risk = slip - traction
    return {"risk": risk, "safe": risk <= 0.0}


def _warn(world: World, helper: Entity, hero: Entity, prize: Entity) -> bool:
    pred = _predict_slide(world, hero, prize, 0.0)
    if pred["safe"]:
        return False
    _add_meme(hero, "worry", 1.0)
    world.say(
        f'"Careful," {helper.id} whispered. "Without more traction, {prize.label} could slip and bump the wall."'
    )
    return True


def _gather_team(world: World, hero: Entity, helper: Entity) -> None:
    _add_meme(hero, "teamwork", 1.0)
    _add_meme(helper, "teamwork", 1.0)
    _add_meme(hero, "courage", 1.0)
    world.say(
        f"{hero.id} took a breath. {hero.pronoun().capitalize()} and {helper.id} decided to work as a team."
    )


def _use_gear(world: World, hero: Entity, prize: Entity) -> Gear:
    chosen = GEAR[0]
    for gear in GEAR:
        if gear.id == "rug":
            chosen = gear
            break
    _add_meter(prize, "traction", chosen.traction_bonus)
    world.say(f"They {chosen.prep}, and the floor stopped feeling so slippery.")
    return chosen


def _pull(world: World, hero: Entity, helper: Entity, prize: Entity, gear: Gear) -> None:
    _add_meter(prize, "pulled", 1.0)
    _add_meter(prize, "traction", 0.4)
    _add_meme(hero, "teamwork", 1.0)
    _add_meme(helper, "teamwork", 1.0)
    world.say(
        f"{hero.id} and {helper.id} {gear.tail}. The jaguar shifted a little, then a little more."
    )


def _settle(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    prize.moved_by = helper.id
    _add_meme(hero, "relief", 1.0)
    _add_meme(helper, "relief", 1.0)
    world.say(
        f"At last, the jaguar reached a safe patch of light. It did not slide, and nothing bumped or broke."
    )
    world.say(
        f"{hero.id} smiled at {helper.id}. The spooky room still creaked, but now it felt friendly."
    )


def tell(setting: Setting, prize_cfg: Prize, hero_name: str, hero_type: str, helper_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=[trait, "gentle"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type="ghost" if helper_name.lower().startswith("g") else "friend",
        traits=["helpful", "quiet"],
    ))
    prize = world.add(Entity(
        id=prize_cfg.type,
        kind="thing",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))
    _add_meter(prize, "slip", prize_cfg.base_slip)

    _do_setup(world, hero, helper, prize)
    world.para()
    _warn(world, helper, hero, prize)
    _gather_team(world, hero, helper)
    gear = _use_gear(world, hero, prize)
    _pull(world, hero, helper, prize, gear)
    _settle(world, hero, helper, prize)

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        prize_cfg=prize_cfg,
        setting=setting,
        gear=gear,
    )
    return world


def story_prompt(world: World) -> list[str]:
    f = world.facts
    hero, helper, prize = f["hero"], f["helper"], f["prize_cfg"]
    return [
        f'Write a short ghost story for a small child about {hero.id}, {helper.id}, and a {prize.label} that needs traction.',
        f"Tell a spooky but gentle story where teamwork helps move a jaguar without making a mess.",
        f'Write a child-friendly story set in {world.setting.place} that includes the words "traction" and "jaguar".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize = f["hero"], f["helper"], f["prize_cfg"]
    return [
        QAItem(
            question=f"What did {hero.id} find in {world.setting.place}?",
            answer=f"{hero.id} found {prize.phrase} in {world.setting.place}."
        ),
        QAItem(
            question=f"Why did {helper.id} warn {hero.id} about the jaguar?",
            answer=f"{helper.id} warned {hero.id} because the floor was slippery and the jaguar could slide and bump the wall."
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} move the jaguar safely?",
            answer="They worked together, laid down a rug for traction, and pulled the jaguar carefully on a rope."
        ),
        QAItem(
            question=f"How did the room feel at the end?",
            answer="The room still felt spooky and creaky, but it also felt friendly because the jaguar was safe and nothing broke."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does traction mean?",
            answer="Traction means grip or friction that helps something not slip on a floor or road."
        ),
        QAItem(
            question="What is a jaguar?",
            answer="A jaguar is a big spotted wild cat."
        ),
        QAItem(
            question="Why is teamwork helpful?",
            answer="Teamwork is helpful because when people work together, they can do hard jobs more safely and more easily."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in SETTINGS:
        for prize_id in PRIZES:
            out.append((place, prize_id))
    return out


def explain_rejection() -> str:
    return "(No story: this world only supports a gentle haunted-house jaguar rescue.)"


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: {_safe_lookup(PRIZES, prize_id).label} fits this world, but the requested gender '{gender}' is invalid here.)"


ASP_RULES = r"""
% A prize is at risk when it is slippery enough to slide.
at_risk(P) :- prize(P), slip(P,S), S > 0.

% Gear provides traction.
helps(G,P) :- gear(G), prize(P), traction_bonus(G,B), slip(P,S), S > B.

% Teamwork is required in this small domain: the rescue is valid only if a
% risky prize has a helper and a gear that overcomes the slip.
valid_story(Place, Prize) :- setting(Place), prize(Prize), at_risk(Prize), has_helper, has_gear, helps(_, Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("slip", pid, p.base_slip))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        lines.append(asp.fact("traction_bonus", g.id, g.traction_bonus))
    lines.append(asp.fact("has_helper"))
    lines.append(asp.fact("has_gear"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set((place, prize) for place, prize in valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP matches Python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" only in ASP:", sorted(clingo_set - python_set))
    print(" only in Python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost-story world about traction, a jaguar, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=TRAITS)
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
    prize_id = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    if getattr(args, "gender", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, prize_id).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["Ghost", "Mara", "Jae", "Pip"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, prize=prize_id, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PRIZES, params.prize), params.name, "girl" if params.gender == "girl" else "boy", params.helper, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompt(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="attic", prize="jaguar", name="Mira", gender="girl", helper="Ghost", trait="curious"),
    StoryParams(place="hall", prize="box", name="Eli", gender="boy", helper="Ghost", trait="brave"),
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
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for place, prize in combos:
            print(f"  {place} / {prize}")
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
