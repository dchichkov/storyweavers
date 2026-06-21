#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bat_quest_curiosity_twist_detective_story.py
=======================================================================

A standalone story world for a gentle child-facing detective tale with a quest,
curiosity, and a twist involving the word "bat".

Premise
-------
A child wants to find a missing baseball bat before a small game starts. The
child follows clues like a tiny detective. The twist is that a *real* bat is
hidden near the sports things, and that is what caused the mystery. A calm
grown-up helps the children make the place safe, lets the bat fly back outside,
and the missing baseball bat is found.

This world models:
- typed entities with physical meters and emotional memes
- a small clue-and-reveal simulation
- a reasonableness gate for safe bat-helping responses
- an inline ASP twin for valid combinations and outcomes
- state-grounded prose and Q&A

Run it
------
python storyworlds/worlds/gpt-5.4/bat_quest_curiosity_twist_detective_story.py
python storyworlds/worlds/gpt-5.4/bat_quest_curiosity_twist_detective_story.py --place garage --response open_window
python storyworlds/worlds/gpt-5.4/bat_quest_curiosity_twist_detective_story.py --response broom
python storyworlds/worlds/gpt-5.4/bat_quest_curiosity_twist_detective_story.py --all
python storyworlds/worlds/gpt-5.4/bat_quest_curiosity_twist_detective_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/bat_quest_curiosity_twist_detective_story.py --verify
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
# Target file lives under storyworlds/worlds/gpt-5.4/, so the package dir is
# three levels up.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


# ---------------------------------------------------------------------------
# Shared entities
# ---------------------------------------------------------------------------
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
    living: bool = False
    nocturnal: bool = False
    can_fly: bool = False
    # Unified simulation axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.living and self.type == "bat":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------
@dataclass
class Place:
    id: str
    label: str
    phrase: str
    sports_spot: str
    bat_spot: str
    echo: str
    exit_kind: str
    exit_phrase: str
    suitable_for_bat: bool = True
    clue_tags: set[str] = field(default_factory=set)


