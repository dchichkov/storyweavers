#!/usr/bin/env python3
"""
storyworlds/worlds/little_muppet_sharing_whodunit.py
====================================================

A tiny storyworld about little muppets, sharing, and a gentle whodunit.

Premise:
A little muppet has something another muppet wants to share. Then the item goes missing,
everyone gets curious, and the group follows small clues to find the truth.

The simulated world tracks:
- physical state in meters: who holds what, where an object is, whether it is hidden
- emotional state in memes: surprise, worry, guilt, relief, trust

The stories are written as complete, child-facing mysteries with:
- a beginning that introduces the shared item
- a middle turn where something goes wrong
- a resolution where the clue trail explains what happened and sharing is restored
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    held_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    caretaker: object | None = None
    friend: object | None = None
    hero: object | None = None
    shared: object | None = None
    def __post_init__(self):
        if not self.meters:
            self.meters = {"here": 0.0, "hidden": 0.0}
        if not self.memes:
            self.memes = {
                "surprise": 0.0,
                "worry": 0.0,
                "guilt": 0.0,
                "relief": 0.0,
                "trust": 0.0,
                "curiosity": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    mood: str
    affords: set[str] = field(default_factory=set)
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
class Toy:
    id: str
    label: str
    phrase: str
    owner_kind: set[str] = field(default_factory=lambda: {"muppet"})
    shareable: bool = True
    easy_to_hide: bool = False
    clue: str = ""
    found_in: str = ""
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


@dataclass
class StoryParams:
    place: str
    toy: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    caretaker_name: str
    caretaker_type: str
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


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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
            self.events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.events = list(self.events)
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_hidden_item(world: World) -> list[str]:
    out = []
    for toy in [e for e in world.entities.values() if e.type == "toy"]:
        if toy.hidden_in and toy.meters["hidden"] >= THRESHOLD:
            sig = ("hidden", toy.id, toy.hidden_in)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"The {toy.label} was hidden in the {toy.hidden_in}.")
    return out


def _r_missing(world: World) -> list[str]:
    out = []
    toy = next((e for e in world.entities.values() if e.type == "toy"), None)
    if not toy:
        return out
    if toy.held_by is None and toy.hidden_in and toy.meters["hidden"] >= THRESHOLD:
        sig = ("missing", toy.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append(f"That was why the {toy.label} seemed missing.")
    return out


CAUSAL_RULES = [
    Rule("hidden_item", _r_hidden_item),
    Rule("missing", _r_missing),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def mystery_setup(world: World, hero: Entity, friend: Entity, caretaker: Entity, toy: Entity) -> None:
    world.say(f"Little {hero.id} was a {hero.traits[0]} muppet who loved sharing.")
    world.say(f"{friend.id} was a {friend.traits[0]} muppet who liked to take turns.")
    world.say(f"{hero.id} had {hero.pronoun('possessive')} {toy.label}, and {friend.id} asked to share {toy.it()}.")
    toy.held_by = hero.id
    hero.memes["trust"] += 1
    friend.memes["curiosity"] += 1


def first_clue(world: World, toy: Entity, hero: Entity, friend: Entity) -> None:
    world.para()
    world.say(
        f"At {world.place.name}, the friends looked around, but the {toy.label} was gone."
    )
    hero.memes["surprise"] += 1
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"{hero.id} asked, \"Who moved it?\" and {friend.id} whispered, "
        f"\"Let's follow the clues.\""
    )


def suspect_sequence(world: World, hero: Entity, friend: Entity, caretaker: Entity, toy: Entity) -> None:
    world.para()
    world.say(
        f"They checked the soft couch, the little basket, and the tall shelf."
    )
    world.say(
        f"At last, {caretaker.id} saw a tiny ribbon stuck near the basket."
    )
    caretaker.memes["curiosity"] += 1
    world.facts["clue"] = toy.clue
    world.facts["found_in"] = toy.found_in


def reveal(world: World, hero: Entity, friend: Entity, caretaker: Entity, toy: Entity) -> None:
    world.para()
    toy.held_by = None
    toy.hidden_in = None
    toy.meters["hidden"] = 0.0
    hero.memes["worry"] = 0.0
    friend.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    caretaker.memes["relief"] += 1
    world.say(
        f"Then {caretaker.id} smiled and said the truth: {toy.clue}."
    )
    world.say(
        f"The {toy.label} had not been stolen at all. It had been tucked in the {toy.found_in} "
        f"so it would stay safe for the next turn."
    )
    world.say(
        f"{hero.id} and {friend.id} shared {toy.it()} together, and the whole room felt fair again."
    )


def tell_story(place: Place, toy: Toy, hero_name: str, hero_type: str, friend_name: str,
               friend_type: str, caretaker_name: str, caretaker_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                            traits=["little", "careful"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type,
                              traits=["little", "friendly"]))
    caretaker = world.add(Entity(id=caretaker_name, kind="character", type=caretaker_type,
                                 traits=["gentle", "watchful"]))
    shared = world.add(Entity(
        id=toy.id,
        kind="thing",
        type="toy",
        label=toy.label,
        phrase=toy.phrase,
        owner=hero.id,
    ))

    mystery_setup(world, hero, friend, caretaker, shared)

    shared.hidden_in = toy.found_in
    shared.meters["hidden"] = 1.0
    propagate(world)

    first_clue(world, shared, hero, friend)
    suspect_sequence(world, hero, friend, caretaker, shared)
    reveal(world, hero, friend, caretaker, shared)

    world.facts.update(
        hero=hero,
        friend=friend,
        caretaker=caretaker,
        toy=shared,
        place=place,
    )
    return world


PLACES = {
    "playroom": Place(name="the playroom", mood="bright", affords={"sharing"}),
    "living_room": Place(name="the living room", mood="cozy", affords={"sharing"}),
    "backstage": Place(name="the backstage room", mood="busy", affords={"sharing"}),
}

TOYS = {
    "drum": Toy(
        id="drum",
        label="little drum",
        phrase="a shiny little drum",
        clue="the ribbon matched the toy box",
        found_in="basket",
    ),
    "ball": Toy(
        id="ball",
        label="soft ball",
        phrase="a bouncy soft ball",
        clue="a patch of fuzz on the couch matched the ball cover",
        found_in="couch",
    ),
    "car": Toy(
        id="car",
        label="red car",
        phrase="a red toy car",
        clue="its tiny wheel print was on the shelf",
        found_in="shelf",
    ),
}

HERO_NAMES = ["Mimi", "Bobo", "Tilly", "Pip", "Niko", "Lulu", "Foz", "Kiki"]
FRIEND_NAMES = ["Wren", "Penny", "Coco", "Ned", "Mara", "Rufus", "Dot", "Juno"]
CAREGIVER_NAMES = ["Nana", "Papa", "Auntie", "Uncle", "Mimi", "Grandpa"]
TRAITS = ["brave", "curious", "small", "cheerful", "gentle"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for toy_id in TOYS:
            if "sharing" in place.affords:
                combos.append((place_id, toy_id))
    return combos


def explain_rejection() -> str:
    return "(No story: this world only supports sharing mysteries in places that can hold a small clue trail.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny sharing whodunit with little muppets.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--caretaker")
    ap.add_argument("--hero-type", choices=["muppet"])
    ap.add_argument("--friend-type", choices=["muppet"])
    ap.add_argument("--caretaker-type", choices=["muppet", "adult"])
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
    if getattr(args, "place", None) and getattr(args, "place", None) not in PLACES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    toy = getattr(args, "toy", None) or rng.choice(sorted(TOYS))
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    friend_name = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    caretaker_name = getattr(args, "caretaker", None) or rng.choice(CAREGIVER_NAMES)
    return StoryParams(
        place=place,
        toy=toy,
        hero_name=hero_name,
        hero_type=getattr(args, "hero_type", None) or "muppet",
        friend_name=friend_name,
        friend_type=getattr(args, "friend_type", None) or "muppet",
        caretaker_name=caretaker_name,
        caretaker_type=getattr(args, "caretaker_type", None) or rng.choice(["muppet", "adult"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short whodunit for little children about sharing a {f['toy'].label} in {f['place'].name}.",
        f"Tell a gentle mystery where little muppets wonder who hid the {f['toy'].label} and then discover the clue.",
        f"Write a child-friendly story about sharing, a missing {f['toy'].label}, and a kind reveal at {f['place'].name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    caretaker = _safe_fact(world, f, "caretaker")
    toy = _safe_fact(world, f, "toy")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who was the story about at {place.name}?",
            answer=f"It was about little {hero.id}, {friend.id}, and {caretaker.id}, and it all happened in {place.name}.",
        ),
        QAItem(
            question=f"What item did they want to share?",
            answer=f"They wanted to share {toy.phrase}.",
        ),
        QAItem(
            question="What made everyone think something was wrong?",
            answer=f"The {toy.label} seemed missing, so the friends started following clues.",
        ),
        QAItem(
            question="Where was the hidden item found?",
            answer=f"It was tucked in the {toy.found_in}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The grown-up explained the clue, the item was found, and the friends shared it fairly again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use something too, so everyone gets a turn.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small hint that helps you solve a mystery.",
        ),
        QAItem(
            question="What does a muppet mean in a story?",
            answer="A muppet is a funny puppet character, usually soft and friendly in stories.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(playroom).
place(living_room).
place(backstage).

toy(drum).
toy(ball).
toy(car).

shared_story(P, T) :- place(P), toy(T).
#show shared_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TOYS:
        lines.append(asp.fact("toy", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show shared_story/2."))
    return sorted(set(asp.atoms(model, "shared_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    toy = _safe_lookup(TOYS, params.toy)
    world = tell_story(place, toy, params.hero_name, params.hero_type,
                       params.friend_name, params.friend_type,
                       params.caretaker_name, params.caretaker_type)
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
    StoryParams(place="playroom", toy="drum", hero_name="Mimi", hero_type="muppet",
                friend_name="Wren", friend_type="muppet", caretaker_name="Nana",
                caretaker_type="adult"),
    StoryParams(place="living_room", toy="ball", hero_name="Bobo", hero_type="muppet",
                friend_name="Penny", friend_type="muppet", caretaker_name="Papa",
                caretaker_type="adult"),
    StoryParams(place="backstage", toy="car", hero_name="Tilly", hero_type="muppet",
                friend_name="Coco", friend_type="muppet", caretaker_name="Auntie",
                caretaker_type="adult"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show shared_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for p, t in combos:
            print(f"  {p:12} {t}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.toy} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
