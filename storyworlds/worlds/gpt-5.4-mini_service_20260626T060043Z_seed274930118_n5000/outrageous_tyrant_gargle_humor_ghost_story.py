#!/usr/bin/env python3
"""
storyworlds/worlds/outrageous_tyrant_gargle_humor_ghost_story.py
================================================================

A standalone story world built from the seed words:
outrageous, tyrant, gargle

Domain: a small haunted place where a bossy ghost and a child discover that
humor can soften a spooky mood.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    cup: object | None = None
    scarf: object | None = None
    tyrant: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Place:
    name: str
    eerie: str
    supports: set[str] = field(default_factory=set)
    SETTING: object | None = None
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
class ObjectThing:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    protective: bool = False
    blocks: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
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
class Trick:
    id: str
    verb: str
    gerund: str
    mess: str
    mood_shift: str
    prompt_word: str
    tags: set[str] = field(default_factory=set)
    TRICK: object | None = None
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_laughter(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("humor", 0.0) >= THRESHOLD and e.memes.get("fear", 0.0) >= THRESHOLD:
            sig = ("laugh", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["fear"] = 0.0
            e.memes["relief"] = e.memes.get("relief", 0.0) + 1
            out.append(f"{e.id} burst into a laugh that sounded brighter than a candle.")
    return out


def _r_soften_tyrant(world: World) -> list[str]:
    out: list[str] = []
    tyrant = world.entities.get("tyrant")
    child = world.entities.get("child")
    if not tyrant or not child:
        return out
    if child.memes.get("humor", 0.0) < THRESHOLD:
        return out
    if tyrant.memes.get("bossy", 0.0) < THRESHOLD:
        return out
    sig = ("soften",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tyrant.memes["bossy"] = 0.0
    tyrant.memes["cheer"] = tyrant.memes.get("cheer", 0.0) + 1
    out.append("The bossy ghost forgot to glare and started to grin instead.")
    return out


CAUSAL_RULES = [_r_laughter, _r_soften_tyrant]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_shift(world: World) -> bool:
    sim = world.copy()
    child = sim.get("child")
    child.memes["humor"] = child.memes.get("humor", 0.0) + 1
    propagate(sim, narrate=False)
    tyrant = sim.get("tyrant")
    return tyrant.memes.get("bossy", 0.0) < THRESHOLD


SETTING = Place(
    name="the old moon house",
    eerie="The old moon house stood under a gray sky, with a crooked chimney and one front window that looked like an eyebrow.",
    supports={"haunt", "humor", "gargle"},
)

TRICK = Trick(
    id="gargle",
    verb="gargle moon water",
    gerund="gargling moon water",
    mess="splashy",
    mood_shift="silly",
    prompt_word="gargle",
    tags={"gargle", "humor", "ghost"},
)

PROPS = {
    "cup": ObjectThing(
        id="cup",
        label="tin cup",
        phrase="a little tin cup of moon water",
        type="cup",
        region="hand",
        guards={"throat"},
    ),
    "scarf": ObjectThing(
        id="scarf",
        label="warm scarf",
        phrase="a soft warm scarf",
        type="scarf",
        region="neck",
        protective=True,
        blocks={"cold"},
    ),
}

NAMES = ["Milo", "Nina", "Tess", "Eli", "June", "Pip", "Luna", "Owen"]
TRAITS = ["curious", "brave", "gentle", "sly", "cheerful", "wobbly"]


@dataclass
class StoryParams:
    name: str
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


def introduce(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.traits[0]} child who loved strange old houses."
    )
    world.say(
        f"On a windy evening, {child.id} walked to {world.place.name}, where the halls felt chilly and funny at the same time."
    )


def meet_ghost(world: World, child: Entity, tyrant: Entity) -> None:
    world.say(
        f"Inside, {child.id} found an outrageous tyrant ghost hovering near the stairs."
    )
    world.say(
        f"The tyrant ghost puffed itself up and barked, \"No tapping, no giggling, no crumbs, and no fun!\""
    )
    tyrant.memes["bossy"] += 1
    child.memes["fear"] += 1


def want_to_help(world: World, child: Entity) -> None:
    child.memes["desire"] = child.memes.get("desire", 0.0) + 1
    world.say(
        f"{child.id} felt a tiny shiver, but also a funny idea. Maybe the ghost was not mean, only stuck in a grumpy mood."
    )


def offer_gargle(world: World, child: Entity, tyrant: Entity) -> None:
    cup = world.get("cup")
    world.say(
        f"{child.id} held up the tin cup and said, \"If you gargle moon water, your spooky voice might sound less scratchy.\""
    )
    child.memes["humor"] += 1
    child.meters["kindness"] = child.meters.get("kindness", 0.0) + 1
    tyrant.memes["curious"] = tyrant.memes.get("curious", 0.0) + 1
    cup.worn_by = child.id


def tyrant_resists(world: World, tyrant: Entity) -> None:
    if tyrant.memes.get("bossy", 0.0) >= THRESHOLD:
        world.say(
            f"The tyrant ghost snorted, \"I do not gargle! I command!\""
        )
        world.say(
            f"But its voice cracked like a dry leaf, which made the complaint sound a little ridiculous."
        )


def gag_and_change(world: World, child: Entity, tyrant: Entity) -> None:
    if not predict_shift(world):
        pass
    child.memes["humor"] += 1
    tyrant.memes["bossy"] = 0.0
    propagate(world, narrate=True)
    world.say(
        f"{child.id} made a dramatic gargling noise: \"glub-glub-gloo!\""
    )
    world.say(
        f"The tyrant ghost blinked, then gave a snorty little laugh that floated up to the ceiling beams."
    )


def ending(world: World, child: Entity, tyrant: Entity) -> None:
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1
    tyrant.memes["cheer"] = tyrant.memes.get("cheer", 0.0) + 1
    world.say(
        f"After that, the ghost became only a playful tyrant, bossy in a silly way and never truly frightful."
    )
    world.say(
        f"{child.id} and the ghost gargled moon water together, then laughed so hard that the old moon house seemed brighter than before."
    )


def tell(name: str, trait: str) -> World:
    world = World(SETTING)
    child = world.add(Entity(id="child", kind="character", type="child", traits=[trait]))
    tyrant = world.add(Entity(id="tyrant", kind="character", type="ghost", label="outrageous tyrant ghost"))
    cup = world.add(Entity(id="cup", type="cup", label="tin cup"))
    scarf = world.add(Entity(id="scarf", type="scarf", label="warm scarf"))

    scarf.worn_by = child.id
    child.memes["fear"] = 0.0
    tyrant.memes["bossy"] = 1.0

    introduce(world, child)
    world.para()
    meet_ghost(world, child, tyrant)
    want_to_help(world, child)
    tyrant_resists(world, tyrant)
    offer_gargle(world, child, tyrant)
    world.para()
    gag_and_change(world, child, tyrant)
    ending(world, child, tyrant)

    world.facts.update(
        child=child,
        tyrant=tyrant,
        cup=cup,
        scarf=scarf,
        place=SETTING,
        trick=TRICK,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short humorous ghost story for a young child that includes the word "gargle".',
        f"Tell a story where a child named {world.facts['child'].id} meets an outrageous tyrant ghost and uses humor to change the mood.",
        "Write a cozy spooky tale where a scary-seeming ghost turns silly after a child suggests gargling moon water.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = _safe_fact(world, world.facts, "child")
    tyrant = _safe_fact(world, world.facts, "tyrant")
    return [
        QAItem(
            question="Where did the child go on the windy evening?",
            answer=f"The child went to {world.place.name}, the old moon house with the crooked chimney.",
        ),
        QAItem(
            question="What kind of ghost did the child meet?",
            answer="The child met an outrageous tyrant ghost that acted bossy and scary at first.",
        ),
        QAItem(
            question="What did the child suggest the ghost should do?",
            answer="The child suggested that the ghost should gargle moon water, because that might make the spooky voice sound less scratchy.",
        ),
        QAItem(
            question="How did the ghost change by the end?",
            answer="By the end, the tyrant ghost stopped being so bossy, laughed, and became playful instead of frightening.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gargle?",
            answer="A gargle is when you move water or liquid in your throat and mouth to make a bubbly sound.",
        ),
        QAItem(
            question="Why can humor help in a scary moment?",
            answer="Humor can help because a funny idea can ease fear and make people feel braver and calmer.",
        ),
        QAItem(
            question="What is a tyrant?",
            answer="A tyrant is a bossy ruler who likes to order everyone around and does not act kindly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        out.append(f"  {e.id:6} ({e.type}) {' '.join(bits)}")
    return "\n".join(out)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    lines.append(asp.fact("place", "moon_house"))
    lines.append(asp.fact("supports", "moon_house", "haunt"))
    lines.append(asp.fact("supports", "moon_house", "humor"))
    lines.append(asp.fact("supports", "moon_house", "gargle"))
    lines.append(asp.fact("character", "child"))
    lines.append(asp.fact("character", "tyrant"))
    lines.append(asp.fact("kind", "tyrant", "ghost"))
    lines.append(asp.fact("trait", "tyrant", "outrageous"))
    lines.append(asp.fact("trait", "tyrant", "bossy"))
    lines.append(asp.fact("trick", "gargle"))
    lines.append(asp.fact("verb", "gargle", "gargle_moon_water"))
    lines.append(asp.fact("mess", "gargle", "splashy"))
    lines.append(asp.fact("mood", "gargle", "silly"))
    return "\n".join(lines)


ASP_RULES = r"""
supported(P,T) :- place(P), supports(P,T).
ghost_story(P) :- supported(P,haunt), supported(P,humor), supported(P,gargle).
bossy_ghost(X) :- character(X), kind(X,ghost), trait(X,bossy).
funny_fix(T) :- trick(T), mood(T,silly).
good_story :- ghost_story(moon_house), bossy_ghost(tyrant), funny_fix(gargle).
#show ghost_story/1.
#show bossy_ghost/1.
#show funny_fix/1.
#show good_story/0.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    atoms = set((sym.name, len(sym.arguments)) for sym in model)
    required = {("ghost_story", 1), ("bossy_ghost", 1), ("funny_fix", 1), ("good_story", 0)}
    if required.issubset(atoms):
        print("OK: ASP twin matches the Python world.")
        return 0
    print("MISMATCH: ASP twin is incomplete.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous ghost story world with an outrageous tyrant and a gargle.")
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(name=name, trait=trait, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.trait)
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
    StoryParams(name="Milo", trait="curious"),
    StoryParams(name="Nina", trait="brave"),
    StoryParams(name="Pip", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        print(" ".join(sorted(str(a) for a in model)))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            p = resolve_params(args, random.Random(seed))
            p.seed = seed
            s = generate(p)
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

    for i, s in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            header = f"### {s.params.name} ({s.params.trait})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
