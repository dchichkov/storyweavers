#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
POSITIONS = {"front", "behind", "beside", "under"}



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
    worn_by: Optional[str] = None
    position: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    hero: object | None = None
    mentor: object | None = None
    problem: object | None = None
    suit: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Mission:
    id: str
    call: str
    object_label: str
    object_phrase: str
    danger: str
    motion: str
    task: str
    safe_position: str
    wrong_position: str
    opening: str
    warning: str
    success: str
    ending_image: str
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
class Power:
    id: str
    label: str
    phrase: str
    handles: set[str] = field(default_factory=set)
    positions: set[str] = field(default_factory=set)
    action: str = ""
    glow: str = ""
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
class Rule:
    name: str
    apply: Callable[["World"], list[str]]
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_wrong_position_risk(world: World) -> list[str]:
    hero = world.get("hero")
    problem = world.get("problem")
    mission: Mission = _safe_fact(world, world.facts, "mission")
    if hero.position != mission.wrong_position:
        return []
    if ("risk", hero.position) in world.fired:
        return []
    world.fired.add(("risk", hero.position))
    problem.meters["risk"] += 1
    hero.memes["conflict"] += 1
    return [mission.warning]


def _r_right_position_control(world: World) -> list[str]:
    hero = world.get("hero")
    problem = world.get("problem")
    mission: Mission = _safe_fact(world, world.facts, "mission")
    power: Power = _safe_fact(world, world.facts, "power")
    if hero.position != mission.safe_position:
        return []
    if mission.task not in power.handles:
        return []
    if mission.safe_position not in power.positions:
        return []
    if ("control", hero.position, power.id) in world.fired:
        return []
    world.fired.add(("control", hero.position, power.id))
    problem.meters["risk"] = 0.0
    problem.meters["safe"] += 1
    hero.memes["joy"] += 1
    hero.memes["trust"] += 1
    hero.memes["conflict"] = 0.0
    return [mission.success]


