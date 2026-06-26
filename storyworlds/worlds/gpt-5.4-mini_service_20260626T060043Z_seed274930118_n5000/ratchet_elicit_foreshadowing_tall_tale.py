#!/usr/bin/env python3
"""
storyworlds/worlds/ratchet_elicit_foreshadowing_tall_tale.py
=============================================================

A standalone story world for a small Tall Tale domain with foreshadowing:
a lumbering problem, a clever ratchet, and a reveal that was hinted at all
along.

Premise:
- A child and a grown helper are trying to open, fix, or free something huge.
- The hero uses a ratchet tool, which can turn a stubborn thing one click at a time.
- Early details foreshadow the ending so the final twist feels earned.

Style:
- Tall tale: concrete, playful exaggeration, vivid images, but still grounded.
- Child-facing prose with a clear beginning, middle turn, and ending image.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    mechanism: object | None = None
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
    weather: str
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
class Mechanism:
    id: str
    noun: str
    verb: str
    gerund: str
    problem: str
    reveal: str
    zones: set[str]
    trigger: str
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
    helper_line: str
    fix_line: str
    effect: str
    works_on: set[str]
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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
class Rule:
    name: str
    apply: callable
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


def _r_warn(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        for mech in world.facts.get("mechanisms", []):
            if hero.memes.get("curiosity", 0.0) < THRESHOLD:
                continue
            if mech.id in world.fired:
                continue
            if world.facts.get("foreshadowed") != mech.id:
                continue
            world.fired.add((mech.id, "warn"))
            hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1
            out.append(
                f"Even before anything went wrong, {hero.id} could tell the big {mech.noun} was "
                f"the sort of thing that kept a secret in its teeth."
            )
    return out


def _r_turn(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    mech = world.facts.get("mechanism")
    tool = world.facts.get("tool")
    if not hero or not mech or not tool:
        return out
    if world.facts.get("attempted"):
        return out
    if hero.memes.get("determination", 0.0) < THRESHOLD:
        return out
    sig = ("turn", mech.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["effort"] = hero.meters.get("effort", 0.0) + 1
    world.facts["turned_with"] = tool.id
    out.append(
        f"Then {hero.id} gave the {tool.label} one brave click, and the stubborn {mech.noun} "
        f"moved a hair's breadth at a time."
    )
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    mech = world.facts.get("mechanism")
    if not mech:
        return out
    if not world.facts.get("turned_with"):
        return out
    sig = ("reveal", mech.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["revealed"] = True
    out.append(mech.reveal)
    return out


CAUSAL_RULES = [
    Rule("warn", _r_warn),
    Rule("turn", _r_turn),
    Rule("reveal", _r_reveal),
]


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


def tell(setting: Setting, mech: Mechanism, tool: Tool, hero_name: str, hero_type: str,
         helper_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"effort": 0.0},
        memes={"curiosity": 1.0, "determination": 1.0, "joy": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        memes={"patience": 1.0},
    ))
    mechanism = world.add(Entity(
        id=mech.id,
        type="thing",
        label=mech.noun,
        phrase=mech.noun,
    ))
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["mechanism"] = mechanism
    world.facts["mechanisms"] = [mech]
    world.facts["tool"] = world.add(Entity(
        id=tool.id,
        type="tool",
        label=tool.label,
        phrase=tool.label,
        owner=hero.id,
    ))
    world.facts["foreshadowed"] = mech.id

    world.say(
        f"{hero.id} lived where {setting.place} could shine or grumble depending on the sky, "
        f"and {hero.pronoun('possessive')} ears were always tuned for big trouble."
    )
    world.say(
        f"{hero.id} loved the {tool.label}; when {hero.id} brought it out, even a jammed gate "
        f"seemed to stand up straighter and pay attention."
    )
    world.say(
        f"That morning, {hero.id} and {helper.label} found a {mech.noun} so large and so stubborn "
        f"that it looked like the moon had once tried to turn it and gone home tired."
    )

    world.para()
    if mech.id == "windmill":
        world.say(
            f"The old {mech.noun} leaned over the field, and its blades sat still as painted clouds."
        )
    elif mech.id == "barn_door":
        world.say(
            f"The {mech.noun} sat half-swallowed by squeaks, as if the wood itself were saving up a story."
        )
    else:
        world.say(
            f"The {mech.noun} crouched beside the road, its one big handle waiting like a fishhook in a pond."
        )
    world.say(
        f"{helper.label.capitalize()} said the thing had not moved right in a week, not since the weather "
        f"had made its old bones complain."
    )
    world.say(
        f"But {hero.id} noticed a little clue: every time the wind changed, the {mech.noun} gave a tiny "
        f"click, as if it was trying to tell on itself."
    )

    world.para()
    hero.memes["curiosity"] += 1
    hero.memes["determination"] += 1
    world.say(
        f"So {hero.id} climbed up, planted {hero.pronoun('possessive')} boots, and wrapped both hands "
        f"around the {tool.label}."
    )
    world.say(
        f'"If I keep to the ratchet rhythm," {hero.id} said, "maybe this old giant will loosen its grin."'
    )
    world.facts["attempted"] = True
    propagate(world, narrate=True)

    world.para()
    hero.memes["joy"] += 1
    world.say(
        f"With one last bright click, the {mech.noun} opened what it had been hiding all along."
    )
    hero.meters["effort"] += 1
    world.say(
        f"And there, inside the giant thing, was not a monster at all, but a secret stash of lanterns, "
        f"fresh apples, and a map folded so many times it had learned how to smile."
    )
    world.say(
        f"{hero.id} laughed so hard {hero.pronoun('possessive')} hat nearly flew off, and {helper.label} "
        f"laughed too, because the biggest lock in town had been guarding the smallest treasure with the "
        f"loudest pride."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        mechanism=mechanism,
        tool=world.facts["tool"],
        setting=setting,
    )
    return world


SETTINGS = {
    "hill": Setting(place="the windy hill", weather="windy", affords={"windmill", "cask"}),
    "yard": Setting(place="the old yard", weather="sunny", affords={"barn_door", "crate"}),
    "dock": Setting(place="the river dock", weather="misty", affords={"chain_box", "crate"}),
}

MECHANISMS = {
    "windmill": Mechanism(
        id="windmill",
        noun="windmill",
        verb="turn the windmill",
        gerund="turning the windmill",
        problem="its wheel is stuck",
        reveal="When the wheel finally spun, a hidden compartment in the windmill yawned open, and it was packed with lanterns and apples for the whole village.",
        zones={"sky"},
        trigger="wind",
        keyword="ratchet",
        tags={"ratchet", "wind", "foreshadowing"},
    ),
    "barn_door": Mechanism(
        id="barn_door",
        noun="barn door",
        verb="open the barn door",
        gerund="opening the barn door",
        problem="its latch is jammed",
        reveal="When the latch gave way, the barn door swung wide and revealed a cozy wagon bed loaded with quilts, cider, and a sleepy kitten.",
        zones={"ground"},
        trigger="wood",
        keyword="elicit",
        tags={"ratchet", "elicit", "foreshadowing"},
    ),
    "chain_box": Mechanism(
        id="chain_box",
        noun="chain box",
        verb="unlock the chain box",
        gerund="unlocking the chain box",
        problem="the chain is wound tighter than a snake in a hatbox",
        reveal="When the box opened, out came a rolled-up map, three brass whistles, and a note that had been waiting for the right brave hands.",
        zones={"ground"},
        trigger="iron",
        keyword="foreshadowing",
        tags={"ratchet", "foreshadowing"},
    ),
    "crate": Mechanism(
        id="crate",
        noun="crate",
        verb="pry open the crate",
        gerund="prying open the crate",
        problem="the nails are stuck",
        reveal="When the lid popped free, the crate was full of tiny bells and bright ribbons for the town's parade.",
        zones={"ground"},
        trigger="wood",
        keyword="tall tale",
        tags={"foreshadowing"},
    ),
}

TOOLS = {
    "ratchet": Tool(
        id="ratchet",
        label="ratchet",
        helper_line="it could bite a bolt one little click at a time",
        fix_line="it made slow work feel mighty",
        effect="turns stubborn fasteners by clicks",
        works_on={"windmill", "barn_door", "chain_box", "crate"},
    ),
}


@dataclass
class StoryParams:
    place: str
    mechanism: str
    tool: str
    name: str
    gender: str
    helper: str
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


GIRL_NAMES = ["Ruby", "Mabel", "Hazel", "Nora", "Ivy", "Ada", "Rose"]
BOY_NAMES = ["Jack", "Milo", "Eli", "Theo", "Otis", "Finn", "Cal"]
TRAITS = ["bold", "curious", "plucky", "cheerful", "quick-thinking", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for mech in setting.affords:
            if mech in MECHANISMS and "ratchet" in TOOLS:
                out.append((place, mech, "ratchet"))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    mech = _safe_fact(world, f, "mechanism")
    return [
        f'Write a short Tall Tale for a child about {hero.id}, a ratchet, and a hidden surprise.',
        f"Tell a foreshadowing story where {hero.id} uses a ratchet to {mech.label} and a clue appears early.",
        f'Write a playful story that includes the word "elicit" and ends with a big reveal inside {mech.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    mech = _safe_fact(world, f, "mechanism")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What was {hero.id} trying to do with the {tool.label}?",
            answer=f"{hero.id} was trying to {mech.verb} by using the {tool.label} one click at a time.",
        ),
        QAItem(
            question=f"Why did the story mention the little click before the big surprise?",
            answer=(
                f"That was foreshadowing. The tiny click hinted that the {mech.noun} was not stuck forever, "
                f"and it was about to give up a secret."
            ),
        ),
        QAItem(
            question=f"What did {helper.label} and {hero.id} find at the end?",
            answer=(
                f"They found the hidden treasure inside the {mech.noun}: lanterns, apples, and a folded map. "
                f"The surprise proved the old machine had been hiding something all along."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ratchet for?",
            answer="A ratchet is a tool that turns nuts, bolts, and stuck parts a little bit at a time.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives a small hint early so the ending feels earned later.",
        ),
        QAItem(
            question="What kind of story is a tall tale?",
            answer="A tall tale is a funny story with larger-than-life details and a big, lively exaggeration.",
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hill", mechanism="windmill", tool="ratchet", name="Ruby", gender="girl", helper="mother", trait="bold"),
    StoryParams(place="yard", mechanism="barn_door", tool="ratchet", name="Jack", gender="boy", helper="father", trait="curious"),
    StoryParams(place="dock", mechanism="chain_box", tool="ratchet", name="Milo", gender="boy", helper="mother", trait="plucky"),
]


def explain_rejection(mech_id: str, tool_id: str) -> str:
    if tool_id != "ratchet":
        return "(No story: this domain only uses a ratchet as the clever tool."
    if mech_id not in MECHANISMS:
        return "(No story: unknown mechanism.)"
    return "(No story: the chosen parts do not make a good foreshadowing turn.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale story world with a ratchet and foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mechanism", choices=MECHANISMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father"])
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
    if getattr(args, "mechanism", None) and getattr(args, "tool", None) and getattr(args, "tool", None) != "ratchet":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mechanism", None) is None or c[1] == getattr(args, "mechanism", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mech, tool = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, mechanism=mech, tool=tool, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(MECHANISMS, params.mechanism), _safe_lookup(TOOLS, params.tool), params.name, params.gender, params.helper)
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
mechanism(M) :- mech(M).
tool(T) :- has_tool(T).
valid(Place, M, T) :- affords(Place, M), mechanism(M), tool(T), T = ratchet.
valid_story(Place, M, T, Gender) :- valid(Place, M, T), wears(Gender, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for m in sorted(s.affords):
            lines.append(asp.fact("affords", pid, m))
    for mid in MECHANISMS:
        lines.append(asp.fact("mech", mid))
    for tid in TOOLS:
        lines.append(asp.fact("has_tool", tid))
    for g in ["girl", "boy"]:
        for mid in MECHANISMS:
            lines.append(asp.fact("wears", g, mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):\n")
        for place, mech, tool in triples:
            genders = sorted(g for (pl, m, t, g) in stories if (pl, m, t) == (place, mech, tool))
            print(f"  {place:8} {mech:12} {tool:8} [{', '.join(genders)}]")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.mechanism} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
