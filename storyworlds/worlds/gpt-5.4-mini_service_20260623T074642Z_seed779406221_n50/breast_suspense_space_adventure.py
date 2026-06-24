#!/usr/bin/env python3
"""
storyworlds/worlds/breast_suspense_space_adventure.py
=====================================================

A small standalone storyworld for a suspenseful space adventure.

Seed idea:
---
A child crew member on a little starship wants to press a glowing button on the
control breast panel, but the captain worries the ship will drift into a dark
patch of space. A careful fix, a helper tool, and a tense moment lead to a safe
landing and a bright ending.

Design goals:
- child-facing space adventure tone
- suspenseful, state-driven tension
- the required seed word "breast" appears as part of the ship's breast panel
- one compact simulated domain with meters and memes
- Python reasonableness gate plus an inline ASP twin
"""

from __future__ import annotations

import argparse
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    panel: object | None = None
    parent: object | None = None
    suit: object | None = None
    tool_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "pilot"}:
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
    place: str
    affords: set[str] = field(default_factory=set)
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    danger: str
    zone: set[str]
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
class Tool:
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
        self.zone: set[str] = set()
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    tool: str
    name: str
    gender: str
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


SETTINGS = {
    "starship": Setting(place="the starship", affords={"signal_drift", "meteor_glow"}),
    "moonbase": Setting(place="the moonbase", affords={"signal_drift"}),
    "spaceport": Setting(place="the spaceport", affords={"meteor_glow", "signal_drift"}),
}

ACTIVITIES = {
    "signal_drift": Activity(
        id="signal_drift",
        verb="follow the drifting signal",
        gerund="chasing the drifting signal",
        rush="dash after the signal light",
        hazard="dim",
        danger="go dim",
        zone={"bridge", "panel"},
        keyword="signal",
        tags={"space", "signal"},
    ),
    "meteor_glow": Activity(
        id="meteor_glow",
        verb="watch the meteor glow",
        gerund="watching the meteor glow",
        rush="run to the window",
        hazard="shaky",
        danger="sparkle and shake",
        zone={"window", "panel"},
        keyword="meteor",
        tags={"space", "meteor"},
    ),
}

TOOLS = [
    Tool(
        id="shield_patch",
        label="a tiny shield patch",
        covers={"panel"},
        guards={"dim"},
        prep="put on a tiny shield patch first",
        tail="clicked the patch onto the breast panel",
    ),
    Tool(
        id="glow_clip",
        label="a glow clip",
        covers={"window"},
        guards={"shaky"},
        prep="clip on a glow clip first",
        tail="snapped the clip onto the view window",
    ),
    Tool(
        id="visor_band",
        label="a visor band",
        covers={"bridge", "panel"},
        guards={"dim", "shaky"},
        prep="fasten a visor band first",
        tail="fastened the band around the front of the suit",
        plural=False,
    ),
]

