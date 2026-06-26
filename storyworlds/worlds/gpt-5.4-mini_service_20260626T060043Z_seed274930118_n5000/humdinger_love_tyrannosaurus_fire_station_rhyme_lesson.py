#!/usr/bin/env python3
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide: object | None = None
    hero: object | None = None
    item: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "mom", "woman", "captain"}
        masculine = {"boy", "father", "dad", "man", "engineer"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def add_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount
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
    place: str = "the fire station"
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    keyword: str
    rhyme: str
    lesson: str
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
class Prize:
    label: str
    phrase: str
    type: str
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.zone = set(self.zone)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def rhyme_line(action: Action) -> str:
    return action.rhyme


def lesson_line(action: Action) -> str:
    return action.lesson


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    world.zone = set(action.zone)
    actor.add_meter("adventure")
    actor.add_meme("love")
    actor.add_meme("suspense", 1.0)
    if narrate:
        world.say(f"{actor.id} launched the {action.gerund} mission.")
        world.say(rhyme_line(action))
    for item in list(world.entities.values()):
        if item.carried_by == actor.id and item.region in world.zone:
            item.add_meter(action.id)
    if narrate:
        world.say(lesson_line(action))


def predict_damage(world: World, actor: Entity, action: Action, prize_id: str) -> bool:
    sim = world.copy()
    _do_action(sim, sim.get(actor.id), action, narrate=False)
    prize = sim.entities[prize_id]
    return prize.meters.get(action.id, 0.0) >= THRESHOLD


def prize_at_risk(action: Action, prize: Prize) -> bool:
    return prize.region in action.zone


def select_gear(action: Action, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if action.id in gear.guards and prize.region in gear.covers:
            return gear
    return None


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved the fire station like a launch pad for brave days.")


def love_of_space_style(world: World, hero: Entity, action: Action) -> None:
    hero.add_meme("love")
    world.say(f"{hero.pronoun().capitalize()} loved the bright buttons, the echoing boots, and the mission hum of the station.")
    world.say(f"The whole place felt like a rocket bay ready for a rescue, and {hero.id} wanted the next big {action.keyword} adventure.")


def bring_prize(world: World, hero: Entity, prize: Entity) -> None:
    prize.carried_by = hero.id
    world.say(f"{hero.id}'s {world.facts['guide'].label_word} had bought {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and carried it everywhere.")


def arrive(world: World, hero: Entity, guide: Entity, action: Action) -> None:
    world.say(f"One busy day, {hero.id} and {hero.pronoun('possessive')} {guide.label_word} were at {world.setting.place}.")
    world.say(f"{hero.id} wanted to {action.verb}, but the station bell gave a sharp little buzz of suspense.")


def warn(world: World, guide: Entity, hero: Entity, action: Action, prize: Entity) -> bool:
    if not predict_damage(world, hero, action, prize.id):
        return False
    world.facts["risk"] = action.risk
    world.say(f'"If you {action.verb}, your {prize.label} will get {action.risk}," {guide.label_word} said.')
    return True


def tense(world: World, hero: Entity, action: Action) -> None:
    hero.add_meme("defiance")
    world.say(f"{hero.id} took a tiny breath and tried to {action.rush}.")
    world.say(f"Then the hallway seemed extra quiet, like everyone was waiting for the choice to land.")


def offer_fix(world: World, guide: Entity, hero: Entity, action: Action, prize: Entity) -> Optional[Gear]:
    gear = select_gear(action, world.facts["prize_cfg"])
    if gear is None:
        return None
    if not predict_damage(world, hero, action, prize.id):
        return None
    item = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
    ))
    item.carried_by = hero.id
    world.say(f'{guide.label_word} smiled and said, "How about we {gear.prep} and still go?"')
    return gear


def resolve(world: World, hero: Entity, guide: Entity, action: Action, prize: Entity, gear: Gear) -> None:
    hero.memes["suspense"] = 0.0
    hero.add_meme("joy")
    world.say(f"{hero.id} nodded fast and hugged {guide.pronoun('object')}.")
    world.say(f"They {gear.tail}. Soon {hero.id} was {action.gerund}, {hero.pronoun('possessive')} {prize.label} stayed safe, and the station shone with happy, busy energy.")
    world.say(f"{hero.id} learned that a humdinger idea is best when it keeps love and safety together.")


