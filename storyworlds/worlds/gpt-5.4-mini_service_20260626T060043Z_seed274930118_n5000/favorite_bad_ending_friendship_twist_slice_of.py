#!/usr/bin/env python3
"""
storyworlds/worlds/favorite_bad_ending_friendship_twist_slice_of.py
====================================================================

A small slice-of-life story world about a favorite thing, a friendship,
and a twist that ends on a sad, quiet note.

The premise is simple: a child and a friend share an ordinary day in a gentle
place. The child has a favorite object that matters a lot. A small problem
appears, the friend helps in a friendly way, and then the twist changes what
the day means. The ending is intentionally bittersweet or bad-leaning: the
favorite thing does not come back exactly as it was, but the story still ends
with a clear image of what changed.

This world is designed to be:

* child-facing and concrete
* state-driven rather than template-swapped
* compact enough to verify by rule parity
* close to slice-of-life, with friendship and a twist
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

    favorite: object | None = None
    friend: object | None = None
    hero: object | None = None
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
        return self.label or self.type
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
    risk: str
    weather: str
    twist: str
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
class Favorite:
    label: str
    phrase: str
    type: str
    fragile: bool = False
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
class FriendAction:
    id: str
    offer: str
    effect: str
    gentle_fix: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = ""

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.weather = self.weather
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    favorite: str
    friend_action: str
    name: str
    gender: str
    friend_name: str
    friend_gender: str
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
    "park": Setting(place="the park", indoor=False, affords={"kites", "snack", "cards"}),
    "bench": Setting(place="the little park bench", indoor=False, affords={"snack", "cards"}),
    "library": Setting(place="the library corner", indoor=True, affords={"reading", "cards"}),
    "kitchen": Setting(place="the kitchen table", indoor=True, affords={"snack", "cards"}),
}

ACTIVITIES = {
    "kites": Activity(
        id="kites",
        verb="fly the kite",
        gerund="flying the kite",
        risk="wind and sudden tugging",
        weather="breezy",
        twist="The string could snap if they ran too fast.",
        tags={"wind", "string"},
    ),
    "snack": Activity(
        id="snack",
        verb="share a snack",
        gerund="sharing a snack",
        risk="crumbs and sticky fingers",
        weather="",
        twist="One tiny bite could fall into the wrong lap.",
        tags={"food", "sticky"},
    ),
    "cards": Activity(
        id="cards",
        verb="play cards",
        gerund="playing cards",
        risk="bent corners and spilled drinks",
        weather="",
        twist="A card could slip under the table and disappear.",
        tags={"paper", "game"},
    ),
    "reading": Activity(
        id="reading",
        verb="read a book",
        gerund="reading together",
        risk="creased pages and a torn cover",
        weather="",
        twist="A page marker might fall out and show a secret note.",
        tags={"book", "paper"},
    ),
}

FAVORITES = {
    "scarf": Favorite(
        label="scarf",
        phrase="a soft blue scarf with one bright stripe",
        type="scarf",
        fragile=False,
    ),
    "notebook": Favorite(
        label="notebook",
        phrase="a small notebook with a green cover",
        type="notebook",
        fragile=True,
    ),
    "mug": Favorite(
        label="mug",
        phrase="a favorite red mug with a chipped handle",
        type="mug",
        fragile=True,
    ),
    "kite": Favorite(
        label="kite",
        phrase="a striped paper kite",
        type="kite",
        fragile=True,
    ),
    "card": Favorite(
        label="card",
        phrase="a lucky picture card",
        type="card",
        fragile=True,
        plural=False,
    ),
}

FRIEND_ACTIONS = {
    "share": FriendAction(
        id="share",
        offer="share the favorite thing carefully",
        effect="their hands moved slow and gentle",
        gentle_fix="keep it near the edge of the table",
        tags={"care", "sharing"},
    ),
    "protect": FriendAction(
        id="protect",
        offer="hold it with both hands",
        effect="they tried to keep it safe",
        gentle_fix="set it down on a napkin",
        tags={"care", "holding"},
    ),
    "help": FriendAction(
        id="help",
        offer="help with the tricky part",
        effect="the friend leaned in to help",
        gentle_fix="slow down and do the hard part together",
        tags={"help", "together"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe", "Ella", "June", "Ruby"]
BOY_NAMES = ["Leo", "Finn", "Max", "Theo", "Owen", "Ben", "Noah", "Eli"]
TRAITS = ["quiet", "gentle", "curious", "cheerful", "careful", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for fav_id, fav in FAVORITES.items():
                if fav.fragile and act_id in {"kites", "reading", "cards"}:
                    for friend_id in FRIEND_ACTIONS:
                        combos.append((place, act_id, fav_id, friend_id))
    return combos


def item_at_risk(activity: Activity, favorite: Favorite) -> bool:
    return favorite.fragile or activity.id in {"kites", "reading", "cards", "snack"}


def select_friend_action(activity: Activity, favorite: Favorite) -> Optional[FriendAction]:
    for act in FRIEND_ACTIONS.values():
        if activity.id == "snack" and act.id in {"share", "protect"}:
            return act
        if activity.id in {"cards", "reading"} and act.id in {"help", "protect"}:
            return act
        if activity.id == "kites" and act.id in {"help", "protect"}:
            return act
    return None


def predict_loss(world: World, hero: Entity, activity: Activity, favorite: Entity) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["worry"] += 1
    sim.get(favorite.id).meters["risk"] += 1
    return favorite.meters.get("damaged", 0) >= THRESHOLD or activity.id in {"reading", "cards", "kites"}


def _do_activity(world: World, hero: Entity, activity: Activity, favorite: Entity, narrate: bool = True) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    if activity.id == "snack":
        favorite.meters["sticky"] = favorite.meters.get("sticky", 0) + 1
    elif activity.id == "cards":
        favorite.meters["bent"] = favorite.meters.get("bent", 0) + 1
    elif activity.id == "reading":
        favorite.meters["creased"] = favorite.meters.get("creased", 0) + 1
    elif activity.id == "kites":
        favorite.meters["tugged"] = favorite.meters.get("tugged", 0) + 1
    if narrate:
        world.say(f"{hero.id} began {activity.gerund} with a calm, ordinary smile.")


def introduce(world: World, hero: Entity, friend: Entity, favorite: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} was a little {hero.pronoun('possessive')} of the day, "
        f"and {friend.id} was the kind of friend who noticed small things."
    )
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {favorite.label} because it was "
        f"{favorite.phrase}."
    )
    world.say(
        f"On this day, they wanted to {activity.verb}, and that seemed like a simple plan."
    )


def warning(world: World, hero: Entity, friend: Entity, favorite: Entity, activity: Activity) -> bool:
    if not predict_loss(world, hero, activity, favorite):
        return False
    world.facts["twist"] = activity.twist
    world.say(
        f"{friend.id} looked at the {favorite.label} and said, "
        f"\"Careful. {activity.twist}\""
    )
    return True


def twist_turn(world: World, hero: Entity, friend: Entity, favorite: Entity, activity: Activity) -> None:
    hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
    if activity.id == "reading":
        world.say(
            f"Then the twist arrived: a folded note slipped from the book, and it was not "
            f"part of the game at all."
        )
    elif activity.id == "cards":
        world.say(
            f"Then the twist arrived: the missing card was not under the table, because "
            f"{friend.id} had quietly tucked it into a pocket for safekeeping."
        )
    elif activity.id == "kites":
        world.say(
            f"Then the twist arrived: the kite string did not break first; instead, the wind "
            f"carried it toward the far fence."
        )
    else:
        world.say(
            f"Then the twist arrived: one sticky bite landed on the {favorite.label}, and the day "
            f"changed its shape."
        )


def bad_ending(world: World, hero: Entity, friend: Entity, favorite: Entity, activity: Activity) -> None:
    hero.memes["sadness"] = hero.memes.get("sadness", 0) + 1
    favorite.meters["damaged"] = favorite.meters.get("damaged", 0) + 1
    world.say(
        f"{friend.id} tried to help, but the {favorite.label} still ended up a little ruined."
    )
    world.say(
        f"{hero.id} held it close anyway, and the room or bench felt suddenly quieter."
    )
    world.say(
        f"In the end, {hero.id} and {friend.id} stayed friends, but the favorite thing was not the same."
    )


def tell(setting: Setting, activity: Activity, favorite_cfg: Favorite,
         hero_name: str, hero_type: str, friend_name: str, friend_type: str) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))
    favorite = world.add(Entity(
        id="favorite",
        type=favorite_cfg.type,
        label=favorite_cfg.label,
        phrase=favorite_cfg.phrase,
        owner=hero.id,
        caretaker=friend.id,
        plural=favorite_cfg.plural,
    ))

    hero.memes["fondness"] = 1
    friend.memes["kindness"] = 1
    favorite.worn_by = hero.id

    introduce(world, hero, friend, favorite, activity)
    world.para()
    _do_activity(world, hero, activity, favorite, narrate=True)
    warning(world, hero, friend, favorite, activity)
    world.para()
    twist_turn(world, hero, friend, favorite, activity)
    friend_action = select_friend_action(activity, favorite_cfg)
    if friend_action:
        world.say(
            f"{friend.id} {friend_action.offer}, and for a moment that made the day feel safer."
        )
    bad_ending(world, hero, friend, favorite, activity)

    world.facts.update(
        hero=hero,
        friend=friend,
        favorite=favorite,
        activity=activity,
        setting=setting,
        friend_action=friend_action,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, activity, favorite = f["hero"], f["friend"], f["activity"], f["favorite"]
    return [
        f'Write a short slice-of-life story about a child named {hero.id}, a friend named {friend.id}, and a favorite {favorite.label}.',
        f"Tell a gentle story where {hero.id} and {friend.id} try to {activity.verb} and something small goes wrong.",
        f'Write a story with a friendship twist that includes the word "favorite" and ends quietly, not happily.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, favorite, activity = f["hero"], f["friend"], f["favorite"], f["activity"]
    return [
        QAItem(
            question=f"What was {hero.id}'s favorite thing?",
            answer=f"{hero.id}'s favorite thing was {favorite.phrase}.",
        ),
        QAItem(
            question=f"Who was {hero.id} spending time with while {hero.id} tried to {activity.verb}?",
            answer=f"{hero.id} was with {friend.id}, a kind friend who tried to help.",
        ),
        QAItem(
            question=f"What small problem showed up during the day?",
            answer=f"The problem was that {activity.twist.lower()}",
        ),
        QAItem(
            question=f"How did the story end for the favorite thing?",
            answer=f"It ended a little badly, because the favorite {favorite.label} got damaged and was not the same afterward.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when something is a favorite?",
            answer="A favorite is something a person likes more than many other things, so it feels special to them.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, spend time together, and try to help each other.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes what the reader expects to happen next.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="park",
        activity="cards",
        favorite="card",
        friend_action="protect",
        name="Mia",
        gender="girl",
        friend_name="Nora",
        friend_gender="girl",
    ),
    StoryParams(
        place="library",
        activity="reading",
        favorite="notebook",
        friend_action="help",
        name="Leo",
        gender="boy",
        friend_name="Eli",
        friend_gender="boy",
    ),
    StoryParams(
        place="kitchen",
        activity="snack",
        favorite="mug",
        friend_action="share",
        name="Ava",
        gender="girl",
        friend_name="June",
        friend_gender="girl",
    ),
    StoryParams(
        place="park",
        activity="kites",
        favorite="kite",
        friend_action="help",
        name="Noah",
        gender="boy",
        friend_name="Max",
        friend_gender="boy",
    ),
]


ASP_RULES = r"""
risk(A,F) :- activity(A), favorite(F), fragile(F).
compatible(P,A,F,FA) :- setting(P), affords(P,A), risk(A,F), friend_action(FA).
valid_story(P,A,F,FA) :- compatible(P,A,F,FA).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, activity in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in sorted(activity.tags):
            lines.append(asp.fact("tag", aid, t))
    for fid, fav in FAVORITES.items():
        lines.append(asp.fact("favorite", fid))
        if fav.fragile:
            lines.append(asp.fact("fragile", fid))
    for faid in FRIEND_ACTIONS:
        lines.append(asp.fact("friend_action", faid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_story_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for fav_id, fav in FAVORITES.items():
                if fav.fragile:
                    for faid in FRIEND_ACTIONS:
                        combos.append((place, act_id, fav_id, faid))
    return combos


def asp_verify() -> int:
    py = set(valid_story_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_story_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world with a favorite thing, friendship, and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--favorite", choices=FAVORITES)
    ap.add_argument("--friend-action", choices=FRIEND_ACTIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    combos = valid_story_combos()
    combos = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
        and (getattr(args, "favorite", None) is None or c[2] == getattr(args, "favorite", None))
        and (getattr(args, "friend_action", None) is None or c[3] == getattr(args, "friend_action", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, favorite, friend_action = rng.choice(list(combos))
    fav = _safe_lookup(FAVORITES, favorite)
    gender = getattr(args, "gender", None) or rng.choice(sorted(fav.genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_gender = getattr(args, "friend_gender", None) or rng.choice(["girl", "boy"])
    friend_name = getattr(args, "friend_name", None) or rng.choice(GIRL_NAMES if friend_gender == "girl" else BOY_NAMES)
    return StoryParams(
        place=place,
        activity=activity,
        favorite=favorite,
        friend_action=friend_action,
        name=name,
        gender=gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(FAVORITES, params.favorite),
        params.name,
        params.gender,
        params.friend_name,
        params.friend_gender,
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
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for place, act, fav, fa in combos:
            print(f"  {place:8} {act:8} {fav:10} {fa}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (favorite: {p.favorite})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
