#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/security_inner_monologue_foreshadowing_misunderstanding_tall_tale.py
================================================================================================

A standalone storyworld about a child, a security guard, and a giant fair exhibit
that looks much stranger than it really is. The story uses:

- security
- inner monologue
- foreshadowing
- misunderstanding
- a tall-tale voice

The simulated world is small on purpose: a child notices one oversized clue near
a guarded fair tent, imagines something wildly wrong, and then learns the truth
from a calm grown-up. Different venues, exhibits, clues, and guesses are only
allowed when they make common-sense sense together.

Run it
------
    python storyworlds/worlds/gpt-5.4/security_inner_monologue_foreshadowing_misunderstanding_tall_tale.py
    python storyworlds/worlds/gpt-5.4/security_inner_monologue_foreshadowing_misunderstanding_tall_tale.py --venue fairground --exhibit pumpkin --clue thump --guess beast
    python storyworlds/worlds/gpt-5.4/security_inner_monologue_foreshadowing_misunderstanding_tall_tale.py --exhibit cheese --clue sweet_air
    python storyworlds/worlds/gpt-5.4/security_inner_monologue_foreshadowing_misunderstanding_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/security_inner_monologue_foreshadowing_misunderstanding_tall_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/security_inner_monologue_foreshadowing_misunderstanding_tall_tale.py --verify