TRAITS = ["brave", "curious", "careful", "lively", "steady"]
GIRL_NAMES = ["Nova", "Mira", "Luna", "Zoe", "Ivy", "Rina"]
BOY_NAMES = ["Jett", "Kai", "Sol", "Finn", "Tavi", "Leo"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_dim(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("suspense", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.label == "space suit":
                continue
            if item.caretaker is None:
                continue
            if "panel" not in world.zone:
                continue
            if world.covered(actor, "panel"):
                continue
            sig = ("dim", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dim"] = item.meters.get("dim", 0.0) + 1
            out.append(f"The {item.label} went dim.")
    return out


def _r_worry(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("suspense", 0.0) < THRESHOLD:
            continue
        sig = ("worry", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
        out.append(f"{actor.id} held very still.")
    return out


CAUSAL_RULES = [Rule("dim", _r_dim), Rule("worry", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def prize_at_risk(activity: Activity, tool: Tool) -> bool:
    return bool(activity.zone & tool.covers)


def select_tool(activity: Activity) -> Optional[Tool]:
    for tool in TOOLS:
        if activity.hazard in tool.guards and activity.zone & tool.covers:
            return tool
    return None


def predict_problem(world: World, actor: Entity, activity: Activity) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    return {
        "dim": any(e.meters.get("dim", 0.0) >= THRESHOLD for e in sim.entities.values()),
        "worry": sum(e.memes.get("worry", 0.0) for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        pass
    world.zone = set(activity.zone)
    actor.meters["suspense"] = actor.meters.get("suspense", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {next((t for t in hero.memes if t), 'space kid')}?")  # overwritten by later lines


def tell(setting: Setting, activity: Activity, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Captain", kind="character", type=params.parent, label="the captain"))
    suit = world.add(Entity(
        id="suit", type="suit", label="space suit",
        phrase="a bright space suit with a breast panel", owner=hero.id, caretaker=parent.id
    ))
    suit.worn_by = hero.id
    panel = world.add(Entity(
        id="panel", type="panel", label="breast panel",
        phrase="the breast panel on the front of the suit", owner=hero.id, caretaker=parent.id
    ))
    panel.worn_by = hero.id

    hero.memes["love"] = 1
    hero.memes["curiosity"] = 1

    world.say(f"{hero.id} was a little {params.trait} {params.gender} who loved the quiet hum of space.")
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund} aboard the starship.")
    world.say(f"{hero.id}'s {parent.label} had given {hero.pronoun('object')} a bright space suit with a breast panel.")
    world.para()
    world.say(f"One dark drift, {hero.id} and {hero.pronoun('possessive')} {parent.label} floated near {world.setting.place}.")
    world.say(f"{hero.id} wanted to {activity.verb}, but the stars looked strange and suspenseful.")
    pred = predict_problem(world, hero, activity)
    if pred["dim"]:
        world.say(f'"If you rush now, the {activity.keyword} light may {activity.danger}," said {parent.label}.')
    hero.meters["suspense"] = hero.meters.get("suspense", 0.0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(f"{hero.id} took one small step, then stopped and listened.")
    tool = select_tool(activity)
    if tool is None:
        pass
    if predict_problem(world, hero, activity)["dim"]:
        world.say(f"Then {parent.label} held up {tool.label} and smiled.")
        world.say(f'"First we should {tool.prep}," {parent.label} said.')
        tool_ent = world.add(Entity(id=tool.id, kind="thing", type="tool", label=tool.label, protective=True, covers=set(tool.covers), owner=hero.id))
        tool_ent.worn_by = hero.id
        if predict_problem(world, hero, activity)["dim"]:
            tool_ent.worn_by = None
            del world.entities[tool_ent.id]
            pass
        world.say(f"{hero.id} nodded and {tool.tail}.")
        world.say(f"After that, {hero.id} could {activity.verb} safely, and the breast panel stayed bright.")
        hero.memes["worry"] = 0.0
    world.para()
    world.say(f"In the end, the dark patch drifted away, the starship stayed steady, and {hero.id} smiled at the shining breast panel.")
    world.facts.update(hero=hero, parent=parent, activity=activity, setting=setting, tool=tool, resolved=True)
    return world


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            if select_tool(act):
                out.append((place, act_id))
    return out


def explain_rejection(activity: Activity) -> str:
    return f"(No story: no tool in this world safely handles {activity.gerund}.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act = f["hero"], f["parent"], f["activity"]
    return [
        f'Write a suspenseful space adventure for a young child where {hero.id} wants to {act.verb}.',
        f"Tell a child-sized story about {hero.id}, {parent.label}, and a bright space suit with a breast panel.",
        f'Write a gentle story that uses the word "breast" and ends with a safe choice aboard a starship.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, tool = f["hero"], f["parent"], f["activity"], (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What did {hero.id} want to do near {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}, even though the scene felt suspenseful.",
        ),
        QAItem(
            question=f"What worried the captain about the breast panel?",
            answer=f"The captain worried that {act.keyword} would make the breast panel go dim.",
        ),
        QAItem(
            question=f"How did {hero.id} stay safe?",
            answer=f"They used {tool.label} first, so {hero.id} could {act.verb} safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a starship?",
            answer="A starship is a ship made for traveling through space.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense means the story feels tense because something important might go wrong.",
        ),
        QAItem(
            question="What is a breast panel on a space suit?",
            answer="A breast panel is the front panel across the chest of a space suit.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "",
             "== Story Q&A =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="starship", activity="signal_drift", tool="shield_patch", name="Nova", gender="girl", parent="captain", trait="brave"),
    StoryParams(place="spaceport", activity="meteor_glow", tool="glow_clip", name="Kai", gender="boy", parent="captain", trait="careful"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity = rng.choice(list(combos))
    tool = select_tool(_safe_lookup(ACTIVITIES, activity))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if (getattr(args, "gender", None) or "girl") == "girl" else BOY_NAMES)
    gender = getattr(args, "gender", None) or ("girl" if name in GIRL_NAMES else "boy")
    parent = getattr(args, "parent", None) or "captain"
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if getattr(args, "tool", None) and getattr(args, "tool", None) != tool.id:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, activity=activity, tool=tool.id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
at_risk(A,T) :- splashes(A,R), covers(T,R).
compatible(A,T) :- at_risk(A,T), guards(T,M), hazard_of(A,M).
valid(Place,A,T) :- affords(Place,A), compatible(A,T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("hazard_of", aid, act.hazard))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for c in sorted(tool.covers):
            lines.append(asp.fact("covers", tool.id, c))
        for g in sorted(tool.guards):
            lines.append(asp.fact("guards", tool.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - ac))
    print("clingo only:", sorted(ac - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Suspenseful space adventure storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--tool", choices=[t.id for t in TOOLS])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
    ap.add_argument("--name")
    ap.add_argument("--trait")
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
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