def tell(setting: Setting, action: Action, prize_cfg: Prize, hero_name: str, hero_type: str, guide_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    guide = world.add(Entity(id="Guide", kind="character", type=guide_type, label="captain"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, caretaker=guide.id, owner=hero.id, carried_by=hero.id))
    world.facts.update(hero=hero, guide=guide, prize=prize, prize_cfg=prize_cfg, action=action, setting=setting)

    intro(world, hero)
    love_of_space_style(world, hero, action)
    bring_prize(world, hero, prize)
    world.para()
    arrive(world, hero, guide, action)
    if warn(world, guide, hero, action, prize):
        tense(world, hero, action)
    world.para()
    gear = offer_fix(world, guide, hero, action, prize)
    if gear:
        resolve(world, hero, guide, action, prize, gear)
        world.facts["gear"] = gear
    else:
        world.say(f"In the end, they chose a safer way, and the station kept its calm hum.")
    return world


SETTINGS = {
    "fire_station": Setting(place="the fire station", affords={"hose_race", "drill_dash", "tower_trek"}),
}

ACTIONS = {
    "hose_race": Action(
        id="hose_race",
        verb="race the hose",
        gerund="racing the hose",
        rush="dash down the hall",
        risk="all tangled and wet",
        zone={"feet", "legs"},
        keyword="hose",
        rhyme="The hose went swoosh, the boots went clack; the tiny crew sped down and back.",
        lesson="Lesson learned: fast fun is better when the gear fits right.",
    ),
    "drill_dash": Action(
        id="drill_dash",
        verb="dash through the drill",
        gerund="dashing through the drill",
        rush="bolt toward the drill room",
        risk="smudged with soot",
        zone={"hands", "torso"},
        keyword="drill",
        rhyme="The drill beep-beeped bright, the lantern glowed; the brave team picked the careful road.",
        lesson="Lesson learned: careful steps can save the day and still feel exciting.",
    ),
    "tower_trek": Action(
        id="tower_trek",
        verb="trek up the tower",
        gerund="trekking up the tower",
        rush="climb up the tower stairs",
        risk="shaking loose",
        zone={"torso", "head"},
        keyword="tower",
        rhyme="Up the tower, step by step, the stars looked near in every step.",
        lesson="Lesson learned: patience helps a big adventure finish well.",
    ),
}

PRIZES = {
    "badge": Prize(label="badge", phrase="a shiny silver badge", type="badge", region="torso"),
    "cape": Prize(label="cape", phrase="a bright red cape", type="cape", region="torso"),
    "helmet": Prize(label="helmet", phrase="a polished helmet", type="helmet", region="head"),
}

GEAR = [
    Gear(id="boots", label="rain boots", covers={"feet", "legs"}, guards={"hose_race"}, prep="put on the rain boots first", tail="walked back in rain boots"),
    Gear(id="jacket", label="a fire jacket", covers={"torso"}, guards={"drill_dash", "tower_trek"}, prep="zip on a fire jacket first", tail="marched on in the fire jacket"),
    Gear(id="helmet_guard", label="a snug helmet guard", covers={"head"}, guards={"tower_trek"}, prep="snap on a snug helmet guard first", tail="kept climbing with the helmet guard"),
]

GIRL_NAMES = ["Mia", "Ava", "Zoe", "Luna", "Nora"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Sam"]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    gender: str
    guide_type: str
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
    out = []
    for place, setting in SETTINGS.items():
        for a in setting.affords:
            action = _safe_lookup(ACTIONS, a)
            for p, prize in PRIZES.items():
                if prize_at_risk(action, prize) and select_gear(action, prize):
                    out.append((place, a, p))
    return out


def explain_rejection(action: Action, prize: Prize) -> str:
    if not prize_at_risk(action, prize):
        return f"(No story: {action.gerund} does not really reach a {prize.label} in a way that makes a fair problem.)"
    return f"(No story: nothing in the gear closet can safely cover a {prize.label} for that kind of action.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a fire-station adventure with rhyme, suspense, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide-type", choices=["mother", "father", "captain"], default="captain")
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
    if getattr(args, "action", None) and getattr(args, "prize", None):
        a, p = _safe_lookup(ACTIONS, getattr(args, "action", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(a, p) and select_gear(a, p)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, prize = rng.choice(list(combos))
    pr = _safe_lookup(PRIZES, prize)
    gender = getattr(args, "gender", None) or rng.choice(sorted(pr.genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide_type = getattr(args, "guide_type", None) or "captain"
    return StoryParams(place=place, action=action, prize=prize, name=name, gender=gender, guide_type=guide_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.guide_type)
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
    return [
        f'Write a short space-adventure-style story for a child set in {f["setting"].place} with rhyme and suspense, using the word "humdinger".',
        f"Tell a gentle fire-station story where {f['hero'].id} loves {f['prize'].label} and learns a safety lesson during a {f['action'].keyword} mission.",
        f'Write a story about a lovable "tyrannosaurus" feeling excitement at a fire station, with a happy lesson learned at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, prize, action = f["hero"], f["guide"], f["prize"], f["action"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do at {world.setting.place}?",
            answer=f"{hero.id} was trying to {action.verb} at {world.setting.place}, because {hero.pronoun('subject')} loved the big, shiny, space-adventure feeling of the station.",
        ),
        QAItem(
            question=f"Why did the {guide.label_word} warn {hero.id} about the {prize.label}?",
            answer=f"The {guide.label_word} warned {hero.id} because the {prize.label} would get {action.risk} if {hero.id} kept going without the right gear.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and the {prize.label}?",
            answer=f"They chose the safe fix, so {hero.id} could keep {action.gerund} while the {prize.label} stayed safe and clean.",
        ),
        QAItem(
            question="What lesson did the story teach?",
            answer=f"It taught that a humdinger idea is best when it is also safe, and that love can help everyone pick a smarter path.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fire station?",
            answer="A fire station is a place where firefighters keep their trucks, tools, and gear so they can help people quickly.",
        ),
        QAItem(
            question="What does a tyrannosaurus mean?",
            answer="A tyrannosaurus is a kind of dinosaur with a long tail, big legs, and a very famous name.",
        ),
        QAItem(
            question="What does a rhyme do in a story?",
            answer="A rhyme makes words sound like they match at the ends, which can make a story feel playful and fun to hear.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is the helpful idea a character understands by the end of a story.",
        ),
    ]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("risk_of", aid, a.risk))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for gid, g in enumerate(GEAR):
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
fix(A,P) :- prize_at_risk(A,P), guards(G,M), covers(G,R), risk_of(A,M), zone(A,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), fix(A,P).
#show valid/3.
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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="fire_station", action="hose_race", prize="badge", name="Mia", gender="girl", guide_type="captain"),
    StoryParams(place="fire_station", action="drill_dash", prize="cape", name="Leo", gender="boy", guide_type="captain"),
    StoryParams(place="fire_station", action="tower_trek", prize="helmet", name="Nora", gender="girl", guide_type="captain"),
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for row in triples:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.action} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
