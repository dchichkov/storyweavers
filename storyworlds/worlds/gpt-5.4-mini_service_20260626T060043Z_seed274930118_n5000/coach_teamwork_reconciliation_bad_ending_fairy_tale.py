#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a coach, a team that can work together, and
a reconciliation that may fail if the wrong choice is made.

Premise:
- A coach trains a little team in a storybook valley.
- The team needs to cooperate to lift, carry, and cross a difficult place.
- A quarrel can be soothed by a peace offering, but this world deliberately
  allows a bad ending when the apology is refused or the task goes wrong.

The simulated state tracks:
- physical meters: load, distance, wear, mud, damage
- emotional memes: trust, worry, anger, hope, shame, pride

This script follows the Storyweavers contract: it is standalone, uses typed
entities with meters and memes, provides QA, trace, JSON, and inline ASP parity
checks.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World model
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    companion_of: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    coach: object | None = None
    t: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "queen", "princess", "maid", "woman"}
        male = {"boy", "father", "dad", "king", "prince", "man", "coach"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def rel(self) -> str:
        if self.label:
            return self.label
        return self.type
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
    name: str
    mood: str
    hazard: str
    requires: set[str] = field(default_factory=set)
    weather: str = ""
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
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    challenge: str
    risk: str
    harm: str
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
class Remedy:
    id: str
    label: str
    prep: str
    action: str
    solves: set[str] = field(default_factory=set)
    needs: set[str] = field(default_factory=set)
    success_image: str = ""
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
    def __init__(self, place: Place, task: Task):
        self.place = place
        self.task = task
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        w = World(self.place, self.task)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "meadow": Place(name="the meadow", mood="bright", hazard="a flooded brook", requires={"rope"}, weather="rainy"),
    "courtyard": Place(name="the castle courtyard", mood="quiet", hazard="a cracked bridge", requires={"plank"}, weather="windy"),
    "woods": Place(name="the woods", mood="shadowy", hazard="a thorn gate", requires={"gloves"}, weather="misty"),
}

TASKS = {
    "bridge": Task(
        id="bridge",
        verb="cross the bridge",
        gerund="crossing the bridge",
        rush="hurry across the bridge",
        challenge="the bridge sagged over the water",
        risk="someone would slip into the stream",
        harm="wet and ashamed",
        tags={"bridge", "rope"},
    ),
    "harvest": Task(
        id="harvest",
        verb="gather the apples",
        gerund="gathering the apples",
        rush="climb for the apples",
        challenge="the branches were high and slick",
        risk="the baskets would fall and bruise the fruit",
        harm="smashed and muddy",
        tags={"harvest", "fruit"},
    ),
    "gate": Task(
        id="gate",
        verb="open the thorn gate",
        gerund="opening the thorn gate",
        rush="push at the thorn gate",
        challenge="the thorn gate would scratch unprotected hands",
        risk="the team would be slowed and sore",
        harm="scratched and stung",
        tags={"gate", "thorns"},
    ),
}

REMEDIES = [
    Remedy(
        id="rope",
        label="a strong rope",
        prep="tie the rope to the sturdy post",
        action="pull together",
        solves={"bridge"},
        needs={"bridge"},
        success_image="the team could cross one by one",
    ),
    Remedy(
        id="plank",
        label="a wide plank",
        prep="lay the plank across the crack",
        action="carry together",
        solves={"bridge"},
        needs={"bridge"},
        success_image="the bridge became a safe little path",
    ),
    Remedy(
        id="basket",
        label="a shared basket",
        prep="share the basket and take turns",
        action="gather together",
        solves={"harvest"},
        needs={"harvest"},
        success_image="the apples stayed neat in the basket",
    ),
    Remedy(
        id="gloves",
        label="soft gloves",
        prep="put on the soft gloves",
        action="hold together",
        solves={"gate"},
        needs={"gate"},
        success_image="the thorns could not sting their hands",
    ),
]

