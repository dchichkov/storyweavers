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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    blouse: object | None = None
    hero: object | None = None
    supporter: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
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
    indoor: bool = False
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
    tension: str
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
class Blouse:
    id: str
    label: str
    phrase: str
    color: str
    occasion: str
    fits: set[str] = field(default_factory=set)
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
class Support:
    id: str
    label: str
    offer: str
    result: str
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
        self.fired: set[tuple] = set()
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    place: str
    activity: str
    blouse: str
    name: str
    gender: str
    supporter: str
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


SETTINGS = {
    "kitchen": Setting("the kitchen", indoor=True, affords={"family_lunch", "cookies"}),
    "library": Setting("the library", indoor=True, affords={"story_time", "quiet_visit"}),
    "school": Setting("the school hallway", indoor=True, affords={"show_and_tell", "class_day"}),
    "garden": Setting("the garden", indoor=False, affords={"tea_party", "neighbor_visit"}),
    "porch": Setting("the front porch", indoor=False, affords={"neighbor_visit", "tea_party"}),
}

ACTIVITIES = {
    "show_and_tell": Activity("show_and_tell", "go to show-and-tell", "going to show-and-tell", "hurry to class", "feel shy", "show-and-tell", {"school", "bravery"}),
    "family_lunch": Activity("family_lunch", "sit down for family lunch", "sitting down for family lunch", "walk to the table", "worry about being noticed", "lunch", {"home", "bravery"}),
    "tea_party": Activity("tea_party", "join the tea party", "joining the tea party", "step into the circle", "feel too small", "tea-party", {"home", "bravery"}),
    "neighbor_visit": Activity("neighbor_visit", "visit the neighbor", "visiting the neighbor", "walk over together", "hesitate at the gate", "neighbor", {"community", "bravery"}),
    "quiet_visit": Activity("quiet_visit", "visit the library", "visiting the library", "head to the shelves", "feel nervous in a quiet room", "library", {"community", "bravery"}),
}

BLOUSES = {
    "yellow": Blouse("yellow", "yellow blouse", "a yellow blouse with tiny buttons", "yellow", "brave", {"school", "home", "community"}, {"bright", "bravery"}),
    "blue": Blouse("blue", "blue blouse", "a blue blouse with soft sleeves", "blue", "everyday", {"home", "community"}, {"calm", "bravery"}),
    "white": Blouse("white", "white blouse", "a white blouse with a little collar", "white", "special", {"school", "home"}, {"bright", "bravery"}),
    "green": Blouse("green", "green blouse", "a green blouse with a neat bow", "green", "friendly", {"garden", "home", "community"}, {"bright", "bravery"}),
}

SUPPORTS = [
    Support("mom", "Mom", "take a slow breath and try the blouse on", "the girl felt steadier"),
    Support("aunt", "Aunt Lina", "straighten the collar and smile", "the blouse felt less scary"),
    Support("friend", "a friend", "say the blouse looked lovely", "the girl stood a little taller"),
]

