#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/rumpus_teamwork_bedtime_story.py
==================================================================================

A tiny bedtime-story world about a late-evening rumpus that only settles when
everybody works together.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    kid: object | None = None
    parent: object | None = None
    sibling: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
    quiet: str
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
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    noise: str
    zone: set[str]
    bedtime_hint: str
    keyword: str = "rumpus"
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
class CleanUpTool:
    id: str
    label: str
    purpose: str
    helps_with: set[str]
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


@dataclass
class StoryParams:
    place: str
    activity: str
    tool: str
    name: str
    sibling: str
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


def story_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        pieces = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            pieces.append(f"meters={meters}")
        if memes:
            pieces.append(f"memes={memes}")
        if e.plural:
            pieces.append("plural=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(pieces)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("rumpus", 0.0) < THRESHOLD:
            continue
        sig = ("noise", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["tired"] = actor.memes.get("tired", 0.0) + 1.0
        out.append(f"The little rumpus made the room feel too bright for sleep.")
    return out


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("rumpus", 0.0) < THRESHOLD:
            continue
        sig = ("mess", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["mess"] = actor.meters.get("mess", 0.0) + 1.0
        out.append(f"Books slid a little, and pillows ended up on the floor.")
    return out


def _r_restore_quiet(world: World) -> list[str]:
    out: list[str] = []
    helper_ids = [e.id for e in world.entities.values() if e.kind == "thing" and e.type == "tool" and e.worn_by]
    if not helper_ids:
        return out
    helper = world.get(helper_ids[0])
    for actor in world.characters():
        if actor.meters.get("mess", 0.0) < THRESHOLD:
            continue
        sig = ("restore", actor.id, helper.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["calm"] = actor.memes.get("calm", 0.0) + 1.0
        actor.meters["mess"] = 0.0
        actor.meters["rumpus"] = 0.0
        out.append("With gentle hands and the right helper, the room grew soft and tidy again.")
    return out


CAUSAL_RULES = [_r_noise, _r_mess, _r_restore_quiet]


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


def choose_tool(activity: Activity, tool: CleanUpTool) -> bool:
    return activity.id in tool.helps_with


def reasonableness_gate(activity: Activity, tool: CleanUpTool) -> bool:
    return choose_tool(activity, tool)


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    activity = _safe_lookup(ACTIVITIES, params.activity)
    tool = _safe_lookup(TOOLS, params.tool)

    if not reasonableness_gate(activity, tool):
        pass

    world = World(setting)
    kid = world.add(Entity(id=params.name, kind="character", type="child"))
    sibling = world.add(Entity(id=params.sibling, kind="character", type="child"))
    parent = world.add(Entity(id=params.parent, kind="character", type="adult"))
    helper = world.add(Entity(
        id=tool.id,
        kind="thing",
        type="tool",
        label=tool.label,
        owner=parent.id,
    ))
    helper.worn_by = parent.id

    kid.memes["sleepy"] = 1.0
    sibling.memes["sleepy"] = 1.0

    world.say(f"At bedtime, {kid.id} and {sibling.id} were in {setting.place}, where the air was {setting.quiet}.")
    world.say(f"They loved {activity.gerund}, and the tiny noise felt like a secret game.")
    world.say(f"{kid.id} wanted to {activity.verb}, but {parent.id} noticed the {activity.keyword} getting bigger.")

    world.para()
    world.say(f'"If we do not slow down, the {activity.bedtime_hint}," {parent.id} said, with a gentle voice.')
    kid.meters["rumpus"] += 1.0
    sibling.meters["rumpus"] += 1.0
    propagate(world)

    world.para()
    world.say(f"{kid.id} looked at {sibling.id}, and they both knew the room needed teamwork.")
    world.say(f"{parent.id} brought out {tool.label}, because {tool.purpose}.")
    if reasonableness_gate(activity, tool):
        world.say(f"Together, they used the {tool.label}, and each small job became easy.")
        kid.memes["pride"] = kid.memes.get("pride", 0.0) + 1.0
        sibling.memes["pride"] = sibling.memes.get("pride", 0.0) + 1.0
        prop = propagate(world)
        if prop:
            world.say("The last bit of rumpus faded, and the room felt ready for a story and a song.")
        else:
            world.say("Soon the room was tidy again, and the sleepy silence came back.")
    world.say(f"At last, {kid.id} and {sibling.id} climbed into bed while {parent.id} smiled in the doorway.")

    world.facts.update(
        kid=kid,
        sibling=sibling,
        parent=parent,
        activity=activity,
        tool=tool,
        setting=setting,
        resolved=True,
    )
    return world


SETTINGS = {
    "nursery": Setting(place="the nursery", quiet="warm and hushed", affords={"blocks", "toys", "songs"}),
    "bedroom": Setting(place="the bedroom", quiet="soft and sleepy", affords={"blocks", "toys", "books"}),
    "playroom": Setting(place="the playroom", quiet="dim and cozy", affords={"blocks", "toys", "puzzles"}),
}

ACTIVITIES = {
    "blocks": Activity(
        id="blocks",
        verb="stack the tallest tower",
        gerund="stacking blocks",
        mess="blocks",
        noise="clatter",
        zone={"floor"},
        bedtime_hint="tower might tumble again",
        keyword="blocks",
    ),
    "toys": Activity(
        id="toys",
        verb="race the toy animals",
        gerund="making toy tracks",
        mess="toys",
        noise="tap-tap",
        zone={"floor"},
        bedtime_hint="the animals would keep galloping",
        keyword="toys",
    ),
    "songs": Activity(
        id="songs",
        verb="sing one more song",
        gerund="singing songs",
        mess="songs",
        noise="humming",
        zone={"air"},
        bedtime_hint="the moon would listen all night",
        keyword="songs",
    ),
    "books": Activity(
        id="books",
        verb="flip through one more book",
        gerund="reading books",
        mess="books",
        noise="rustle",
        zone={"bed"},
        bedtime_hint="the pages would keep whispering",
        keyword="books",
    ),
}

TOOLS = {
    "basket": CleanUpTool(
        id="basket",
        label="a toy basket",
        purpose="all the little toys could be gathered quickly",
        helps_with={"toys"},
    ),
    "bin": CleanUpTool(
        id="bin",
        label="a block bin",
        purpose="the blocks could be scooped up before they rolled away",
        helps_with={"blocks"},
    ),
    "bookstack": CleanUpTool(
        id="bookstack",
        label="a book stack",
        purpose="the books could be placed back in a neat pile",
        helps_with={"books"},
    ),
    "blanket": CleanUpTool(
        id="blanket",
        label="a soft blanket",
        purpose="it could wrap the sleepy room in quiet",
        helps_with={"songs"},
    ),
}

NAMES = ["Mia", "Nora", "Eli", "Luca", "Rose", "Theo", "Ava", "Finn"]
TRAITS = ["gentle", "curious", "bouncy", "sweet", "spirited"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for tool_id, tool in TOOLS.items():
                if choose_tool(_safe_lookup(ACTIVITIES, act), tool):
                    combos.append((place, act, tool_id))
    return combos


def explain_rejection(activity: Activity, tool: CleanUpTool) -> str:
    return f"(No story: {tool.label} does not help settle a {activity.keyword} rumpus.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid, sibling, act, tool = f["kid"], f["sibling"], f["activity"], (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write a bedtime story for a small child about a "rumpus" that settles through teamwork.',
        f"Tell a gentle story where {kid.id} and {sibling.id} make a {act.keyword} rumpus and then calm it with {tool.label}.",
        f"Write a cozy bedtime story set in {world.setting.place} with a little rumpus, a helper, and a sleepy ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid, sibling, parent, act, tool = f["kid"], f["sibling"], f["parent"], f["activity"], (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who made the rumpus in {world.setting.place}?",
            answer=f"{kid.id} and {sibling.id} made the rumpus together while {parent.id} watched kindly.",
        ),
        QAItem(
            question=f"What did {parent.id} bring to help with the {act.keyword} mess?",
            answer=f"{parent.id} brought {tool.label}, because {tool.purpose}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The children worked with {parent.id}, the rumpus got small and quiet, and everybody settled into bed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other do a job together.",
        ),
        QAItem(
            question="What is a rumpus?",
            answer="A rumpus is a noisy, lively bit of play where everything feels a little too busy.",
        ),
        QAItem(
            question="Why do children get sleepy at bedtime?",
            answer="Children get sleepy at bedtime because their bodies and minds are ready to rest after a long day.",
        ),
    ]


ASP_RULES = r"""
% A bedtime rumpus is settled when a helpful tool matches the activity.
compatible(T, A) :- tool(T), activity(A), helps_with(T, A).

% If a child has rumpus and a compatible tool is present, teamwork resolves it.
resolved(A) :- rumpus(A), compatible(_, A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", aid, z))
        lines.append(asp.fact("helps_with", aid, aid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for a in sorted(t.helps_with):
            lines.append(asp.fact("helps_with", tid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((t, a) for _, a, t in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about a rumpus and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--sibling")
    ap.add_argument("--parent", default="Mom", help="parent name")
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "activity", None):
        combos = [c for c in combos if c[1] == getattr(args, "activity", None)]
    if getattr(args, "tool", None):
        combos = [c for c in combos if c[2] == getattr(args, "tool", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, tool = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    sibling = getattr(args, "sibling", None) or rng.choice([n for n in NAMES if n != name])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, tool=tool, name=name, sibling=sibling, parent=getattr(args, "parent", None), trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(story_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="nursery", activity="blocks", tool="bin", name="Mia", sibling="Noah", parent="Mom", trait="gentle"),
    StoryParams(place="bedroom", activity="books", tool="bookstack", name="Eli", sibling="Rose", parent="Dad", trait="curious"),
    StoryParams(place="playroom", activity="toys", tool="basket", name="Ava", sibling="Finn", parent="Mom", trait="bouncy"),
    StoryParams(place="nursery", activity="songs", tool="blanket", name="Theo", sibling="Luca", parent="Dad", trait="sweet"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (tool, activity) pairs:\n")
        for tool, act in combos:
            print(f"  {tool:10} {act}")
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

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
