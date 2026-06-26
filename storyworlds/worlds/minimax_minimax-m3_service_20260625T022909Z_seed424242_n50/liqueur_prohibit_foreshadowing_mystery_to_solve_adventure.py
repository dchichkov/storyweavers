#!/usr/bin/env python3
"""
storyworlds/worlds/liqueur_prohibit_foreshadowing_mystery_to_solve_adventure.py
==============================================================================

A standalone *story world* sketch in the spirit of the seed

    "liqueur, prohibit" + Foreshadowing + Mystery to Solve + Adventure

The seed paints a tiny, child-safe intrigue: at a great-aunt's house, the
grown-ups keep disappearing into a small, locked room.  A bright child,
their older cousin, and the kindly butler have to find out what the
adults are doing in there (a banned coffee liqueur tasting), and what
better sense of "mystery to solve" and "foreshadowing" there is than the
clues the house keeps leaving behind?

Initial story (used to build the world model)
---
Once upon a time, in a small town by the sea, there was a clever girl
named Nora who was visiting her great-aunt Mira for the whole summer.
The house had a long hallway with many closed doors, and one tiny door
at the very end that the grown-ups always closed behind them when they
went inside.

Nora liked adventures, and her cousin Otto, who was a little older,
liked puzzles.  One morning the grown-ups whispered at breakfast about a
"surprise" they were keeping from the children.  Later that day Nora
spotted a small puddle of dark liquid near the tiny door, and a faint
sweet smell in the air.  Otto found a list of rules pinned behind a
painting: "No tasting in the kitchen.  No sharing with the children.
No bottles out where the little ones can see."

The two cousins decided it was a mystery worth solving.  They followed
the clues: the dark puddle, the sweet smell, the grown-ups' whispers,
the hidden list of rules, and a worn recipe book in the pantry.  With
the butler's help they discovered the truth -- the grown-ups were
tasting a banned coffee liqueur, a treat strictly prohibited by
great-aunt Mira's own house rule.  Because the children had solved the
mystery cleanly (without tasting it themselves), Mira laughed, said the
children had earned a turn, and poured each of them a single, careful
sip from a tiny cup -- her way of welcoming them to the grown-up table.

Foreshadowing beats (state->prose)
---
    do adult preparation        -> adult.secret += 1   (grown-up grows more guarded)
    child reads rule            -> child.evidence += 1
    child spots physical clue   -> child.evidence += 1
    child confronts adult       -> adult.guilt += 1
    adult fesses up             -> child.trust += 1 ; adult.guilt -> 0

Mystery-to-Solve beats
---
    every clue the children gather adds one *evidence* tick
    until 3 ticks -> mystery solved
    if children < 3 evidence -> mystery remains open
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

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Family-room kinds and physical regions for the gear-coverage-style constraint.
ROOMS = {"kitchen", "pantry", "hallway", "locked_room", "garden"}

# Clue kinds the world can leave behind, each tied to a different sense.
CLUE_KINDS = {"puddle", "sweet_smell", "whisper", "rule_list", "recipe_book", "keyhole_glimpse"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # girl, boy, butler, aunt, mother ...
    label: str = ""                # short reference
    phrase: str = ""               # full noun phrase, e.g. "a clever girl named Nora"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    region: str = ""                  # where an object sits: kitchen | hallway | locked_room
    protective: bool = False          # keeps the secret closed (locked_room door)
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "great-aunt", "maid"}
        male = {"boy", "man", "father", "uncle", "butler", "gardener"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"great-aunt": "aunt"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "great-aunt Mira's house"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)   # which clues this place supports


@dataclass
class Clue:
    """A single foreshadowing breadcrumb left in the world."""
    id: str
    noun: str           # "a small dark puddle"
    place: str          # where it is found: ROOMS
    sense: str          # "see" | "smell" | "hear"
    test: Callable[["World", Entity], bool]   # can this child spot it right now?


@dataclass
class Liqueur:
    """The thing the grown-ups are hiding -- with one clear rule against it."""
    id: str
    name: str           # "the coffee liqueur"
    rule: str           # the house rule that prohibits it
    evidence_phrase: str  # how the children describe their evidence


@dataclass
class Reveal:
    """The dramatic turn: how the secret is finally exposed, and the payoff."""
    id: str
    opener: str         # how the confrontation opens
    confession: str     # how the adult finally confesses
    payoff: str         # the child's earned sip at the end


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.room: str = ""            # current room of action (foreshadowing)
        self.facts: dict = {}

    # entity helpers
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def objects_in(self, region: str) -> list[Entity]:
        return [e for e in self.entities.values() if e.region == region]

    # narration helpers
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.room = self.room
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_secret_grows(world: World) -> list[str]:
    """Any adult who helps prepare the surprise grows more guarded."""
    out: list[str] = []
    for ent in world.characters():
        if ent.type not in {"aunt", "great-aunt", "mother", "father", "butler", "maid"}:
            continue
        if ent.meters["prep"] < THRESHOLD:
            continue
        sig = ("secret", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["secret"] += 1
        out.append(
            f"{ent.id} looked around to be sure no one was listening before "
            f"{ent.pronoun()} went on with the work."
        )
    return out


def _r_guilt_at_confrontation(world: World) -> list[str]:
    """A child confronting an adult whose secret is up -> adult guilt."""
    for adult in world.characters():
        if adult.memes["secret"] < THRESHOLD:
            continue
        for child in world.characters():
            if child.type not in {"girl", "boy"}:
                continue
            if child.memes["confronted"] < THRESHOLD:
                continue
            sig = ("guilt", adult.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            adult.memes["guilt"] += 1
            return ["__guilt__"]
    return []


def _r_trust_on_confession(world: World) -> list[str]:
    """If the adult confessed and was caught -> child's trust rises, guilt clears."""
    for adult in world.characters():
        if adult.memes["confessed"] < THRESHOLD:
            continue
        for child in world.characters():
            if child.type not in {"girl", "boy"}:
                continue
            sig = ("trust", child.id, adult.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            child.memes["trust"] += 1
            adult.memes["guilt"] = 0.0
            return ["__trust__"]
    return []


def _r_evidence_threshold(world: World) -> list[str]:
    """When the lead child gathers 3+ evidence, the mystery is solvable."""
    for child in world.characters():
        if child.type not in {"girl", "boy"}:
            continue
        if child.meters["evidence"] < 3:
            continue
        sig = ("mystery", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["mystery_solved"] = 1.0
        return ["__solved__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="secret_grows", tag="social", apply=_r_secret_grows),
    Rule(name="guilt_confront", tag="social", apply=_r_guilt_at_confrontation),
    Rule(name="trust_confess", tag="social", apply=_r_trust_on_confession),
    Rule(name="mystery_threshold", tag="mystery", apply=_r_evidence_threshold),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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
def clue_plausible(setting: Setting, clue: Clue) -> bool:
    return clue.place in setting.affords


def select_clues(setting: Setting, count: int = 3) -> list[Clue]:
    """Pick the first N clues that this place can plausibly host."""
    out: list[Clue] = []
    for c in CLUES:
        if clue_plausible(setting, c):
            out.append(c)
            if len(out) >= count:
                break
    return out


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def setting_detail(setting: Setting) -> str:
    if setting.place == "great-aunt Mira's house":
        return ("The house smelled of lemon polish and old books, and a long "
                "hallway with many closed doors led toward a tiny door at the "
                "very end.")
    return f"{setting.place.capitalize()} was full of quiet corners and small, useful secrets."


def introduce(world: World, hero: Entity, cousin: Entity) -> None:
    trait = next((t for t in hero.traits if t not in {"little", "young"}), "")
    c_trait = next((t for t in cousin.traits if t not in {"little", "young", "older"}), "")
    world.say(
        f"In a small town by the sea, there was a {trait} {hero.type} named "
        f"{hero.id}, who was visiting {hero.pronoun('possessive)} great-aunt for "
        f"the summer."
    )
    world.say(
        f"{cousin.id}, {cousin.pronoun('possessive')} older cousin, came to stay "
        f"too. {cousin.pronoun('subject').capitalize()} liked puzzles; {hero.id} "
        f"liked adventures."
    )


def arrive(world: World, hero: Entity, cousin: Entity, setting: Setting) -> None:
    world.say(f"They spent the first week exploring {setting.place}.")
    world.say(setting_detail(setting))


def whisper_beats(world: World, hero: Entity, liqueur: Liqueur) -> None:
    """Foreshadowing beat 1: the grown-ups whisper at breakfast."""
    for adult in world.characters():
        if adult.type not in {"aunt", "great-aunt", "mother", "father", "butler", "maid"}:
            continue
        adult.meters["prep"] += 1
        adult.memes["secret"] += 1
        world.say(
            f"On the second morning, {adult.id} and {adult.pronoun('possessive')} "
            f"friends whispered about a surprise they were keeping from the "
            f"children."
        )
        break


def find_puddle(world: World, hero: Entity, liqueur: Liqueur) -> None:
    """Foreshadowing beat 2: a small dark puddle near the tiny door."""
    world.room = "hallway"
    hero.meters["evidence"] += 1
    world.say(
        f"That afternoon, {hero.id} walked the long hallway and noticed a small "
        f"dark puddle near the tiny door at the end."
    )


def find_sweet_smell(world: World, hero: Entity, liqueur: Liqueur) -> None:
    """Foreshadowing beat 3: a faint sweet smell in the air."""
    world.room = "kitchen"
    hero.meters["evidence"] += 1
    world.say(
        f"In the kitchen there was a faint sweet smell, like coffee with sugar "
        f"hidden in the back of a cupboard."
    )


def find_rule_list(world: World, cousin: Entity, liqueur: Liqueur) -> None:
    """Mystery beat 1: the rule list pinned behind the painting."""
    cousin.meters["evidence"] += 1
    world.say(
        f"{cousin.id} found a small list pinned behind a painting in the hallway. "
        f'It read: "{liqueur.rule}"'
    )


def find_recipe_book(world: World, cousin: Entity, liqueur: Liqueur) -> None:
    """Mystery beat 2: a worn recipe book in the pantry."""
    cousin.meters["evidence"] += 1
    world.say(
        f"In the pantry, {cousin.id} found a worn recipe book with a sticky note: "
        f'"{liqueur.name}, for grown-ups only."'
    )


def keyhole_glimpse(world: World, hero: Entity, cousin: Entity, liqueur: Liqueur) -> None:
    """Mystery beat 3: a glimpse through the keyhole of the tiny door."""
    world.room = "locked_room"
    hero.meters["evidence"] += 1
    world.say(
        f"Together they knelt by the tiny door and peeked through the keyhole. "
        f"They saw a long table with small cups and a tall bottle in the middle."
    )


def consult_butler(world: World, hero: Entity, cousin: Entity, butler: Entity) -> None:
    """The butler, who is on the children's side, agrees to help."""
    butler.memes["allied"] += 1
    world.say(
        f"They went to {butler.id}, who smiled and said he would help, so long "
        f"as the children promised not to taste anything before the truth was "
        f"known."
    )


def confrontation(world: World, hero: Entity, cousin: Entity, aunt: Entity,
                  liqueur: Liqueur) -> None:
    """The children confront the great-aunt with their evidence."""
    hero.memes["confronted"] += 1
    cousin.memes["confronted"] += 1
    propagate(world, narrate=False)          # fires guilt rule
    world.say(
        f"That evening, {hero.id} and {cousin.id} stood in front of "
        f"{aunt.id} and laid their clues on the table: the puddle, the sweet "
        f"smell, the rule list, the recipe book, and the glimpse through the "
        f"keyhole."
    )


def confession(world: World, aunt: Entity, liqueur: Liqueur, reveal: Reveal) -> None:
    """The aunt confesses, the rule is named, the tension resolves."""
    aunt.memes["confessed"] += 1
    propagate(world, narrate=False)          # fires trust rule
    world.say(reveal.confession)


def payoff(world: World, hero: Entity, cousin: Entity, aunt: Entity,
           liqueur: Liqueur, reveal: Reveal) -> None:
    """The children earn a careful sip -- the resolution image."""
    world.say(reveal.payoff)


def landing_image(world: World, hero: Entity, liqueur: Liqueur) -> None:
    """The closing image: a concrete, sensory proof that something changed."""
    world.say(
        f"They finished their small cups and looked out at the garden, where "
        f"the evening light made the lemon trees shine. The mystery of "
        f"{liqueur.name} was theirs now, too."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, liqueur: Liqueur, reveal: Reveal,
         hero_name: str, hero_type: str, cousin_name: str, cousin_type: str,
         aunt_type: str, butler_name: str = "Mr. Penny",
         butler_type: str = "butler",
         hero_traits: Optional[list[str]] = None,
         cousin_traits: Optional[list[str]] = None) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "brave"]),
    ))
    cousin = world.add(Entity(
        id=cousin_name, kind="character", type=cousin_type,
        traits=["older"] + (cousin_traits or ["clever", "patient"]),
    ))
    aunt = world.add(Entity(
        id="Aunt", kind="character", type=aunt_type, label="aunt",
    ))
    butler = world.add(Entity(
        id=butler_name, kind="character", type=butler_type, label="the butler",
        protective=True, covers={"locked_room"},
    ))
    bottle = world.add(Entity(
        id="bottle", type="bottle", label="the bottle", region="locked_room",
        owner=aunt.id,
    ))
    tiny_door = world.add(Entity(
        id="tiny_door", type="door", label="the tiny door",
        region="hallway", protective=True, covers={"locked_room"},
    ))

    # Act 1 -- setup
    introduce(world, hero, cousin)
    arrive(world, hero, cousin, setting)

    # Act 2 -- foreshadowing + mystery
    world.para()
    whisper_beats(world, hero, liqueur)
    find_puddle(world, hero, liqueur)
    find_sweet_smell(world, hero, liqueur)
    find_rule_list(world, cousin, liqueur)
    consult_butler(world, hero, cousin, butler)
    find_recipe_book(world, cousin, liqueur)
    keyhole_glimpse(world, hero, cousin, liqueur)

    # Act 3 -- confrontation, confession, payoff
    world.para()
    confrontation(world, hero, cousin, aunt, liqueur)
    confession(world, aunt, liqueur, reveal)
    payoff(world, hero, cousin, aunt, liqueur, reveal)
    landing_image(world, hero, liqueur)

    # Record facts for the Q&A generators.
    world.facts.update(
        hero=hero, cousin=cousin, aunt=aunt, butler=butler, bottle=bottle,
        tiny_door=tiny_door, liqueur=liqueur, reveal=reveal, setting=setting,
        evidence=int(hero.meters["evidence"] + cousin.meters["evidence"]),
        resolved=bool(hero.memes["mystery_solved"] >= THRESHOLD
                      or cousin.memes["mystery_solved"] >= THRESHOLD),
        confessed=bool(aunt.memes["confessed"] >= THRESHOLD),
    )
    return world


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "aunt_house": Setting(
        place="great-aunt Mira's house",
        indoor=True,
        affords={"hallway", "kitchen", "pantry", "locked_room", "garden"},
    ),
    "manor": Setting(
        place="the old manor",
        indoor=True,
        affords={"hallway", "kitchen", "pantry", "locked_room", "garden"},
    ),
    "villa": Setting(
        place="the seaside villa",
        indoor=True,
        affords={"kitchen", "pantry", "locked_room", "garden"},
    ),
}

