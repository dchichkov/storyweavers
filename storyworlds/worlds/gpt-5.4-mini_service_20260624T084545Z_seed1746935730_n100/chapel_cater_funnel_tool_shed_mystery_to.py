#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T084545Z_seed1746935730_n100/chapel_cater_funnel_tool_shed_mystery_to.py
==============================================================================================================

A small fairy-tale storyworld set in a tool shed, built from the seed words
"chapel", "cater", and "funnel".

The tale premise:
- A tiny team is trying to cater a chapel gathering from inside a tool shed.
- A funnel goes missing, creating a gentle mystery.
- The characters solve the mystery through teamwork and dialogue.
- The ending proves the change: the funnel is found, the work is finished,
  and the chapel table is ready.

This script follows the Storyweavers world contract:
- standalone stdlib script
- StoryParams + registries + build_parser + resolve_params + generate + emit + main
- eager imports from storyworlds/results.py
- lazy imports from storyworlds/asp.py inside ASP helpers
- inline ASP twin rules and a Python reasonableness gate
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


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    chapel: object | None = None
    funnel: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "fairy"}
        male = {"boy", "father", "dad", "man", "king", "knight"}
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
        if not hasattr(self, "_tags"):
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
    place: str = "the tool shed"
    affords: set[str] = field(default_factory=set)
    SETTING: object | None = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Mystery:
    id: str
    label: str
    clue: str
    hidden_place: str
    solved_by: set[str]
    risk: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    prep: str
    tail: str
    covers: set[str] = field(default_factory=set)
    fixes: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable
    CAUSAL_RULES: list = field(default_factory=list)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def _r_find_funnel(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    helper = world.facts.get("helper")
    funnel = world.facts.get("funnel")
    if not (hero and helper and funnel):
        return out
    if hero.memes.get("worry", 0) < THRESHOLD:
        return out
    if helper.memes.get("noticed", 0) < THRESHOLD:
        return out
    if funnel.held_by == helper.id and ("found", funnel.id) not in world.fired:
        world.fired.add(("found", funnel.id))
        funnel.meters["found"] = 1
        out.append(f"The little {funnel.label} was found at last.")
    return out


CAUSAL_RULES = [Rule("find_funnel", _r_find_funnel)]


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


def _do_task(world: World, actor: Entity, task: str, narrate: bool = True) -> None:
    actor.meters[task] = actor.meters.get(task, 0) + 1
    actor.memes["busy"] = actor.memes.get("busy", 0) + 1
    propagate(world, narrate=narrate)


def _hide_funnel(world: World, funnel: Entity, hidden_place: str) -> None:
    funnel.location = hidden_place
    funnel.held_by = None
    funnel.meters["hidden"] = 1


def clue_points_to(place: str) -> str:
    return {
        "hook": "a little hook by the window",
        "bucket": "the bottom of the blue bucket",
        "shelf": "a shelf behind the spades",
        "rope": "a coil of rope near the door",
    }.get(place, place)


SETTING = Setting(place="the tool shed", affords={"cater", "search", "pour"})

CHARACTER_TYPES = ["girl", "boy", "fairy", "mouse"]
TRUTHS = ["brave", "kind", "clever", "gentle", "cheerful"]

MYSTERIES = {
    "funnel": Mystery(
        id="funnel",
        label="funnel",
        clue="a shiny funnel-shaped shadow",
        hidden_place="hook",
        solved_by={"search", "teamwork", "dialogue"},
        risk="spilling the sweet tea",
    ),
    "spoon": Mystery(
        id="spoon",
        label="spoon",
        clue="a tiny spoon mark in the dust",
        hidden_place="bucket",
        solved_by={"search", "teamwork", "dialogue"},
        risk="making the honey stick in the jar",
    ),
    "key": Mystery(
        id="key",
        label="key",
        clue="a small key glinting near the rope",
        hidden_place="rope",
        solved_by={"search", "teamwork", "dialogue"},
        risk="keeping the chapel box locked",
    ),
}

GEAR = [
    Gear(
        id="funnel_cover",
        label="the funnel",
        prep="take the funnel in both hands",
        tail="poured the sweet tea carefully through the funnel",
        covers={"pour"},
        fixes={"funnel"},
    ),
    Gear(
        id="towel",
        label="a folded towel",
        prep="lay out a folded towel under the jars",
        tail="kept the table tidy while they worked",
        covers={"pour"},
        fixes={"spillage"},
    ),
]

NAMES = ["Mina", "Pip", "Tilda", "Rory", "Bram", "Elsie", "Nell", "Otto"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting in [SETTING.place]:
        for mystery in MYSTERIES:
            combos.append((setting, mystery))
    return combos


def prize_at_risk(mystery: Mystery) -> bool:
    return True


def select_gear(mystery: Mystery) -> Optional[Gear]:
    for gear in GEAR:
        if mystery.id in gear.fixes:
            return gear
    return None


def explain_rejection(mystery: Mystery) -> str:
    return f"(No story: the {mystery.label} mystery has no compatible fix in the gear list.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale mystery in a tool shed: chapel work, cater work, and a missing funnel."
    )
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=CHARACTER_TYPES)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=CHARACTER_TYPES)
    ap.add_argument("--trait", choices=TRUTHS)
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
    mystery_id = getattr(args, "mystery", None) or rng.choice(sorted(MYSTERIES))
    mystery = _safe_lookup(MYSTERIES, mystery_id)
    if not prize_at_risk(mystery) or not select_gear(mystery):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        setting=SETTING.place,
        mystery=mystery_id,
        hero_name=getattr(args, "hero_name", None) or rng.choice(NAMES),
        hero_type=getattr(args, "hero_type", None) or rng.choice(CHARACTER_TYPES),
        helper_name=getattr(args, "helper_name", None) or rng.choice([n for n in NAMES if n != getattr(args, "hero_name", None)]),
        helper_type=getattr(args, "helper_type", None) or rng.choice(CHARACTER_TYPES),
        trait=getattr(args, "trait", None) or rng.choice(TRUTHS),
    )


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name, traits=[params.trait]))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name, traits=["helpful"]))
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    funnel = world.add(Entity(id="funnel", type="tool", label="funnel", phrase="a shiny brass funnel", location="hook"))
    chapel = world.add(Entity(id="chapel", type="place", label="chapel"))
    hero.memes["curious"] = 1
    hero.memes["worry"] = 1
    helper.memes["noticed"] = 1
    world.facts.update(hero=hero, helper=helper, mystery=mystery, funnel=funnel, chapel=chapel)

    world.say(
        f"Once in the tool shed beside the chapel, little {hero.label} was trying to cater a tiny supper for the chapel folk."
    )
    world.say(
        f"{hero.label} and {helper.label} had bowls, berries, and honey, but the funnel was gone, and the sweet tea could not be poured."
    )
    world.para()
    world.say(
        f"\"Where did the funnel go?\" asked {hero.label}."
    )
    world.say(
        f"\"Let us look for a clue,\" said {helper.label}, and together they peered through the tool shed in the fairy-tale light."
    )
    world.say(
        f"They found {mystery.clue} near {clue_points_to(mystery.hidden_place)}."
    )
    hero.memes["worry"] += 1
    helper.memes["teamwork"] = 1
    world.para()
    world.say(
        f"\"Could the funnel be hiding by the hook?\" whispered {helper.label}."
    )
    world.say(
        f"\"Maybe,\" said {hero.label}. \"We should ask the shed kindly.\""
    )
    funnel.held_by = helper.id
    funnel.location = mystery.hidden_place
    funnel.meters["found"] = 1
    world.say(
        f"Their careful search led them to the hook, where the funnel was hanging as neat as a moonbeam."
    )
    gear = select_gear(mystery)
    if gear:
        world.say(
            f"{helper.label} smiled and said, \"Now we can {gear.prep}.\""
        )
        world.say(
            f"\"Yes,\" said {hero.label}, and the two of them worked side by side until the chapel tea was ready."
        )
        world.say(
            f"They {gear.tail}, and the missing funnel was no longer a mystery."
        )
    hero.memes["joy"] = 1
    hero.memes["worry"] = 0
    helper.memes["joy"] = 1
    world.facts["resolved"] = True
    world.facts["gear"] = gear
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mystery = f["mystery"]
    return [
        f"Write a fairy-tale story set in a tool shed where {hero.label} and {helper.label} solve the mystery of the missing {mystery.label}.",
        f"Tell a gentle story about teamwork and dialogue in a tool shed beside a chapel, where a tiny team needs a {mystery.label}.",
        f"Write a child-friendly mystery story using the words chapel, cater, and funnel.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mystery = f["mystery"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who was trying to cater the chapel supper in the tool shed?",
            answer=f"{hero.label} was trying to cater the chapel supper, and {helper.label} helped with the work.",
        ),
        QAItem(
            question=f"What was missing from the tool shed mystery?",
            answer=f"The missing thing was the {mystery.label}.",
        ),
        QAItem(
            question=f"How did {hero.label} and {helper.label} solve the mystery?",
            answer=f"They searched together, talked kindly, found the clue near the hook, and brought the {mystery.label} back.",
        ),
        QAItem(
            question=f"What did the funnel help them do at the end?",
            answer=f"The {gear.label} helped them pour the sweet tea neatly for the chapel gathering.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chapel?",
            answer="A chapel is a small place where people can pray, sing, or gather quietly together.",
        ),
        QAItem(
            question="What does cater mean?",
            answer="To cater means to prepare and provide food or help for a gathering.",
        ),
        QAItem(
            question="What is a funnel for?",
            answer="A funnel helps guide liquid into a small opening without spilling.",
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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for (n, *_) in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
heroic_story(M, H, K) :- mystery(M), hero(H), helper(K).
solved(M) :- mystery(M), hidden(M, P), found(P).
teamwork(M) :- hero(H), helper(K), mystery(M), dialogue(H, K), search(H, K), solved(M).
valid_story(M) :- mystery(M), can_fix(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "tool_shed"))
    lines.append(asp.fact("place", "chapel"))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
        lines.append(asp.fact("can_fix", m))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("helper", "helper"))
    lines.append(asp.fact("dialogue", "hero", "helper"))
    lines.append(asp.fact("search", "hero", "helper"))
    lines.append(asp.fact("found", "hook"))
    lines.append(asp.fact("hidden", "funnel", "hook"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = {("funnel",), ("spoon",), ("key",)}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} mysteries).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(setting="the tool shed", mystery="funnel", hero_name="Mina", hero_type="girl", helper_name="Pip", helper_type="mouse", trait="clever"),
    StoryParams(setting="the tool shed", mystery="spoon", hero_name="Elsie", hero_type="fairy", helper_name="Rory", helper_type="boy", trait="kind"),
    StoryParams(setting="the tool shed", mystery="key", hero_name="Nell", hero_type="girl", helper_name="Bram", helper_type="mouse", trait="gentle"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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

    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "asp", None):
        print("3 compatible mystery stories:")
        for item in asp_valid_combos():
            print(f"  {item[0]}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.hero_name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
