#!/usr/bin/env python3
"""
storyworlds/worlds/tint_way_pot_dim_humor_sharing_suspense.py
=============================================================

A small space-adventure storyworld about a crew, a shaky way home, a dim pot
of tint, humor, sharing, and suspense.

Premise:
- A young space helper wants to tint a navigation panel for a festival beacon.
- The job needs a shared pot of glowing tint.
- The pot is too dim, so the crew must cooperate, improvise, and keep calm.

World shape:
- Physical meters: light, charge, tint, steady, distance, dimness.
- Emotional memes: worry, humor, trust, sharing, suspense, relief.

The story is intentionally compact and state-driven:
setup -> problem -> suspenseful teamwork -> shared fix -> ending image.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    friend: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad"}
        female = {"girl", "woman", "mother", "mom"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    affords: set[str] = field(default_factory=set)
    indoor: bool = False
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
class Job:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.light_mode: str = ""

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
        clone.light_mode = self.light_mode
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


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


def _r_dim(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters.get("tint", 0.0) >= THRESHOLD and e.meters.get("light", 0.0) < THRESHOLD:
            sig = ("dim", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["suspense"] = e.memes.get("suspense", 0.0) + 1
            out.append(f"The glow on {e.label or e.id} looked thin and dim.")
    return out


def _r_share(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.memes.get("sharing", 0.0) < THRESHOLD:
            continue
        sig = ("share", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["trust"] = e.memes.get("trust", 0.0) + 1
        out.append(f"{e.id} did not grab the job alone; {e.pronoun().capitalize()} shared the work.")
    return out


def _r_humor(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.memes.get("humor", 0.0) < THRESHOLD:
            continue
        sig = ("humor", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{e.id} gave a tiny laugh, and the room felt less sharp.")
    return out


CAUSAL_RULES = [Rule("dim", _r_dim), Rule("share", _r_share), Rule("humor", _r_humor)]


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


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for jid, j in JOBS.items():
        lines.append(asp.fact("job", jid))
        lines.append(asp.fact("mess_of", jid, j.mess))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", gid, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", gid, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(J, P) :- job(J), prize(P), splashes(J, R), worn_on(P, R).
protects(G, J, P) :- gear(G), prize_at_risk(J, P), guards(G, M), mess_of(J, M), covers(G, R), worn_on(P, R).
has_fix(J, P) :- protects(_, J, P).
valid_story(S, J, P, G) :- affords(S, J), prize_at_risk(J, P), has_fix(J, P), wears(G, P).
valid(S, J, P) :- affords(S, J), prize_at_risk(J, P), has_fix(J, P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_jobs() -> list[tuple[str, str, str]]:
    out = []
    for s, setting in SETTINGS.items():
        for j in setting.affords:
            job = _safe_lookup(JOBS, j)
            for p, prize in PRIZES.items():
                if prize.region in job.zone and select_gear(job, prize):
                    out.append((s, j, p))
    return out


def select_gear(job: Job, prize: Prize) -> Optional[Gear]:
    for gear in GEAR.values():
        if job.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict(world: World, hero: Entity, job: Job, prize_id: str) -> dict:
    sim = world.copy()
    _do_job(sim, sim.get(hero.id), job, narrate=False)
    prize = sim.entities[prize_id]
    return {"damaged": prize.meters.get(job.mess, 0.0) >= THRESHOLD}


def _do_job(world: World, actor: Entity, job: Job, narrate: bool = True) -> None:
    actor.meters[job.mess] = actor.meters.get(job.mess, 0.0) + 1
    actor.memes["suspense"] = actor.memes.get("suspense", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "young"), "brave")
    world.say(f"{hero.id} was a young {trait} space helper who loved every bright control panel.")


def setup(world: World, hero: Entity, friend: Entity, prize: Entity, job: Job) -> None:
    world.say(
        f"{hero.id} wanted to {job.verb}, and {friend.id} had brought a shared pot of tint."
    )
    world.say(
        f"{hero.id} loved the job because the {job.keyword} made the ship feel like a parade float in the stars."
    )
    prize.worn_by = hero.id
    world.say(f"{friend.id} handed over {prize.phrase}, and {hero.id} kept it close.")


def warning(world: World, friend: Entity, hero: Entity, job: Job, prize: Prize) -> bool:
    pred = predict(world, hero, job, prize.id)
    if not pred["damaged"]:
        return False
    world.facts["risk"] = True
    world.say(
        f'"Careful," {friend.id} said. "If you rush the {job.keyword}, your {prize.label} could get ruined."'
    )
    return True


def joke(world: World, hero: Entity) -> None:
    hero.memes["humor"] = hero.memes.get("humor", 0.0) + 1
    world.say(f"{hero.id} snorted a laugh and called the pot 'the dim star soup.'")


def share_plan(world: World, friend: Entity, hero: Entity, job: Job, prize: Prize) -> Optional[Gear]:
    gear = select_gear(job, prize)
    if gear is None:
        return None
    hero.memes["sharing"] = hero.memes.get("sharing", 0.0) + 1
    friend.memes["sharing"] = friend.memes.get("sharing", 0.0) + 1
    world.say(
        f"{friend.id} smiled. 'Let's use {gear.label} first, and we can still {job.verb} safely.'"
    )
    return gear


def accept(world: World, hero: Entity, friend: Entity, gear: Gear, prize: Prize, job: Job) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    friend.memes["trust"] = friend.memes.get("trust", 0.0) + 1
    world.say(
        f"{hero.id} nodded, and together they followed the safer way: {gear.prep}."
    )
    world.say(
        f"Soon {hero.id} was {job.gerund}, the {prize.label} stayed bright, and the ship's path glowed steady again."
    )


def tell(setting: Setting, job: Job, prize_cfg: Prize, hero_name: str = "Nova", friend_name: str = "Pip",
         hero_type: str = "girl", friend_type: str = "boy") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["young", "brave", "curious"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, traits=["young", "funny", "careful"]))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                             region=prize_cfg.region, plural=prize_cfg.plural, owner=hero.id, caretaker=friend.id))

    intro(world, hero)
    world.para()
    setup(world, hero, friend, prize, job)
    warning(world, friend, hero, job, prize)
    joke(world, hero)
    world.para()
    gear = share_plan(world, friend, hero, job, prize)
    if gear:
        accept(world, hero, friend, gear, prize, job)
    world.facts.update(hero=hero, friend=friend, prize=prize, job=job, setting=setting, gear=gear)
    return world


SETTINGS = {
    "dock": Setting(place="the moon dock", affords={"tint_way"}, indoor=True),
    "bay": Setting(place="the star bay", affords={"tint_way"}, indoor=True),
    "hall": Setting(place="the launch hall", affords={"tint_way"}, indoor=True),
}

JOBS = {
    "tint_way": Job(
        id="tint_way",
        verb="tint the way marker",
        gerund="tinting the way marker",
        rush="dash toward the panel",
        mess="dim",
        soil="too dim",
        keyword="way",
        tags={"way", "tint", "suspense", "sharing", "humor"},
    ),
}

PRIZES = {
    "cap": Prize(label="cap", phrase="a shiny captain's cap", type="cap", region="torso"),
    "badge": Prize(label="badge", phrase="a bright pilot badge", type="badge", region="torso"),
}

GEAR = {
    "lamp": Gear(id="lamp", label="a small lamp shield", covers={"torso"}, guards={"dim"}, prep="clip on the lamp shield", tail="kept the lamp shield on"),
}


GIRL_NAMES = ["Nova", "Luna", "Mira", "Zia", "Tess"]
BOY_NAMES = ["Pip", "Jett", "Rafe", "Kai", "Finn"]
TRAITS = ["brave", "curious", "bouncy", "cheerful", "sly"]


@dataclass
class StoryParams:
    place: str
    job: str
    prize: str
    name: str
    friend: str
    gender: str
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


def story_prompts(world: World) -> list[str]:
    f = world.facts
    hero, job, prize = f["hero"], f["job"], f["prize"]
    return [
        f'Write a short space-adventure story for a young child about "{job.keyword}", a shared problem, and a funny fix.',
        f"Tell a story where {hero.id} wants to {job.verb} but the pot is too dim, so {f['friend'].id} helps.",
        f"Write a gentle suspense story about a crew sharing one tool to make a way home glow again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, job = f["hero"], f["friend"], f["prize"], f["job"]
    gear = f.get("gear")
    qs = [
        QAItem(
            question=f"What did {hero.id} want to do with the shared pot at {world.setting.place}?",
            answer=f"{hero.id} wanted to {job.verb}, because the {job.keyword} made the ship's way look bright and friendly.",
        ),
        QAItem(
            question=f"Why did {friend.id} warn {hero.id} about the {prize.label}?",
            answer=f"{friend.id} warned {hero.id} because the way marker could end up {job.soil}, which would not fit the shiny {prize.label}.",
        ),
        QAItem(
            question=f"What made the story funny instead of only scary?",
            answer=f"{hero.id} joked that the pot was 'the dim star soup,' and that little laugh softened the suspense.",
        ),
    ]
    if gear:
        qs.append(QAItem(
            question=f"How did {gear.label} help the crew share the job safely?",
            answer=f"They used {gear.label} first, so they could {job.verb} without ruining the {prize.label}.",
        ))
        qs.append(QAItem(
            question=f"How did the story end for {hero.id} and {friend.id}?",
            answer=f"They finished together, with {hero.id} {job.gerund} and {friend.id} smiling because the way glowed steady again.",
        ))
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tint?",
            answer="Tint is a little bit of color added to something to change how it looks.",
        ),
        QAItem(
            question="What does a way marker do?",
            answer="A way marker helps people see where to go, like a sign or glowing guide.",
        ),
        QAItem(
            question="Why can a dim light feel spooky?",
            answer="A dim light leaves more shadows, so things are harder to see and can feel mysterious.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items())}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items())}}}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="dock", job="tint_way", prize="cap", name="Nova", friend="Pip", gender="girl"),
    StoryParams(place="bay", job="tint_way", prize="badge", name="Mira", friend="Jett", gender="girl"),
]


def explain_rejection(job: Job, prize: Prize) -> str:
    return f"(No story: {job.verb} does not reasonably threaten a {prize.label} in this world.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(PRIZES, prize_id).genders))
    return f"(No story: try --gender {ok} for this prize.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with tint, way, pot-dim humor, sharing, and suspense.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--job", choices=JOBS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    if getattr(args, "job", None) and getattr(args, "prize", None):
        job, prize = _safe_lookup(JOBS, getattr(args, "job", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not select_gear(job, prize):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_jobs()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "job", None) is None or c[1] == getattr(args, "job", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, job, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = getattr(args, "friend", None) or rng.choice(BOY_NAMES if gender == "girl" else GIRL_NAMES)
    return StoryParams(place=place, job=job, prize=prize, name=name, friend=friend, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(JOBS, params.job), _safe_lookup(PRIZES, params.prize), params.name, params.friend, params.gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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


def asp_valid_jobs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_jobs())
    cl = set(asp_valid_jobs())
    if py == cl:
        print(f"OK: clingo gate matches valid_jobs() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_jobs()
        print(f"{len(triples)} compatible (place, job, prize) combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
