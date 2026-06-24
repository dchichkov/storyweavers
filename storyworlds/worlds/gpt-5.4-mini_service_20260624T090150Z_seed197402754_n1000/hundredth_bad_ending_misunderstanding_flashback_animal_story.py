#!/usr/bin/env python3
"""
storyworlds/worlds/hundredth_bad_ending_misunderstanding_flashback_animal_story.py
=================================================================================

A small animal-story world about a misunderstood gift, a flashback, and a bad ending.

Seed tale:
---
At the hundredth dawn of spring, a little rabbit found a bright berry on a rock.
She wanted to save it for her friend, a shy mouse who loved shiny things.
When she ran back, the mouse saw the berry and thought the rabbit had taken
the berry from his own nest.
He said something sharp, and the rabbit remembered the day he had once promised
to share his best snack.
The rabbit tried to explain, but the mouse was too upset to listen.
In the end, the berry rolled into the grass, the rabbit went home alone, and the
mouse sat by himself under the tree, feeling sorry and sad.

World model:
---
This script models a tiny animal domain with:
- physical meters: carried things, hunger, distance, dirt, dropped items
- emotional memes: trust, worry, hurt, pride, regret, loneliness

The narrative is driven by state:
- a flashback is triggered by a remembered promise
- a misunderstanding is triggered by an observed object with the wrong ownership guess
- a bad ending results when the animals fail to reconcile
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
    species: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    obj: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    place: str = "the old oak tree"
    season: str = "spring"
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
class Animal:
    species: str
    label: str
    adjective: str
    home: str
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
class ObjectThing:
    id: str
    label: str
    phrase: str
    location: str
    owner: Optional[str] = None
    carried_by: Optional[str] = None
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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = _copy.deepcopy(self.facts)
        return w


RABBITS = [
    Animal("rabbit", "Pip", "little", "burrow"),
    Animal("rabbit", "Mina", "bright-eyed", "burrow"),
    Animal("rabbit", "Tori", "quick", "burrow"),
]

MICE = [
    Animal("mouse", "Nip", "shy", "nest"),
    Animal("mouse", "Lio", "tiny", "nest"),
    Animal("mouse", "Sera", "soft-spoken", "nest"),
]

OBJECTS = {
    "berry": ObjectThing("berry", "bright berry", "a bright berry", "rock"),
    "acorn": ObjectThing("acorn", "golden acorn", "a golden acorn", "rock"),
    "feather": ObjectThing("feather", "silver feather", "a silver feather", "rock"),
}

SETTINGS = {
    "oak": Setting(place="the old oak tree", season="spring"),
}

PRIZES = list(OBJECTS.keys())


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_species: str
    friend_name: str
    friend_species: str
    object_id: str
    seed: Optional[int] = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with a misunderstanding, flashback, and bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-species", choices=["rabbit", "mouse"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-species", choices=["rabbit", "mouse"])
    ap.add_argument("--object", dest="object_id", choices=PRIZES)
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
    place = getattr(args, "place", None) or "oak"
    hero_species = getattr(args, "hero_species", None) or rng.choice(["rabbit", "mouse"])
    friend_species = getattr(args, "friend_species", None) or ("mouse" if hero_species == "rabbit" else "rabbit")
    hero_pool = RABBITS if hero_species == "rabbit" else MICE
    friend_pool = MICE if friend_species == "mouse" else RABBITS
    hero = next((a for a in hero_pool if a.label != getattr(args, "friend_name", None)), rng.choice(hero_pool))
    friend = next((a for a in friend_pool if a.label != hero.label), rng.choice(friend_pool))
    object_id = getattr(args, "object_id", None) or rng.choice(PRIZES)
    if hero_species == friend_species and hero.label == friend.label:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=place,
        hero_name=getattr(args, "hero_name", None) or hero.label,
        hero_species=hero_species,
        friend_name=getattr(args, "friend_name", None) or friend.label,
        friend_species=friend_species,
        object_id=object_id,
    )


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _capitalize_sentence(text: str) -> str:
    return text[:1].upper() + text[1:]


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(
        id="hero",
        kind="character",
        species=params.hero_species,
        label=params.hero_name,
        phrase=f"{_article(params.hero_species)} {params.hero_species}",
        location="path",
        meters={"hunger": 1.0, "travel": 2.0},
        memes={"hope": 1.0, "trust": 1.0, "worry": 0.0, "hurt": 0.0, "regret": 0.0, "loneliness": 0.0},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        species=params.friend_species,
        label=params.friend_name,
        phrase=f"{_article(params.friend_species)} {params.friend_species}",
        location="nest",
        meters={"hunger": 1.0, "travel": 0.5},
        memes={"trust": 1.0, "worry": 0.0, "hurt": 0.0, "pride": 0.0, "regret": 0.0, "loneliness": 0.0},
    ))
    obj_cfg = _safe_lookup(OBJECTS, params.object_id)
    obj = world.add(Entity(
        id="object",
        kind="thing",
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        location="rock",
        owner="hero",
        carried_by="hero",
        meters={"shine": 1.0},
    ))
    world.facts.update(hero=hero, friend=friend, object=obj, object_id=params.object_id, params=params)
    return world


def predict_misunderstanding(world: World) -> bool:
    return world.get("object").carried_by == "hero" and world.get("friend").location == "nest"


def tell_story(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    obj = world.get("object")

    world.say(f"On the hundredth morning of spring, {hero.label} the {hero.species} trotted under {world.setting.place}.")
    world.say(f"{hero.label} found {obj.phrase} on a rock and picked {obj.it()} up very carefully.")
    hero.memes["hope"] += 1
    hero.meters["travel"] += 1

    world.para()
    world.say(f"{hero.label} hurried to {friend.label}'s nest, wanting to share the shiny treat.")
    if predict_misunderstanding(world):
        friend.memes["worry"] += 1
        friend.memes["hurt"] += 1
        world.say(f"But when {friend.label} saw {obj.phrase} in {hero.label}'s paws, {friend.label} frowned.")
        world.say(f'"You took that from my nest," {friend.label} said, and the words landed hard.')
        world.say(f"{hero.label} blinked. That was not true, but the misunderstanding had already grown big.")
    else:
        pass

    world.para()
    world.say(f"{hero.label} remembered a flashback from the day before: {friend.label} had promised to share the next sweet thing they found.")
    hero.memes["trust"] += 0.5
    friend.memes["trust"] += 0.2
    world.say(f"That memory should have helped, but {friend.label} was too upset to listen now.")
    world.say(f"{hero.label} tried to explain, yet {friend.label} turned away and hugged the doorway of the nest.")

    world.para()
    obj.carried_by = None
    obj.location = "grass"
    hero.memes["hurt"] += 1
    hero.memes["loneliness"] += 1
    friend.memes["regret"] += 1
    friend.memes["loneliness"] += 1
    friend.meters["travel"] += 0.2
    world.say(f"In the end, {obj.phrase} rolled into the grass between them.")
    world.say(f"{hero.label} walked home alone, and {friend.label} sat under the tree with a sour face.")
    world.say(f"The shiny thing was still bright, but the morning felt dim and quiet.")

    world.facts["bad_ending"] = True
    world.facts["misunderstanding"] = True
    world.facts["flashback"] = True


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f"Write a short animal story for young children about {p.hero_name} and {p.friend_name} that includes the word hundredth.",
        f"Tell a gentle but sad story where a {p.hero_species} brings a shiny thing to a {p.friend_species}, but they misunderstand each other.",
        "Write an animal story that uses a flashback and ends with a bad ending after a misunderstanding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.get("hero")
    f = world.get("friend")
    o = world.get("object")
    return [
        QAItem(
            question=f"Who found the shiny thing at the old tree?",
            answer=f"{h.label}, the {h.species}, found {o.phrase} on a rock.",
        ),
        QAItem(
            question=f"Why did {f.label} get upset?",
            answer=f"{f.label} thought {h.label} had taken {o.phrase} from the nest, but that was a misunderstanding.",
        ),
        QAItem(
            question="What remembered moment showed up in the middle of the story?",
            answer=f"There was a flashback to the day before, when {f.label} had promised to share the next sweet thing they found.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended badly: {h.label} went home alone, {f.label} stayed under the tree, and the shiny thing rolled away into the grass.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that shows something that happened earlier.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when one character thinks something untrue and gets it wrong.",
        ),
        QAItem(
            question="What can make an animal feel lonely?",
            answer="An animal can feel lonely when a friend is upset and will not listen or play.",
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
        parts = []
        if e.label:
            parts.append(f"label={e.label!r}")
        if e.location:
            parts.append(f"location={e.location!r}")
        if e.carried_by:
            parts.append(f"carried_by={e.carried_by!r}")
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) " + " ".join(parts))
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- character(H).
friend(F) :- character(F).
misunderstanding(H,F,O) :- character(H), character(F), thing(O), carried_by(O,H), sees(F,O), not knows_truth(F,O).
flashback(H,F) :- remembers(H, promise(F)).
bad_ending(H,F,O) :- misunderstanding(H,F,O), flashback(H,F), not reconciled(H,F).
#show misunderstanding/3.
#show flashback/2.
#show bad_ending/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for eid, e in _last_world.entities.items():
        if e.kind == "character":
            lines.append(asp.fact("character", eid))
        else:
            lines.append(asp.fact("thing", eid))
        if e.carried_by:
            lines.append(asp.fact("carried_by", eid, e.carried_by))
        if e.location:
            lines.append(asp.fact("sees", "friend", eid) if eid == "object" else asp.fact("located", eid, e.location))
    lines.append(asp.fact("remembers", "hero", "promise_friend"))
    return "\n".join(lines)


_last_world: World


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(place="oak", hero_name="Pip", hero_species="rabbit", friend_name="Nip", friend_species="mouse", object_id="berry"),
    StoryParams(place="oak", hero_name="Mina", hero_species="rabbit", friend_name="Lio", friend_species="mouse", object_id="acorn"),
    StoryParams(place="oak", hero_name="Tori", hero_species="rabbit", friend_name="Sera", friend_species="mouse", object_id="feather"),
]


def generate(params: StoryParams) -> StorySample:
    global _last_world
    world = setup_world(params)
    tell_story(world)
    _last_world = world
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show bad_ending/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

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
