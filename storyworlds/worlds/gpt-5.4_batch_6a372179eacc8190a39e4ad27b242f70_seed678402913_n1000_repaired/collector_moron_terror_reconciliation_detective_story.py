#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/collector_moron_terror_reconciliation_detective_story.py
===================================================================================

A standalone storyworld for a tiny child-facing detective story domain:
a young collector thinks a prized object has been stolen, blurts out the rude
word "moron" in a moment of terror, then follows a clue, solves the small
mystery, apologizes, and makes things right.

The world model keeps the story grounded in simulated state:
- physical meters: hidden, found, mess, tension
- emotional memes: pride, suspicion, hurt, terror, relief, apology, trust

Reasonableness gate:
- a clue must actually match the cause of the disappearance
- the venue must plausibly contain the hiding place implied by that cause

The feature is always reconciliation, but the route there is state-driven:
terror causes the rude outburst, the clue corrects the false suspicion, and the
apology unlocks forgiveness.

Run it
------
    python storyworlds/worlds/gpt-5.4/collector_moron_terror_reconciliation_detective_story.py
    python storyworlds/worlds/gpt-5.4/collector_moron_terror_reconciliation_detective_story.py --venue library --cause slid_under_crate --clue paper_corner
    python storyworlds/worlds/gpt-5.4/collector_moron_terror_reconciliation_detective_story.py --cause tucked_in_poster_tube --venue library
    python storyworlds/worlds/gpt-5.4/collector_moron_terror_reconciliation_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/collector_moron_terror_reconciliation_detective_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "librarian": "librarian"}.get(self.type, self.type)


