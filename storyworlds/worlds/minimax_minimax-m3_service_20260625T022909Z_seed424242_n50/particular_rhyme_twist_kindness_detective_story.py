#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/particular_rhyme_twist_kindness_detective_story.py
========================================================================================================================

A standalone *story world* sketch for a particular little detective tale.

Domain: a *Detective Story* told in a kind, rhyming voice. A particular
child-detective follows a *twist* of small clues (a note, a footprint, a
button) until the case closes with a kind resolution that surprises nobody
and everybody at once.

Story shape (used to build the world model):
---
Once upon a time, in a small and tidy town, there lived a particular little
detective named Pip. Pip wore a small gray hat and carried a small notebook
in which she wrote down everything she noticed.

One morning, a baker came to the door. "Three muffins are missing from my
tin," she said, "and the tin still smells of berries." Pip put on her hat,
took her notebook, and walked to the bakery.

In the bakery, Pip found three clues: a faint blue footprint on the floor,
a button shaped like a tiny star, and a paper note that said, in careful
letters, "I was hungry, and I am sorry." Pip copied the note into her
notebook, exactly word for word.

Pip followed the blue footprints to a little garden, where she met a small
gray rabbit with a star-shaped button on her collar. "I took the muffins,"
said the rabbit, "because I had no breakfast and no one came to the garden."
Pip did not shout. She sat down beside the rabbit, and they shared a rhyme
about crumbs and kindness.

Then Pip walked back to the bakery with the rabbit. The baker smiled when
she saw them, and she gave each a warm muffin, fresh from a new tin. The
rabbit bowed and said, "Thank you, particular detective, for being kind."
Pip tipped her hat, wrote "Case closed, with kindness" in her notebook,
and walked home under a small bright sky.

Causal updates in the model:
    case_open + new clue     -> notebook.clues += 1
    rabbit confess          -> case.confession += 1
    baker forgives          -> rabbit.relief += 1
    rhyme shared            -> detector.kindness += 1
    case resolved with care -> notebook.closed = True