GIRL_NAMES = ["Ella", "Mina", "Iris", "Mara", "Lina", "Faye"]
BOY_NAMES = ["Owen", "Pip", "Theo", "Rowan", "Nico", "Bram"]
TEAM_ROLES = ["fox", "goat", "sparrow", "mouse", "hare", "badger"]
TRAITS = ["brave", "gentle", "earnest", "stubborn", "kind", "curious"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    task: str
    coach_name: str
    coach_type: str
    team_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
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


def coach_title(coach_type: str) -> str:
    return {"woman": "coach", "man": "coach", "queen": "coach-queen", "king": "coach-king"}.get(coach_type, "coach")


def team_phrase(team_name: str) -> str:
    return f"the {team_name}"


def select_remedy(task: Task) -> Optional[Remedy]:
    for remedy in REMEDIES:
        if task.id in remedy.solves:
            return remedy
    return None


def predict(world: World, use_remedy: bool) -> dict:
    sim = world.copy()
    task = sim.task
    coach = sim.get("coach")
    team = [e for e in sim.entities.values() if e.kind == "teammate"]
    if use_remedy:
        coach.memes["hope"] = coach.memes.get("hope", 0) + 1
        for t in team:
            t.memes["trust"] = t.memes.get("trust", 0) + 1
        return {"safe": True, "reconciled": True}
    for t in team:
        t.meters["damage"] = t.meters.get("damage", 0) + 1
    coach.memes["worry"] = coach.memes.get("worry", 0) + 1
    return {"safe": False, "reconciled": False, "harm": task.harm}


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def introduce(world: World, coach: Entity, team_name: str) -> None:
    world.say(
        f"Once in {world.place.name}, there lived a {coach_title(coach.type)} named {coach.id} "
        f"who kindly led {team_phrase(team_name)}."
    )
    world.say(
        f"{coach.pronoun().capitalize()} believed a good team could do hard things if they listened, "
        f"shared, and kept their hearts in step."
    )


def show_task(world: World, coach: Entity, team_name: str) -> None:
    task = world.task
    world.say(
        f"One day, {coach.id} brought {team_phrase(team_name)} to {world.place.name} because they needed to {task.verb}."
    )
    world.say(
        f"{task.challenge.capitalize()}, and {task.risk}."
    )


def quarrel(world: World, coach: Entity, team_name: str) -> None:
    coach.memes["worry"] = coach.memes.get("worry", 0) + 1
    coach.memes["hope"] = coach.memes.get("hope", 0) + 1
    world.say(
        f"But the little team began to bicker, and their voices tangled like brambles."
    )
    world.say(
        f"{coach.id} lifted a hand and said, \"We must work as one, or this will end badly.\""
    )


def apology_offer(world: World, coach: Entity, team_name: str) -> None:
    coach.memes["hope"] = coach.memes.get("hope", 0) + 1
    world.say(
        f"Then {coach.id} chose a gentle way to mend the mood and asked the team to breathe together."
    )
    world.say(
        f"\"If we can reconcile,\" {coach.pronoun().capitalize()} said, \"we can still finish the task.\""
    )


def attempt_task(world: World, coach: Entity, team_name: str, remedy: Optional[Remedy]) -> None:
    task = world.task
    if remedy:
        world.say(
            f"The team tried a plan with {remedy.label}: {remedy.prep}, and then they would {remedy.action}."
        )
        world.say(
            f"With that help, the work felt steadier."
        )
        world.facts["used_remedy"] = remedy.id
    else:
        world.say(
            f"Without a shared plan, they rushed at the job anyway."
        )
        world.say(
            f"{task.harm.capitalize()}."
        )
        world.facts["used_remedy"] = None


def resolve(world: World, coach: Entity, team_name: str, remedy: Optional[Remedy]) -> None:
    team = [e for e in world.entities.values() if e.kind == "teammate"]
    if remedy is None:
        coach.memes["worry"] = coach.memes.get("worry", 0) + 2
        coach.memes["shame"] = coach.memes.get("shame", 0) + 1
        for t in team:
            t.memes["trust"] = max(0.0, t.memes.get("trust", 0) - 1)
            t.meters["damage"] = t.meters.get("damage", 0) + 1
        world.say(
            f"No one listened in time, and the chance to reconcile slipped away."
        )
        world.say(
            f"In the end, the team went home sad, the task was unfinished, and {world.place.hazard} still waited in the path."
        )
        world.facts["ending"] = "bad"
        return

    coach.memes["trust"] = coach.memes.get("trust", 0) + 1
    coach.memes["hope"] = coach.memes.get("hope", 0) + 1
    for t in team:
        t.memes["trust"] = t.memes.get("trust", 0) + 1
        t.memes["pride"] = t.memes.get("pride", 0) + 1
    world.say(
        f"The team finally reconciled and followed the plan together."
    )
    world.say(
        f"But even then, the work turned out too hard, and the day still ended badly."
    )
    world.say(
        f"{coach.id} watched the last brave step and knew the lesson had been learned too late."
    )
    world.facts["ending"] = "bad"
    world.facts["remedy_name"] = remedy.label


def tell(place: Place, task: Task, coach_name: str, coach_type: str, team_name: str) -> World:
    world = World(place, task)
    coach = world.add(Entity(id=coach_name, kind="character", type=coach_type, label=coach_title(coach_type)))
    teammates = []
    for i, role in enumerate(TEAM_ROLES[:3]):
        t = world.add(Entity(
            id=f"team{i+1}",
            kind="teammate",
            type=role,
            label=role,
            traits=[_safe_lookup(TRAITS, i % len(TRAITS))],
            owner=coach.id,
            memes={"trust": 1.0, "worry": 0.0, "anger": 0.0, "hope": 0.0, "pride": 0.0},
            meters={"damage": 0.0},
        ))
        teammates.append(t)
    coach.memes.update({"hope": 1.0, "worry": 0.0, "trust": 1.0, "pride": 0.0, "shame": 0.0})
    world.facts.update(coach=coach, teammates=teammates, team_name=team_name)

    introduce(world, coach, team_name)
    world.para()
    show_task(world, coach, team_name)
    quarrel(world, coach, team_name)
    apology_offer(world, coach, team_name)
    world.para()
    remedy = select_remedy(task)
    if remedy:
        world.facts["predict"] = predict(world, use_remedy=True)
    attempt_task(world, coach, team_name, remedy)
    world.para()
    resolve(world, coach, team_name, remedy)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    coach: Entity = _safe_fact(world, world.facts, "coach")
    team_name = _safe_fact(world, world.facts, "team_name")
    task = world.task
    return [
        f'Write a fairy tale about a coach and {team_phrase(team_name)} who try to {task.verb}.',
        f"Tell a gentle story where {coach.id} teaches teamwork, then reconciliation, but the ending still turns bad.",
        f'Create a short fairy tale that includes a coach, a quarrel, a peace offering, and the words "{task.id}" and "coach".',
    ]


def story_qa(world: World) -> list[QAItem]:
    coach: Entity = _safe_fact(world, world.facts, "coach")
    task = world.task
    team_name = _safe_fact(world, world.facts, "team_name")
    remedy: Optional[Remedy] = None
    if world.facts.get("used_remedy"):
        remedy = next((r for r in REMEDIES if r.label == world.facts["used_remedy"]), None)
    qas = [
        QAItem(
            question=f"Who guided {team_phrase(team_name)} in the story?",
            answer=f"The {coach_title(coach.type)} named {coach.id} guided them through the lesson."
        ),
        QAItem(
            question=f"What did the team need to do in {world.place.name}?",
            answer=f"They needed to {task.verb}, but the task was hard because {task.challenge}."
        ),
        QAItem(
            question="Why did the coach ask for teamwork?",
            answer="Because the job was too hard for one small traveler alone, and everyone needed to help in the same direction."
        ),
    ]
    if remedy:
        qas.append(
            QAItem(
                question=f"What helped the team try to {task.verb} together?",
                answer=f"{remedy.label.capitalize()} helped. The coach told them to {remedy.prep}, and that gave them a shared plan."
            )
        )
    qas.append(
        QAItem(
            question="How did the story end?",
            answer="The team did not get a happy ending; even after the reconciliation, the day still ended badly."
        )
    )
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a coach?",
            answer="A coach is a guide who teaches, encourages, and helps a team work together."
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means different helpers do their jobs together so they can finish something hard."
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace after a quarrel so people can be kind again."
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is when the problem is not truly solved, and things finish in a sad or difficult way."
        ),
    ]


