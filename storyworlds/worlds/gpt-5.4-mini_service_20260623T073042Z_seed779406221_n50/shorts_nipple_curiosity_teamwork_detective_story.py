#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T073042Z_seed779406221_n50/shorts_nipple_curiosity_teamwork_detective_story.py
=============================================================================================================

A small standalone storyworld in a detective-story style.

Premise:
- A child detective is trying to find a missing pair of shorts.
- A baby bottle nipple becomes an odd clue.
- Curiosity and teamwork help the search.
- The ending proves what changed by showing the found shorts and the solved clue.

The world is intentionally tiny:
- one setting per story
- one missing object
- one clue object
- one helper
- a single state-driven resolution

The prose is child-facing and concrete, with the detective-story tone coming from
searching, clues, observations, and a final reveal.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

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
            keys = [upper + "S", upper + "ES"]
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    owner: Optional[str] = None
    location: str = ""
    found: bool = False

    clue: object | None = None
    detective: object | None = None
    helper: object | None = None
    shorts: object | None = None
    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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
    id: str
    place: str
    mood: str
    affordances: set[str] = field(default_factory=set)
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


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    place_hint: str
    tags: set[str] = field(default_factory=set)
    answer: str = ""
    question: str = ""
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Clue:
    id: str
    label: str
    phrase: str
    place_hint: str
    points_to: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_discover(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    clue = world.get("clue")
    shorts = world.get("shorts")
    if detective.memes["curiosity"] >= THRESHOLD and clue.meters["noticed"] >= THRESHOLD:
        sig = ("discover",)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["certainty"] += 1
            shorts.meters["found"] += 1
            shorts.found = True
            out.append("The clue finally made sense, and the missing shorts were found.")
    return out


CAUSAL_RULES = [Rule("discover", _r_discover)]


def detect_trace(world: World) -> None:
    detective = world.get("detective")
    helper = world.get("helper")
    detective.memes["curiosity"] += 1
    helper.memes["teamwork"] += 1
    world.say(
        f"{detective.label} looked over the room like a little detective. "
        f"{detective.label} loved curious questions, and {helper.label} liked to help."
    )
    world.say(
        f"One thing was missing: {world.get('shorts').label}. "
        f"The empty spot made the case feel important."
    )


def inspect_setting(world: World) -> None:
    clue = world.get("clue")
    detective = world.get("detective")
    world.say(
        f"The search started in {world.setting.place}, where the air felt "
        f"{world.setting.mood}. "
        f"{detective.label} followed the clue: {clue.phrase}."
    )
    clue.meters["noticed"] += 1
    detective.memes["curiosity"] += 1
    propagate(world)


def teamwork_turn(world: World) -> None:
    detective = world.get("detective")
    helper = world.get("helper")
    clue = world.get("clue")
    shorts = world.get("shorts")
    helper.memes["teamwork"] += 1
    detective.memes["teamwork"] += 1
    world.say(
        f"{helper.label} checked under the low shelf while {detective.label} "
        f"peeked near the basket. Together they noticed that {clue.label_word} "
        f"pointed toward {clue.place_hint}."
    )
    if not shorts.found:
        world.say(
            f"The clue was odd at first, but teamwork made it clearer. "
            f"{detective.label} and {helper.label} kept looking side by side."
        )


def resolve(world: World) -> None:
    detective = world.get("detective")
    helper = world.get("helper")
    shorts = world.get("shorts")
    detective.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At last, they found the shorts {world.get('shorts').location}. "
        f"The missing pair was safe again, and the case was solved."
    )
    world.say(
        f"{detective.label} smiled at {helper.label}. Curiosity had led the way, "
        f"and teamwork had finished the job."
    )


def tell(setting: Setting, hero_name: str, helper_name: str) -> World:
    world = World(setting)
    detective = world.add(Entity(
        id="detective",
        kind="character",
        type="child",
        label=hero_name,
        attrs={"role": "detective"},
        meters=defaultdict(float),
        memes=defaultdict(float),
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="child",
        label=helper_name,
        attrs={"role": "helper"},
        meters=defaultdict(float),
        memes=defaultdict(float),
    ))
    shorts = world.add(Entity(
        id="shorts",
        type="clothes",
        label="blue shorts",
        location="under the laundry basket",
        owner=detective.id,
        attrs={"kind": "shorts"},
        meters=defaultdict(float),
        memes=defaultdict(float),
    ))
    clue = world.add(Entity(
        id="clue",
        type="object",
        label="nipple clue",
        location="on the nursery shelf",
        attrs={"kind": "nipple"},
        meters=defaultdict(float),
        memes=defaultdict(float),
    ))
    world.facts["detective"] = detective
    world.facts["helper"] = helper
    world.facts["shorts"] = shorts
    world.facts["clue"] = clue

    detect_trace(world)
    world.para()
    inspect_setting(world)
    teamwork_turn(world)
    world.para()
    if shorts.found:
        resolve(world)
    else:
        world.say("They kept searching until the last clue fit.")
        shorts.found = True
        shorts.meters["found"] += 1
        resolve(world)

    world.facts.update(
        setting=setting,
        found=shorts.found,
    )
    return world


SETTINGS = {
    "nursery": Setting(id="nursery", place="the nursery", mood="quiet and tidy", affordances={"search"}),
    "laundry": Setting(id="laundry", place="the laundry room", mood="bright and busy", affordances={"search"}),
    "bedroom": Setting(id="bedroom", place="the bedroom", mood="soft and still", affordances={"search"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Ben"]


@dataclass
class StoryParams:
    setting: str
    detective: str
    helper: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, "curiosity", "teamwork") for s in SETTINGS]


ASP_RULES = r"""
setting(nursery). setting(laundry). setting(bedroom).
valid(S, curiosity, teamwork) :- setting(S).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("setting", s) for s in SETTINGS)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: ASP matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    print(" only in asp:", sorted(a - p))
    print(" only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style storyworld about shorts, a nipple clue, curiosity, and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
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
    combos = [c for c in valid_combos() if getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting = rng.choice([c[0] for c in combos])
    detective = getattr(args, "detective", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != detective])
    return StoryParams(setting=setting, detective=detective, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a young child where {f["detective"].label} and {f["helper"].label} search for missing shorts and notice a nipple clue.',
        f"Tell a curious teamwork story in {f['setting'].place} where blue shorts go missing and the clue is a nipple on a shelf.",
        f"Write a gentle mystery story with curiosity, teamwork, shorts, and a clue about a nipple that helps solve the case.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What was missing in the story?",
            answer=f"The missing thing was the blue shorts. The detective noticed they were gone and started looking for them.",
        ),
        QAItem(
            question=f"What clue did {f['detective'].label} follow?",
            answer=f"{f['detective'].label} followed a nipple clue on the nursery shelf. It was odd, but it helped point the search the right way.",
        ),
        QAItem(
            question=f"How did the children solve the case?",
            answer=f"They solved it by using curiosity and teamwork together. One looked while the other checked a different spot, and that helped them find the shorts.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is curiosity?", answer="Curiosity is the wish to look, ask, and learn about something new."),
        QAItem(question="What is teamwork?", answer="Teamwork means people help each other and do a job together."),
        QAItem(question="What are shorts?", answer="Shorts are a kind of clothing with short legs that people wear when they want to stay cool and move around easily."),
        QAItem(question="What is a nipple on a bottle?", answer="A bottle nipple is the soft top part of a baby bottle that a baby drinks from."),
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)} attrs={e.attrs}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), params.detective, params.helper)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for setting, a, b in combos:
            print(setting, a, b)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(setting=s, detective="Mia", helper="Leo")) for s in SETTINGS]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
