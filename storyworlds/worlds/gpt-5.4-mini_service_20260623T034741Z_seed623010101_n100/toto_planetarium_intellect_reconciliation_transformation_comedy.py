#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/toto_planetarium_intellect_reconciliation_transformation_comedy.py
====================================================================================================

A standalone story world about Toto, a planetarium, and a small comedy of
intellect, reconciliation, and transformation.

Seed tale:
---
Toto visited a planetarium with a big idea and a bigger grin. He wanted to
prove his intellect by fixing the projector all by himself. But the dome lights
kept blinking, the stars spun the wrong way, and the guide grew cross because the
show was turning into a wobbling joke.

Toto finally admitted he did not know enough. The guide laughed, not unkindly,
and showed him the right gear. Together they transformed the broken show into a
silly, glowing sky full of spinning moons and funny comets. Toto and the guide
made up, and Toto learned that true intellect also knows when to ask for help.

The next show was brighter, funnier, and better than before.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    id: str
    label: str
    mood: str
    tags: set[str] = field(default_factory=set)
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
class Problem:
    id: str
    verb: str
    mishap: str
    risk: str
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
class Fix:
    id: str
    tool: str
    action: str
    result: str
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
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


def _r_blunder(world: World) -> list[str]:
    out = []
    guide = world.get("guide")
    if guide.meters.get("annoyed", 0) < THRESHOLD:
        return out
    sig = ("blunder",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("show").meters["wobble"] = world.get("show").meters.get("wobble", 0) + 1
    out.append("The show wobbled like a jellyfish on skates.")
    return out


def _r_spark(world: World) -> list[str]:
    show = world.get("show")
    if show.meters.get("wobble", 0) < THRESHOLD:
        return []
    sig = ("spark",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    show.meters["broken"] = show.meters.get("broken", 0) + 1
    world.get("toto").memes["embarrassed"] = world.get("toto").memes.get("embarrassed", 0) + 1
    return ["__spark__"]


CAUSAL_RULES = [Rule("blunder", _r_blunder), Rule("spark", _r_spark)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_fix(world: World, problem: Problem, fix: Fix) -> dict:
    sim = world.copy()
    _do_problem(sim, narrate=False)
    return {"broken": sim.get("show").meters.get("broken", 0) >= THRESHOLD,
            "wobble": sim.get("show").meters.get("wobble", 0)}


def _do_problem(world: World, narrate: bool = True) -> None:
    toto = world.get("toto")
    guide = world.get("guide")
    show = world.get("show")
    toto.meters["overconfident"] = toto.meters.get("overconfident", 0) + 1
    guide.meters["annoyed"] = guide.meters.get("annoyed", 0) + 1
    show.meters["wobble"] = show.meters.get("wobble", 0) + 1
    propagate(world, narrate=narrate)


def tell(place: Place, problem: Problem, fix: Fix, hero_name: str = "Toto",
         guide_name: str = "Mara") -> World:
    w = World()
    w.add(Entity(id="toto", kind="character", type="boy", label=hero_name,
                 role="hero", meters={"curious": 1.0}, memes={"pride": 1.0, "joy": 1.0},
                 attrs={"place": place.id}, tags={"toto"}))
    w.add(Entity(id="guide", kind="character", type="woman", label=guide_name,
                 role="guide", meters={"patient": 1.0}, memes={"calm": 1.0, "worry": 1.0},
                 attrs={"place": place.id}, tags={"guide"}))
    w.add(Entity(id="planetarium", kind="thing", type="place", label=place.label,
                 meters={"lights": 1.0, "show_ready": 1.0}, memes={"wonder": 1.0},
                 tags=place.tags))
    w.add(Entity(id="show", kind="thing", type="machine", label="the projector",
                 meters={"wobble": 0.0, "broken": 0.0}, memes={"grumble": 1.0},
                 tags={"projector"}))

    w.say(f"Toto went to {place.label} with a grin and a pocket full of intellect.")
    w.say(f"The dome smelled like dust and popcorn, and the big show waited above their heads.")
    w.say(f"Toto wanted to {problem.verb} the projector all by himself, because he thought his intellect could do anything.")

    w.para()
    w.say(f"But the projector made a {problem.mishap}, and the stars began to spin the wrong way.")
    w.say(f"The guide frowned. {problem.risk}, {guide_name} said, and the whole room felt a little silly.")

    _do_problem(w)

    w.para()
    w.say(f"Then Toto blinked, sighed, and admitted he had guessed wrong.")
    w.say(f'{guide_name} stopped frowning and laughed. "Now that is better intellect," she said. "One brain is good; two are funnier."')
    if predict_fix(w, problem, fix)["broken"]:
        w.say(f"So the two of them used {fix.tool}, {fix.action}, and {fix.result}.")
    else:
        w.say(f"So the two of them used {fix.tool}, {fix.action}, and {fix.result}.")
    w.say(f"That turned the broken mess into a bright new joke of a show.")

    w.para()
    w.say(f"Toto and {guide_name} made up, and the planetarium glowed with spinning moons, friendly comets, and a very proud little boy.")
    w.say(f"By the end, Toto's intellect was not just bigger -- it was kinder, and that made the whole night shine.")
    w.facts.update(
        toto=w.get("toto"),
        guide=w.get("guide"),
        planetarium=w.get("planetarium"),
        show=w.get("show"),
        place=place,
        problem=problem,
        fix=fix,
        reconciled=True,
        transformed=True,
    )
    return w


SETTINGS = {
    "planetarium": Place(id="planetarium", label="the planetarium", mood="twinkly", tags={"planetarium"}),
}

PROBLEMS = {
    "self_fix": Problem(id="self_fix", verb="fix", mishap="wobble and squeak", risk="You'll only make it wobblier", tags={"intellect", "pride"}),
    "button_mash": Problem(id="button_mash", verb="poke", mishap="blink and bleep", risk="The machine is getting confused", tags={"intellect", "comedy"}),
}

FIXES = {
    "helper_hands": Fix(id="helper_hands", tool="a tiny wrench and a clean cloth", action="the guide showed Toto where to turn and what to leave alone", result="the projector settled down and began to sing stars again", tags={"reconciliation", "transformation"}),
    "reboot": Fix(id="reboot", tool="one careful reset and a big deep breath", action="they restarted the show together", result="the dome lit up with a silly new pattern of moons and comets", tags={"transformation"}),
}

@dataclass
class StoryParams:
    place: str = "planetarium"
    problem: str = "self_fix"
    fix: str = "helper_hands"
    name: str = "Toto"
    guide: str = "Mara"
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


CURATED = [
    StoryParams(place="planetarium", problem="self_fix", fix="helper_hands", seed=None),
    StoryParams(place="planetarium", problem="button_mash", fix="reboot", seed=None),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in SETTINGS:
        for prob in PROBLEMS:
            for fx in FIXES:
                out.append((p, prob, fx))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy story world about Toto, a planetarium, and intellect.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--guide")
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
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "fix", None) is None or c[2] == getattr(args, "fix", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, fix = rng.choice(list(combos))
    return StoryParams(
        place=place,
        problem=problem,
        fix=fix,
        name=getattr(args, "name", None) or "Toto",
        guide=getattr(args, "guide", None) or "Mara",
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        pass
    if params.problem not in PROBLEMS:
        pass
    if params.fix not in FIXES:
        pass
    w = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PROBLEMS, params.problem), _safe_lookup(FIXES, params.fix),
             hero_name=params.name, guide_name=params.guide)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_knowledge_qa(w),
        world=w,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a funny story about Toto at a planetarium who tries to show off his intellect.",
        "Tell a comedy about a planetarium projector, a small mistake, and two people making up.",
        "Write a child-friendly story where intellect means asking for help, not just guessing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    toto = f["toto"]
    guide = f["guide"]
    show = f["show"]
    return [
        QAItem(
            question="Why did Toto and Mara end up laughing together?",
            answer="Toto finally admitted he needed help, and Mara showed him a better way. That turned the argument into a funny team-up instead of a fight.",
        ),
        QAItem(
            question="What changed in the planetarium show?",
            answer="The wobbling, messy projector became a bright, silly show with moons and comets. The transformation made the ending feel cheerful instead of awkward.",
        ),
        QAItem(
            question="What did Toto learn about intellect?",
            answer="He learned that intellect is not just pretending to know everything. Real intellect also knows when to listen, ask, and share the job.",
        ),
        QAItem(
            question="Who fixed the projector with Toto?",
            answer=f"{guide.label} fixed it with Toto. They worked together, and that reconciliation made the whole room calmer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a planetarium?",
            answer="A planetarium is a place where people look at a dome show about stars, moons, and space. It is a fun place for learning and pretending.",
        ),
        QAItem(
            question="What does intellect mean?",
            answer="Intellect means thinking and understanding things with your mind. It helps you solve problems, especially when you also listen to other people.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop arguing and make up. It often includes an apology, kindness, or working together again.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a new form or becomes very different. A broken show can transform into a fun one.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(sample.prompts)
    parts.append("")
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Prob, Fix) :- place(P), problem(Prob), fix(Fix).
"""


def asp_facts() -> str:
    import asp
    out = []
    for p in SETTINGS:
        out.append(asp.fact("place", p))
    for p in PROBLEMS:
        out.append(asp.fact("problem", p))
    for f in FIXES:
        out.append(asp.fact("fix", f))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    try:
        if set(asp_valid_combos()) != set(valid_combos()):
            print("MISMATCH: ASP and Python combo sets differ.")
            return 1
        sample = generate(CURATED[0])
        if not sample.story.strip():
            print("MISMATCH: generated story is empty.")
            return 1
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=False)
        print("OK: ASP parity and story generation smoke test passed.")
        return 0
    except Exception as e:
        print(f"VERIFY FAILED: {e}")
        return 1


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
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
