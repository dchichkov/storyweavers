#!/usr/bin/env python3
"""
storyworlds/worlds/hub_chum_gag_lesson_learned_humor_folk.py
============================================================

A standalone *story world* for the "Hub & Chum and the Giggle-Gag" tale and
its close, constraint-checked variations.  Folk-tale style, gentle humor, and
a clear lesson learned.

Initial story (used to build a world model):
---
Once upon a time, in a small village, there lived a cheerful little raccoon
named Hub.  Hub was a clever raccoon, but he had one bad habit: he loved to
play pranks.  He was a great practical joker, and he was always coming up
with new ways to make people laugh.  He would often hide things from his
friends, jump out and scare them, and tell silly jokes.

One day, Hub's best friend, a little fox named Chum, was walking through the
village square.  Hub saw Chum and thought, "I'm going to play a great prank
on Chum today!"  He ran and hid behind a big oak tree.  When Chum walked
past, Hub jumped out and said "Boo!"  Chum was so startled that he fell
backwards into a pile of soft hay.  Hub laughed and laughed.

Chum was not angry, but he was a little sad.  He said, "Hub, you are my
friend, but your pranks hurt people sometimes.  I want to be your friend,
but I don't want to be your clown."

Hub thought about what Chum had said.  He realized that he had been so busy
trying to make people laugh that he had forgotten to make them happy.  He
went home and thought of a new plan.

The next day, Hub invited all his friends to the village square.  He had
prepared a special show.  He did a funny dance, told silly jokes, and even
did a magic trick.  But this time, the jokes were gentle, and the pranks
were kind.  Everyone laughed, but no one was hurt.

From that day on, Hub was known as the kindest joker in the village.  And
he and Chum were the best of friends forever.

Causal state updates:
---
    prank pulled            -> victim.fear += 1 ; prankster.pride += 1
    victim hurt             -> victim.hurt += 1 ; chum.sadness += 1
    friend voices concern   -> prankster.thoughtful += 1
    kind joke performed     -> audience.joy += 1 ; prankster.kindness += 1
    audience amused safely  -> prankster.reputation.kind += 1

Scripted social/emotional beats:
---
    victim speaks up        -> actor.thoughtful += 1  (the turn)
    prankster reflects      -> actor.thoughtful += 1  (the turn)
    resolution              -> actor.joy += 1 ; actor.conflict -> 0
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Prank "kinds" the prankster can pull -- each maps to a different victim effect.
PRANK_KINDS = {"scare", "hide_object", "silly_joke"}


# ---------------------------------------------------------------------------
# Entities: characters share one representation.
# ---------------------------------------------------------------------------

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
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # raccoon, fox, bear, owl, ...
    label: str = ""                # short reference, e.g. "Hub"
    phrase: str = ""               # full noun phrase
    traits: list[str] = field(default_factory=list)
    plural: bool = False
    # Two numeric dimensions: physical meters and emotional memes.
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    chum: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "he", "object": "him", "possessive": "his"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.id


# ---------------------------------------------------------------------------
# Parametrization knobs.
# ---------------------------------------------------------------------------
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
    place: str = "the village square"
    indoor: bool = False
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
class Prank:
    """A prank kind the prankster loves to pull."""
    id: str
    verb: str            # after "wanted to ..."              : "scare Chum"
    gerund: str          # after "loved playing ... and ..." : "scaring friends"
    setup: str           # the physical setup: "hide behind the oak tree"
    jump: str            # the reveal: "jump out and shout 'Boo!'"
    effect: str          # what it does to the victim: "scare" | "confuse" | "embarrass"
    mess: str            # a small physical mess it may leave: "hay scattered"
    keyword: str = ""    # topic word for generation prompts
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
class Prop:
    """An object the prankster hides or uses in the prank."""
    label: str
    phrase: str
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
class Riddle:
    """A gentle joke the prankster can use in the kind resolution."""
    question: str
    answer: str


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
    audience: set[str] = field(default_factory=set)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        # Facts recorded during the screenplay, read back by the Q&A generators.
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        """Throwaway clone used for forward-simulation (prediction)."""
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
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


def _r_victim_effect(world: World) -> list[str]:
    """prankster pulls prank -> victim effect + prankster pride."""
    out: list[str] = []
    prankster = next((e for e in world.characters() if e.memes["prank_pulled"] >= THRESHOLD), None)
    if prankster is None:
        return out
    prank_id = world.facts.get("prank_id", "scare")
    for actor in world.characters():
        if actor.id == prankster.id:
            continue
        sig = ("victim_effect", prankster.id, actor.id, prank_id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters[prank_id if prank_id in PRANK_KINDS else "fear"] += 1
        actor.memes["startled"] += 1
        out.append(f"{actor.id} was startled by {prankster.id}'s prank.")
    return out


def _r_friend_sadness(world: World) -> list[str]:
    """chum is the prankster's best friend; if chum is hurt, chum feels sad."""
    for actor in world.characters():
        if actor.id != "Chum":
            continue
        if actor.memes["startled"] < THRESHOLD:
            continue
        sig = ("chum_sad", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["sad"] += 1
        return ["__chum_sad__"]
    return []


def _r_kind_joke_joy(world: World) -> list[str]:
    """A kind joke performed -> audience joy + prankster kindness."""
    out: list[str] = []
    prankster = next((e for e in world.characters() if e.memes["kind_joke"] >= THRESHOLD), None)
    if prankster is None:
        return out
    for actor in world.characters():
        if actor.id == prankster.id:
            continue
        sig = ("kind_joy", prankster.id, actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["joy"] += 1
        out.append(f"{actor.id} laughed along with {prankster.id}.")
    return out


def _r_reputation(world: World) -> list[str]:
    """If the prankster has done both a prank and a kind joke, build a reputation."""
    for actor in world.characters():
        if actor.memes["pride"] < THRESHOLD or actor.memes["kindness"] < THRESHOLD:
            continue
        sig = ("reputation", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["reputation"] += 1
        return ["__reputation__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="victim_effect", tag="physical", apply=_r_victim_effect),
    Rule(name="chum_sadness", tag="social", apply=_r_friend_sadness),
    Rule(name="kind_joy", tag="social", apply=_r_kind_joke_joy),
    Rule(name="reputation", tag="social", apply=_r_reputation),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    """Apply all rules until nothing new fires (forward chaining to fixpoint)."""
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers.
# ---------------------------------------------------------------------------
def prank_compatible(prank: Prank, victim_type: str) -> bool:
    """Some pranks don't make sense for some victims (e.g. scaring a baby)."""
    if victim_type in {"baby", "tadpole"} and prank.effect == "scare":
        return False
    return True


def select_kind_joke(victim: Entity) -> Riddle:
    """Pick a riddle that doesn't embarrass the victim."""
    for riddle in RIDDLES:
        if victim.type in riddle.audience:
            return riddle
    return _safe_lookup(RIDDLES, 0)


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(
        f"Once upon a time, in a small village, there lived a {desc} named {hero.id}."
    )


def loves_pranks(world: World, hero: Entity, prank: Prank) -> None:
    hero.memes["love_play"] += 1
    world.say(
        f"{hero.id} was a clever {hero.type}, but {hero.pronoun('subject')} had one bad habit: "
        f"{hero.pronoun('subject')} loved playing pranks."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} was a great practical joker, and "
        f"{hero.pronoun('subject')} was always coming up with new ways to make people laugh."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} would often {prank.setup}, "
        f"jump out, and {prank.jump} just to see the look on a friend's face."
    )


def introduce_chum(world: World, hero: Entity, chum: Entity) -> None:
    chum.memes["love_play"] += 1
    world.say(
        f"{hero.id}'s best friend was a little {chum.type} named {chum.id}, "
        f"and the two of them shared a pocketful of silly jokes."
    )


def prank_setup(world: World, hero: Entity, chum: Entity, prank: Prank, prop: Optional[Prop]) -> None:
    hero.memes["desire"] += 1
    prop_clause = f" and a stolen {prop.label}" if prop else ""
    world.say(
        f"One bright morning, {chum.id} was walking through {world.setting.place}, "
        f"and {hero.id} spied {chum.pronoun('object')} from afar."
    )
    world.say(
        f'"I\'m going to play a great prank on {chum.id} today!" {hero.id} said, '
        f"and {hero.pronoun('subject')} tiptoed off to {prank.setup}{prop_clause}."
    )


def prank_pull(world: World, hero: Entity, chum: Entity, prank: Prank) -> None:
    hero.memes["prank_pulled"] += 1
    hero.memes["pride"] += 1
    world.facts["prank_id"] = prank.id
    world.say(
        f"When {chum.id} walked past, {hero.id} leapt out and said, "
        f'"Boo!  I am a {prank.id.replace("_", " ")}!"'
    )


def prank_aftermath(world: World, hero: Entity, chum: Entity, prank: Prank) -> None:
    propagate(world, narrate=False)        # fires victim_effect + chum_sadness
    if prank.mess:
        world.say(f"{chum.id} tumbled into the {prank.mess} with a thump.")
    else:
        world.say(f"{chum.id} jumped a little and dropped {chum.pronoun('possessive')} basket.")
    world.say(
        f"{hero.id} laughed and laughed, but {chum.id} was not angry -- "
        f"only a little sad."
    )


def chum_speaks(world: World, hero: Entity, chum: Entity) -> None:
    chum.memes["thoughtful"] += 1
    chum.memes["conflict"] += 1
    hero.memes["thoughtful"] += 1
    world.say(
        f'"{hero.id}, you are my friend," {chum.id} said gently, '
        f'"but your pranks hurt people sometimes.  I want to be your '
        f'friend, but I do not want to be your clown."'
    )


def prankster_reflects(world: World, hero: Entity, chum: Entity) -> None:
    hero.memes["reflection"] += 1
    hero.memes["conflict"] += 1
    world.say(
        f"{hero.id} thought about what {chum.id} had said, and "
        f"{hero.pronoun('subject')} realized that {hero.pronoun('subject')} had been so "
        f"busy trying to make people laugh that {hero.pronoun('subject')} had "
        f"forgotten to make them happy."
    )


def new_plan(world: World, hero: Entity) -> None:
    hero.memes["plan"] += 1
    world.say(
        f"That night, {hero.id} sat by the fire and thought of a brand-new plan. "
        f"The next day, {hero.pronoun('subject')} would invite all the villagers to a "
        f"show that was funny, but kind."
    )


def show_opens(world: World, hero: Entity) -> None:
    world.say(
        f"The next morning, the {world.setting.place} filled with friends, "
        f"and {hero.id} hopped up onto a small wooden stump."
    )


def kind_dance(world: World, hero: Entity) -> None:
    hero.memes["kind_joke"] += 1
    world.say(
        f"{hero.id} did a silly dance, wiggled {hero.pronoun('possessive')} ears, "
        f"and made funny faces.  This time the pranks were gentle, and the "
        f"jokes were kind."
    )


def kind_riddle(world: World, hero: Entity, chum: Entity) -> None:
    hero.memes["kind_joke"] += 1
    riddle = select_kind_joke(chum)
    world.say(
        f'"{riddle.question}" {hero.id} asked, winking at {chum.id}.'
    )
    world.say(
        f'The villagers thought, then someone called out, "{riddle.answer}!"'
    )
    world.say(
        f"Everyone laughed, but no one was hurt, and {chum.id} clapped the loudest."
    )


def resolve(world: World, hero: World, chum: Entity) -> None:  # type: ignore[override]
    pass  # narrative handled by kind_joy propagation + closing beat below


def closing(world: World, hero: Entity, chum: Entity) -> None:
    propagate(world, narrate=False)        # fires kind_joy + reputation
    hero.memes["joy"] += 1
    hero.memes["conflict"] = 0.0
    chum.memes["joy"] += 1
    chum.memes["conflict"] = 0.0
    world.say(
        f"From that day on, {hero.id} was known as the kindest joker in the "
        f"village, and the two friends lived -- and laughed -- happily ever after."
    )


# ---------------------------------------------------------------------------
# The screenplay.
# ---------------------------------------------------------------------------
def tell(setting: Setting, prank: Prank, prop_id: Optional[str],
         hero_name: str = "Hub", hero_type: str = "raccoon",
         chum_type: str = "fox", hero_traits: Optional[list[str]] = None
         ) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["cheerful", "mischievous"]),
    ))
    chum = world.add(Entity(
        id="Chum", kind="character", type=chum_type, label="Chum",
    ))
    if prop_id:
        prop_cfg = _safe_lookup(PROPS, prop_id)
        world.add(Entity(
            id="prop", type="prop", label=prop_cfg.label, phrase=prop_cfg.phrase,
            plural=prop_cfg.plural,
        ))

    # Act 1 -- setup.
    introduce(world, hero)
    loves_pranks(world, hero, prank)
    introduce_chum(world, hero, chum)

    # Act 2 -- the prank and the gentle reckoning.
    world.para()
    prank_setup(world, hero, chum, prank, PROPS.get(prop_id) if prop_id else None)
    prank_pull(world, hero, chum, prank)
    prank_aftermath(world, hero, chum, prank)
    chum_speaks(world, hero, chum)
    prankster_reflects(world, hero, chum)
    new_plan(world, hero)

    # Act 3 -- the kind show, the lesson learned, the resolution.
    world.para()
    show_opens(world, hero)
    kind_dance(world, hero)
    kind_riddle(world, hero, chum)
    closing(world, hero, chum)

    world.facts.update(hero=hero, chum=chum, prank=prank, prop_id=prop_id,
                       setting=setting, resolved=True,
                       had_prank=hero.memes["prank_pulled"] >= THRESHOLD,
                       had_kind=hero.memes["kind_joke"] >= THRESHOLD,
                       lesson="gentle jokes can be funny and kind at the same time")
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "square": Setting(place="the village square", indoor=False, affords={"scare", "hide_object", "silly_joke"}),
    "fair": Setting(place="the harvest fair", indoor=False, affords={"scare", "hide_object", "silly_joke"}),
    "orchard": Setting(place="the apple orchard", indoor=False, affords={"scare", "hide_object"}),
    "schoolhouse": Setting(place="the little schoolhouse", indoor=True, affords={"silly_joke"}),
}

