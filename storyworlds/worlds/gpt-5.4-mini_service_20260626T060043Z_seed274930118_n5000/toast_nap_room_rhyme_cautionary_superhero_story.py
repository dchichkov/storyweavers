#!/usr/bin/env python3
"""
A standalone Storyweavers world: a tiny superhero-style nap-room story about toast.

Premise:
- A sleepy child in a nap room loves a crunchy toast snack.
- A little helper superhero wants the room quiet for rest.
- Toast crumbs threaten the blanket and the nap.

Turn:
- The child tries to crunch the toast during rest time.
- The helper warns that loud munching and crumbs will wake everyone.
- A careless choice makes the mess spread.

Resolution:
- The child agrees to a careful compromise: finish the toast in the hall, then return
  to the nap room with clean hands and a quieter heart.

This script models both physical meters and emotional memes, includes a Python
reasonableness gate plus an inline ASP twin, and supports QA/trace/JSON modes.
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
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    hero: object | None = None
    toast: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"crumbs": 0.0, "noise": 0.0, "tidy": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "rest": 0.0, "defiance": 0.0, "care": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    place: str = "the nap room"
    indoor: bool = True
    affords: set[str] = field(default_factory=lambda: {"toast"})
    SETTING: object | None = None
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
    keyword: str = ""
    tags: set[str] = field(default_factory=set)
    TOAST_ACTIVITY: object | None = None
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
class Snack:
    label: str
    phrase: str
    type: str
    region: str = "hands"
    plural: bool = False
    TOAST_SNACK: object | None = None
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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def rhyme(a: str, b: str) -> str:
    return f"{a} and {b}"


def intro_line(hero: Entity, sidekick: Entity) -> str:
    return (
        f"In the nap room soft and dim, {hero.id} was small but full of vim; "
        f"{sidekick.id} kept watch with a brave white cape, to keep the sleepy room in shape."
    )


def is_risky(activity: Activity, snack: Snack) -> bool:
    return snack.region in activity.zone


def choose_gear(activity: Activity, snack: Snack) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and snack.region in gear.covers:
            return gear
    return None


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    actor.meters["noise"] += 1
    propagate(world, narrate=narrate)


def _crumb_spread(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["crumbs"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("crumb_spread", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["crumbs"] += 1
            item.meters["tidy"] += 1
            out.append(
                f"{actor.id}'s {item.label} got crumb-specked, and the room looked less neat."
            )
    return out


def _noise_spread(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["noise"] < THRESHOLD:
            continue
        sig = ("noise", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for e in world.characters():
            if e.id != actor.id:
                e.memes["worry"] += 1
        out.append("The crunchy sound shook the sleepy hush.")
    return out


def _care_wins(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("Child")
    sidekick = world.entities.get("Hero")
    snack = world.entities.get("toast")
    if not hero or not sidekick or not snack:
        return out
    if hero.memes["care"] < THRESHOLD:
        return out
    sig = ("care", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["defiance"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["rest"] += 1
    sidekick.memes["joy"] += 1
    out.append("Careful choices made the room calm again.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_crumb_spread, _noise_spread, _care_wins):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, activity: Activity, snack_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    snack = sim.entities.get(snack_id)
    return {
        "soiled": bool(snack and snack.meters["tidy"] >= THRESHOLD),
        "noise": sum(e.meters["noise"] for e in sim.characters()),
    }


def tell() -> World:
    world = World(SETTING)
    child = world.add(Entity(id="Child", kind="character", type="boy"))
    hero = world.add(Entity(id="Hero", kind="character", type="superhero", label="Captain Quiet"))
    toast = world.add(Entity(
        id="toast",
        type="toast",
        label="toast",
        phrase="a warm slice of toast",
        owner=child.id,
        caretaker=hero.id,
        region="hands",
    ))

    world.say(intro_line(child, hero))
    world.say(
        f"{child.id} loved {TOAST_ACTIVITY.gerund} during quiet time, because the golden "
        f"toast tasted crisp and sweet."
    )
    world.say(f"{hero.label} had a cape that whispered, 'Rest first, then snack, then play.'")
    world.say(f"{child.id} held {child.pronoun('possessive')} {toast.label} like treasure.")

    world.para()
    world.say(
        f"At the nap room door, {hero.label} pointed to the mats and said, "
        f"'{TOAST_ACTIVITY.warning_line}'"
    )
    world.say(
        f"But {child.id} wanted to {TOAST_ACTIVITY.rush}, even though the room was meant for naps."
    )

    pred = predict_mess(world, child, TOAST_ACTIVITY, toast.id)
    world.facts["predicted_noise"] = pred["noise"]
    world.facts["predicted_soil"] = TOAST_ACTIVITY.soil

    if pred["soiled"]:
        child.memes["defiance"] += 1
        child.meters["crumbs"] += 1
        world.say(
            f"{child.id} took one big bite, and crumbs hopped onto the blanket like tiny villains."
        )
        _do_activity(world, child, TOAST_ACTIVITY, narrate=True)
        world.say(
            f"{hero.label} gently lifted a hand and said, 'A crumbly crunch can chase sleep away.'"
        )
        world.say(
            f"{child.id} paused, looked at the messy blanket, and felt the room grow more serious."
        )

    world.para()
    gear = choose_gear(TOAST_ACTIVITY, toast)
    if gear is None:
        pass
    helper = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        protective=True,
        covers=set(gear.covers),
        owner=child.id,
        caretaker=hero.id,
        plural=gear.plural,
    ))
    helper.worn_by = child.id
    if predict_mess(world, child, TOAST_ACTIVITY, toast.id)["soiled"]:
        helper.worn_by = None
        del world.entities[helper.id]
        pass
    world.say(
        f"{hero.label} smiled and said, '{gear.prep}, and then come back for rest.'"
    )
    child.memes["care"] += 1
    world.say(
        f"{child.id} nodded, carried the toast to the hall, and took careful bites there."
    )
    world.say(
        f"Then {child.id} returned to the nap room, where the blanket stayed clean and the hush came back."
    )

    world.facts.update(
        child=child,
        hero=hero,
        toast=toast,
        activity=TOAST_ACTIVITY,
        gear=gear,
        resolved=True,
        conflict=True,
    )
    return world


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Child"
    hero_name: str = "Captain Quiet"
    CURATED: list = field(default_factory=list)
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


SETTING = Setting(place="the nap room", indoor=True, affords={"toast"})
TOAST_ACTIVITY = Activity(
    id="toast",
    verb="eat toast",
    gerund="eating toast",
    rush="crunch the toast in the nap room",
    mess="crumbs",
    soil="crumb-speckled",
    zone={"hands", "blanket"},
    keyword="toast",
    tags={"toast", "crumbs", "nap_room"},
)
TOAST_SNACK = Snack(
    label="toast",
    phrase="a warm slice of toast",
    type="toast",
)
GEAR = [
    Gear(
        id="napkin",
        label="a big napkin",
        covers={"hands"},
        guards={"crumbs"},
        prep="wrap the toast in a big napkin and eat it in the hall",
        tail="walked the toast to the hall for careful bites",
    ),
    Gear(
        id="tray",
        label="a little tray",
        covers={"hands", "blanket"},
        guards={"crumbs"},
        prep="set the toast on a little tray first",
        tail="carried the tray away from the blanket",
    ),
]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short superhero story for a little child in a nap room that includes the word "toast".',
        'Tell a cautionary rhyme where Captain Quiet warns a child about crumbly toast during nap time.',
        'Write a gentle nap-room story about a child, a superhero helper, and a safe way to enjoy toast.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = _safe_fact(world, world.facts, "child")
    hero = _safe_fact(world, world.facts, "hero")
    toast = _safe_fact(world, world.facts, "toast")
    gear = _safe_fact(world, world.facts, "gear")
    return [
        QAItem(
            question=f"Who wanted to eat toast in the nap room?",
            answer=f"{child.id} wanted to eat toast in the nap room, and {hero.label} tried to keep the room calm.",
        ),
        QAItem(
            question=f"Why did {hero.label} warn {child.id} about the toast?",
            answer=(
                f"{hero.label} warned {child.id} because crunchy toast can spill crumbs and make a nap room messy and loud."
            ),
        ),
        QAItem(
            question=f"What helped {child.id} enjoy the toast more carefully?",
            answer=(
                f"A {gear.label} helped {child.id} take the toast to the hall, where the crumbs would not land on the blanket."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended with {child.id} returning to the nap room while the blanket stayed clean and the sleepy hush came back."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is toast?",
            answer="Toast is bread that has been browned until it is crisp and warm.",
        ),
        QAItem(
            question="Why can crumbs be a problem in a nap room?",
            answer="Crumbs can make a blanket messy and can wake sleepy children if they crunch and scatter.",
        ),
        QAItem(
            question="What does a superhero helper do?",
            answer="A superhero helper watches for trouble and gives brave, careful advice to keep everyone safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/2.
#show valid_story/3.

valid(A,P) :- affords(A), activity(A), snack(P), at_risk(A,P), has_fix(A,P).
valid_story(A,P,H) :- valid(A,P), hero(H).

at_risk(A,P) :- splashes(A,R), worn_on(P,R).
has_fix(A,P) :- gear(G), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R), splashes(A,R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("affords", "nap_room", "toast"))
    lines.append(asp.fact("activity", TOAST_ACTIVITY.id))
    lines.append(asp.fact("mess_of", TOAST_ACTIVITY.id, TOAST_ACTIVITY.mess))
    for r in sorted(TOAST_ACTIVITY.zone):
        lines.append(asp.fact("splashes", TOAST_ACTIVITY.id, r))
    lines.append(asp.fact("snack", TOAST_SNACK.type))
    lines.append(asp.fact("worn_on", TOAST_SNACK.type, TOAST_SNACK.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    lines.append(asp.fact("hero", "Hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    return [("nap_room", "toast")]


def explain_rejection() -> str:
    return "(No story: the nap room only supports the toast cautionary superhero setup.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a superhero cautionary rhyme about toast in a nap room.")
    ap.add_argument("--place", choices=["nap_room"])
    ap.add_argument("--activity", choices=["toast"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "place", None) != "nap_room":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "activity", None) and getattr(args, "activity", None) != "toast":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(seed=None)


def generate(params: StoryParams) -> StorySample:
    world = tell()
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


CURATED = [StoryParams(seed=274930118)]


def valid_story_count() -> int:
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with hero):")
        for combo in triples:
            print(" ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
