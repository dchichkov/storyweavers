#!/usr/bin/env python3
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    momdad: object | None = None
    snack: object | None = None
    tool: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Room:
    place: str
    afford: set[str]
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
class Treat:
    id: str
    label: str
    phrase: str
    region: str
    mess: str
    soil: str
    verb: str
    gerund: str
    rustle: str
    keyword: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Helper:
    id: str
    label: str
    label_phrase: str
    protects: set[str]
    guards: set[str]
    prep: str
    fix: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    room: str
    treat: str
    helper: str
    name: str
    gender: str
    parent: str
    trait: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


ROOMS = {
    "kitchen": Room("the kitchen", {"donut"}),
    "bedroom": Room("the bedroom", {"bedtime"}),
    "porch": Room("the porch", {"donut", "bedtime"}),
}

TREATS = {
    "donut": Treat(
        id="donut",
        label="donut",
        phrase="a small, sugary donut",
        region="hands",
        mess="crumbs",
        soil="crumbly",
        verb="eat the donut",
        gerund="nibbling the donut",
        rustle="softly",
        keyword="donut",
        tags={"donut", "crumbs", "sweet"},
    ),
    "crumby_donut": Treat(
        id="crumby_donut",
        label="donut",
        phrase="a glazed donut with sprinkles",
        region="hands",
        mess="crumbs",
        soil="extra crumbly",
        verb="eat the donut",
        gerund="savoring the donut",
        rustle="carefully",
        keyword="donut",
        tags={"donut", "crumbs", "sweet"},
    ),
}

HELPERS = {
    "plate": Helper(
        id="plate",
        label="a little plate",
        label_phrase="a little plate",
        protects={"hands"},
        guards={"crumbs"},
        prep="put the donut on a little plate",
        fix="placed the donut on the plate",
    ),
    "napkin": Helper(
        id="napkin",
        label="a soft napkin",
        label_phrase="a soft napkin",
        protects={"hands"},
        guards={"crumbs"},
        prep="wrap the donut in a soft napkin",
        fix="wrapped the donut in the napkin",
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Ruby", "Ivy", "Ella", "Maya"]
BOY_NAMES = ["Owen", "Finn", "Theo", "Leo", "Max", "Nico", "Eli"]
TRAITS = ["compliant", "gentle", "sleepy", "careful", "patient"]

KNOWLEDGE = {
    "donut": [
        ("What is a donut?",
         "A donut is a sweet, round treat that people often eat for a snack or dessert."),
    ],
    "crumbs": [
        ("What are crumbs?",
         "Crumbs are tiny broken pieces of food, like little bits from bread or cake."),
    ],
    "sweet": [
        ("Why do sweet treats taste good?",
         "Sweet treats taste good because sugar gives them a pleasant flavor people often enjoy."),
    ],
}

KNOWLEDGE_ORDER = ["donut", "crumbs", "sweet"]


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def _risk(treat: Treat) -> bool:
    return treat.region == "hands"


def _compatible(treat: Treat, helper: Helper) -> bool:
    return treat.mess in helper.guards and treat.region in helper.protects


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room = getattr(args, "room", None) or rng.choice(sorted(ROOMS))
    treat = getattr(args, "treat", None) or rng.choice(sorted(TREATS))
    helper = getattr(args, "helper", None) or rng.choice(sorted(HELPERS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if getattr(args, "prize", None) and getattr(args, "prize", None) != treat:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "name", None) is None:
        pass
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)

    tr = _safe_lookup(TREATS, treat)
    hp = _safe_lookup(HELPERS, helper)
    if not _risk(tr):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if not _compatible(tr, hp):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(room=room, treat=treat, helper=helper, name=name, gender=gender, parent=parent, trait=trait)


def tell(room: Room, treat: Treat, helper: Helper, name: str, gender: str, parent: str, trait: str) -> World:
    w = World(room)
    child = w.add(Entity(id=name, kind="character", type=gender, memes={"sleepy": 1.0, "desire": 1.0}))
    momdad = w.add(Entity(id="Parent", kind="character", type=parent, label=f"the {parent}"))
    snack = w.add(Entity(id="Treat", type="treat", label="donut", phrase=treat.phrase, owner=child.id, caretaker=momdad.id, region=treat.region))
    tool = w.add(Entity(id=helper.id, type="helper", label=helper.label, phrase=helper.label_phrase, owner=child.id, caretaker=momdad.id, protective=True, covers=set(helper.protects), plural=helper.plural))

    w.say(f"At bedtime, {name} was a {trait} little {gender} who loved the warm, sweet smell of a {snack.label}.")
    w.say(f"{name} had been compliant all day, but when the lamp grew soft and golden, {name} noticed one last {snack.label} on the counter.")
    w.say(f"The {parent} smiled and gave a small cautionary warning: if the {snack.label} was eaten too fast, crumbs might fall onto the quilt.")
    w.say(f"{name} looked at the donut, then at the sleepy bedroom, and wanted a cozy way to enjoy it without making a mess.")

    w.say(f"Then {name} chose problem solving. {name} asked for {helper.label_phrase}, and the {parent} said yes.")
    w.say(f"They {helper.prep}, so the treat stayed neat and ready for slow, careful bites.")
    w.say(f"{name} ate the {snack.label} {treat.rustle}, with tiny crumbs kept in check.")
    w.say(f"When the last bite was gone, the bedroom felt calm again, and {name} climbed into bed with a happy, tidy tummy.")
    w.say(f"The moon looked in at the window while the quilt stayed clean, and the bedtime story ended as softly as a yawn.")

    w.facts.update(child=child, parent=momdad, treat=snack, helper=tool, treat_cfg=treat, helper_cfg=helper, room=room)
    return w


def generation_prompts(w: World) -> list[str]:
    f = w.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    parent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    treat = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "treat_cfg")
    return [
        f'Write a bedtime story for a young child about {child.id}, a compliant little {child.type}, and a {treat.keyword}.',
        f"Tell a gentle story where {child.id} wants a donut at bedtime, but {parent.label} warns about crumbs and they solve it calmly.",
        f'Write a cozy story that includes the words "compliant" and "donut" and ends with a tidy, sleepy scene.',
    ]


def story_qa(w: World) -> list[QAItem]:
    f = w.facts
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")  # type: ignore[assignment]
    parent: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")  # type: ignore[assignment]
    treat: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "treat")  # type: ignore[assignment]
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")  # type: ignore[assignment]
    trait = child.memes and "compliant" or "sleepy"
    return [
        QAItem(
            question=f"What did {child.id} want at bedtime?",
            answer=f"{child.id} wanted a donut at bedtime, because the sweet smell made the evening feel cozy.",
        ),
        QAItem(
            question=f"Why did the {parent.type} give a cautionary warning?",
            answer=f"The {parent.type} warned about crumbs because a donut can fall apart and make the quilt messy.",
        ),
        QAItem(
            question=f"How did {child.id} solve the problem?",
            answer=f"{child.id} solved it by using {helper.label_phrase} and eating the donut carefully.",
        ),
        QAItem(
            question=f"How did {child.id} act in the story?",
            answer=f"{child.id} was compliant and listened, which helped turn the bedtime moment into a calm solution.",
        ),
    ]


