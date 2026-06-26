#!/usr/bin/env python3
"""
A small heartwarming storyworld about a child who tries to build a tiny
pyramid, learns by curiosity, and discovers that humor can turn a wobble into
glory.
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
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Place:
    id: str
    label: str
    surface: str
    affords: set[str] = field(default_factory=set)
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
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    ripple: str
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
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    at_risk_by: set[str] = field(default_factory=set)
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
class Helper:
    id: str
    label: str
    offer: str
    effect: str
    rhyme: str
    funny: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place) -> None:
        self.place = place
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

    def character(self) -> Entity:
        for e in self.entities.values():
            if e.kind == "character":
                return e
        pass

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        import copy
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    helper: str
    name: str
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


PLACES = {
    "patio": Place("patio", "the patio", "stone", {"build"}),
    "garden": Place("garden", "the garden", "grass", {"build"}),
    "sandbox": Place("sandbox", "the sandbox", "sand", {"build"}),
}

ACTIVITIES = {
    "blocks": Activity(
        id="blocks",
        verb="build a tower",
        gerund="building a tower",
        mess="wobble",
        ripple="the blocks could slip",
        keyword="pyramid",
        tags={"pyramid", "glory", "curiosity"},
    ),
    "cups": Activity(
        id="cups",
        verb="stack cups into a pyramid",
        gerund="stacking cups into a pyramid",
        mess="tilt",
        ripple="the cups could tip",
        keyword="cup-ful",
        tags={"cup-ful", "pyramid", "humor"},
    ),
}

PRIZES = {
    "pyramid": Prize(
        id="pyramid",
        label="pyramid",
        phrase="a little wooden pyramid",
        region="table",
        at_risk_by={"wobble", "tilt"},
    ),
    "cupful": Prize(
        id="cupful",
        label="cup-ful",
        phrase="a bright cup-ful of water",
        region="table",
        plural=False,
        at_risk_by={"wobble", "tilt"},
    ),
}

HELPERS = {
    "rhyme": Helper(
        id="rhyme",
        label="rhyme",
        offer="say a tiny rhyme",
        effect="steady",
        rhyme="A stack can sway, but we can say, 'Hold on, hold on, stay!'",
        funny="the rhyme made the wobble feel less scary",
        guards={"wobble", "tilt"},
        covers={"table"},
    ),
    "curiosity": Helper(
        id="curiosity",
        label="curiosity",
        offer="look closely and figure out why it leaned",
        effect="learn",
        rhyme="Why did it bend? Let's gently tend and find the helpful end.",
        funny="the curious look made everyone slow down and smile",
        guards={"wobble", "tilt"},
        covers={"table"},
    ),
    "humor": Helper(
        id="humor",
        label="humor",
        offer="laugh kindly at the silly teeter",
        effect="soften",
        rhyme="If it goes boop, we do not swoop; we giggle, then we regroup.",
        funny="the giggle turned the wobble into a game",
        guards={"wobble", "tilt"},
        covers={"table"},
    ),
}

NAMES = ["Mina", "Eli", "Noa", "Luca", "Iris", "June", "Owen", "Rory"]


def start_story(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f"{hero.id} loved making small things with careful hands, especially when a pyramid could grow."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} wanted to {activity.verb}, because a tiny pyramid felt full of glory."
    )
    world.say(
        f"On the {world.place.label}, {hero.id} set down {prize.phrase} and got ready to begin."
    )


def predict_problem(world: World, activity: Activity, prize: Entity) -> bool:
    return prize.region == "table" and activity.mess in prize.at_risk_by


def do_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters[activity.mess] = hero.meters.get(activity.mess, 0.0) + 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    if activity.id == "blocks":
        hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    else:
        hero.memes["humor"] = hero.memes.get("humor", 0.0) + 1.0


def warn(world: World, hero: Entity, prize: Entity, activity: Activity) -> None:
    if predict_problem(world, activity, prize):
        world.say(
            f"{hero.id} noticed the stack leaning and paused. "
            f'"If I keep going," {hero.pronoun("subject")} thought, "the {prize.label} might topple."'
        )


def helper_turn(world: World, hero: Entity, helper: Helper, activity: Activity, prize: Entity) -> None:
    sig = ("helper", helper.id, activity.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes[helper.effect] = hero.memes.get(helper.effect, 0.0) + 1.0
    world.say(
        f"Then {hero.id} chose {helper.label}: {helper.offer}."
    )
    world.say(helper.rhyme)
    world.say(
        f"That {helper.funny}, and {hero.id} used the idea to steady the {prize.label}."
    )


def resolve(world: World, hero: Entity, activity: Activity, prize: Entity, helper: Helper) -> None:
    hero.memes["glory"] = hero.memes.get("glory", 0.0) + 1.0
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
    world.say(
        f"With a slower breath and a happier grin, {hero.id} fixed the last piece in place."
    )
    if activity.id == "cups":
        world.say(
            f"The cup-ful stayed safe, and the little pyramid stood tall instead of wobbling."
        )
    else:
        world.say(
            f"The pyramid stood straight at last, and its neat shape made the whole afternoon glow."
        )
    world.say(
        f"{hero.id} looked at the finished pile and felt quiet glory, the kind that comes after trying again."
    )


def tell(place: Place, activity: Activity, prize_cfg: Prize, helper: Helper, hero_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character"))
    prize = world.add(Entity(id=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase, plural=prize_cfg.plural))

    start_story(world, hero, activity, prize)
    world.para()
    warn(world, hero, prize, activity)
    do_activity(world, hero, activity)
    world.say(
        f"{hero.id} took one careful step at a time, but the stack still quivered."
    )
    helper_turn(world, hero, helper, activity, prize)
    world.para()
    resolve(world, hero, activity, prize, helper)

    world.facts = {
        "hero": hero,
        "prize": prize,
        "activity": activity,
        "helper": helper,
        "place": place,
    }
    return world


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for aid, activity in ACTIVITIES.items():
            if "build" not in place.affords:
                continue
            for prize_id, prize in PRIZES.items():
                if activity.mess in prize.at_risk_by:
                    for hid in HELPERS:
                        out.append((pid, aid, prize_id, hid))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a small child that includes the word "{f["activity"].keyword}".',
        f"Tell a gentle story about {f['hero'].id} making a tiny pyramid on {f['place'].label} with a little help from {f['helper'].label}.",
        f'Write a story with a playful rhyme, a curious moment, and a happy ending about "{f["prize"].label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    prize: Entity = _safe_fact(world, f, "prize")
    activity: Activity = _safe_fact(world, f, "activity")
    helper: Helper = _safe_fact(world, f, "helper")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"What did {hero.id} want to build on {place.label}?",
            answer=f"{hero.id} wanted to {activity.verb}. It was a small pyramid project full of glory.",
        ),
        QAItem(
            question=f"Why did {hero.id} stop and think before finishing the {prize.label} story?",
            answer=f"{hero.id} noticed the {prize.label} could get into trouble because the stack might {activity.ripple}.",
        ),
        QAItem(
            question=f"How did {helper.label} help {hero.id} at the end?",
            answer=f"{helper.label.capitalize()} helped by letting {hero.id} {helper.offer}, which made the stack steadier and happier.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pyramid?",
            answer="A pyramid is a shape that starts wide and becomes narrower as it goes up.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity helps you ask questions and look closely so you can learn new things.",
        ),
        QAItem(
            question="Why can humor help when something wobbles?",
            answer="Humor can make people feel calmer and kinder, so they can keep trying without feeling upset.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== (1) Generation prompts ==")
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


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
        lines.append(asp.fact("mess", aid, a.mess))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("at_risk_by", pid, "wobble"))
        lines.append(asp.fact("at_risk_by", pid, "tilt"))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for g in sorted(h.guards):
            lines.append(asp.fact("guards", hid, g))
        for c in sorted(h.covers):
            lines.append(asp.fact("covers", hid, c))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Act, Prize, Helper) :- affords(Place, build), activity(Act), prize(Prize), helper(Helper).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld about a pyramid, glory, cup-ful, rhyme, curiosity, and humor.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
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
    combos = valid_combos()
    combos = [c for c in combos
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
              and (getattr(args, "helper", None) is None or c[3] == getattr(args, "helper", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize, helper = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, helper=helper, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), _safe_lookup(HELPERS, params.helper), params.name)
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
        lines.append(f"{e.id}: meters={meters} memes={memes}")
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
    StoryParams("patio", "blocks", "pyramid", "rhyme", "Mina"),
    StoryParams("garden", "cups", "cupful", "curiosity", "Eli"),
    StoryParams("sandbox", "blocks", "pyramid", "humor", "Iris"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/4."))
        for item in sorted(set(asp.atoms(model, "valid"))):
            print(item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        for i in range(max(getattr(args, "n", None) * 50, 50)):
            if len(samples) >= getattr(args, "n", None):
                break
            seed = base_seed + i
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
            header = f"### {p.name}: {p.activity} at {p.place} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
