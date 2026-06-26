#!/usr/bin/env python3
"""
Standalone storyworld: Method, Crevice, Auditorium.

A tiny fable-like simulation about a careful helper, a troublesome crevice in an
auditorium, and a humorous method for making things right.

The world is built around one small premise:
- A tidy performer or stage helper notices a crevice in the auditorium floor.
- The crevice causes a comic problem: a dropped pebble, a squeaky cart wheel,
  a missing poster, or a wobbling prop.
- The hero first tries a sensible method, then learns that the clever fix is a
  patient, cooperative one.
- The ending proves something changed in the world, not just in the wording.

The style aims to stay close to a fable: concrete, simple, moral-minded, and
lightly humorous.
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


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    obstacle: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "fox"}
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
class Setting:
    place: str = "the auditorium"
    indoors: bool = True
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
class Method:
    id: str
    name: str
    verb: str
    steps: str
    joke: str
    fix: str
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
class Trouble:
    id: str
    label: str
    phrase: str
    region: str
    mess: str
    at_risk: set[str]
    outcome: str
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
class Aid:
    id: str
    label: str
    covers: set[str]
    helps: set[str]
    prep: str
    ending: str
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
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.lines = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "auditorium": Setting(place="the auditorium", indoors=True, affords={"echo", "cleanup", "repair"}),
    "stage": Setting(place="the auditorium stage", indoors=True, affords={"echo", "repair"}),
    "balcony": Setting(place="the balcony", indoors=True, affords={"echo", "cleanup"}),
}

METHODS = {
    "bucket": Method(
        id="bucket",
        name="the bucket method",
        verb="carry water",
        steps="walk carefully, set the bucket down, and pour just enough water",
        joke="the bucket wobbled like it wanted applause",
        fix="spill less and smile more",
        tags={"water", "cleanup", "humor"},
    ),
    "plank": Method(
        id="plank",
        name="the plank method",
        verb="bridge gaps",
        steps="place a sturdy plank across the crack and test it with one brave toe",
        joke="the plank made a tiny drumroll underfoot",
        fix="cross safely without hopping like a startled rabbit",
        tags={"repair", "humor"},
    ),
    "ribbon": Method(
        id="ribbon",
        name="the ribbon method",
        verb="mark the edge",
        steps="tie bright ribbons around the danger and guide everyone around it",
        joke="the ribbons looked like a dress-up party for the floor",
        fix="warn guests before anyone giggled and stumbled",
        tags={"cleanup", "repair", "humor"},
    ),
    "silent": Method(
        id="silent",
        name="the silent method",
        verb="listen closely",
        steps="stand still, count three breaths, and hear where the trouble was echoing from",
        joke="the silence was so serious it became funny again",
        fix="find the exact spot without guessing",
        tags={"echo", "humor"},
    ),
}

TROUBLES = {
    "crevice": Trouble(
        id="crevice",
        label="crevice",
        phrase="a narrow crevice in the floor",
        region="floor",
        mess="wobble",
        at_risk={"foot", "wheel", "prop"},
        outcome="the crevice stayed open and mischievous",
        tags={"repair", "humor"},
    ),
    "gap": Trouble(
        id="gap",
        label="gap",
        phrase="a gap beside the old curtain rail",
        region="wall",
        mess="echo",
        at_risk={"voice", "banner"},
        outcome="the gap kept letting noise escape",
        tags={"echo", "humor"},
    ),
    "crack": Trouble(
        id="crack",
        label="crack",
        phrase="a crack under the front row seats",
        region="floor",
        mess="tilt",
        at_risk={"foot", "paper", "tray"},
        outcome="the crack kept making little things tip sideways",
        tags={"cleanup", "repair", "humor"},
    ),
}

AIDS = [
    Aid(
        id="plank",
        label="a short plank",
        covers={"floor"},
        helps={"repair"},
        prep="fetch a short plank and lay it across the crevice",
        ending="laid the plank across the crevice",
    ),
    Aid(
        id="sign",
        label="a bright sign",
        covers={"wall", "floor"},
        helps={"echo", "cleanup"},
        prep="set up a bright sign and point everyone around the crevice",
        ending="placed the bright sign where everyone could see it",
    ),
    Aid(
        id="ribbon",
        label="red ribbons",
        covers={"floor", "wall"},
        helps={"repair", "cleanup", "echo"},
        prep="tie red ribbons around the trouble and make the edge obvious",
        ending="tied the red ribbons around the trouble",
        plural=True,
    ),
]

MORALS = [
    "A careful method is kinder than a rushed guess.",
    "A small plan can save a big tumble.",
    "When people laugh and listen, even a crevice can be handled well.",
    "A good fix begins with noticing what is actually there.",
]

NAMES = ["Mina", "Toby", "Pip", "Luna", "Ned", "Ivy", "Otto", "Mara"]
KINDS = ["girl", "boy", "fox", "rabbit", "hen"]
TRAITS = ["careful", "cheerful", "patient", "curious", "steady", "clever"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A trouble is at risk when the method or aid touches the same region.
risk(M, T) :- method(M), trouble(T), touches(M, R), at_risk(T, R).
risk(A, T) :- aid(A), trouble(T), covers(A, R), at_risk(T, R).

% A compatible fix needs a real overlap between aid and trouble.
fix(A, T) :- aid(A), trouble(T), helps(A, K), trouble_tag(T, K), risk(A, T).

valid(Setting, Method, Trouble, Aid) :-
    setting(Setting), method(Method), trouble(Trouble), aid(Aid),
    relevant(Setting, Method, Trouble),
    fix(Aid, Trouble).

% A story is valid only if the setting allows the method and the aid can fix it.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        for t in sorted(method.tags):
            lines.append(asp.fact("method_tag", mid, t))
    for tid, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        for r in sorted(trouble.at_risk):
            lines.append(asp.fact("at_risk", tid, r))
        for t in sorted(trouble.tags):
            lines.append(asp.fact("trouble_tag", tid, t))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid.id))
        for r in sorted(aid.covers):
            lines.append(asp.fact("covers", aid.id, r))
        for k in sorted(aid.helps):
            lines.append(asp.fact("helps", aid.id, k))
    for sid, setting in SETTINGS.items():
        for mid in METHODS:
            for tid in TROUBLES:
                if sid == "auditorium" and mid in METHODS and tid in TROUBLES:
                    lines.append(asp.fact("relevant", sid, mid, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# Reasonableness gate and simulation
# ---------------------------------------------------------------------------

def relevant(setting: Setting, method: Method, trouble: Trouble) -> bool:
    if setting.place != "the auditorium" and "auditorium" not in setting.place:
        return False
    if trouble.id == "gap" and method.id != "silent":
        return False
    if trouble.id == "crevice" and method.id not in {"plank", "ribbon"}:
        return False
    if trouble.id == "crack" and method.id not in {"plank", "ribbon"}:
        return False
    return True


def compatible_aid(trouble: Trouble) -> Aid:
    for aid in AIDS:
        if trouble.tags & aid.helps:
            return aid
    pass


def predict(world: World, hero: Entity, method: Method, trouble: Trouble) -> dict:
    sim = world.copy()
    perform_method(sim, hero.id, method, trouble, narrate=False)
    return {
        "fixed": sim.facts.get("fixed", False),
        "comedy": sim.facts.get("comedy", 0),
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------

def perform_method(world: World, hero_id: str, method: Method, trouble: Trouble, narrate: bool = True) -> None:
    hero = world.get(hero_id)
    world.zone = set(trouble.at_risk)
    hero.memes["attention"] = hero.memes.get("attention", 0) + 1
    if trouble.id == "gap":
        hero.memes["echo"] = hero.memes.get("echo", 0) + 1
    if trouble.id == "crevice":
        hero.meters["care"] = hero.meters.get("care", 0) + 1

    if narrate:
        world.say(
            f"{hero.id} chose {method.name} and {method.steps}. "
            f"{method.joke.capitalize()}."
        )


def trouble_happens(world: World, hero: Entity, trouble: Trouble) -> None:
    hero.memes["concern"] = hero.memes.get("concern", 0) + 1
    world.say(
        f"In {world.setting.place}, {trouble.phrase} caused trouble. "
        f"{trouble.outcome.capitalize()}."
    )


def ask_help(world: World, hero: Entity, helper: Entity, trouble: Trouble, method: Method) -> None:
    helper.memes["willing"] = helper.memes.get("willing", 0) + 1
    world.say(
        f"{hero.id} asked {helper.id} for help, and {helper.pronoun()} "
        f"showed a better {method.name}."
    )


def resolve_with_aid(world: World, hero: Entity, trouble: Trouble, aid: Aid, method: Method) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    world.facts["fixed"] = True
    world.say(
        f"Together they {aid.prep}. After that, {hero.id} could keep using "
        f"{method.name} without any wobble."
    )
    world.say(
        f"{aid.ending}, and the auditorium looked neat again."
    )


def moral_line(world: World) -> None:
    world.say(f"Moral: {random.choice(MORALS)}")


# ---------------------------------------------------------------------------
# Tale construction
# ---------------------------------------------------------------------------

def tell(setting: Setting, method: Method, trouble: Trouble, hero_name: str, hero_kind: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_kind, traits=[trait, "little"]))
    helper = world.add(Entity(id="Helper", kind="character", type="mouse", label="the mouse janitor", traits=["busy", "kind"]))
    obstacle = world.add(Entity(id=trouble.id, type=trouble.id, label=trouble.label, phrase=trouble.phrase))

    world.say(
        f"{hero.id} was a {trait} little {hero_kind} who liked to solve problems "
        f"with a neat method."
    )
    world.say(
        f"{hero.id} worked in {setting.place} and loved the sound of a tidy plan."
    )

    world.para()
    trouble_happens(world, hero, trouble)
    if trouble.id == "gap":
        world.say(
            f"Every word bounced twice, which made the room sound like it was joking."
        )
    perform_method(world, hero.id, method, trouble)
    if trouble.id == "crevice":
        world.say(
            f"But the crevice was tricky, and {method.name} alone did not finish the job."
        )
    elif trouble.id == "gap":
        world.say(
            f"But the echo kept returning like a cat that had forgotten where it lived."
        )
    else:
        world.say(
            f"But the crack still wiggled underfoot, as if it wanted a curtain call."
        )

    world.para()
    ask_help(world, hero, helper, trouble, method)
    aid = compatible_aid(trouble)
    world.say(
        f"The mouse janitor brought {aid.label} and smiled at {hero.id}'s serious face."
    )
    resolve_with_aid(world, hero, trouble, aid, method)
    world.say(
        f"{hero.id} laughed and said that good work should be calm enough to make room for a joke."
    )
    moral_line(world)

    world.facts.update(
        hero=hero,
        helper=helper,
        trouble=obstacle,
        method=method,
        aid=aid,
        setting=setting,
        fixed=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    method = _safe_fact(world, f, "method")
    trouble = _safe_fact(world, f, "trouble")
    return [
        f"Write a short fable for children about {hero.id}, {method.name}, and {trouble.label} in an auditorium.",
        f"Tell a humorous story where a careful helper uses {method.name} to handle a {trouble.label}.",
        f"Write a simple moral story in the auditorium that starts with a troublesome {trouble.label} and ends with a clever fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    method = _safe_fact(world, f, "method")
    trouble = _safe_fact(world, f, "trouble")
    aid = _safe_fact(world, f, "aid")
    helper = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"Who was trying to solve the trouble in the auditorium?",
            answer=f"{hero.id} was trying to solve it with {method.name} and then with help from {helper.id}.",
        ),
        QAItem(
            question=f"What problem did {hero.id} notice first?",
            answer=f"{hero.id} noticed {trouble.phrase}, which was a {trouble.label} that caused trouble in the auditorium.",
        ),
        QAItem(
            question=f"What helped finish the job after the first method was not enough?",
            answer=f"{aid.label} helped finish the job, and the trouble was fixed at the end.",
        ),
        QAItem(
            question=f"What kind of story was this in the end?",
            answer=f"It was a humorous fable about thinking carefully before acting and asking for help when needed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an auditorium?",
            answer="An auditorium is a room or building made for people to gather, sit, and listen or watch a performance.",
        ),
        QAItem(
            question="What is a crevice?",
            answer="A crevice is a narrow crack or opening in something like rock or a floor.",
        ),
        QAItem(
            question="What does a method mean?",
            answer="A method is a planned way of doing something, usually step by step.",
        ),
        QAItem(
            question="Why can humor help in a hard job?",
            answer="Humor can help because it keeps people calm, helps them work together, and makes a problem feel less frightening.",
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
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "character" and e.traits:
            bits.append(f"traits={e.traits}")
        out.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    out.append(f"  facts={world.facts}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Params and CLI
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    method: str
    trouble: str
    name: str
    kind: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Humorous fable storyworld: method, crevice, auditorium.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=KINDS)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    method = getattr(args, "method", None) or rng.choice(list(METHODS))
    trouble = getattr(args, "trouble", None) or rng.choice(list(TROUBLES))
    if not relevant(_safe_lookup(SETTINGS, setting), _safe_lookup(METHODS, method), _safe_lookup(TROUBLES, trouble)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    kind = getattr(args, "kind", None) or rng.choice(KINDS)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, method=method, trouble=trouble, name=name, kind=kind, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(METHODS, params.method),
        _safe_lookup(TROUBLES, params.trouble),
        params.name,
        params.kind,
        params.trait,
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


def explain_mismatch() -> str:
    py = {(s.setting, s.method, s.trouble) for s in CURATED}
    return f"Python curated set has {len(py)} items; ASP mode is available for parity checks."


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid/4.")
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set()
    for sid in SETTINGS:
        for mid in METHODS:
            for tid in TROUBLES:
                if relevant(_safe_lookup(SETTINGS, sid), _safe_lookup(METHODS, mid), _safe_lookup(TROUBLES, tid)):
                    for aid in AIDS:
                        if _safe_lookup(TROUBLES, tid).tags & aid.helps:
                            python_set.add((sid, mid, tid, aid.id))
    if clingo_set == python_set:
        print(f"OK: ASP and Python agree on {len(clingo_set)} valid combinations.")
        return 0
    print("MISMATCH between ASP and Python:")
    if clingo_set - python_set:
        print("  only in ASP:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in Python:", sorted(python_set - clingo_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(setting="auditorium", method="plank", trouble="crevice", name="Mina", kind="girl", trait="careful"),
    StoryParams(setting="stage", method="silent", trouble="gap", name="Pip", kind="rabbit", trait="curious"),
    StoryParams(setting="auditorium", method="ribbon", trouble="crack", name="Toby", kind="boy", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid_combos()
        print(f"{len(vals)} compatible combinations:")
        for row in vals:
            print("  ", row)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.method} / {p.trouble} / {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
