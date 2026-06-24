#!/usr/bin/env python3
"""
A small slice-of-life storyworld about something that seems easy at first,
but needs caution and repetition before it goes well.

The child wants to carry a drink across the room. It seems simple, but the cup
can wobble, the floor can be slippery, and the lesson is to slow down, use a
tray or two hands, and try again carefully until the job is done.
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

    chosen: object | None = None
    hero: object | None = None
    obj: object | None = None
    parent: object | None = None
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
class Setting:
    place: str = "the kitchen"
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
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    mishap: str
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
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)
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


@dataclass
class StoryParams:
    place: str
    task: str
    object_: str
    name: str
    gender: str
    parent: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting("the kitchen", {"juice", "soup"}),
    "hallway": Setting("the hallway", {"juice", "soup"}),
    "porch": Setting("the porch", {"juice"}),
}

TASKS = {
    "juice": Task(
        id="juice",
        verb="carry the juice",
        gerund="carrying the juice",
        rush="hurry across the room with the cup",
        risk="the cup could wobble and spill",
        mishap="spilled the juice",
        tags={"drink", "spill", "careful"},
    ),
    "soup": Task(
        id="soup",
        verb="bring the soup",
        gerund="bringing the soup",
        rush="dash to the table with the bowl",
        risk="the bowl could slosh and splash",
        mishap="slopped the soup",
        tags={"soup", "spill", "careful"},
    ),
}

OBJECTS = {
    "cup": {"label": "a small cup", "phrase": "a small cup of juice", "plural": False},
    "glass": {"label": "a tall glass", "phrase": "a tall glass of juice", "plural": False},
    "bowl": {"label": "a bowl", "phrase": "a warm bowl of soup", "plural": False},
}

GEAR = [
    Gear(
        id="tray",
        label="a little tray",
        prep="set the cup on a little tray",
        tail="carried the tray slowly with both hands",
        helps={"juice", "soup"},
    ),
    Gear(
        id="two_hands",
        label="two careful hands",
        prep="hold the cup with two careful hands",
        tail="walked slowly and watched the cup",
        helps={"juice", "soup"},
    ),
    Gear(
        id="lid",
        label="a lid",
        prep="put a lid on the cup",
        tail="carried it without sloshing",
        helps={"juice"},
    ),
]

GIRL_NAMES = ["Mia", "Nora", "Ava", "Lila", "Zoe", "Ella"]
BOY_NAMES = ["Theo", "Ben", "Leo", "Max", "Noah", "Finn"]
TRAITS = ["curious", "careful", "cheerful", "playful", "patient", "spirited"]


# ---------------------------------------------------------------------------
# Prose helpers
# ---------------------------------------------------------------------------

def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def setting_line(setting: Setting, task: Task) -> str:
    if setting.place == "the hallway":
        return "The hallway looked long and easy to cross, but the floor had a little shine to it."
    if setting.place == "the porch":
        return "The porch was bright and breezy, and the steps seemed a little tricky."
    return "The kitchen was warm and busy, with smooth tiles under small feet."


def hero_intro(hero: Entity) -> str:
    trait = next((t for t in hero.memes.get("traits", []) if t != "little"), "careful")
    return f"{hero.id} was a little {trait} {hero.type} who liked simple jobs that seemed easy."


def predict_spill(world: World, task: Task, object_id: str, gear_id: Optional[str] = None) -> bool:
    sim = world.copy()
    obj = sim.get(object_id)
    obj.meters["spill"] = 0
    if gear_id:
        gear = sim.get(gear_id)
        sim.fired.add(("gear", gear.id))
        obj.meters["protected"] = 1
    if task.id == "juice":
        obj.meters["spill"] += 1 if not gear_id else 0
    else:
        obj.meters["spill"] += 1 if not gear_id else 0
    return obj.meters["spill"] >= THRESHOLD


# ---------------------------------------------------------------------------
# Plot actions
# ---------------------------------------------------------------------------

def start(world: World, hero: Entity, parent: Entity, task: Task, obj: Entity) -> None:
    world.say(hero_intro(hero))
    world.say(f"{hero.pronoun().capitalize()} loved {task.gerund}, because it seemed like a tiny grown-up job.")
    world.say(f"One afternoon, {hero.id}'s {parent.label} gave {hero.pronoun('object')} {obj.phrase}.")
    world.say(f"{hero.id} smiled at {obj.phrase} and said {task.risk + '.'}")


def caution(world: World, hero: Entity, parent: Entity, task: Task, obj: Entity) -> None:
    world.para()
    world.say(setting_line(world.setting, task))
    world.say(f"{hero.id} tried to {task.verb}, but {hero.pronoun('possessive')} {parent.label} held up a hand.")
    world.say(f'"Slow down," {parent.id} said. "If you rush, {task.risk}."')


def repeat_attempt(world: World, hero: Entity, task: Task, obj: Entity) -> None:
    hero.memes["wants"] = hero.memes.get("wants", 0) + 1
    world.say(f"{hero.id} nodded, but the cup still seemed lighter than the warning.")
    world.say(f"{hero.pronoun().capitalize()} tried again and started to {task.rush}.")
    obj.meters["wobble"] = obj.meters.get("wobble", 0) + 1
    if obj.meters["wobble"] >= THRESHOLD:
        obj.meters["spill"] = obj.meters.get("spill", 0) + 1
        world.say(f"The cup wobbled, and {hero.id} {task.mishap}.")
        hero.memes["oops"] = hero.memes.get("oops", 0) + 1


def offer_fix(world: World, parent: Entity, hero: Entity, task: Task, obj: Entity) -> Optional[Gear]:
    gear = next((g for g in GEAR if task.id in g.helps), None)
    if gear is None:
        return None
    if predict_spill(world, task, obj.id, gear.id):
        return None
    chosen = world.add(Entity(id=gear.id, type="gear", label=gear.label, plural=gear.plural))
    hero.memes["listening"] = hero.memes.get("listening", 0) + 1
    world.say(f"Then {hero.pronoun('possessive')} {parent.label} smiled and offered {gear.label}.")
    world.say(f'"How about you {gear.prep}?" {parent.id} asked.')
    return chosen


def resolve(world: World, hero: Entity, parent: Entity, task: Task, obj: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["lesson_learned"] = hero.memes.get("lesson_learned", 0) + 1
    obj.meters["spill"] = 0
    world.para()
    world.say(f"{hero.id} tried once more, this time with {gear.label}.")
    world.say(f"{hero.id} {gear.tail}, and the drink stayed safe.")
    world.say(f"In the end, {hero.id} finished {task.gerund} without a mess, and the room felt calm again.")
    world.say(f"{hero.id} looked proud, because the job that once seemed easy had taught {hero.pronoun('object')} to be careful.")


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def tell(setting: Setting, task: Task, object_cfg: dict, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name, memes={"traits": [trait, "little"]}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    obj = world.add(Entity(id="Object", type=object_cfg["label"], label=object_cfg["label"], phrase=object_cfg["phrase"], plural=object_cfg["plural"]))

    start(world, hero, parent, task, obj)
    caution(world, hero, parent, task, obj)
    repeat_attempt(world, hero, task, obj)
    gear = offer_fix(world, parent, hero, task, obj)
    if gear is not None:
        resolve(world, hero, parent, task, obj, gear)
    else:
        world.para()
        world.say(f"{hero.id} paused, listened, and tried a slower way.")
        world.say(f"This time, the careful steps worked, and {task.gerund} felt better than rushing.")

    world.facts = {
        "hero": hero,
        "parent": parent,
        "object": obj,
        "task": task,
        "gear": gear,
        "setting": setting,
        "resolved": True,
    }
    return world


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            for object_id in OBJECTS:
                combos.append((place, task_id, object_id))
    return combos


def explain_rejection(setting: Setting, task: Task, object_id: str) -> str:
    return f"(No story: {task.gerund} does not fit {object_id} in {setting.place}.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
task_place(P,T) :- affords(P,T).
valid(P,T,O) :- task_place(P,T), object(O).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
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
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    task = _safe_fact(world, f, "task")
    obj = _safe_fact(world, f, "object")
    return [
        f'Write a gentle slice-of-life story where a child named {hero.id} wants to {task.verb}, but the {obj.label} seems easy and still needs caution.',
        f"Tell a short story about a child, a repeated mistake, and a lesson learned while {task.gerund}.",
        f'Write a child-friendly story that includes the word "seem" and ends with a careful success.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    task = _safe_fact(world, f, "task")
    obj = _safe_fact(world, f, "object")
    gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"What did {hero.id} want to do at the start of the story?",
            answer=f"{hero.id} wanted to {task.verb}. It seemed like an easy job, but it needed patience.",
        ),
        QAItem(
            question=f"Why did {parent.id} warn {hero.id} to slow down?",
            answer=f"{parent.id} warned {hero.id} because {task.risk}, and a rush could make a mess.",
        ),
        QAItem(
            question=f"What happened when {hero.id} tried again too quickly?",
            answer=f"The cup wobbled and {hero.id} {task.mishap}. That was the cautionary moment in the story.",
        ),
        QAItem(
            question=f"How did {hero.id} finish the job after listening?",
            answer=(
                f"{hero.id} used {gear.label if gear else 'a slower, careful plan'} and finished {task.gerund} without spilling. "
                f"It became a lesson learned about taking time."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when something seems easy?",
            answer="When something seems easy, it looks simple at first, but it may still need care and practice.",
        ),
        QAItem(
            question="Why do people use a tray for carrying drinks?",
            answer="People use a tray so a cup or bowl stays steadier and is less likely to spill.",
        ),
        QAItem(
            question="Why is repeating a careful step useful?",
            answer="Repeating a careful step helps you learn the right way to do a job, so you make fewer mistakes.",
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        out.append(f"  {e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="kitchen", task="juice", object_="cup", name="Mia", gender="girl", parent="mother", trait="careful"),
    StoryParams(place="hallway", task="soup", object_="bowl", name="Theo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="porch", task="juice", object_="glass", name="Ava", gender="girl", parent="mother", trait="playful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about caution, repetition, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--task", choices=TASKS.keys())
    ap.add_argument("--object", dest="object_", choices=OBJECTS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "object_", None) is None or c[2] == getattr(args, "object_", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, object_ = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, task=task, object_=object_, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(OBJECTS, params.object_), params.name, params.gender, params.parent, params.trait)
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

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:\n")
        for p, t, o in vals:
            print(f"  {p:9} {t:8} {o}")
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