"""

from __future__ import annotations

import argparse
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

TRAIT_BONUS = {
    "brave": 2,
    "curious": 1,
    "dreamy": 1,
    "cautious": 0,
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Venue:
    id: str
    place: str
    opening: str
    security_spot: str
    hosts: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Exhibit:
    id: str
    label: str
    phrase: str
    reveal: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    text: str
    thought: str
    requires: set[str] = field(default_factory=set)
    reveals: set[str] = field(default_factory=set)
    spook: int = 0
    tags: set[str] = field(default_factory=set)


@dataclass
class Guess:
    id: str
    label: str
    phrase: str
    boast: str
    requires: set[str] = field(default_factory=set)
    scary: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    venue: str
    exhibit: str
    clue: str
    guess: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


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


VENUES = {
    "fairground": Venue(
        id="fairground",
        place="the county fairground",
        opening="Banners snapped over the midway, and every board on every booth seemed to brag louder than the last.",
        security_spot="the blue-ribbon tent by the pumpkin scales",
        hosts={"pumpkin", "watermelon", "cheese"},
        tags={"fair"},
    ),
    "harvest_barn": Venue(
        id="harvest_barn",
        place="the harvest barn",
        opening="The rafters were so high they looked as if they had borrowed a piece of sky.",
        security_spot="the roped-off prize stall",
        hosts={"pumpkin", "watermelon"},
        tags={"barn"},
    ),
    "market_hall": Venue(
        id="market_hall",
        place="the old market hall",
        opening="The long hall smelled of wood polish and apples, and footsteps bounced around as if the floor were applauding.",
        security_spot="the champion table under the clock",
        hosts={"cheese"},
        tags={"hall"},
    ),
}

EXHIBITS = {
    "pumpkin": Exhibit(
        id="pumpkin",
        label="pumpkin",
        phrase="a pumpkin so big it looked ready to ask for its own zip code",
        reveal="the famous giant pumpkin that needed two wagons and three groans to get indoors",
        ending_image="the giant pumpkin sat under its ribbons like a sleepy orange hill",
        tags={"huge", "round", "thump", "sweet", "orange"},
    ),
    "watermelon": Exhibit(
        id="watermelon",
        label="watermelon",
        phrase="a watermelon broader than a washtub and striped like a green moon",
        reveal="the champion watermelon, cool and striped and harmless as a picnic",
        ending_image="the champion watermelon gleamed in the lamplight like a polished green moon",
        tags={"huge", "round", "thump", "sweet", "green"},
    ),
    "cheese": Exhibit(
        id="cheese",
        label="cheese wheel",
        phrase="a cheese wheel as round as a wagon wheel and almost as proud",
        reveal="the town's prize cheese wheel, waxed gold and grand enough to deserve its own little fence",
        ending_image="the golden cheese wheel rested on its stand like a small yellow sun",
        tags={"round", "thump", "gold", "savory"},
    ),
}

CLUES = {
    "thump": Clue(
        id="thump",
        text="From behind the tent came a thump so deep it made the paper cups tremble.",
        thought="If that thing takes one more step, thought {name}, it may shake the buttons right off my shirt.",
        requires={"thump"},
        reveals={"huge", "thump"},
        spook=2,
        tags={"sound"},
    ),
    "big_shadow": Clue(
        id="big_shadow",
        text="A shadow slid across the canvas, broad as a porch roof and twice as mysterious.",
        thought="That is no ordinary shadow, thought {name}. That is the kind of shadow that arrives before the rest of the trouble does.",
        requires={"huge"},
        reveals={"huge"},
        spook=1,
        tags={"shadow"},
    ),
    "round_bulge": Clue(
        id="round_bulge",
        text="The canvas bulged in one place, round and smooth, like the moon had forgotten how to stay in the sky.",
        thought="A round thing that size ought to have its own weather, thought {name}.",
        requires={"round"},
        reveals={"round", "huge"},
        spook=1,
        tags={"shape"},
    ),
    "sweet_air": Clue(
        id="sweet_air",
        text="Warm sweet air drifted from the tent, thick enough to make even the bees slow down and listen.",
        thought="Something mighty ripe is hiding in there, thought {name}, and it smells too grand to be ordinary.",
        requires={"sweet"},
        reveals={"sweet"},
        spook=0,
        tags={"smell"},
    ),
    "gold_glint": Clue(
        id="gold_glint",
        text="A gold glint winked through the flap as if someone had tied up a piece of sunset and told it to keep still.",
        thought="Anything shining like that is either treasure or trouble, thought {name}. Maybe both.",
        requires={"gold"},
        reveals={"gold", "round"},
        spook=1,
        tags={"shine"},
    ),
}

GUESSES = {
    "beast": Guess(
        id="beast",
        label="a hill-eating beast",
        phrase="a hill-eating beast with knees like fence posts",
        boast="For one dizzy second, {name} was sure a hill-eating beast was breathing in there.",
        requires={"huge", "thump"},
        scary=True,
        tags={"beast"},
    ),
    "moon": Guess(
        id="moon",
        label="a runaway moon",
        phrase="a runaway moon that had rolled down to earth and lost its manners",
        boast="In {name}'s mind, it became a runaway moon, round and enormous and plainly up to no good.",
        requires={"round"},
        scary=False,
        tags={"moon"},
    ),
    "pie_mountain": Guess(
        id="pie_mountain",
        label="a pie mountain",
        phrase="a pie mountain high enough to feed a parade and still leave crumbs for the mayor",
        boast="Then {name} imagined a pie mountain, because the air smelled much too delicious for anything small.",
        requires={"sweet"},
        scary=False,
        tags={"pie"},
    ),
    "treasure": Guess(
        id="treasure",
        label="a heap of treasure",
        phrase="a heap of treasure bright enough to make a pirate forget his own name",
        boast="The glimmer made {name} picture a heap of treasure guarded by more rules than a courthouse.",
        requires={"gold"},
        scary=False,
        tags={"treasure"},
    ),
    "giant": Guess(
        id="giant",
        label="a sleeping giant",
        phrase="a sleeping giant curled up small only by giant standards",
        boast="All at once, {name} decided it must be a sleeping giant trying very hard not to snore.",
        requires={"huge"},
        scary=True,
        tags={"giant"},
    ),
}

GIRL_NAMES = ["Mabel", "Lila", "Nora", "Sadie", "Clara", "Minnie", "Pearl", "Ivy"]
BOY_NAMES = ["Jasper", "Otis", "Eli", "Milo", "Benny", "Cal", "Theo", "Wade"]
TRAITS = ["brave", "curious", "dreamy", "cautious"]


CURATED = [
    StoryParams(
        venue="fairground",
        exhibit="pumpkin",
        clue="thump",
        guess="beast",
        name="Mabel",
        gender="girl",
        parent="father",
        trait="cautious",
        seed=1,
    ),
    StoryParams(
        venue="harvest_barn",
        exhibit="watermelon",
        clue="round_bulge",
        guess="moon",
        name="Otis",
        gender="boy",
        parent="mother",
        trait="dreamy",
        seed=2,
    ),
    StoryParams(
        venue="market_hall",
        exhibit="cheese",
        clue="gold_glint",
        guess="treasure",
        name="Clara",
        gender="girl",
        parent="father",
        trait="curious",
        seed=3,
    ),
    StoryParams(
        venue="fairground",
        exhibit="pumpkin",
        clue="sweet_air",
        guess="pie_mountain",
        name="Jasper",
        gender="boy",
        parent="mother",
        trait="brave",
        seed=4,
    ),
    StoryParams(
        venue="harvest_barn",
        exhibit="watermelon",
        clue="big_shadow",
        guess="giant",
        name="Pearl",
        gender="girl",
        parent="mother",
        trait="cautious",
        seed=5,
    ),
]


def exhibit_fits_venue(venue: Venue, exhibit: Exhibit) -> bool:
    return exhibit.id in venue.hosts


def clue_fits_exhibit(clue: Clue, exhibit: Exhibit) -> bool:
    return clue.requires.issubset(exhibit.tags)


def guess_fits_clue(guess: Guess, clue: Clue) -> bool:
    return guess.requires.issubset(clue.reveals)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for venue_id, venue in VENUES.items():
        for exhibit_id, exhibit in EXHIBITS.items():
            if not exhibit_fits_venue(venue, exhibit):
                continue
            for clue_id, clue in CLUES.items():
                if not clue_fits_exhibit(clue, exhibit):
                    continue
                for guess_id, guess in GUESSES.items():
                    if guess_fits_clue(guess, clue):
                        combos.append((venue_id, exhibit_id, clue_id, guess_id))
    return combos


def route_of(trait: str, clue: Clue) -> str:
    if clue.spook > TRAIT_BONUS[trait] + 1:
        return "peek"
    return "ask"


def explain_combo_rejection(venue: Venue, exhibit: Exhibit, clue: Clue, guess: Guess) -> str:
    if not exhibit_fits_venue(venue, exhibit):
        return (
            f"(No story: {venue.place} is not the place for {exhibit.phrase}. "
            f"The guarded exhibit has to belong where the story says it is.)"
        )
    if not clue_fits_exhibit(clue, exhibit):
        return (
            f"(No story: the clue '{clue.id}' does not fit {exhibit.label}. "
            f"The foreshadowing clue must come honestly from the hidden exhibit.)"
        )
    if not guess_fits_clue(guess, clue):
        return (
            f"(No story: the misunderstanding '{guess.label}' does not follow from the clue '{clue.id}'. "
            f"The child may imagine wildly, but the wild guess must grow out of what was noticed.)"
        )
    return "(No story: this combination is unreasonable.)"


def introduce(world: World, hero: Entity, parent: Entity, venue: Venue) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"One long afternoon, {hero.id} went to {venue.place} with {hero.pronoun('possessive')} "
        f"{parent.label_word}. {venue.opening}"
    )
    world.say(
        f"{hero.id} loved fairs and halls and barns that made ordinary things look bigger than life."
    )


def spot_security(world: World, hero: Entity, venue: Venue) -> None:
    world.get("guard").meters["watch"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"Near {venue.security_spot} stood a security guard in a neat blue jacket, "
        f"watching one closed flap as carefully as if it hid the last cookie on earth."
    )
    world.say(
        f"That alone was enough to make {hero.id}'s thoughts hop up on tiptoe."
    )


def foreshadow(world: World, hero: Entity, clue: Clue) -> None:
    hero.meters["noticed_clue"] += 1
    hero.memes["curiosity"] += 1
    hero.memes["fear"] += float(clue.spook)
    world.say(clue.text)
    world.say(clue.thought.format(name=hero.id))


def misunderstand(world: World, hero: Entity, guess: Guess) -> None:
    hero.memes["imagination"] += 1
    if guess.scary:
        hero.memes["fear"] += 1
    world.say(guess.boast.format(name=hero.id))
    world.say(
        f'"Why else would they need security?" {hero.id} whispered to {hero.pronoun("self") if False else hero.pronoun("object")}.'
    )


def decide(world: World, hero: Entity, route: str) -> None:
    world.facts["route"] = route
    if route == "peek":
        hero.meters["peeked"] += 1
        world.say(
            f"{hero.id} edged closer, one toe at a time, planning to peek first and ask questions later."
        )
    else:
        hero.meters["asked"] += 1
        hero.memes["bravery"] += 1
        world.say(
            f"{hero.id} swallowed once, squared {hero.pronoun('possessive')} shoulders, and decided that asking was better than creeping."
        )


def meet_guard(world: World, hero: Entity, parent: Entity, guess: Guess, route: str) -> None:
    guard = world.get("guard")
    guard.memes["calm"] += 1
    if route == "peek":
        hero.memes["alarm"] += 1
        world.say(
            f'Before {hero.pronoun()} could lift the flap, the guard turned and said, '
            f'"Easy there, little wanderer. No need to sneak."'
        )
    else:
        world.say(
            f'{hero.id} tugged {hero.pronoun("possessive")} {parent.label_word} closer and asked, '
            f'"Excuse me, is it {guess.label} in there?"'
        )
    if guess.scary:
        world.say(
            f"The guard blinked once, and then a smile spread across his face so fast it nearly needed its own pair of boots."
        )
    else:
        world.say(
            f"The guard tipped his cap and smiled, as if he had heard stranger guesses before breakfast."
        )


def reveal(world: World, hero: Entity, exhibit: Exhibit, route: str) -> None:
    guard = world.get("guard")
    hero.meters["learned_truth"] += 1
    hero.memes["fear"] = 0.0
    hero.memes["wonder"] += 2
    hero.memes["relief"] += 1
    hero.memes["trust"] += 1
    guard.memes["kindness"] += 1
    world.say(
        f'"Nothing so wild," he said. "We are guarding {exhibit.reveal}."'
    )
    if route == "peek":
        world.say(
            f"He lifted the flap just enough for {hero.id} to see inside."
        )
    else:
        world.say(
            f"Then, because kind answers are often the biggest ones, he opened the flap for a proper look."
        )
    world.say(
        f"There it was: {exhibit.phrase}."
    )


def resolve(world: World, hero: Entity, parent: Entity, exhibit: Exhibit, guess: Guess) -> None:
    parent.memes["amusement"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"{hero.id}'s face grew warm. {hero.pronoun().capitalize()} had not found {guess.phrase} at all."
    )
    world.say(
        f"Instead, {hero.pronoun()} laughed so hard that even {hero.pronoun('possessive')} {parent.label_word} had to laugh too."
    )
    world.say(
        f'Soon the misunderstanding was smaller than a peanut, and the truth was grander than the guess.'
    )
    world.say(
        f"When they walked on, {hero.id} kept looking back, where {exhibit.ending_image}, "
        f"and the guard kept watch with patient security over something wonderful and perfectly real."
    )


def tell(
    venue: Venue,
    exhibit: Exhibit,
    clue: Clue,
    guess: Guess,
    name: str,
    gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            role="hero",
            traits=[trait],
            label=name,
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    guard = world.add(
        Entity(
            id="Guard",
            kind="character",
            type="man",
            role="guard",
            label="the security guard",
        )
    )
    prize = world.add(
        Entity(
            id="Exhibit",
            kind="thing",
            type=exhibit.label,
            role="exhibit",
            label=exhibit.label,
            phrase=exhibit.phrase,
            tags=set(exhibit.tags),
        )
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        guard=guard,
        venue=venue,
        exhibit_cfg=exhibit,
        clue=clue,
        guess=guess,
        trait=trait,
        prize=prize,
    )

    introduce(world, hero, parent, venue)
    world.para()
    spot_security(world, hero, venue)
    foreshadow(world, hero, clue)
    misunderstand(world, hero, guess)
    decide(world, hero, route_of(trait, clue))
    world.para()
    meet_guard(world, hero, parent, guess, world.facts["route"])
    reveal(world, hero, exhibit, world.facts["route"])
    world.para()
    resolve(world, hero, parent, exhibit, guess)

    world.facts["mismatch"] = guess.label != exhibit.label
    world.facts["safe_end"] = hero.memes["fear"] < THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue"]
    guess = f["guess"]
    venue = f["venue"]
    exhibit = f["exhibit_cfg"]
    route = f["route"]
    return [
        'Write a tall-tale-style story for a 3-to-5-year-old that includes the word "security" and uses inner monologue, foreshadowing, and a misunderstanding.',
        f"Tell a playful tall tale where {hero.id} notices a strange clue at {venue.place}, imagines {guess.label}, and then learns the truth from a calm security guard.",
        f"Write a story where the foreshadowing clue is '{clue.id}', the hidden truth is {exhibit.label}, and the child chooses to {route} before the misunderstanding is cleared up.",
    ]


KNOWLEDGE = {
    "security": [
        (
            "What does security mean at a fair or market?",
            "Security means a grown-up is there to watch over people or important things and help keep them safe.",
        )
    ],
    "pumpkin": [
        (
            "What is a giant pumpkin?",
            "A giant pumpkin is just a pumpkin that has grown unusually big. People sometimes bring giant pumpkins to fairs and contests.",
        )
    ],
    "watermelon": [
        (
            "Why might a big watermelon be in a contest?",
            "Some fairs and festivals give prizes for the biggest or best fruit. A very large watermelon can be part of that kind of contest.",
        )
    ],
    "cheese": [
        (
            "What is a cheese wheel?",
            "A cheese wheel is a big round shape of cheese. It can be made large so it can age and be cut later.",
        )
    ],
    "shadow": [
        (
            "Why can a big shadow look scary?",
            "A shadow can hide details and make something seem stranger than it really is. Your eyes notice the size first, but not the whole truth.",
        )
    ],
    "sound": [
        (
            "Why can a thump make people imagine something big?",
            "Deep sounds often come from heavy things, so your mind may guess something huge before you see it clearly.",
        )
    ],
    "smell": [
        (
            "Can a smell give you a clue about what is nearby?",
            "Yes. A smell can tell you that food, flowers, or fruit is close even before you see it.",
        )
    ],
    "shine": [
        (
            "Why does something shiny sometimes look like treasure?",
            "Bright shiny things catch your eye quickly. If you do not know what they are yet, your imagination may guess treasure first.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone gets the wrong idea about what is going on. Later, they learn the real truth.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "security",
    "pumpkin",
    "watermelon",
    "cheese",
    "shadow",
    "sound",
    "smell",
    "shine",
    "misunderstanding",
]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    venue = f["venue"]
    clue = f["clue"]
    guess = f["guess"]
    exhibit = f["exhibit_cfg"]
    route = f["route"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who went to {venue.place} with {hero.pronoun('possessive')} {parent.label_word} and noticed a guarded tent. A calm security guard helps explain what is really there.",
        ),
        (
            "What first made the place feel mysterious?",
            f"The mystery began when {hero.id} saw security watching the closed flap and then noticed this clue: {clue.text} That foreshadowing clue made the hidden thing feel much bigger and stranger than usual.",
        ),
        (
            f"What did {hero.id} think was hidden there?",
            f"{hero.id} imagined {guess.phrase}. That was the misunderstanding, because the clue made {hero.pronoun('object')} guess wildly before {hero.pronoun()} knew the truth.",
        ),
        (
            f"Did {hero.id} peek first or ask first?",
            f"{hero.id} chose to {route} first. The choice matched how scary the clue felt and how bold {hero.pronoun()} was willing to be in that moment.",
        ),
        (
            "What was really behind the flap?",
            f"It was {exhibit.reveal}. The guard showed {hero.id} the exhibit and turned the misunderstanding into a laugh.",
        ),
        (
            f"Why was security there?",
            f"Security was there to guard the prize exhibit and keep people from bothering it. The guarded flap looked dramatic, but the reason was simple and safe.",
        ),
        (
            "How did the story end?",
            f"It ended with relief and wonder. {hero.id} walked away still looking back at the enormous exhibit, now knowing the truth was real and friendly instead of frightening.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    exhibit = f["exhibit_cfg"]
    clue = f["clue"]
    tags = {"security", "misunderstanding"}
    if exhibit.id in KNOWLEDGE:
        tags.add(exhibit.id)
    if "shadow" in clue.tags:
        tags.add("shadow")
    if "sound" in clue.tags:
        tags.add("sound")
    if "smell" in clue.tags:
        tags.add("smell")
    if "shine" in clue.tags:
        tags.add("shine")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  facts: route={world.facts.get('route')} mismatch={world.facts.get('mismatch')}")
    return "\n".join(lines)


ASP_RULES = r"""
% venue/exhibit compatibility
fits_venue(V, E) :- venue(V), exhibit(E), hosts(V, E).

