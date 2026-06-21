#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/loquacious_bad_ending_happy_ending_foreshadowing_whodunit.py
=======================================================================================

A standalone storyworld for a tiny child-facing whodunit: a prized object goes
missing at a cheerful event, a loquacious witness blurts out an early clue, and
the young detective either follows that clue to a kind solution or jumps to a
wrong accusation and spoils the day.

The world is built around a few constraint-checked parts:

- a venue with certain plausible hiding places
- a missing object with physical traits
- a "case" describing who moved it, what clue they left, and where it ended up
- an investigation method that leads to a happy or bad ending

Foreshadowing is stateful, not ornamental: the witness really observes a clue
before the detective knows the object is missing, and the happy branch depends
on remembering that clue.

Run it
------
    python storyworlds/worlds/gpt-5.4/loquacious_bad_ending_happy_ending_foreshadowing_whodunit.py
    python storyworlds/worlds/gpt-5.4/loquacious_bad_ending_happy_ending_foreshadowing_whodunit.py --venue garden_party --item medal --case magpie_branch
    python storyworlds/worlds/gpt-5.4/loquacious_bad_ending_happy_ending_foreshadowing_whodunit.py --method accuse_first
    python storyworlds/worlds/gpt-5.4/loquacious_bad_ending_happy_ending_foreshadowing_whodunit.py --all --qa
    python storyworlds/worlds/gpt-5.4/loquacious_bad_ending_happy_ending_foreshadowing_whodunit.py --verify
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
SENSE_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Venue:
    id: str
    label: str
    opening: str
    places: set[str] = field(default_factory=set)
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
class ItemCfg:
    id: str
    label: str
    phrase: str
    adjective: str
    traits: set[str] = field(default_factory=set)
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
class CaseCfg:
    id: str
    culprit_name: str
    culprit_type: str
    culprit_label: str
    suspect_hint: str
    clue_label: str
    foreshadow_line: str
    place_key: str
    place_phrase: str
    found_pose: str
    move_reason: str
    moved_how: str
    requires: set[str] = field(default_factory=set)
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
class Method:
    id: str
    label: str
    sense: int
    public: bool = False
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


