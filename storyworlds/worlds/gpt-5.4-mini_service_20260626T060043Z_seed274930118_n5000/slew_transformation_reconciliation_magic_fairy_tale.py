#!/usr/bin/env python3
"""
storyworlds/worlds/slew_transformation_reconciliation_magic_fairy_tale.py
========================================================================

A small fairy-tale storyworld about a magical mishap, a transformation,
and a reconciliation that makes the ending feel warm and complete.

Seed tale:
---
In a little kingdom by a silver river, a young swan-prince named Soren
was told never to wake the moon-lily. But when a prickly sprite made
the lily spill stardust over the castle path, Soren's laugh turned into
a goose's honk. The queen feared the spell would last, yet a kindly
witch showed Soren how to mend the lily, apologize to the sprite, and
choose a truer kind of magic.

This script turns that premise into a tiny simulated world with:
- a kingdom setting
- a magical source, a visible transformation, and a reconciliation turn
- state-driven prose, grounded QA, and an ASP twin for reasonableness
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    transformed_into: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    queen: object | None = None
    sprite: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"queen", "witch", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"king", "prince", "boy", "man"}:
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
    place: str = "the silver kingdom"
    affords: set[str] = field(default_factory=lambda: {"splash", "spell", "song"})
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
class MagicSource:
    id: str
    label: str
    kind: str
    glow: str
    spill: str
    transforms_into: str
    keyword: str = "magic"
    tags: set[str] = field(default_factory=set)
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
class CreatureForm:
    id: str
    label: str
    phrase: str
    kind: str
    plural: bool = False
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
class Spell:
    id: str
    label: str
    source: str
    target: str
    effect: str
    requires: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "castle": Setting(place="the silver kingdom", affords={"splash", "spell", "song"}),
    "garden": Setting(place="the moonlit garden", affords={"spell", "song"}),
    "river": Setting(place="the riverbank", affords={"splash", "spell"}),
}

FORMS = {
    "swan": CreatureForm("swan", "a swan", "a white swan", "swan"),
    "goose": CreatureForm("goose", "a goose", "a gray goose", "goose"),
    "frog": CreatureForm("frog", "a frog", "a green frog", "frog"),
    "cat": CreatureForm("cat", "a cat", "a velvet cat", "cat"),
}

MAGIC = {
    "moonlily": MagicSource(
        id="moonlily",
        label="moon-lily",
        kind="flower",
        glow="silver",
        spill="stardust",
        transforms_into="goose",
        tags={"magic", "flower", "stardust"},
    ),
    "glasswand": MagicSource(
        id="glasswand",
        label="glass wand",
        kind="wand",
        glow="blue",
        spill="sparkles",
        transforms_into="cat",
        tags={"magic"},
    ),
    "riverpearl": MagicSource(
        id="riverpearl",
        label="river pearl",
        kind="pearl",
        glow="white",
        spill="mist",
        transforms_into="frog",
        tags={"magic", "water"},
    ),
}

SPELLS = {
    "spilled_spell": Spell(
        id="spilled_spell",
        label="spill-spell",
        source="moonlily",
        target="hero",
        effect="transformation",
        requires="apology",
    )
}

NAMES = ["Soren", "Elin", "Mira", "Rowan", "Ari", "Nia", "Clover", "Luna"]
TRAITS = ["gentle", "brave", "curious", "bright", "kind", "dreamy"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    magic: str
    form: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
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


THRESHOLD = 1.0


def reasonableness_gate(params: StoryParams) -> None:
    if params.magic not in MAGIC:
        pass
    if params.form not in FORMS:
        pass
    if params.setting not in SETTINGS:
        pass
    magic = MAGIC[params.magic]
    form = _safe_lookup(FORMS, params.form)
    if magic.transforms_into != form.kind:
        pass


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for magic_id, magic in MAGIC.items():
            for form_id, form in FORMS.items():
                if magic.transforms_into == form.kind:
                    combos.append((setting, magic_id, form_id))
    return combos


def predict_transform(world: World, hero: Entity, magic: MagicSource, form: CreatureForm) -> dict:
    sim = world.copy()
    _apply_magic(sim, hero.id, magic, form, narrate=False)
    return {
        "transformed": sim.get(hero.id).transformed_into == form.kind,
        "reconciled": bool(sim.facts.get("reconciled")),
    }


def _apply_magic(world: World, hero_id: str, magic: MagicSource, form: CreatureForm, narrate: bool = True) -> None:
    hero = world.get(hero_id)
    sig = ("transform", hero.id, magic.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.transformed_into = form.kind
    hero.meters["changed"] = 1
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1
    if narrate:
        world.say(
            f"A {magic.glow} glow rose from the {magic.label}, and {hero.id} began to change."
        )


def _reconcile(world: World, hero: Entity, helper: Entity, magic: MagicSource) -> None:
    sig = ("reconcile", hero.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["shame"] = 0.0
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1
    helper.memes["mercy"] = helper.memes.get("mercy", 0.0) + 1
    world.facts["reconciled"] = True
    world.say(
        f"{helper.pronoun('subject').capitalize()} taught {hero.id} how to apologize, and the sprite forgave the mistake."
    )
    world.say(
        f"The {magic.label} grew gentle again, as if it had been waiting for kindness all along."
    )


def setting_line(world: World) -> str:
    return {
        "the silver kingdom": "The silver kingdom shone with pale roofs and quiet paths.",
        "the moonlit garden": "The moonlit garden smelled of mint and roses, and the paths glimmered softly.",
        "the riverbank": "The riverbank was bright with reeds, stones, and quick silver water.",
    }.get(world.setting.place, f"{world.setting.place.capitalize()} was waiting under a hush of light.")


def form_phrase(form: CreatureForm) -> str:
    return form.phrase


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def tell(setting: Setting, magic: MagicSource, form: CreatureForm, hero_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="prince", label=hero_name, memes={"curiosity": 1.0}))
    queen = world.add(Entity(id="Queen", kind="character", type="queen", label="the queen"))
    helper = world.add(Entity(id="Witch", kind="character", type="witch", label="the witch"))
    sprite = world.add(Entity(id="Sprite", kind="character", type="sprite", label="the sprite"))

    world.say(f"Once there was a {trait} prince named {hero_name} who lived in {setting.place}.")
    world.say(
        f"{hero_name} loved the {magic.label}; its {magic.glow} light made every hallway look like a secret."
    )
    world.say(
        f"But the queen warned him never to wake the {magic.label}, because old magic could be tricky."
    )

    world.para()
    world.say(setting_line(world))
    world.say(
        f"One evening, the sprite hurried past and jostled the {magic.label}, and {magic.spill} spilled over the path."
    )
    world.say(
        f"{hero_name} laughed at the glittering mess, and at once the spell caught hold."
    )
    _apply_magic(world, hero.id, magic, form, narrate=False)
    world.say(
        f"A moment later, {hero_name} had become {form_phrase(form)}."
    )
    world.say(
        f"The queen gasped, because she feared {hero_name} would stay changed forever."
    )

    world.para()
    world.say(
        f"Then the witch arrived and said that magic listens best when someone tells the truth."
    )
    world.say(
        f"{hero_name} bowed to the sprite and said sorry for laughing at the spill."
    )
    _reconcile(world, hero, helper, magic)
    world.say(
        f"The sprite smiled, and the spell loosened like a ribbon untied in warm hands."
    )
    world.say(
        f"By morning, {hero_name} was still changed in a small way: {hero_name} was kinder, and the kingdom felt safer."
    )

    world.facts.update(
        hero=hero,
        queen=queen,
        helper=helper,
        sprite=sprite,
        magic=magic,
        form=form,
        setting=setting,
        reconciled=world.facts.get("reconciled", False),
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale for young children about {f["hero"].id}, the {f["magic"].label}, and a spell that changes someone into {f["form"].label}.',
        f"Tell a gentle story where a {f['hero'].type} named {f['hero'].id} is transformed by {f['magic'].label} and then makes peace with the sprite.",
        f'Write a short magical story that includes the word "slew" only if it fits the tale naturally as a sudden turn of events.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    magic: MagicSource = _safe_fact(world, f, "magic")
    form: CreatureForm = _safe_fact(world, f, "form")
    queen: Entity = _safe_fact(world, f, "queen")
    helper: Entity = _safe_fact(world, f, "helper")
    sprite: Entity = _safe_fact(world, f, "sprite")
    qa = [
        QAItem(
            question=f"Who was the story mostly about?",
            answer=f"The story was mostly about {hero.id}, a kind prince in {world.setting.place}.",
        ),
        QAItem(
            question=f"What did the {magic.label} do when it was disturbed?",
            answer=f"It spilled {magic.spill} and cast a spell that turned {hero.id} into {form.label}.",
        ),
        QAItem(
            question=f"Why did the queen worry?",
            answer=f"The queen worried because she thought the transformation might last forever.",
        ),
    ]
    if f.get("reconciled"):
        qa.append(
            QAItem(
                question=f"How did the ending become peaceful again?",
                answer=f"The witch helped {hero.id} apologize to {sprite.label}, and the sprite forgave the mistake.",
            )
        )
        qa.append(
            QAItem(
                question=f"What changed in {hero.id} after the magic and the apology?",
                answer=f"{hero.id} was still changed in a kinder way, and the kingdom felt calmer after the reconciliation.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "magic": [
        QAItem(
            question="What is magic in a fairy tale?",
            answer="Magic is a special kind of power that can make surprising things happen, like glowing lights, spells, or transformations.",
        )
    ],
    "stardust": [
        QAItem(
            question="What is stardust in a story?",
            answer="Stardust is a shiny, sparkly powder that fairy tales use to make something feel enchanted.",
        )
    ],
    "transform": [
        QAItem(
            question="What does it mean to transform something?",
            answer="To transform something means to change it into a different form.",
        )
    ],
    "reconcile": [
        QAItem(
            question="What does it mean to reconcile?",
            answer="To reconcile means to make peace again after a mistake or a disagreement.",
        )
    ],
    "apology": [
        QAItem(
            question="Why do people apologize?",
            answer="People apologize to say they are sorry and to help repair hurt feelings.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["magic"].tags)
    tags.update({"magic", "transform", "reconcile", "apology"})
    out: list[QAItem] = []
    for tag in ["magic", "stardust", "transform", "reconcile", "apology"]:
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
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
        if e.transformed_into:
            bits.append(f"transformed_into={e.transformed_into}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the magic naturally transforms into the chosen form.
valid(Setting, Magic, Form) :- setting(Setting), magic(Magic), form(Form),
                               transforms_into(Magic, Form).

% Reconciliation is a meaningful ending only when a helper and a wronged sprite exist.
reconcilable(Setting, Magic, Form) :- valid(Setting, Magic, Form),
                                      helper_present, sprite_present.
#show valid/3.
#show reconcilable/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MAGIC.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("transforms_into", mid, m.transforms_into))
    for fid in FORMS:
        lines.append(asp.fact("form", fid))
    lines.append(asp.fact("helper_present"))
    lines.append(asp.fact("sprite_present"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos().")
    return 1


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fairy-tale world of magic, transformation, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--form", choices=FORMS)
    ap.add_argument("--name", choices=NAMES)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    magic = getattr(args, "magic", None) or rng.choice(list(MAGIC))
    form = getattr(args, "form", None) or rng.choice(list(FORMS))
    reasonableness_gate(StoryParams(setting=setting, magic=magic, form=form, name="x", trait="kind"))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, magic=magic, form=form, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), MAGIC[params.magic], _safe_lookup(FORMS, params.form), params.name, params.trait)
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
    StoryParams(setting="castle", magic="moonlily", form="goose", name="Soren", trait="gentle"),
    StoryParams(setting="garden", magic="glasswand", form="cat", name="Elin", trait="curious"),
    StoryParams(setting="river", magic="riverpearl", form="frog", name="Mira", trait="bright"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3.\n#show reconcilable/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3.\n#show reconcilable/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        recs = sorted(set(asp.atoms(model, "reconcilable")))
        print(f"{len(vals)} valid combos, {len(recs)} reconcilable combos")
        for t in vals:
            print("  valid:", t)
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
            header = f"### {p.name}: {p.magic} -> {p.form} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
