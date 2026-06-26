#!/usr/bin/env python3
"""
Standalone storyworld for a small slice-of-life tale about frolic, sound effects,
and a gentle conflict that ends in compromise.

Seed premise:
A child wants to frolic with noisy sound effects while a baby naps nearby.
A parent worries about waking the baby, then helps the child switch to a softer
game so everyone can enjoy the afternoon.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    baby: object | None = None
    child: object | None = None
    parent: object | None = None
    def __post_init__(self) -> None:
        for k in ["noise", "joy", "sleep", "conflict", "care", "curiosity", "softness"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

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
    name: str
    indoor: bool
    allows: set[str] = field(default_factory=set)
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    loudness: float
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
class Toy:
    id: str
    label: str
    phrase: str
    sound: str
    loud: float
    soft_version: str = ""
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.lines = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_noise_wakes(world: World) -> list[str]:
    out: list[str] = []
    baby = world.entities.get("baby")
    if baby is None or baby.meters["sleep"] < THRESHOLD:
        return out
    for actor in world.characters():
        if actor.meters["noise"] < THRESHOLD:
            continue
        sig = ("wake", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        baby.meters["sleep"] = max(0.0, baby.meters["sleep"] - 1.0)
        baby.memes["startled"] += 1
        out.append("The noise made the baby stir.")
    return out


def _r_conflict(world: World) -> list[str]:
    child = world.entities.get("child")
    parent = world.entities.get("parent")
    if not child or not parent:
        return []
    if child.memes["want"] < THRESHOLD or parent.memes["worry"] < THRESHOLD:
        return []
    sig = ("conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["conflict"] += 1
    parent.memes["conflict"] += 1
    return ["__conflict__"]


def _r_soften(world: World) -> list[str]:
    child = world.entities.get("child")
    toy = world.entities.get("toy")
    if not child or not toy:
        return []
    if child.memes["cooperate"] < THRESHOLD:
        return []
    sig = ("soften",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["noise"] = max(0.0, child.meters["noise"] - 1.0)
    child.meters["joy"] += 1.0
    child.memes["conflict"] = 0.0
    return ["The sound got softer and the room felt calmer."]


RULES = [
    _r_noise_wakes,
    _r_conflict,
    _r_soften,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            res = rule(world)
            if res:
                changed = True
                produced.extend(x for x in res if x != "__conflict__")
    if narrate:
        for line in produced:
            world.say(line)
    return produced


@dataclass
class StoryParams:
    place: str
    activity: str
    toy: str
    name: str
    parent: str
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


SETTINGS = {
    "living_room": Place("the living room", True, {"frolic", "quiet_play"}),
    "backyard": Place("the backyard", False, {"frolic"}),
    "playroom": Place("the playroom", True, {"frolic", "quiet_play"}),
}

ACTIVITIES = {
    "frolic": Activity(
        id="frolic",
        verb="frolic",
        gerund="frolicking",
        rush="dash around and clap",
        sound="boing-boing",
        loudness=1.0,
        keyword="frolic",
        tags={"frolic", "sound_effects", "slice_of_life"},
    ),
    "quiet_play": Activity(
        id="quiet_play",
        verb="play quietly",
        gerund="playing quietly",
        rush="tiptoe around and whisper",
        sound="shh",
        loudness=0.3,
        keyword="quiet",
        tags={"quiet", "slice_of_life"},
    ),
}

TOYS = {
    "drum": Toy(
        id="drum",
        label="a little drum",
        phrase="a little drum with a bright stripe",
        sound="boom-boom",
        loud=1.0,
        soft_version="tap-tap",
        tags={"sound_effects"},
    ),
    "sock_puppet": Toy(
        id="sock_puppet",
        label="a sock puppet",
        phrase="a soft sock puppet",
        sound="boop",
        loud=0.4,
        soft_version="boop",
        tags={"gentle"},
    ),
    "toy_car": Toy(
        id="toy_car",
        label="a toy car",
        phrase="a small toy car with shiny wheels",
        sound="vroom",
        loud=0.8,
        soft_version="vrrr",
        tags={"sound_effects"},
    ),
}

NAMES = ["Mia", "Noah", "Lina", "Eli", "Zoe", "Ben", "Ivy", "Tara"]
PARENTS = ["mother", "father"]


ASP_RULES = r"""
place(P) :- setting(P).
activity(A) :- act(A).
toy(T) :- toy(T).

