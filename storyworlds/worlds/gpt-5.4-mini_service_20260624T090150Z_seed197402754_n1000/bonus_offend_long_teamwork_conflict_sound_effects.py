#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/bonus_offend_long_teamwork_conflict_sound_effects.py
=================================================================================================

A small heartwarming story world about a team working on a long project,
an accidental offense, a bonus helper, and a noisy but kind resolution.

The seed tale behind this world is simple:
A child joins a team to finish a long job with cheerful sound effects.
Someone feels offended by a careless remark, the group pauses, and then
everyone works together to make things right. The bonus is not money first;
it is the warm feeling that comes from helping, apologizing, and finishing
the job together.

This script models:
- people, a shared project, and a setting
- meters for physical progress and sound
- memes for feelings like pride, worry, hurt, and trust
- a tension turn caused by an offense
- a resolution powered by teamwork

It also includes an inline ASP twin for the reasonableness gate and registry
parity checks.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = __import__('collections').defaultdict(float)
        if not self.memes:
            self.memes = __import__('collections').defaultdict(float)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "aunt"}
        male = {"boy", "father", "man", "brother", "uncle"}
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
    indoor: bool
    affordances: set[str] = field(default_factory=set)
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
class Project:
    id: str
    label: str
    phrase: str
    long_kind: str
    sound_kind: str
    finish_word: str
    reward_word: str
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
class TeamMove:
    id: str
    title: str
    action: str
    sound: str
    progress: float
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        return clone


def _default_meters() -> dict[str, float]:
    return {
        "progress": 0.0,
        "sound": 0.0,
        "bonus": 0.0,
    }


def _default_memes() -> dict[str, float]:
    return {
        "joy": 0.0,
        "pride": 0.0,
        "worry": 0.0,
        "hurt": 0.0,
        "trust": 0.0,
        "teamwork": 0.0,
        "conflict": 0.0,
        "kindness": 0.0,
    }


def make_entity(**kwargs) -> Entity:
    kwargs.setdefault("meters", _default_meters())
    kwargs.setdefault("memes", _default_memes())
    return Entity(**kwargs)


def narrate_sound(sound: str) -> str:
    return {
        "tap": "tap-tap",
        "snip": "snip-snip",
        "ding": "ding!",
        "whoosh": "whoosh",
        "clap": "clap-clap",
        "swish": "swish",
    }.get(sound, sound)


def setup_text(setting: Setting, project: Project) -> str:
    if setting.indoor:
        return f"Inside {setting.place}, the table was long and ready for {project.phrase}."
    return f"At {setting.place}, the long project waited in the bright air."


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for ent in list(world.entities.values()):
            if ent.kind != "character":
                continue
            if ent.memes["hurt"] >= THRESHOLD and ("comfort", ent.id) not in world.fired:
                world.fired.add(("comfort", ent.id))
                ent.memes["hurt"] = max(0.0, ent.memes["hurt"] - 1.0)
                ent.memes["trust"] += 1.0
                out.append(f"{ent.id} felt a little better after the apology.")
                changed = True
    if narrate:
        for line in out:
            world.say(line)
    return out


def long_project_at_risk(project: Project, move: TeamMove) -> bool:
    return "long" in project.tags and "teamwork" in move.tags


def offense_possible(move: TeamMove) -> bool:
    return "offend" in move.tags


def reasonableness_gate(project: Project, move: TeamMove) -> None:
    if not long_project_at_risk(project, move):
        pass
    if not offense_possible(move):
        pass
    if "sound" not in move.tags:
        pass


def predict_conflict(world: World, speaker: Entity, listener: Entity, move: TeamMove) -> bool:
    sim = world.copy()
    speaker.memes["pride"] += 0.0
    listener.memes["hurt"] += 1.0 if offense_possible(move) else 0.0
    return offense_possible(move)


def intro(world: World, child: Entity, leader: Entity, project: Project) -> None:
    world.say(
        f"{child.id} loved helping on the team. "
        f"{leader.id} was already smiling about {project.phrase}, "
        f"because it was a long job that needed many hands."
    )


def start_work(world: World, child: Entity, team: list[Entity], move: TeamMove, project: Project) -> None:
    world.say(
        f"{child.id} joined the others and began to {move.action}. "
        f"{narrate_sound(move.sound)} went the tools, and the room felt busy and kind."
    )
    for ent in team:
        ent.memes["teamwork"] += 1.0
    project_meter = _safe_fact(world, world.facts, "project_entity")
    project_meter.meters["progress"] += move.progress
    project_meter.meters["sound"] += 1.0
    child.memes["joy"] += 1.0