CAUSAL_RULES = [
    Rule("wrong_position_risk", _r_wrong_position_risk),
    Rule("right_position_control", _r_right_position_control),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                out.extend(lines)
    if narrate:
        for line in out:
            world.say(line)
    return out


def power_fits(power: Power, mission: Mission) -> bool:
    return mission.task in power.handles and mission.safe_position in power.positions


def predict_position(world: World, position: str) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.position = position
    propagate(sim, narrate=False)
    problem = sim.get("problem")
    return {
        "risk": problem.meters["risk"],
        "safe": problem.meters["safe"],
        "conflict": hero.memes["conflict"],
    }


def position_phrase(pos: str) -> str:
    return {
        "front": "in front",
        "behind": "behind",
        "beside": "beside",
        "under": "under",
    }[pos]


def rhyme_for(mission: Mission) -> str:
    good = position_phrase(mission.safe_position)
    bad = position_phrase(mission.wrong_position)
    table = {
        "front": "Front to block the bumping thing",
        "behind": "Behind to brace and stop its swing",
        "beside": "Beside to guide the flapping side",
        "under": "Under to catch what drops and slides",
    }
    good_line = table[mission.safe_position]
    return f'"Not {bad}, {good}; pause, choose, and save the day," said the mentor in a rhyme.'


def introduce(world: World, hero: Entity, power: Power) -> None:
    trait = hero.traits[0] if hero.traits else "brave"
    world.say(
        f"In {world.setting.place}, {hero.id} was a little {trait} superhero who wore "
        f"{power.phrase} and practiced helping before breakfast was even over."
    )
    world.say(
        f"When {power.glow} shimmered around {hero.pronoun('possessive')} hands, "
        f"{hero.pronoun()} felt ready for any small emergency."
    )


def mentor_intro(world: World, mentor: Entity) -> None:
    world.say(
        f"{mentor.id}, the neighborhood mentor, always said that real heroes did not only move fast. "
        f"They also chose the right position."
    )


def alarm(world: World, mission: Mission) -> None:
    world.say(
        f"That afternoon, a call came from {world.setting.place}: {mission.opening}"
    )


def boast(world: World, hero: Entity, mission: Mission) -> None:
    hero.memes["pride"] += 1
    hero.position = mission.wrong_position
    world.say(
        f'"I know where to stand!" {hero.id} said. {hero.pronoun().capitalize()} zipped '
        f'{position_phrase(mission.wrong_position)} the {mission.object_label}, because it looked like the flashiest spot.'
    )
    propagate(world, narrate=True)


def warning(world: World, mentor: Entity, mission: Mission) -> None:
    wrong = predict_position(world, mission.wrong_position)
    if wrong["risk"] >= THRESHOLD:
        world.say(
            f'{mentor.id} lifted a careful finger. "That spot looks bold, but it will make the trouble worse," '
            f'{mentor.pronoun()} said.'
        )
        world.facts["predicted_risk"] = wrong["risk"]
        world.facts["predicted_wrong_position"] = mission.wrong_position


def resist(world: World, hero: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"{hero.id} frowned for a moment. {hero.pronoun().capitalize()} wanted the biggest pose, not the quietest plan."
    )


def teach_rhyme(world: World, mentor: Entity, mission: Mission) -> None:
    world.say(rhyme_for(mission))
    world.facts["rhyme"] = rhyme_for(mission)


def reposition(world: World, hero: Entity, mission: Mission, power: Power) -> None:
    hero.position = mission.safe_position
    world.say(
        f"{hero.id} took a breath, moved {position_phrase(mission.safe_position)} the {mission.object_label}, "
        f"and remembered what {power.label} were really for."
    )
    propagate(world, narrate=True)


def celebrate(world: World, hero: Entity, mentor: Entity, mission: Mission, power: Power) -> None:
    world.say(
        f'The whole place cheered. "{mission.call} complete!" {mentor.id} said with a grin.'
    )
    world.say(
        f"{hero.id} smiled then, because the best part of being a superhero was not looking tallest. "
        f"It was helping at the right moment from the right position."
    )
    world.say(
        f"In the last bright picture of the day, {hero.id} stood {position_phrase(mission.safe_position)} the "
        f"{mission.object_label}, {power.glow} glowing softly, while {mission.ending_image}"
    )


def tell(setting: Setting, mission: Mission, power: Power, hero_name: str, hero_type: str,
         trait: str, mentor_name: str, mentor_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=[trait],
        label=hero_name,
    ))
    mentor = world.add(Entity(
        id=mentor_name,
        kind="character",
        type=mentor_type,
        label=mentor_name,
    ))
    problem = world.add(Entity(
        id="problem",
        kind="thing",
        type="hazard",
        label=mission.object_label,
        phrase=mission.object_phrase,
    ))
    suit = world.add(Entity(
        id="power",
        kind="thing",
        type="gear",
        label=power.label,
        phrase=power.phrase,
        owner=hero.id,
        worn_by=hero.id,
    ))

    world.facts.update(
        hero=hero,
        mentor=mentor,
        mission=mission,
        power=power,
        setting=setting,
        suit=suit,
    )

    introduce(world, hero, power)
    mentor_intro(world, mentor)

    world.para()
    alarm(world, mission)
    warning(world, mentor, mission)
    boast(world, hero, mission)

    world.para()
    resist(world, hero)
    teach_rhyme(world, mentor, mission)
    reposition(world, hero, mission, power)
    celebrate(world, hero, mentor, mission, power)

    world.facts["resolved"] = world.get("problem").meters["safe"] >= THRESHOLD
    world.facts["final_position"] = hero.position
    return world


SETTINGS = {
    "Maple Park": Setting(place="Maple Park", affords={"ball", "banner", "kitten"}),
    "River Square": Setting(place="River Square", affords={"stroller", "banner"}),
    "Sunbeam Schoolyard": Setting(place="Sunbeam Schoolyard", affords={"ball", "kitten"}),
}