PRANKS = {
    "scare": Prank(
        id="scare",
        verb="scare Chum",
        gerund="scaring friends",
        setup="hide behind the big oak tree",
        jump="shout 'Boo!'",
        effect="scare",
        mess="pile of soft hay",
        keyword="scare",
        tags={"scare", "prank"},
    ),
    "hide_object": Prank(
        id="hide_object",
        verb="hide Chum's lunch pail",
        gerund="hiding things from friends",
        setup="tiptoe around to the picnic blanket",
        jump="snatch the pail and dart behind the wagon",
        effect="confuse",
        mess="crumbs",
        keyword="hide",
        tags={"hide", "prank"},
    ),
    "silly_joke": Prank(
        id="silly_joke",
        verb="tell a silly riddle",
        gerund="telling silly riddles",
        setup="creep up behind the chair",
        jump="whisper a nonsense riddle in Chum's ear",
        effect="embarrass",
        mess="",
        keyword="riddle",
        tags={"riddle", "prank"},
    ),
}

# A prop is something the prankster can lift / hide -- only meaningful for some pranks.
PROPS = {
    "pail": Prop(label="lunch pail", phrase="a small tin lunch pail"),
    "hat": Prop(label="red hat", phrase="a pointed red hat", plural=False),
    "pencil": Prop(label="pencil", phrase="a brand-new pencil"),
}

