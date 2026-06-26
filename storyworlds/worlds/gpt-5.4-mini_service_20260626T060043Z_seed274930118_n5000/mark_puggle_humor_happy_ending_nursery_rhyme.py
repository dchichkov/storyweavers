#!/usr/bin/env python3
"""
storyworlds/worlds/mark_puggle_humor_happy_ending_nursery_rhyme.py
===================================================================

A tiny story world for a nursery-rhyme style tale about Mark and a puggle:
a playful little dog, a bit of comedy, a small tangle, and a happy ending.

The simulated premise:
- Mark loves rhyme, games, and gentle jokes.
- His puggle loves to bounce, snuffle, and steal attention.
- A small outing can become funny trouble when the puggle's antics disturb
  something Mark cares about.
- A kind fix restores order, with laughter at the end.

The world is state-driven:
- physical meters track location, dirt, bells, treats, and mess
- emotional memes track joy, worry, mischief, and relief

The generated stories stay close to a nursery-rhyme cadence and avoid
internal scaffolding in child-facing text.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    mark: object | None = None
    prize: object | None = None
    puggle: object | None = None
    def __post_init__(self) -> None:
        for k in ["dirt", "sparkle", "treat", "bell", "noise", "mud"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "mischief", "love", "relief", "humor"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    indoors: bool
    affords: set[str]
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
    mess: str
    soil: str
    keyword: str
    tags: set[str]
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
    genders: set[str] = field(default_factory=lambda: {"boy", "girl"})
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
class Comfort:
    id: str
    label: str
    covers: set[str]
    helps: set[str]
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
        self.lines: list[str] = []
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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "garden": Setting("the garden", False, {"skip", "sniff"}),
    "yard": Setting("the yard", False, {"skip", "sniff"}),
    "porch": Setting("the porch", False, {"ding", "rhyme"}),
    "kitchen": Setting("the kitchen", True, {"kitchen-song"}),
}

ACTIVITIES = {
    "skip": Activity(
        id="skip",
        verb="skip in a circle",
        gerund="skipping in circles",
        rush="skip faster and faster",
        mess="mud",
        soil="muddy",
        keyword="skip",
        tags={"humor", "mud"},
    ),
    "sniff": Activity(
        id="sniff",
        verb="sniff for crumbs",
        gerund="sniffing for crumbs",
        rush="snuffle at the table leg",
        mess="crumbs",
        soil="crumb-specked",
        keyword="sniff",
        tags={"humor", "crumbs"},
    ),
    "ding": Activity(
        id="ding",
        verb="ring a little bell",
        gerund="dinging the bell",
        rush="tap the bell again and again",
        mess="noise",
        soil="ding-dented",
        keyword="ding",
        tags={"humor", "noise"},
    ),
    "rhyme": Activity(
        id="rhyme",
        verb="say a nursery rhyme",
        gerund="saying nursery rhymes",
        rush="chant the rhyme aloud",
        mess="noise",
        soil="loud",
        keyword="rhyme",
        tags={"humor", "rhyme"},
    ),
    "kitchen-song": Activity(
        id="kitchen-song",
        verb="sing a kitchen song",
        gerund="singing a kitchen song",
        rush="sing louder and louder",
        mess="noise",
        soil="ringing",
        keyword="song",
        tags={"humor", "song"},
    ),
}

PRIZES = {
    "muffin": Prize("muffin", "muffin", "a warm little muffin", "hands"),
    "cap": Prize("cap", "cap", "a bright little cap", "head"),
    "book": Prize("book", "book", "a storybook with shiny pages", "hands"),
    "spoon": Prize("spoon", "spoon", "a tin spoon for tapping", "hands"),
}

COMFORTS = [
    Comfort(
        id="apron",
        label="an apron",
        covers={"hands", "torso"},
        helps={"mud", "crumbs"},
        prep="put on an apron first",
        tail="went back inside for the apron",
    ),
    Comfort(
        id="cap",
        label="a soft cap",
        covers={"head"},
        helps={"noise"},
        prep="wear a soft cap and then rhyme again",
        tail="found the soft cap and came back smiling",
    ),
    Comfort(
        id="mitts",
        label="little mitts",
        covers={"hands"},
        helps={"mud", "crumbs"},
        prep="slip on little mitts before the game",
        tail="patted on the little mitts and returned to play",
        plural=True,
    ),
]

NAMES = ["Mark"]
PUGGLE_NAMES = ["Puggle"]
TRAITS = ["cheery", "bouncy", "spry", "jolly"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str = "Mark"
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


def reasonableness_gate(activity: Activity, prize: Prize) -> bool:
    if activity.id in {"skip", "sniff"} and prize.region != "hands":
        return False
    if activity.id in {"ding", "rhyme", "kitchen-song"} and prize.region not in {"head", "hands"}:
        return False
    return True


def select_comfort(activity: Activity, prize: Prize) -> Optional[Comfort]:
    for c in COMFORTS:
        if activity.mess in c.helps and prize.region in c.covers:
            return c
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} would not honestly trouble the {prize.label}. "
        f"Try a prize on the {prize.region} or a different activity.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mark and a puggle in a nursery-rhyme world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", default="Mark")
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
    combos = [
        (p, a, pr)
        for p, setting in SETTINGS.items()
        for a in setting.affords
        for pr in PRIZES
        if reasonableness_gate(_safe_lookup(ACTIVITIES, a), _safe_lookup(PRIZES, pr))
    ]
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        if not reasonableness_gate(_safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    return StoryParams(place=place, activity=activity, prize=prize, name=getattr(args, "name", None))


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.memes["joy"] += 1
    if activity.mess == "mud":
        actor.meters["mud"] += 1
    elif activity.mess == "crumbs":
        actor.meters["dirt"] += 1
    else:
        actor.meters["noise"] += 1
    if narrate:
        world.say(f"{actor.id} loved {activity.gerund}.")


def predict_damage(world: World, actor: Entity, activity: Activity, prize: Entity) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    if prize.region == "hands" and activity.mess in {"mud", "crumbs"}:
        ruined = True
    elif prize.region == "head" and activity.mess == "noise":
        ruined = True
    else:
        ruined = False
    return {"ruined": ruined}


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str) -> World:
    world = World(setting)
    mark = world.add(Entity(id=name, kind="character", type="boy"))
    puggle = world.add(Entity(id="puggle", kind="character", type="dog", label="the puggle"))
    prize = world.add(Entity(id="prize", type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase, caretaker=mark.id))
    world.add(Entity(id="toy", type="thing", label="a tiny toy", caretaker=mark.id))

    mark.memes["love"] += 1
    puggle.memes["mischief"] += 1
    world.say(f"Mark had a puggle, and the puggle was merry and small.")
    world.say(f"Mark kept {prize.phrase} near, because it was dear.")
    world.para()
    world.say(f"One day at {setting.place}, Mark began to {activity.verb}, as happy as a lark.")
    world.say(f"The puggle joined in with a wiggle and a wiggle, a wobble and a giggle.")
    world.say(f"That made the day feel like a rhyme, a jingle-jangle nursery time.")

    world.para()
    _do_activity(world, puggle, activity, narrate=False)
    pred = predict_damage(world, puggle, activity, prize)
    if pred["ruined"]:
        prize.memes["worry"] += 1
        mark.memes["worry"] += 1
        world.say(f"But oh dear me, the {prize.label} was in the way.")
        if activity.mess == "mud":
            world.say(f"The puggle's paws went pat-a-pat, and the {prize.label} got muddy on the mat.")
        elif activity.mess == "crumbs":
            world.say(f"The puggle nosed the crumbs and gave the {prize.label} a crumbly humdrum.")
        else:
            world.say(f"The puggle's ding-ding-ding made the {prize.label} ring and ring.")
        comfort = select_comfort(activity, prize)
        if comfort:
            world.say(f"Then Mark laughed a tiny laugh and said, \"Let's use {comfort.label} instead.\"")
            world.say(f"So they {comfort.tail}, and the puggle trotted back, snug and settled.")
            mark.memes["relief"] += 1
            mark.memes["joy"] += 1
            prize.memes["worry"] = 0
            prize.meters["dirt"] = 0
            prize.meters["noise"] = 0
            world.para()
            world.say(
                f"Mark and the puggle skipped on in peace, and the little trouble turned to fun and ease."
            )
            world.say(
                f"The day ended bright, with the {prize.label} safe and clean, and the puggle looking very pleased."
            )
        else:
            pass
    else:
        world.say(f"But nothing went wrong, and the puggle only made the tune more spry.")
        world.say(f"So Mark laughed, and the puggle wagged, and the little day went by-by-by.")

    world.facts.update(
        mark=mark,
        puggle=puggle,
        prize=prize,
        activity=activity,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story about Mark and a puggle that includes "{f["activity"].keyword}".',
        f"Tell a funny story where Mark and the puggle start with {f['activity'].gerund} and end happily.",
        f"Write a child-friendly rhyme about {f['setting'].place} where Mark keeps {f['prize'].phrase} safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    act: Activity = _safe_fact(world, f, "activity")
    prize: Prize = _safe_fact(world, f, "prize")
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"The story is about Mark and his puggle.",
        ),
        QAItem(
            question=f"What was Mark doing at {f['setting'].place}?",
            answer=f"Mark was {act.gerund} at {f['setting'].place}.",
        ),
        QAItem(
            question=f"What did the puggle almost mess up?",
            answer=f"The puggle almost messed up {prize.phrase}, but Mark fixed the problem.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with everyone happy, laughing, and safe.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a puggle?",
            answer="A puggle is a small, playful dog, often with a very bouncy personality.",
        ),
        QAItem(
            question="Why do people laugh at silly little mix-ups?",
            answer="People laugh because little mix-ups can be surprising, harmless, and funny.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending is when the problem gets fixed and the characters feel glad again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden", "skip", "muffin", "Mark"),
    StoryParams("yard", "sniff", "book", "Mark"),
    StoryParams("porch", "ding", "cap", "Mark"),
    StoryParams("kitchen", "rhyme", "spoon", "Mark"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name)
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
at_risk(A,P) :- activity(A), prize(P), mess_of(A,M), harms(M,P).
compatible(A,P) :- at_risk(A,P), comfort(C), helps(C,M), mess_of(A,M), covers(C,R), worn_on(P,R).
valid_story(Place,A,P) :- affords(Place,A), compatible(A,P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for c in COMFORTS:
        lines.append(asp.fact("comfort", c.id))
        for m in sorted(c.helps):
            lines.append(asp.fact("helps", c.id, m))
        for r in sorted(c.covers):
            lines.append(asp.fact("covers", c.id, r))
    # positive harms relation for the tiny domain
    lines.append(asp.fact("harms", "mud", "muffin"))
    lines.append(asp.fact("harms", "mud", "book"))
    lines.append(asp.fact("harms", "crumbs", "book"))
    lines.append(asp.fact("harms", "crumbs", "muffin"))
    lines.append(asp.fact("harms", "noise", "cap"))
    lines.append(asp.fact("harms", "noise", "spoon"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    python_set = set(
        (place, act, pr)
        for place, setting in SETTINGS.items()
        for act in setting.affords
        for pr in PRIZES
        if reasonableness_gate(_safe_lookup(ACTIVITIES, act), _safe_lookup(PRIZES, pr))
    )
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    if python_set == clingo_set:
        print(f"OK: clingo gate matches python gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(python_set - clingo_set))
    print("clingo-only:", sorted(clingo_set - python_set))
    return 1


def build_world_from_params(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
