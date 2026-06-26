#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a child, a handmade wood swatter,
and the lesson learned after a small everyday mistake.

Seed imagery:
- nifty
- wood
- swatter

Premise:
A child is proud of a nifty wood swatter they made for a simple job around
the house or yard. They want to use it right away, but the first plan is a
little too eager and creates a tiny mess or scare. A parent or helper suggests
a safer, calmer way to use it. The child learns the lesson, tries again, and
ends with a useful, satisfying result.

This world is designed to produce short, concrete, authored stories with a
clear turn and a lesson learned at the end.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str
    indoor: bool
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
    rush: str
    result: str
    risk: str
    mess: str
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
class Tool:
    id: str
    label: str
    phrase: str
    purpose: str
    safe_use: str
    misuse: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _append_clause(base: str, extra: str) -> str:
    return base + (", " if not base.endswith((" ", "\n")) else "") + extra


def predict(world: World, child: Entity, activity: Activity, tool: Tool) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(child.id), activity, tool, narrate=False)
    return {
        "messy": bool(sim.get(tool.id).meters.get("dirt", 0) >= THRESHOLD or sim.get(tool.id).meters.get("scratched", 0) >= THRESHOLD),
        "lesson": sim.facts.get("lesson", False),
    }


def _do_activity(world: World, child: Entity, activity: Activity, tool: Tool, narrate: bool = True) -> list[str]:
    out: list[str] = []
    child.memes["eager"] = child.memes.get("eager", 0) + 1
    if activity.id == "swat_fast":
        child.meters["swift"] = child.meters.get("swift", 0) + 1
        tool.meters["dirt"] = tool.meters.get("dirt", 0) + 1
        tool.meters["scratched"] = tool.meters.get("scratched", 0) + 1
        out.append(f"The quick swing knocked dust onto the swatter.")
    elif activity.id == "tap_leaves":
        child.meters["careful"] = child.meters.get("careful", 0) + 1
        out.append(f"The slower taps brushed the leaves cleanly.")
    elif activity.id == "hang_tool":
        child.meters["tidy"] = child.meters.get("tidy", 0) + 1
        out.append(f"The swatter hung neatly by the door again.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def intro(world: World, child: Entity) -> None:
    world.say(f"{child.id} was a little {child.type} who liked small useful jobs around the house.")


def setup(world: World, child: Entity, tool: Tool, activity: Activity) -> None:
    world.say(
        f"{child.id} found a nifty wood swatter and held {tool.phrase} with both hands."
    )
    world.say(
        f"{child.pronoun().capitalize()} wanted to {activity.verb}, because {tool.purpose}."
    )


def warning(world: World, parent: Entity, child: Entity, tool: Tool, activity: Activity) -> bool:
    pred = predict(world, child, activity, tool)
    if not pred["messy"]:
        return False
    world.facts["lesson"] = True
    world.say(
        f'"Wait," {parent.pronoun("subject")} said. "If you swing it that fast, {tool.misuse}."'
    )
    return True


def mistake(world: World, child: Entity, activity: Activity, tool: Tool) -> None:
    child.memes["stubborn"] = child.memes.get("stubborn", 0) + 1
    world.say(
        f"{child.id} tried to {activity.rush}, and the first try went a little wrong."
    )
    _do_activity(world, child, activity, tool, narrate=True)


def lesson(world: World, parent: Entity, child: Entity, activity: Activity, tool: Tool) -> None:
    child.memes["listening"] = child.memes.get("listening", 0) + 1
    child.memes["pride"] = max(child.memes.get("pride", 0), 1)
    child.memes["calm"] = child.memes.get("calm", 0) + 1
    world.say(
        f'{parent.pronoun("subject").capitalize()} showed {child.pronoun("object")} how to use it more slowly: "{tool.safe_use}."'
    )
    world.say(
        f"{child.id} nodded, because the lesson was easy to see."
    )
    _do_activity(world, child, activity, tool, narrate=True)


def ending(world: World, child: Entity, parent: Entity, tool: Tool, activity: Activity) -> None:
    world.say(
        f"In the end, {child.id} hung the wood swatter back up and smiled at the neat little tool."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} had learned that nifty things work best when they are used carefully."
    )


SETTINGS = {
    "yard": Setting(place="the yard", indoor=False, affords={"swat_fast", "tap_leaves", "hang_tool"}),
    "porch": Setting(place="the porch", indoor=False, affords={"swat_fast", "tap_leaves", "hang_tool"}),
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"swat_fast", "tap_leaves", "hang_tool"}),
}

