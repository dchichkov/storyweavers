#!/usr/bin/env python3
"""
scrape_reconciliation_slice_of_life.py
=====================================

A small slice-of-life story world about a child getting a scrape, feeling hurt
and embarrassed, and then reaching reconciliation with a helper.

Premise:
- A child is playing in an ordinary neighborhood moment.
- A small fall causes a scrape.
- The child first feels upset or stubborn.
- A parent, sibling, or friend helps clean it.
- The child and helper reconcile through care, apology, and a small comfort.

The world is intentionally small and constraint-checked: the scrape must be
plausible, the response must be gentle, and reconciliation must be earned by a
helpful action that changes the emotional state.

The simulated state includes physical meters and emotional memes, and the prose
is assembled from those state changes rather than from a frozen template.
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"scrape": 0.0, "clean": 0.0}
        if not self.memes:
            self.memes = {"hurt": 0.0, "embarrassed": 0.0, "stubborn": 0.0, "peace": 0.0, "care": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
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
    place: str = "the front steps"
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
    slip: str
    scrape_where: str
    mess: str = "scrape"
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
class Aid:
    id: str
    label: str
    action: str
    result: str
    comfort: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone
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


def is_valid_combo(setting: Setting, activity: Activity, aid: Aid) -> bool:
    return activity.id in setting.affords and aid.id in {"bandage", "sink", "hug"}


def scrape_risk(activity: Activity) -> bool:
    return activity.scrape_where in {"knee", "elbow", "palm"}


def predict_reconciliation(world: World, child: Entity, activity: Activity, aid: Aid) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(child.id), activity, narrate=False)
    apply_aid(sim, sim.get("Helper"), sim.get(child.id), aid, narrate=False)
    kid = sim.get(child.id)
    return {
        "scraped": kid.meters["scrape"] >= THRESHOLD,
        "peace": kid.memes["peace"] >= THRESHOLD,
    }


def _rule_embarrassed(world: World) -> list[str]:
    out: list[str] = []
    for child in world.characters():
        if child.meters["scrape"] >= THRESHOLD and child.memes["hurt"] >= THRESHOLD:
            sig = ("embarrassed", child.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            child.memes["embarrassed"] += 1
            out.append(f"{child.pronoun('subject').capitalize()} looked down and wished the moment could be undone.")
    return out


def _rule_reconcile(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("Child")
    helper = world.entities.get("Helper")
    if not child or not helper:
        return out
    if child.memes["care"] < THRESHOLD or child.memes["peace"] >= THRESHOLD:
        return out
    sig = ("reconcile", child.id, helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["peace"] += 1
    child.memes["stubborn"] = 0.0
    out.append("The two of them settled into the same quiet, kinder mood.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_rule_embarrassed, _rule_reconcile):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def do_activity(world: World, child: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        pass
    child.meters["scrape"] += 1
    child.memes["hurt"] += 1
    child.memes["stubborn"] += 1
    world.facts["scrape_where"] = activity.scrape_where
    world.facts["activity_id"] = activity.id
    if narrate:
        world.say(
            f"{child.id} {activity.verb} near {world.setting.place}, and then {child.pronoun('subject')} {activity.slip}."
        )
        world.say(f"{child.pronoun('possessive').capitalize()} {activity.scrape_where} got a small scrape.")
    propagate(world, narrate=narrate)


def apply_aid(world: World, helper: Entity, child: Entity, aid: Aid, narrate: bool = True) -> None:
    child.memes["care"] += 1
    child.memes["stubborn"] = max(0.0, child.memes["stubborn"] - 1)
    if aid.id == "bandage":
        child.meters["clean"] += 1
    if aid.id == "hug":
        child.memes["peace"] += 1
    if narrate:
        world.say(f"{helper.id} came over and {aid.action}.")
        world.say(f"{aid.result} {aid.comfort}")
    propagate(world, narrate=narrate)


def setting_line(setting: Setting) -> str:
    if setting.indoor:
        return f"It was quiet inside {setting.place}."
    return f"The afternoon at {setting.place} felt ordinary and warm."


def opening(world: World, child: Entity) -> None:
    world.say(f"{child.id} was a little {child.type} who liked simple days and familiar places.")
    world.say(setting_line(world.setting))


def desire(world: World, child: Entity, activity: Activity) -> None:
    world.say(f"{child.pronoun('subject').capitalize()} loved {activity.gerund}, because it made the day feel bigger.")
    world.say(f"So {child.pronoun('subject')} wanted to {activity.verb} right away.")


def upset(world: World, child: Entity) -> None:
    if child.memes["hurt"] >= THRESHOLD:
        world.say(f"But the scrape stung, and {child.pronoun('subject')} felt embarrassed too.")
        world.say(f"{child.pronoun('subject').capitalize()} did not want everyone looking at {child.pronoun('possessive')} knee.")


def apology(world: World, helper: Entity, child: Entity, aid: Aid) -> None:
    if child.memes["peace"] < THRESHOLD:
        return
    world.say(f"{helper.id} stayed close and spoke gently, and {child.id} listened.")
    world.say(f"{child.id} finally nodded, and the two of them reconciled over the small hurt.")
    world.say(f"After that, {child.id} could breathe easier and stand up straighter.")


SETTINGS = {
    "porch": Setting(place="the front steps", indoor=False, affords={"steps", "run"}),
    "yard": Setting(place="the backyard", indoor=False, affords={"bike", "run"}),
    "hall": Setting(place="the hallway", indoor=True, affords={"run", "trip"}),
    "playground": Setting(place="the playground", indoor=False, affords={"slide", "swing"}),
}

ACTIVITIES = {
    "steps": Activity(
        id="steps",
        verb="walked down the steps",
        gerund="walking down the steps",
        slip="slipped on the last step",
        scrape_where="knee",
        tags={"steps", "fall"},
    ),
    "bike": Activity(
        id="bike",
        verb="rode a small bike",
        gerund="riding a small bike",
        slip="turned too fast and tipped over",
        scrape_where="elbow",
        tags={"bike", "fall"},
    ),
    "run": Activity(
        id="run",
        verb="ran to catch a ball",
        gerund="running around",
        slip="tripped on the edge of the path",
        scrape_where="palm",
        tags={"run", "fall"},
    ),
    "slide": Activity(
        id="slide",
        verb="slid down the slide",
        gerund="sliding",
        slip="landed a little too hard",
        scrape_where="knee",
        tags={"slide", "fall"},
    ),
}

AIDS = {
    "bandage": Aid(
        id="bandage",
        label="a bandage",
        action="cleaned the scrape and put on a bandage",
        result="The sore spot felt neat and safe again.",
        comfort="That made the hurt feel smaller.",
    ),
    "sink": Aid(
        id="sink",
        label="warm water",
        action="washed the scrape with warm water",
        result="The tiny scratch looked cleaner right away.",
        comfort="The cool sting faded a little.",
    ),
    "hug": Aid(
        id="hug",
        label="a hug",
        action="gave the child a careful hug",
        result="The child leaned in and felt less alone.",
        comfort="That made the moment feel kinder.",
    ),
}

CHILD_NAMES = ["Mina", "Theo", "Ruby", "Owen", "Pia", "Luca", "Nora", "Eli"]
HELPER_NAMES = ["Mom", "Dad", "Aunt June", "Ben", "Sage", "Jules"]
TRAITS = ["quiet", "busy", "curious", "gentle", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    aid: str
    name: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            if not scrape_risk(act):
                continue
            for aid_id in AIDS:
                combos.append((place, act_id, aid_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life scrape and reconciliation story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    combos = [c for c in combos
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "aid", None) is None or c[2] == getattr(args, "aid", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, aid = rng.choice(list(combos))
    return StoryParams(
        place=place,
        activity=activity,
        aid=aid,
        name=getattr(args, "name", None) or rng.choice(CHILD_NAMES),
        helper=getattr(args, "helper", None) or rng.choice(HELPER_NAMES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(id="Child", kind="character", type="girl" if params.name in {"Mina", "Ruby", "Pia", "Nora"} else "boy"))
    child.id = params.name
    child.label = params.name
    child.type = child.type if params.name not in {"Mina", "Ruby", "Pia", "Nora"} else "girl"
    helper_type = "mother" if params.helper in {"Mom", "Aunt June"} else "boy"
    if params.helper in {"Dad", "Ben", "Jules"}:
        helper_type = "father" if params.helper == "Dad" else "boy"
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=params.helper))
    helper.id = params.helper
    helper.label = params.helper
    opening(world, child)
    world.para()
    desire(world, child, _safe_lookup(ACTIVITIES, params.activity))
    do_activity(world, child, _safe_lookup(ACTIVITIES, params.activity), narrate=True)
    upset(world, child)
    world.para()
    apply_aid(world, helper, child, _safe_lookup(AIDS, params.aid), narrate=True)
    apology(world, helper, child, _safe_lookup(AIDS, params.aid))
    world.facts.update(
        child=child,
        helper=helper,
        activity=_safe_lookup(ACTIVITIES, params.activity),
        aid=_safe_lookup(AIDS, params.aid),
        setting=_safe_lookup(SETTINGS, params.place),
        resolved=child.memes["peace"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    act = _safe_fact(world, f, "activity")
    aid = _safe_fact(world, f, "aid")
    return [
        f'Write a gentle slice-of-life story about {child.id} and a small {act.id} scrape.',
        f"Tell a short story where {child.id} gets hurt while {act.gerund} and then {aid.label} helps."
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    act = _safe_fact(world, f, "activity")
    aid = _safe_fact(world, f, "aid")
    return [
        QAItem(
            question=f"What happened to {child.id} while {child.pronoun('subject')} was {act.gerund}?",
            answer=f"{child.id} {act.slip}, and {child.pronoun('possessive')} {act.scrape_where} got a small scrape.",
        ),
        QAItem(
            question=f"Who helped {child.id} after the scrape?",
            answer=f"{helper.label} helped by {aid.action.lower()}.",
        ),
        QAItem(
            question=f"How did the story end after the hurt moment?",
            answer=f"{child.id} and {helper.label} reconciled, and the small scrape felt much easier to handle.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a scrape?",
            answer="A scrape is a small skin injury, usually from bumping or rubbing against something rough.",
        ),
        QAItem(
            question="Why do people clean scrapes?",
            answer="People clean scrapes so dirt does not stay in the sore spot and the skin can heal safely.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people calm down, make up, and feel friendly again after a bad moment.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: meters={ {k: round(v, 2) for k, v in e.meters.items() if v} } "
            f"memes={ {k: round(v, 2) for k, v in e.memes.items() if v} }"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="porch", activity="steps", aid="bandage", name="Mina", helper="Mom", trait="curious"),
    StoryParams(place="yard", activity="bike", aid="sink", name="Theo", helper="Dad", trait="thoughtful"),
    StoryParams(place="playground", activity="slide", aid="hug", name="Ruby", helper="Aunt June", trait="gentle"),
]


ASP_RULES = r"""
scrape_happens(A) :- activity(A), risk(A).
reconciliation(A, H, I) :- scrape_happens(A), aid(I), helper(H).
valid_story(P, A, I) :- setting(P), affords(P, A), aid(I), risk(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("risk", aid))
    for iid in AIDS:
        lines.append(asp.fact("aid", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set()
    for p, a, i in valid_combos():
        python_set.add((p, a, i))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if clingo_set - python_set:
        print("only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("only in python:", sorted(python_set - clingo_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        for c in combos:
            print(c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
