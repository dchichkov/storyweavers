#!/usr/bin/env python3
"""
storyworlds/worlds/stein_strangle_strobe_lesson_learned_tall_tale.py
====================================================================

A tall-tale storyworld about a booming-big lesson at a small frontier fair:
a noisy show, a shiny stein, and a strobe lamp that is a little too bright
for common sense.

Seed tale:
---
Old Jeb was the biggest, bounciest fellow in the county, and he loved to
show off at the summer fair. One day he won a polished stein from the prize
table and an energetic little strobe lamp from the vaudeville booth. The lamp
flashed like angry lightning, and the stein gleamed like a moon in a bucket.

Jeb wanted to make the crowd cheer, so he tried to strangle the strobe with
both hands to make it stop blinking. The crowd gasped, the stein slipped, and
the lamp kept strobbing like a thousand fireflies in a tin pail. Then Grandma
Nell laughed her big wise laugh and showed Jeb a better way: cover the lamp
with a cloth, set the stein on a wagon, and let the show go on kindly.

Causal world:
---
    bright strobe near bare eyes    -> watcher.glare += 1 ; watcher.startle += 1
    clumsy squeeze on lamp          -> lamp.wobble += 1 ; lamp.sputter += 1
    lamp wobble + uncovered prize   -> prize.rattle += 1 ; prize.fret += 1
    wise helper covers lamp         -> watcher.startle -> 0 ; watcher.relief += 1
    lesson accepted                 -> hero.lesson += 1 ; hero.pride -> humble

Style:
---
Tall tale, child-facing, with a big-hearted exaggeration and a clear lesson
learned at the end.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    region: str = ""
    helper: object | None = None
    hero: object | None = None
    lamp: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = __import__('collections').defaultdict(float)
        if not self.memes:
            self.memes = __import__('collections').defaultdict(float)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandma"}
        male = {"boy", "father", "dad", "man", "cowboy"}
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
    indoors: bool = False
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
    mess: str
    soil: str
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


@dataclass
class Rule:
    name: str
    apply: callable
    CAUSAL_RULES: list = field(default_factory=list)
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


def _r_strobe_glare(world: World) -> list[str]:
    out = []
    for ch in world.characters():
        if ch.meters.get("glare", 0) < THRESHOLD:
            continue
        sig = ("glare", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ch.memes["startle"] = ch.memes.get("startle", 0) + 1
        out.append(f"The bright strobe made {ch.id} blink and startle.")
    return out


def _r_lamp_wobble(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.type != "strobe":
            continue
        if ent.meters.get("wobble", 0) < THRESHOLD:
            continue
        sig = ("wobble", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["sputter"] = ent.meters.get("sputter", 0) + 1
        out.append("The strobe lamp sputtered and skittered in the hand.")
    return out


def _r_prize_fret(world: World) -> list[str]:
    out = []
    strobe = next((e for e in world.entities.values() if e.type == "strobe"), None)
    if not strobe or strobe.meters.get("sputter", 0) < THRESHOLD:
        return out
    for prize in list(world.entities.values()):
        if prize.type != "stein":
            continue
        if prize.meters.get("rattle", 0) >= THRESHOLD:
            continue
        if prize.region not in world.zone or world.covered(world.get(world.facts["hero"].id), prize.region):
            continue
        sig = ("fret", prize.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        prize.meters["rattle"] = prize.meters.get("rattle", 0) + 1
        prize.memes["fret"] = prize.memes.get("fret", 0) + 1
        out.append("The stein rattled like a kettle with hiccups.")
    return out


def _r_lesson(world: World) -> list[str]:
    hero = world.facts.get("hero")
    helper = world.facts.get("helper")
    if not hero or not helper:
        return []
    h = hero
    if h.memes.get("startle", 0) < THRESHOLD:
        return []
    sig = ("lesson", h.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    h.memes["lesson"] = h.memes.get("lesson", 0) + 1
    h.memes["pride"] = 0
    h.memes["relief"] = h.memes.get("relief", 0) + 1
    return ["__lesson__"]


CAUSAL_RULES = [Rule("strobe_glare", _r_strobe_glare), Rule("lamp_wobble", _r_lamp_wobble), Rule("prize_fret", _r_prize_fret), Rule("lesson", _r_lesson)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            msgs = rule.apply(world)
            if msgs:
                changed = True
                for m in msgs:
                    if m != "__lesson__":
                        produced.append(m)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    if setting.indoors:
        return f"Inside {setting.place}, the air felt close and the lights bounced off every board and bottle."
    return f"Outside {setting.place}, the sun shone on the dust and the whole fair sparkled."


def build_story(world: World, hero: Entity, helper: Entity, prize: Entity, lamp: Entity, activity: Activity) -> None:
    world.say(f"{hero.id} was a big, booming fellow with a laugh that could roll clear across the county.")
    world.say(f"{hero.pronoun('subject').capitalize()} loved {activity.gerund} at the fair and showing off for the cheering crowd.")
    world.say(f"That afternoon {hero.id} won {hero.pronoun('object')} {prize.phrase}, and it gleamed as proud as a new penny.")
    world.say(f"Then the vaudeville booth handed over {hero.pronoun('object')} {lamp.phrase}, a strobe that flashed like a tiny thunderstorm.")
    world.para()
    world.say(setting_detail(world.setting))
    world.say(f"{hero.id} wanted to {activity.verb}, but the strobe kept blinking bright enough to make folks squint.")
    world.say(f"So {hero.id} tried to strangle the strobe with both hands, just to make it quit its blinky fuss.")
    lamp.meters["wobble"] = lamp.meters.get("wobble", 0) + 1
    hero.meters["glare"] = hero.meters.get("glare", 0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    propagate(world, narrate=True)
    world.say(f"The crowd gasped, and the stein nearly jumped right out of {hero.pronoun('possessive')} grip.")
    world.para()
    helper.memes["wisdom"] = helper.memes.get("wisdom", 0) + 1
    world.say(f"Then {helper.id} came over smiling, as calm as a porch cat at sundown.")
    world.say(f'"No need for rough hands," {helper.id} said. "Cover that strobe with a cloth, set the stein on the wagon, and let the show be kind."')
    lamp.protective = True
    lamp.covers = {"eyes"}
    hero.memes["startle"] = hero.memes.get("startle", 0) + 1
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    propagate(world, narrate=True)
    world.say(f"{hero.id} took a breath, nodded once, and learned the lesson right then and there.")
    world.say(f"After that, {helper.id} covered the strobe, the stein stayed steady, and the fair went on shining without any more grand foolishness.")


SETTINGS = {
    "fair": Setting(place="the county fair", indoors=False, affords={"show"}),
    "barn": Setting(place="the big barn dance", indoors=True, affords={"show"}),
    "river": Setting(place="the river bend picnic", indoors=False, affords={"show"}),
}

ACTIVITIES = {
    "show": Activity(
        id="show",
        verb="put on a bright show",
        gerund="putting on bright shows",
        rush="wave the lamp around",
        mess="glare",
        soil="all dazzled and rattled",
        zone={"eyes", "hands"},
        keyword="strobe",
        tags={"strobe", "light"},
    )
}

PRIZES = {
    "stein": Prize(
        label="stein",
        phrase="a polished stein",
        type="stein",
        region="hands",
    )
}

GEAR = [
    Gear(
        id="cloth",
        label="a soft cloth",
        covers={"eyes"},
        guards={"glare"},
        prep="cover the lamp with a soft cloth",
        tail="covered the strobe with a soft cloth",
    )
]

NAMES = ["Jeb", "Hank", "Mose", "Clem", "Bub", "Zeke", "Ike"]
HELPERS = ["Grandma Nell", "Aunt Tilly", "Old Ezra", "Miss Polly"]


@dataclass
class StoryParams:
    place: str
    name: str
    helper: str
    seed: Optional[int] = None
    params: object | None = None
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, "show") for place in SETTINGS]


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), covers(G,R), worn_on(P,R), guards(G,M), mess_of(A,M).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: clingo gate matches valid_combos().")
        return 0
    print("MISMATCH between clingo and valid_combos().")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: a bright strobe, a proud stein, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    if place not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type="man", memes={"pride": 1.0}))
    helper = world.add(Entity(id=params.helper, kind="character", type="woman", memes={"wisdom": 1.0}))
    prize = world.add(Entity(id="stein", type="stein", label="stein", phrase="a polished stein", owner=hero.id, caretaker=helper.id, region="hands"))
    lamp = world.add(Entity(id="strobe", type="strobe", label="strobe", phrase="an energetic little strobe lamp", owner=hero.id, caretaker=helper.id))
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    build_story(world, hero, helper, prize, lamp, ACTIVITIES["show"])
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f'Write a tall tale for a child about a giant fellow named {params.name}, a stein, and a strobe at {world.setting.place}.',
            "Tell a gentle frontier story where someone learns a better way instead of trying to strangle the strobe.",
            f'Write a short story that uses the words "stein", "strangle", and "strobe" and ends with a lesson learned.',
        ],
        story_qa=[
            QAItem(
                question=f"What did {params.name} win at the fair?",
                answer=f"{params.name} won a polished stein from the prize table.",
            ),
            QAItem(
                question=f"What silly thing did {params.name} try to do to the strobe?",
                answer=f"{params.name} tried to strangle the strobe with both hands to make it stop blinking.",
            ),
            QAItem(
                question=f"What better way did {params.helper} show {params.name}?",
                answer=f"{params.helper} showed {params.name} how to cover the strobe with a soft cloth and set the stein on the wagon.",
            ),
            QAItem(
                question="What lesson was learned at the end?",
                answer="The lesson was to use a gentle, safe fix instead of rough hands.",
            ),
        ],
        world_qa=[
            QAItem(
                question="What is a stein?",
                answer="A stein is a sturdy mug or cup, often used for drinks.",
            ),
            QAItem(
                question="What does a strobe do?",
                answer="A strobe flashes on and off very quickly, making bright blinking light.",
            ),
            QAItem(
                question="What should you do if a light is too bright?",
                answer="You can cover it, dim it, or turn away so your eyes are more comfortable.",
            ),
        ],
        world=world,
    )
    return sample


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            if e.protective:
                bits.append(f"covers={sorted(e.covers)}")
            print(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    if qa:
        print()
        print("== Story Q&A ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== World Q&A ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid/3."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place in SETTINGS:
            params = StoryParams(place=place, name="Jeb", helper="Grandma Nell")
            samples.append(generate(params))
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
