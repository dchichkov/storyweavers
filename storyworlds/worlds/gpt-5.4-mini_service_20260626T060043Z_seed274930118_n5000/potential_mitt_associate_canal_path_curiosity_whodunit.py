#!/usr/bin/env python3
"""
A tiny whodunit-style storyworld set along a canal path.

Premise:
- A curious child notices something odd on the canal path.
- A mitt may be missing, misplaced, or found as a clue.
- An associate helps follow the trail and solve the little mystery.

The story is generated from a simulated world model, not a fixed paragraph.
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
# World model
# ---------------------------------------------------------------------------


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
    carried_by: Optional[str] = None
    found_at: str = ""
    plural: bool = False
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    associate: object | None = None
    child: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    place: str = "the canal path"
    detail: str = "The canal water moved quietly beside the path."
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
    clue: str
    risk: str
    twist: str
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
class ObjectThing:
    id: str
    label: str
    phrase: str
    category: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    mitt_ent: object | None = None
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.objects: dict[str, ObjectThing] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_obj(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.id] = obj
        return obj

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def people(self) -> list[Entity]:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.objects = copy.deepcopy(self.objects)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "canal_path": Setting(
        place="the canal path",
        detail="The canal water moved quietly beside the path, and long reeds brushed the edge.",
        affords={"search", "follow", "inspect"},
    )
}

ACTIVITIES = {
    "search": Activity(
        id="search",
        verb="search the canal path",
        gerund="searching the canal path",
        clue="a small mark in the dust",
        risk="a missing mitt could be tracked",
        twist="the clue pointed not to loss, but to a helpful hand",
        keyword="potential",
        tags={"curiosity", "whodunit"},
    ),
    "follow": Activity(
        id="follow",
        verb="follow the clue",
        gerund="following the clue",
        clue="fresh footprints by the reeds",
        risk="the trail might vanish at the bend",
        twist="the trail ended where someone had paused to help",
        keyword="mitt",
        tags={"curiosity", "whodunit"},
    ),
    "inspect": Activity(
        id="inspect",
        verb="inspect the waterline",
        gerund="inspecting the waterline",
        clue="a mitt loop snagged on a reed",
        risk="the item might look lost forever",
        twist="it turned out to have been tucked aside on purpose",
        keyword="associate",
        tags={"curiosity", "whodunit"},
    ),
}

MITTS = {
    "red_mitt": ObjectThing(
        id="red_mitt",
        label="mitt",
        phrase="a red mitt with a soft cuff",
        category="mitt",
    ),
    "blue_mitt": ObjectThing(
        id="blue_mitt",
        label="mitt",
        phrase="a blue mitt with a stitched thumb",
        category="mitt",
    ),
}

NAMES = ["Nora", "Milo", "Iris", "Theo", "Lena", "Owen", "Clara", "Eli"]
ASSOCIATES = ["neighbor", "friend", "assistant", "older cousin"]
TRAITS = ["curious", "careful", "quiet", "sharp-eyed"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    activity: str
    mitt: str
    name: str
    associate: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
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
        for act_id, act in ACTIVITIES.items():
            for mitt_id in MITTS:
                if place == "canal_path" and "whodunit" in act.tags:
                    combos.append((place, act_id, mitt_id))
    return combos


def explain_rejection() -> str:
    return "(No story: this world only makes sense as a small mystery on the canal path.)"


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def predict(world: World, actor: Entity, activity: Activity, mitt: Entity) -> dict:
    sim = world.copy()
    sim.get(actor.id).memes["curiosity"] = sim.get(actor.id).memes.get("curiosity", 0) + 1
    sim.objects[mitt.id].meters["significance"] = 1
    return {
        "clue_seen": True,
        "mitt_mysterious": True,
    }


def intro(world: World, child: Entity, associate: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.traits[0]} child who noticed tiny details."
    )
    world.say(
        f"{child.pronoun().capitalize()} liked walking along {world.setting.place} with "
        f"{associate.pronoun('possessive')} {associate.type}."
    )


def inciting(world: World, child: Entity, mitt: Entity, activity: Activity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    mitt.meters["lostness"] = 1
    world.say(
        f"One day, {child.id} saw {mitt.phrase} near the reeds."
    )
    world.say(
        f"That felt like a clue, so {child.id} wanted to {activity.verb}."
    )


def tension(world: World, child: Entity, associate: Entity, activity: Activity, mitt: Entity) -> None:
    child.memes["wonder"] = child.memes.get("wonder", 0) + 1
    world.say(
        f"{child.id} wondered if the mitt meant something important, but the trail was thin."
    )
    world.say(
        f"{associate.id} said the answer might be hiding in plain sight, if they looked slowly."
    )


def solve(world: World, child: Entity, associate: Entity, mitt: Entity, activity: Activity) -> None:
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    associate.memes["helpfulness"] = associate.memes.get("helpfulness", 0) + 1
    mitt.meters["found"] = 1
    mitt.carried_by = child.id
    mitt.found_at = world.setting.place
    world.say(
        f"They found the truth at last: {mitt.label} had been set aside by a helpful associate so it would not blow into the canal."
    )
    world.say(
        f"{child.id} smiled, because the mystery was solved and {mitt.pronoun('possessive')} mitt was safe again."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.
place(canal_path).
setting_place(canal_path, canal_path).
activity(search).
activity(follow).
activity(inspect).
mitt(red_mitt).
mitt(blue_mitt).

valid(P,A,M) :- place(P), activity(A), mitt(M).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "canal_path")]
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for m in MITTS:
        lines.append(asp.fact("mitt", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def story_qa(world: World) -> list[QAItem]:
    child = _safe_fact(world, world.facts, "child")
    associate = _safe_fact(world, world.facts, "associate")
    mitt = _safe_fact(world, world.facts, "mitt")
    activity = _safe_fact(world, world.facts, "activity")
    return [
        QAItem(
            question=f"What did {child.id} notice on {world.setting.place}?",
            answer=f"{child.id} noticed {mitt.phrase}. It looked like a clue and made {child.id} curious.",
        ),
        QAItem(
            question=f"Who helped {child.id} with the little mystery?",
            answer=f"{associate.id} helped by looking carefully and pointing out where the trail really led.",
        ),
        QAItem(
            question=f"What was the answer to the mystery about the {mitt.label}?",
            answer=f"The {mitt.label} had been set aside by a helpful associate so it would stay safe near {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {child.id} want to {activity.verb}?",
            answer=f"Because the {mitt.label} seemed like an important clue, and {child.id} had a lot of curiosity.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is the canal path?",
            answer="The canal path is a narrow walkway beside the canal where someone can stroll, look, and notice clues.",
        ),
        QAItem(
            question="What is a mitt?",
            answer="A mitt is a soft hand covering, often worn to keep hands warm or to protect them while outside.",
        ),
        QAItem(
            question="What does curiosity do in a mystery?",
            answer="Curiosity makes someone look closer, ask questions, and follow small clues until the answer appears.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short whodunit-style story for children set on a canal path, using the word "potential".',
        f"Tell a gentle mystery where a curious child and an associate solve a clue about a mitt on {world.setting.place}.",
        'Write a child-friendly detective story where the clue seems important at first, but the answer is kind.',
    ]


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    activity = _safe_lookup(ACTIVITIES, params.activity)
    mitt = _safe_lookup(MITTS, params.mitt)

    world = World(setting)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        traits=[params.trait, "curious"],
    ))
    associate = world.add(Entity(
        id=params.associate,
        kind="character",
        type="associate",
        traits=["helpful", "careful"],
    ))
    mitt_ent = world.add_obj(ObjectThing(
        id=mitt.id,
        label=mitt.label,
        phrase=mitt.phrase,
        category=mitt.category,
    ))

    intro(world, child, associate)
    world.para()
    inciting(world, child, mitt_ent, activity)
    tension(world, child, associate, activity, mitt_ent)
    world.para()
    solve(world, child, associate, mitt_ent, activity)

    world.facts = {
        "child": child,
        "associate": associate,
        "mitt": mitt_ent,
        "activity": activity,
    }

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        lines.append(f"  {e.id:10} ({e.type}) meters={meters} memes={memes}")
    for o in world.objects.values():
        meters = {k: v for k, v in o.meters.items() if v}
        lines.append(f"  {o.id:10} (object) meters={meters} carried_by={o.carried_by} found_at={o.found_at}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld on the canal path.")
    ap.add_argument("--setting", choices=SETTINGS.keys(), default="canal_path")
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--mitt", choices=MITTS.keys())
    ap.add_argument("--name")
    ap.add_argument("--associate", choices=ASSOCIATES)
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
    combos = valid_combos()
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    activity = getattr(args, "activity", None) or rng.choice(sorted(ACTIVITIES))
    mitt = getattr(args, "mitt", None) or rng.choice(sorted(MITTS))
    setting = getattr(args, "setting", None)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    associate = getattr(args, "associate", None) or rng.choice(ASSOCIATES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)

    if (setting, activity, mitt) not in combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    return StoryParams(
        setting=setting,
        activity=activity,
        mitt=mitt,
        name=name,
        associate=associate,
        trait=trait,
    )


CURATED = [
    StoryParams(setting="canal_path", activity="search", mitt="red_mitt", name="Nora", associate="neighbor", trait="curious"),
    StoryParams(setting="canal_path", activity="follow", mitt="blue_mitt", name="Milo", associate="assistant", trait="careful"),
    StoryParams(setting="canal_path", activity="inspect", mitt="red_mitt", name="Iris", associate="friend", trait="sharp-eyed"),
]


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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
            header = f"### {p.name}: {p.activity} on {p.setting} (mitt: {p.mitt})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
