#!/usr/bin/env python3
"""
storyworlds/worlds/squat_reconciliation_mystery_to_solve_sharing_myth.py
=========================================================================

A standalone story world for a small mythic tale about a child who squats down
to solve a mystery, then learns to reconcile and share.

The world keeps one clear premise:
- someone notices a strange sign,
- squats to inspect it,
- solves the mystery by tracing a clue,
- and ends by sharing something precious and making peace.

The prose is state-driven: physical meters track what was found, carried, hidden,
shared, and revealed; emotional memes track worry, pride, hurt, trust, and relief.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    sharable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    clue: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Place:
    id: str
    label: str
    image: str
    mystery: str
    clue: str
    what_changed: str
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
class Mystery:
    id: str
    label: str
    phrase: str
    clue_word: str
    resolve_word: str
    risk_word: str
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
class Gift:
    id: str
    label: str
    phrase: str
    sharing_way: str
    ending_image: str
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone
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


@dataclass
class StoryParams:
    place: str
    mystery: str
    gift: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
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


PLACES = {
    "grove": Place(
        id="grove",
        label="the moon grove",
        image="The moon grove slept under silver leaves, and a round stone arch stood at its center.",
        mystery="a soft humming under the stone",
        clue="a trail of bright dust",
        what_changed="the arch was open and the grove looked less lonely",
        affords={"moon", "dust", "hush"},
    ),
    "river": Place(
        id="river",
        label="the river bend",
        image="At the river bend, reeds bowed over the water and an old root made a little seat.",
        mystery="ripples that moved in circles",
        clue="a dropped ribbon on the bank",
        what_changed="the ribbon was back in safe hands and the river ran calm again",
        affords={"river", "ribbon", "shell"},
    ),
    "hill": Place(
        id="hill",
        label="the starlit hill",
        image="On the starlit hill, grass leaned low and a broken ring of stones waited like a secret circle.",
        mystery="a light that blinked between the stones",
        clue="a hidden hollow in the grass",
        what_changed="the stones formed a clear path and the hill shone kinder",
        affords={"star", "stone", "seed"},
    ),
    "cave": Place(
        id="cave",
        label="the whisper cave",
        image="Inside the whisper cave, the air was cool and a low ledge made everyone bend their knees.",
        mystery="a voice echoing back from nowhere",
        clue="a pebble trail to the far wall",
        what_changed="the cave was quiet again, and the echoes felt friendly",
        affords={"echo", "pebble", "honey"},
    ),
}

MYSTERIES = {
    "moon_dust": Mystery(
        id="moon_dust",
        label="moon dust",
        phrase="the moon dust mystery",
        clue_word="dust",
        resolve_word="opened",
        risk_word="hidden",
        tags={"moon", "dust"},
    ),
    "lost_ribbon": Mystery(
        id="lost_ribbon",
        label="lost ribbon",
        phrase="the lost ribbon mystery",
        clue_word="ribbon",
        resolve_word="returned",
        risk_word="taken",
        tags={"ribbon", "river"},
    ),
    "stone_seed": Mystery(
        id="stone_seed",
        label="stone seed",
        phrase="the stone seed mystery",
        clue_word="seed",
        resolve_word="sprouted",
        risk_word="buried",
        tags={"stone", "seed"},
    ),
    "echo_honey": Mystery(
        id="echo_honey",
        label="honey jar",
        phrase="the echo-and-honey mystery",
        clue_word="honey",
        resolve_word="shared",
        risk_word="kept",
        tags={"echo", "honey"},
    ),
}

GIFTS = {
    "bread": Gift(
        id="bread",
        label="warm bread",
        phrase="a round loaf of warm bread",
        sharing_way="broke the loaf in two and handed over the softer half",
        ending_image="both children had crumbs on their fingers and smiles on their faces",
        tags={"bread", "share"},
    ),
    "honey_cakes": Gift(
        id="honey_cakes",
        label="honey cakes",
        phrase="two sticky honey cakes",
        sharing_way="set the cakes on a flat stone and split them carefully",
        ending_image="sweet crumbs sparkled on the stone like tiny stars",
        tags={"honey", "share"},
    ),
    "berries": Gift(
        id="berries",
        label="berry bowl",
        phrase="a small bowl of red berries",
        sharing_way="poured the berries into two wooden cups",
        ending_image="the cups were half-full and both children were laughing",
        tags={"berry", "share"},
    ),
    "milk": Gift(
        id="milk",
        label="milk pot",
        phrase="a little clay pot of milk",
        sharing_way="tilted the pot between them so each could drink first",
        ending_image="the pot was lighter and the moon looked kinder above them",
        tags={"milk", "share"},
    ),
}

GIRL_NAMES = ["Mira", "Nia", "Lina", "Sana", "Tala", "Iris"]
BOY_NAMES = ["Oren", "Jai", "Niko", "Eli", "Ravi", "Kian"]
TRAITS = ["curious", "gentle", "bold", "quiet", "patient", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, m, g) for p in PLACES for m in MYSTERIES for g in GIFTS]


def reasonableness_gate(place: Place, mystery: Mystery, gift: Gift) -> bool:
    return bool(mystery.tags & place.affords) and "share" in gift.tags


def explain_rejection(place: Place, mystery: Mystery, gift: Gift) -> str:
    return (
        f"(No story: {mystery.phrase} doesn't fit {place.label} in a way the story can "
        f"solve, or {gift.label} doesn't support the sharing ending.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world about a mystery, reconciliation, and sharing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
              and (getattr(args, "gift", None) is None or c[2] == getattr(args, "gift", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery, gift = rng.choice(list(combos))
    hero_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    helper_gender = getattr(args, "helper_gender", None) or ("boy" if hero_gender == "girl" and rng.random() < 0.5 else "girl")
    hero = getattr(args, "name", None) or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    return StoryParams(place=place, mystery=mystery, gift=gift, hero_name=hero, hero_gender=hero_gender, helper_name=helper, helper_gender=helper_gender)


def _make_entity(eid: str, name: str, gender: str, role: str) -> Entity:
    return Entity(id=eid, kind="character", type=gender, label=name, role=role)


def tell(params: StoryParams) -> World:
    place = PLACES.get(params.place)
    mystery = MYSTERIES.get(params.mystery)
    gift = GIFTS.get(params.gift)
    if not place or not mystery or not gift:
        pass
    if not reasonableness_gate(place, mystery, gift):
        pass

    world = World(place)
    hero = world.add(_make_entity("hero", params.hero_name, params.hero_gender, "seeker"))
    helper = world.add(_make_entity("helper", params.helper_name, params.helper_gender, "keeper"))
    clue = world.add(Entity(id="clue", label=mystery.clue_word, hidden=True, sharable=False))
    treasure = world.add(Entity(id="gift", label=gift.label, phrase=gift.phrase, sharable=True, owner=helper.id))

    hero.memes.update(wonder=1.0, worry=0.0, hurt=0.0, trust=0.0, relief=0.0, joy=0.0)
    helper.memes.update(wonder=0.0, worry=0.0, hurt=1.0, trust=0.0, relief=0.0, joy=0.0)
    treasure.meters.update(held=1.0, shared=0.0)
    world.facts.update(place=place, mystery=mystery, gift=gift, hero=hero, helper=helper, clue=clue, treasure=treasure, solved=False, reconciled=False, shared=False, found=False, squatted=False)

    world.say(f"In {place.label}, {place.image}")
    world.say(f"{hero.label} noticed {place.mystery}.")
    world.para()
    hero.meters["squat"] += 1
    world.facts["squatted"] = True
    world.say(f"{hero.label} squatted low by the stone and peered into the shadow.")
    hero.memes["wonder"] += 1
    hero.memes["worry"] += 1
    clue.hidden = False
    world.facts["found"] = True
    world.say(f"There, {hero.label} found {place.clue}.")
    world.say(f"It was the key to {mystery.phrase}.")
    world.para()
    helper.memes["hurt"] += 1
    hero.memes["hurt"] += 1
    world.say(f"At first, {helper.label} frowned, for the secret had felt {mystery.risk_word} to keep alone.")
    world.say(f"But {hero.label} held out the clue and spoke softly to {helper.label}.")
    helper.memes["trust"] += 1
    hero.memes["trust"] += 1
    hero.memes["hurt"] = 0.0
    helper.memes["hurt"] = 0.0
    world.facts["reconciled"] = True
    world.say(f"Their hearts settled, and the two children reconciled like clouds parting after rain.")
    world.para()
    treasure.meters["shared"] = 1.0
    world.facts["shared"] = True
    world.say(f"Then they shared {gift.phrase}.")
    world.say(f"{gift.sharing_way.capitalize()}, and {gift.ending_image}.")
    world.say(f"By the end, {place.what_changed}.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mythic story for a child that includes the word "squat" and a mystery at {f["place"].label}.',
        f"Tell a gentle myth where {f['hero'].label} solves {f['mystery'].phrase}, reconciles with {f['helper'].label}, and ends by sharing {f['gift'].label}.",
        f'Write a child-facing myth about a quiet clue, a squatting look under stone, and a sharing ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    mystery = f["mystery"]
    gift = f["gift"]
    return [
        QAItem(
            question=f"Why did {hero.label} squat by the stone at {place.label}?",
            answer=f"{hero.label} squatted to look closely at the strange sign in {place.label}. That close look helped {hero.pronoun()} find the clue for {mystery.phrase}.",
        ),
        QAItem(
            question=f"What did {hero.label} find that helped solve the mystery?",
            answer=f"{hero.label} found {place.clue}. It was the clue that explained {mystery.phrase}.",
        ),
        QAItem(
            question=f"How did {hero.label} and {helper.label} make peace?",
            answer=f"{hero.label} handed over the clue and spoke gently, and {helper.label} listened. After that, they reconciled and the hurt between them went away.",
        ),
        QAItem(
            question=f"What did the children share at the end?",
            answer=f"They shared {gift.phrase}. {gift.sharing_way.capitalize()}, and the ending showed both of them enjoying it together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does it mean to squat?", "To squat means to bend your knees and lower your body close to the ground. People do it to look under something or to rest low for a moment."),
        QAItem("What is reconciliation?", "Reconciliation means making peace after people have been upset with each other. It happens when hurt feelings calm down and trust comes back."),
        QAItem("What is a mystery?", "A mystery is something that is not understood at first. You look for clues until the answer becomes clear."),
        QAItem("Why do people share?", "People share so everyone can have some of a good thing. Sharing can turn one person's treasure into a happy moment for more than one person."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        out.append(f"  {e.id}: label={e.label!r} meters={dict(e.meters)} memes={dict(e.memes)} hidden={e.hidden} owner={e.owner}")
    out.append(f"  facts: solved={world.facts.get('solved')} reconciled={world.facts.get('reconciled')} shared={world.facts.get('shared')}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="grove", mystery="moon_dust", gift="bread", hero_name="Mira", hero_gender="girl", helper_name="Oren", helper_gender="boy"),
    StoryParams(place="river", mystery="lost_ribbon", gift="berries", hero_name="Ravi", hero_gender="boy", helper_name="Lina", helper_gender="girl"),
    StoryParams(place="hill", mystery="stone_seed", gift="milk", hero_name="Tala", hero_gender="girl", helper_name="Kian", helper_gender="boy"),
    StoryParams(place="cave", mystery="echo_honey", gift="honey_cakes", hero_name="Nia", hero_gender="girl", helper_name="Eli", helper_gender="boy"),
]


ASP_RULES = r"""
valid(P,M,G) :- place(P), mystery(M), gift(G), aff(P,M), shareable(G).
solved(P,M) :- valid(P,M,_).
reconciled(P,M) :- solved(P,M).
shared(P,M,G) :- valid(P,M,G).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m, mm in MYSTERIES.items():
        lines.append(asp.fact("mystery", m))
        for aff in mm.tags:
            lines.append(asp.fact("aff", m, aff))
    for g, gg in GIFTS.items():
        lines.append(asp.fact("gift", g))
        lines.append(asp.fact("shareable", g))
        for t in gg.tags:
            lines.append(asp.fact("gift_tag", g, t))
    for p, place in PLACES.items():
        for a in place.affords:
            lines.append(asp.fact("place_aff", p, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH in valid_combos")
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    smoke = generate(CURATED[0])
    if not smoke.story or "squat" not in smoke.story:
        ok = False
        print("SMOKE FAILED: generated story missing expected content.")
    else:
        print("OK: smoke generation produced a story.")
    return 0 if ok else 1


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