% clue must honestly fit the hidden exhibit
fits_clue(C, E) :- clue(C), exhibit(E), not clue_missing(C, E).
clue_missing(C, E) :- clue_requires(C, T), not exhibit_tag(E, T).

% misunderstanding must grow from the clue
fits_guess(G, C) :- guess(G), clue(C), not guess_missing(G, C).
guess_missing(G, C) :- guess_requires(G, T), not clue_reveals(C, T).

valid(V, E, C, G) :- fits_venue(V, E), fits_clue(C, E), fits_guess(G, C).

route(peek) :- trait(T), clue(C), spook(C, S), trait_bonus(T, B), S > B + 1.
route(ask)  :- trait(T), clue(C), spook(C, S), trait_bonus(T, B), not S > B + 1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id, venue in VENUES.items():
        lines.append(asp.fact("venue", venue_id))
        for exhibit_id in sorted(venue.hosts):
            lines.append(asp.fact("hosts", venue_id, exhibit_id))
    for exhibit_id, exhibit in EXHIBITS.items():
        lines.append(asp.fact("exhibit", exhibit_id))
        for tag in sorted(exhibit.tags):
            lines.append(asp.fact("exhibit_tag", exhibit_id, tag))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("spook", clue_id, clue.spook))
        for tag in sorted(clue.requires):
            lines.append(asp.fact("clue_requires", clue_id, tag))
        for tag in sorted(clue.reveals):
            lines.append(asp.fact("clue_reveals", clue_id, tag))
    for guess_id, guess in GUESSES.items():
        lines.append(asp.fact("guess", guess_id))
        for tag in sorted(guess.requires):
            lines.append(asp.fact("guess_requires", guess_id, tag))
    for trait, bonus in TRAIT_BONUS.items():
        lines.append(asp.fact("trait_bonus", trait, bonus))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_route(trait: str, clue_id: str) -> str:
    import asp

    extra = "\n".join([asp.fact("trait", trait), asp.fact("clue", clue_id)])
    model = asp.one_model(asp_program(extra, "#show route/1."))
    atoms = asp.atoms(model, "route")
    return atoms[0][0] if atoms else "?"


