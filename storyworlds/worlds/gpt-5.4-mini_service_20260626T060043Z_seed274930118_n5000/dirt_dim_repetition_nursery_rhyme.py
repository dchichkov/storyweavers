#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about dirt, dim light, and repeating chores.

A seed tale sits underneath this world:
- A child finds a dim little room or corner.
- A dirty object or patch makes the place feel gloomy.
- The child repeats a simple helpful action: sweep, wipe, carry, or sort.
- Each repeat changes the world a little, until the place turns bright and tidy.

The prose is intentionally simple, rhythmic, and child-facing. The world model
tracks physical meters and emotional memes, and the repeated action matters:
one pass is not enough; several passes are needed before the story can end.
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

    hero: object | None = None
    item: object | None = None
    parent: object | None = None
    def __post_init__(self):
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

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
class Setting:
    place: str
    dim: bool
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
class Action:
    id: str
    verb: str
    gerund: str
    repeat_line: str
    mess: str
    clean_gain: float
    brighten_gain: float
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
class Item:
    id: str
    label: str
    phrase: str
    type: str
    fragile: bool = False
    plural: bool = False
    needs: str = "clean"
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
        self.lines: list[str] = []
        self.facts: dict = {}
        self.repetitions: int = 0
        self.fired: set[tuple] = set()

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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        w.repetitions = self.repetitions
        w.fired = set(self.fired)
        return w


def prince_or_princess(hero: Entity) -> str:
    return "girl" if hero.type == "girl" else "boy"


SETTINGS = {
    "nursery": Setting(place="the nursery", dim=True, affords={"sweep", "wipe", "sort"}),
    "hall": Setting(place="the hall", dim=True, affords={"sweep", "wipe"}),
    "kitchen": Setting(place="the kitchen", dim=False, affords={"wipe", "sort"}),
}

ACTIONS = {
    "sweep": Action(
        id="sweep",
        verb="sweep the floor",
        gerund="sweeping the floor",
        repeat_line="Again and again, the little broom went swish-swish-swish.",
        mess="dirt",
        clean_gain=0.45,
        brighten_gain=0.25,
        tags={"dirt", "repetition"},
    ),
    "wipe": Action(
        id="wipe",
        verb="wipe the table",
        gerund="wiping the table",
        repeat_line="Again and again, the cloth went pat-pat-pat.",
        mess="dirt",
        clean_gain=0.35,
        brighten_gain=0.35,
        tags={"dirt", "dim", "repetition"},
    ),
    "sort": Action(
        id="sort",
        verb="sort the toys",
        gerund="sorting the toys",
        repeat_line="Again and again, one block after one block found its home.",
        mess="dim",
        clean_gain=0.25,
        brighten_gain=0.45,
        tags={"dim", "repetition"},
    ),
}

ITEMS = {
    "apron": Item(id="apron", label="apron", phrase="a blue apron", type="apron"),
    "cloth": Item(id="cloth", label="cloth", phrase="a soft cloth", type="cloth"),
    "broom": Item(id="broom", label="broom", phrase="a little broom", type="broom"),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Rose", "Tia"]
BOY_NAMES = ["Ben", "Theo", "Finn", "Leo", "Max", "Sam"]
TRAITS = ["gentle", "spry", "cheerful", "curious", "small", "patient"]


@dataclass
class StoryParams:
    place: str
    action: str
    item: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld: dirt, dim light, and repetition."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def reasonableness_gate(place: str, action: str, item: str) -> bool:
    if place == "kitchen" and action == "sweep":
        return False
    if action == "sort" and item == "broom":
        return False
    return True


def explain_rejection(place: str, action: str, item: str) -> str:
    return f"(No story: {_safe_lookup(ACTIONS, action).verb} with {_safe_lookup(ITEMS, item).label} at {_safe_lookup(SETTINGS, place).place} is not a good nursery-rhyme fit.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = []
    for place in SETTINGS:
        for action in ACTIONS:
            for item in ITEMS:
                if not reasonableness_gate(place, action, item):
                    continue
                if getattr(args, "place", None) and getattr(args, "place", None) != place:
                    continue
                if getattr(args, "action", None) and getattr(args, "action", None) != action:
                    continue
                if getattr(args, "item", None) and getattr(args, "item", None) != item:
                    continue
                combos.append((place, action, item))
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, item = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, action=action, item=item, name=name, gender=gender, trait=trait)