CLUES = [
    Clue(
        id="puddle",
        noun="a small dark puddle",
        place="hallway",
        sense="see",
        test=lambda w, h: True,
    ),
    Clue(
        id="sweet_smell",
        noun="a faint sweet smell",
        place="kitchen",
        sense="smell",
        test=lambda w, h: True,
    ),
    Clue(
        id="rule_list",
        noun="a small list pinned behind a painting",
        place="hallway",
        sense="see",
        test=lambda w, h: True,
    ),
    Clue(
        id="recipe_book",
        noun="a worn recipe book in the pantry",
        place="pantry",
        sense="see",
        test=lambda w, h: True,
    ),
    Clue(
        id="keyhole_glimpse",
        noun="a glimpse through the keyhole",
        place="locked_room",
        sense="see",
        test=lambda w, h: True,
    ),
]

LIQUEURS = {
    "coffee_liqueur": Liqueur(
        id="coffee_liqueur",
        name="the coffee liqueur",
        rule="No tasting in the kitchen. No sharing with the children. "
             "No bottles out where the little ones can see.",
        evidence_phrase="grown-ups hiding coffee liqueur from the children",
    ),
    "cherry_liqueur": Liqueur(
        id="cherry_liqueur",
        name="the cherry liqueur",
        rule="No bottles left on the sideboard. No sips before supper. "
             "No sharing until the children earn their cup.",
        evidence_phrase="grown-ups hiding cherry liqueur from the children",
    ),
    "honey_liqueur": Liqueur(
        id="honey_liqueur",
        name="the honey liqueur",
        rule="No tasting in the pantry. No telling the children. "
             "No bottles where the little hands can reach.",
        evidence_phrase="grown-ups hiding honey liqueur from the children",
    ),
}