ACTIVITIES = {
    "swat_fast": Activity(
        id="swat_fast",
        verb="swat the flies",
        gerund="swatting flies",
        rush="swat at the air too fast",
        result="made the swatter bounce and stir up dust",
        risk="it could get dusty and rough",
        mess="dusty",
        keyword="swatter",
        tags={"swatter", "wood", "lesson"},
    ),
    "tap_leaves": Activity(
        id="tap_leaves",
        verb="tap the leaves away",
        gerund="tapping leaves aside",
        rush="tap the leaves in a careful way",
        result="kept the tool clean and neat",
        risk="it would stay tidy",
        mess="clean",
        keyword="wood",
        tags={"wood", "lesson"},
    ),
    "hang_tool": Activity(
        id="hang_tool",
        verb="put the swatter away",
        gerund="putting the tool away",
        rush="hang the swatter up at once",
        result="put the tool back where it belonged",
        risk="it would be safe on its hook",
        mess="clean",
        keyword="nifty",
        tags={"nifty", "lesson"},
    ),
}

TOOLS = {
    "wood_swatter": Tool(
        id="wood_swatter",
        label="wood swatter",
        phrase="the nifty wood swatter",
        purpose="it was handy for light jobs around the house",
        safe_use="Hold the handle steady and swing only as much as you need",
        misuse="the wood can get dusty and chipped",
        tags={"nifty", "wood", "swatter"},
    ),
}

CHILD_NAMES = ["Milo", "Ivy", "Nina", "Theo", "June", "Arlo", "Maya", "Finn"]
PARENT_NAMES = ["Mom", "Dad"]
CHILD_TYPES = {"girl", "boy"}


@dataclass
class StoryParams:
    place: str
    activity: str
    tool: str
    name: str
    gender: str
    parent: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about a nifty wood swatter and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["Mom", "Dad"])
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for tool in TOOLS:
                combos.append((place, act, tool))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)
              and getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None)
              and getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None)]
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, tool = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENT_NAMES)
    return StoryParams(place=place, activity=activity, tool=tool, name=name, gender=gender, parent=parent)


def tell(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id=params.parent, kind="character", type="mother" if params.parent == "Mom" else "father"))
    tool = world.add(Entity(id=params.tool, type="thing", label="wood swatter", phrase="the nifty wood swatter", owner=child.id, caretaker=parent.id))
    activity = _safe_lookup(ACTIVITIES, params.activity)

    intro(world, child)
    world.para()
    setup(world, child, tool, activity)
    warning(world, parent, child, tool, activity)
    mistake(world, child, activity, tool)
    world.para()
    lesson(world, parent, child, activity, tool)
    ending(world, child, parent, tool, activity)

    world.facts.update(child=child, parent=parent, tool=tool, activity=activity, lesson=True)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return tell(params)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    activity: Activity = _safe_fact(world, f, "activity")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f"Write a short slice-of-life story for a young child about a nifty wood swatter and a lesson learned.",
        f"Tell a gentle story where {child.id} wants to {activity.verb} with {tool.phrase} but learns to be careful.",
        f"Write a small everyday story that includes the words nifty, wood, and swatter, and ends with a lesson.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    activity: Activity = _safe_fact(world, f, "activity")
    return [
        QAItem(
            question=f"What did {child.id} find at the start of the story?",
            answer=f"{child.id} found a nifty wood swatter, a small tool that was handy for little jobs around the house.",
        ),
        QAItem(
            question=f"What did {child.id} want to do with the wood swatter?",
            answer=f"{child.id} wanted to {activity.verb}. That made sense because the swatter was meant to help with that kind of job.",
        ),
        QAItem(
            question=f"Why did {parent.id} speak up when {child.id} rushed ahead?",
            answer=f"{parent.id} warned {child.id} because swinging it too fast could make the wood swatter dusty or chipped.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn by the end?",
            answer=f"{child.id} learned that nifty things work best when they are used carefully and with a little patience.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is wood?",
            answer="Wood is the hard material that comes from trees. People use it to make furniture, tools, and many other things.",
        ),
        QAItem(
            question="What is a swatter?",
            answer="A swatter is a small tool used to swat or brush away things like flies or leaves.",
        ),
        QAItem(
            question="What does nifty mean?",
            answer="Nifty means neat, clever, or nicely made.",
        ),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:12} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A,T) :- setting(P), affords(P,A), tool(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="yard", activity="swat_fast", tool="wood_swatter", name="Milo", gender="boy", parent="Mom"),
    StoryParams(place="porch", activity="tap_leaves", tool="wood_swatter", name="Ivy", gender="girl", parent="Dad"),
    StoryParams(place="kitchen", activity="hang_tool", tool="wood_swatter", name="Nina", gender="girl", parent="Mom"),
]


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
        print(asp_valid_combos())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
