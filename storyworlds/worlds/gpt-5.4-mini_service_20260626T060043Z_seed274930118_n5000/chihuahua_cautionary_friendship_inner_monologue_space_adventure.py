#!/usr/bin/env python3
"""
A standalone storyworld for a tiny space-adventure tale featuring a chihuahua,
cautionary friendship, and inner monologue.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    partner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "pilot"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type
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
    place: str = "the starport"
    feature: str = "a window onto the rings of Saturn"
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
    verb: str
    gerund: str
    rush: str
    danger: str
    consequence: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.zone = set(self.zone)
        w.fired = set(self.fired)
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


THRESHOLD = 1.0


def _propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("alarm", 0.0) >= THRESHOLD and actor.memes.get("reckless", 0.0) >= THRESHOLD:
            sig = ("trouble", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                actor.memes["trouble"] = actor.memes.get("trouble", 0.0) + 1
                out.append(f"{actor.pronoun().capitalize()} felt a pinch of trouble in {actor.pronoun('possessive')} chest.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def _do_mission(world: World, actor: Entity, mission: Mission, narrate: bool = True) -> None:
    if mission.id not in world.setting.affords:
        pass
    world.zone = {"hands", "torso", "eyes"}
    actor.meters[mission.id] = actor.meters.get(mission.id, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    if mission.id == "orbit_walk":
        actor.memes["awe"] = actor.memes.get("awe", 0.0) + 1
    _propagate(world, narrate=narrate)


def predict_risk(world: World, actor: Entity, mission: Mission, prize_id: str) -> dict:
    sim = world.copy()
    _do_mission(sim, sim.get(actor.id), mission, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "risk": prize.memes.get("shaken", 0.0) >= THRESHOLD,
        "fear": actor.memes.get("fear", 0.0) + 1,
    }


def prize_at_risk(mission: Mission, prize: Prize) -> bool:
    return prize.region in {"torso", "hands", "eyes"} or mission.id in {"asteroid_drift", "engine_buzz"}


def select_gear(mission: Mission, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if mission.danger in gear.guards and prize.region in gear.covers:
            return gear
    return None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "starport": Setting(place="the starport", feature="a bright blue planet in the viewport", affords={"orbit_walk", "asteroid_drift"}),
    "moonbase": Setting(place="the moonbase", feature="silver dust under the boots", affords={"orbit_walk", "engine_buzz"}),
    "dock": Setting(place="the docking bay", feature="a long tunnel full of blinking lights", affords={"asteroid_drift", "engine_buzz"}),
}

MISSIONS = {
    "orbit_walk": Mission(
        id="orbit_walk",
        verb="take a float walk",
        gerund="floating by the window",
        rush="dash toward the open hatch",
        danger="swaying",
        consequence="tossing them around",
        keyword="stars",
        tags={"space", "stars"},
    ),
    "asteroid_drift": Mission(
        id="asteroid_drift",
        verb="drift near the asteroids",
        gerund="drifting near the asteroids",
        rush="push off too hard",
        danger="bumping",
        consequence="sending them spinning",
        keyword="asteroids",
        tags={"space", "asteroids"},
    ),
    "engine_buzz": Mission(
        id="engine_buzz",
        verb="peek into the engine room",
        gerund="peeking at the engines",
        rush="run closer to the humming panel",
        danger="sparking",
        consequence="making the lights flash",
        keyword="engines",
        tags={"space", "engine"},
    ),
}

PRIZES = {
    "helmet": Prize(label="helmet", phrase="a shiny helmet with a clear visor", region="head"),
    "scarf": Prize(label="scarf", phrase="a soft scarf with tiny planets", region="torso"),
    "gloves": Prize(label="gloves", phrase="small blue gloves", region="hands", plural=True),
}

GEAR = [
    Gear(
        id="visor",
        label="a visor shield",
        covers={"head"},
        guards={"swaying"},
        prep="put on the visor shield first",
        tail="carefully came back with the visor shield on",
    ),
    Gear(
        id="tether",
        label="a tether belt",
        covers={"torso"},
        guards={"bumping"},
        prep="clip on the tether belt first",
        tail="stayed close with the tether belt clipped on",
    ),
    Gear(
        id="heatglove",
        label="heat gloves",
        covers={"hands"},
        guards={"sparking"},
        prep="wear the heat gloves first",
        tail="kept their hands safe with the heat gloves on",
    ),
]

CHIHUAHUA_NAMES = ["Pip", "Taco", "Milo", "Luz", "Nori", "Peanut"]
HUMAN_NAMES = ["Nova", "Iris", "Kai", "Juno", "Mira", "Rex"]
TRAITS = ["brave", "careful", "curious", "small", "bold"]


@dataclass
class StoryParams:
    place: str
    mission: str
    prize: str
    name: str
    partner: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning and narration
# ---------------------------------------------------------------------------
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
    out = []
    for place, setting in SETTINGS.items():
        for mission_id in setting.affords:
            mission = _safe_lookup(MISSIONS, mission_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(mission, prize) and select_gear(mission, prize):
                    out.append((place, mission_id, prize_id))
    return out


def intro(world: World, hero: Entity, partner: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a little chihuahua with a big heart and quick ears."
    )
    world.say(
        f"{hero.id} loved {partner.id}, {hero.pronoun('possessive')} human friend, and also loved {prize.phrase}."
    )


def setup(world: World, hero: Entity, partner: Entity, mission: Mission) -> None:
    world.say(
        f"One day at {world.setting.place}, {hero.id} and {partner.id} stared at {world.setting.feature}."
    )
    world.say(
        f"{hero.id} wanted to {mission.verb}, because {mission.gerund} felt like flying."
    )


def caution(world: World, hero: Entity, partner: Entity, mission: Mission, prize: Entity) -> bool:
    pred = predict_risk(world, hero, mission, prize.id)
    if not pred["risk"]:
        return False
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    world.say(
        f'"If you go now, your {prize.label} could get {mission.danger}," {partner.id} said softly.'
    )
    world.say(
        f"{hero.id} looked down, and a worried thought bounced inside {hero.pronoun('possessive')} head: "
        f"*Maybe the shiny thing is too fragile for this kind of space play.*"
    )
    return True


def defy_and_pause(world: World, hero: Entity, mission: Mission) -> None:
    hero.memes["reckless"] = hero.memes.get("reckless", 0.0) + 1
    world.say(
        f"{hero.id} almost rushed toward the hatch anyway, then stopped with tiny paws planted firm."
    )
    world.say(
        f"*I want to be fearless,* {hero.pronoun()} thought. *But being careful is also brave.*"
    )


def friendship_turn(world: World, hero: Entity, partner: Entity, mission: Mission, prize: Entity) -> Optional[Gear]:
    gear = select_gear(mission, prize)
    if gear is None:
        return None
    world.say(
        f"{partner.id} smiled and held up {gear.label}. \"We can still go,\" {partner.id} said. "
        f"\"Let's use this first.\""
    )
    world.say(
        f"{hero.id} listened, and the worry in {hero.pronoun('possessive')} chest got smaller."
    )
    return gear


def accept_and_finish(world: World, hero: Entity, partner: Entity, mission: Mission, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["fear"] = 0.0
    world.say(
        f"{hero.id} nodded, and {partner.id} helped {hero.id} {gear.prep}."
    )
    world.say(
        f"Then {hero.id} could {mission.verb}, {mission.gerund}, while {prize.label} stayed safe."
    )
    world.say(
        f"By the end, {hero.id} was smiling at the stars, and {partner.id} was laughing right beside {hero.id}."
    )


def tell_world(setting: Setting, mission: Mission, prize_cfg: Prize,
               name: str = "Pip", partner_name: str = "Nova", trait: str = "curious") -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="chihuahua", label=name))
    partner = world.add(Entity(id=partner_name, kind="character", type="boy", label=partner_name))
    prize = world.add(Entity(id="prize", type=prize_cfg.label, label=prize_cfg.label, phrase=prize_cfg.phrase))
    hero.partner = partner.id
    prize.owner = hero.id

    intro(world, hero, partner, prize)
    world.para()
    setup(world, hero, partner, mission)
    caution(world, hero, partner, mission, prize)
    defy_and_pause(world, hero, mission)
    world.para()
    gear = friendship_turn(world, hero, partner, mission, prize)
    if gear:
        accept_and_finish(world, hero, partner, mission, prize, gear)

    world.facts.update(
        hero=hero, partner=partner, prize=prize, mission=mission, gear=gear, setting=setting
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, partner, mission, prize = f["hero"], f["partner"], f["mission"], f["prize"]
    return [
        'Write a short space-adventure story for a little child about a chihuahua, friendship, and a careful choice.',
        f"Tell a gentle story where {hero.id} the chihuahua wants to {mission.verb} but {partner.id} worries about {prize.label}.",
        f'Write a story that includes the word "chihuahua" and ends with two friends choosing a safer way to explore space.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, partner, mission, prize = f["hero"], f["partner"], f["mission"], f["prize"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little chihuahua, and {partner.id}, who helps as a friend."
        ),
        QAItem(
            question=f"Why did {partner.id} warn {hero.id} about the {prize.label}?",
            answer=f"{partner.id} warned {hero.id} because going on the mission could make the {prize.label} get {mission.danger}."
        ),
        QAItem(
            question=f"How did {hero.id} feel in the middle of the story?",
            answer=f"{hero.id} felt worried at first, then calmer after {partner.id} offered a safer plan."
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"{hero.id} got to {mission.verb} safely, and the {prize.label} stayed safe too."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chihuahua?",
            answer="A chihuahua is a very small dog with a big personality."
        ),
        QAItem(
            question="What does it mean to be cautious?",
            answer="Being cautious means being careful and thinking about what could go wrong before you act."
        ),
        QAItem(
            question="What is a friendship?",
            answer="A friendship is a kind relationship where friends care about each other and help each other."
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet thinking voice inside a character's head."
        ),
        QAItem(
            question="Why do spaceships need safe gear?",
            answer="Spaceships need safe gear because space can be risky, and gear can help protect people and things."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
at_risk(M,P) :- mission(M), prize(P), mission_region(M,R), prize_region(P,R).
compatible(M,P,G) :- at_risk(M,P), gear(G), mission_danger(M,D), guards(G,D), covers(G,R), prize_region(P,R).
valid(Place,M,P) :- affords(Place,M), at_risk(M,P), compatible(M,P,_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for m in sorted(s.affords):
            lines.append(asp.fact("affords", pid, m))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("mission_region", mid, "torso" if mid != "engine_buzz" else "hands"))
        lines.append(asp.fact("mission_danger", mid, m.danger))
    for prid, p in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("prize_region", prid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for guard in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, guard))
    return "\n".join(lines)


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
        print(f"OK: clingo matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with a chihuahua, caution, friendship, and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--partner")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mission", None) is None or c[1] == getattr(args, "mission", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mission, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(CHIHUAHUA_NAMES)
    partner = getattr(args, "partner", None) or rng.choice(HUMAN_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, mission=mission, prize=prize, name=name, partner=partner, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_world(_safe_lookup(SETTINGS, params.place), _safe_lookup(MISSIONS, params.mission), _safe_lookup(PRIZES, params.prize),
                       name=params.name, partner_name=params.partner, trait=params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
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
    StoryParams(place="starport", mission="orbit_walk", prize="helmet", name="Pip", partner="Nova", trait="careful"),
    StoryParams(place="moonbase", mission="engine_buzz", prize="gloves", name="Taco", partner="Iris", trait="curious"),
    StoryParams(place="dock", mission="asteroid_drift", prize="scarf", name="Milo", partner="Kai", trait="brave"),
]


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
        header = f"### variant {i+1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