@dataclass
class Sport:
    id: str
    game: str
    item: str
    item_phrase: str
    item_plural: bool = False
    opening: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    text: str
    inference: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    quiet: bool
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    sport: Sport
    clue: Clue
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        return World(
            place=self.place,
            sport=self.sport,
            clue=self.clue,
            entities=copy.deepcopy(self.entities),
            fired=set(self.fired),
            paragraphs=[[]],
            facts=copy.deepcopy(self.facts),
        )


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_flutter(world: World) -> list[str]:
    out: list[str] = []
    real_bat = world.get("real_bat")
    room = world.get("room")
    if real_bat.meters["disturbed"] < THRESHOLD:
        return out
    sig = ("flutter",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["fluttering"] += 1
    for ent in world.entities.values():
        if ent.role in {"detective", "helper"}:
            ent.memes["surprise"] += 1
            ent.memes["curiosity"] += 1
    out.append("__flutter__")
    return out


def _r_escape(world: World) -> list[str]:
    out: list[str] = []
    real_bat = world.get("real_bat")
    room = world.get("room")
    if real_bat.meters["exit_open"] < THRESHOLD or real_bat.meters["calm"] < THRESHOLD:
        return out
    if real_bat.meters["escaped"] >= THRESHOLD:
        return out
    sig = ("escape",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    real_bat.meters["escaped"] += 1
    room.meters["fluttering"] = 0.0
    for ent in world.entities.values():
        if ent.role in {"detective", "helper"}:
            ent.memes["relief"] += 1
            ent.memes["kindness"] += 1
    out.append("__escape__")
    return out


CAUSAL_RULES = [
    Rule(name="flutter", tag="physical", apply=_r_flutter),
    Rule(name="escape", tag="physical", apply=_r_escape),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def habitat_match(place: Place) -> bool:
    return place.suitable_for_bat


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def clue_supported(place: Place, clue: Clue) -> bool:
    return bool(place.clue_tags & clue.tags)


def valid_combo(place_id: str, sport_id: str, clue_id: str) -> bool:
    place = PLACES[place_id]
    sport = SPORTS[sport_id]
    clue = CLUES[clue_id]
    return habitat_match(place) and clue_supported(place, clue) and bool(sport.tags)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for sport_id in SPORTS:
            for clue_id in CLUES:
                if valid_combo(place_id, sport_id, clue_id):
                    combos.append((place_id, sport_id, clue_id))
    return combos


def outcome_for(place_id: str, response_id: str) -> str:
    place = PLACES[place_id]
    response = RESPONSES[response_id]
    if not habitat_match(place):
        return "invalid"
    return "safe" if response.sense >= SENSE_MIN and response.power >= 2 else "scared"


def explain_place(place: Place) -> str:
    return (
        f"(No story: {place.label.capitalize()} is not a good place for this mystery. "
        f"The twist needs a real bat to have slipped into a sheltered spot, and this place "
        f"does not support that clue trail.)"
    )


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = " / ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). A gentle detective story should use a calm, "
        f"safe way to help the bat. Try: {better}.)"
    )


# ---------------------------------------------------------------------------
# Simulation verbs
# ---------------------------------------------------------------------------
def introduce(world: World, detective: Entity, helper: Entity, grownup: Entity) -> None:
    sport = world.sport
    world.say(
        f"On a bright afternoon, {detective.id} had one small but urgent case to solve. "
        f"{sport.opening} But the {sport.item} was gone."
    )
    world.say(
        f'"Detective {detective.id} is on the case," {detective.pronoun()} whispered, '
        f"pressing two fingers to {detective.pronoun('possessive')} chin. "
        f"{helper.id} came along as the clue-helper, while {grownup.label_word} promised to listen "
        f"if the mystery grew too big."
    )


def start_quest(world: World, detective: Entity) -> None:
    place = world.place
    sport = world.sport
    detective.memes["quest"] += 1
    detective.memes["curiosity"] += 1
    world.say(
        f"The search led straight to {place.phrase}, where they usually kept the {sport.item} "
        f"near {place.sports_spot}. {place.echo.capitalize()} made every tiny sound feel important."
    )


def find_clue(world: World, detective: Entity, helper: Entity) -> None:
    clue = world.clue
    detective.meters["clues"] += 1
    detective.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.facts["clue_text"] = clue.text
    world.say(
        f"Near the shelf, {detective.id} spotted the first clue: {clue.text}. "
        f'"That means {clue.inference}," {detective.pronoun()} said.'
    )


def follow_sound(world: World, detective: Entity, helper: Entity) -> None:
    clue = world.clue
    world.say(
        f"Then they heard {clue.sound}. The sound came from {world.place.bat_spot}, "
        f"not from the hook where the sports things usually hung."
    )
    helper.memes["wonder"] += 1
    detective.memes["wonder"] += 1


def reveal_twist(world: World, detective: Entity, helper: Entity) -> None:
    real_bat = world.get("real_bat")
    baseball_bat = world.get("play_bat")
    real_bat.meters["disturbed"] += 1
    baseball_bat.meters["misplaced"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{detective.id} lifted the bag flap just a little. Inside was not a sneaky thief at all. "
        f"A tiny real bat blinked back from the dim corner."
    )
    world.say(
        f'That was the twist. The little animal had fluttered in, bumped the sports bag, and nudged '
        f'the {baseball_bat.label} out of sight behind {world.place.sports_spot}.'
    )


def call_grownup(world: World, detective: Entity, grownup: Entity) -> None:
    detective.memes["good_sense"] += 1
    world.say(
        f"{detective.id} took one careful step back. "
        f'"This is a real-bat mystery," {detective.pronoun()} said. '
        f'"We need {grownup.label_word} now."'
    )


def help_bat(world: World, grownup: Entity, response: Response) -> None:
    real_bat = world.get("real_bat")
    real_bat.meters["exit_open"] += 1
    if response.quiet:
        real_bat.meters["calm"] += 1
    else:
        real_bat.meters["calm"] -= 1
    propagate(world, narrate=False)
    world.say(
        f"{grownup.label_word.capitalize()} came in quietly and {response.text}."
    )
    if real_bat.meters["escaped"] >= THRESHOLD:
        world.say(
            f"In one soft sweep of wings, the little bat found {world.place.exit_phrase} "
            f"and slipped back into the evening air."
        )
    else:
        world.say(
            f"But the little bat only whirled around the room, more frightened than before."
        )


def recover_bat(world: World, detective: Entity, helper: Entity) -> None:
    baseball_bat = world.get("play_bat")
    baseball_bat.meters["found"] += 1
    detective.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"When the fluttering had stopped, {helper.id} peeked behind {world.place.sports_spot} "
        f"and found the missing {baseball_bat.label} lying on the floor."
    )
    world.say(
        f'"Case closed," {detective.id} said, smiling at last. '
        f'The mystery had not been about a thief. It had been about making room for a lost wild visitor.'
    )


def ending_safe(world: World, detective: Entity, helper: Entity, grownup: Entity) -> None:
    sport = world.sport
    world.say(
        f"A little later, they carried the {sport.item} outside. "
        f"They still played {sport.game}, but first they looked up at the darkening sky and hoped "
        f"the tiny bat had found a quiet tree."
    )
    world.say(
        f"{detective.id} felt proud for solving the case kindly, and {helper.id} said the best detectives "
        f"notice clues and help creatures too."
    )


def ending_scared(world: World, detective: Entity, helper: Entity, grownup: Entity, response: Response) -> None:
    baseball_bat = world.get("play_bat")
    baseball_bat.meters["found"] += 1
    detective.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f"At last, {grownup.label_word} found the missing {baseball_bat.label}, but nobody felt like playing right away."
    )
    world.say(
        f"The mystery was solved, yet the room had turned too noisy and scary. "
        f"{detective.id} decided that a good detective should stay calm and let grown-ups help animals the gentle way."
    )
    world.facts["failed_response_text"] = response.fail