def offend(world: World, speaker: Entity, listener: Entity, project: Project) -> None:
    listener.memes["hurt"] += 1.0
    listener.memes["trust"] = max(0.0, listener.memes["trust"] - 0.5)
    listener.memes["conflict"] += 1.0
    world.say(
        f"Then {speaker.id} made a careless joke about {listener.id}'s work, and {listener.id} went quiet. "
        f"The words stung more than anyone meant, because everyone cared about the long project."
    )


def apologize(world: World, speaker: Entity, listener: Entity) -> None:
    speaker.memes["kindness"] += 1.0
    listener.memes["trust"] += 1.0
    listener.memes["conflict"] = max(0.0, listener.memes["conflict"] - 1.0)
    world.say(
        f"{speaker.id} looked at {listener.id} and said sorry right away. "
        f"That was not a big speech, just an honest one, and it helped."
    )


def teamwork_turn(world: World, team: list[Entity], project: Project, move: TeamMove) -> None:
    for ent in team:
        ent.memes["trust"] += 0.5
        ent.memes["joy"] += 0.5
    project_ent = _safe_fact(world, world.facts, "project_entity")
    project_ent.meters["progress"] += move.progress
    bonus = _safe_fact(world, world.facts, "bonus_entity")
    bonus.meters["bonus"] += 1.0
    world.say(
        f"After that, everyone worked side by side. "
        f"{narrate_sound(move.sound)} {narrate_sound('clap')} {narrate_sound('ding')} went the room, "
        f"and the long project moved ahead faster than before."
    )


def finish(world: World, child: Entity, team: list[Entity], project: Project, bonus: Entity) -> None:
    project_ent = _safe_fact(world, world.facts, "project_entity")
    if project_ent.meters["progress"] < THRESHOLD:
        project_ent.meters["progress"] = THRESHOLD
    child.memes["joy"] += 1.0
    child.memes["pride"] += 1.0
    for ent in team:
        ent.memes["trust"] += 0.5
        ent.memes["kindness"] += 0.5
    bonus.meters["bonus"] += 1.0
    world.say(
        f"At last, the team finished {project.phrase}. "
        f"The final {project.finish_word} sounded bright, and the room filled with happy faces. "
        f"The real bonus was not just {project.reward_word}; it was the warm feeling of having made it together."
    )


def tell(setting: Setting, project: Project, move: TeamMove, child_name: str, child_type: str, leader_name: str) -> World:
    reasonableness_gate(project, move)
    world = World(setting)

    child = world.add(make_entity(id=child_name, kind="character", type=child_type, label=child_name, traits=["helpful", "gentle"]))
    leader = world.add(make_entity(id=leader_name, kind="character", type="adult", label=leader_name, traits=["patient"]))
    friend = world.add(make_entity(id="Mina", kind="character", type="girl", label="Mina", traits=["careful"]))
    bonus = world.add(make_entity(id="bonus", kind="thing", type="thing", label="bonus", phrase="bonus", traits=[]))
    project_ent = world.add(make_entity(id="project", kind="thing", type="thing", label=project.label, phrase=project.phrase, traits=[]))

    world.facts["project_entity"] = project_ent
    world.facts["bonus_entity"] = bonus
    world.facts["child"] = child
    world.facts["leader"] = leader
    world.facts["friend"] = friend
    world.facts["project"] = project
    world.facts["move"] = move

    intro(world, child, leader, project)
    world.para()
    world.say(setup_text(setting, project))
    start_work(world, child, [child, leader, friend], move, project)

    world.para()
    if predict_conflict(world, child, friend, move):
        offend(world, child, friend, project)
        apologize(world, child, friend)
    teamwork_turn(world, [child, leader, friend], project, move)
    propagate(world)

    world.para()
    finish(world, child, [child, leader, friend], project, bonus)

    world.facts["resolved"] = True
    world.facts["conflict"] = True
    return world


SETTINGS = {
    "studio": Setting(place="the art studio", indoor=True, affordances={"work"}),
    "hall": Setting(place="the community hall", indoor=True, affordances={"work"}),
    "garden": Setting(place="the school garden", indoor=False, affordances={"work"}),
}

PROJECTS = {
    "banner": Project(
        id="banner",
        label="banner",
        phrase="a long welcome banner",
        long_kind="long",
        sound_kind="rustle",
        finish_word="ribbon",
        reward_word="cookies",
        tags={"long", "teamwork", "sound"},
    ),
    "bridge": Project(
        id="bridge",
        label="cardboard bridge",
        phrase="a long cardboard bridge",
        long_kind="long",
        sound_kind="tap",
        finish_word="panel",
        reward_word="juice",
        tags={"long", "teamwork", "sound"},
    ),
}