REVEALS = {
    "earned_sip": Reveal(
        id="earned_sip",
        opener="",
        confession=(
            "\"You found us out,\" she laughed. \"We were tasting "
            "{LIQUEUR}, which is why the rule says the children may not "
            "taste it. Because you solved the puzzle without tasting any, "
            "you have earned your very first sip.\""
        ),
        payoff=(
            "She poured each of them a single careful sip from a tiny cup. "
            "The taste was warm and sweet and a little bitter, like a small "
            "grown-up secret they were finally allowed to share."
        ),
    ),
    "shared_table": Reveal(
        id="shared_table",
        opener="",
        confession=(
            "\"All right,\" she said, sitting down. \"You are right. We were "
            "tasting {LIQUEUR}. The rule was not to share it with children, "
            "and we kept our promise. But you have earned a seat at the "
            "grown-up table today.\""
        ),
        payoff=(
            "She set out two small cups beside the bottle. The cousins "
            "shared the smallest sip and felt the warm sweetness settle on "
            "their tongues."
        ),
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Otto", "Theo", "Ben", "Max", "Sam", "Finn", "Noah", "Eli", "Jude", "Wren"]
TRAITS_HERO = ["curious", "brave", "spirited", "bright", "cheerful"]
TRAITS_COUSIN = ["clever", "patient", "careful", "quiet", "thoughtful"]

AUNT_KINDS = ["great-aunt", "aunt", "grandmother"]
BUTLER_KINDS = ["butler", "housekeeper", "gardener"]


def valid_combos() -> list[tuple[str, str]]:
    """(place, liqueur) pairs that the world can host (place affords the clues)."""
    combos = []
    for place, setting in SETTINGS.items():
        for lid, liqueur in LIQUEURS.items():
            # require at least the three core clue rooms to be afforded
            if {"hallway", "kitchen", "pantry"}.issubset(setting.affords):
                combos.append((place, lid))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    liqueur: str
    reveal: str
    hero: str
    gender: str
    cousin: str
    cousin_gender: str
    aunt_kind: str
    butler_kind: str
    butler_name: str
    trait_hero: str
    trait_cousin: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "liqueur": [("What is a liqueur?",
                 "A liqueur is a sweet, strong drink made by adding sugar "
                 "and flavors to a spirit, and it is usually sipped in "
                 "small amounts after dinner.")],
    "rule": [("What is a house rule?",
              "A house rule is a promise the people living together agree "
              "to keep, like a special kind of family law.")],
    "butler": [("What is a butler?",
                "A butler is a person whose job is to take care of a big "
                "house, opening doors, serving meals, and helping the "
                "family with daily tasks.")],
    "mystery": [("What is a mystery?",
                 "A mystery is something that you do not yet understand, "
                 "and you solve it by gathering clues until the answer "
                 "becomes clear.")],
    "keyhole": [("What is a keyhole?",
                 "A keyhole is the small shaped opening in a lock that "
                 "you slip a key into, and through which you can also "
                 "peek inside a room.")],
    "foreshadow": [("What is foreshadowing?",
                    "Foreshadowing is when a story drops small clues early "
                    "on that hint at what will happen later, so the "
                    "ending feels earned instead of surprising.")],
}
KNOWLEDGE_ORDER = ["liqueur", "rule", "butler", "mystery", "keyhole", "foreshadow"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, cousin, liqueur, setting = f["hero"], f["cousin"], f["liqueur"], f["setting"]
    kw = liqueur.name.replace("the ", "").strip()
    return [
        f'Write a gentle mystery for a 5-to-7-year-old on the theme "children '
        f'solve a grown-up secret" that includes the word "{kw}".',
        f'Write a short adventure where two cousins, {hero.id} and {cousin.id}, '
        f"follow foreshadowing clues in {setting.place} to discover why the "
        f"adults are hiding {liqueur.name}.",
        f"Write a TinyStories-style mystery in which the secret is "
        f"{liqueur.name} and the resolution is the children earning their "
        f"first sip from the grown-ups.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, cousin, aunt, butler, liqueur = (
        f["hero"], f["cousin"], f["aunt"], f["butler"], f["liqueur"],
    )
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = f["setting"].place
    trait = next((t for t in hero.traits if t not in {"little"}), "curious")
    c_trait = next((t for t in cousin.traits if t not in {"older", "little"}), "clever")
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the mystery about when {hero.id} visits {place} and "
                f"finds grown-up clues near the tiny door?"
            ),
            answer=(
                f"It is about a {trait} {hero.type} named {hero.id} and "
                f"{pos} older cousin {cousin.id}, who is {c_trait}. They "
                f"spend the summer at {place} and find a string of clues that "
                f"lead to the grown-ups' secret."
            ),
        ),
        QAItem(
            question=(
                f"What were the grown-ups whispering about at {place} that "
                f"started the mystery for {hero.id} and {cousin.id}?"
            ),
            answer=(
                f"The grown-ups were whispering about a surprise they were "
                f"keeping from the children, which {hero.id} and {cousin.id} "
                f"slowly realized was {liqueur.name}."
            ),
        ),
        QAItem(
            question=(
                f"What five clues did {hero.id} and {cousin.id} gather at "
                f"{place} before they confronted {aunt.id}?"
            ),
            answer=(
                f"They gathered five clues: a small dark puddle near the tiny "
                f"door, a faint sweet smell in the kitchen, a rule list pinned "
                f"behind a painting, a worn recipe book in the pantry, and a "
                f"glimpse through the keyhole of the locked room."
            ),
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=(
                f"How did {aunt.id} react when {hero.id} and {cousin.id} "
                f"confronted her at {place} with their evidence about "
                f"{liqueur.name}?"
            ),
            answer=(
                f"{aunt.id} laughed, said the children were right, and "
                f"thanked them for solving the puzzle without tasting any of "
                f"{liqueur.name} first."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What reward did {hero.id} and {cousin.id} earn for solving "
                f"the {liqueur.name} mystery at {place}?"
            ),
            answer=(
                f"They earned a single, careful sip of {liqueur.name} from "
                f"tiny cups, the way the grown-ups taste it after dinner, "
                f"which was {aunt.id}'s way of welcoming them to the "
                f"grown-up table."
            ),
        ))
    if f.get("resolved"):
        qa.append(QAItem(
            question=(
                f"How did {butler.id} help {hero.id} and {cousin.id} solve "
                f"the {liqueur.name} mystery at {place}?"
            ),
            answer=(
                f"{butler.id} smiled and agreed to help, on the condition "
                f"that the children promise not to taste any of "
                f"{liqueur.name} until the truth was known. He did not give "
                f"the answer himself, but he let them keep following the "
                f"clues until they earned it."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out: list[QAItem] = []
    tags = {"liqueur", "rule", "butler", "mystery", "keyhole", "foreshadow"}
    if f.get("resolved"):
        tags.add("mystery")
    if f.get("confessed"):
        tags.add("rule")
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="aunt_house", liqueur="coffee_liqueur", reveal="earned_sip",
        hero="Nora", gender="girl", cousin="Otto", cousin_gender="boy",
        aunt_kind="great-aunt", butler_kind="butler", butler_name="Mr. Penny",
        trait_hero="curious", trait_cousin="patient",
    ),
    StoryParams(
        place="manor", liqueur="cherry_liqueur", reveal="shared_table",
        hero="Mia", gender="girl", cousin="Theo", cousin_gender="boy",
        aunt_kind="grandmother", butler_kind="housekeeper", butler_name="Mrs. Lin",
        trait_hero="brave", trait_cousin="careful",
    ),
    StoryParams(
        place="villa", liqueur="honey_liqueur", reveal="earned_sip",
        hero="Ava", gender="girl", cousin="Finn", cousin_gender="boy",
        aunt_kind="aunt", butler_kind="gardener", butler_name="Mr. Brook",
        trait_hero="bright", trait_cousin="thoughtful",
    ),
]


def explain_rejection(place: str, liqueur_id: str) -> str:
    if place in SETTINGS and "hallway" not in SETTINGS[place].affords:
        return (f"(No story: {SETTINGS[place].place} has no long hallway, so "
                f"the puddle and rule-list clues cannot be set.  Try "
                f"--place {', '.join(sorted(SETTINGS))}.)")
    return "(No story: the chosen place and liqueur do not satisfy the room constraints.)"


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A place is valid only when it affords every room the mystery needs:
% hallway (puddle + rule_list), kitchen (sweet_smell), pantry (recipe_book),
% locked_room (keyhole_glimpse), and a place to land the story (garden).
valid(Place, L) :- setting(Place),
                    affords(Place, hallway),
                    affords(Place, kitchen),
                    affords(Place, pantry),
                    affords(Place, locked_room),
                    affords(Place, garden),
                    liqueur(L).

% Gender is implicit (no constraint here), but we surface it through the
% heroine/hero naming layer for stories with both a girl and a boy.
valid_story(Place, L) :- valid(Place, L).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for r in sorted(s.affords):
            lines.append(asp.fact("affords", pid, r))
    for lid, l in LIQUEURS.items():
        lines.append(asp.fact("liqueur", lid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
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
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a mess, a compromise. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--liqueur", choices=LIQUEURS)
    ap.add_argument("--reveal", choices=REVEALS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--cousin")
    ap.add_argument("--cousin-gender", choices=["girl", "boy"])
    ap.add_argument("--aunt-kind", choices=AUNT_KINDS)
    ap.add_argument("--butler-kind", choices=BUTLER_KINDS)
    ap.add_argument("--butler-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in unspecified choices; raise StoryError on impossible combos."""
    if args.place and args.liqueur:
        if args.liqueur not in {lid for _, lid in valid_combos()
                                if _ == args.place}:
            raise StoryError(explain_rejection(args.place, args.liqueur))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.liqueur is None or c[1] == args.liqueur)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, liqueur_id = rng.choice(sorted(combos))
    reveal = args.reveal or rng.choice(sorted(REVEALS))
    gender = args.gender or rng.choice(["girl", "boy"])
    cousin_gender = args.cousin_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    if args.cousin:
        cousin = args.cousin
    else:
        if cousin_gender == gender and gender == "girl":
            cousin = rng.choice([n for n in GIRL_NAMES if n != hero])
        elif cousin_gender == gender and gender == "boy":
            cousin = rng.choice([n for n in BOY_NAMES if n != hero])
        else:
            cousin = rng.choice(GIRL_NAMES if cousin_gender == "girl" else BOY_NAMES)
    aunt_kind = args.aunt_kind or rng.choice(AUNT_KINDS)
    butler_kind = args.butler_kind or rng.choice(BUTLER_KINDS)
    butler_name = args.butler_name or {
        "butler": rng.choice(["Mr. Penny", "Mr. Hale", "Mr. Reed"]),
        "housekeeper": rng.choice(["Mrs. Lin", "Mrs. Brooke", "Mrs. West"]),
        "gardener": rng.choice(["Mr. Brook", "Mr. Vale", "Mr. Sage"]),
    }[butler_kind]
    trait_hero = rng.choice(TRAITS_HERO)
    trait_cousin = rng.choice(TRAITS_COUSIN)
    return StoryParams(
        place=place,
        liqueur=liqueur_id,
        reveal=reveal,
        hero=hero,
        gender=gender,
        cousin=cousin,
        cousin_gender=cousin_gender,
        aunt_kind=aunt_kind,
        butler_kind=butler_kind,
        butler_name=butler_name,
        trait_hero=trait_hero,
        trait_cousin=trait_cousin,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + Q&A sets."""
    liqueur = LIQUEURS[params.liqueur]
    reveal = REVEALS[params.reveal]
    # interpolate the liqueur name into the reveal text
    reveal = Reveal(
        id=reveal.id,
        opener=reveal.opener,
        confession=reveal.confession.replace("{LIQUEUR}", liqueur.name),
        payoff=reveal.payoff.replace("{LIQUEUR}", liqueur.name),
    )
    world = tell(
        SETTINGS[params.place], liqueur, reveal,
        hero_name=params.hero, hero_type=params.gender,
        cousin_name=params.cousin, cousin_type=params.cousin_gender,
        aunt_type=params.aunt_kind,
        butler_name=params.butler_name, butler_type=params.butler_kind,
        hero_traits=[params.trait_hero, "curious"],
        cousin_traits=[params.trait_cousin, "clever"],
    )
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, liqueur) combos:\n")
        for place, lid in triples:
            print(f"  {place:11} {lid}")
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
            header = f"### {p.hero} & {p.cousin}: {p.liqueur} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
