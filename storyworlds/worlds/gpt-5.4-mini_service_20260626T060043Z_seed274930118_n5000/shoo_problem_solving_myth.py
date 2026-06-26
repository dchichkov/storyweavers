#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/shoo_problem_solving_myth.py
==========================================================================================================

A small mythic storyworld about a young keeper, a troublesome sky-swarm,
and a clever shooing plan that restores peace.

Seed tale:
---
In an old valley, the bell garden kept the village safe. Each dawn, a cloud of
black birds came down and pecked the silver seeds before the people could gather
them. The old priest told the children to scare the birds away, but loud shouts
only made the birds circle back.

One morning, a young keeper named Mara watched the birds land again. She noticed
that the birds liked the shiny bowl of grain near the gate. So Mara fetched a
bright ribbon, tied it to a long reed, and walked slowly toward the gate. When
the birds hopped closer, she waved the ribbon and softly said, "Shoo, shoo."
The birds flapped up into the air, followed the ribbon for a moment, and then
drifted off to the far reeds.

The silver seeds stayed safe, and the priest smiled, saying Mara had won with
patience, not with noise.

World premise:
- A sacred bell garden stores silver seed for the village.
- A sky-swarm of crows/spirits pecks the seed unless outwitted.
- Loud force is ineffective; a calm, clever shooing plan works.

Causal updates:
- Planning lowers fear and raises hope.
- Loud shouts raise swarm anger; gentle shooing lowers it.
- The correct tool or decoy changes swarm attention and resolves the threat.
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    h: object | None = None
    p: object | None = None
    q: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def add_m(self, key: str, amount: float) -> None:
        self.meters[key] = self.m(key) + amount

    def add_e(self, key: str, amount: float) -> None:
        self.memes[key] = self.e(key) + amount

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "priest"}:
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
    place: str = "the bell garden"
    has_wind: bool = True
    sacred: bool = True
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
class Problem:
    id: str
    threat: str
    verb: str
    shoo_line: str
    mess: str
    zone: set[str]
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
class Tool:
    id: str
    label: str
    phrase: str
    use_line: str
    helps_with: set[str] = field(default_factory=set)
    calm: bool = False
    decoy: bool = False
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


THRESHOLD = 1.0

SETTINGS = {
    "bell_garden": Setting(place="the bell garden", has_wind=True, sacred=True, affords={"shoo", "decoy", "signal"}),
    "river_shrine": Setting(place="the river shrine", has_wind=True, sacred=True, affords={"shoo", "decoy"}),
    "moon_courtyard": Setting(place="the moon courtyard", has_wind=False, sacred=True, affords={"shoo", "signal"}),
}

PROBLEMS = {
    "crows": Problem(
        id="crows",
        threat="crows",
        verb="peck the silver seed",
        shoo_line="shoo, shoo",
        mess="scattered",
        zone={"seed", "ground"},
        tags={"bird", "seed", "dark"},
    ),
    "wisps": Problem(
        id="wisps",
        threat="wisps",
        verb="drift into the prayer bowls",
        shoo_line="shoo, little lights",
        mess="trembling",
        zone={"bowls", "altar"},
        tags={"spirit", "light", "wind"},
    ),
    "goats": Problem(
        id="goats",
        threat="goats",
        verb="nibble the lantern herbs",
        shoo_line="shoo, shoo, away",
        mess="trampled",
        zone={"herbs", "path"},
        tags={"animal", "herb", "garden"},
    ),
}

TOOLS = {
    "ribbon": Tool(
        id="ribbon",
        label="a bright ribbon",
        phrase="a bright ribbon tied to a reed",
        use_line="waved the ribbon slowly",
        helps_with={"crows", "wisps"},
        calm=True,
        decoy=True,
    ),
    "bell": Tool(
        id="bell",
        label="a hand bell",
        phrase="a hand bell with a clear note",
        use_line="rang the bell once, then waited",
        helps_with={"goats", "crows"},
        calm=True,
        decoy=False,
    ),
    "mirror": Tool(
        id="mirror",
        label="a little mirror",
        phrase="a little mirror on a cord",
        use_line="lifted the mirror toward the sky",
        helps_with={"wisps", "crows"},
        calm=False,
        decoy=True,
    ),
}

PRIZES = {
    "seed": Prize(id="seed", label="silver seed", phrase="silver seed in a shallow bowl", region="seed"),
    "candles": Prize(id="candles", label="prayer candles", phrase="prayer candles on the altar", region="altar"),
    "herbs": Prize(id="herbs", label="lantern herbs", phrase="lantern herbs by the path", region="path"),
}

HERO_NAMES = ["Mara", "Nia", "Sela", "Tarin", "Ivo", "Lio"]
HELPER_NAMES = ["the old priest", "the shrine keeper", "the grandmother", "the watchman"]


@dataclass
class StoryParams:
    place: str
    problem: str
    prize: str
    hero: str
    helper: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, s in SETTINGS.items():
        for pid in s.affords:
            for prize_id in PRIZES:
                if prize_at_risk(_safe_lookup(PROBLEMS, pid), _safe_lookup(PRIZES, prize_id)):
                    if select_tool(_safe_lookup(PROBLEMS, pid), _safe_lookup(PRIZES, prize_id)) is not None:
                        combos.append((place, pid, prize_id))
    return combos


def prize_at_risk(problem: Problem, prize: Prize) -> bool:
    return prize.region in problem.zone