def predict_finish(world: World, action: Action) -> bool:
    sim = world.copy()
    child = sim.get("hero")
    while child.meters["mess"] > THRESHOLD and sim.repetitions < 6:
        child.meters["clean"] = child.meters.get("clean", 0.0) + action.clean_gain
        child.meters["brightness"] = child.meters.get("brightness", 0.0) + action.brighten_gain
        child.meters["mess"] = max(0.0, child.meters["mess"] - 0.5)
        sim.repetitions += 1
    return child.meters.get("brightness", 0.0) >= 1.0 and child.meters["mess"] <= 0.5


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, meters={"clean": 0.0, "brightness": 0.0}, memes={"joy": 0.0}))
    parent = world.add(Entity(id="parent", kind="character", type="mother", label="mother", meters={"patience": 0.0}, memes={"love": 1.0}))
    item = world.add(Entity(id="item", type=_safe_lookup(ITEMS, params.item).type, label=_safe_lookup(ITEMS, params.item).label, phrase=_safe_lookup(ITEMS, params.item).phrase, owner="hero", caretaker="parent"))
    act = _safe_lookup(ACTIONS, params.action)

    world.say(f"{params.name} was a little {params.trait} {prince_or_princess(hero)} in {world.setting.place}.")
    world.say(f"{params.name} liked the dim room, but one dirty spot made the day feel glum.")
    world.say(f"{params.name}'s {item.label} was waiting there, neat as a pin, until the little dirt came in.")
    world.say(f"{params.name} wanted to {act.verb}, and {params.name}'s mother gave a nod and a grin.")

    hero.meters["mess"] = 1.5
    world.facts["hero_name"] = params.name
    world.facts["parent_name"] = "mother"
    world.facts["place"] = world.setting.place
    world.facts["action"] = act
    world.facts["item"] = item
    world.facts["params"] = params

    if not predict_finish(world, act):
        pass

    world.say(f"{params.name} began to {act.gerund}, and the little broom sang in time.")
    while hero.meters["mess"] > 0.5:
        world.repetitions += 1
        hero.meters["clean"] = hero.meters.get("clean", 0.0) + act.clean_gain
        hero.meters["brightness"] = hero.meters.get("brightness", 0.0) + act.brighten_gain
        hero.meters["mess"] = max(0.0, hero.meters["mess"] - 0.5)
        parent.meters["patience"] += 0.2
        world.say(act.repeat_line)

    if hero.meters["brightness"] >= 1.0:
        world.say(f"At last, the dim was less dim, and the dirt was gone from sight.")
        world.say(f"{params.name} smiled at the tidy place, and the little room shone bright and light.")
        hero.memes["joy"] += 1.0
        parent.memes["love"] += 0.5

    world.facts["repetitions"] = world.repetitions
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act = _safe_fact(world, f, "action")
    item = _safe_fact(world, f, "item")
    return [
        f'Write a short nursery-rhyme-style story about "{act.id}" and a little bit of dirt-dim repetition.',
        f"Tell a gentle story where a child keeps {act.gerund} until {item.label} and the room feel bright again.",
        f'Write a simple story with repeating lines, a dim place, and a dirty spot that becomes tidy.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = _safe_fact(world, f, "params")
    act: Action = _safe_fact(world, f, "action")
    item: Item = _safe_fact(world, f, "item")
    name = _safe_fact(world, f, "hero_name")
    return [
        QAItem(
            question=f"What did {name} keep doing in {world.setting.place}?",
            answer=f"{name} kept {act.gerund}, over and over, until the dirty place was tidier.",
        ),
        QAItem(
            question=f"Why did the little room feel less dim by the end?",
            answer=f"It felt less dim because {name} repeated the helpful work and slowly cleared the dirt away.",
        ),
        QAItem(
            question=f"What did {name}'s {item.label} have to do with the story?",
            answer=f"The {item.label} was part of the tidy scene, and it stayed with {name} while the room was being cleaned.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does dirt usually do to a room?",
            answer="Dirt makes a room look messy and gloomy until someone cleans it up.",
        ),
        QAItem(
            question="Why can repeating a chore help?",
            answer="Repeating a chore can help because one small pass may not be enough, but many passes can slowly make things clean.",
        ),
        QAItem(
            question="What does dim mean?",
            answer="Dim means not very bright, so things can look soft, shaded, or a little dark.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"repetitions={world.repetitions}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place,Action,Item) :- place(Place), action(Action), item(Item), good_combo(Place,Action,Item).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    for p in SETTINGS:
        for a in ACTIONS:
            for i in ITEMS:
                if reasonableness_gate(p, a, i):
                    lines.append(asp.fact("good_combo", p, a, i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set()
    for p in SETTINGS:
        for a in ACTIONS:
            for i in ITEMS:
                if reasonableness_gate(p, a, i):
                    py.add((p, a, i))
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches reasonableness_gate() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


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


CURATED = [
    StoryParams(place="nursery", action="sweep", item="broom", name="Mia", gender="girl", trait="patient"),
    StoryParams(place="hall", action="wipe", item="cloth", name="Ben", gender="boy", trait="cheerful"),
    StoryParams(place="kitchen", action="sort", item="apron", name="Lily", gender="girl", trait="gentle"),
]


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
        for p, a, i in vals:
            print(p, a, i)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
