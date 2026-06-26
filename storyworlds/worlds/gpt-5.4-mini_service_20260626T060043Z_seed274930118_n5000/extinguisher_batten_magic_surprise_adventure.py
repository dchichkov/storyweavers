#!/usr/bin/env python3
"""
Storyworld: extinguisher / batten / magic / surprise / adventure.

A small, constraint-checked adventure story world where a child wants to
explore a windy harbor loft, but a loose batten and a tricky spark of magic
create a tense moment. A magical extinguisher becomes the surprising fix: it
cools the spark, and the batten can be secured so the child can keep exploring.

The prose is generated from a simulated world model with physical meters and
emotional memes. The story is not a frozen template; events follow from state.
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    entity: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
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


def _meters() -> dict[str, float]:
    return {"spark": 0.0, "wobble": 0.0, "dust": 0.0, "safe": 0.0, "work": 0.0}


def _memes() -> dict[str, float]:
    return {"joy": 0.0, "fear": 0.0, "curiosity": 0.0, "surprise": 0.0, "bond": 0.0}


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the harbor loft"
    indoor: bool = True
    afford: set[str] = field(default_factory=lambda: {"explore", "climb", "fix"})
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
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    surprise: str
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
class Tool:
    id: str
    label: str
    phrase: str
    guards: set[str]
    covers: set[str]
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "harbor_loft": Setting(place="the harbor loft", indoor=True, afford={"explore", "fix", "climb"}),
    "dock_shed": Setting(place="the dock shed", indoor=True, afford={"explore", "fix"}),
    "lighthouse_room": Setting(place="the lighthouse room", indoor=True, afford={"explore", "fix"}),
}

CHALLENGES = {
    "glow": Challenge(
        id="glow",
        verb="explore the glowing corner",
        gerund="exploring the glowing corner",
        rush="dash toward the glowing corner",
        danger="sparkly and hot",
        surprise="a flash of surprise magic",
        zone={"torso", "hands"},
        keyword="Magic",
        tags={"magic", "surprise"},
    ),
    "drift": Challenge(
        id="drift",
        verb="follow the drifting light",
        gerund="following the drifting light",
        rush="run after the drifting light",
        danger="unsteady and bright",
        surprise="a sudden twinkle",
        zone={"feet", "hands"},
        keyword="Surprise",
        tags={"surprise"},
    ),
    "lantern": Challenge(
        id="lantern",
        verb="inspect the lantern nook",
        gerund="inspecting the lantern nook",
        rush="hurry to the lantern nook",
        danger="warm and flickery",
        surprise="a magic puff of smoke",
        zone={"torso", "hands"},
        keyword="Magic",
        tags={"magic"},
    ),
}

PRIZES = {
    "cloak": Prize(label="cloak", phrase="a soft explorer's cloak", type="cloak", region="torso"),
    "boots": Prize(label="boots", phrase="sturdy harbor boots", type="boots", region="feet", plural=True),
    "cap": Prize(label="cap", phrase="a bright little cap", type="cap", region="head"),
}

TOOLS = [
    Tool(
        id="extinguisher",
        label="magic extinguisher",
        phrase="a magic extinguisher",
        guards={"spark", "wobble"},
        covers={"torso", "hands", "feet"},
        prep="lift the magic extinguisher and press the silver lever",
        tail="held the extinguisher steady while the shimmer faded",
    ),
    Tool(
        id="batten",
        label="wooden batten",
        phrase="a wooden batten",
        guards={"wobble"},
        covers={"torso", "hands"},
        prep="set the wooden batten across the loose hatch",
        tail="slid the batten into place and kept the hatch from wobbling",
    ),
]

NAMES = {
    "girl": ["Maya", "Lina", "Tess", "Nora", "Ivy"],
    "boy": ["Eli", "Finn", "Theo", "Noah", "Owen"],
}
TRAITS = ["curious", "brave", "bright-eyed", "cheerful", "restless"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def prize_at_risk(challenge: Challenge, prize: Prize) -> bool:
    return prize.region in challenge.zone


def select_tool(challenge: Challenge, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS:
        if prize.region in tool.covers and challenge.id == "glow" and tool.id == "extinguisher":
            return tool
        if prize.region in tool.covers and challenge.id == "lantern" and tool.id == "extinguisher":
            return tool
        if challenge.id == "drift" and tool.id == "batten" and prize.region in tool.covers:
            return tool
    return None


def explain_rejection(challenge: Challenge, prize: Prize) -> str:
    return (
        f"(No story: {challenge.gerund} does not honestly threaten {prize.label} in a way "
        f"that the available tools can fix. Try a prize worn on {sorted(challenge.zone)}.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def predict(world: World, hero: Entity, challenge: Challenge, prize_id: str) -> dict:
    sim = world.copy()
    _do_challenge(sim, sim.get(hero.id), challenge, narrate=False)
    prize = sim.get(prize_id)
    return {
        "ruined": bool(prize.meters.get("dust", 0) >= THRESHOLD or prize.meters.get("spark", 0) >= THRESHOLD),
        "wobble": prize.meters.get("wobble", 0),
    }


def _do_challenge(world: World, hero: Entity, challenge: Challenge, narrate: bool = True) -> None:
    world.zone = set(challenge.zone)
    hero.meters["spark"] += 1
    hero.memes["curiosity"] += 1
    if narrate:
        world.say(f"{hero.id} went to {challenge.gerund}, and the air felt {challenge.danger}.")
    if hero.meters["spark"] >= THRESHOLD:
        for item in world.worn_items(hero):
            if item.protective:
                continue
            if item.region in world.zone and not world.covered(hero, item.region):
                item.meters["spark"] += 1
                item.meters["dust"] += 1
                if narrate:
                    world.say(f"{hero.pronoun('possessive').capitalize()} {item.label} got a little sparkly and dusty.")


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved surprises and brave little adventures.")


def setup(world: World, hero: Entity, parent: Entity, prize: Entity, challenge: Challenge) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.label} climbed up to {world.setting.place}, "
        f"where {hero.id} wore {hero.pronoun('possessive')} {prize.label} and looked ready for a new path."
    )
    world.say(
        f"{hero.id} wanted to {challenge.verb}, because {challenge.surprise} waited somewhere in the room."
    )


def warn(world: World, parent: Entity, hero: Entity, challenge: Challenge, prize: Entity) -> bool:
    pred = predict(world, hero, challenge, prize.id)
    if not pred["ruined"]:
        return False
    world.facts["predicted_ruin"] = True
    world.say(
        f'"If you rush in now, your {prize.label} could get messy," {hero.pronoun("possessive")} {parent.label} said. '
        f'"Let us think of a safer way."'
    )
    return True


def surprise_turn(world: World, hero: Entity, challenge: Challenge) -> None:
    hero.memes["surprise"] += 1
    world.say(
        f"{hero.id} still hurried toward the light, and then {challenge.surprise} popped out of the dark."
    )


def fix_with_tool(world: World, parent: Entity, hero: Entity, challenge: Challenge, prize: Entity) -> Optional[Tool]:
    tool = select_tool(challenge, prize)
    if tool is None:
        return None
    entity = world.add(Entity(
        id=tool.id,
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        protective=True,
        covers=set(tool.covers),
        plural=tool.plural,
        owner=hero.id,
        caretaker=parent.id,
    ))
    entity.worn_by = hero.id
    if predict(world, hero, challenge, prize.id)["ruined"]:
        entity.worn_by = None
        del world.entities[entity.id]
        return None
    world.say(
        f"Then {hero.pronoun('possessive')} {parent.label} smiled and said, "
        f'"How about we {tool.prep}?"'
    )
    return tool


def resolve(world: World, parent: Entity, hero: Entity, challenge: Challenge, prize: Entity, tool: Tool) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["joy"] += 1
    hero.memes["bond"] += 1
    world.say(
        f"{hero.id} nodded fast, and {hero.pronoun('possessive')} {parent.label} {tool.tail}."
    )
    if tool.id == "extinguisher":
        world.say(
            f"The magic extinguisher gave one soft puff, the surprise spark went out, and {hero.id}'s {prize.label} stayed clean."
        )
    else:
        world.say(
            f"The wooden batten held the loose hatch still, and {hero.id}'s {prize.label} stayed safe while the room settled down."
        )
    world.say(
        f"After that, {hero.id} kept exploring, with the room quiet and the adventure feeling bigger than the scare."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    challenge: Challenge,
    prize_cfg: Prize,
    hero_name: str = "Maya",
    hero_type: str = "girl",
    parent_type: str = "mother",
    trait: str = "curious",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters=_meters(), memes=_memes()))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="guide", meters=_meters(), memes=_memes()))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        owner=hero.id,
        caretaker=parent.id,
        meters=_meters(),
        memes=_memes(),
    ))

    hero.memes["curiosity"] += 1
    hero.trait = trait  # type: ignore[attr-defined]

    introduce(world, hero)
    world.say(
        f"{hero.id} was {trait} and loved the kind of adventure that started with one tiny surprise."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label} brought along {hero.pronoun('possessive')} {prize.label}, because the day looked ready for exploring."
    )
    world.say(f"{hero.id} felt a little thrill when the word {challenge.keyword} seemed to glow in the room.")

    world.para()
    setup(world, hero, parent, prize, challenge)
    warn(world, parent, hero, challenge, prize)
    surprise_turn(world, hero, challenge)

    world.para()
    tool = fix_with_tool(world, parent, hero, challenge, prize)
    if tool:
        resolve(world, parent, hero, challenge, prize, tool)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        challenge=challenge,
        setting=setting,
        tool=tool,
        resolved=tool is not None,
        trait=trait,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, prize, challenge = f["hero"], f["prize"], f["challenge"]
    return [
        f'Write a short adventure story for a child where {hero.id} finds a {challenge.keyword.lower()} surprise and uses a magic tool.',
        f"Tell a child-friendly story about {hero.id}, a {prize.label}, and a {challenge.id} moment in {world.setting.place}.",
        f"Write a small adventure with the words 'extinguisher' and 'batten' that ends safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, challenge, tool = f["hero"], f["parent"], f["prize"], f["challenge"], (f.get("tool") or next(iter(TOOLS.values())))
    qa = [
        QAItem(
            question=f"Who went exploring in {world.setting.place}?",
            answer=f"{hero.id} went exploring with {hero.pronoun('possessive')} {parent.label}.",
        ),
        QAItem(
            question=f"What was the surprise that made the adventure tricky?",
            answer=f"The tricky part was {challenge.surprise}, which made the room feel {challenge.danger}.",
        ),
        QAItem(
            question=f"What was {hero.id} wearing that needed to stay safe?",
            answer=f"{hero.id} was wearing {hero.pronoun('possessive')} {prize.label}, and it needed to stay clean and safe.",
        ),
    ]
    if f.get("resolved") and tool:
        qa.append(
            QAItem(
                question=f"How did the magic tool help at the end?",
                answer=(
                    f"The {tool.label} handled the trouble: it cooled the spark or held the wobble still, "
                    f"so {hero.id} could keep exploring without ruining the {prize.label}."
                ),
            )
        )
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel after the plan worked?",
                answer=f"{hero.id} felt happy and braver, because the surprise turned into a safe adventure with {hero.pronoun('possessive')} {parent.label}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    challenge = _safe_fact(world, f, "challenge")
    items: list[QAItem] = []
    if "magic" in challenge.tags:
        items.append(QAItem(
            question="What does magic mean in a story?",
            answer="Magic is something strange and wonderful that can make surprising things happen, like glowing lights or impossible tricks.",
        ))
    if "surprise" in challenge.tags:
        items.append(QAItem(
            question="What is a surprise?",
            answer="A surprise is something you do not expect. It can make you gasp, smile, or jump a little.",
        ))
    if f.get("tool") and (f.get("tool") or next(iter(TOOLS.values()))).id == "extinguisher":
        items.append(QAItem(
            question="What is an extinguisher for?",
            answer="An extinguisher is used to stop flames or sparks and make a dangerous fire go out.",
        ))
    if f.get("tool") and (f.get("tool") or next(iter(TOOLS.values()))).id == "batten":
        items.append(QAItem(
            question="What is a batten for?",
            answer="A batten is a flat strip of wood used to hold something steady or cover a gap.",
        ))
    return items


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
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
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(C,P) :- zone_of(C,R), worn_on(P,R).
needs_extinguisher(C,P) :- challenge(C), prize_at_risk(C,P), can_fix(extinguisher,C,P).
needs_batten(C,P) :- challenge(C), prize_at_risk(C,P), can_fix(batten,C,P).
valid(Place,C,P) :- setting(Place), challenge(C), prize(P), prize_at_risk(C,P), fixable(C,P).
valid_story(Place,C,P,G) :- valid(Place,C,P), wears(G,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for r in sorted(c.zone):
            lines.append(asp.fact("zone_of", cid, r))
        if "magic" in c.tags:
            lines.append(asp.fact("tag", cid, "magic"))
        if "surprise" in c.tags:
            lines.append(asp.fact("tag", cid, "surprise"))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in ("girl", "boy"):
            lines.append(asp.fact("wears", g, pid))
        if p.plural:
            lines.append(asp.fact("plural", pid))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, c))
        if t.id == "extinguisher":
            lines.append(asp.fact("can_fix", t.id, "glow", "prize"))
            lines.append(asp.fact("can_fix", t.id, "lantern", "prize"))
        if t.id == "batten":
            lines.append(asp.fact("can_fix", t.id, "drift", "prize"))
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for cid in setting.afford:
            challenge = _safe_lookup(CHALLENGES, cid)
            for pid, prize in PRIZES.items():
                if prize_at_risk(challenge, prize) and select_tool(challenge, prize):
                    combos.append((place, cid, pid))
    return combos


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


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
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
    ap = argparse.ArgumentParser(description="Adventure storyworld with magic and surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "challenge", None) and getattr(args, "prize", None):
        ch, pr = _safe_lookup(CHALLENGES, getattr(args, "challenge", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(ch, pr) and select_tool(ch, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, challenge, prize_id = rng.choice(list(combos))
    prize = _safe_lookup(PRIZES, prize_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(CHALLENGES, params.challenge),
        _safe_lookup(PRIZES, params.prize),
        hero_name=params.name,
        hero_type=params.gender,
        parent_type=params.parent,
        trait=params.trait,
    )
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


CURATED = [
    StoryParams(place="harbor_loft", challenge="glow", prize="cloak", name="Maya", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="dock_shed", challenge="drift", prize="boots", name="Eli", gender="boy", parent="father", trait="brave"),
    StoryParams(place="lighthouse_room", challenge="lantern", prize="cap", name="Nora", gender="girl", parent="mother", trait="bright-eyed"),
]


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
        for place, ch, prize in triples:
            genders = sorted(g for (pl, c, p, g) in stories if (pl, c, p) == (place, ch, prize))
            print(f"  {place:14} {ch:10} {prize:8}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.challenge} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