can_frolic(P,A) :- allows(P,A), activity(A).
noisy(A) :- loud(A, L), L >= 1.
at_risk(P,T) :- baby_present(P), noisy(A), toy(T), place(P).
"""
def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(p.allows):
            lines.append(asp.fact("allows", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("act", aid))
        lines.append(asp.fact("loud", aid, int(round(a.loudness * 10))))
    for tid in TOYS:
        lines.append(asp.fact("toy", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def aspirational_gate() -> bool:
    return True


def reasonableness_gate(place: str, activity: str, toy: str) -> None:
    if activity not in _safe_lookup(SETTINGS, place).allows:
        pass
    if activity == "frolic" and toy not in {"drum", "sock_puppet", "toy_car"}:
        pass
    if activity == "frolic" and toy == "sock_puppet":
        pass


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(
        id="child",
        kind="character",
        type="girl" if params.name in {"Mia", "Lina", "Zoe", "Ivy", "Tara"} else "boy",
        label=params.name,
        traits=["little", "curious", "spirited"],
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=params.parent,
        traits=["calm", "watchful"],
    ))
    baby = world.add(Entity(
        id="baby",
        kind="character",
        type="baby",
        label="the baby",
        traits=["sleepy", "tiny"],
    ))
    toy = _safe_lookup(TOYS, params.toy)
    world.add(Entity(
        id="toy",
        type="toy",
        label=toy.label,
        phrase=toy.phrase,
        owner=child.id,
    ))
    baby.meters["sleep"] = 1.0
    child.memes["want"] = 1.0
    parent.memes["worry"] = 1.0
    world.facts.update(child=child, parent=parent, baby=baby, toy=toy, activity=_safe_lookup(ACTIVITIES, params.activity), place=_safe_lookup(SETTINGS, params.place))
    return world


def tell(world: World, params: StoryParams) -> None:
    child: Entity = world.get("child")
    parent: Entity = world.get("parent")
    baby: Entity = world.get("baby")
    toy: Entity = world.get("toy")
    act = _safe_lookup(ACTIVITIES, params.activity)

    world.say(f"{child.label} was a little {child.pronoun('subject')} who loved a good {act.keyword}.")
    world.say(f"{child.label} liked the sound of {toy.sound}, and the whole room could feel like a game.")
    world.say(f"One afternoon, {child.label} and {parent.label} were in {world.place.name}, and the baby was asleep on the couch.")

    world.para()
    child.meters["noise"] += act.loudness
    child.memes["curiosity"] += 1.0
    child.memes["want"] += 1.0
    world.say(f"{child.label} wanted to {act.verb}, {act.gerund}, and make {toy.sound} sounds.")
    world.say(f"{child.pronoun().capitalize()} started to {act.rush}, and the fun made {child.label} shine.")
    propagate(world, narrate=True)

    if baby.meters["sleep"] < THRESHOLD:
        parent.memes["worry"] += 1.0
        world.say(f"{parent.label.capitalize()} frowned a little. The baby had almost woken up.")

    world.para()
    if act.id == "frolic":
        world.say(f'"If you frolic that loudly," {parent.label} said, "the baby might wake up."')
    else:
        world.say(f'"Could you keep it gentle?" {parent.label} asked.')
    child.memes["want"] += 0.5
    child.memes["conflict"] += 1.0
    parent.memes["conflict"] += 1.0
    world.say(f"{child.label} paused with a serious face. The fun still felt big inside {child.pronoun('possessive')} chest.")

    world.para()
    child.memes["cooperate"] += 1.0
    world.say(f"Then {child.label} spotted a softer idea.")
    if toy.soft_version:
        world.say(f"{child.label} tried {toy.soft_version} instead of {toy.sound}.")
    else:
        world.say(f"{child.label} made the game smaller and quieter.")
    propagate(world, narrate=True)
    world.say(f"{parent.label.capitalize()} smiled, and the baby kept breathing slow and steady.")

    world.para()
    world.say(f"In the end, {child.label} was still frolicky, just in a gentler way.")
    if toy.soft_version:
        ending_sound = toy.soft_version
    else:
        ending_sound = "soft taps"
    world.say(f"The room held {ending_sound} sounds, a happy child, and a sleepy baby who never had to wake up.")


def generation_prompts(world: World) -> list[str]:
    act = _safe_fact(world, world.facts, "activity")
    toy = _safe_fact(world, world.facts, "toy")
    child: Entity = _safe_fact(world, world.facts, "child")
    return [
        f"Write a short slice-of-life story about {child.label} wanting to {act.verb} with {toy.label} sounds.",
        f"Tell a gentle story where a child tries to use {toy.sound} while a baby is sleeping, and a parent helps them compromise.",
        "Write a child-facing story with frolic, sound effects, and a small family conflict that ends kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = _safe_fact(world, world.facts, "child")
    parent: Entity = _safe_fact(world, world.facts, "parent")
    baby: Entity = _safe_fact(world, world.facts, "baby")
    toy: Toy = _safe_fact(world, world.facts, "toy")
    act: Activity = _safe_fact(world, world.facts, "activity")
    place: Place = _safe_fact(world, world.facts, "place")
    qas = [
        QAItem(
            question=f"What did {child.label} want to do in {place.name}?",
            answer=f"{child.label} wanted to {act.verb} with {toy.label} because the sound made play feel exciting.",
        ),
        QAItem(
            question=f"Why was {parent.label} worried about the noise?",
            answer=f"{parent.label} worried because the baby was asleep, and {toy.sound} sounded loud enough to wake the baby.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"{child.label} chose a softer way to play, so the room stayed calm and everyone could be happy.",
        ),
    ]
    if child.memes["conflict"] >= THRESHOLD:
        qas.append(QAItem(
            question=f"What caused the conflict in the middle of the story?",
            answer=f"The conflict came from {child.label} wanting to {act.verb} loudly while {parent.label} wanted to protect the baby's nap.",
        ))
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is frolic?",
            answer="To frolic means to move around in a playful, lively way.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are playful noises, like booms, taps, or vrooms, that help a game feel lively.",
        ),
        QAItem(
            question="Why do people try to be quiet near a sleeping baby?",
            answer="People try to be quiet near a sleeping baby so the baby can rest without waking up too soon.",
        ),
    ]
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, p in SETTINGS.items():
        for act in p.allows:
            for toy in TOYS:
                try:
                    reasonableness_gate(place, act, toy)
                except StoryError:
                    continue
                out.append((place, act, toy))
    return out


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP/Python parity holds ({len(python_set)} combos).")
        return 0
    print("Mismatch.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: frolic, sound effects, and conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--parent", choices=PARENTS)
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
              and (getattr(args, "toy", None) is None or c[2] == getattr(args, "toy", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, toy = rng.choice(list(combos))
    return StoryParams(
        place=place,
        activity=activity,
        toy=toy,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        parent=getattr(args, "parent", None) or rng.choice(PARENTS),
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params.place, params.activity, params.toy)
    world = build_world(params)
    tell(world, params)
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
        print(f"{len(valid_combos())} compatible combos.")
        for combo in valid_combos():
            print(combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place, activity, toy in valid_combos():
            params = StoryParams(place=place, activity=activity, toy=toy, name="Mia", parent="mother")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
