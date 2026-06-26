#!/usr/bin/env python3
"""
storyworlds/worlds/delicate_rhyme_slice_of_life.py
===================================================

A small slice-of-life story world about a child making a delicate rhyme.

Seed idea:
- A gentle child wants to share a tiny rhyme.
- The rhyme is delicate, so a noisy, hurried, or messy setting can spoil it.
- A kind helper suggests a quiet, careful way to finish and deliver it.

This world keeps the story grounded in ordinary objects and feelings:
paper, pencil, envelope, flowers, tea, and the calm effort of making something
pretty without rushing it.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    fragile: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    child: object | None = None
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


@dataclass
class Place:
    id: str
    label: str
    quiet: bool = True
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
    rush: str
    noise: str
    mess: str
    risk: set[str]
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
    fragile: bool = False
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
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    helps: set[str] = field(default_factory=set)
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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, tag: str) -> bool:
        return any(item.fragile and tag in item.meters for item in self.worn_items(actor))


SETTINGS = {
    "kitchen_table": Place("kitchen_table", "the kitchen table", quiet=True, affords={"rhyme", "tea", "cards"}),
    "sunroom": Place("sunroom", "the sunroom", quiet=True, affords={"rhyme", "flowers", "tea"}),
    "window_seat": Place("window_seat", "the window seat", quiet=True, affords={"rhyme", "tea", "reading"}),
    "garden_bench": Place("garden_bench", "the garden bench", quiet=True, affords={"rhyme", "flowers"}),
}

ACTIVITIES = {
    "rhyme": Activity(
        id="rhyme",
        verb="write a rhyme",
        gerund="writing a rhyme",
        rush="scribble too fast",
        noise="the scratch of a hurried pencil",
        mess="creased",
        risk={"paper", "ink"},
        keyword="rhyme",
        tags={"rhyme", "paper", "quiet"},
    ),
    "tea": Activity(
        id="tea",
        verb="sip tea",
        gerund="sipping tea",
        rush="carry the cup too quickly",
        noise="a small clink against the saucer",
        mess="spilled",
        risk={"cup", "napkin"},
        keyword="tea",
        tags={"tea", "quiet"},
    ),
    "flowers": Activity(
        id="flowers",
        verb="arrange flowers",
        gerund="arranging flowers",
        rush="toss the stems together",
        noise="a soft rustle of petals",
        mess="bruised",
        risk={"petal"},
        keyword="flowers",
        tags={"flowers", "gentle"},
    ),
    "cards": Activity(
        id="cards",
        verb="make a card",
        gerund="making a card",
        rush="fold the paper too quickly",
        noise="the flap of paper",
        mess="creased",
        risk={"paper"},
        keyword="card",
        tags={"card", "paper", "quiet"},
    ),
}

PRIZES = {
    "paper": Prize("paper", "a fresh sheet of cream paper", "paper"),
    "card": Prize("card", "a folded card with a blue ribbon", "card"),
    "letter": Prize("letter", "a little letter for Grandma", "letter"),
}

TOOLS = [
    Tool("pencil", "a sharpened pencil", prep="sharpen the pencil and sit near the lamp", tail="sat quietly and finished the lines", guards={"creased"}, helps={"rhyme", "cards"}),
    Tool("eraser", "a soft eraser", prep="keep a soft eraser nearby", tail="smiled and fixed the tiny mistakes", guards={"creased"}, helps={"rhyme", "cards"}),
    Tool("tray", "a small tray", prep="set the cup on a small tray", tail="walked the tray slowly to the table", guards={"spilled"}, helps={"tea"}),
    Tool("vase", "a little vase", prep="place the stems in a little vase", tail="set the flowers by the window", guards={"bruised"}, helps={"flowers"}),
]

NAMES = ["Mina", "Lena", "Iris", "Nora", "Ada", "Maya", "Tess", "Wren"]
PARENT_NAMES = ["Mom", "Dad", "Aunt Jo", "Grandma"]
TRAITS = ["gentle", "quiet", "patient", "careful", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    if activity.id == "rhyme":
        return prize.label in {"paper", "card", "letter"}
    if activity.id == "tea":
        return prize.label in {"paper", "card", "letter"}
    if activity.id == "flowers":
        return prize.label in {"paper", "card", "letter"}
    if activity.id == "cards":
        return prize.label in {"paper", "letter"}
    return False


def select_tool(activity: Activity, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS:
        if activity.id in tool.helps and prize.label in {"paper", "card", "letter"}:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in SETTINGS.items():
        for act_id in place.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_tool(act, prize):
                    combos.append((place_id, act_id, prize_id))
    return combos


def calm_detail(place: Place, activity: Activity) -> str:
    if place.id == "sunroom":
        return "The sunroom was warm and bright, with dust motes floating like tiny notes."
    if place.id == "window_seat":
        return "The window seat was snug, and the rain outside sounded like a hush."
    if place.id == "garden_bench":
        return "The garden bench was cool and still, and the leaves barely moved."
    return "The kitchen table was neat, with a lamp glowing over the paper."


def introduce(world: World, child: Entity) -> None:
    world.say(f"{child.id} was a little {next(t for t in [child.type, *child.meters.keys()] if t)} who liked making small, careful things.")
    world.say(f"{child.pronoun().capitalize()} loved the way a {world.facts['activity'].keyword} could feel soft and special when nobody hurried.")


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    act = sim.get(actor.id)
    act.meters[activity.mess] = act.meters.get(activity.mess, 0) + 1
    return {"soiled": prize_at_risk(activity, world.facts["prize"])}


def tell(place: Place, activity: Activity, prize_cfg: Prize, name: str = "Mina", gender: str = "girl", helper: str = "Mom", trait: str = "gentle") -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={"joy": 0.0, "worry": 0.0, "calm": 0.0}))
    adult = world.add(Entity(id=helper, kind="character", type="mother" if helper == "Mom" else "father"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=child.id, caretaker=adult.id, fragile=prize_cfg.fragile, plural=prize_cfg.plural))
    world.facts.update(child=child, adult=adult, prize=prize, activity=activity, place=place, trait=trait)

    world.say(f"{child.id} sat at {place.label} with a {trait} smile.")
    world.say(f"{child.pronoun().capitalize()} wanted to {activity.verb}, because {activity.keyword} felt like a tiny, delicate song.")
    world.say(f"{helper} had just brought out {prize.phrase} for the afternoon.")

    world.para()
    world.say(calm_detail(place, activity))
    world.say(f"{child.id} reached for the paper, but {helper} paused and looked at the page.")
    world.say(f'"If you {activity.rush}, the {activity.keyword} will lose its soft shape," {helper} said.')

    world.para()
    world.say(f"{child.id} frowned for a moment, then listened.")
    world.say(f"{child.id} liked the warning, because {activity.noise} would have spoiled the quiet mood.")
    tool = select_tool(activity, prize)
    if tool:
        world.say(f"{helper} suggested they {tool.prep}.")
        world.say(f"{child.id} nodded, took a careful breath, and began again.")
        world.say(f"Before long, the two of them {tool.tail}.")
        world.say(f"The little {activity.keyword} stayed neat on {prize.label}, and {child.id} could read it aloud without rushing.")
        child.memes["joy"] += 1
        child.memes["calm"] += 2
    else:
        pass

    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle slice-of-life story about {f["child"].id} making a delicate {f["activity"].keyword} at {f["place"].label}.',
        f"Tell a calm story where {f['child'].id} wants to {f['activity'].verb} but learns to do it carefully with {f['adult'].id}.",
        f'Write a short childhood story that includes the word "{f["activity"].keyword}" and ends with a quiet, happy finish.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, adult, prize, activity = f["child"], f["adult"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {child.id} want to do at {f['place'].label}?",
            answer=f"{child.id} wanted to {activity.verb}, because {activity.keyword} felt delicate and pretty.",
        ),
        QAItem(
            question=f"Why did {adult.id} tell {child.id} not to rush?",
            answer=f"{adult.id} wanted the {activity.keyword} to stay neat, because rushing could have spoiled the soft, careful feeling.",
        ),
        QAItem(
            question=f"What stayed safe in the end?",
            answer=f"{prize.phrase} stayed safe, and the little {activity.keyword} was finished calmly.",
        ),
        QAItem(
            question=f"How did {child.id} feel after listening?",
            answer=f"{child.id} felt calm and happy, because the careful way worked better than hurrying.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does delicate mean?",
            answer="Delicate means something is soft, careful, or easy to spoil, so it should be handled gently.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a short bit of language where words sound pleasing together, like a tiny song.",
        ),
        QAItem(
            question="Why can paper wrinkle?",
            answer="Paper can wrinkle when it is folded, pressed, or handled too roughly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen_table", activity="rhyme", prize="paper", name="Mina", gender="girl", helper="Mom", trait="gentle"),
    StoryParams(place="window_seat", activity="cards", prize="letter", name="Iris", gender="girl", helper="Grandma", trait="careful"),
    StoryParams(place="sunroom", activity="flowers", prize="card", name="Nora", gender="girl", helper="Aunt Jo", trait="thoughtful"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} does not realistically endanger {prize.phrase} in a way the world can fix.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small slice-of-life story world about delicate rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=PARENT_NAMES)
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
    if getattr(args, "place", None) and getattr(args, "activity", None) and getattr(args, "prize", None):
        act, prize = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(act, prize) and select_tool(act, prize)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place_id, act_id, prize_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(PARENT_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place_id, activity=act_id, prize=prize_id, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.helper, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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
place(P) :- setting(P).
activity(A) :- activity(A).
prize(P) :- prize(P).

risk(A,P) :- keyword(A,K), prize_name(P,K).
valid(P,A,R) :- place(P), activity(A), prize(R), risk(A,R), has_tool(A,R).
has_tool(rhyme,paper) :- true.
has_tool(cards,paper) :- true.
has_tool(cards,letter) :- true.
has_tool(flowers,card) :- true.
has_tool(flowers,paper) :- true.

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if place.quiet:
            lines.append(asp.fact("quiet", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("keyword", aid, act.keyword))
        for t in sorted(act.tags):
            lines.append(asp.fact("tag", aid, t))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize_name", pid, prize.label))
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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
