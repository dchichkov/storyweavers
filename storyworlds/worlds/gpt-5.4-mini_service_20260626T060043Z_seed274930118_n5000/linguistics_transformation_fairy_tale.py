#!/usr/bin/env python3
"""
storyworlds/worlds/linguistics_transformation_fairy_tale.py
============================================================

A small fairy-tale story world about linguistics and transformation.

The seed premise:
- A child in a fairy-tale place loves words.
- A magical transformation can happen when the child uses the right word form.
- A careless form can make the change go wrong.
- A helper explains the pattern, and the child tries again.
- The ending proves the world changed because the words were chosen well.

This world keeps the prose child-facing and concrete while the simulation tracks
physical meters and emotional memes.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    target: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "woman"}
        male = {"boy", "prince", "king", "father", "man"}
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
    magic: str
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
class Spell:
    id: str
    root: str
    change: str
    chant: str
    result: str
    safe_if: str
    needs_helper: bool = True
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
class Target:
    label: str
    phrase: str
    type: str
    transformed_phrase: str
    emotion: str = "hopeful"
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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


def _r_tangle(world: World) -> list[str]:
    out: list[str] = []
    for hero in list(world.entities.values()):
        if hero.kind != "character":
            continue
        if hero.memes.get("guessing", 0.0) < THRESHOLD:
            continue
        sig = ("tangle", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["confusion"] = hero.memes.get("confusion", 0.0) + 1
        out.append(f"The words twisted and made {hero.id} feel muddled.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    target = world.entities.get("target")
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    spell = world.facts.get("spell")
    if not target or not hero or not spell:
        return out
    if hero.memes.get("precision", 0.0) < THRESHOLD:
        return out
    if helper is None or helper.memes.get("guided", 0.0) < THRESHOLD:
        return out
    sig = ("transform", target.id, spell.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    target.meters["changed"] = 1
    target.meters["glow"] = 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    out.append(f"The spell settled, and {target.label} became something new.")
    return out


CAUSAL_RULES = [
    Rule(name="tangle", apply=_r_tangle),
    Rule(name="transform", apply=_r_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                produced.extend(sent)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_setting() -> Setting:
    return Setting(
        place="the mossy castle garden",
        magic="word magic",
        affords={"transform"},
    )


SPELLS = {
    "add-en": Spell(
        id="add-en",
        root="bright",
        change="add -en",
        chant="brighten",
        result="grew bright and warm",
        safe_if="the child says the word form clearly",
        needs_helper=True,
    ),
    "turn-into": Spell(
        id="turn-into",
        root="still",
        change="turn into",
        chant="turn into",
        result="changed into a different shape",
        safe_if="the child follows the helper's rhyme",
        needs_helper=True,
    ),
    "un-": Spell(
        id="un-",
        root="lace",
        change="add un-",
        chant="unlace",
        result="came loose and easy",
        safe_if="the child remembers the beginning sound",
        needs_helper=True,
    ),
}

TARGETS = {
    "thorn-arch": Target(
        label="the thorn arch",
        phrase="a thorny arch by the gate",
        type="arch",
        transformed_phrase="a rose arch",
    ),
    "stone-step": Target(
        label="the stone step",
        phrase="a cold stone step",
        type="step",
        transformed_phrase="a warm golden step",
    ),
    "gray-frog": Target(
        label="the gray frog",
        phrase="a gray frog beside the pond",
        type="frog",
        transformed_phrase="a green frog with a crown of lilies",
    ),
}

NAMES_GIRL = ["Mira", "Elin", "Ava", "Luna", "Talia", "Nora"]
NAMES_BOY = ["Bram", "Owen", "Lio", "Finn", "Theo", "Pip"]
HELPER_NAMES = ["Grandmother", "the old owl", "the fairy tutor"]
TRAITS = ["curious", "gentle", "brave", "careful", "bright-eyed"]


@dataclass
class StoryParams:
    setting: str
    spell: str
    target: str
    name: str
    gender: str
    helper: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for spell in SPELLS:
            for target in TARGETS:
                combos.append((s, spell, target))
    return combos


SETTINGS = {
    "castle": build_setting(),
}

GIRL_NAMES = NAMES_GIRL
BOY_NAMES = NAMES_BOY


def choose_hero_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(
        f"In the mossy castle garden, little {trait} {hero.id} loved words more than ribbons or jewels."
    )
    world.say(
        f"{hero.pronoun().capitalize()} listened for changes in sounds, as if every word were a tiny door."
    )


def love_words(world: World, hero: Entity) -> None:
    hero.memes["love_words"] = hero.memes.get("love_words", 0.0) + 1
    world.say(
        f"{hero.id} liked linguistics, because it showed how a root could grow into a new shape."
    )


def present_spell(world: World, helper: Entity, hero: Entity, spell: Spell) -> None:
    helper.memes["wise"] = helper.memes.get("wise", 0.0) + 1
    world.say(
        f"One evening, {helper.label} brought out a little spell card and said, "
        f"'{spell.chant} is the change-word for this trick.'"
    )
    world.say(
        f"'If you use {spell.change}, you can make something {spell.result}, but only if you keep the sounds in order.'"
    )


def show_target(world: World, target: Entity) -> None:
    world.say(
        f"At the gate stood {target.phrase}, waiting like it had been there since the first fairy tale."
    )


def attempt(world: World, hero: Entity, spell: Spell, target: Entity) -> None:
    hero.memes["guessing"] = hero.memes.get("guessing", 0.0) + 1
    world.say(
        f"{hero.id} tried to guess the right form and whispered the word too quickly."
    )
    world.say(
        f"The air flickered, but the change did not settle on {target.label}."
    )
    propagate(world, narrate=True)


def guide(world: World, helper: Entity, hero: Entity, spell: Spell) -> None:
    helper.memes["guided"] = helper.memes.get("guided", 0.0) + 1
    hero.memes["precision"] = hero.memes.get("precision", 0.0) + 1
    world.say(
        f"{helper.label} smiled and pointed to the root inside the spell: '{spell.root}'."
    )
    world.say(
        f"'Say it slowly,' {helper.label} said. 'First the root, then the change.'"
    )


def succeed(world: World, hero: Entity, target: Entity, spell: Spell, helper: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    target.meters["changed"] = 1
    target.meters["glow"] = 1
    world.say(
        f"{hero.id} said the word carefully, and the spell answered at once."
    )
    world.say(
        f"{target.label} shimmered and became {target.transformed_phrase}, while {helper.label} clapped softly."
    )


def tell(setting: Setting, spell: Spell, target_cfg: Target, hero_name: str, hero_type: str,
         helper_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, traits=["little", trait]))
    helper = world.add(Entity(id="helper", kind="character", type="woman", label=helper_name))
    target = world.add(Entity(id="target", type=target_cfg.type, label=target_cfg.label, phrase=target_cfg.phrase))
    world.facts.update(hero=hero, helper=helper, target=target, spell=spell, target_cfg=target_cfg)

    introduce(world, hero)
    love_words(world, hero)
    world.para()
    present_spell(world, helper, hero, spell)
    show_target(world, target)
    attempt(world, hero, spell, target)
    world.para()
    guide(world, helper, hero, spell)
    succeed(world, hero, target, spell, helper)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, spell, target = f["hero"], f["helper"], f["spell"], f["target_cfg"]
    return [
        'Write a fairy tale for a young child about linguistics and transformation.',
        f"Tell a gentle story where {hero.label} wants to use the spell '{spell.chant}' "
        f"to change {target.phrase}, but {helper.label} teaches the right word form.",
        f"Write a short story in a fairy-tale voice that includes the idea of a root word and ends with {target.transformed_phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, spell, target_cfg = f["hero"], f["helper"], f["spell"], f["target_cfg"]
    return [
        QAItem(
            question=f"Who loved words in the story?",
            answer=f"{hero.label} loved words and listened for how they changed shape.",
        ),
        QAItem(
            question=f"What did {helper.label} teach {hero.label} about the spell?",
            answer=f"{helper.label} taught {hero.label} to say the root first and then make the change carefully.",
        ),
        QAItem(
            question=f"What happened when the spell finally worked?",
            answer=f"{target_cfg.phrase} became {target_cfg.transformed_phrase}, and the garden looked bright and new.",
        ),
        QAItem(
            question=f"Why did the first try go wrong?",
            answer=f"{hero.label} said the word too quickly, so the change did not settle on the target.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is linguistics?",
            answer="Linguistics is the study of language, words, sounds, and how they change.",
        ),
        QAItem(
            question="What is a root word?",
            answer="A root word is the base part of a word that other word parts can be added to.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means a change from one shape or form into another.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="castle", spell="add-en", target="thorn-arch", name="Mira", gender="girl", helper="Grandmother", trait="curious"),
    StoryParams(setting="castle", spell="turn-into", target="stone-step", name="Theo", gender="boy", helper="the old owl", trait="careful"),
    StoryParams(setting="castle", spell="un-", target="gray-frog", name="Luna", gender="girl", helper="the fairy tutor", trait="bright-eyed"),
]


def valid_story(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.spell in SPELLS and params.target in TARGETS


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the requested fairy-tale combination does not fit this small world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about linguistics and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
    setting = getattr(args, "setting", None) or "castle"
    spell = getattr(args, "spell", None) or rng.choice(list(SPELLS))
    target = getattr(args, "target", None) or rng.choice(list(TARGETS))
    if not valid_story(StoryParams(setting, spell, target, "", "girl", "", "")):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or choose_hero_name(gender, rng)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, spell=spell, target=target, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(SPELLS, params.spell),
        _safe_lookup(TARGETS, params.target),
        params.name,
        params.gender,
        params.helper,
        params.trait,
    )
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


ASP_RULES = r"""
setting(castle).

spell(add_en).
spell(turn_into).
spell(un_prefix).

target(thorn_arch).
target(stone_step).
target(gray_frog).

root(add_en, bright).
root(turn_into, still).
root(un_prefix, lace).

needs_helper(add_en).
needs_helper(turn_into).
needs_helper(un_prefix).

valid(S, Sp, T) :- setting(S), spell(Sp), target(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for sp in SPELLS:
        lines.append(asp.fact("spell", sp))
    for t in TARGETS:
        lines.append(asp.fact("target", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - ac:
        print("  only in python:", sorted(py - ac))
    if ac - py:
        print("  only in clingo:", sorted(ac - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for s, sp, t in triples:
            print(f"  {s:8} {sp:10} {t:12}")
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
            header = f"### {p.name}: {p.spell} on {p.target}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