# ---------------------------------------------------------------------------
# Reasonability and ASP
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for task_id, task in TASKS.items():
            if task_id in place.requires or task.id in {"bridge", "gate", "harvest"}:
                combos.append((place_id, task_id))
    return combos


ASP_RULES = r"""
place(P) :- setting(P).
task(T) :- challenge(T, _).

requires_fix(P, T) :- place(P), task(T), hazard_for(P, T).
valid(P, T) :- requires_fix(P, T), remedy_for(T, R).

#show valid/2.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("hazard_for", pid, p.requires.pop() if p.requires else "none"))
    for tid, t in TASKS.items():
        lines.append(asp.fact("challenge", tid, t.challenge))
    for r in REMEDIES:
        for s in r.solves:
            lines.append(asp.fact("remedy_for", s, r.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in asp:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about a coach, teamwork, reconciliation, and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["woman", "man"])
    ap.add_argument("--team-name", choices=["little band", "small team", "flower crew", "valley team", "moss troop"])
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
    if getattr(args, "place", None) and getattr(args, "task", None) and (getattr(args, "place", None), getattr(args, "task", None)) not in combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    valid = [c for c in combos if (not getattr(args, "place", None) or c[0] == getattr(args, "place", None)) and (not getattr(args, "task", None) or c[1] == getattr(args, "task", None))]
    if not valid:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task = rng.choice(sorted(valid))
    gender = getattr(args, "gender", None) or rng.choice(["woman", "man"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "woman" else BOY_NAMES)
    team_name = getattr(args, "team_name", None) or rng.choice(["little band", "small team", "flower crew", "valley team", "moss troop"])
    return StoryParams(place=place, task=task, coach_name=name, coach_type=gender, team_name=team_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(TASKS, params.task), params.coach_name, params.coach_type, params.team_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(parts)}")
    lines.append(f"  place={world.place.name}")
    lines.append(f"  task={world.task.id}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="meadow", task="bridge", coach_name="Mina", coach_type="woman", team_name="flower crew"),
    StoryParams(place="courtyard", task="bridge", coach_name="Owen", coach_type="man", team_name="moss troop"),
    StoryParams(place="woods", task="gate", coach_name="Faye", coach_type="woman", team_name="little band"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, task) combos:\n")
        for place, task in combos:
            print(f"  {place:10} {task}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.coach_name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