The screenplay is driven by these state transitions; the prose is generated
from the world, not from a frozen template.
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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"               # "character" | "thing" | "clue"
    type: str = "thing"
    label: str = ""                   # short reference, e.g. "button"
    phrase: str = ""                  # full noun phrase
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    color: str = ""                   # a small visual property used in prose
    rhymes_with: str = ""             # word a rhyming line echoes against
    clues: list[str] = field(default_factory=list)   # clue text written to notebook
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "detective-girl", "baker", "rabbit", "doe", "heroine"}
        male = {"boy", "man", "detective-boy", "fox", "tailor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.kind in {"clue", "clues"} else "it"


# ---------------------------------------------------------------------------
# Parametrization knobs
# ---------------------------------------------------------------------------
@dataclass
class Case:
    """A small missing-thing case that opens a detective tale."""
    id: str
    victim_type: str            # "baker", "tailor", "librarian", "gardener"
    missing_noun: str           # "muffins", "buttons", "books", "apples"
    missing_phrase: str         # "three small muffins"
    missing_singular: str       # "muffin" (for "a small ... was missing")
    plural: bool = True
    smell: str = ""             # sensory detail the tin still carries
    rhyme_pair: tuple[str, str] = ("tin", "skin")  # the rhyming frame
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    """A small, kind culprit whose confession becomes the twist."""
    id: str
    type: str                   # "rabbit", "fox", "mouse", "kitten"
    phrase: str                 # "a small gray rabbit"
    color: str                  # "gray"
    button_shape: str           # "star", "moon", "leaf", "heart"
    confession: str             # what they admit, in their own words
    relief_word: str            # what they say when forgiven
    rhyme_word: str             # the second half of the kindness rhyme
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    """One physical clue the detective finds at the scene."""
    id: str
    kind: str                   # "footprint", "button", "note"
    detail: str                 # "a faint blue footprint on the floor"
    note_text: Optional[str]    # the literal text of the note (or None)
    rhyme_word: str             # the clue's rhyming partner, if any
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.notebook: list[str] = []     # everything the detective writes down
        self.case_open: bool = False
        self.case_closed: bool = False
        self.kind_ending: bool = False
        self.twist_seen: bool = False
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def clues(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "clue"]

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.notebook = list(self.notebook)
        clone.case_open = self.case_open
        clone.case_closed = self.case_closed
        clone.kind_ending = self.kind_ending
        clone.twist_seen = self.twist_seen
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_clue_logged(world: World) -> list[str]:
    """Each clue the detective *notices* is recorded in the notebook."""
    out: list[str] = []
    for c in world.clues():
        if c.meters["noticed"] < THRESHOLD:
            continue
        sig = ("log", c.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.notebook.append(c.detail)
        c.meters["logged"] += 1
    return out


def _r_kindness_rhythm(world: World) -> list[str]:
    """A confession + an unhurried sitting-down + a rhyme = kindness embedded."""
    for det in world.characters():
        if det.type not in {"detective-girl", "detective-boy"}:
            continue
        if det.memes["confession"] < THRESHOLD:
            continue
        if det.memes["sat_down"] < THRESHOLD:
            continue
        if det.memes["shared_rhyme"] < THRESHOLD:
            continue
        sig = ("kindness", det.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        det.memes["kindness"] += 1
        world.kind_ending = True
    return []


def _r_case_closes(world: World) -> list[str]:
    """Forgiveness from the victim + kindness embedded -> the case is closed."""
    for det in world.characters():
        if det.type not in {"detective-girl", "detective-boy"}:
            continue
        if det.memes["kindness"] < THRESHOLD:
            continue
        sig = ("close", det.id)
        if sig in world.fired:
            continue
        if not world.kind_ending:
            continue
        world.fired.add(sig)
        world.case_closed = True
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="clue_logged", apply=_r_clue_logged),
    Rule(name="kindness_rhythm", apply=_r_kindness_rhythm),
    Rule(name="case_closes", apply=_r_case_closes),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for r in CAUSAL_RULES:
            if r.apply(world):
                changed = True


# ---------------------------------------------------------------------------
# Rhyming line generator: a kind two-line rhyme built from the case and culprit.
# ---------------------------------------------------------------------------
def rhyme_line_a(case: Case) -> str:
    a, b = case.rhyme_pair
    return f"Here is a small and honest {b},"


def rhyme_line_b(culprit: Culprit) -> str:
    return f"and a {culprit.type} learns to share."


def closing_rhyme(case: Case, culprit: Culprit) -> str:
    return (
        f'"{rhyme_line_a(case)} {rhyme_line_b(culprit)}," '
        f"they said together, in soft voices."
    )


# ---------------------------------------------------------------------------
# Verbs (each mutates state, then narrates)
# ---------------------------------------------------------------------------
def introduce_detective(world: World, det: Entity) -> None:
    det.memes["introduced"] += 1
    world.say(
        f"In a small and tidy town there lived a particular little detective "
        f"named {det.id}."
    )
    world.say(
        f"{det.pronoun('subject').capitalize()} wore a small {det.color} hat "
        f"and carried a small notebook, in which {det.pronoun('subject')} "
        f"wrote down everything {det.pronoun('subject')} noticed."
    )


def case_opens(world: World, det: Entity, victim: Entity, case: Case) -> None:
    world.case_open = True
    world.say(
        f"One morning, a {victim.type} came to the door and said, "
        f'"Three of my {case.missing_noun} are missing from my {case.rhyme_pair[0]}, '
        f'and the {case.rhyme_pair[0]} still smells of {case.smell}."'
    )
    world.say(
        f"{det.id} put on {det.pronoun('possessive')} hat, took the small notebook, "
        f"and walked to the {victim.type}'s place."
    )


def finds_clue(world: World, det: Entity, clue_entity: Entity) -> None:
    det.memes["clues_found"] += 1
    clue_entity.meters["noticed"] += 1
    propagate(world)
    world.say(
        f"On the floor, on a shelf, and on a small dish, {det.id} found three clues: "
        f"a {clue_entity.clues[0]}, a {clue_entity.clues[1]}, and a paper note."
    )


def note_text(world: World, det: Entity, note_text_value: str) -> None:
    det.memes["note_seen"] += 1
    det.clues = det.clues or []
    det.clues.append(note_text_value)
    world.say(
        f"The note, in careful letters, said: \"{note_text_value}\" "
        f"{det.id} copied the note into the notebook, exactly word for word."
    )


def follows_trail(world: World, det: Entity, culprit: Entity) -> None:
    det.memes["trail_followed"] += 1
    world.say(
        f"{det.pronoun('subject').capitalize()} followed the small prints to a "
        f"little garden, and there {det.pronoun('subject')} met "
        f"{culprit.phrase} with a {culprit.button_shape}-shaped button on "
        f"{culprit.pronoun('possessive')} collar."
    )


def twist_revealed(world: World, det: Entity, culprit: Entity) -> None:
    det.memes["confession"] += 1
    culprit.memes["confessed"] += 1
    world.twist_seen = True
    world.say(
        f'"I took the {culprit.memes.get("took", "things")}," '
        f'the {culprit.type} said softly, "because I had no breakfast and no '
        f'one came to the garden this morning."'
    )


def kindness_pause(world: World, det: Entity, culprit: Entity) -> None:
    det.memes["sat_down"] += 1
    world.say(
        f"{det.pronoun('subject').capitalize()} did not shout. "
        f"{det.pronoun('subject').capitalize()} sat down beside the {culprit.type}, "
        f"and the two of them shared a rhyme about crumbs and kindness."
    )


def rhyme_spoken(world: World, det: Entity, case: Case, culprit: Culprit) -> None:
    det.memes["shared_rhyme"] += 1
    world.say(closing_rhyme(case, culprit))


def walks_back(world: World, det: Entity, culprit: Entity, victim: Entity) -> None:
    world.say(
        f"Then {det.id} walked back to the {victim.type} with the {culprit.type} "
        f"beside {det.pronoun('object')}, slow and quiet."
    )


def baker_forgives(world: World, victim: Entity, culprit: Entity, case: Case) -> None:
    victim.memes["forgave"] += 1
    culprit.memes["relief"] += 1
    world.say(
        f"The {victim.type} looked at the {culprit.type}, and at the small "
        f"notebook, and smiled. \"Bring {culprit.pronoun('object')} in,\" "
        f'{culprit.pronoun('subject')} said, "and let us share what we have."'
    )
    world.say(
        f"The {victim.type} gave each of them a warm {case.missing_singular}, "
        f"fresh from a new {case.rhyme_pair[0]}, and the {culprit.type} bowed."
    )


def culprit_thanks(world: World, det: Entity, culprit: Entity) -> None:
    world.say(
        f'"Thank you, particular detective, for being kind," the '
        f"{culprit.type} said."
    )


def case_closes(world: World, det: Entity, case: Case) -> None:
    propagate(world)
    if world.case_closed:
        world.say(
            f"{det.id} tipped {det.pronoun('possessive')} hat, wrote "
            f'"Case closed, with kindness" in the notebook, and walked home '
            f"under a small bright sky. The notebook held three clues, a "
            f"careful note, and a rhyme the {case.victim_type} would remember."
        )


# ---------------------------------------------------------------------------
# The screenplay (driven entirely by verbs + state)
# ---------------------------------------------------------------------------
def tell(case: Case, culprit: Culprit, clue_cfg: Clue,
         det_name: str = "Pip", det_type: str = "detective-girl",
         det_color: str = "gray",
         victim_type: Optional[str] = None) -> World:
    world = World()
    if victim_type is None:
        victim_type = case.victim_type

    det = world.add(Entity(
        id=det_name, kind="character", type=det_type, color=det_color,
        traits=["particular", "kind", "careful"],
    ))
    victim = world.add(Entity(
        id="victim", kind="character", type=victim_type,
        label=f"the {victim_type}",
    ))
    culprit_ent = world.add(Entity(
        id="culprit", kind="character", type=culprit.type,
        label=f"the {culprit.type}",
        color=culprit.color,
    ))
    # A single clue entity whose .clues is a triple of detail strings.
    clue_entity = world.add(Entity(
        id="clue", kind="clue", type=clue_cfg.kind,
        clues=[clue_cfg.kind, clue_cfg.detail, "paper note"],
    ))

    # Act 1: setup -- a particular detective, a case that walks in.
    introduce_detective(world, det)
    world.para()
    case_opens(world, det, victim, case)

    # Act 2: the investigation -- three clues, a trail, the twist.
    world.para()
    finds_clue(world, det, clue_entity)
    note_text(world, det, culprit.confession)
    follows_trail(world, det, culprit_ent)
    twist_revealed(world, det, culprit_ent)

    # Act 3: kindness, rhyme, forgiveness, the closing image.
    world.para()
    kindness_pause(world, det, culprit_ent)
    rhyme_spoken(world, det, case, culprit_ent)
    walks_back(world, det, culprit_ent, victim)
    baker_forgives(world, victim, culprit_ent, case)
    culprit_thanks(world, det, culprit_ent)
    case_closes(world, det, case)

    world.facts.update(
        det=det, victim=victim, culprit=culprit_ent,
        case=case, culprit=culprit, clue=clue_cfg,
        notebook=world.notebook,
        case_open=world.case_open,
        case_closed=world.case_closed,
        twist_seen=world.twist_seen,
        kind_ending=world.kind_ending,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
CASES = {
    "muffins": Case(
        id="muffins",
        victim_type="baker",
        missing_noun="muffins",
        missing_phrase="three small muffins",
        missing_singular="muffin",
        plural=True,
        smell="berries",
        rhyme_pair=("tin", "skin"),
        tags={"baker", "muffin", "tin"},
    ),
    "buttons": Case(
        id="buttons",
        victim_type="tailor",
        missing_noun="buttons",
        missing_phrase="three small buttons",
        missing_singular="button",
        plural=True,
        smell="thread",
        rhyme_pair=("tin", "pin"),
        tags={"tailor", "button"},
    ),
    "books": Case(
        id="books",
        victim_type="librarian",
        missing_noun="books",
        missing_phrase="three small books",
        missing_singular="book",
        plural=True,
        smell="paper",
        rhyme_pair=("shelf", "self"),
        tags={"librarian", "book"},
    ),
    "apples": Case(
        id="apples",
        victim_type="gardener",
        missing_noun="apples",
        missing_phrase="three small apples",
        missing_singular="apple",
        plural=True,
        smell="leaves",
        rhyme_pair=("basket", "ask it"),
        tags={"gardener", "apple"},
    ),
}

CULPRITS = {
    "rabbit": Culprit(
        id="rabbit",
        type="rabbit",
        phrase="a small gray rabbit",
        color="gray",
        button_shape="star",
        confession="I was hungry, and I am sorry",
        relief_word="share",
        rhyme_word="skin",
        tags={"rabbit", "small", "kind"},
    ),
    "mouse": Culprit(
        id="mouse",
        type="mouse",
        phrase="a small brown mouse",
        color="brown",
        button_shape="moon",
        confession="I was curious, and I am sorry",
        relief_word="share",
        rhyme_word="pin",
        tags={"mouse", "small", "kind"},
    ),
    "kitten": Culprit(
        id="kitten",
        type="kitten",
        phrase="a small orange kitten",
        color="orange",
        button_shape="leaf",
        confession="I was lonely, and I am sorry",
        relief_word="share",
        rhyme_word="self",
        tags={"kitten", "small", "kind"},
    ),
    "fox": Culprit(
        id="fox",
        type="fox",
        phrase="a small red fox",
        color="red",
        button_shape="heart",
        confession="I was tired, and I am sorry",
        relief_word="share",
        rhyme_word="ask it",
        tags={"fox", "small", "kind"},
    ),
}

CLUES = {
    "footprint": Clue(
        id="footprint",
        kind="footprint",
        detail="a faint blue footprint on the floor",
        note_text=None,
        rhyme_word="floor",
        tags={"footprint", "blue"},
    ),
    "thread": Clue(
        id="thread",
        kind="thread",
        detail="a single loose thread on the doorstep",
        note_text=None,
        rhyme_word="step",
        tags={"thread"},
    ),
    "crumb": Clue(
        id="crumb",
        kind="crumb",
        detail="a single small crumb by the shelf",
        note_text=None,
        rhyme_word="shelf",
        tags={"crumb"},
    ),
    "leaf": Clue(
        id="leaf",
        kind="leaf",
        detail="a single small leaf by the basket",
        note_text=None,
        rhyme_word="basket",
        tags={"leaf"},
    ),
}

DETECTIVE_NAMES_GIRL = ["Pip", "Mira", "Wren", "Ivy", "Juno", "Sage", "Lila", "Thea", "Fern", "Esme"]
DETECTIVE_NAMES_BOY = ["Kit", "Theo", "Reo", "Jude", "Otis", "Nico", "Cato", "Levi", "Bram", "Wells"]
HAT_COLORS = ["gray", "blue", "brown", "green", "violet"]
TRAITS = ["particular", "patient", "gentle", "quiet", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    """(case, culprit, clue, detective_type) sets that compose into a kind tale."""
    combos: list[tuple[str, str, str, str]] = []
    for case_id in CASES:
        for culprit_id in CULPRITS:
            for clue_id in CLUES:
                for dtype in ("detective-girl", "detective-boy"):
                    combos.append((case_id, culprit_id, clue_id, dtype))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    case: str
    culprit: str
    clue: str
    name: str
    gender: str
    hat: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det, case, culprit = f["det"], f["case"], f["culprit"]
    return [
        f'Write a short detective story for a 3-to-5-year-old that uses the '
        f'word "particular" and ends with a kind resolution.',
        f'Tell a rhyming detective story where {det.id} solves a small missing-'
        f'{case.missing_noun} case and forgives the {culprit.type} who took them.',
        f'Write a gentle story that includes a small clue, a small note that '
        f'says "{culprit.confession}", and a two-line kindness rhyme.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det, victim, culprit, case, clue = (
        f["det"], f["victim"], f["culprit"], f["case"], f["clue"],
    )
    sub, obj, pos = (det.pronoun("subject"), det.pronoun("object"),
                     det.pronoun("possessive"))
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the particular little detective who came to help the "
                f"{victim.type} when three {case.missing_noun} went missing?"
            ),
            answer=(
                f"It was a particular little detective named {det.id}, who "
                f"wore a small {det.color} hat and carried a small notebook. "
                f"{sub.capitalize()} wrote down everything {sub} noticed."
            ),
        ),
        QAItem(
            question=(
                f"What three clues did {det.id} find at the {victim.type}'s place "
                f"about the missing {case.missing_noun}?"
            ),
            answer=(
                f"{det.id} found three clues: a {clue.detail}, a "
                f"{culprit.button_shape}-shaped button, and a paper note in "
                f"careful letters."
            ),
        ),
        QAItem(
            question=(
                f"What did the paper note say that {det.id} copied into the "
                f"notebook word for word?"
            ),
            answer=(
                f"The paper note, in careful letters, said: "
                f"\"{culprit.confession}.\" {det.id} copied it exactly, word for word."
            ),
        ),
    ]
    if f.get("twist_seen"):
        qa.append(QAItem(
            question=(
                f"How did the {culprit.type} explain taking the "
                f"{case.missing_noun} in the small garden?"
            ),
            answer=(
                f"The {culprit.type} said softly, \"{culprit.confession},\" "
                f"because no breakfast had come and no one had come to the garden."
            ),
        ))
    if f.get("kind_ending"):
        qa.append(QAItem(
            question=(
                f"What small rhyme did {det.id} and the {culprit.type} share "
                f"before going back to the {victim.type}?"
            ),
            answer=(
                f"They shared a small rhyme together: "
                f"\"{rhyme_line_a(case)} {rhyme_line_b(culprit)}.\" It was a "
                f"rhyme about crumbs and kindness, in soft voices."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did the {victim.type} greet the {culprit.type} when "
                f"{det.id} brought {culprit.pronoun('object')} back to the shop?"
            ),
            answer=(
                f"The {victim.type} smiled, forgave the {culprit.type}, and "
                f"gave each of them a warm {case.missing_singular} fresh from "
                f"a new {case.rhyme_pair[0]}."
            ),
        ))
    if f.get("case_closed"):
        qa.append(QAItem(
            question=(
                f"How did {det.id} close the case of the missing "
                f"{case.missing_noun} in the notebook?"
            ),
            answer=(
                f"{det.id} tipped {pos} hat and wrote \"Case closed, with "
                f"kindness\" in the notebook, then walked home under a small "
                f"bright sky."
            ),
        ))
    return qa


KNOWLEDGE = {
    "detective": [
        ("What is a detective?",
         "A detective is a person who looks carefully at small clues to find "
         "out what happened when something is missing or wrong."),
    ],
    "notebook": [
        ("Why do detectives carry notebooks?",
         "Detectives carry notebooks so they can write down what they see and "
         "remember each clue exactly as they noticed it."),
    ],
    "clue": [
        ("What is a clue?",
         "A clue is a small thing -- a footprint, a button, a note -- that "
         "helps you guess what really happened."),
    ],
    "kindness": [
        ("Why does kindness matter when you solve a problem?",
         "Kindness matters when you solve a problem because the person who did "
         "the wrong thing can learn, and the hurt can turn into a small, kind "
         "moment instead of a louder one."),
    ],
    "rhyme": [
        ("What is a rhyme?",
         "A rhyme is when two words end with the same sound, like 'tin' and "
         "'skin' or 'hare' and 'share'."),
    ],
    "twist": [
        ("What is a twist in a story?",
         "A twist is a small surprise near the end of a story that changes "
         "how you understand what just happened."),
    ],
    "muffin": [
        ("What is a muffin?",
         "A muffin is a small, soft cake baked in a tin, often with berries "
         "or fruit folded into the dough."),
    ],
    "button": [
        ("What is a button?",
         "A button is a small round fastener on clothes that fits through a "
         "small slit called a buttonhole."),
    ],
    "rabbit": [
        ("What do rabbits like to eat?",
         "Rabbits like to eat tender leaves, carrots, and small green things "
         "they find in the garden."),
    ],
    "forgive": [
        ("What does it mean to forgive someone?",
         "To forgive someone means to let go of the hurt they caused and to "
         "treat them kindly again."),
    ],
}
KNOWLEDGE_ORDER = ["detective", "notebook", "clue", "kindness", "rhyme", "twist",
                   "muffin", "button", "rabbit", "forgive"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set()
    tags.update(f["case"].tags)
    tags.update(f["culprit"].tags)
    tags.add("detective")
    tags.add("notebook")
    tags.add("kindness")
    tags.add("rhyme")
    tags.add("twist")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
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


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:18}) {' '.join(bits)}")
    lines.append(f"  notebook: {world.notebook}")
    lines.append(f"  case_open={world.case_open} case_closed={world.case_closed} "
                 f"twist_seen={world.twist_seen} kind_ending={world.kind_ending}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(case="muffins", culprit="rabbit", clue="footprint",
                name="Pip", gender="girl", hat="gray", trait="particular"),
    StoryParams(case="buttons", culprit="mouse", clue="thread",
                name="Kit", gender="boy", hat="blue", trait="patient"),
    StoryParams(case="books", culprit="kitten", clue="crumb",
                name="Wren", gender="girl", hat="green", trait="gentle"),
    StoryParams(case="apples", culprit="fox", clue="leaf",
                name="Theo", gender="boy", hat="brown", trait="thoughtful"),
]