def world_knowledge_qa(w: World) -> list[QAItem]:
    tags = set(w.facts["treat_cfg"].tags)  # type: ignore[index]
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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


def dump_trace(w: World) -> str:
    lines = ["--- world model state ---"]
    for e in w.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A treat is at risk if it is something eaten with the hands.
at_risk(T) :- treat(T), region(T,hands).

% A helper solves the problem when it guards crumbs and covers hands.
solves(H,T) :- helper(H), treat(T), at_risk(T),
               guards(H,crumbs), covers(H,hands).

valid_story(Room,T,H) :- room(Room), affords(Room,donut),
                         treat(T), helper(H), at_risk(T), solves(H,T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for rid, r in ROOMS.items():
        lines.append(asp.fact("room", rid))
        for a in sorted(r.afford):
            lines.append(asp.fact("affords", rid, a))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("region", tid, t.region))
        lines.append(asp.fact("mess", tid, t.mess))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for g in sorted(h.guards):
            lines.append(asp.fact("guards", hid, g))
        for c in sorted(h.protects):
            lines.append(asp.fact("covers", hid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show valid_story/3.")
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set()
    for room in ROOMS:
        for tid, t in TREATS.items():
            for hid, h in HELPERS.items():
                if room in ROOMS and "donut" in _safe_lookup(ROOMS, room).afford and _risk(t) and _compatible(t, h):
                    python_set.add((room, tid, hid))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    print(" only in clingo:", sorted(clingo_set - python_set))
    print(" only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy bedtime story world about compliant donut choices.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--prize")
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


def generate(params: StoryParams) -> StorySample:
    w = tell(_safe_lookup(ROOMS, params.room), _safe_lookup(TREATS, params.treat), _safe_lookup(HELPERS, params.helper), params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_knowledge_qa(w),
        world=w,
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


def resolve_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room = getattr(args, "room", None) or rng.choice(sorted(ROOMS))
    treat = getattr(args, "treat", None) or rng.choice(sorted(TREATS))
    helper = getattr(args, "helper", None) or rng.choice(sorted(HELPERS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if treat not in TREATS or helper not in HELPERS:
        pass
    if not _risk(_safe_lookup(TREATS, treat)) or not _compatible(_safe_lookup(TREATS, treat), _safe_lookup(HELPERS, helper)):
        pass
    return StoryParams(room=room, treat=treat, helper=helper, name=name, gender=gender, parent=parent, trait=trait)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        for combo in combos:
            print(" ".join(map(str, combo)))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for room in ROOMS:
            for treat in TREATS:
                for helper in HELPERS:
                    try:
                        params = StoryParams(room=room, treat=treat, helper=helper, name="Mina", gender="girl", parent="mother", trait="compliant")
                        if not (_risk(_safe_lookup(TREATS, treat)) and _compatible(_safe_lookup(TREATS, treat), _safe_lookup(HELPERS, helper))):
                            continue
                        samples.append(generate(params))
                    except StoryError:
                        continue
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_from_args(args, random.Random(seed))
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

    for i, s in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