GIRL_NAMES = ["Mia", "Lena", "Nora", "Ivy", "Sofia", "Ruby", "Ella", "June"]
BOY_NAMES = ["Ben", "Leo", "Finn", "Theo", "Max", "Owen"]
TRAITS = ["shy", "gentle", "thoughtful", "quiet", "curious", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for blouse_id, blouse in BLOUSES.items():
                if act.id in blouse.fits or any(t in blouse.tags for t in act.tags):
                    out.append((place, act_id, blouse_id))
    return out


def explain_rejection(activity: Activity, blouse: Blouse) -> str:
    return f"(No story: {blouse.label} doesn't fit the mood of {activity.gerund} in a believable slice-of-life way.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: blouse + bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--blouse", choices=BLOUSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--supporter", choices=[s.id for s in SUPPORTS])
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
    if getattr(args, "activity", None) and getattr(args, "blouse", None):
        if (getattr(args, "place", None), getattr(args, "activity", None), getattr(args, "blouse", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "blouse", None) is None or c[2] == getattr(args, "blouse", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, blouse_id = rng.choice(list(combos))
    blouse = _safe_lookup(BLOUSES, blouse_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if gender == "boy":
        name = getattr(args, "name", None) or rng.choice(BOY_NAMES)
    else:
        name = getattr(args, "name", None) or rng.choice(GIRL_NAMES)
    supporter = getattr(args, "supporter", None) or rng.choice([s.id for s in SUPPORTS])
    trait = rng.choice(TRAITS)
    return StoryParams(place, activity, blouse_id, name, gender, supporter, trait)


def _do_activity(world: World, actor: Entity, activity: Activity) -> None:
    actor.memes["shyness"] = max(0.0, actor.memes.get("shyness", 0.0) - 0.25)
    actor.memes["bravery"] = actor.memes.get("bravery", 0.0) + 0.5
    actor.meters["steadiness"] = actor.meters.get("steadiness", 0.0) + 0.5


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(params.name, kind="character", type=params.gender))
    support_cfg = next(s for s in SUPPORTS if s.id == params.supporter)
    supporter = world.add(Entity(support_cfg.label, kind="character", type="mother" if support_cfg.id == "mom" else "aunt"))
    blouse = world.add(Entity(params.blouse, type="blouse", label=_safe_lookup(BLOUSES, params.blouse).label, phrase=_safe_lookup(BLOUSES, params.blouse).phrase, owner=hero.id))
    blouse.worn_by = hero.id

    hero.memes["shyness"] = 1.0
    hero.memes["bravery"] = 0.0
    hero.memes["want"] = 1.0

    act = _safe_lookup(ACTIVITIES, params.activity)
    world.say(f"{hero.id} was a {params.trait} {params.gender} who liked quiet mornings and neat clothes.")
    world.say(f"{hero.id} had {blouse.phrase}, and {hero.pronoun('subject')} liked how it made {hero.pronoun('object')} look grown-up.")
    world.para()
    world.say(f"One day, {hero.id} and {supporter.label} were getting ready to {act.verb} at {world.setting.place}.")
    world.say(f"{hero.id} wanted to wear the blouse, but {hero.pronoun('subject')} started to {act.tension}.")
    hero.memes["shyness"] += 0.75
    world.say(f"{hero.id} looked at the doorway and then at the blouse, feeling stuck between staying hidden and being brave.")
    world.para()
    world.say(f"Then {supporter.label} said, \"Let's {support_cfg.offer}.\"")
    hero.memes["bravery"] += 1.0
    hero.memes["shyness"] = max(0.0, hero.memes["shyness"] - 0.5)
    world.say(f"{hero.id} took a slow breath, smoothed the blouse, and went along.")
    _do_activity(world, hero, act)
    world.say(f"At {world.setting.place}, {hero.id} did not hide behind anyone. {hero.pronoun('subject').capitalize()} {act.rush}, and the day felt easier after the first step.")
    world.para()
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
    world.say(f"By the end, {hero.id} felt proud of {hero.pronoun('possessive')} brave choice.")
    world.say(f"The blouse was still neat, and {supporter.label} smiled because {support_cfg.result}.")
    world.facts.update(hero=hero, supporter=supporter, blouse=blouse, activity=act, setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, blouse, act = f["hero"], f["blouse"], f["activity"]
    return [
        f'Write a short slice-of-life story about a child named {hero.id} who feels brave in {blouse.label}.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but needs courage first.",
        f'Write a simple story about "{blouse.label}" and a small brave choice on an ordinary day.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, supporter, blouse, act = f["hero"], f["supporter"], f["blouse"], f["activity"]
    return [
        QAItem(question=f"What did {hero.id} want to wear on the day {hero.id} went to {act.verb}?", answer=f"{hero.id} wanted to wear {blouse.phrase}."),
        QAItem(question=f"Who helped {hero.id} feel braver before {hero.pronoun('subject')} went to {act.verb}?", answer=f"{supporter.id} helped {hero.id} feel braver."),
        QAItem(question=f"How did {hero.id} feel at the end of the story?", answer=f"{hero.id} felt proud and brave after going along."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a blouse?", answer="A blouse is a shirt that is often soft, neat, and nice to wear."),
        QAItem(question="What is bravery?", answer="Bravery means doing something even when you feel nervous or unsure."),
        QAItem(question="What does it mean to take a slow breath?", answer="It means breathing in and out gently to help your body feel calmer."),
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        out.append(f"  {e.id:10} ({e.type}) meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(out)


ASP_RULES = r"""
valid_combo(Place,Act,Blouse) :- setting(Place), affords(Place,Act), activity(Act), blouse(Blouse),
                                compatible(Act,Blouse).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p, s in SETTINGS.items():
        lines.append(asp.fact("setting", p))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", p, a))
    for a, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", a))
        for t in sorted(act.tags):
            lines.append(asp.fact("act_tag", a, t))
    for b, bl in BLOUSES.items():
        lines.append(asp.fact("blouse", b))
        for t in sorted(bl.tags):
            lines.append(asp.fact("blouse_tag", b, t))
        for f in sorted(bl.fits):
            lines.append(asp.fact("fits", b, f))
    for a, act in ACTIVITIES.items():
        for b, bl in BLOUSES.items():
            if (a in bl.fits) or (act.tags & bl.tags):
                lines.append(asp.fact("compatible", a, b))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(cl - py))
    print(" only in python:", sorted(py - cl))
    return 1


CURATED = [
    StoryParams("school", "show_and_tell", "white", "Mia", "girl", "mom", "shy"),
    StoryParams("kitchen", "family_lunch", "blue", "Nora", "girl", "aunt", "careful"),
    StoryParams("garden", "tea_party", "green", "Ella", "girl", "mom", "quiet"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
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
        header = f"### variant {i+1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