def explain_invalid(case_id: str, culprit_id: str) -> str:
    return (
        f"(No story: the case '{case_id}' and the culprit '{culprit_id}' do "
        f"not compose into a kind detective tale here. Try a different pairing.)"
    )


# ---------------------------------------------------------------------------
# ASP twin -- a small declarative reasonableness gate for the curated set.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A kind detective story needs a case, a culprit, a clue, and a detective type.
story(C, U, L, D) :- case(C), culprit(U), clue(L), detective(D).

% A kind closing requires all three: confession, a rhyme, and a forgiveness beat.
kind_closing(D) :- has_confession(D), has_rhyme(D), has_forgiveness(D).

% A case can only be closed if it was opened and then closed with kindness.
closed(D) :- opens(D), kind_closing(D).

#show story/4.
#show kind_closing/1.
#show closed/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in CASES:
        lines.append(asp.fact("case", cid))
    for uid in CULPRITS:
        lines.append(asp.fact("culprit", uid))
    for lid in CLUES:
        lines.append(asp.fact("clue", lid))
    for d in ("detective-girl", "detective-boy"):
        lines.append(asp.fact("detective", d))
    # Auxiliary facts describing narrative beats every detective uses here.
    for d in ("detective-girl", "detective-boy"):
        lines.append(asp.fact("opens", d))
        lines.append(asp.fact("has_confession", d))
        lines.append(asp.fact("has_rhyme", d))
        lines.append(asp.fact("has_forgiveness", d))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story/4."))
    return sorted(set(asp.atoms(model, "story")))