class World:
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
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
        clone = World(self.venue)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_missing(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("owner").memes["worry"] += 1
    world.get("detective").memes["curiosity"] += 1
    return []


def _r_false_accusation(world: World) -> list[str]:
    suspect = world.get("suspect")
    if suspect.meters["accused"] < THRESHOLD or suspect.attrs.get("culprit", False):
        return []
    sig = ("false_accusation",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.memes["hurt"] += 1
    world.get("detective").memes["guilt"] += 1
    world.get("owner").memes["worry"] += 1
    return []


def _r_found(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("found",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("owner").memes["relief"] += 1
    world.get("detective").memes["relief"] += 1
    return []


def _r_apology(world: World) -> list[str]:
    if world.get("detective").meters["apology"] < THRESHOLD:
        return []
    sig = ("apology",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("suspect").memes["comfort"] += 1
    world.get("detective").memes["kindness"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing", tag="social", apply=_r_missing),
    Rule(name="false_accusation", tag="social", apply=_r_false_accusation),
    Rule(name="found", tag="social", apply=_r_found),
    Rule(name="apology", tag="social", apply=_r_apology),
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
        for sent in produced:
            world.say(sent)
    return produced


def valid_combo(venue_id: str, item_id: str, case_id: str) -> bool:
    if venue_id not in VENUES or item_id not in ITEMS or case_id not in CASES:
        return False
    venue = VENUES[venue_id]
    item = ITEMS[item_id]
    case = CASES[case_id]
    return case.place_key in venue.places and case.requires.issubset(item.traits)


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for venue_id in VENUES:
        for item_id in ITEMS:
            for case_id in CASES:
                if valid_combo(venue_id, item_id, case_id):
                    out.append((venue_id, item_id, case_id))
    return out


def explain_rejection(venue_id: str, item_id: str, case_id: str) -> str:
    venue = VENUES.get(venue_id)
    item = ITEMS.get(item_id)
    case = CASES.get(case_id)
    if venue is None or item is None or case is None:
        return "(No story: one of the requested options is unknown.)"
    if case.place_key not in venue.places:
        return (
            f"(No story: {venue.label} has no plausible place like {case.place_phrase}, "
            f"so this clue trail cannot happen there.)"
        )
    missing_traits = sorted(case.requires - item.traits)
    if missing_traits:
        return (
            f"(No story: {item.phrase} lacks the needed trait(s) {missing_traits} for "
            f"the {case.id} case. Pick an item that can reasonably fit that clue.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


def predict_follow_clue(world: World) -> dict:
    sim = world.copy()
    sim.get("item").meters["found"] += 1
    sim.get("item").meters["missing"] = 0.0
    propagate(sim, narrate=False)
    return {
        "finds_item": sim.get("item").meters["found"] >= THRESHOLD,
        "owner_relief": sim.get("owner").memes["relief"],
    }


def introduce(world: World, detective: Entity, owner: Entity, witness: Entity,
              item: Entity, venue: Venue) -> None:
    world.say(
        f"At {venue.label}, {owner.id} set out {item.label} on a little cloth and "
        f"kept peeking at it with a proud smile."
    )
    world.say(
        f"{detective.id} loved a mystery, especially a small one that could be solved "
        f"before the cake went dry or the music stopped."
    )
    world.say(
        f"The noisiest helper was {witness.id}, a loquacious {witness.type} who told "
        f"everyone every tiny thing {witness.pronoun()} noticed."
    )


def foreshadow(world: World, witness: Entity, case: CaseCfg) -> None:
    witness.memes["noticed"] += 1
    world.say(
        f'"Wait, wait, I have three important things to report," {witness.id} said. '
        f'"First, {case.foreshadow_line} Second, someone nearly stepped on my toe. '
        f'Third, I think the lemon cake smells amazing."'
    )
    world.facts["clue_heard"] = case.clue_label


def discover_loss(world: World, detective: Entity, owner: Entity, item: Entity) -> None:
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"A few minutes later, {owner.id} looked back at the cloth and gasped. "
        f'"My {item.label} is gone!"'
    )
    world.say(
        f"{detective.id} leaned close to the empty spot. It was not a giant case, "
        f"but it was certainly a real one."
    )


def worry_and_hint(world: World, owner: Entity, suspect: Entity, case: CaseCfg) -> None:
    world.say(
        f"{owner.id} wrung {owner.pronoun('possessive')} hands. "
        f"\"{suspect.id} was near here earlier,\" {owner.pronoun()} whispered, "
        f"\"and {case.suspect_hint}.\""
    )


def remember_clue(world: World, detective: Entity, case: CaseCfg) -> None:
    pred = predict_follow_clue(world)
    world.facts["predicted_find"] = pred["finds_item"]
    world.say(
        f"Then {detective.id} remembered {witness_phrase(world)} about {case.clue_label}. "
        f"That detail had sounded silly at first, but now it shone like a tiny lamp inside the case."
    )


def accuse_first(world: World, detective: Entity, suspect: Entity, owner: Entity, item: Entity) -> None:
    suspect.meters["accused"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(
        f'{detective.id} pointed too quickly. "{suspect.id} must have taken it," '
        f'{detective.pronoun()} said.'
    )
    world.say(
        f"{suspect.id}'s face fell. \"I didn't,\" {suspect.pronoun()} said, and this time "
        f"{suspect.pronoun()} did not sound cross, only hurt."
    )
    world.say(
        f"Nobody found {item.label} before the songs began. The case stayed open, "
        f"and the happy buzz of {world.venue.label} turned thin and awkward."
    )


def follow_clue(world: World, detective: Entity, witness: Entity, owner: Entity,
                suspect: Entity, culprit: Entity, item: Entity, case: CaseCfg) -> None:
    item.meters["trail_followed"] += 1
    world.para()
    world.say(
        f'"Tell me your long version," {detective.id} said, and {witness.id} beamed.'
    )
    world.say(
        f"{witness.id} repeated every detail until the useful one came back around: "
        f"{case.clue_label}."
    )
    world.say(
        f"{detective.id} followed that clue to {case.place_phrase}."
    )
    world.say(
        f"There was {culprit.label}, {case.found_pose}, and beside {culprit.pronoun('object')} lay {item.label}."
    )
    item.meters["found"] += 1
    item.meters["missing"] = 0.0
    culprit.meters["revealed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{case.moved_how}, {case.move_reason}."
    )
    if suspect.meters["accused"] >= THRESHOLD:
        world.get("detective").meters["apology"] += 1
        propagate(world, narrate=False)
    world.say(
        f"{detective.id} picked up {item.label} and carried it back to {owner.id}."
    )
    world.say(
        f'{owner.id} hugged it to {owner.pronoun("possessive")} chest. "Case closed," '
        f'{owner.pronoun()} said, and this time the smile came all the way back.'
    )


def apology(world: World, detective: Entity, suspect: Entity) -> None:
    world.get("detective").meters["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{detective.id} turned to {suspect.id}. "I am sorry I almost blamed you," '
        f'{detective.pronoun()} said. "{suspect.pronoun().capitalize()} deserved questions, not a guess."'
    )


def happy_ending(world: World, detective: Entity, owner: Entity, witness: Entity, item: Entity) -> None:
    world.para()
    world.say(
        f"Soon {item.label} was back on the cloth, this time with a little box beside it "
        f"so it could not wander again."
    )
    world.say(
        f"{witness.id} announced the whole solution in one delighted breath, and nobody "
        f"even minded how long the speech was."
    )
    world.say(
        f"As the music started, {detective.id} grinned at {owner.id}. The mystery had ended "
        f"with everyone safe, heard, and smiling."
    )


def bad_ending(world: World, detective: Entity, owner: Entity, suspect: Entity, item: Entity) -> None:
    world.para()
    world.say(
        f"{owner.id} tried to enjoy the rest of the day, but {owner.pronoun('possessive')} eyes kept drifting "
        f"to the empty cloth where {item.label} should have been."
    )
    world.say(
        f"{detective.id} heard the songs and clapping all around, yet the case felt heavy now. "
        f"A fast guess had hurt {suspect.id} and solved nothing."
    )
    world.say(
        f"By sunset, the mystery was still unsolved, and that made {world.venue.label} feel smaller "
        f"and sadder than it had that morning."
    )


def witness_phrase(world: World) -> str:
    witness = world.get("witness")
    return f"{witness.id}'s long speech"
@dataclass
class StoryParams:
    venue: str
    item: str
    case: str
    method: str
    detective: str
    detective_gender: str
    owner: str
    owner_gender: str
    witness: str
    witness_gender: str
    suspect: str
    suspect_gender: str
    parent: str
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


KNOWLEDGE = {
    "clue": [(
        "What is a clue in a mystery?",
        "A clue is a small sign that helps you figure out what happened. Good detectives look closely before they guess."
    )],
    "kindness": [(
        "Why is it better to ask questions than to blame someone right away?",
        "Questions help you learn the truth without hurting someone. A quick blame can make an innocent person feel sad."
    )],
    "accusation": [(
        "What does it mean to accuse someone?",
        "To accuse someone means to say you think they did something wrong. You should be careful, because accusing the wrong person can hurt feelings."
    )],
    "pawprints": [(
        "What can pawprints tell you?",
        "Pawprints can show that an animal walked somewhere. They are like tiny tracks that point to where it went."
    )],
    "feather": [(
        "Why might a feather be a useful clue?",
        "A feather can show that a bird was nearby. If something shiny is missing, that clue might matter a lot."
    )],
    "fur": [(
        "What can a bit of fur tell you?",
        "Fur can show that an animal brushed past or hid in a place. It helps you know who might have been there."
    )],
    "crumbs": [(
        "Why do crumbs matter in a small mystery?",
        "Crumbs show where someone or something has been eating or carrying food. They can lead your eyes to a hiding spot."
    )],
    "seeds": [(
        "Why would seed shells make someone think of a squirrel?",
        "Squirrels like nibbling seeds and nuts. Little shells left behind can be a sign that a squirrel was there."
    )],
    "ribbon": [(
        "What is a ribbon?",
        "A ribbon is a strip of soft cloth. People use ribbons for prizes, decorations, or tying things neatly."
    )],
    "bell": [(
        "What is a bell?",
        "A bell is a small object that rings when it moves. Its sound can help people notice it quickly."
    )],
    "medal": [(
        "What is a medal?",
        "A medal is a prize, often made of metal, that shows someone did something well. People like to keep medals safe because they feel special."
    )],
    "puppy": [(
        "Why do puppies carry things away?",
        "Puppies explore with their mouths and noses. A new object can seem like a wonderful toy to them."
    )],
    "kitten": [(
        "Why do kittens hide inside boxes or trunks?",
        "Kittens like small, cozy places that feel safe. They also bat at soft or shiny things because those things seem fun."
    )],
    "magpie": [(
        "What is a magpie?",
        "A magpie is a black-and-white bird. It notices bright objects very quickly and can be curious about shiny things."
    )],
    "mouse": [(
        "Why might a mouse pull little objects into a hiding place?",
        "Mice like snug hiding spots and gather tiny things there. A small object can seem useful or interesting to them."
    )],
    "squirrel": [(
        "Why does a squirrel hide things?",
        "Squirrels tuck things away in safe places. Hiding is part of how they explore and keep treasures or snacks close."
    )],
}
KNOWLEDGE_ORDER = [
    "clue", "kindness", "accusation", "pawprints", "feather", "fur", "crumbs",
    "seeds", "ribbon", "bell", "medal", "puppy", "kitten", "magpie", "mouse", "squirrel",
]


CURATED = [
    StoryParams(
        venue="school_fair",
        item="ribbon",
        case="puppy_stage",
        method="follow_clue",
        detective="Nora",
        detective_gender="girl",
        owner="Owen",
        owner_gender="boy",
        witness="Milo",
        witness_gender="boy",
        suspect="June",
        suspect_gender="girl",
        parent="mother",
        seed=101,
    ),
    StoryParams(
        venue="garden_party",
        item="medal",
        case="magpie_branch",
        method="follow_clue",
        detective="Ben",
        detective_gender="boy",
        owner="Ruby",
        owner_gender="girl",
        witness="Mina",
        witness_gender="girl",
        suspect="Theo",
        suspect_gender="boy",
        parent="father",
        seed=102,
    ),
    StoryParams(
        venue="library_show",
        item="ribbon",
        case="kitten_trunk",
        method="accuse_first",
        detective="Ava",
        detective_gender="girl",
        owner="Leo",
        owner_gender="boy",
        witness="Milo",
        witness_gender="boy",
        suspect="Maya",
        suspect_gender="girl",
        parent="mother",
        seed=103,
    ),
    StoryParams(
        venue="library_show",
        item="bell",
        case="mouse_puppet",
        method="follow_clue",
        detective="Finn",
        detective_gender="boy",
        owner="Ella",
        owner_gender="girl",
        witness="Nora",
        witness_gender="girl",
        suspect="Max",
        suspect_gender="boy",
        parent="father",
        seed=104,
    ),
    StoryParams(
        venue="garden_party",
        item="bell",
        case="squirrel_bench",
        method="accuse_first",
        detective="Zoe",
        detective_gender="girl",
        owner="Sam",
        owner_gender="boy",
        witness="Mina",
        witness_gender="girl",
        suspect="Lily",
        suspect_gender="girl",
        parent="mother",
        seed=105,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small child-facing whodunit with foreshadowing, a loquacious witness, and either a happy or bad ending."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    if not choices:
        raise StoryError("(No story: ran out of distinct names for the chosen genders.)")
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.venue and args.item and args.case and not valid_combo(args.venue, args.item, args.case):
        raise StoryError(explain_rejection(args.venue, args.item, args.case))

    combos = [
        combo for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.item is None or combo[1] == args.item)
        and (args.case is None or combo[2] == args.case)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue_id, item_id, case_id = rng.choice(sorted(combos))
    method_id = args.method or rng.choice(sorted(METHODS))
    parent = args.parent or rng.choice(["mother", "father"])

    detective_gender = rng.choice(["girl", "boy"])
    owner_gender = rng.choice(["girl", "boy"])
    witness_gender = rng.choice(["girl", "boy"])
    suspect_gender = rng.choice(["girl", "boy"])

    used: set[str] = set()
    detective = _pick_name(rng, detective_gender, used)
    used.add(detective)
    owner = _pick_name(rng, owner_gender, used)
    used.add(owner)
    witness = _pick_name(rng, witness_gender, used)
    used.add(witness)
    suspect = _pick_name(rng, suspect_gender, used)

    return StoryParams(
        venue=venue_id,
        item=item_id,
        case=case_id,
        method=method_id,
        detective=detective,
        detective_gender=detective_gender,
        owner=owner,
        owner_gender=owner_gender,
        witness=witness,
        witness_gender=witness_gender,
        suspect=suspect,
        suspect_gender=suspect_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.venue not in VENUES:
        raise StoryError(f"(No story: unknown venue {params.venue!r}.)")
    if params.item not in ITEMS:
        raise StoryError(f"(No story: unknown item {params.item!r}.)")
    if params.case not in CASES:
        raise StoryError(f"(No story: unknown case {params.case!r}.)")
    if params.method not in METHODS:
        raise StoryError(f"(No story: unknown method {params.method!r}.)")
    if not valid_combo(params.venue, params.item, params.case):
        raise StoryError(explain_rejection(params.venue, params.item, params.case))

    world = tell(
        venue=VENUES[params.venue],
        item_cfg=ITEMS[params.item],
        case=CASES[params.case],
        method=METHODS[params.method],
        detective_name=params.detective,
        detective_type=params.detective_gender,
        owner_name=params.owner,
        owner_type=params.owner_gender,
        witness_name=params.witness,
        witness_type=params.witness_gender,
        suspect_name=params.suspect,
        suspect_type=params.suspect_gender,
        parent_type=params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    item_cfg = f["item_cfg"]
    venue = f["venue"]
    case = f["case_cfg"]
    outcome = f["outcome"]
    if outcome == "happy":
        return [
            f'Write a child-friendly whodunit set at {venue.label} where a loquacious witness accidentally foreshadows the answer to a mystery about {item_cfg.phrase}.',
            f"Tell a small detective story where {detective.id} listens carefully to a long, chatty clue and solves the case kindly.",
            f'Write a short mystery with the word "loquacious" that ends happily after a clue about {case.clue_label} is finally understood.',
        ]
    return [
        f'Write a gentle whodunit set at {venue.label} where a loquacious witness gives an early clue about missing {item_cfg.label}, but the detective guesses too fast.',
        f"Tell a mystery story for young children where a wrong accusation leads to a bad ending even though the clue was there from the start.",
        f'Write a short story with the word "loquacious", strong foreshadowing, and a sad ending caused by not listening carefully.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    owner = f["owner"]
    witness = f["witness"]
    suspect = f["suspect"]
    culprit = f["culprit"]
    item_cfg = f["item_cfg"]
    case = f["case_cfg"]
    venue = f["venue"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            f"The mystery was that {owner.id}'s {item_cfg.label} vanished at {venue.label}. {detective.id} treated that small loss like a real case that needed careful thinking."
        ),
        (
            f"Why was {witness.id} described as loquacious?",
            f"{witness.id} kept talking about every tiny thing {witness.pronoun()} saw. That long speech mattered because one small detail inside it became the key clue."
        ),
        (
            "How did the story use foreshadowing?",
            f"The foreshadowing came when {witness.id} mentioned {case.clue_label} before anyone knew the prize was missing. That clue seemed unimportant at first, but later it pointed toward the truth."
        ),
    ]
    if outcome == "happy":
        qa.extend([
            (
                f"How did {detective.id} solve the case?",
                f"{detective.id} stopped guessing and listened to the clue about {case.clue_label}. That led {detective.pronoun('object')} to {case.place_phrase}, where {culprit.label} had the missing prize."
            ),
            (
                f"Who really moved the {item_cfg.label}, and why?",
                f"It was {culprit.label}. {case.moved_how.lower()}, {case.move_reason}."
            ),
            (
                "Why was the ending happy?",
                f"The missing {item_cfg.label} was found and returned, so {owner.id} felt relieved. The detective also chose listening over blaming, which kept the mystery from hurting anyone."
            ),
        ])
    else:
        qa.extend([
            (
                f"Why did the ending turn bad?",
                f"{detective.id} accused {suspect.id} before checking the clue. That fast guess hurt {suspect.id}'s feelings and still did not bring the missing {item_cfg.label} back."
            ),
            (
                f"Was {suspect.id} really the one who took the {item_cfg.label}?",
                f"No. The story shows that {suspect.id} was blamed without proof. That is why the case stayed unsolved and the day felt sad."
            ),
            (
                "What should the detective have done instead?",
                f"{detective.id} should have listened carefully to the clue about {case.clue_label} and looked near {case.place_phrase}. A slower, kinder investigation would have had a much better chance of solving the case."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["method"].tags)
    tags |= set(world.facts["item_cfg"].tags)
    tags |= set(world.facts["case_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(V,I,C) :- venue(V), item(I), case(C), supports(V,P), place_of(C,P), requires_all(C,I).
requires_all(C,I) :- case(C), item(I), not missing_req(C,I).
missing_req(C,I) :- requires(C,T), not has_trait(I,T).

happy :- chosen_method(follow_clue).
bad   :- chosen_method(accuse_first).

outcome(happy) :- happy.
outcome(bad)   :- bad.

#show valid/3.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id, venue in VENUES.items():
        lines.append(asp.fact("venue", venue_id))
        for place in sorted(venue.places):
            lines.append(asp.fact("supports", venue_id, place))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for trait in sorted(item.traits):
            lines.append(asp.fact("has_trait", item_id, trait))
    for case_id, case in CASES.items():
        lines.append(asp.fact("case", case_id))
        lines.append(asp.fact("place_of", case_id, case.place_key))
        for need in sorted(case.requires):
            lines.append(asp.fact("requires", case_id, need))
    for method_id in METHODS:
        lines.append(asp.fact("method", method_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    model = asp.one_model(asp_program(asp.fact("chosen_method", params.method)))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "happy" if params.method == "follow_clue" else "bad"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP valid combos match Python ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for s in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


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

    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, item, case) combos:\n")
        for venue_id, item_id, case_id in combos:
            print(f"  {venue_id:12} {item_id:8} {case_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.venue} / {p.item} / {p.case} / {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(venue: Venue, item_cfg: ItemCfg, case: CaseCfg, method: Method,
         detective_name: str = "Nora", detective_type: str = "girl",
         owner_name: str = "Owen", owner_type: str = "boy",
         witness_name: str = "Milo", witness_type: str = "boy",
         suspect_name: str = "June", suspect_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(venue)

    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_type,
        role="detective",
        label=detective_name,
        attrs={},
        tags={"detective"},
    ))
    owner = world.add(Entity(
        id=owner_name,
        kind="character",
        type=owner_type,
        role="owner",
        label=owner_name,
        attrs={},
        tags={"owner"},
    ))
    witness = world.add(Entity(
        id=witness_name,
        kind="character",
        type=witness_type,
        role="witness",
        label=witness_name,
        attrs={"loquacious": True},
        tags={"witness", "loquacious"},
    ))
    suspect = world.add(Entity(
        id=suspect_name,
        kind="character",
        type=suspect_type,
        role="suspect",
        label=suspect_name,
        attrs={"culprit": False},
        tags={"suspect"},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="grownup",
        label="the grown-up",
        attrs={},
        tags={"grownup"},
    ))
    culprit = world.add(Entity(
        id="culprit",
        kind="character",
        type=case.culprit_type,
        role="culprit",
        label=case.culprit_label,
        attrs={"culprit": True},
        tags=set(case.tags),
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type=item_cfg.id,
        role="item",
        label=item_cfg.phrase,
        attrs={"traits": sorted(item_cfg.traits)},
        tags=set(item_cfg.tags),
    ))

    world.facts.update(
        venue=venue,
        item_cfg=item_cfg,
        case_cfg=case,
        method=method,
        detective=detective,
        owner=owner,
        witness=witness,
        suspect=suspect,
        culprit=culprit,
        parent=parent,
        item=item,
        clue_heard=case.clue_label,
        predicted_find=False,
        outcome="",
    )

    introduce(world, detective, owner, witness, item, venue)
    foreshadow(world, witness, case)
    discover_loss(world, detective, owner, item)
    worry_and_hint(world, owner, suspect, case)

    if method.id == "follow_clue":
        remember_clue(world, detective, case)
        follow_clue(world, detective, witness, owner, suspect, culprit, item, case)
        apology(world, detective, suspect)
        happy_ending(world, detective, owner, witness, item)
        outcome = "happy"
    else:
        accuse_first(world, detective, suspect, owner, item)
        bad_ending(world, detective, owner, suspect, item)
        outcome = "bad"

    world.facts["outcome"] = outcome
    world.facts["item_found"] = item.meters["found"] >= THRESHOLD
    world.facts["false_accusation"] = suspect.meters["accused"] >= THRESHOLD and not suspect.attrs.get("culprit", False)
    return world


VENUES = {
    "school_fair": Venue(
        id="school_fair",
        label="the school fair",
        opening="Bright paper chains swung over the booths.",
        places={"stage_skirt", "craft_basket"},
        tags={"fair"},
    ),
    "garden_party": Venue(
        id="garden_party",
        label="the garden party",
        opening="Little tables stood under pearly strings of lanterns.",
        places={"low_branch", "bench_shadow"},
        tags={"garden"},
    ),
    "library_show": Venue(
        id="library_show",
        label="the library show",
        opening="Pillows, paper stars, and a puppet curtain made one corner look magical.",
        places={"costume_trunk", "puppet_stage"},
        tags={"library"},
    ),
}

ITEMS = {
    "ribbon": ItemCfg(
        id="ribbon",
        label="ribbon",
        phrase="a satin blue ribbon",
        adjective="satin blue",
        traits={"small", "soft", "shiny"},
        tags={"ribbon"},
    ),
    "bell": ItemCfg(
        id="bell",
        label="bell",
        phrase="a little brass bell",
        adjective="little brass",
        traits={"small", "shiny", "jangly"},
        tags={"bell"},
    ),
    "medal": ItemCfg(
        id="medal",
        label="medal",
        phrase="a silver medal",
        adjective="silver",
        traits={"small", "round", "shiny"},
        tags={"medal"},
    ),
}

CASES = {
    "puppy_stage": CaseCfg(
        id="puppy_stage",
        culprit_name="Pip",
        culprit_type="animal",
        culprit_label="the baker's puppy",
        suspect_hint="she had been dashing past the stage all morning",
        clue_label="muddy pawprints",
        foreshadow_line="I saw muddy pawprints by the stage skirt",
        place_key="stage_skirt",
        place_phrase="the striped cloth hanging from the front of the stage",
        found_pose="with its tail thumping the floor",
        moved_how="The puppy had carried the prize away in its mouth",
        move_reason="because it looked like a marvelous toy",
        requires={"small"},
        tags={"puppy", "pawprints"},
    ),
    "cousin_basket": CaseCfg(
        id="cousin_basket",
        culprit_name="Tessa",
        culprit_type="girl",
        culprit_label="little cousin Tessa",
        suspect_hint="she loved peeking at prizes before anyone else could",
        clue_label="a loop of yellow yarn",
        foreshadow_line="a loop of yellow yarn was snagged on the craft basket",
        place_key="craft_basket",
        place_phrase="the big craft basket by the glue sticks",
        found_pose="kneeling inside a ring of paper flowers",
        moved_how="Tessa had borrowed the prize very quietly",
        move_reason="because she wanted to make her doll look important for one minute",
        requires={"small"},
        tags={"basket", "yarn"},
    ),
    "magpie_branch": CaseCfg(
        id="magpie_branch",
        culprit_name="Mott",
        culprit_type="animal",
        culprit_label="a black-and-white magpie",
        suspect_hint="he liked climbing and had looked up into the trees",
        clue_label="a black feather",
        foreshadow_line="a black feather was caught on the low branch near the lemonade table",
        place_key="low_branch",
        place_phrase="the low tree branch above the lanterns",
        found_pose="tilting its head at the silver shine",
        moved_how="The magpie had flown off with the prize",
        move_reason="because shiny things made its bright bird eyes greedy",
        requires={"shiny"},
        tags={"magpie", "feather"},
    ),
    "kitten_trunk": CaseCfg(
        id="kitten_trunk",
        culprit_name="Muffin",
        culprit_type="animal",
        culprit_label="the costume-room kitten",
        suspect_hint="she had been playing dress-up all afternoon",
        clue_label="white fur on a velvet edge",
        foreshadow_line="there was white fur on the lid of the costume trunk",
        place_key="costume_trunk",
        place_phrase="the half-open costume trunk beside the puppet curtain",
        found_pose="curled on a pile of capes like a tiny queen",
        moved_how="The kitten had dragged the prize into the trunk",
        move_reason="because the soft shine made a perfect nest toy",
        requires={"soft"},
        tags={"kitten", "fur"},
    ),
    "mouse_puppet": CaseCfg(
        id="mouse_puppet",
        culprit_name="Nib",
        culprit_type="animal",
        culprit_label="a mouse from the puppet corner",
        suspect_hint="he loved making puppet voices and everyone had watched him there",
        clue_label="tiny crumbs under the puppet stage",
        foreshadow_line="tiny crumbs were tucked under the puppet stage",
        place_key="puppet_stage",
        place_phrase="the shadowy gap under the puppet stage",
        found_pose="nibbling cheerfully beside a paper crown",
        moved_how="The mouse had tugged the prize away",
        move_reason="because it wanted the shiny bit for its snug little hoard",
        requires={"small"},
        tags={"mouse", "crumbs"},
    ),
    "squirrel_bench": CaseCfg(
        id="squirrel_bench",
        culprit_name="Crackle",
        culprit_type="animal",
        culprit_label="a squirrel with a twitchy tail",
        suspect_hint="she had run toward the benches when the music started",
        clue_label="chewed seed shells",
        foreshadow_line="chewed seed shells were scattered under the painted bench",
        place_key="bench_shadow",
        place_phrase="the cool shadow under the painted bench",
        found_pose="sitting up with bright eyes and quick paws",
        moved_how="The squirrel had dragged the prize under the bench",
        move_reason="because anything small and sparkling looked worth hiding",
        requires={"small"},
        tags={"squirrel", "seeds"},
    ),
}

METHODS = {
    "follow_clue": Method(
        id="follow_clue",
        label="follow the clue",
        sense=3,
        public=False,
        tags={"clue", "kindness"},
    ),
    "accuse_first": Method(
        id="accuse_first",
        label="accuse first",
        sense=1,
        public=True,
        tags={"accusation"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Maya", "Ava", "Zoe", "Ella", "Mina", "Ruby"]
BOY_NAMES = ["Owen", "Ben", "Theo", "Max", "Sam", "Leo", "Finn", "Milo"]

if __name__ == "__main__":
    main()