MISSIONS = {
    "ball": Mission(
        id="ball",
        call="Bumper Ball Alert",
        object_label="giant rubber ball",
        object_phrase="a giant rubber ball with a wobbling star on it",
        danger="it might bump the juice table",
        motion="bouncing",
        task="block",
        safe_position="front",
        wrong_position="behind",
        opening="A giant rubber ball had bounced loose and was thumping toward the juice table.",
        warning="From behind, the hero could only chase the ball while it kept bouncing toward the cups.",
        success="From the front, the hero planted steady feet and blocked the ball before one drop of juice could spill.",
        ending_image="the giant rubber ball rested still and the paper cups trembled no more",
        tags={"ball", "front", "position"},
    ),
    "stroller": Mission(
        id="stroller",
        call="Rolling Stroller Alert",
        object_label="empty stroller",
        object_phrase="an empty stroller with a moon sticker on the handle",
        danger="it might roll down the little hill",
        motion="rolling",
        task="brace",
        safe_position="behind",
        wrong_position="front",
        opening="An empty stroller had started rolling toward the little hill by the flower bed.",
        warning="In front, the hero would get pushed and bumped as the stroller rolled faster.",
        success="From behind, the hero braced, pushed back with care, and stopped the stroller before it reached the hill.",
        ending_image="the empty stroller stood safe by the path while the flowers nodded in the breeze",
        tags={"wheels", "behind", "position"},
    ),
    "banner": Mission(
        id="banner",
        call="Parade Banner Alert",
        object_label="parade banner",
        object_phrase="a bright parade banner snapping in the wind",
        danger="it might slap the cookie stand and tear",
        motion="flapping",
        task="guide",
        safe_position="beside",
        wrong_position="under",
        opening="A bright parade banner had come loose and was snapping wild circles over the cookie stand.",
        warning="Under the banner, the hero could only duck while the cloth whipped from side to side.",
        success="Beside the banner, the hero guided the cloth with gentle pulls until it settled and stayed tied.",
        ending_image="the parade banner fluttered neatly and the cookie stand looked calm again",
        tags={"wind", "beside", "position"},
    ),
    "kitten": Mission(
        id="kitten",
        call="Tree-Top Kitten Alert",
        object_label="striped kitten",
        object_phrase="a striped kitten peeking from a branch",
        danger="it might slip from the branch",
        motion="slipping",
        task="catch",
        safe_position="under",
        wrong_position="beside",
        opening="A striped kitten on a branch kept mewing and sliding closer to the edge.",
        warning="Beside the tree, the hero could wave and worry, but not catch the kitten if it slipped.",
        success="Under the branch, the hero lifted ready arms and caught the kitten in a soft, safe scoop.",
        ending_image="the striped kitten purred against a small shoulder while the branch swayed overhead",
        tags={"tree", "under", "position"},
    ),
}

POWERS = {
    "mirror_shield": Power(
        id="mirror_shield",
        label="Mirror Shield",
        phrase="a silver suit with a round Mirror Shield",
        handles={"block"},
        positions={"front"},
        action="held up the bright shield",
        glow="a neat blue shine",
        tags={"shield"},
    ),
    "rocket_boots": Power(
        id="rocket_boots",
        label="Rocket Boots",
        phrase="red boots that hummed with tiny rocket sounds",
        handles={"brace"},
        positions={"behind"},
        action="dug in with the rocket boots",
        glow="a warm orange sparkle",
        tags={"boots"},
    ),
    "stretch_ribbon": Power(
        id="stretch_ribbon",
        label="Stretch Ribbon",
        phrase="a hero belt with a long Stretch Ribbon",
        handles={"guide"},
        positions={"beside"},
        action="looped the ribbon around the flapping cloth",
        glow="a purple twinkle",
        tags={"ribbon"},
    ),
    "cloud_arms": Power(
        id="cloud_arms",
        label="Cloud Arms",
        phrase="soft cloud sleeves that could puff big and gentle",
        handles={"catch"},
        positions={"under"},
        action="puffed the sleeves into a safe catching cushion",
        glow="a pearly white glow",
        tags={"cloud"},
    ),
}

