#!/usr/bin/env python3
"""
storyworlds/worlds/mamma_cliff_lookout_conflict_cautionary_myth.py
===================================================================

A small mythic storyworld set at a cliff lookout.

Seed story:
---
At a cliff lookout above the foam, a child walked with mamma to watch the sea
and hear the old wind-stones hum. The child loved the high view and wanted to
climb closer to the edge to see where the gulls vanished. Mamma warned that the
stone ledge could be slick and that the cliff did not forgive careless feet.

The child still reached for a brighter view, but the wind pulled hard at the
cloak and the path shivered under small steps. Mamma held the child back and
showed a safer place behind the marker stones. There, they watched the horizon
together, and the child learned that a wise heart can admire the wonder without
walking into danger.

Mythic premise:
---
A child, a mamma, a cliff lookout, and an old warning about the sea.
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
REGIONS = {"feet", "legs", "torso", "hands"}
DANGER_KINDS = {"slippery", "windy", "cold"}



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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm_ent: object | None = None
    child: object | None = None
    mamma: object | None = None
    relic: object | None = None
    def __post_init__(self) -> None:
        for k in ["slippery", "windy", "cold", "safe", "workload"]:
            self.meters.setdefault(k, 0.0)
        for k in ["love", "fear", "warning", "courage", "relief", "conflict", "wonder"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "mamma", "woman"}
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
    place: str = "the cliff lookout"
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
    danger: str
    weather: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)
    zone: set[str] = field(default_factory=set)
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
class Charm:
    id: str
    label: str
    phrase: str
    region: str
    guards: set[str]
    covers: set[str]
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.danger_zone: set[str] = set()

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


def _r_slick(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for kind in DANGER_KINDS:
            if actor.meters[kind] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.danger_zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("slick", actor.id, item.id, kind)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[kind] += 1
                item.meters["safe"] = 0.0
                out.append(f"The {item.label} grew troubled by the {kind} air.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["warning"] < THRESHOLD or actor.memes["reach"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["relieved"] >= THRESHOLD:
            continue
        if actor.memes["conflict"] < THRESHOLD:
            continue
        if actor.memes["safepath"] < THRESHOLD:
            continue
        actor.memes["relieved"] += 1
        actor.memes["conflict"] = 0.0
        out.append(f"Their fear thinned like mist.")
    return out


CAUSAL_RULES = [
    _r_slick,
    _r_conflict,
    _r_relief,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting, activity: Activity) -> str:
    return (
        f"{setting.place.capitalize()} stood above the white foam, and the wind "
        f"moved like a patient old voice."
    )


def predict_risk(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = copy_world(world)
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"danger": bool(prize.meters["slippery"] >= THRESHOLD), "conflict": actor.memes["warning"] >= THRESHOLD}


def copy_world(world: World) -> World:
    import copy
    clone = World(world.setting)
    clone.entities = copy.deepcopy(world.entities)
    clone.paragraphs = [[]]
    clone.facts = dict(world.facts)
    clone.fired = set(world.fired)
    clone.danger_zone = set(world.danger_zone)
    return clone


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.danger_zone = set(activity.zone)
    actor.meters[activity.id] += 1
    actor.memes["reach"] += 1
    actor.memes["wonder"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, child: Entity) -> None:
    world.say(
        f"At {world.setting.place}, {child.id} was a little {child.type} who loved "
        f"the sea wind and the far silver line of the horizon."
    )


def loves_view(world: World, child: Entity) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"{child.pronoun().capitalize()} loved looking down at the gulls below and "
        f"up at the clouds that moved like slow white ships."
    )


def warns(world: World, mamma: Entity, child: Entity, activity: Activity, relic: Entity) -> bool:
    pred = predict_risk(world, child, activity, relic.id)
    if not pred["danger"]:
        return False
    child.memes["warning"] += 1
    world.facts["predicted_danger"] = activity.danger
    world.say(
        f'"Careful," {mamma.id} said. "That stone can be {activity.danger}, and the cliff does not forgive careless feet."'
    )
    return True


def reaches(world: World, child: Entity, activity: Activity) -> None:
    child.memes["reach"] += 1
    world.say(
        f"{child.id} still wanted to {activity.verb}, and {child.pronoun()} took one "
        f"small step toward the brighter edge."
    )


def hold_back(world: World, mamma: Entity, child: Entity, activity: Activity) -> None:
    child.memes["held"] = 1.0
    child.memes["warning"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {mamma.id} held {child.pronoun('possessive')} hand and led {child.pronoun('object')} away from the edge."
    )


def choose_safe(world: World, mamma: Entity, child: Entity, activity: Activity, relic: Entity, charm: Charm) -> None:
    child.memes["safepath"] += 1
    child.memes["relieved"] += 1
    world.say(
        f'"Come stand by the marker stones," {mamma.id} said, "and we can watch the sea safely."'
    )
    world.say(
        f"So they stayed where the ground was steady, and {child.id} watched the gulls "
        f"from behind the old stones while {relic.label} stayed safe."
    )


SETTINGS = {
    "lookout": Setting(place="the cliff lookout", affords={"edge", "storm"}),
    "ledge": Setting(place="the cliff lookout ledge", affords={"edge"}),
}

ACTIVITIES = {
    "edge": Activity(
        id="edge",
        verb="peer over the edge",
        gerund="peering over the edge",
        rush="run closer to the brink",
        danger="slick and wild",
        weather="windy",
        keyword="cliff",
        tags={"cliff", "wind"},
        zone={"feet", "legs"},
    ),
    "storm": Activity(
        id="storm",
        verb="chase the storm light",
        gerund="chasing storm-light",
        rush="run toward the bright flashes",
        danger="full of hard wind",
        weather="windy",
        keyword="storm",
        tags={"storm", "wind"},
        zone={"feet", "legs", "hands"},
    ),
}

CHARMS = {
    "sandals": Charm(
        id="sandals",
        label="sandals",
        phrase="thin rope sandals",
        region="feet",
        guards={"slippery"},
        covers={"feet"},
        plural=True,
    ),
    "cloak": Charm(
        id="cloak",
        label="a wool cloak",
        phrase="a wool cloak",
        region="torso",
        guards={"cold", "windy"},
        covers={"torso"},
    ),
    "grip": Charm(
        id="grip",
        label="a hand-wrap",
        phrase="a hand-wrap woven tight",
        region="hands",
        guards={"windy"},
        covers={"hands"},
    ),
}

GIRL_NAMES = ["Mira", "Nina", "Lina", "Tala", "Rosa"]
BOY_NAMES = ["Ivo", "Niko", "Jori", "Kian", "Orin"]
TRAITS = ["curious", "bold", "thoughtful", "restless", "gentle"]


@dataclass
class StoryParams:
    place: str
    activity: str
    charm: str
    name: str
    gender: str
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
            for ch_id, charm in CHARMS.items():
                if act.zone and charm.region in act.zone and "slippery" in charm.guards:
                    combos.append((place, act_id, ch_id))
                elif act.zone and charm.region in act.zone and "windy" in charm.guards:
                    combos.append((place, act_id, ch_id))
    return combos


def explain_rejection(activity: Activity, charm: Charm) -> str:
    return (
        f"(No story: {charm.label} does not make a convincing mythic safeguard "
        f"for {activity.gerund} at the cliff lookout. Try a charm that covers the "
        f"at-risk region and speaks to the danger.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic cautionary storyworld at a cliff lookout.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if getattr(args, "activity", None) and getattr(args, "charm", None):
        if (getattr(args, "place", None) or "lookout", getattr(args, "activity", None), getattr(args, "charm", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "charm", None) is None or c[2] == getattr(args, "charm", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, charm = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, charm=charm, name=name, gender=gender, trait=trait)


def tell(setting: Setting, activity: Activity, charm: Charm, child_name: str, gender: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=gender, traits=["little", trait]))
    mamma = world.add(Entity(id="mamma", kind="character", type="mamma", label="mamma"))
    relic = world.add(Entity(
        id="relic", kind="thing", type="relic", label="old sea-marker",
        phrase="an old sea-marker carved with spirals", caretaker="mamma", region=charm.region
    ))
    relic.worn_by = child.id
    charm_ent = world.add(Entity(
        id=charm.id, kind="thing", type="charm", label=charm.label, phrase=charm.phrase,
        owner=child.id, protective=True, region=charm.region, covers=set(charm.covers), plural=charm.plural
    ))
    charm_ent.worn_by = child.id

    introduce(world, child)
    loves_view(world, child)
    world.say(
        f"{child.id} wore {charm.phrase} and felt ready to meet the wide wind above the foam."
    )

    world.para()
    world.say(setting_detail(setting, activity))
    warns(world, mamma, child, activity, relic)
    reaches(world, child, activity)
    hold_back(world, mamma, child, activity)

    world.para()
    choose_safe(world, mamma, child, activity, relic, charm)
    world.say(
        f"In the end, {child.id} learned that a cliff can be admired best from a wise distance."
    )

    world.facts.update(child=child, mamma=mamma, relic=relic, charm=charm, activity=activity, setting=setting, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    activity = _safe_fact(world, f, "activity")
    return [
        f'Write a short myth for a young child about {child.id} at {world.setting.place}, with a warning and a safe choice.',
        f"Tell a cautionary story where mamma stops {child.id} from {activity.verb} near a cliff.",
        f'Write a gentle mythic tale that uses the word "{activity.keyword}" and ends with a wise, safe view of the sea.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, activity, charm = f["child"], f["activity"], f["charm"]
    return [
        QAItem(
            question=f"Where did {child.id} want to go to {activity.verb}?",
            answer=f"{child.id} wanted to go closer to the edge at {world.setting.place}, where the wind felt strong and the sea looked bright.",
        ),
        QAItem(
            question=f"Why did mamma warn {child.id} about the cliff lookout?",
            answer=f"Mamma warned {child.id} because the stone could be {activity.danger} and the cliff was not a place for careless feet.",
        ),
        QAItem(
            question=f"What did mamma ask {child.id} to do instead?",
            answer=f"Mamma asked {child.id} to stand by the marker stones and watch the sea from a safer place.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt safer and wiser, and the wide sea could still be admired without going too close to danger.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cliff lookout?",
            answer="A cliff lookout is a place high above the ground where people can see far across the land or sea.",
        ),
        QAItem(
            question="Why should people be careful near a cliff?",
            answer="People should be careful near a cliff because the ground can be steep, windy, or slippery, and a mistake can be dangerous.",
        ),
        QAItem(
            question="What does a wise warning do in a story?",
            answer="A wise warning helps someone notice danger early so they can choose a safer path.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
dangerous(A, P) :- activity(A), charm(P), zone(A, R), region(P, R).
safe_fix(A, P) :- dangerous(A, P), guards(P, slippery).
safe_fix(A, P) :- dangerous(A, P), guards(P, windy).
valid(Place, A, P) :- affords(Place, A), safe_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("region", cid, c.region))
        for g in sorted(c.guards):
            lines.append(asp.fact("guards", cid, g))
        for r in sorted(c.covers):
            lines.append(asp.fact("covers", cid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="lookout", activity="edge", charm="sandals", name="Mira", gender="girl", trait="curious"),
    StoryParams(place="lookout", activity="edge", charm="cloak", name="Ivo", gender="boy", trait="thoughtful"),
    StoryParams(place="ledge", activity="storm", charm="grip", name="Tala", gender="girl", trait="bold"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(CHARMS, params.charm), params.name, params.gender, params.trait)
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
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