def select_tool(problem: Problem, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS.values():
        if problem.id in tool.helps_with:
            return tool
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld about shooing trouble away with a clever plan.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
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
    if getattr(args, "problem", None) and getattr(args, "prize", None):
        if not (prize_at_risk(_safe_lookup(PROBLEMS, getattr(args, "problem", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))) and select_tool(_safe_lookup(PROBLEMS, getattr(args, "problem", None)), _safe_lookup(PRIZES, getattr(args, "prize", None)))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, prize = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, problem=problem, prize=prize, hero=hero, helper=helper)


def predict(world: World, problem: Problem, tool: Tool) -> dict:
    sim = world.copy()
    # louder start raises danger
    danger = 1.0
    if not tool.calm:
        danger += 1.0
    if tool.decoy:
        danger -= 0.5
    if danger <= 1.0:
        return {"resolved": True, "danger": danger}
    return {"resolved": False, "danger": danger}


def tell(setting: Setting, problem: Problem, prize: Prize, hero: str, helper: str) -> World:
    world = World(setting)
    h = world.add(Entity(id=hero, kind="character", type="girl", label=hero))
    p = world.add(Entity(id="helper", kind="character", type="priest", label=helper))
    q = world.add(Entity(id=prize.id, type=prize.id, label=prize.label, phrase=prize.phrase, region=prize.region))
    tool = select_tool(problem, prize)
    if tool is None:
        pass

    world.facts.update(hero=h, helper=p, prize=q, problem=problem, tool=tool, setting=setting)

    world.say(f"{h.id} lived near {setting.place}, where the old stones listened and the wind carried every prayer.")
    world.say(f"Each dawn, {problem.threat} would come and {problem.verb}, so the people guarded the {q.label} with worried hearts.")
    world.say(f"{h.id} loved the quiet bells, but she also loved thinking, and she wanted to help.")
    world.para()
    world.say(f"One bright morning, {helper} warned {h.id} that shouting would only make the trouble worse.")
    world.say(f"{h.id} watched carefully, then chose {tool.label} because it could pull the trouble aside without breaking the peace.")
    world.para()
    if tool.decoy:
        world.say(f"She {tool.use_line}, stepped forward, and said, \"{problem.shoo_line}!\"")
    else:
        world.say(f"She {tool.use_line}, rang the sound across the yard, and softly said, \"{problem.shoo_line}!\"")
    world.say(f"The {problem.threat} turned toward the false glitter and drifted away from the {q.label}.")
    world.say(f"When the danger faded, {helper} smiled and said that wisdom had shooed the trouble better than anger ever could.")
    world.para()
    world.say(f"By sunset, the {q.label} rested safe again, and the garden was calm enough to hear the bells breathe in the dark.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short myth for a child about how a clever keeper used "shoo" to save a sacred place.',
        f"Tell a gentle mythic story in which {f['hero'].id} solves the problem of {f['problem'].threat} with a calm tool and the word 'shoo'.",
        f"Make a simple legend about {f['hero'].id}, {f['helper'].label}, and {f['prize'].label} that ends with peace restored.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    prize = _safe_fact(world, f, "prize")
    problem = _safe_fact(world, f, "problem")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who solved the trouble in the {world.setting.place}?",
            answer=f"{hero.id} solved it with help from {helper.label}. She noticed what the {problem.threat} wanted and chose a calm plan.",
        ),
        QAItem(
            question=f"What did the trouble try to do to the {prize.label}?",
            answer=f"The {problem.threat} tried to {problem.verb}, which would have left the {prize.label} in danger.",
        ),
        QAItem(
            question=f"What did {hero.id} use to make the trouble leave?",
            answer=f"{hero.id} used {tool.label} and the word shoo. That gentle trick pulled the {problem.threat} away without harming anything.",
        ),
        QAItem(
            question=f"Why did the helper like {hero.id}'s idea?",
            answer=f"{helper.label} liked it because the plan was quiet, clever, and safe. It solved the problem instead of making the trouble fiercer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to shoo something away?",
            answer="To shoo something away means to make it leave a place, usually by waving, calling softly, or using a gentle scare.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an old story people tell about heroes, strange creatures, and big lessons about the world.",
        ),
        QAItem(
            question="Why can a clever plan be better than shouting?",
            answer="A clever plan can solve the trouble without causing more fear or damage, so it often works better than loud shouting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PROBLEMS, params.problem), _safe_lookup(PRIZES, params.prize), params.hero, params.helper)
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
problem_risk(P, R) :- threatens(P, R).
tool_fits(T, P, R) :- helps(T, P), threatens(P, R).
valid_story(Place, P, R) :- affords(Place, P), problem_risk(P, R), tool_fits(T, P, R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for z in sorted(p.zone):
            lines.append(asp.fact("threatens", pid, z))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(t.helps_with):
            lines.append(asp.fact("helps", tid, p))
    for rid, r in PRIZES.items():
        lines.append(asp.fact("prize", rid))
        lines.append(asp.fact("worn_on", rid, r.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="bell_garden", problem="crows", prize="seed", hero="Mara", helper="the old priest"),
    StoryParams(place="river_shrine", problem="wisps", prize="candles", hero="Nia", helper="the shrine keeper"),
    StoryParams(place="moon_courtyard", problem="goats", prize="herbs", hero="Sela", helper="the grandmother"),
]


def explain_rejection(problem: Problem, prize: Prize) -> str:
    return f"(No story: {problem.threat} do not naturally threaten {prize.label} in a way this world can solve.)"


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
            header = f"### {p.hero}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
