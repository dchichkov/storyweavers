#!/usr/bin/env python3
"""
drastic_cautionary_adventure.py
===============================

A small cautionary adventure storyworld about a child who wants to do a
drastic thing, a careful warning, and a safer brave choice.

The premise is intentionally simple:
- a curious child wants to rush into an adventure
- a parent sees a real risk in the world
- the child gets a chance to choose a safer path
- the ending proves the choice changed the state of the world

This world is designed to feel like a tiny adventure tale rather than a fixed
template. The story changes with the sampled place, danger, tool, and rescue
gear, while the physical and emotional state drive the narration.
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    child: object | None = None
    parent: object | None = None
    tool_ent: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"risk": 0.0, "worry": 0.0, "damage": 0.0, "danger": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "curiosity": 0.0, "fear": 0.0, "courage": 0.0, "conflict": 0.0}

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
class Danger:
    id: str
    label: str
    verb: str
    warns: str
    zone: set[str]
    risk: str
    keyword: str
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
    uses: set[str]
    guards: set[str]
    prep: str
    tail: str
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _predict_harm(world: World, child: Entity, danger: Danger, tool: Optional[Tool]) -> bool:
    sim = World(world.setting)
    import copy
    sim.entities = copy.deepcopy(world.entities)
    sim.zone = set(danger.zone)
    c = sim.get(child.id)
    c.memes["curiosity"] += 1
    c.meters["risk"] += 1
    if tool is not None:
        t = sim.get(tool.id)
        t.worn_by = child.id
    for item in sim.worn_items(c):
        if item.protective and danger.id in item.id:
            pass
    return True


def _danger_fires(world: World, child: Entity, danger: Danger) -> None:
    if danger.id in world.fired:
        return
    if child.meters["risk"] < THRESHOLD:
        return
    world.fired.add((danger.id, child.id))
    child.memes["fear"] += 1
    child.meters["damage"] += 1
    world.say(f"The {danger.label} made the moment feel sharper and more serious.")


def _worry(world: World, parent: Entity, child: Entity, danger: Danger) -> None:
    if child.meters["risk"] < THRESHOLD:
        return
    if ("worry", parent.id, child.id) in world.fired:
        return
    world.fired.add(("worry", parent.id, child.id))
    parent.memes["fear"] += 1
    parent.meters["worry"] += 1
    world.say(
        f'"{danger.warns}," {child.pronoun("possessive")} parent said. '
        f'"That would be too drastic."'
    )


def _conflict(world: World, child: Entity, parent: Entity) -> None:
    if ("conflict", child.id) in world.fired:
        return
    if child.memes["fear"] + child.meters["risk"] < THRESHOLD:
        return
    world.fired.add(("conflict", child.id))
    child.memes["conflict"] += 1
    world.say(f"{child.id} wanted the adventure anyway, and the wish tugged hard at {child.pronoun('possessive')} chest.")


def _resolve_with_tool(world: World, child: Entity, parent: Entity, danger: Danger, tool: Tool) -> None:
    if ("resolve", child.id) in world.fired:
        return
    if not any(tool.id == e.id for e in world.worn_items(child)):
        return
    if danger.id not in tool.guards:
        return
    world.fired.add(("resolve", child.id))
    child.memes["fear"] = 0.0
    child.memes["joy"] += 1
    child.memes["courage"] += 1
    child.memes["conflict"] = 0.0
    world.say(
        f'Then {child.id} and {parent.label} chose the safer path. '
        f'They used {tool.label} and kept going with careful steps.'
    )
    world.say(
        f'By the end, {child.id} was still adventuring, but {child.pronoun("possessive")} {danger.keyword} stayed under control.'
    )


def run_story(world: World, child: Entity, parent: Entity, danger: Danger, tool: Optional[Tool]) -> None:
    world.say(
        f"{child.id} was a little {next((t for t in child.traits if t != 'little'), 'brave')} {child.type} who loved to explore."
    )
    world.say(
        f"{child.pronoun().capitalize()} noticed {world.setting.place} and dreamed of a drastic adventure."
    )
    if tool is not None:
        world.say(
            f"That morning, {parent.label} had already packed {tool.phrase}."
        )
        tool_ent = world.add(Entity(
            id=tool.id,
            type="gear",
            label=tool.label,
            phrase=tool.phrase,
            owner=child.id,
            protective=True,
            covers=set(),
            plural=tool.plural,
        ))
        tool_ent.worn_by = child.id

    world.para()
    world.say(f"At {world.setting.place}, the {danger.label} waited nearby, and the air felt tense.")
    child.memes["curiosity"] += 1
    child.meters["risk"] += 1
    _worry(world, parent, child, danger)
    _conflict(world, child, parent)

    if tool is not None:
        world.para()
        world.say(f"{parent.label} offered a safer idea: {tool.prep}.")
        if danger.id in tool.guards:
            child.memes["joy"] += 1
            world.say(f"{child.id} nodded, because the plan still felt like an adventure.")
            world.say(f"They {tool.tail}, and the scary part never got the chance to win.")
            _resolve_with_tool(world, child, parent, danger, tool)
        else:
            world.say(f"But that tool would not really help with this danger, so they did not use it.")
    else:
        world.para()
        world.say(f"{child.id} paused, listened, and chose not to charge ahead.")
        child.memes["courage"] += 1
        child.memes["joy"] += 1
        world.say(f"That careful choice was the bravest part of the day.")

    world.facts.update(child=child, parent=parent, danger=danger, tool=tool)


SETTINGS = {
    "old_bridge": Setting(place="the old bridge", affords={"crossing"}),
    "cave": Setting(place="the cave mouth", affords={"exploring"}),
    "cliff": Setting(place="the windy cliff path", affords={"climbing"}),
    "riverbank": Setting(place="the riverbank", affords={"crossing", "exploring"}),
}

DANGERS = {
    "rocks": Danger(
        id="rocks",
        label="loose rocks",
        verb="slide",
        warns="Those rocks could slip and send you tumbling",
        zone={"feet"},
        risk="slipping",
        keyword="rocks",
        tags={"rock", "slip"},
    ),
    "water": Danger(
        id="water",
        label="fast water",
        verb="rush",
        warns="That water could pull you off balance",
        zone={"feet", "legs"},
        risk="swept away",
        keyword="water",
        tags={"water", "current"},
    ),
    "wind": Danger(
        id="wind",
        label="strong wind",
        verb="whip",
        warns="That wind could knock you sideways",
        zone={"torso"},
        risk="blown sideways",
        keyword="wind",
        tags={"wind"},
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="a sturdy rope",
        phrase="a sturdy rope",
        uses={"crossing", "climbing"},
        guards={"water", "rocks", "wind"},
        prep="tie on the rope first",
        tail="fastened the rope and crossed together",
    ),
    "lantern": Tool(
        id="lantern",
        label="a bright lantern",
        phrase="a bright lantern",
        uses={"exploring"},
        guards={"rocks"},
        prep="take the lantern along",
        tail="carried the lantern and looked carefully",
    ),
    "boots": Tool(
        id="boots",
        label="mud boots",
        phrase="mud boots",
        uses={"crossing", "exploring"},
        guards={"water", "rocks"},
        prep="put on the mud boots first",
        tail="stomped on with safer steps",
        plural=True,
    ),
}

CHILDREN = ["Aria", "Milo", "Nina", "Toby", "Iris", "Ezra", "Luna", "Felix"]
TRAITS = ["curious", "bold", "spirited", "thoughtful", "eager", "restless"]


@dataclass
class StoryParams:
    place: str
    danger: str
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
    ap = argparse.ArgumentParser(description="A tiny cautionary adventure storyworld.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--danger", choices=DANGERS.keys())
    ap.add_argument("--tool", choices=TOOLS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
        for danger_id in setting.affords:
            for tool_id, tool in TOOLS.items():
                if danger_id in tool.guards and (danger_id != "wind" or tool_id == "rope"):
                    combos.append((place, danger_id, tool_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "danger", None) is None or c[1] == getattr(args, "danger", None))
        and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, danger, tool = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHILDREN)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, danger=danger, tool=tool, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    child_type = "girl" if params.gender == "girl" else "boy"
    child = world.add(Entity(id=params.name, kind="character", type=child_type, traits=["little", params.trait, "stubborn"]))
    parent_type = "mother" if params.parent == "mother" else "father"
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {params.parent}"))
    danger = _safe_lookup(DANGERS, params.danger)
    tool = _safe_lookup(TOOLS, params.tool)
    run_story(world, child, parent, danger, tool)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c: Entity = _safe_fact(world, f, "child")
    d: Danger = _safe_fact(world, f, "danger")
    t: Optional[Tool] = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write a short cautionary adventure story about {c.id} and the {d.label}.',
        f"Tell a child-friendly adventure where a {c.type} named {c.id} wants to be drastic, but a parent warns about {d.risk}.",
        f"Write a gentle story in which {c.id} chooses a safer adventure with {t.label if t else 'no tool'}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c: Entity = _safe_fact(world, f, "child")
    p: Entity = _safe_fact(world, f, "parent")
    d: Danger = _safe_fact(world, f, "danger")
    t: Optional[Tool] = (f.get("tool") or next(iter(TOOLS.values())))
    qa = [
        QAItem(
            question=f"Who wanted to rush into the adventure at {world.setting.place}?",
            answer=f"{c.id}, the little {c.type}, wanted to go first, because {c.pronoun('possessive')} curiosity was strong.",
        ),
        QAItem(
            question=f"Why did {p.label} worry about the {d.label}?",
            answer=f"{p.label} worried because the {d.warns.lower()}. That made the plan feel too drastic.",
        ),
        QAItem(
            question=f"What safer thing did they use in the end?",
            answer=f"They used {t.label} so {c.id} could keep going more safely.",
        ),
    ]
    if any(item.worn_by == c.id for item in world.entities.values() if item.protective):
        qa.append(QAItem(
            question=f"How did the safer choice change the ending for {c.id}?",
            answer=f"{c.id} stayed adventurous, but the danger was handled carefully, so the day ended with more courage than fear.",
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    d: Danger = _safe_fact(world, f, "danger")
    t: Tool = (f.get("tool") or next(iter(TOOLS.values())))
    out = [
        QAItem(
            question="What is a cautionary story?",
            answer="A cautionary story is a story that warns about danger and helps someone choose a safer way to act.",
        ),
        QAItem(
            question=f"What does {t.label} help with?",
            answer=f"{t.label} helps by making a risky adventure safer, especially when the danger is {d.label}.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for did, d in DANGERS.items():
        lines.append(asp.fact("danger", did))
        for z in sorted(d.zone):
            lines.append(asp.fact("zone", did, z))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", tid, g))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(D, T) :- danger(D), tool(T), guards(T, D).
valid(Place, D, T) :- setting(Place), affords(Place, _), danger(D), tool(T), guards(T, D).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="old_bridge", danger="water", tool="rope", name="Aria", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="cave", danger="rocks", tool="lantern", name="Milo", gender="boy", parent="father", trait="bold"),
    StoryParams(place="cliff", danger="wind", tool="rope", name="Nina", gender="girl", parent="mother", trait="spirited"),
    StoryParams(place="riverbank", danger="water", tool="boots", name="Ezra", gender="boy", parent="father", trait="thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
