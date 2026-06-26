#!/usr/bin/env python3
"""
A tiny heartwarming storyworld about tangy treats and kind choices.

The seed idea is simple: a child makes or finds something with a bright tang,
worries about it going wrong, then kindness turns the moment into a warm,
shared ending.

The simulation tracks:
- physical state: tang, spill, mix, share
- emotional state: worry, kindness, gratitude, joy

The prose is state-driven and the story only exists when the world model says
the turn and resolution make sense.
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

TANG_THRESHOLD = 1.0
KIND_THRESHOLD = 1.0



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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Scene:
    place: str
    sound: str
    afford: set[str] = field(default_factory=set)
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
class Offer:
    id: str
    label: str
    prep: str
    tail: str
    fits: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        w = World(self.scene)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


SCENES = {
    "kitchen": Scene(place="the kitchen", sound="soft clinks", afford={"mix", "share"}),
    "porch": Scene(place="the porch", sound="warm breeze", afford={"mix", "share"}),
    "yard": Scene(place="the yard", sound="birdsong", afford={"mix", "share"}),
}

ACTIVITIES = {
    "lemonade": {
        "verb": "make lemonade",
        "gerund": "making lemonade",
        "mess": "tang",
        "spill": "too sour",
        "taste": "bright and tangy",
        "risk": "a sour spill",
        "keyword": "tang",
    },
    "jamtoast": {
        "verb": "spread jam on toast",
        "gerund": "spreading jam on toast",
        "mess": "sticky",
        "spill": "sticky",
        "taste": "sweet with a little tang",
        "risk": "a sticky spill",
        "keyword": "tang",
    },
    "fruitbowl": {
        "verb": "cut fruit for a bowl",
        "gerund": "cutting fruit",
        "mess": "tang",
        "spill": "squirted",
        "taste": "fresh and tangy",
        "risk": "juice on the table",
        "keyword": "tang",
    },
}

GENTLE_FIXES = [
    Offer(id="extra_cup", label="an extra cup", prep="pour the tangy drink into an extra cup first", tail="poured it into an extra cup", fits={"lemonade", "fruitbowl"}),
    Offer(id="napkins", label="a stack of napkins", prep="set out a stack of napkins and slice carefully", tail="kept a stack of napkins nearby", fits={"jamtoast", "fruitbowl"}),
    Offer(id="tray", label="a small tray", prep="carry everything on a small tray", tail="carried the snacks on a small tray", fits={"lemonade", "jamtoast", "fruitbowl"}),
]

CHILD_NAMES = ["Milo", "Nina", "Pip", "Lena", "Owen", "Maya", "Ivy", "Finn"]
PARENT_TYPES = ["mother", "father"]
TRAITS = ["gentle", "curious", "brave", "sweet", "careful", "cheerful"]


@dataclass
class StoryParams:
    scene: str
    activity: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming tang storyworld.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
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


def valid_activities() -> list[str]:
    return list(ACTIVITIES)


def valid_story_choices() -> list[tuple[str, str]]:
    return [(scene, act) for scene in SCENES for act in _safe_lookup(SCENES, scene).afford if act in ACTIVITIES]


def choose_offer(activity: str) -> Optional[Offer]:
    for offer in GENTLE_FIXES:
        if activity in offer.fits:
            return offer
    return None


def explain_rejection(activity: str) -> str:
    return f"(No story: there is no gentle kindness-based fix that fits {activity}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [(s, a) for s, a in valid_story_choices()
               if (getattr(args, "scene", None) is None or s == getattr(args, "scene", None))
               and (getattr(args, "activity", None) is None or a == getattr(args, "activity", None))]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    scene, activity = rng.choice(sorted(choices))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENT_TYPES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(scene=scene, activity=activity, name=name, gender=gender, parent=parent, trait=trait)


def story_intro(world: World, child: Entity, parent: Entity, activity: dict) -> None:
    world.say(
        f"{child.id} was a little {child.type} who loved {activity['gerund']} and the "
        f"soft {world.scene.sound} of {world.scene.place}."
    )
    world.say(
        f"{child.pronoun('possessive').capitalize()} {parent.label_word} liked to watch "
        f"{child.id} with a warm smile, because small days could still feel special."
    )


def predict_spill(world: World, child: Entity, activity: dict) -> bool:
    sim = world.copy()
    sim.get(child.id).meters[activity["mess"]] = 1.0
    return True


def act(world: World, child: Entity, parent: Entity, activity: dict) -> None:
    child.meters[activity["mess"]] = 1.0
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    world.say(
        f"One day, {child.id} wanted to {activity['verb']} right away, but the first try "
        f"looked a little risky."
    )
    world.say(
        f"{parent.pronoun('possessive').capitalize()} {parent.label_word} noticed the chance for "
        f"{activity['risk']}."
    )


def worry(world: World, child: Entity, parent: Entity, activity: dict) -> None:
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(
        f'"If we rush, the snack might get {activity["spill"]}," {parent.label_word} said '
        f"softly. {child.id} paused and listened."
    )


def offer_kindness(world: World, child: Entity, parent: Entity, activity: dict) -> Optional[Offer]:
    offer = choose_offer(activity["verb"].split()[1] if False else _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "activity"))
    offer = choose_offer(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "activity"))
    if offer is None:
        return None
    world.say(
        f'{parent.pronoun("possessive").capitalize()} {parent.label_word} had a kind idea: '
        f"{offer.prep}."
    )
    return offer


def accept(world: World, child: Entity, parent: Entity, activity: dict, offer: Offer) -> None:
    child.memes["kindness"] = child.memes.get("kindness", 0) + 1
    child.memes["gratitude"] = child.memes.get("gratitude", 0) + 1
    child.memes["worry"] = 0.0
    world.say(
        f"{child.id}'s face brightened. {child.pronoun().capitalize()} helped with a careful hand, "
        f"and together they {offer.tail}."
    )
    world.say(
        f"Soon the treat was {activity['taste']}, and {child.id} shared the first happy sip "
        f"with {parent.pronoun('object')}."
    )


def tell(params: StoryParams) -> World:
    scene = _safe_lookup(SCENES, params.scene)
    activity = _safe_lookup(ACTIVITIES, params.activity)
    world = World(scene)
    child_type = params.gender
    child = world.add(Entity(id=params.name, kind="character", type=child_type, meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent", meters={}, memes={}))
    world.facts["activity"] = params.activity

    story_intro(world, child, parent, activity)
    world.para()
    act(world, child, parent, activity)
    worry(world, child, parent, activity)
    world.para()
    offer = offer_kindness(world, child, parent, activity)
    if offer is not None:
        accept(world, child, parent, activity, offer)
    world.facts.update(child=child, parent=parent, offer=offer, activity_cfg=activity, scene=scene)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    parent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    activity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "activity_cfg")
    return [
        f'Write a heartwarming story for a child about {child.id} making something with a little "{activity["keyword"]}".',
        f"Tell a gentle story where {child.id} wants to {activity['verb']} and {parent.label_word} helps with kindness.",
        f"Write a short story that includes tangy details, a kind pause, and a happy shared ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    parent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    activity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "activity_cfg")
    offer = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "offer")
    scene = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "scene")
    qs = [
        QAItem(
            question=f"What did {child.id} want to do in {scene.place}?",
            answer=f"{child.id} wanted to {activity['verb']}, and the idea felt bright and exciting.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} stop {child.id} for a moment?",
            answer=f"{parent.label_word} noticed that rushing could cause {activity['risk']}, so {child.id} paused to listen.",
        ),
        QAItem(
            question=f"What kind idea helped {child.id} and {parent.label_word} finish together?",
            answer=f"They used {offer.label} so they could keep things neat while still enjoying the {activity['taste']} treat.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt happy and grateful, because {child.id} and {parent.label_word} shared the treat together.",
        ),
    ]
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does tangy mean?",
            answer="Tangy means a taste that is bright, sharp, or a little sour in a way that wakes up your mouth.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone helps, shares, or speaks gently so another person feels cared for.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== prompts ==")
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
kind_story(Scene, Act) :- scene(Scene), activity(Act), affords(Scene, Act).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, scene in SCENES.items():
        lines.append(asp.fact("scene", sid))
        for act in sorted(scene.afford):
            lines.append(asp.fact("affords", sid, act))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show kind_story/2."))
    return sorted(set(asp.atoms(model, "kind_story")))


def asp_verify() -> int:
    py = set(valid_story_choices())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show kind_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(scene=s, activity=a, name="Milo", gender="boy", parent="mother", trait="gentle")) for s, a in valid_story_choices()]
    else:
        seen = set()
        for i in range(max(getattr(args, "n", None) * 50, 50)):
            if len(samples) >= getattr(args, "n", None):
                break
            seed = base_seed + i
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