# ---------------------------------------------------------------------------
# Full screenplay
# ---------------------------------------------------------------------------
def tell(
    place: Place,
    sport: Sport,
    clue: Clue,
    response: Response,
    detective_name: str = "Nora",
    detective_type: str = "girl",
    helper_name: str = "Ben",
    helper_type: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World(place=place, sport=sport, clue=clue)

    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_type,
        role="detective",
        label=detective_name,
        phrase=detective_name,
        traits=["careful", "curious"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        role="helper",
        label=helper_name,
        phrase=helper_name,
        traits=["loyal", "observant"],
    ))
    grownup = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="grownup",
        label="the parent",
        phrase="the parent",
    ))
    room = world.add(Entity(
        id="room",
        type="place",
        label=place.label,
        phrase=place.phrase,
    ))
    play_bat = world.add(Entity(
        id="play_bat",
        type="sports_item",
        label=sport.item,
        phrase=sport.item_phrase,
        role="missing_item",
        tags=set(sport.tags),
    ))
    real_bat = world.add(Entity(
        id="real_bat",
        type="bat",
        label="bat",
        phrase="a tiny real bat",
        role="wild_visitor",
        living=True,
        nocturnal=True,
        can_fly=True,
        tags={"bat", "animal", "night"},
    ))

    introduce(world, detective, helper, grownup)
    start_quest(world, detective)

    world.para()
    find_clue(world, detective, helper)
    follow_sound(world, detective, helper)

    world.para()
    reveal_twist(world, detective, helper)
    call_grownup(world, detective, grownup)

    world.para()
    help_bat(world, grownup, response)
    recover_bat(world, detective, helper)

    world.para()
    if outcome_for(place.id, response.id) == "safe":
        ending_safe(world, detective, helper, grownup)
        outcome = "safe"
    else:
        ending_scared(world, detective, helper, grownup, response)
        outcome = "scared"

    world.facts.update(
        detective=detective,
        helper=helper,
        grownup=grownup,
        place=place,
        sport=sport,
        clue=clue,
        response=response,
        play_bat=play_bat,
        real_bat=real_bat,
        outcome=outcome,
        twist_revealed=real_bat.meters["disturbed"] >= THRESHOLD,
        escaped=real_bat.meters["escaped"] >= THRESHOLD,
        item_found=play_bat.meters["found"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "garage": Place(
        id="garage",
        label="garage",
        phrase="the cool garage",
        sports_spot="the workbench",
        bat_spot="the old sports bag under the workbench",
        echo="The garage",
        exit_kind="door",
        exit_phrase="the half-open garage door",
        suitable_for_bat=True,
        clue_tags={"dust", "flutter", "night"},
    ),
    "shed": Place(
        id="shed",
        label="shed",
        phrase="the little garden shed",
        sports_spot="the wooden shelf",
        bat_spot="the rakes and hanging bags by the back wall",
        echo="The shed",
        exit_kind="window",
        exit_phrase="the open shed window",
        suitable_for_bat=True,
        clue_tags={"dust", "scratch", "night"},
    ),
    "clubhouse": Place(
        id="clubhouse",
        label="clubhouse",
        phrase="the old backyard clubhouse",
        sports_spot="the corner trunk",
        bat_spot="the rafters above the trunk",
        echo="The clubhouse",
        exit_kind="window",
        exit_phrase="the open clubhouse window",
        suitable_for_bat=True,
        clue_tags={"flutter", "paper", "night"},
    ),
    "sandbox": Place(
        id="sandbox",
        label="sandbox",
        phrase="the sunny sandbox",
        sports_spot="the toy bucket",
        bat_spot="the edge of the sandbox",
        echo="The sandbox",
        exit_kind="gate",
        exit_phrase="the little yard gate",
        suitable_for_bat=False,
        clue_tags={"sand"},
    ),
}

SPORTS = {
    "ballgame": Sport(
        id="ballgame",
        game="a short backyard ball game",
        item="baseball bat",
        item_phrase="the smooth baseball bat",
        item_plural=False,
        opening="The cousins were getting ready for a short backyard ball game",
        tags={"bat", "sports"},
    ),
    "tee_ball": Sport(
        id="tee_ball",
        game="tee-ball in the yard",
        item="tee-ball bat",
        item_phrase="the light tee-ball bat",
        item_plural=False,
        opening="The children were almost ready for tee-ball in the yard",
        tags={"bat", "sports"},
    ),
    "costume_case": Sport(
        id="costume_case",
        game="their pretend detective parade",
        item="costume bat",
        item_phrase="the cardboard bat for a bat costume",
        item_plural=False,
        opening="The children were setting up their pretend detective parade",
        tags={"bat", "pretend"},
    ),
}

CLUES = {
    "dust_arc": Clue(
        id="dust_arc",
        text="a pale arc in the dust, as if something long had been bumped and dragged",
        inference="something moved in a hurry",
        sound="a small leathery flutter, then a soft tick against metal",
        tags={"dust", "flutter"},
    ),
    "paper_rustle": Clue(
        id="paper_rustle",
        text="a crinkled scorecard on the floor with one corner folded under a bag",
        inference="the bag had shifted on its own",
        sound="a papery rustle high above them",
        tags={"paper", "flutter"},
    ),
    "scratch_mark": Clue(
        id="scratch_mark",
        text="fine scratch marks on a shelf beside a wobbling glove",
        inference="something tiny had landed there",
        sound="a quick scratch and a hush from the dark corner",
        tags={"scratch", "night"},
    ),
    "sand_line": Clue(
        id="sand_line",
        text="a little line of sand leading away from a bucket",
        inference="someone carried the sports things to the sandbox",
        sound="only the wind moving through the grass",
        tags={"sand"},
    ),
}

RESPONSES = {
    "open_window": Response(
        id="open_window",
        sense=3,
        power=3,
        quiet=True,
        text="opened a wide way out, turned off the bright light, and waited very still",
        fail="opened a way out, but the room stayed too bright and busy",
        qa_text="opened a quiet exit and waited still until the bat flew out",
        tags={"bat_help", "window", "quiet"},
    ),
    "towel_guide": Response(
        id="towel_guide",
        sense=2,
        power=2,
        quiet=True,
        text="held up a towel like a soft wall and gently guided the bat toward the open air",
        fail="tried to guide the bat, but there was too much flapping and noise",
        qa_text="used a soft towel to guide the bat toward the open air",
        tags={"bat_help", "quiet"},
    ),
    "broom": Response(
        id="broom",
        sense=1,
        power=1,
        quiet=False,
        text="waved a broom in a rush",
        fail="waved a broom and made the frightened bat whirl faster",
        qa_text="waved a broom at the bat",
        tags={"loud", "chase"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli"]


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    sport: str
    clue: str
    response: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="garage",
        sport="ballgame",
        clue="dust_arc",
        response="open_window",
        detective_name="Nora",
        detective_type="girl",
        helper_name="Ben",
        helper_type="boy",
        parent="mother",
    ),
    StoryParams(
        place="shed",
        sport="tee_ball",
        clue="scratch_mark",
        response="towel_guide",
        detective_name="Max",
        detective_type="boy",
        helper_name="Lucy",
        helper_type="girl",
        parent="father",
    ),
    StoryParams(
        place="clubhouse",
        sport="costume_case",
        clue="paper_rustle",
        response="open_window",
        detective_name="Ava",
        detective_type="girl",
        helper_name="Finn",
        helper_type="boy",
        parent="mother",
    ),
    StoryParams(
        place="garage",
        sport="ballgame",
        clue="dust_arc",
        response="broom",
        detective_name="Leo",
        detective_type="boy",
        helper_name="Mia",
        helper_type="girl",
        parent="father",
    ),
]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "bat": [
        (
            "What is a bat?",
            "A bat is a small flying mammal. Many bats sleep in sheltered places during the day and come out at night."
        )
    ],
    "animal": [
        (
            "Why should people be calm around a wild animal indoors?",
            "A wild animal is usually scared, not naughty. Staying calm gives it a better chance to find a safe way out."
        )
    ],
    "window": [
        (
            "Why can an open window or door help a bat get outside?",
            "It gives the bat a clear path back to open air. If the room is calm, the bat can follow that path and leave."
        )
    ],
    "quiet": [
        (
            "Why does quiet help with a frightened animal?",
            "Loud waving and chasing can make an animal more scared. Quiet waiting helps it settle and move safely."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective notices clues, asks what they mean, and puts small facts together to solve a mystery."
        )
    ],
    "sports": [
        (
            "What is a baseball bat used for?",
            "A baseball bat is used to hit a ball in a ball game. It is sports gear, not something to swing around carelessly indoors."
        )
    ],
}

KNOWLEDGE_ORDER = ["detective", "bat", "animal", "window", "quiet", "sports"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    clue = f["clue"]
    sport = f["sport"]
    place = f["place"]
    return [
        'Write a short detective story for a 3-to-5-year-old that includes the word "bat" and uses a quest, curiosity, and a twist.',
        f"Tell a gentle mystery where {detective.id} hunts for a missing {sport.item} in {place.phrase}, follows {clue.text}, and discovers a surprising twist.",
        f"Write a child-facing detective tale where clues lead to a real bat, the mystery is solved kindly, and the ending shows what the detective learned.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    grownup = f["grownup"]
    place = f["place"]
    sport = f["sport"]
    clue = f["clue"]
    response = f["response"]
    real_bat = f["real_bat"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a tiny detective, and {helper.id}, the clue-helper. They are trying to solve the mystery of a missing {sport.item}."
        ),
        (
            f"What was the quest in the story?",
            f"The quest was to find the missing {sport.item} before {sport.game}. That goal is what led the children into {place.phrase} to look for clues."
        ),
        (
            f"What clue did {detective.id} find first?",
            f"{detective.id} found {clue.text}. {detective.pronoun().capitalize()} used that clue to decide that something had moved near the sports things."
        ),
        (
            "What was the twist?",
            f"The twist was that the mystery was not about a thief at all. A real bat had fluttered into the place, bumped the bag, and knocked the {sport.item} out of sight."
        ),
    ]
    if f["escaped"]:
        qa.append((
            f"How did {grownup.label_word} help the bat?",
            f"{grownup.label_word.capitalize()} {response.qa_text}. That calm method let the frightened bat find {place.exit_phrase} and leave safely."
        ))
        qa.append((
            f"How was the missing {sport.item} found?",
            f"After the fluttering stopped, {helper.id} looked behind {place.sports_spot} and found it. The bat had been hidden there because the real bat had jostled the bag."
        ))
        qa.append((
            f"What did {detective.id} learn at the end?",
            f"{detective.id} learned that good detectives do more than solve puzzles. They stay calm, notice the real cause, and help living creatures kindly."
        ))
    else:
        qa.append((
            f"Did the first response help the bat calmly?",
            f"No. The room became more frightening instead of calmer. That showed the children that loud chasing is not a good way to help a wild animal."
        ))
        qa.append((
            f"What did {detective.id} learn at the end?",
            f"{detective.id} learned that solving a mystery is not the same as rushing at it. A good detective lets grown-ups help animals in the gentle way."
        ))
    if real_bat.meters["disturbed"] >= THRESHOLD:
        qa.append((
            "Why were the children curious instead of just scared?",
            f"They had already found clues and wanted to understand what made the strange sounds. Their curiosity helped them notice that the mystery had a real cause, not a pretend one."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"detective", "bat", "animal", "sports"}
    tags |= set(f["response"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        if ent.living:
            flags.append("living")
        if ent.nocturnal:
            flags.append("nocturnal")
        if ent.can_fly:
            flags.append("can_fly")
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% --- base reasonableness gate ----------------------------------------------
valid(Place, Sport, Clue) :- place(Place), sport(Sport), clue(Clue),
                             suitable_for_bat(Place),
                             clue_tagged(Clue, Tag), place_supports(Place, Tag).

sensible(Response) :- response(Response), sense(Response, S), sense_min(M), S >= M.

% --- outcome model ----------------------------------------------------------
outcome(Place, Response, safe) :- suitable_for_bat(Place), sensible(Response), power(Response, P), P >= 2.
outcome(Place, Response, scared) :- suitable_for_bat(Place), response(Response),
                                    not outcome(Place, Response, safe).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.suitable_for_bat:
            lines.append(asp.fact("suitable_for_bat", pid))
        for tag in sorted(place.clue_tags):
            lines.append(asp.fact("place_supports", pid, tag))
    for sid in SPORTS:
        lines.append(asp.fact("sport", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for tag in sorted(clue.tags):
            lines.append(asp.fact("clue_tagged", cid, tag))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(place_id: str, response_id: str) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_place", place_id),
        asp.fact("chosen_response", response_id),
        f"chosen_outcome(O) :- outcome({place_id}, {response_id}, O).",
    ])
    model = asp.one_model(asp_program(extra, "#show chosen_outcome/1."))
    atoms = asp.atoms(model, "chosen_outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            continue

    mismatches = []
    for params in cases:
        py_out = outcome_for(params.place, params.response)
        asp_out = asp_outcome(params.place, params.response)
        if py_out != asp_out:
            mismatches.append((params.place, params.response, py_out, asp_out))
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print("MISMATCH in outcomes:")
        for item in mismatches[:10]:
            print(" ", item)

    # smoke test ordinary generation
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"VERIFY smoke test failed: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle detective story world about a missing bat, curiosity, and a twist."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sport", choices=SPORTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--detective-name")
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and not habitat_match(PLACES[args.place]):
        raise StoryError(explain_place(PLACES[args.place]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.place and args.clue and not clue_supported(PLACES[args.place], CLUES[args.clue]):
        raise StoryError("(No story: that clue does not fit the chosen place well enough for the detective trail.)")

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.sport is None or combo[1] == args.sport)
        and (args.clue is None or combo[2] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, sport, clue = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))

    detective_name, detective_type = _pick_name(rng)
    if args.detective_name:
        detective_name = args.detective_name
    helper_name, helper_type = _pick_name(rng, avoid=detective_name)
    if args.helper_name:
        helper_name = args.helper_name
        if helper_name in GIRL_NAMES:
            helper_type = "girl"
        elif helper_name in BOY_NAMES:
            helper_type = "boy"

    parent = args.parent or rng.choice(["mother", "father"])

    return StoryParams(
        place=place,
        sport=sport,
        clue=clue,
        response=response,
        detective_name=detective_name,
        detective_type=detective_type,
        helper_name=helper_name,
        helper_type=helper_type,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.sport not in SPORTS:
        raise StoryError(f"(No story: unknown sport '{params.sport}'.)")
    if params.clue not in CLUES:
        raise StoryError(f"(No story: unknown clue '{params.clue}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(No story: unknown response '{params.response}'.)")
    if not valid_combo(params.place, params.sport, params.clue):
        raise StoryError("(No story: these detective details do not make a reasonable mystery together.)")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        place=PLACES[params.place],
        sport=SPORTS[params.sport],
        clue=CLUES[params.clue],
        response=RESPONSES[params.response],
        detective_name=params.detective_name,
        detective_type=params.detective_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, sport, clue) combos:\n")
        for place, sport, clue in combos:
            print(f"  {place:10} {sport:12} {clue}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name} and {p.helper_name}: {p.place}, {p.sport}, {p.response} ({outcome_for(p.place, p.response)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