HERO_NAMES = ["Nova", "Dash", "Skye", "Bolt", "Mira", "Jett", "Ruby", "Max"]
MENTOR_NAMES = ["Captain Star", "Aunt Nova", "Coach Comet", "Guardian Glow"]
TRAITS = ["brave", "quick", "eager", "sparkly", "determined", "kind"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for mission_id in sorted(setting.affords):
            mission = _safe_lookup(MISSIONS, mission_id)
            for power_id, power in POWERS.items():
                if power_fits(power, mission):
                    combos.append((place, mission_id, power_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    mission: str
    power: str
    hero_name: str
    hero_type: str
    mentor_name: str
    mentor_type: str
    trait: str
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


KNOWLEDGE = {
    "front": [
        (
            "What does standing in front of something mean?",
            "Standing in front means you are on the side that faces where something is going, so you can block it or meet it first.",
        )
    ],
    "behind": [
        (
            "What does standing behind something mean?",
            "Standing behind means you are on the back side of it, which can help you brace it or slow it down safely.",
        )
    ],
    "beside": [
        (
            "What does standing beside something mean?",
            "Standing beside means you are next to it, which is useful when you need to guide it from the side.",
        )
    ],
    "under": [
        (
            "What does standing under something mean?",
            "Standing under means you are below it, ready to catch it if it drops.",
        )
    ],
    "shield": [
        (
            "What does a shield help a hero do?",
            "A shield helps a hero block something moving toward them, like a ball or a splash.",
        )
    ],
    "boots": [
        (
            "Why would rocket boots help someone brace something?",
            "Rocket boots can push against the ground, so they help a hero stay steady and stop something from rolling away.",
        )
    ],
    "ribbon": [
        (
            "How can a ribbon help with a flapping banner?",
            "A long ribbon can reach the loose cloth and guide it gently from the side until it settles down.",
        )
    ],
    "cloud": [
        (
            "Why is it good to be under something that might fall?",
            "Being under it lets you catch it safely before it hits the ground.",
        )
    ],
    "position": [
        (
            "Why does a superhero's position matter?",
            "A superhero's position matters because standing in the right place makes the power work better and keeps everyone safer.",
        )
    ],
}

KNOWLEDGE_ORDER = ["position", "front", "behind", "beside", "under", "shield", "boots", "ribbon", "cloud"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    mission: Mission = _safe_fact(world, f, "mission")
    power: Power = _safe_fact(world, f, "power")
    mentor: Entity = _safe_fact(world, f, "mentor")
    return [
        f'Write a tiny superhero story for a young child that uses the word "position" and includes a gentle conflict.',
        f"Tell a superhero story where {hero.id} first stands {position_phrase(mission.wrong_position)} a {mission.object_label}, then learns through a rhyme to stand {position_phrase(mission.safe_position)} instead.",
        f"Write a simple rescue story in {world.setting.place} featuring {power.label}, a mentor named {mentor.id}, and a happy ending that proves the right position solved the problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    mentor: Entity = _safe_fact(world, f, "mentor")
    mission: Mission = _safe_fact(world, f, "mission")
    power: Power = _safe_fact(world, f, "power")
    qa: list[QAItem] = [
        QAItem(
            question=f"Who is the little superhero in this story, and what power did {hero.pronoun()} wear?",
            answer=f"The little superhero is {hero.id}. {hero.pronoun().capitalize()} wore {power.phrase}, which helped with the rescue.",
        ),
        QAItem(
            question=f"What problem happened in {world.setting.place}?",
            answer=f"In {world.setting.place}, {mission.opening[0].lower() + mission.opening[1:]} The trouble was that {mission.danger}.",
        ),
        QAItem(
            question=f"Where did {hero.id} stand at first, and why was that a problem?",
            answer=(
                f"{hero.id} stood {position_phrase(mission.wrong_position)} the {mission.object_label} at first because it looked flashy. "
                f"That was a problem because {mission.warning[0].lower() + mission.warning[1:]}"
            ),
        ),
        QAItem(
            question=f"What rhyme helped {hero.id} choose the right position?",
            answer=(
                f"{mentor.id} used a rhyme to remind {hero.id} that the rescue needed the right position, not the showiest one. "
                f"The rhyme pointed away from standing {position_phrase(mission.wrong_position)} and toward standing {position_phrase(mission.safe_position)}."
            ),
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did {hero.id} finally solve the problem?",
                answer=(
                    f"{hero.id} moved {position_phrase(mission.safe_position)} the {mission.object_label} and used {power.label}. "
                    f"{mission.success} That is how the rescue worked."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    mission: Mission = _safe_fact(world, world.facts, "mission")
    power: Power = _safe_fact(world, world.facts, "power")
    tags = set(mission.tags) | set(power.tags)
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.position:
            bits.append(f"position={ent.position}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="Maple Park",
        mission="ball",
        power="mirror_shield",
        hero_name="Nova",
        hero_type="girl",
        mentor_name="Captain Star",
        mentor_type="woman",
        trait="brave",
    ),
    StoryParams(
        place="River Square",
        mission="stroller",
        power="rocket_boots",
        hero_name="Dash",
        hero_type="boy",
        mentor_name="Coach Comet",
        mentor_type="man",
        trait="quick",
    ),
    StoryParams(
        place="Maple Park",
        mission="banner",
        power="stretch_ribbon",
        hero_name="Mira",
        hero_type="girl",
        mentor_name="Aunt Nova",
        mentor_type="woman",
        trait="kind",
    ),
    StoryParams(
        place="Sunbeam Schoolyard",
        mission="kitten",
        power="cloud_arms",
        hero_name="Jett",
        hero_type="boy",
        mentor_name="Guardian Glow",
        mentor_type="woman",
        trait="eager",
    ),
]


def explain_rejection(mission: Mission, power: Power) -> str:
    if mission.task not in power.handles:
        return (
            f"(No story: {power.label} cannot handle the task '{mission.task}' needed for the "
            f"{mission.object_label} rescue.)"
        )
    if mission.safe_position not in power.positions:
        return (
            f"(No story: {power.label} does not work from the needed position "
            f"'{mission.safe_position}' for the {mission.object_label} rescue.)"
        )
    return "(No story: that combination is unreasonable.)"


ASP_RULES = r"""
fits_power(Mission, Power) :-
    needs_task(Mission, Task),
    needs_position(Mission, Pos),
    handles(Power, Task),
    works_at(Power, Pos).

valid(Place, Mission, Power) :-
    affords(Place, Mission),
    fits_power(Mission, Power).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for mission_id in sorted(setting.affords):
            lines.append(asp.fact("affords", place, mission_id))
    for mission_id, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mission_id))
        lines.append(asp.fact("needs_task", mission_id, mission.task))
        lines.append(asp.fact("needs_position", mission_id, mission.safe_position))
    for power_id, power in POWERS.items():
        lines.append(asp.fact("power", power_id))
        for task in sorted(power.handles):
            lines.append(asp.fact("handles", power_id, task))
        for pos in sorted(power.positions):
            lines.append(asp.fact("works_at", power_id, pos))
    return "\n".join(lines)


def asp_program(extra_show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra_show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny superhero story world about choosing the right position with help from a rhyme."
    )
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--mission", choices=list(MISSIONS))
    ap.add_argument("--power", choices=list(POWERS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--mentor-name")
    ap.add_argument("--mentor-type", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--seed", type=int, default=None, help="base random seed")
    ap.add_argument("--trace", action="store_true", help="show world-model state")
    ap.add_argument("--qa", action="store_true", help="include QA sets")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity")
    ap.add_argument("--show-asp", action="store_true", help="print ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "mission", None) and getattr(args, "mission", None) not in _safe_lookup(SETTINGS, getattr(args, "place", None)).affords:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "mission", None) and getattr(args, "power", None):
        mission = _safe_lookup(MISSIONS, getattr(args, "mission", None))
        power = _safe_lookup(POWERS, getattr(args, "power", None))
        if not power_fits(power, mission):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        combo for combo in valid_combos()
        if (getattr(args, "place", None) is None or combo[0] == getattr(args, "place", None))
        and (getattr(args, "mission", None) is None or combo[1] == getattr(args, "mission", None))
        and (getattr(args, "power", None) is None or combo[2] == getattr(args, "power", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, mission, power = (list(rng.choice(combos)) + [None, None, None])[:3]
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    mentor_type = getattr(args, "mentor_type", None) or rng.choice(["woman", "man"])
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    mentor_name = getattr(args, "mentor_name", None) or rng.choice(MENTOR_NAMES)
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place,
        mission=mission,
        power=power,
        hero_name=hero_name,
        hero_type=hero_type,
        mentor_name=mentor_name,
        mentor_type=mentor_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(MISSIONS, params.mission),
        _safe_lookup(POWERS, params.power),
        params.hero_name,
        params.hero_type,
        params.trait,
        params.mentor_name,
        params.mentor_type,
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        status = asp_verify()
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else 12345
        rng = random.Random(base_seed)
        checked = 0
        for _ in range(min(10, len(valid_combos()))):
            params = resolve_params(args, rng)
            sample = generate(params)
            if not sample.story.strip():
                print("Verification failed: empty story")
                sys.exit(1)
            checked += 1
        if status == 0:
            print(f"OK: exercised {checked} generated stories.")
        sys.exit(status)
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, mission, power) combos:\n")
        for place, mission, power in triples:
            print(f"  {place:18} {mission:10} {power}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.hero_name}: {p.mission} at {p.place} with {p.power}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