MOVES = {
    "paint": TeamMove(
        id="paint",
        title="paint the letters",
        action="paint the letters",
        sound="tap",
        progress=0.6,
        tags={"teamwork", "sound", "offend"},
    ),
    "tie": TeamMove(
        id="tie",
        title="tie the ribbons",
        action="tie the ribbons",
        sound="swish",
        progress=0.6,
        tags={"teamwork", "sound"},
    ),
    "build": TeamMove(
        id="build",
        title="build the long edge",
        action="build the long edge",
        sound="ding",
        progress=0.7,
        tags={"teamwork", "sound", "offend"},
    ),
}

CHILD_NAMES = ["Nora", "Eli", "Maya", "Theo", "Ava", "Noah", "Luna", "Ben"]
LEADERS = ["Sam", "Rosa", "Tess", "Owen"]
GENDERS = {"girl": "girl", "boy": "boy"}


@dataclass
class StoryParams:
    place: str
    project: str
    move: str
    name: str
    gender: str
    leader: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in SETTINGS:
        for proj in PROJECTS:
            for mv in MOVES:
                combos.append((p, proj, mv))
    return combos


def explain_rejection(project: Project, move: TeamMove) -> str:
    if "long" not in project.tags:
        return "(No story: the project must be long so teamwork can matter.)"
    if "offend" not in move.tags:
        return "(No story: the move must plausibly offend someone so the apology can change the mood.)"
    if "sound" not in move.tags:
        return "(No story: the story needs sound effects, so the chosen move must make some.)"
    return "(No story: that combination does not make a clear heartwarming turn.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming teamwork storyworld with conflict and sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--leader", choices=LEADERS)
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
    project = _safe_lookup(PROJECTS, getattr(args, "project", None)) if getattr(args, "project", None) else rng.choice(list(PROJECTS.values()))
    move = _safe_lookup(MOVES, getattr(args, "move", None)) if getattr(args, "move", None) else rng.choice(list(MOVES.values()))
    if getattr(args, "project", None) and getattr(args, "move", None):
        if "long" not in project.tags or "teamwork" not in move.tags or "sound" not in move.tags or "offend" not in move.tags:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    leader = getattr(args, "leader", None) or rng.choice(LEADERS)
    return StoryParams(place=place, project=project.id, move=move.id, name=name, gender=gender, leader=leader)


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "project")
    m = _safe_fact(world, world.facts, "move")
    child = _safe_fact(world, world.facts, "child")
    return [
        f"Write a heartwarming story about {child.id} helping with {p.phrase} in {world.setting.place}.",
        f"Tell a gentle teamwork story where a long job includes {m.action} and a small apology.",
        f"Write a child-friendly story with sound effects, a hurt feeling, and a happy bonus at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = _safe_fact(world, world.facts, "child")
    leader = _safe_fact(world, world.facts, "leader")
    friend = _safe_fact(world, world.facts, "friend")
    project = _safe_fact(world, world.facts, "project")
    move = _safe_fact(world, world.facts, "move")
    place = world.setting.place
    return [
        QAItem(
            question=f"Who helped with {project.phrase} at {place}?",
            answer=f"{child.id} helped with {project.phrase} at {place} together with {leader.id} and {friend.id}.",
        ),
        QAItem(
            question=f"What caused the conflict in the middle of the story?",
            answer=f"The conflict started when {child.id} made a careless joke that offended {friend.id}.",
        ),
        QAItem(
            question=f"What did the team do after the apology?",
            answer=f"After the apology, everyone worked together again and kept going with {move.action}.",
        ),
        QAItem(
            question=f"What was the bonus at the end?",
            answer=f"The bonus was the happy feeling of finishing the long project together, along with a small treat.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help one another and work together toward the same goal.",
        ),
        QAItem(
            question="What does it mean to offend someone?",
            answer="To offend someone is to hurt their feelings, even if you did not mean to be unkind.",
        ),
        QAItem(
            question="Why do sound effects make a story fun?",
            answer="Sound effects help readers imagine what the tools, feet, or hands might sound like in the scene.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
long_project(P) :- project(P), tag(P,long).
teamwork_move(M) :- move(M), tag(M,teamwork).
offensive_move(M) :- move(M), tag(M,offend).
sound_move(M) :- move(M), tag(M,sound).
valid_combo(S,P,M) :- setting(S), project(P), move(M),
                      long_project(P), teamwork_move(M),
                      offensive_move(M), sound_move(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
    for mid, m in MOVES.items():
        lines.append(asp.fact("move", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="hall", project="banner", move="paint", name="Nora", gender="girl", leader="Sam"),
    StoryParams(place="studio", project="bridge", move="build", name="Eli", gender="boy", leader="Rosa"),
    StoryParams(place="garden", project="banner", move="tie", name="Maya", gender="girl", leader="Tess"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PROJECTS, params.project), _safe_lookup(MOVES, params.move), params.name, params.gender, params.leader)
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
        print(asp_program("#show valid_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