def asp_kind_closings() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show kind_closing/1."))
    return sorted(set(asp.atoms(model, "kind_closing")))


def asp_verify() -> int:
    clingo_stories = set(asp_stories())
    python_stories = set(valid_combos())
    if clingo_stories == python_stories:
        print(f"OK: clingo gate matches valid_combos() "
              f"({len(clingo_stories)} stories).")
        # Exercise: every curated sample must render and close.
        for p in CURATED:
            sample = generate(p)
            if not sample.world.facts["case_closed"]:
                print(f"FAIL: curated sample {p.name} did not close the case.")
                return 1
        print(f"OK: rendered and closed {len(CURATED)} curated samples.")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_stories - python_stories:
        print("  only in clingo:", sorted(clingo_stories - python_stories))
    if python_stories - clingo_stories:
        print("  only in python:", sorted(python_stories - clingo_stories))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a particular detective, a twist, a "
                    "kind rhyme. Unspecified choices are picked at random "
                    "(seeded).")
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--hat", choices=HAT_COLORS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true",
                    help="list the kind-detective-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.case and args.culprit and args.case not in {"muffins", "buttons", "books", "apples"}:
        raise StoryError(explain_invalid(args.case, args.culprit))

    combos = [c for c in valid_combos()
              if (args.case is None or c[0] == args.case)
              and (args.culprit is None or c[1] == args.culprit)
              and (args.clue is None or c[2] == args.clue)
              and (args.gender is None
                   or (c[3] == "detective-girl" and args.gender == "girl")
                   or (c[3] == "detective-boy" and args.gender == "boy"))]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    case, culprit, clue, dtype = rng.choice(sorted(combos))
    gender = args.gender or ("girl" if dtype == "detective-girl" else "boy")
    name = args.name or rng.choice(DETECTIVE_NAMES_GIRL if gender == "girl"
                                   else DETECTIVE_NAMES_BOY)
    hat = args.hat or rng.choice(HAT_COLORS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        case=case, culprit=culprit, clue=clue,
        name=name, gender=gender, hat=hat, trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    det_type = "detective-girl" if params.gender == "girl" else "detective-boy"
    world = tell(CASES[params.case], CULPRITS[params.culprit], CLUES[params.clue],
                 det_name=params.name, det_type=det_type, det_color=params.hat)
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

    if args.show_asp:
        print(asp_program("#show story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_stories()
        print(f"{len(stories)} kind detective stories (case, culprit, clue, type):\n")
        for case, culprit, clue, dtype in stories:
            print(f"  {case:8} {culprit:7} {clue:9} {dtype}")
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
            header = (f"### {p.name}: {p.case} case, {p.culprit} culprit, "
                      f"{p.clue} clue")
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