def smoke_verify() -> int:
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            print("SMOKE FAIL: generated empty story.")
            return 1
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        dumped = buf.getvalue()
        if "security" not in sample.story.lower():
            print("SMOKE FAIL: story does not contain required word 'security'.")
            return 1
        if "### smoke" not in dumped or "--- world model state ---" not in dumped:
            print("SMOKE FAIL: emit() did not print expected sections.")
            return 1
        return 0
    except Exception as exc:  # pragma: no cover - defensive smoke test
        print(f"SMOKE FAIL: generation or emit crashed: {exc}")
        return 1


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    scenarios = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            scenarios.append(params)
        except StoryError:
            continue

    bad = []
    for params in scenarios:
        py_route = route_of(params.trait, CLUES[params.clue])
        clingo_route = asp_route(params.trait, params.clue)
        if py_route != clingo_route:
            bad.append((params.trait, params.clue, py_route, clingo_route))
    if not bad:
        print(f"OK: route model matches on {len(scenarios)} scenarios.")
    else:
        rc = 1
        print("MISMATCH in route model:")
        for item in bad[:10]:
            print(" ", item)

    rc |= smoke_verify()
    if rc == 0:
        print("OK: smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child misunderstands a guarded giant exhibit at a fair."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--exhibit", choices=EXHIBITS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--guess", choices=GUESSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.venue and args.exhibit and not exhibit_fits_venue(VENUES[args.venue], EXHIBITS[args.exhibit]):
        clue = CLUES[args.clue] if args.clue else next(iter(CLUES.values()))
        guess = GUESSES[args.guess] if args.guess else next(iter(GUESSES.values()))
        raise StoryError(explain_combo_rejection(VENUES[args.venue], EXHIBITS[args.exhibit], clue, guess))
    if args.exhibit and args.clue and not clue_fits_exhibit(CLUES[args.clue], EXHIBITS[args.exhibit]):
        venue = VENUES[args.venue] if args.venue else next(iter(VENUES.values()))
        guess = GUESSES[args.guess] if args.guess else next(iter(GUESSES.values()))
        raise StoryError(explain_combo_rejection(venue, EXHIBITS[args.exhibit], CLUES[args.clue], guess))
    if args.clue and args.guess and not guess_fits_clue(GUESSES[args.guess], CLUES[args.clue]):
        venue = VENUES[args.venue] if args.venue else next(iter(VENUES.values()))
        exhibit = EXHIBITS[args.exhibit] if args.exhibit else next(iter(EXHIBITS.values()))
        raise StoryError(explain_combo_rejection(venue, exhibit, CLUES[args.clue], GUESSES[args.guess]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.exhibit is None or combo[1] == args.exhibit)
        and (args.clue is None or combo[2] == args.clue)
        and (args.guess is None or combo[3] == args.guess)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue_id, exhibit_id, clue_id, guess_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        venue=venue_id,
        exhibit=exhibit_id,
        clue=clue_id,
        guess=guess_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        venue = VENUES[params.venue]
        exhibit = EXHIBITS[params.exhibit]
        clue = CLUES[params.clue]
        guess = GUESSES[params.guess]
    except KeyError as exc:
        raise StoryError(f"(No story: invalid parameter value {exc!s}.)") from exc

    if not exhibit_fits_venue(venue, exhibit):
        raise StoryError(explain_combo_rejection(venue, exhibit, clue, guess))
    if not clue_fits_exhibit(clue, exhibit):
        raise StoryError(explain_combo_rejection(venue, exhibit, clue, guess))
    if not guess_fits_clue(guess, clue):
        raise StoryError(explain_combo_rejection(venue, exhibit, clue, guess))
    if params.trait not in TRAIT_BONUS:
        raise StoryError(f"(No story: unknown trait '{params.trait}'.)")

    world = tell(
        venue=venue,
        exhibit=exhibit,
        clue=clue,
        guess=guess,
        name=params.name,
        gender=params.gender,
        parent_type=params.parent,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show route/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, exhibit, clue, guess) combos:\n")
        for venue_id, exhibit_id, clue_id, guess_id in combos:
            print(f"  {venue_id:12} {exhibit_id:10} {clue_id:12} {guess_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.exhibit} at {p.venue} ({p.clue} -> {p.guess})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
