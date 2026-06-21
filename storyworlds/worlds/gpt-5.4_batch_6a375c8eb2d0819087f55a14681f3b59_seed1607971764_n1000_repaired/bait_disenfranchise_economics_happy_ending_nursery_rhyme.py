#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bait_disenfranchise_economics_happy_ending_nursery_rhyme.py
=======================================================================================

A standalone story world for a nursery-rhyme-like tale about a village fair,
a tempting bait, a threatened vote, and a happy, fair ending.

The tiny domain:
- Small animal children come to a village fair with voting acorns.
- The village must choose how to spend a shared little budget: bridge boards,
  library cart wheels, or a rain barrel for the garden.
- A sly trader uses bait to distract the children and tries to hide the vote
  basket, which would disenfranchise the smallest voices.
- A careful helper notices what happened and restores the vote in a sensible way.
- The ending is always happy: the children learn a little word, "economics",
  and the town keeps everyone's say.

The world enforces reasonableness:
- Not every bait fits every place.
- Not every remedy works in every place or for every bait.
- Explicit invalid choices raise StoryError with a plain explanation.
- A Python gate and an inline ASP twin agree on valid combos and outcomes.

Run it
------
    python storyworlds/worlds/gpt-5.4/bait_disenfranchise_economics_happy_ending_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/bait_disenfranchise_economics_happy_ending_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/bait_disenfranchise_economics_happy_ending_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/bait_disenfranchise_economics_happy_ending_nursery_rhyme.py --asp
    python storyworlds/worlds/gpt-5.4/bait_disenfranchise_economics_happy_ending_nursery_rhyme.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "goose", "ewe"}
        male = {"boy", "father", "fox", "toad", "badger"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    opening: str
    feature: str
    affords_bait: set[str] = field(default_factory=set)
    affords_remedy: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Bait:
    id: str
    label: str
    phrase: str
    jingle: str
    clue: str
    lure: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Project:
    id: str
    label: str
    need: str
    benefit: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Remedy:
    id: str
    label: str
    method: str
    success: str
    qa_text: str
    works_for: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


def _r_disenfranchise_risk(world: World) -> list[str]:
    out: list[str] = []
    voters = world.get("voters")
    basket = world.get("basket")
    helper = world.get("helper")
    if voters.meters["distracted"] < THRESHOLD:
        return out
    if basket.meters["hidden"] < THRESHOLD:
        return out
    sig = ("risk",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    voters.memes["worry"] += 1
    helper.memes["alert"] += 1
    world.get("fairness").meters["low_voice"] += 1
    world.facts["risk_word"] = "disenfranchise"
    out.append("__risk__")
    return out


def _r_restore_fairness(world: World) -> list[str]:
    out: list[str] = []
    basket = world.get("basket")
    fairness = world.get("fairness")
    if basket.meters["restored"] < THRESHOLD:
        return out
    sig = ("restore",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fairness.meters["low_voice"] = 0.0
    fairness.meters["everyone_counted"] += 1
    for eid in ("hero", "friend", "helper"):
        world.get(eid).memes["relief"] += 1
    out.append("__restored__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="disenfranchise_risk", tag="social", apply=_r_disenfranchise_risk),
    Rule(name="restore_fairness", tag="social", apply=_r_restore_fairness),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def bait_fits(place: Place, bait: Bait) -> bool:
    return bait.id in place.affords_bait


def remedy_fits(place: Place, bait: Bait, remedy: Remedy) -> bool:
    return remedy.id in place.affords_remedy and bait.id in remedy.works_for


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for bait_id, bait in BAITS.items():
            if not bait_fits(place, bait):
                continue
            for project_id in PROJECTS:
                for remedy_id, remedy in REMEDIES.items():
                    if remedy_fits(place, bait, remedy):
                        combos.append((place_id, bait_id, project_id, remedy_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    trait_bonus = 1 if HERO_TRAITS[params.trait]["careful"] else 0
    lure = BAITS[params.bait].lure
    if trait_bonus >= lure:
        return "averted"
    return "restored"


def explain_bait(place: Place, bait: Bait) -> str:
    return (
        f"(No story: {bait.phrase} does not suit {place.label}. "
        f"Pick bait that belongs in that place's little fair.)"
    )


def explain_remedy(place: Place, bait: Bait, remedy: Remedy) -> str:
    if remedy.id not in place.affords_remedy:
        return (
            f"(No story: {remedy.label} is not available at {place.label}. "
            f"Choose a remedy the place can honestly support.)"
        )
    return (
        f"(No story: {remedy.label} does not sensibly solve trouble caused by "
        f"{bait.phrase}. Pick a remedy that matches the clue the bait leaves.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_trouble(world: World, bait_id: str, trait: str) -> dict:
    sim = world.copy()
    bait = BAITS[bait_id]
    trait_bonus = 1 if HERO_TRAITS[trait]["careful"] else 0
    if trait_bonus < bait.lure:
        sim.get("voters").meters["distracted"] += 1
        sim.get("basket").meters["hidden"] += 1
        propagate(sim, narrate=False)
    return {
        "risk": sim.get("fairness").meters["low_voice"] >= THRESHOLD,
        "everyone_counted": sim.get("fairness").meters["everyone_counted"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs and beats
# ---------------------------------------------------------------------------
def introduce(world: World, place: Place, hero: Entity, friend: Entity, helper: Entity,
              project: Project) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In {place.label}, by {place.feature}, "
        f"{hero.id} and {friend.id} came skipping with a clack-clack-clack."
    )
    world.say(
        f"They each held one smooth acorn token for the village choice that day: "
        f"whether to spend the shared chest on {project.label}."
    )
    world.say(
        f'"Small paws, small feet, small voices too, '
        f'but every vote must still ring true," sang {helper.id}.'
    )


def explain_project(world: World, helper: Entity, project: Project) -> None:
    world.say(
        f"{helper.id} tapped the chalkboard and told them why the choice mattered. "
        f"The town had only one little budget, and picking {project.label} would mean {project.benefit}."
    )
    world.say(
        f'"That is economics," {helper.id} said. '
        f'"It means choosing how shared coins help the whole village best."'
    )


def tempt(world: World, trader: Entity, bait: Bait) -> None:
    trader.memes["scheming"] += 1
    world.say(
        f"Then {trader.id} came tripping by with {bait.phrase}. "
        f'"{bait.jingle}" he chimed.'
    )


def warn(world: World, helper: Entity, hero: Entity, bait: Bait, trait: str) -> None:
    pred = predict_trouble(world, bait.id, trait)
    world.facts["predicted_risk"] = pred["risk"]
    cautious_line = HERO_TRAITS[trait]["warning"]
    if pred["risk"]:
        world.say(
            f'{helper.id} lowered {helper.pronoun("possessive")} voice. '
            f'"Mind the bait, mind the gate. If everyone wanders off at once, '
            f'some small voices could be left out."'
        )
        world.say(cautious_line)
    else:
        world.say(
            f'{helper.id} smiled at {hero.id}. "{cautious_line[1:-1]}"'
            if cautious_line.startswith('"') and cautious_line.endswith('"')
            else f'{helper.id} smiled at {hero.id}. {cautious_line}'
        )


def resist(world: World, hero: Entity, friend: Entity, bait: Bait) -> None:
    hero.memes["care"] += 1
    friend.memes["care"] += 1
    world.say(
        f"{hero.id} sniffed the {bait.label}, then tucked the acorn token in a tight little paw."
    )
    world.say(
        f'"First the vote, then the treat," {hero.id} said. '
        f"And {friend.id} nodded to the beat."
    )


def get_distracted(world: World, hero: Entity, friend: Entity, bait: Bait) -> None:
    voters = world.get("voters")
    basket = world.get("basket")
    voters.meters["distracted"] += 1
    voters.memes["tempted"] += 1
    basket.meters["hidden"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The smell and sparkle danced in the air, and off the children skipped to stare."
    )
    world.say(
        f"While noses lifted toward the bait, the vote basket slid behind the trader's crate."
    )


def name_the_risk(world: World, helper: Entity) -> None:
    if world.get("fairness").meters["low_voice"] >= THRESHOLD:
        world.say(
            f'{helper.id} gasped, then spoke a long, important word: '
            f'"To hide the basket now would disenfranchise the youngest voters. '
            f'It means pushing fair voices out."'
        )


def restore(world: World, helper: Entity, trader: Entity, remedy: Remedy, bait: Bait) -> None:
    basket = world.get("basket")
    basket.meters["restored"] += 1
    basket.meters["hidden"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} moved quickly and {remedy.method}."
    )
    world.say(
        f"{remedy.success} The trader hung his head and set the basket back where all could see."
    )


def lesson(world: World, helper: Entity, hero: Entity, friend: Entity, project: Project) -> None:
    world.say(
        f'"A fair little village must count every say," {helper.id} told them. '
        f'"That is good economics too, because shared things should help everyone."'
    )
    world.say(
        f"{hero.id} and {friend.id} dropped in their acorn tokens with a plink-plink sound."
    )
    world.say(
        f"Soon the village chose {project.label}, and {project.need} no longer had to wait."
    )


def ending(world: World, place: Place, hero: Entity, friend: Entity, bait: Bait) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Only after the vote did the children share {bait.phrase}, one by one and round by round."
    )
    world.say(
        f"In {place.label}, by {place.feature}, they sang as the sunset painted gold: "
        f'"Count us kindly, count us right; little voices make things bright."'
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    bait: str
    project: str
    remedy: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    helper: str
    helper_type: str
    trader: str
    trader_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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


def tell(place: Place, bait: Bait, project: Project, remedy: Remedy,
         hero_name: str = "Mim", hero_type: str = "mouse",
         friend_name: str = "Pip", friend_type: str = "duck",
         helper_name: str = "Owl Ada", helper_type: str = "owl",
         trader_name: str = "Mr. Fox", trader_type: str = "fox",
         trait: str = "careful") -> World:
    world = World()

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=[trait],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_type,
        label=friend_name,
        role="friend",
        traits=["cheerful"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        label=helper_name,
        role="helper",
        traits=["wise"],
    ))
    trader = world.add(Entity(
        id=trader_name,
        kind="character",
        type=trader_type,
        label=trader_name,
        role="trader",
        traits=["sly"],
    ))
    world.add(Entity(
        id="basket",
        type="basket",
        label="vote basket",
        attrs={"visible": True},
    ))
    world.add(Entity(
        id="voters",
        type="group",
        label="young voters",
    ))
    world.add(Entity(
        id="fairness",
        type="fairness",
        label="fairness",
    ))

    world.facts["risk_word"] = ""
    world.facts["predicted_risk"] = False

    introduce(world, place, hero, friend, helper, project)
    explain_project(world, helper, project)

    world.para()
    tempt(world, trader, bait)
    warn(world, helper, hero, bait, trait)

    if outcome_of(StoryParams(
        place=place.id,
        bait=bait.id,
        project=project.id,
        remedy=remedy.id,
        hero=hero_name,
        hero_type=hero_type,
        friend=friend_name,
        friend_type=friend_type,
        helper=helper_name,
        helper_type=helper_type,
        trader=trader_name,
        trader_type=trader_type,
        trait=trait,
        seed=None,
    )) == "averted":
        resist(world, hero, friend, bait)
    else:
        get_distracted(world, hero, friend, bait)
        name_the_risk(world, helper)

        world.para()
        restore(world, helper, trader, remedy, bait)

    world.para()
    lesson(world, helper, hero, friend, project)
    ending(world, place, hero, friend, bait)

    world.facts.update(
        place=place,
        bait=bait,
        project=project,
        remedy=remedy,
        hero=hero,
        friend=friend,
        helper=helper,
        trader=trader,
        outcome=outcome_of(StoryParams(
            place=place.id,
            bait=bait.id,
            project=project.id,
            remedy=remedy.id,
            hero=hero_name,
            hero_type=hero_type,
            friend=friend_name,
            friend_type=friend_type,
            helper=helper_name,
            helper_type=helper_type,
            trader=trader_name,
            trader_type=trader_type,
            trait=trait,
            seed=None,
        )),
        risk=world.get("fairness").meters["low_voice"] >= THRESHOLD,
        restored=world.get("fairness").meters["everyone_counted"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "green": Place(
        id="green",
        label="the village green",
        opening="Under the elm on the green",
        feature="the old elm tree",
        affords_bait={"ribbons", "cakes"},
        affords_remedy={"roll_call", "drum_recall"},
        tags={"vote", "fair"},
    ),
    "riverside": Place(
        id="riverside",
        label="the riverside fair",
        opening="Down by the reeds",
        feature="the stepping-stone bridge",
        affords_bait={"bells", "cakes"},
        affords_remedy={"roll_call", "follow_crumbs"},
        tags={"vote", "fair"},
    ),
    "orchard": Place(
        id="orchard",
        label="the orchard square",
        opening="Among the apple boughs",
        feature="the cider press",
        affords_bait={"bells", "ribbons"},
        affords_remedy={"roll_call", "drum_recall"},
        tags={"vote", "fair"},
    ),
}

BAITS = {
    "cakes": Bait(
        id="cakes",
        label="honey cakes",
        phrase="a tray of honey cakes",
        jingle="Bait so sweet, come taste, come take!",
        clue="crumbs on the grass",
        lure=1,
        tags={"bait", "food"},
    ),
    "ribbons": Bait(
        id="ribbons",
        label="ribbon kites",
        phrase="a bunch of ribbon kites",
        jingle="Bait on a breeze, bright as a song!",
        clue="streamers in the hedge",
        lure=2,
        tags={"bait", "wind"},
    ),
    "bells": Bait(
        id="bells",
        label="berry bells",
        phrase="a string of berry bells",
        jingle="Bait that tinkles, come skip along!",
        clue="bell-chimes by the stall",
        lure=2,
        tags={"bait", "sound"},
    ),
}

PROJECTS = {
    "bridge": Project(
        id="bridge",
        label="new bridge boards",
        need="the stepping bridge",
        benefit="the shaky bridge could be mended before the rainy week",
        tags={"economics", "bridge"},
    ),
    "cart": Project(
        id="cart",
        label="library cart wheels",
        need="the story cart",
        benefit="the story cart could roll to every lane with fewer squeaks and stops",
        tags={"economics", "books"},
    ),
    "barrel": Project(
        id="barrel",
        label="a garden rain barrel",
        need="the thirsty bean patch",
        benefit="the bean patch could catch rainwater and stay green in dry weather",
        tags={"economics", "garden"},
    ),
}

REMEDIES = {
    "roll_call": Remedy(
        id="roll_call",
        label="a roll call",
        method="called each small voter by name and checked the chalk ledger",
        success="One by one, every child returned with the right token and the line grew fair again.",
        qa_text="called the roll from the ledger and brought every voter back",
        works_for={"cakes", "ribbons", "bells"},
        tags={"fairness", "vote"},
    ),
    "follow_crumbs": Remedy(
        id="follow_crumbs",
        label="following crumbs",
        method="followed the sticky crumbs from the cakes straight behind the trader's crate",
        success="There sat the missing basket, easy to find once the crumbs told the tale.",
        qa_text="followed the cake crumbs to the hidden basket",
        works_for={"cakes"},
        tags={"fairness", "clue"},
    ),
    "drum_recall": Remedy(
        id="drum_recall",
        label="the recall drum",
        method="beat the meeting drum and sang the voting rhyme until every youngster came hopping back",
        success="The basket was seen again, and no child's turn was skipped.",
        qa_text="used the meeting drum to call the young voters back",
        works_for={"ribbons", "bells"},
        tags={"fairness", "sound"},
    ),
}

HERO_TRAITS = {
    "careful": {"careful": True, "warning": '"Count first, nibble later," whispered the little one.'},
    "steady": {"careful": True, "warning": '"A bright thing can wait if the right thing is first," said the little one.'},
    "bouncy": {"careful": False, "warning": '"It all looks lovely," laughed the little one.'},
    "curious": {"careful": False, "warning": '"I only want a closer peek," said the little one.'},
}

HEROES = [
    ("Mim", "mouse"),
    ("Dot", "duck"),
    ("Nell", "hen"),
    ("Pru", "goat"),
]
FRIENDS = [
    ("Pip", "duck"),
    ("Tansy", "lamb"),
    ("Roo", "mouse"),
    ("Bea", "hen"),
]
HELPERS = [
    ("Owl Ada", "owl"),
    ("Mayor Badger", "badger"),
    ("Auntie Goose", "goose"),
]
TRADERS = [
    ("Mr. Fox", "fox"),
    ("Toad Pike", "toad"),
]


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "bait": [
        (
            "What is bait?",
            "Bait is something tempting that is used to pull attention in one direction. In this story world, the bait is not kind, because it is used to distract children from something fair and important.",
        )
    ],
    "vote": [
        (
            "Why should every vote be counted?",
            "Every vote should be counted so each person gets a fair say. When some voices are left out, the choice no longer belongs to everyone together.",
        )
    ],
    "economics": [
        (
            "What is economics?",
            "Economics is about choosing how to use limited money or goods. It helps a group decide what will help everyone most when they cannot buy everything at once.",
        )
    ],
    "disenfranchise": [
        (
            "What does disenfranchise mean?",
            "Disenfranchise means unfairly taking away someone's chance to vote or be counted. It pushes a voice out of a decision that should include them.",
        )
    ],
    "fairness": [
        (
            "What makes a choice fair?",
            "A choice is fair when the same rules are used for everyone and each voice gets a turn. Fairness matters most when something shared belongs to the whole group.",
        )
    ],
}
KNOWLEDGE_ORDER = ["bait", "vote", "economics", "disenfranchise", "fairness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    bait = f["bait"]
    project = f["project"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a nursery-rhyme style story for a 3-to-5-year-old that includes the words "bait", "disenfranchise", and "economics". Set it at {place.label} and let a careful child resist {bait.label} so every vote is counted.',
            f"Tell a sing-song village story where children must choose how to spend a tiny shared budget on {project.label}, and a wise helper explains economics in a child-friendly way.",
            f"Write a rhyming fair-day story where tempting bait appears, but the children put fairness first and end with a happy shared vote.",
        ]
    return [
        f'Write a nursery-rhyme style story for a 3-to-5-year-old that includes the words "bait", "disenfranchise", and "economics". Set it at {place.label}, let tempting {bait.label} distract the children, and end with fairness restored.',
        f"Tell a sing-song village story where a sly trader tries to use bait so the smallest voters might be left out, but a wise helper saves the day.",
        f"Write a gentle rhyming story about a shared budget, a threatened vote, and a happy ending where every child's token is counted.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    trader = f["trader"]
    bait = f["bait"]
    project = f["project"]
    remedy = f["remedy"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id} at the village fair, with {helper.id} helping them and {trader.id} causing the trouble.",
        ),
        (
            "What were the children choosing?",
            f"They were choosing whether the village should spend its small shared budget on {project.label}. That mattered because the town could only afford one helpful thing at a time, which is why {helper.id} called it economics.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"Why did {hero.id} not run after the bait?",
                f"{hero.id} remembered that the vote had to come first, so the shiny treat could wait. By holding onto the acorn token, {hero.pronoun()} helped make sure nobody would be left out.",
            )
        )
        qa.append(
            (
                "Did anyone get disenfranchised?",
                f"No. {helper.id} warned them in time, and the children kept their place in the line. That meant every small voice was still counted fairly.",
            )
        )
    else:
        qa.append(
            (
                f"What danger did {helper.id} notice?",
                f"{helper.id} saw that the bait had pulled the children away while the vote basket was hidden. {helper.pronoun().capitalize()} said that would disenfranchise the youngest voters, because their tokens might not be counted.",
            )
        )
        qa.append(
            (
                f"How was the problem fixed?",
                f"{helper.id} {remedy.qa_text}. That brought the voting back into the open, so every child could take a turn and the choice became fair again.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended happily with the children casting their acorn tokens and the village choosing {project.label}. After the fair vote was done, they shared the treat together instead of letting the bait boss them around.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"bait", "vote", "economics", "fairness"}
    if world.facts.get("risk_word") == "disenfranchise" or world.facts["outcome"] == "restored":
        tags.add("disenfranchise")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:14} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% valid combinations
fits_bait(P,B) :- place(P), bait(B), place_bait(P,B).
fits_remedy(P,B,R) :- place(P), bait(B), remedy(R), place_remedy(P,R), remedy_bait(R,B).
valid(P,B,Pr,R) :- place(P), bait(B), project(Pr), remedy(R), fits_bait(P,B), fits_remedy(P,B,R).

% outcome model
trait_bonus(1) :- chosen_trait(T), careful_trait(T).
trait_bonus(0) :- chosen_trait(T), not careful_trait(T).
lure_now(L) :- chosen_bait(B), lure(B,L).
averted :- trait_bonus(TB), lure_now(L), TB >= L.
outcome(averted) :- averted.
outcome(restored) :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for bait_id in sorted(place.affords_bait):
            lines.append(asp.fact("place_bait", place_id, bait_id))
        for remedy_id in sorted(place.affords_remedy):
            lines.append(asp.fact("place_remedy", place_id, remedy_id))
    for bait_id, bait in BAITS.items():
        lines.append(asp.fact("bait", bait_id))
        lines.append(asp.fact("lure", bait_id, bait.lure))
    for project_id in PROJECTS:
        lines.append(asp.fact("project", project_id))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        for bait_id in sorted(remedy.works_for):
            lines.append(asp.fact("remedy_bait", remedy_id, bait_id))
    for trait_id, data in HERO_TRAITS.items():
        lines.append(asp.fact("trait", trait_id))
        if data["careful"]:
            lines.append(asp.fact("careful_trait", trait_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_bait", params.bait),
        asp.fact("chosen_trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combo gate matches ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"resolve_params unexpectedly failed for seed {seed}")
            continue
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print(
                f"MISMATCH outcome for seed {seed}: "
                f"asp={asp_outcome(params)} python={outcome_of(params)}"
            )

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: bait, fairness, economics, and a happy nursery-rhyme ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--bait", choices=BAITS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--trait", choices=HERO_TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.bait:
        place = PLACES[args.place]
        bait = BAITS[args.bait]
        if not bait_fits(place, bait):
            raise StoryError(explain_bait(place, bait))
    if args.place and args.bait and args.remedy:
        place = PLACES[args.place]
        bait = BAITS[args.bait]
        remedy = REMEDIES[args.remedy]
        if not remedy_fits(place, bait, remedy):
            raise StoryError(explain_remedy(place, bait, remedy))
    if args.remedy and args.bait and not any(
        remedy_fits(place, BAITS[args.bait], REMEDIES[args.remedy]) for place in PLACES.values()
    ):
        raise StoryError(explain_remedy(next(iter(PLACES.values())), BAITS[args.bait], REMEDIES[args.remedy]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.bait is None or combo[1] == args.bait)
        and (args.project is None or combo[2] == args.project)
        and (args.remedy is None or combo[3] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, bait_id, project_id, remedy_id = rng.choice(sorted(combos))
    hero, hero_type = rng.choice(HEROES)
    friend_choices = [pair for pair in FRIENDS if pair[0] != hero]
    friend, friend_type = rng.choice(friend_choices)
    helper, helper_type = rng.choice(HELPERS)
    trader, trader_type = rng.choice(TRADERS)
    trait = args.trait or rng.choice(sorted(HERO_TRAITS))
    return StoryParams(
        place=place_id,
        bait=bait_id,
        project=project_id,
        remedy=remedy_id,
        hero=hero,
        hero_type=hero_type,
        friend=friend,
        friend_type=friend_type,
        helper=helper,
        helper_type=helper_type,
        trader=trader,
        trader_type=trader_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.bait not in BAITS:
        raise StoryError(f"(Unknown bait: {params.bait})")
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    if params.trait not in HERO_TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")

    place = PLACES[params.place]
    bait = BAITS[params.bait]
    remedy = REMEDIES[params.remedy]
    if not bait_fits(place, bait):
        raise StoryError(explain_bait(place, bait))
    if not remedy_fits(place, bait, remedy):
        raise StoryError(explain_remedy(place, bait, remedy))

    world = tell(
        place=place,
        bait=bait,
        project=PROJECTS[params.project],
        remedy=remedy,
        hero_name=params.hero,
        hero_type=params.hero_type,
        friend_name=params.friend,
        friend_type=params.friend_type,
        helper_name=params.helper,
        helper_type=params.helper_type,
        trader_name=params.trader,
        trader_type=params.trader_type,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
    StoryParams(
        place="green",
        bait="cakes",
        project="bridge",
        remedy="roll_call",
        hero="Mim",
        hero_type="mouse",
        friend="Pip",
        friend_type="duck",
        helper="Owl Ada",
        helper_type="owl",
        trader="Mr. Fox",
        trader_type="fox",
        trait="careful",
        seed=None,
    ),
    StoryParams(
        place="riverside",
        bait="cakes",
        project="cart",
        remedy="follow_crumbs",
        hero="Dot",
        hero_type="duck",
        friend="Roo",
        friend_type="mouse",
        helper="Mayor Badger",
        helper_type="badger",
        trader="Toad Pike",
        trader_type="toad",
        trait="curious",
        seed=None,
    ),
    StoryParams(
        place="orchard",
        bait="bells",
        project="barrel",
        remedy="drum_recall",
        hero="Nell",
        hero_type="hen",
        friend="Tansy",
        friend_type="lamb",
        helper="Auntie Goose",
        helper_type="goose",
        trader="Mr. Fox",
        trader_type="fox",
        trait="bouncy",
        seed=None,
    ),
    StoryParams(
        place="green",
        bait="ribbons",
        project="cart",
        remedy="drum_recall",
        hero="Pru",
        hero_type="goat",
        friend="Bea",
        friend_type="hen",
        helper="Owl Ada",
        helper_type="owl",
        trader="Toad Pike",
        trader_type="toad",
        trait="steady",
        seed=None,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, bait, project, remedy) combos:\n")
        for place, bait, project, remedy in combos:
            print(f"  {place:10} {bait:8} {project:7} {remedy}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.bait} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
