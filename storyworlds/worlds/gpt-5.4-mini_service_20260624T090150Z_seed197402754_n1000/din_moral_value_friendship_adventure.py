#!/usr/bin/env python3
"""
A small adventure story world about a loud din, a moral choice, and friendship.
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

@dataclass(frozen=True)
class Place:
    id: str
    name: str
    detail: str
    keepsafe: bool = False
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


@dataclass(frozen=True)
class ObjectDef:
    id: str
    label: str
    phrase: str
    weight: str
    loud: bool = False
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


@dataclass(frozen=True)
class ChoiceDef:
    id: str
    label: str
    kind: str
    moral: str
    friendship: str
    outcome: str
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
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    held: Optional[str] = None
    at: Optional[str] = None
    hero: object | None = None
    pal: object | None = None
    thing: object | None = None
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
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
        self.trace.append(text)

    def render(self) -> str:
        return " ".join(self.trace)


@dataclass
class StoryParams:
    place: str
    object: str
    choice: str
    name: str
    friend: str
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


PLACES = {
    "forest_path": Place(
        id="forest_path",
        name="the forest path",
        detail="Tall trees leaned over the path, and birds watched from above.",
    ),
    "river_bridge": Place(
        id="river_bridge",
        name="the river bridge",
        detail="The wooden bridge creaked over bright water that hurried below.",
    ),
    "cave_entrance": Place(
        id="cave_entrance",
        name="the cave entrance",
        detail="A dark cave mouth yawned beside the trail, with pebbles underfoot.",
        keepsafe=True,
    ),
}

OBJECTS = {
    "lantern": ObjectDef(
        id="lantern",
        label="lantern",
        phrase="a little brass lantern",
        weight="light",
        loud=False,
    ),
    "bell": ObjectDef(
        id="bell",
        label="bell",
        phrase="a small silver bell",
        weight="light",
        loud=True,
    ),
    "map": ObjectDef(
        id="map",
        label="map",
        phrase="a folded trail map",
        weight="light",
        loud=False,
    ),
}

CHOICES = {
    "share": ChoiceDef(
        id="share",
        label="share the lantern",
        kind="kindness",
        moral="It is good to share when a friend is worried.",
        friendship="Sharing made both friends feel braver.",
        outcome="They could go on together.",
    ),
    "wait": ChoiceDef(
        id="wait",
        label="wait for the helper",
        kind="patience",
        moral="It is wise to wait when a safe way takes time.",
        friendship="Waiting showed trust between friends.",
        outcome="They stayed safe and kept each other company.",
    ),
    "tell_truth": ChoiceDef(
        id="tell_truth",
        label="tell the truth about the noise",
        kind="honesty",
        moral="Telling the truth helps friends solve a problem.",
        friendship="Honesty kept the friendship strong.",
        outcome="They fixed the trouble together.",
    ),
}

NAMES = ["Maya", "Leo", "Nora", "Sam", "Ivy", "Finn", "Ava", "Eli"]
FRIENDS = ["pals", "friends", "companions", "buddies"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world about din, moral choice, and friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    obj = getattr(args, "object", None) or rng.choice(list(OBJECTS))
    choice = getattr(args, "choice", None) or rng.choice(list(CHOICES))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIENDS)
    return StoryParams(place=place, object=obj, choice=choice, name=name, friend=friend)


def _narrate(world: World, hero: Entity, pal: Entity, obj: Entity, choice: ChoiceDef) -> None:
    world.say(f"{hero.label} and {pal.label} set out along {world.place.name}.")
    world.say(world.place.detail)
    world.say(f"They carried {_safe_lookup(OBJECTS, obj.id).phrase}, and the little {obj.label} gave them courage.")

    if obj.id == "bell":
        hero.meters["din"] += 2
        world.say("But the bell made a sharp din that echoed off the stones.")
        if world.place.keepsafe:
            world.say("The din could startle the bats in the cave, so they had to choose carefully.")
    else:
        hero.meters["din"] += 0
        world.say("The path stayed calm, and the two travelers listened for clues in the breeze.")

    pal.memes["worry"] += 1
    hero.memes["duty"] += 1
    world.say(f"{pal.label} looked uneasy, but {hero.label} remembered the moral choice ahead.")

    if choice.id == "share":
        hero.memes["kindness"] += 1
        pal.memes["trust"] += 1
        world.say(f"{hero.label} chose to share the lantern, and {pal.label} smiled with relief.")
        world.say(choice.moral)
        world.say(choice.friendship)
        world.say("Together they followed the safer side of the trail, where the light stayed steady.")
    elif choice.id == "wait":
        hero.memes["patience"] += 1
        pal.memes["trust"] += 1
        world.say(f"{hero.label} stopped and said they could wait for help instead of rushing ahead.")
        world.say(choice.moral)
        world.say(choice.friendship)
        world.say("Soon the helpful guide arrived, and the friends walked on without fear.")
    else:
        hero.memes["honesty"] += 1
        pal.memes["trust"] += 1
        world.say(f"{hero.label} told the truth: the noisy bell was making the din, not a monster.")
        world.say(choice.moral)
        world.say(choice.friendship)
        world.say("Once they knew the truth, they wrapped the bell in cloth and carried on together.")

    world.say(f"In the end, {hero.label} and {pal.label} reached the quiet end of the path, still good friends.")


def generate_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    obj = _safe_lookup(OBJECTS, params.object)
    choice = _safe_lookup(CHOICES, params.choice)
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", label=params.name))
    pal = world.add(Entity(id="pal", kind="character", label=params.friend))
    thing = world.add(Entity(id=obj.id, kind="object", label=obj.label))
    hero.at = place.id
    pal.at = place.id
    thing.held = hero.id
    world.facts.update(hero=hero, pal=pal, obj=thing, choice=choice, place=place, object_def=obj)
    _narrate(world, hero, pal, thing, choice)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short adventure story for a small child about {f['hero'].label}, {f['pal'].label}, and a loud din.",
        f"Tell a gentle tale where a friend chooses {f['choice'].label} while traveling at {f['place'].name}.",
        f"Write a friendship story that includes a din and ends with a moral choice leading to safety.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    pal = _safe_fact(world, f, "pal")
    choice = _safe_fact(world, f, "choice")
    place = _safe_fact(world, f, "place")
    obj = _safe_fact(world, f, "object_def")
    return [
        QAItem(
            question=f"Who went on the adventure at {place.name}?",
            answer=f"{hero.label} and {pal.label} went on the adventure together at {place.name}.",
        ),
        QAItem(
            question=f"What made the loud din in the story?",
            answer=f"The loud din came from the {obj.label} that {hero.label} was carrying.",
        ),
        QAItem(
            question=f"What good choice did {hero.label} make?",
            answer=f"{hero.label} chose to {choice.label} so the two friends could stay safe and help each other.",
        ),
        QAItem(
            question=f"How did the story show friendship?",
            answer=f"{hero.label} and {pal.label} trusted each other, shared the work, and stayed together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a din?",
            answer="A din is a loud, noisy sound that can fill the whole place and make it hard to think.",
        ),
        QAItem(
            question="Why is friendship important on an adventure?",
            answer="Friendship is important because friends help each other, stay calm, and make safer choices.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good way to behave, like being kind, honest, or patient.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.at:
            parts.append(f"at={e.at}")
        if e.held:
            parts.append(f"held={e.held}")
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id:6} ({e.kind:8}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- entity(H, character).
friend(F) :- entity(F, character), F != H.
loud_din(O) :- object(O), din_source(O).
kind_choice(C) :- choice(C), moral(C).
good_story(H,F,O,C) :- hero(H), friend(F), loud_din(O), kind_choice(C).
#show good_story/4.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
    for o in OBJECTS.values():
        lines.append(asp.fact("object", o.id))
        if o.loud:
            lines.append(asp.fact("din_source", o.id))
    for c in CHOICES.values():
        lines.append(asp.fact("choice", c.id))
        lines.append(asp.fact("moral", c.id))
    lines.append(asp.fact("entity", "hero", "character"))
    lines.append(asp.fact("entity", "pal", "character"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _load_asp():
    import storyworlds.asp as asp
    return asp


def asp_verify() -> int:
    asp = _load_asp()
    model = asp.one_model(asp_program("#show good_story/4."))
    atoms = set(asp.atoms(model, "good_story"))
    expected = {("hero", "pal", oid, cid) for oid, o in OBJECTS.items() if o.loud for cid in CHOICES}
    if atoms == expected:
        print(f"OK: clingo gate matches Python reasoning ({len(atoms)} combinations).")
        return 0
    print("MISMATCH between clingo and Python reasoning:")
    if atoms - expected:
        print("  only in clingo:", sorted(atoms - expected))
    if expected - atoms:
        print("  only in python:", sorted(expected - atoms))
    return 1


def build_storysample(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
    StoryParams(place="forest_path", object="bell", choice="tell_truth", name="Maya", friend="Leo"),
    StoryParams(place="river_bridge", object="lantern", choice="share", name="Nora", friend="Ava"),
    StoryParams(place="cave_entrance", object="map", choice="wait", name="Finn", friend="Ivy"),
]


def generate(params: StoryParams) -> StorySample:
    return build_storysample(params)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show good_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        asp = _load_asp()
        model = asp.one_model(asp_program("#show good_story/4."))
        combos = sorted(set(asp.atoms(model, "good_story")))
        print(f"{len(combos)} compatible story combinations:\n")
        for combo in combos:
            print("  ", combo)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.choice} at {p.place} (object: {p.object})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
