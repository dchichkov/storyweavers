#!/usr/bin/env python3
"""
storyworlds/worlds/rock_n_roll_humor_dialogue_slice_of.py
==========================================================

A small slice-of-life storyworld about a child who loves rock'n'roll, a little
home mess of sound, a worried grown-up, and a humorous compromise.

The premise is simple: a child wants to play loud music at home, but someone in
the house needs quiet. The world tracks physical sound, instrument state, and
emotional beats, then resolves the scene through a believable everyday bargain.

This script follows the Storyweavers storyworld contract:
- standalone stdlib script
- imports results eagerly, asp lazily
- StoryParams + parser + resolve_params + generate + emit + main
- Python reasonableness gate and inline ASP twin
- state-driven prose with QA sets
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)
    plural: bool = False

    hero: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
        if not hasattr(self, "_tags"):
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
class Venue:
    id: str
    label: str
    place: str
    requires_quiet: bool = False
    affords: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Instrument:
    id: str
    label: str
    phrase: str
    loudness: int
    portable: bool = True
    unplugged: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Compromise:
    id: str
    label: str
    phrase: str
    method: str
    quieter_by: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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


class World:
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.venue)
        import copy as _copy
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    venue: str
    instrument: str
    compromise: str
    hero: str
    hero_gender: str
    parent: str
    trait: str
    pet: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


VENUES = {
    "apartment": Venue("apartment", "the apartment", "the apartment", True, {"plugged", "unplugged"}),
    "porch": Venue("porch", "the porch", "the porch", False, {"plugged", "unplugged"}),
    "garage": Venue("garage", "the garage", "the garage", False, {"plugged", "unplugged"}),
}

INSTRUMENTS = {
    "guitar": Instrument("guitar", "electric guitar", "a shiny electric guitar", 8, True, False, {"rock", "string"}),
    "drums": Instrument("drums", "drum kit", "a little drum kit", 9, False, False, {"rock", "beat"}),
    "ukulele": Instrument("ukulele", "ukulele", "a tiny ukulele", 3, True, False, {"string", "soft"}),
}

COMPROMISES = {
    "unplugged": Compromise("unplugged", "unplugged mode", "play unplugged", 4, 5, {"quiet", "music"}),
    "headphones": Compromise("headphones", "headphones", "put on headphones and use the amp on low", 6, 6, {"quiet", "music"}),
    "porch": Compromise("porch", "porch jam", "take the music to the porch", 7, 7, {"quiet", "music"}),
}

HEROES = ["Maya", "Leo", "Nina", "Owen", "Sofia", "Ben", "Ava", "Noah"]
TRAITS = ["funny", "sly", "bouncy", "dramatic", "cheerful", "silly"]
PETS = ["the cat", "the dog", "the goldfish", "the sleepy rabbit"]


def loud_enough(inst: Instrument) -> bool:
    return inst.loudness >= 7


def needs_quiet(world: World) -> bool:
    return world.venue.requires_quiet


def can_use(comp: Compromise, inst: Instrument, venue: Venue) -> bool:
    if comp.id == "porch":
        return venue.id in {"apartment", "porch", "garage"}
    if comp.id == "unplugged":
        return True
    if comp.id == "headphones":
        return inst.id == "guitar"
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for v in VENUES.values():
        for i in INSTRUMENTS.values():
            for c in COMPROMISES.values():
                if needs_quiet(World(v)) and loud_enough(i) and can_use(c, i, v):
                    out.append((v.id, i.id, c.id))
                elif not needs_quiet(World(v)) and can_use(c, i, v):
                    out.append((v.id, i.id, c.id))
    return out


def reasonableness_gate(venue: Venue, inst: Instrument, comp: Compromise) -> bool:
    return can_use(comp, inst, venue)


def select_compromise(inst: Instrument, venue: Venue) -> Optional[Compromise]:
    for c in (COMPROMISES["unplugged"], COMPROMISES["headphones"], COMPROMISES["porch"]):
        if reasonableness_gate(venue, inst, c):
            return c
    return None


def predict_noise(world: World, inst: Instrument) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["noise"] += inst.loudness
    if sim.venue.requires_quiet and hero.meters["noise"] >= 7:
        sim.get("parent").memes["stress"] += 1
    return {"noisy": hero.meters["noise"] >= 7, "stress": sim.get("parent").memes["stress"]}


def apply_jam(world: World, hero: Entity, inst: Instrument, narrate: bool = True) -> None:
    hero.meters["noise"] += inst.loudness
    hero.memes["joy"] += 1
    if world.venue.requires_quiet and hero.meters["noise"] >= 7:
        world.get("parent").memes["stress"] += 1
        if narrate:
            world.say("The sound bounced off the walls like a rubber ball in sneakers.")


def tell_setup(world: World, hero: Entity, parent: Entity, inst: Instrument) -> None:
    hero.memes["love_music"] += 1
    world.say(
        f"{hero.id} was a {next((t for t in hero.attrs.get('traits','').split(',') if t), 'funny')} "
        f"{hero.type} who loved rock'n'roll and {inst.phrase}."
    )
    world.say(
        f"At {world.venue.place}, {hero.id} kept tapping a beat on the table like "
        f"{hero.id} was already the star of a tiny concert."
    )
    world.say(
        f"'{hero.id}, not so loud,' {parent.id} said. '{parent.attrs.get('reason','someone is napping')}.'"
    )


def tell_want(world: World, hero: Entity, parent: Entity, inst: Instrument) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} grinned. 'But this song has a solo!' {hero.pronoun().capitalize()} said, "
        f"holding up {inst.phrase} like it was a microphone."
    )


def tell_warning(world: World, parent: Entity, hero: Entity, inst: Instrument) -> None:
    pred = predict_noise(world, inst)
    world.facts["predicted_noise"] = pred["noisy"]
    world.facts["predicted_stress"] = pred["stress"]
    if pred["noisy"]:
        world.say(
            f"'{inst.label.title()} is great,' {parent.id} said, 'but not when the walls can hear every note.'"
        )
    else:
        world.say(
            f"'{inst.label.title()} is fine,' {parent.id} said, 'just not as a parade for the whole building.'"
        )


def tell_joke(world: World, hero: Entity, parent: Entity) -> None:
    hero.memes["humor"] += 1
    world.say(
        f"{hero.id} squinted at the ceiling. 'What if I call it practice and the neighbors call it thunder?'"
    )
    world.say(f"{parent.id} laughed so hard {parent.pronoun()} nearly forgot to be stern.")


def tell_compromise(world: World, hero: Entity, parent: Entity, inst: Instrument, comp: Compromise) -> None:
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    parent.memes["stress"] = max(0, parent.memes["stress"] - comp.quieter_by)
    if comp.id == "unplugged":
        world.say(
            f"'{hero.id}, how about we {comp.method}?' {parent.id} said. "
            f"{hero.id} tilted {hero.pronoun('possessive')} head. 'Rock'n'roll, but with manners?'"
        )
    elif comp.id == "headphones":
        world.say(
            f"'{hero.id}, try {comp.method},' {parent.id} said, sliding over the headphones. "
            f"'{hero.id} can still feel the beat, and the baby can keep dreaming.'"
        )
    else:
        world.say(
            f"'{hero.id}, let's {comp.method},' {parent.id} said. "
            f"'{hero.id} can still be loud enough for the stars, just not for the hallway.'"
        )


def tell_accept(world: World, hero: Entity, parent: Entity, inst: Instrument, comp: Compromise) -> None:
    world.say(
        f"{hero.id} laughed. 'Okay,' {hero.pronoun().capitalize()} said. "
        f"'I can be a rock star and still let {parent.id} finish a sentence.'"
    )
    world.say(
        f"They {comp.method}, and soon {hero.id} was {inst.label if inst.id != 'drums' else 'keeping time'} "
        f"with a grin so big it almost counted as stage lights."
    )


def tell_end(world: World, hero: Entity, parent: Entity, inst: Instrument, comp: Compromise) -> None:
    world.say(
        f"By the end, {hero.id}'s song was smaller, sweeter, and somehow cooler. "
        f"The little house stayed calm, the beat kept going, and {parent.id} had to admit it was catchy."
    )


def tell(world: World, hero_name: str, hero_gender: str, parent_type: str, trait: str, pet: str,
         inst: Instrument, comp: Compromise) -> World:
    hero = world.add(Entity("hero", "character", hero_gender, hero_name, attrs={"traits": trait}))
    parent = world.add(Entity("parent", "character", parent_type, "the parent", attrs={"reason": f"{pet} is sleeping"}))
    world.add(Entity("pet", "character", "thing", pet))
    world.facts["hero"] = hero
    world.facts["parent"] = parent
    world.facts["instrument"] = inst
    world.facts["compromise"] = comp
    world.facts["venue"] = world.venue
    tell_setup(world, hero, parent, inst)
    world.para()
    tell_want(world, hero, parent, inst)
    tell_warning(world, parent, hero, inst)
    tell_joke(world, hero, parent)
    world.para()
    tell_compromise(world, hero, parent, inst, comp)
    apply_jam(world, hero, inst, narrate=False)
    tell_accept(world, hero, parent, inst, comp)
    tell_end(world, hero, parent, inst, comp)
    return world


KNOWLEDGE = {
    "rock": [("What is rock'n'roll?", "Rock'n'roll is a kind of lively music with a strong beat, guitars, and a big attitude.")],
    "guitar": [("What does a guitar do?", "A guitar makes music when you strum or pick its strings.")],
    "drums": [("What do drums do?", "Drums keep the beat by making loud, steady sounds when you hit them.")],
    "noise": [("What is noise?", "Noise is sound that can be too loud, especially when someone needs quiet.")],
    "quiet": [("Why do people need quiet sometimes?", "People need quiet so they can sleep, rest, or focus without being distracted.")],
    "headphones": [("What are headphones for?", "Headphones let one person hear music without making the whole room listen.")],
    "porch": [("What is a porch for?", "A porch is a place outside the house where you can sit, talk, or play a little more freely.")],
}

KNOWLEDGE_ORDER = ["rock", "guitar", "drums", "noise", "quiet", "headphones", "porch"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old about {f["hero"].id} who loves rock\'n\'roll, but has to keep the music from getting too loud.',
        f"Tell a humorous dialogue story where {f['hero'].id} wants to play {f['instrument'].label} at {world.venue.place} and {f['parent'].id} asks for more quiet.",
        f'Write a small everyday story about music, jokes, and a compromise, ending with {f["hero"].id} still smiling.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    inst: Instrument = f["instrument"]
    comp: Compromise = f["compromise"]
    qa = [
        QAItem(
            question=f"Who is the story about when {hero.id} wants to play {inst.label}?",
            answer=f"It is about {hero.id}, a little {hero.type} who loves rock'n'roll and wanted to play {inst.label} at {world.venue.place}.",
        ),
        QAItem(
            question=f"Why did {parent.id} ask {hero.id} to keep the music down?",
            answer=f"{parent.id} wanted some quiet in {world.venue.place}, so the music would not bounce around and bother everyone else.",
        ),
        QAItem(
            question=f"What funny thing did {hero.id} say about the music?",
            answer=f'{hero.id} joked, "What if I call it practice and the neighbors call it thunder?" That made the grown-up laugh.',
        ),
        QAItem(
            question=f"What compromise did {parent.id} offer to {hero.id}?",
            answer=f"They agreed on {comp.phrase}, which let {hero.id} keep playing while making the room much quieter.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and relieved, because {hero.id} still got to rock out and the home stayed calm.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"rock", "noise"}
    if world.facts["instrument"].id == "guitar":
        tags.add("guitar")
    if world.facts["instrument"].id == "drums":
        tags.add("drums")
    if world.facts["compromise"].id == "headphones":
        tags.add("headphones")
    if world.facts["compromise"].id == "porch":
        tags.add("porch")
    out = []
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("apartment", "guitar", "unplugged", "Maya", "girl", "mother", "funny", "the cat"),
    StoryParams("garage", "drums", "porch", "Leo", "boy", "father", "silly", "the dog"),
    StoryParams("porch", "guitar", "headphones", "Nina", "girl", "mother", "bouncy", "the goldfish"),
]


def explain_rejection(venue: Venue, inst: Instrument, comp: Compromise) -> str:
    return f"(No story: {comp.label} does not make sense for {inst.label} at {venue.place}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life rock'n'roll storyworld with humor and dialogue.")
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--compromise", choices=COMPROMISES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    chosen_venue = getattr(args, "venue", None) or rng.choice(list(VENUES))
    chosen_inst = getattr(args, "instrument", None) or rng.choice(list(INSTRUMENTS))
    chosen_comp = getattr(args, "compromise", None) or rng.choice(list(COMPROMISES))
    venue = _safe_lookup(VENUES, chosen_venue)
    inst = _safe_lookup(INSTRUMENTS, chosen_inst)
    comp = _safe_lookup(COMPROMISES, chosen_comp)
    if not reasonableness_gate(venue, inst, comp):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "name", None):
        name = getattr(args, "name", None)
        gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    else:
        gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
        name = rng.choice(HEROES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    pet = rng.choice(PETS)
    return StoryParams(chosen_venue, chosen_inst, chosen_comp, name, gender, parent, trait, pet)


def generate(params: StoryParams) -> StorySample:
    world = tell(World(_safe_lookup(VENUES, params.venue)), params.hero, params.hero_gender, params.parent, params.trait, params.pet,
                 _safe_lookup(INSTRUMENTS, params.instrument), _safe_lookup(COMPROMISES, params.compromise))
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(V,I,C) :- venue(V), instrument(I), compromise(C), can_use(C,I,V).
can_use(unplugged,I,V) :- instrument(I), venue(V).
can_use(headphones,guitar,V) :- venue(V).
can_use(porch,I,V) :- venue(V), V != porch.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for vid in VENUES:
        lines.append(asp.fact("venue", vid))
    for iid, inst in INSTRUMENTS.items():
        lines.append(asp.fact("instrument", iid))
        lines.append(asp.fact("loudness", iid, inst.loudness))
    for cid in COMPROMISES:
        lines.append(asp.fact("compromise", cid))
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
    print("MISMATCH:")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        header = f"### variant {idx+1}" if len(samples) > 1 else ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero}: {p.instrument} at {p.venue}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