@dataclass
class Venue:
    id: str
    label: str
    display: str
    detective_line: str
    keeper_type: str
    keeper_label: str
    spots: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Collectible:
    id: str
    label: str
    phrase: str
    case_label: str
    shine: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    spot: str
    found_at: str
    move_text: str
    proof_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    see_text: str
    points_to: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    apology_text: str
    ending_text: str
    tags: set[str] = field(default_factory=set)


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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_hidden_worries(world: World) -> list[str]:
    hero = world.entities.get("hero")
    item = world.entities.get("item")
    room = world.entities.get("room")
    if not hero or not item or not room:
        return []
    if item.meters["hidden"] < THRESHOLD:
        return []
    sig = ("hidden_worries",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["terror"] += 1
    hero.memes["suspicion"] += 1
    room.meters["tension"] += 1
    return ["__missing__"]


def _r_insult_hurts(world: World) -> list[str]:
    helper = world.entities.get("helper")
    if not helper or helper.memes["insulted"] < THRESHOLD:
        return []
    sig = ("insult_hurts",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["hurt"] += 1
    helper.memes["distance"] += 1
    return ["__hurt__"]


def _r_apology_reconciles(world: World) -> list[str]:
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    item = world.entities.get("item")
    if not hero or not helper or not item:
        return []
    if hero.memes["apology"] < THRESHOLD or item.meters["found"] < THRESHOLD:
        return []
    sig = ("apology_reconciles",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["forgiveness"] += 1
    helper.memes["trust"] += 1
    hero.memes["relief"] += 1
    hero.memes["trust"] += 1
    helper.memes["hurt"] = 0.0
    return ["__reconciled__"]


CAUSAL_RULES = [
    Rule(name="hidden_worries", tag="emotional", apply=_r_hidden_worries),
    Rule(name="insult_hurts", tag="social", apply=_r_insult_hurts),
    Rule(name="apology_reconciles", tag="social", apply=_r_apology_reconciles),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(x for x in lines if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


VENUES = {
    "library": Venue(
        id="library",
        label="the little library hall",
        display="a red display table by the window",
        detective_line="Every mystery leaves a trail if you look slowly.",
        keeper_type="librarian",
        keeper_label="the librarian",
        spots={"under_crate", "poster_tube"},
        tags={"library", "detective"},
    ),
    "museum": Venue(
        id="museum",
        label="the town history room",
        display="a blue exhibit stand under a glass lamp",
        detective_line="Good detectives notice what moved, not just what vanished.",
        keeper_type="mother",
        keeper_label="the museum guide",
        spots={"under_crate", "curtain_fold"},
        tags={"museum", "detective"},
    ),
    "school_fair": Venue(
        id="school_fair",
        label="the school fair corner",
        display="a folding table near the art wall",
        detective_line="A clue is a small thing that points to a big answer.",
        keeper_type="father",
        keeper_label="the fair helper",
        spots={"poster_tube", "curtain_fold"},
        tags={"school", "detective"},
    ),
}

COLLECTIBLES = {
    "stamps": Collectible(
        id="stamps",
        label="stamp album",
        phrase="a neat stamp album full of bright corners",
        case_label="album",
        shine="tiny pictures from faraway places",
        tags={"collector", "stamps"},
    ),
    "buttons": Collectible(
        id="buttons",
        label="button tray",
        phrase="a wooden tray of shiny buttons",
        case_label="tray",
        shine="round buttons that flashed like little moons",
        tags={"collector", "buttons"},
    ),
    "shells": Collectible(
        id="shells",
        label="shell box",
        phrase="a small shell box with careful labels",
        case_label="box",
        shine="striped shells that looked like sleepy smiles",
        tags={"collector", "shells"},
    ),
}

CAUSES = {
    "slid_under_crate": Cause(
        id="slid_under_crate",
        label="slid under a supply crate",
        spot="under_crate",
        found_at="under a wooden supply crate",
        move_text="A bump from a rolling cart had nudged the display, and the collectible slid out of sight.",
        proof_text="A paper corner peeked from the dust under the crate.",
        tags={"under", "accident"},
    ),
    "tucked_in_poster_tube": Cause(
        id="tucked_in_poster_tube",
        label="slipped into a poster tube",
        spot="poster_tube",
        found_at="inside a tall poster tube",
        move_text="When the display papers curled, the collectible slipped neatly into the open tube.",
        proof_text="A curl of matching paper was caught at the tube's mouth.",
        tags={"tube", "accident"},
    ),
    "caught_in_curtain_fold": Cause(
        id="caught_in_curtain_fold",
        label="caught in a curtain fold",
        spot="curtain_fold",
        found_at="inside the thick curtain by the display",
        move_text="A breeze from the open window lifted the edge and carried the collectible into the curtain fold.",
        proof_text="The curtain hem held a bright thread and a tiny flake from the display card.",
        tags={"curtain", "accident"},
    ),
}

CLUES = {
    "paper_corner": Clue(
        id="paper_corner",
        label="paper corner",
        see_text="Near the floor, a tiny paper corner stuck out where it should not have been.",
        points_to="slid_under_crate",
        tags={"paper", "floor"},
    ),
    "curled_label": Clue(
        id="curled_label",
        label="curled label",
        see_text="A label strip had curled itself into a little tunnel shape.",
        points_to="tucked_in_poster_tube",
        tags={"paper", "tube"},
    ),
    "bright_thread": Clue(
        id="bright_thread",
        label="bright thread",
        see_text="One bright thread trembled on the curtain edge as if it had caught something.",
        points_to="caught_in_curtain_fold",
        tags={"cloth", "window"},
    ),
}

REPAIRS = {
    "plain_apology": Repair(
        id="plain_apology",
        apology_text='"{helper}, I was wrong," {hero} said. "I was scared and called you a moron, and that was mean. I am sorry."',
        ending_text="They set the display straight together and the mystery table looked calm again.",
        tags={"apology"},
    ),
    "shared_fix": Repair(
        id="shared_fix",
        apology_text='"{hero} took a breath. "I was scared, and I called you a moron. That was rude and unfair. Will you help me fix the table while I say I am sorry?"',
        ending_text="Side by side, they fixed the display cards until the whole corner looked ready for visitors again.",
        tags={"apology", "repair"},
    ),
    "offer_badge": Repair(
        id="offer_badge",
        apology_text='"{hero} held out the detective badge. "You were helping, not taking anything. I called you a moron because I felt terror in my belly, and I am sorry. Will you be my detective partner again?"',
        ending_text="The badge changed hands and then came back, and both children smiled as they rebuilt the neat little exhibit.",
        tags={"apology", "badge"},
    ),
}


def valid_combo(venue_id: str, cause_id: str, clue_id: str) -> bool:
    if venue_id not in VENUES or cause_id not in CAUSES or clue_id not in CLUES:
        return False
    venue = VENUES[venue_id]
    cause = CAUSES[cause_id]
    clue = CLUES[clue_id]
    return cause.spot in venue.spots and clue.points_to == cause.id


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for venue_id in VENUES:
        for cause_id in CAUSES:
            for clue_id in CLUES:
                if valid_combo(venue_id, cause_id, clue_id):
                    combos.append((venue_id, cause_id, clue_id))
    return combos


@dataclass
class StoryParams:
    venue: str
    collectible: str
    cause: str
    clue: str
    repair: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    keeper_name: str
    keeper_type: str
    hero_trait: str
    helper_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        venue="library",
        collectible="stamps",
        cause="slid_under_crate",
        clue="paper_corner",
        repair="offer_badge",
        hero_name="Mia",
        hero_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        keeper_name="Mrs. Vale",
        keeper_type="librarian",
        hero_trait="careful",
        helper_trait="patient",
    ),
    StoryParams(
        venue="museum",
        collectible="buttons",
        cause="caught_in_curtain_fold",
        clue="bright_thread",
        repair="shared_fix",
        hero_name="Leo",
        hero_gender="boy",
        helper_name="Nora",
        helper_gender="girl",
        keeper_name="Guide Anna",
        keeper_type="mother",
        hero_trait="serious",
        helper_trait="gentle",
    ),
    StoryParams(
        venue="school_fair",
        collectible="shells",
        cause="tucked_in_poster_tube",
        clue="curled_label",
        repair="plain_apology",
        hero_name="Zoe",
        hero_gender="girl",
        helper_name="Max",
        helper_gender="boy",
        keeper_name="Mr. Reed",
        keeper_type="father",
        hero_trait="curious",
        helper_trait="steady",
    ),
]


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS_HERO = ["careful", "curious", "serious", "observant", "brave", "thoughtful"]
TRAITS_HELPER = ["patient", "gentle", "steady", "kind", "calm", "loyal"]


def introduce(world: World, hero: Entity, helper: Entity, keeper: Entity,
              venue: Venue, collectible: Collectible) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"On Saturday morning, {hero.id} carried {collectible.phrase} into {venue.label}. "
        f"{hero.pronoun().capitalize()} was a young collector and loved arranging {collectible.shine} on {venue.display}."
    )
    world.say(
        f"{helper.id} came along to help, and {keeper.id}, {venue.keeper_label}, pinned a paper detective badge to the table. "
        f'"{venue.detective_line}"'
    )


def setup_case(world: World, hero: Entity, helper: Entity, collectible: Collectible) -> None:
    world.say(
        f"Together the two children straightened every card and counted every piece in the {collectible.case_label}. "
        f'"Case of the Missing Treasure," {helper.id} whispered, just for fun.'
    )


def discover_missing(world: World, hero: Entity, item: Entity, collectible: Collectible) -> None:
    item.meters["hidden"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {hero.id} lifted the cover again, one special part of the {collectible.label} was gone. "
        f"The empty space looked much bigger than it really was."
    )
    if hero.memes["terror"] >= THRESHOLD:
        world.say(
            f"A small puff of terror fluttered in {hero.pronoun('possessive')} chest. "
            f"{hero.pronoun().capitalize()} felt sure the mystery had turned real."
        )


def false_accusation(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["suspicion"] += 1
    helper.memes["insulted"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} spun around and saw {helper.id} beside the table. "
        f'"Did you touch it? Don\'t just stand there, you moron!" {hero.pronoun()} burst out.'
    )
    if helper.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{helper.id} went very still. {helper.pronoun().capitalize()} had only been trying to help, and the rude word stung."
        )


def steady_adult(world: World, keeper: Entity, hero: Entity) -> None:
    world.say(
        f'{keeper.id} did not scold. "{hero.id}," {keeper.pronoun()} said softly, "good detectives do not blame first. They look first."'
    )


def inspect_clue(world: World, hero: Entity, helper: Entity, clue: Clue) -> None:
    hero.memes["focus"] += 1
    world.say(
        f"{hero.id} knelt beside the table and blinked hard until the scared feeling stopped buzzing so loudly. "
        f"{clue.see_text}"
    )
    world.say(
        f'"That is our clue," {helper.id} said quietly. {hero.id} nodded, because the clue pointed better than a guess.'
    )


def solve_case(world: World, hero: Entity, helper: Entity, item: Entity,
               cause: Cause, collectible: Collectible) -> None:
    item.meters["found"] += 1
    item.meters["hidden"] = 0.0
    hero.memes["terror"] = 0.0
    hero.memes["relief"] += 1
    world.say(
        f"They followed the clue and looked {cause.found_at}. {cause.move_text}"
    )
    world.say(
        f"There it was: the missing part of the {collectible.label}, safe at last. {cause.proof_text}"
    )
    world.facts["solved_by_clue"] = clue_text = cause.proof_text


def apologize(world: World, hero: Entity, helper: Entity, repair: Repair) -> None:
    hero.memes["apology"] += 1
    propagate(world, narrate=False)
    text = repair.apology_text.format(hero=hero.id, helper=helper.id)
    world.say(text)
    if helper.memes["forgiveness"] >= THRESHOLD:
        world.say(
            f'{helper.id} nodded. "I know you were scared," {helper.pronoun()} said. "Next time, let\'s solve it together."'
        )


def ending(world: World, hero: Entity, helper: Entity, repair: Repair, collectible: Collectible) -> None:
    world.say(repair.ending_text)
    world.say(
        f"When visitors came by, {hero.id} and {helper.id} stood shoulder to shoulder behind the {collectible.label}. "
        f"The case was closed, and their friendship looked neat again too."
    )


def tell(params: StoryParams) -> World:
    venue = VENUES[params.venue]
    collectible = COLLECTIBLES[params.collectible]
    cause = CAUSES[params.cause]
    clue = CLUES[params.clue]
    repair = REPAIRS[params.repair]

    world = World()
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_gender,
        role="hero",
        traits={params.hero_trait},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_gender,
        role="helper",
        traits={params.helper_trait},
    ))
    keeper = world.add(Entity(
        id=params.keeper_name,
        kind="character",
        type=params.keeper_type,
        role="keeper",
        label=venue.keeper_label,
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="collectible",
        label=collectible.label,
        phrase=collectible.phrase,
        tags=set(collectible.tags),
    ))
    world.add(Entity(id="room", type="room", label=venue.label, tags=set(venue.tags)))

    introduce(world, hero, helper, keeper, venue, collectible)
    setup_case(world, hero, helper, collectible)

    world.para()
    discover_missing(world, hero, item, collectible)
    false_accusation(world, hero, helper)
    steady_adult(world, keeper, hero)

    world.para()
    inspect_clue(world, hero, helper, clue)
    solve_case(world, hero, helper, item, cause, collectible)

    world.para()
    apologize(world, hero, helper, repair)
    ending(world, hero, helper, repair, collectible)

    world.facts.update(
        venue=venue,
        collectible=collectible,
        cause=cause,
        clue=clue,
        repair=repair,
        hero=hero,
        helper=helper,
        keeper=keeper,
        item=item,
        reconciliation=helper.memes["forgiveness"] >= THRESHOLD,
        insult_happened=helper.memes["insulted"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "collector": [
        (
            "What is a collector?",
            "A collector is a person who carefully gathers and keeps special things, like stamps, shells, or buttons. Collectors usually sort their things and try not to lose them."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and figures out what happened. Good detectives do not just guess; they check the small details."
        )
    ],
    "terror": [
        (
            "What does terror mean?",
            "Terror means a very big burst of fear. It can make your body feel jumpy and make it hard to think calmly."
        )
    ],
    "apology": [
        (
            "Why does an apology help after hurt feelings?",
            "An apology helps because it admits the hurt and shows you want to repair the friendship. Kind words and changed actions can help trust grow again."
        )
    ],
    "stamps": [
        (
            "Why do people collect stamps?",
            "People collect stamps because each one can have a different picture, place, or story on it. A stamp album lets them keep the stamps neat and safe."
        )
    ],
    "buttons": [
        (
            "Why might someone collect buttons?",
            "Buttons can have different colors, shapes, and shiny surfaces. A collection lets someone compare and sort them."
        )
    ],
    "shells": [
        (
            "Why do shells make a nice collection?",
            "Shells come in many sizes and patterns, so they are fun to sort and label. They can remind people of beaches and walks by the water."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    venue = f["venue"]
    collectible = f["collectible"]
    return [
        f'Write a short detective story for a 3-to-5-year-old that includes the words "collector", "moron", and "terror", and ends in reconciliation.',
        f"Tell a gentle mystery where {hero.id}, a young collector, thinks something from a {collectible.label} is missing in {venue.label}, wrongly snaps at {helper.id}, and then solves the case with a clue.",
        f"Write a child-facing case-of-the-missing-object story where fear causes a rude mistake, and the ending shows friendship repaired through an apology and shared work.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    keeper = f["keeper"]
    venue = f["venue"]
    collectible = f["collectible"]
    cause = f["cause"]
    clue = f["clue"]
    repair = f["repair"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young collector, {helper.id}, who came to help, and {keeper.id}, the calm grown-up at {venue.label}."
        ),
        (
            f"Why did {hero.id} feel scared?",
            f"{hero.id} saw that part of the {collectible.label} was missing and felt terror right away. The empty place made the problem seem like a real theft before {hero.pronoun()} had checked for clues."
        ),
        (
            f"Why did {hero.id} call {helper.id} a moron?",
            f"{hero.id} said that rude word because fear and suspicion rushed in before any careful thinking. {hero.pronoun().capitalize()} wrongly guessed that {helper.id} had done something, even though {helper.pronoun()} was only nearby and helping."
        ),
        (
            "What clue solved the mystery?",
            f"The clue was the {clue.label}. It mattered because it pointed toward the real place where the missing piece had gone."
        ),
        (
            "Where was the missing collectible really found?",
            f"It was found {cause.found_at}. The mystery was an accident, not a theft, because {cause.move_text.lower()}"
        ),
    ]
    if f.get("reconciliation"):
        qa.append(
            (
                f"How did {hero.id} and {helper.id} make peace?",
                f"{hero.id} apologized for saying 'moron' and explained that fear had made {hero.pronoun('object')} speak badly. Then they repaired the display together, which showed the apology was real and helped trust come back."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with reconciliation: the collectible was back, the mystery was solved, and the two children stood together behind the table again. {repair.ending_text}"
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"collector", "detective", "terror", "apology"}
    collectible = world.facts["collectible"]
    tags |= set(collectible.tags)
    out: list[tuple[str, str]] = []
    for key in ["collector", "detective", "terror", "apology", "stamps", "buttons", "shells"]:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:12} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(V, C, Cl) :- venue(V), cause(C), clue(Cl), spot_ok(V, S), cause_spot(C, S), clue_points(Cl, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id, venue in VENUES.items():
        lines.append(asp.fact("venue", venue_id))
        for spot in sorted(venue.spots):
            lines.append(asp.fact("spot_ok", venue_id, spot))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("cause_spot", cause_id, cause.spot))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_points", clue_id, clue.points_to))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def explain_rejection(venue_id: str, cause_id: str, clue_id: str) -> str:
    venue = VENUES.get(venue_id)
    cause = CAUSES.get(cause_id)
    clue = CLUES.get(clue_id)
    if venue and cause and cause.spot not in venue.spots:
        return (
            f"(No story: {venue.label} does not have the right hiding place for this accident. "
            f"The cause needs a {cause.spot.replace('_', ' ')}, but that venue would not support that clue trail.)"
        )
    if cause and clue and clue.points_to != cause.id:
        return (
            f"(No story: the clue '{clue_id}' points to {clue.points_to}, not to {cause.id}. "
            f"A detective story needs the clue to honestly lead to the true answer.)"
        )
    return "(No story: this mystery setup is not reasonable.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child collector, a false accusation, and a reconciled detective case."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--collectible", choices=COLLECTIBLES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible mystery setups derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run generation smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.venue and args.cause and args.clue and not valid_combo(args.venue, args.cause, args.clue):
        raise StoryError(explain_rejection(args.venue, args.cause, args.clue))

    combos = [
        combo for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.cause is None or combo[1] == args.cause)
        and (args.clue is None or combo[2] == args.clue)
    ]
    if not combos:
        venue_id = args.venue or next(iter(VENUES))
        cause_id = args.cause or next(iter(CAUSES))
        clue_id = args.clue or next(iter(CLUES))
        raise StoryError(explain_rejection(venue_id, cause_id, clue_id))

    venue_id, cause_id, clue_id = rng.choice(sorted(combos))
    collectible_id = args.collectible or rng.choice(sorted(COLLECTIBLES))
    repair_id = args.repair or rng.choice(sorted(REPAIRS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=hero_name)
    keeper_name = {
        "librarian": rng.choice(["Mrs. Vale", "Ms. Dawn", "Mrs. Hill"]),
        "mother": rng.choice(["Guide Anna", "Ms. June", "Miss Clara"]),
        "father": rng.choice(["Mr. Reed", "Mr. Hale", "Coach Ben"]),
    }[VENUES[venue_id].keeper_type]
    return StoryParams(
        venue=venue_id,
        collectible=collectible_id,
        cause=cause_id,
        clue=clue_id,
        repair=repair_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        keeper_name=keeper_name,
        keeper_type=VENUES[venue_id].keeper_type,
        hero_trait=rng.choice(TRAITS_HERO),
        helper_trait=rng.choice(TRAITS_HELPER),
    )


def generate(params: StoryParams) -> StorySample:
    if params.venue not in VENUES:
        raise StoryError(f"(Unknown venue: {params.venue})")
    if params.collectible not in COLLECTIBLES:
        raise StoryError(f"(Unknown collectible: {params.collectible})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    if not valid_combo(params.venue, params.cause, params.clue):
        raise StoryError(explain_rejection(params.venue, params.cause, params.clue))

    world = tell(params)
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


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    for seed in [0, 1, 2, 7, 13]:
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            sample = generate(params)
            if "moron" not in sample.story or "terror" not in sample.story or "collector" not in sample.story:
                raise StoryError("(Smoke test failed: required seed words missing from story.)")
        except Exception as err:  # pragma: no cover - verify path
            rc = 1
            print(f"RANDOM SCENARIO FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke tests succeeded.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, cause, clue) combos:\n")
        for venue_id, cause_id, clue_id in combos:
            print(f"  {venue_id:11} {cause_id:24} {clue_id}")
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
            header = f"### {p.hero_name} and {p.helper_name}: {p.collectible} at {p.venue} ({p.cause})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