RIDDLES = [
    Riddle(
        question="What has a head but no eyes, a tail but no fur, and runs without legs?",
        answer="a coin",
        audience={"fox", "raccoon", "bear", "owl", "mouse", "rabbit", "boy", "girl"},
    ),
    Riddle(
        question="What falls but never breaks, and breaks but never falls?",
        answer="night and day",
        audience={"fox", "raccoon", "bear", "owl", "mouse", "rabbit", "boy", "girl"},
    ),
    Riddle(
        question="I am always ahead of you but can never be seen.  What am I?",
        answer="tomorrow",
        audience={"fox", "raccoon", "bear", "owl", "mouse", "rabbit", "boy", "girl"},
    ),
]

HERO_TYPES = ["raccoon", "fox", "bear", "rabbit", "mouse"]
CHUM_TYPES = ["fox", "raccoon", "owl", "rabbit", "mouse"]
HERO_NAMES = ["Hub", "Pip", "Tib", "Bun", "Mim", "Fiz", "Wig", "Nub", "Lox", "Peb"]
CHUM_NAME = "Chum"
TRAITS = ["cheerful", "clever", "mischievous", "spirited", "lively", "bright"]


def valid_combos() -> list[tuple]:
    """(setting, prank, prop) triples that pass the reasonableness constraint."""
    combos = []
    for sid, setting in SETTINGS.items():
        for prank_id in setting.affords:
            prank = _safe_lookup(PRANKS, prank_id)
            for prop_id in list(PROPS) + [None]:
                if prop_id is None:
                    combos.append((sid, prank_id, None))
                else:
                    combos.append((sid, prank_id, prop_id))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story."""
    place: str
    prank: str
    prop: Optional[str]
    name: str
    hero_type: str
    chum_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation.
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


KNOWLEDGE = {
    "prank": [("What is a prank?",
               "A prank is a playful trick.  It can be funny, but the kindest "
               "pranks do not hurt anyone.")],
    "scare": [("Why is it not nice to scare a friend?",
               "Scaring a friend can make their heart pound and their feelings "
               "hurt, even when the scare is meant as a joke.")],
    "hide": [("What does it feel like when a friend hides your things?",
              "It can feel confusing or unfair, because you cannot find what "
              "you need and you may worry it is lost.")],
    "riddle": [("What is a riddle?",
                "A riddle is a short puzzle with a tricky question and a clever "
                "answer that is not always the first one you think of.")],
    "joke": [("What makes a joke kind?",
              "A kind joke makes people laugh together, and nobody is the "
              "butt of the joke or left feeling hurt.")],
    "lesson": [("Why do stories end with a lesson?",
                "Stories end with a lesson to help the listener remember a "
                "small piece of wisdom, like being gentle even when you are "
                "being funny.")],
    "friend": [("What is a good friend?",
                "A good friend is kind to you, listens when you speak, and "
                "stops doing things that hurt you.")],
    "folk": [("What is a folk tale?",
              "A folk tale is an old story told out loud, with simple characters "
              "and a clear lesson at the end.")],
}
KNOWLEDGE_ORDER = ["prank", "scare", "hide", "riddle", "joke", "lesson", "friend", "folk"]


def generation_prompts(world: World) -> list[str]:
    """(1) Generation asks that would produce this story."""
    f = world.facts
    hero, chum, prank = f["hero"], f["chum"], f["prank"]
    kw = prank.keyword
    return [
        f'Write a short folk-tale style story for a 3-to-5-year-old on the '
        f'theme "a prankster learns a kind lesson" that includes the word "{kw}".',
        f'Tell a gentle folk tale where a little {hero.type} named {hero.id} '
        f'plays a prank on {chum.id}, learns that pranks can hurt, and ends by '
        f'putting on a kind show for the village.',
        f'Write a simple story that uses the noun "{kw}" and ends with a '
        f'clear lesson learned about being kind even when you are being funny.',
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    hero, chum, prank, setting = f["hero"], f["chum"], f["prank"], f["setting"]
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} decides to play a prank "
                f"on {chum.id} in {setting.place}?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id} and "
                f"{pos} best friend, a little {chum.type} named {chum.id}. They "
                f"share a pocketful of silly jokes, and the trouble starts when "
                f"{hero.id} wants to play a {prank.id.replace('_', ' ')} prank."
            ),
        ),
        QAItem(
            question=(
                f"What bad habit did the little {hero.type} {hero.id} have before "
                f"{chum.id} spoke up at {setting.place}?"
            ),
            answer=(
                f"{hero.id.capitalize()} loved playing pranks on friends. {sub.capitalize()} "
                f"would often {prank.setup}, jump out, and {prank.jump} just to "
                f"see the look on a friend's face."
            ),
        ),
        QAItem(
            question=(
                f"What did {chum.id} say to {hero.id} after the {prank.id.replace('_', ' ')} "
                f"prank at {setting.place}?"
            ),
            answer=(
                f'{chum.id.capitalize()} said, "{hero.id}, you are my friend, but '
                f'your pranks hurt people sometimes. I want to be your friend, but '
                f'I do not want to be your clown."'
            ),
        ),
        QAItem(
            question=(
                f"What did the little {hero.type} {hero.id} do the next day to "
                f"show {chum.id} a kind lesson at {setting.place}?"
            ),
            answer=(
                f"{hero.id.capitalize()} put on a kind show with a silly dance "
                f"and a gentle riddle. The jokes were kind, and everyone "
                f"laughed, but no one was hurt."
            ),
        ),
        QAItem(
            question=(
                f"What lesson was learned by {hero.id} after the kind show at {setting.place}?"
            ),
            answer=(
                f"{hero.id.capitalize()} learned that gentle jokes can be funny "
                f"and kind at the same time, and that being a good friend is "
                f"more important than being the loudest joker."
            ),
        ),
        QAItem(
            question=(
                f"How did {chum.id} feel at the end of the story with the "
                f"little {hero.type} {hero.id}?"
            ),
            answer=(
                f"{chum.id.capitalize()} felt happy and clapped the loudest at "
                f"the kind show, and the two friends lived and laughed happily ever after."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags = set(f["prank"].tags)
    tags.add("joke")
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags or tag in {"lesson", "folk", "friend"}:
            for q, a in KNOWLEDGE[tag]:
                out.append(QAItem(question=q, answer=a))
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


# ---------------------------------------------------------------------------
# CLI / trace.
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(place="square", prank="scare", prop=None,
                name="Hub", hero_type="raccoon", chum_type="fox", trait="cheerful"),
    StoryParams(place="fair", prank="hide_object", prop="pail",
                name="Pip", hero_type="fox", chum_type="rabbit", trait="mischievous"),
    StoryParams(place="schoolhouse", prank="silly_joke", prop=None,
                name="Tib", hero_type="rabbit", chum_type="owl", trait="bright"),
    StoryParams(place="orchard", prank="scare", prop="hat",
                name="Bun", hero_type="bear", chum_type="mouse", trait="lively"),
    StoryParams(place="fair", prank="hide_object", prop="pencil",
                name="Fiz", hero_type="mouse", chum_type="raccoon", trait="clever"),
]


def explain_rejection(prank: Prank, chum_type: str) -> str:
    if not prank_compatible(prank, chum_type):
        return (f"(No story: a {prank.id.replace('_', ' ')} prank is not "
                f"kind to a {chum_type} -- the worry is too great.)")
    return "(No story: this argument is rejected by the gate.)"


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prank is compatible with a setting when the setting affords it.
prank_in_setting(S, P) :- setting(S), prank(P), affords(S, P).

% A prop is allowed only when the prank kind can use a prop.
prop_ok(P, R) :- prank(P), prop(R), uses_prop(P).

% A (setting, prank, prop) combo is valid when the prank fits the setting.
valid(S, P, R) :- prank_in_setting(S, P), prop_ok(P, R).
valid_no_prop(S, P) :- prank_in_setting(S, P), not any_prop(P).
any_prop(P) :- prank(P), prop(R), uses_prop(P).

% A prank is compatible with a victim type when the prank effect is gentle enough.
prank_victim_ok(P, V) :- prank(P), victim(V), effect_ok(P, V).
effect_ok(P, V) :- prank(P), victim(V), not harsh(P, V).
harsh(P, V) :- prank(P), victim(V), scare_only(V), effect(P, scare).
scare_only(baby). scare_only(tadpole).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for p in sorted(s.affords):
            lines.append(asp.fact("affords", sid, p))
    for pid, p in PRANKS.items():
        lines.append(asp.fact("prank", pid))
        lines.append(asp.fact("effect", pid, p.effect))
        if any(PROPS):
            lines.append(asp.fact("uses_prop", pid))
    for rid, _ in PROPS.items():
        lines.append(asp.fact("prop", rid))
    for chum_t in CHUM_TYPES:
        lines.append(asp.fact("victim", chum_t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (setting, prank, prop) triples."""
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    valid_triples = sorted(set(asp.atoms(model, "valid")))
    # Add the no-prop triples that valid_no_prop covers.
    no_prop_model = asp.one_model(asp_program("#show valid_no_prop/2."))
    no_prop_triples = [(s, p, None) for (s, p) in sorted(set(asp.atoms(no_prop_model, "valid_no_prop")))]
    return sorted(set(valid_triples) | set(no_prop_triples))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with the Python valid_combos()."""
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: Hub & Chum and the Giggle-Gag. "
                    "Folk-tale style, gentle humor, lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prank", choices=PRANKS)
    ap.add_argument("--prop", choices=list(PROPS) + ["none"])
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--chum-type", choices=CHUM_TYPES)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in unspecified choices at random, keeping the combo reasonable."""
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "prank", None):
        combos = [c for c in combos if c[1] == getattr(args, "prank", None)]
    if getattr(args, "prop", None) is not None:
        if getattr(args, "prop", None) == "none":
            combos = [c for c in combos if c[2] is None]
        else:
            combos = [c for c in combos if c[2] == getattr(args, "prop", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, prank_id, prop_id = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    chum_type = getattr(args, "chum_type", None) or rng.choice([t for t in CHUM_TYPES if t != hero_type])
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        prank=prank_id,
        prop=prop_id,
        name=name,
        hero_type=hero_type,
        chum_type=chum_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PRANKS, params.prank), params.prop,
                 params.name, params.hero_type, params.chum_type,
                 [params.trait, "mischievous"])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (setting, prank, prop) combos:\n")
        for place, prank, prop in triples:
            print(f"  {place:12} {prank:14} prop={prop}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

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
            header = f"### {p.name}: {p.prank} at {p.place} (prop: {p.prop})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
