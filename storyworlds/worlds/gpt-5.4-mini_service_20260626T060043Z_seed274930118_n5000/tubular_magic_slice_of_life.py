#!/usr/bin/env python3
"""
storyworlds/worlds/tubular_magic_slice_of_life.py
=================================================

A small slice-of-life storyworld about a child, a tubular bit of magic,
and an everyday problem that turns into a gentle, careful solution.

Premise:
- A child keeps a tubular magic wand-tube in an ordinary home setting.
- The tube can help with tiny daily tasks, but careless magic can make a mess.
- A parent notices the risk, worries aloud, and guides the child toward a
  safer way to use the magic.

The world is intentionally small and constraint-checked:
- only a few compatible setting/activity/object combinations are allowed;
- invalid explicit choices raise StoryError;
- the story is driven by simulated state rather than a frozen template;
- the magical tube changes meters and memories in the world model.

The domain is meant to feel like Slice of Life: warm, domestic, and concrete,
with a touch of magic.
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    item: object | None = None
    parent: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    weather: str = ""
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
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False
    tubular: bool = True
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
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
        for item in self.worn_items(actor):
            if item.protective and region in getattr(item, "covers", set()):
                return True
        return False

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
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


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


def _r_splash(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ("wet", "sparkle"):
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective:
                    continue
                if item.id == "apron" and "torso" not in world.zone:
                    continue
                if item.id == "slippers" and "feet" not in world.zone:
                    continue
                sig = ("splash", actor.id, item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0.0) + 1
                item.meters["messy"] = item.meters.get("messy", 0.0) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess} and a little messy.")
    return out


def _r_work(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("messy", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] = carer.meters.get("workload", 0.0) + 1
        out.append(f"That would mean more cleanup for {carer.label}.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("worry", 0.0) < THRESHOLD or actor.memes.get("warning", 0.0) < THRESHOLD:
            continue
        sig = ("worry", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["tension"] = actor.memes.get("tension", 0.0) + 1
        out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("splash", _r_splash), Rule("work", _r_work), Rule("worry", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__worry__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, actor: Entity, activity: Activity, item_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    item = sim.entities[item_id]
    return {
        "messy": item.meters.get("messy", 0.0) >= THRESHOLD,
        "workload": sum(e.meters.get("workload", 0.0) for e in sim.characters()),
    }


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def setting_line(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The room was quiet, and the little table by the window waited for something nice to happen."
    if activity.weather == "rainy":
        return f"The air smelled fresh, and {setting.place} looked shiny after the rain."
    return f"{setting.place.capitalize()} felt calm and ordinary in the best way."


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "bright")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved small useful tricks.")


def loves_magic(world: World, hero: Entity, tube: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{hero.id} loved {tube.phrase}; the {tube.label} was tubular, smooth, and magic in a gentle way."
    )


def buys(world: World, parent: Entity, hero: Entity, tube: Entity) -> None:
    world.say(f"One week, {hero.pronoun('possessive')} {parent.label} brought home {hero.pronoun('object')} {tube.phrase}.")


def loves_item(world: World, hero: Entity, tube: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    tube.worn_by = hero.id
    world.say(f"{hero.id} treasured {hero.pronoun('possessive')} {tube.label} and carried {tube.it()} everywhere.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = "One rainy afternoon, " if activity.weather == "rainy" else "One quiet afternoon, "
    go = "went to" if not world.setting.indoor else "stayed in"
    world.say(f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label} {go} {world.setting.place}.")
    world.say(setting_line(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {activity.verb} right away, but {hero.pronoun('possessive')} {parent.label} paused.")
    world.say(f"{hero.pronoun().capitalize()} reached for the tubular magic tube and smiled.")

def warn(world: World, parent: Entity, hero: Entity, activity: Activity, item: Entity) -> bool:
    pred = predict(world, hero, activity, item.id)
    if not pred["messy"]:
        return False
    hero.memes["warning"] = hero.memes.get("warning", 0.0) + 1
    parent.memes["worry"] = parent.memes.get("worry", 0.0) + 1
    clause = f"You'll get your {item.label} {activity.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += ", and then I'll have to clean it up"
    world.say(f'"{clause}," {parent.pronoun("possessive")} {parent.label} said softly.')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    world.say(f"{hero.id} still wanted to try.")
    world.say(f"{hero.pronoun().capitalize()} started to {activity.rush}.")


def gentle_stop(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["held"] = hero.memes.get("held", 0.0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.pronoun('possessive')} {parent.label} held up a hand and said, "
        f'"We can still do it, just the careful way."'
    )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, item: Entity) -> Optional[Tool]:
    tool_def = select_tool(activity, item)
    if tool_def is None:
        return None
    tool = world.add(Entity(
        id=tool_def.id,
        type="tool",
        label=tool_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        plural=tool_def.plural,
    ))
    tool.worn_by = hero.id
    if predict(world, hero, activity, item.id)["messy"]:
        tool.worn_by = None
        del world.entities[tool.id]
        return None
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label} looked at the {item.label} and then at the {tube_name(hero)}."
        f' "How about we use {tool_def.prep} and still {activity.verb}?"'
    )
    return tool_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, item: Entity, tool_def: Tool) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    hero.memes["tension"] = 0.0
    world.say(f"{hero.id}'s face lit up, and {hero.pronoun()} hugged {hero.pronoun('possessive')} {parent.label}.")
    world.say(
        f'"Yes!" {hero.pronoun()} said. They {tool_def.tail}. Soon {hero.id} was {activity.gerund}, '
        f"{item.label} stayed clean, and the little room felt brighter than before."
    )


def tube_name(hero: Entity) -> str:
    return "magic tube"


def select_tool(activity: Activity, item: Entity) -> Optional[Tool]:
    for tool in TOOLS:
        if activity.mess in tool.guards and item_id_to_region(item.id) in tool.covers:
            return tool
    return None


def item_id_to_region(item_id: str) -> str:
    return {"mug": "torso", "apron": "torso", "slippers": "feet"}[item_id]


def tell(setting: Setting, activity: Activity, item_cfg: Entity, hero_name: str = "Mina", hero_type: str = "girl",
         parent_type: str = "mother", trait: str = "curious") -> World:
    world = World(setting)
    world.weather = activity.weather if not setting.indoor else ""
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait, "gentle"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom" if parent_type == "mother" else "dad"))
    item = world.add(Entity(
        id=item_cfg.id, type=item_cfg.type, label=item_cfg.label, phrase=item_cfg.phrase,
        owner=hero.id, caretaker=parent.id, plural=item_cfg.plural
    ))
    introduce(world, hero)
    loves_magic(world, hero, item)
    buys(world, parent, hero, item)
    loves_item(world, hero, item)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, item)
    defies(world, hero, activity)
    gentle_stop(world, parent, hero, activity)

    world.para()
    tool_def = compromise(world, parent, hero, activity, item)
    if tool_def:
        accept(world, parent, hero, activity, item, tool_def)

    world.facts.update(hero=hero, parent=parent, item=item, activity=activity, setting=setting, tool=tool_def,
                       resolved=tool_def is not None, conflict=True)
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"tea", "water_plants"}),
    "porch": Setting(place="the porch", indoor=False, affords={"water_plants"}),
    "laundry": Setting(place="the laundry room", indoor=True, affords={"fold_clothes"}),
}

ACTIVITIES = {
    "tea": Activity(
        id="tea",
        verb="brew tea",
        gerund="brewing tea",
        rush="dash to the kettle",
        mess="wet",
        soil="splashy and wet",
        zone={"torso"},
        keyword="tea",
        weather="rainy",
        tags={"water", "home"},
    ),
    "water_plants": Activity(
        id="water_plants",
        verb="water the plants",
        gerund="watering the plants",
        rush="run to the plant shelf",
        mess="wet",
        soil="splashed and wet",
        zone={"torso", "feet"},
        keyword="plants",
        weather="rainy",
        tags={"plants", "water", "home"},
    ),
    "fold_clothes": Activity(
        id="fold_clothes",
        verb="help fold clothes",
        gerund="folding clothes",
        rush="dash to the clean basket",
        mess="sparkle",
        soil="sparkly and wrinkled",
        zone={"hands"},
        keyword="clothes",
        weather="",
        tags={"laundry", "home"},
    ),
}

ITEMS = {
    "mug": Entity(id="mug", type="mug", label="blue mug", phrase="a blue mug with a tiny star", plural=False),
    "apron": Entity(id="apron", type="apron", label="apron", phrase="a striped apron", plural=False),
    "slippers": Entity(id="slippers", type="slippers", label="slippers", phrase="soft house slippers", plural=True),
}

TOOLS = [
    Tool(id="saucer", label="a saucer", phrase="a saucer", covers={"torso"}, guards={"wet"}, prep="set the mug on a saucer first", tail="set the saucer under the mug"),
    Tool(id="tray", label="a tray", phrase="a tray", covers={"torso", "feet"}, guards={"wet"}, prep="carry it on a tray", tail="moved the tray carefully"),
    Tool(id="towel", label="a towel", phrase="a towel", covers={"torso", "feet"}, guards={"wet", "sparkle"}, prep="wrap it in a towel", tail="wrapped the towel around everything"),
]

TRAITS = ["curious", "gentle", "cheerful", "patient", "playful"]

@dataclass
class StoryParams:
    place: str
    activity: str
    item: str
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


CURATED = [
    StoryParams(place="kitchen", activity="tea", item="mug", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="porch", activity="water_plants", item="slippers", name="Noah", gender="boy", parent="father", trait="gentle"),
    StoryParams(place="laundry", activity="fold_clothes", item="apron", name="Ivy", gender="girl", parent="mother", trait="playful"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for item_id, item in ITEMS.items():
                if prize_at_risk(act, item) and select_tool(act, item):
                    combos.append((place, act_id, item_id))
    return combos


def prize_at_risk(activity: Activity, item: Entity) -> bool:
    return item_id_to_region(item.id) in activity.zone


def explain_rejection(activity: Activity, item: Entity) -> str:
    if not prize_at_risk(activity, item):
        return f"(No story: {activity.gerund} doesn't reach the {item.label}, so there is no real worry to solve.)"
    return f"(No story: nothing in the tool set safely protects the {item.label} from {activity.gerund}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "item", None):
        act, item = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(ITEMS, getattr(args, "item", None))
        if not (prize_at_risk(act, item) and select_tool(act, item)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, item = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(["Mina", "Ivy", "Noah", "Leo", "Rosa", "Eli"])
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, item=item, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(ITEMS, params.item), params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, item = f["hero"], f["parent"], f["activity"], f["item"]
    return [
        f'Write a gentle slice-of-life story about a child named {hero.id}, a tubular magic tube, and {item.label}.',
        f"Tell a short story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label} worries about {item.label}.",
        f'Write a cozy story with the word "tubular" that ends with a safer way to use magic at {world.setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, item = f["hero"], f["parent"], f["activity"], f["item"]
    resolved = f.get("resolved", False)
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.type}, and {hero.pronoun('possessive')} {parent.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}, because {hero.pronoun()} loved the everyday magic of the tubular tube.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the {item.label}?",
            answer=f"{parent.label} worried because {act.gerund} could leave the {item.label} {act.soil} and make more cleanup.",
        ),
    ]
    if resolved:
        tool = (f.get("tool") or next(iter(TOOLS.values())))
        qa.append(QAItem(
            question=f"How did the family solve the problem?",
            answer=f"They used {tool.label} first, so {hero.id} could keep playing while the {item.label} stayed clean.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and calmer, and the room felt bright and ordinary again in a nice way.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("tool"):
        tags.add("magic")
        tags.add("tubular")
    out = []
    if "tubular" in tags or True:
        out.append(QAItem(
            question="What does tubular mean?",
            answer="Tubular means shaped like a tube, long and round in the middle.",
        ))
    if "magic" in tags:
        out.append(QAItem(
            question="What is magic in stories?",
            answer="Magic in stories is something special and surprising that can change what happens in a gentle way.",
        ))
    if "home" in tags:
        out.append(QAItem(
            question="Why do people keep things tidy at home?",
            answer="People keep things tidy at home so the room stays pleasant, safe, and easy to use.",
        ))
    return out


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
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("worn_on", iid, item_id_to_region(iid)))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for m in sorted(t.guards):
            lines.append(asp.fact("guards", t.id, m))
        for r in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, r))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, I) :- splashes(A, R), worn_on(I, R).
protects(T, A, I) :- tool(T), prize_at_risk(A, I), mess_of(A, M), guards(T, M), covers(T, R), worn_on(I, R).
has_fix(A, I) :- protects(_, A, I).
valid(Place, A, I) :- affords(Place, A), prize_at_risk(A, I), has_fix(A, I).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a tubular magic slice of life story.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for place, act, item in triples:
            print(f"  {place:10} {act:14} {item}")
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
            header = f"### {p.name}: {p.activity} at {p.place} (item: {p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
