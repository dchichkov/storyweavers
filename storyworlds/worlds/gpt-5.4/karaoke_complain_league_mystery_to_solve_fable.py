#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/karaoke_complain_league_mystery_to_solve_fable.py
=============================================================================

A standalone story world for a small fable-like domain built from the seed
words "karaoke", "complain", and "league", with a "Mystery to Solve" feature.

Premise
-------
In a little animal karaoke league, singing cannot begin because an important
music object has gone missing. One animal starts to complain, but another stops
guessing and follows clues. The mystery has a sensible, concrete cause, the
missing object is found, and the league learns that helping solves more than
grumbling.

Why this world exists
---------------------
This script models a tiny causal domain rather than swapping nouns into one
paragraph. Typed entities carry physical meters and emotional memes. A simple
reasonableness gate ensures the chosen venue, missing object, and cause fit
together: wind can carry paper, a magpie borrows shiny things, and a frog only
mistakes floating things near water. The story is then rendered from the world
state in a child-facing fable style.

Run it
------
    python storyworlds/worlds/gpt-5.4/karaoke_complain_league_mystery_to_solve_fable.py
    python storyworlds/worlds/gpt-5.4/karaoke_complain_league_mystery_to_solve_fable.py --venue pond --item songbook --cause wind
    python storyworlds/worlds/gpt-5.4/karaoke_complain_league_mystery_to_solve_fable.py --item bell --cause wind
    python storyworlds/worlds/gpt-5.4/karaoke_complain_league_mystery_to_solve_fable.py --all
    python storyworlds/worlds/gpt-5.4/karaoke_complain_league_mystery_to_solve_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/karaoke_complain_league_mystery_to_solve_fable.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root or from this nested subdirectory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    movable: bool = False
    shiny: bool = False
    paper: bool = False
    floats: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Venue:
    id: str
    label: str
    stage: str
    edge: str
    crowd_image: str
    has_water: bool = False
    windy: bool = False
    shiny_spots: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    use_line: str
    clue_mark: str
    movable: bool = True
    shiny: bool = False
    paper: bool = False
    floats: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    culprit_label: str
    style: str
    requires_water: bool = False
    requires_wind: bool = False
    requires_shiny: bool = False
    requires_paper: bool = False
    requires_float: bool = False
    clue_text: str = ""
    found_place: str = ""
    fix_line: str = ""
    lesson_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Seeker:
    id: str
    phrase: str
    method: str
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


def _r_stall_show(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("stall_show", "item")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    stage = world.get("stage")
    stage.meters["stalled"] += 1
    for ent in list(world.entities.values()):
        if ent.kind == "character" and ent.role in {"complainer", "detective", "leader"}:
            ent.memes["worry"] += 1
    return ["__stalled__"]


def _r_complaint_spreads(world: World) -> list[str]:
    complainer = world.get("complainer")
    if complainer.memes["complain"] < THRESHOLD:
        return []
    sig = ("complaint_spreads", "complainer")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crowd = world.get("crowd")
    crowd.memes["gloom"] += 1
    world.get("detective").memes["resolve"] += 1
    return []


def _r_clue_confirms(world: World) -> list[str]:
    if world.get("trail").meters["followed"] < THRESHOLD:
        return []
    sig = ("clue_confirms", "trail")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("detective").memes["certainty"] += 1
    return []


CAUSAL_RULES = [
    Rule("stall_show", "physical", _r_stall_show),
    Rule("complaint_spreads", "social", _r_complaint_spreads),
    Rule("clue_confirms", "mental", _r_clue_confirms),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def cause_fits(venue: Venue, item: MissingItem, cause: Cause) -> bool:
    if not item.movable:
        return False
    if cause.requires_water and not venue.has_water:
        return False
    if cause.requires_wind and not venue.windy:
        return False
    if cause.requires_shiny and not item.shiny:
        return False
    if cause.requires_paper and not item.paper:
        return False
    if cause.requires_float and not item.floats:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for venue_id, venue in VENUES.items():
        for item_id, item in ITEMS.items():
            for cause_id, cause in CAUSES.items():
                if cause_fits(venue, item, cause):
                    out.append((venue_id, item_id, cause_id))
    return out


def predict_recoverability(world: World, cause: Cause) -> dict:
    sim = world.copy()
    sim.get("item").meters["missing"] += 1
    propagate(sim, narrate=False)
    can_trace = bool(cause.clue_text and cause.found_place)
    return {
        "show_stalled": sim.get("stage").meters["stalled"] >= THRESHOLD,
        "can_trace": can_trace,
    }


def opening(world: World, venue: Venue, leader: Entity, complainer: Entity, detective: Entity) -> None:
    world.say(
        f"In {venue.label}, the Little Song League gathered for its evening karaoke. "
        f"{venue.crowd_image} around {venue.stage}."
    )
    world.say(
        f"{leader.id}, the league leader, smiled at {complainer.id} and {detective.id}. "
        f"Everyone was ready to sing as soon as the first tune began."
    )


def discover_missing(world: World, item: MissingItem, leader: Entity) -> None:
    world.get("item").meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {leader.id} reached for {item.phrase}, it was gone. "
        f"Without it, {item.use_line}, and the karaoke league fell silent."
    )


def complain(world: World, complainer: Entity) -> None:
    complainer.memes["complain"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Oh, this is always the way," {complainer.id} began to complain. '
        f'"Now no one will sing, and the whole league will have a gloomy night."'
    )


def choose_search(world: World, detective: Entity, seeker: Seeker, cause: Cause) -> None:
    detective.memes["resolve"] += 1
    pred = predict_recoverability(world, cause)
    world.facts["predicted_stall"] = pred["show_stalled"]
    world.facts["predicted_trace"] = pred["can_trace"]
    world.say(
        f'But {detective.id}, {seeker.phrase}, lifted {detective.pronoun("possessive")} chin. '
        f'"Complaining does not make clues," {detective.pronoun()} said. '
        f'"I will {seeker.method}."'
    )


def inspect_clue(world: World, detective: Entity, cause: Cause, item: MissingItem) -> None:
    world.get("trail").meters["followed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Soon {detective.id} found a sign: {cause.clue_text} "
        f"It matched the sort of mark that {item.label} would leave behind."
    )


def solve_mystery(world: World, detective: Entity, cause: Cause, item: MissingItem) -> None:
    world.get("item").meters["missing"] = 0.0
    world.get("item").meters["found"] += 1
    world.get("stage").meters["stalled"] = 0.0
    detective.memes["pride"] += 1
    world.get("complainer").memes["shame"] += 1
    world.say(
        f"Following the clue, {detective.id} came to {cause.found_place}. "
        f"There was {item.phrase}, and beside it was {cause.culprit_label}."
    )
    world.say(cause.fix_line.format(item=item.label))


def return_and_sing(world: World, venue: Venue, leader: Entity, complainer: Entity, detective: Entity, item: MissingItem) -> None:
    leader.memes["relief"] += 1
    complainer.memes["relief"] += 1
    complainer.memes["kindness"] += 1
    detective.memes["joy"] += 1
    world.say(
        f"They carried {item.phrase} back to {venue.stage}. Soon the karaoke league was bright again, "
        f"and even the shy singers tapped their feet."
    )
    world.say(
        f'{complainer.id} lowered {complainer.pronoun("possessive")} voice. '
        f'"I spent my breath on complaint when I should have spent it on help," '
        f'{complainer.pronoun()} said.'
    )
    world.say(
        f'{leader.id} rang the start, and {detective.id} sang the first song so cheerfully '
        f"that the whole league joined in."
    )


def moral(world: World, cause: Cause) -> None:
    world.say(
        f"So the little league learned {cause.lesson_line} "
        f"In a mystery, a patient eye is worth more than a noisy grumble."
    )


def tell(venue: Venue, item_cfg: MissingItem, cause: Cause, seeker: Seeker,
         leader_name: str = "Tortoise", complainer_name: str = "Goat",
         detective_name: str = "Wren") -> World:
    world = World()
    leader = world.add(Entity(id=leader_name, kind="character", type="animal", role="leader", label=leader_name))
    complainer = world.add(Entity(id=complainer_name, kind="character", type="animal", role="complainer", label=complainer_name))
    detective = world.add(Entity(id=detective_name, kind="character", type="animal", role="detective", label=detective_name))
    world.add(Entity(id="crowd", kind="thing", type="group", label="the crowd"))
    world.add(Entity(id="stage", kind="thing", type="stage", label=venue.stage))
    world.add(Entity(
        id="item", kind="thing", type="item", label=item_cfg.label, movable=item_cfg.movable,
        shiny=item_cfg.shiny, paper=item_cfg.paper, floats=item_cfg.floats
    ))
    world.add(Entity(id="trail", kind="thing", type="clue", label="the clue trail"))

    opening(world, venue, leader, complainer, detective)
    world.para()
    discover_missing(world, item_cfg, leader)
    complain(world, complainer)
    choose_search(world, detective, seeker, cause)
    world.para()
    inspect_clue(world, detective, cause, item_cfg)
    solve_mystery(world, detective, cause, item_cfg)
    world.para()
    return_and_sing(world, venue, leader, complainer, detective, item_cfg)
    moral(world, cause)

    world.facts.update(
        venue=venue,
        item_cfg=item_cfg,
        cause=cause,
        seeker=seeker,
        leader=leader,
        complainer=complainer,
        detective=detective,
        item=world.get("item"),
        solved=world.get("item").meters["found"] >= THRESHOLD,
        stalled=world.get("stage").meters["stalled"] >= THRESHOLD,
    )
    return world


VENUES = {
    "pond": Venue(
        "pond", "a willow-ringed pond", "the flat stone stage by the pond",
        "the soft reeds at the edge", "Fireflies bobbed like tiny lanterns",
        has_water=True, windy=False, shiny_spots=False, tags={"pond", "water"}
    ),
    "hill": Venue(
        "hill", "a breezy hilltop", "the smooth stump stage on the hill",
        "the tall grass below the stage", "Crickets chirped while the moon peeped over the slope",
        has_water=False, windy=True, shiny_spots=False, tags={"hill", "wind"}
    ),
    "market": Venue(
        "market", "the moonlit market square", "the little crate stage by the fig stall",
        "the basket stack behind the lantern post", "Lantern light blinked on coins and bottle tops",
        has_water=False, windy=False, shiny_spots=True, tags={"market", "shiny"}
    ),
}

ITEMS = {
    "songbook": MissingItem(
        "songbook", "songbook", "the league songbook", "no one knew which song should begin",
        "a torn bit of page caught on a twig", movable=True, paper=True, floats=False,
        tags={"songbook", "paper", "karaoke"}
    ),
    "bell": MissingItem(
        "bell", "bell", "the brass start bell", "the singers would not know whose turn came first",
        "a bright scrape in the dust", movable=True, shiny=True, floats=False,
        tags={"bell", "shiny", "karaoke"}
    ),
    "shell_mic": MissingItem(
        "shell_mic", "shell microphone", "the echoing shell microphone", "small voices sounded too timid to reach the back row",
        "a curling trail in the damp mud", movable=True, shiny=False, paper=False, floats=True,
        tags={"shell", "karaoke"}
    ),
}

CAUSES = {
    "wind": Cause(
        "wind", "the evening wind", "nature",
        requires_wind=True, requires_paper=True,
        clue_text="a fluttering page corner trembled in the grass",
        found_place="the tall grass below the stage, where the pages had skidded together",
        fix_line="The wind had whisked the {item} away, but not out of reach. Wren pressed it flat and tucked it safely under a pebble.",
        lesson_line="that the wind may scatter pages, but fretful noise scatters good sense first.",
        tags={"wind", "paper"}
    ),
    "magpie": Cause(
        "magpie", "a magpie with a guilty tilt to its head", "animal",
        requires_shiny=True,
        clue_text="one black feather lay beside a little glittering scratch",
        found_place="the basket stack behind the lantern post, inside a nest of stolen sparkle",
        fix_line="The magpie had borrowed the {item} because it gleamed. Wren traded it for a polished button, and the bird was content.",
        lesson_line="that a borrowed glitter can be won back with calm words faster than with sour ones.",
        tags={"magpie", "shiny"}
    ),
    "frog": Cause(
        "frog", "a puzzled frog", "animal",
        requires_water=True, requires_float=True,
        clue_text="small wet hops led from the stage toward the reeds",
        found_place="the soft reeds at the edge, half tucked beside a lily pad",
        fix_line="The frog had nudged the {item} into the reeds, thinking it was a floating toy. Wren lifted it gently, and the frog blinked in surprise.",
        lesson_line="that near water, hasty blame sinks while careful looking stays afloat.",
        tags={"frog", "water"}
    ),
}

SEEKERS = {
    "listener": Seeker("listener", "the smallest and steadiest listener in the league", "follow the quiet signs instead of the loud guesses", tags={"listen"}),
    "tracker": Seeker("tracker", "a neat-eyed tracker of little trails", "trace every mark from the stage to its end", tags={"track"}),
    "thinker": Seeker("thinker", "a patient little thinker", "ask what sort of thing could truly have carried the object away", tags={"think"}),
}

LEADER_NAMES = ["Tortoise", "Badger", "Mole", "Otter"]
COMPLAINER_NAMES = ["Goat", "Crow", "Duck", "Marmot"]
DETECTIVE_NAMES = ["Wren", "Mouse", "Robin", "Hedgehog"]


@dataclass
class StoryParams:
    venue: str
    item: str
    cause: str
    seeker: str
    leader: str
    complainer: str
    detective: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "karaoke": [(
        "What is karaoke?",
        "Karaoke is when people sing songs while taking turns, often with words or music to help them. It is a fun way to sing together."
    )],
    "league": [(
        "What is a league?",
        "A league is a group that joins together for the same activity. In a little singing league, friends meet to practice and take turns."
    )],
    "complain": [(
        "What does it mean to complain?",
        "To complain means to speak mostly about what feels wrong. Complaining can show a problem, but by itself it does not fix one."
    )],
    "mystery": [(
        "What is a mystery to solve?",
        "A mystery is something important that is not understood yet. You solve it by noticing clues and thinking carefully about what happened."
    )],
    "wind": [(
        "What can wind do to paper?",
        "Wind can lift, push, and scatter light paper. That is why papers are often tucked under something heavy."
    )],
    "magpie": [(
        "Why do some birds take shiny things?",
        "Some birds notice bright objects because they sparkle and stand out. A shiny thing can catch an animal's eye very quickly."
    )],
    "frog": [(
        "Why might a frog push a floating shell?",
        "A frog notices things in water and near reeds. If something floats, a frog may bump it while exploring."
    )],
}

KNOWLEDGE_ORDER = ["karaoke", "league", "complain", "mystery", "wind", "magpie", "frog"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    venue, item, cause = f["venue"], f["item_cfg"], f["cause"]
    detective, complainer = f["detective"], f["complainer"]
    return [
        f'Write a short fable for a 3-to-5-year-old that includes the words "karaoke", "complain", and "league", and centers on a mystery to solve.',
        f"Tell a gentle animal fable where a little karaoke league cannot begin because {item.phrase} is missing, {complainer.id} starts to complain, and {detective.id} solves the mystery at {venue.label}.",
        f'Write a simple mystery fable in which clues reveal that {cause.culprit_label} took or moved an important singing object, and the ending teaches that helping is wiser than grumbling.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    venue, item, cause, seeker = f["venue"], f["item_cfg"], f["cause"], f["seeker"]
    leader, complainer, detective = f["leader"], f["complainer"], f["detective"]
    out = [
        (
            "Who is the story about?",
            f"It is about a little karaoke league of animals, especially {complainer.id}, who began to complain, and {detective.id}, who chose to solve the mystery."
        ),
        (
            "What was the problem at the start?",
            f"{item.phrase.capitalize()} was missing, so the singers could not begin properly. Because of that, the whole league went quiet instead of singing."
        ),
        (
            f"Why did {complainer.id} complain?",
            f"{complainer.id} saw that the singing had stopped and felt sure the night was spoiled. The missing {item.label} made the problem feel bigger because no song could start the usual way."
        ),
        (
            f"How did {detective.id} try to solve the mystery?",
            f"{detective.id} acted like {seeker.phrase} and decided to {seeker.method}. That helped {detective.pronoun()} look for clues instead of making wild guesses."
        ),
        (
            "What clue solved the mystery?",
            f"The key clue was that {cause.clue_text} That sign pointed toward {cause.found_place} and matched what had happened to the missing {item.label}."
        ),
        (
            f"Where was the missing {item.label} found, and what had happened?",
            f"It was found at {cause.found_place}. {cause.fix_line.format(item=item.label)}"
        ),
        (
            "How did the story end?",
            f"The league got its singing object back, the karaoke began, and the animals sang together happily. The ending proves the change because the silence turned back into music."
        ),
        (
            "What lesson did the league learn?",
            f"They learned that complaining can fill the air without helping anyone. Careful looking and calm help solve a mystery much faster."
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"karaoke", "league", "complain", "mystery"} | set(f["cause"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [n for n, on in (
            ("movable", e.movable),
            ("shiny", e.shiny),
            ("paper", e.paper),
            ("floats", e.floats),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hill", "songbook", "wind", "tracker", "Tortoise", "Goat", "Wren"),
    StoryParams("market", "bell", "magpie", "listener", "Badger", "Crow", "Mouse"),
    StoryParams("pond", "shell_mic", "frog", "thinker", "Mole", "Duck", "Robin"),
]


def explain_rejection(venue: Venue, item: MissingItem, cause: Cause) -> str:
    if cause.requires_wind and not venue.windy:
        return f"(No story: {cause.id} needs a breezy place, but {venue.label} is not windy enough to carry {item.label} away.)"
    if cause.requires_water and not venue.has_water:
        return f"(No story: {cause.id} only makes sense near water, but {venue.label} has no water edge.)"
    if cause.requires_shiny and not item.shiny:
        return f"(No story: a magpie-like borrowing mystery fits a shiny object, but {item.phrase} is not shiny.)"
    if cause.requires_paper and not item.paper:
        return f"(No story: wind can scatter paper like a songbook, but it does not sensibly carry this {item.label} in this domain.)"
    if cause.requires_float and not item.floats:
        return f"(No story: this water-side mix-up needs something that floats, but {item.phrase} would not drift that way.)"
    return "(No story: that venue, missing item, and cause do not form a sensible mystery.)"


ASP_RULES = r"""
compatible(V, I, C) :-
    venue(V), item(I), cause(C),
    movable(I),
    not need_water_missing(V, C),
    not need_wind_missing(V, C),
    not need_shiny_missing(I, C),
    not need_paper_missing(I, C),
    not need_float_missing(I, C).

need_water_missing(V, C) :- cause_needs_water(C), venue(V), not has_water(V).
need_wind_missing(V, C)  :- cause_needs_wind(C), venue(V), not windy(V).
need_shiny_missing(I, C) :- cause_needs_shiny(C), item(I), not shiny(I).
need_paper_missing(I, C) :- cause_needs_paper(C), item(I), not paper(I).
need_float_missing(I, C) :- cause_needs_float(C), item(I), not floats(I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for vid, v in VENUES.items():
        lines.append(asp.fact("venue", vid))
        if v.has_water:
            lines.append(asp.fact("has_water", vid))
        if v.windy:
            lines.append(asp.fact("windy", vid))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if it.movable:
            lines.append(asp.fact("movable", iid))
        if it.shiny:
            lines.append(asp.fact("shiny", iid))
        if it.paper:
            lines.append(asp.fact("paper", iid))
        if it.floats:
            lines.append(asp.fact("floats", iid))
    for cid, c in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        if c.requires_water:
            lines.append(asp.fact("cause_needs_water", cid))
        if c.requires_wind:
            lines.append(asp.fact("cause_needs_wind", cid))
        if c.requires_shiny:
            lines.append(asp.fact("cause_needs_shiny", cid))
        if c.requires_paper:
            lines.append(asp.fact("cause_needs_paper", cid))
        if c.requires_float:
            lines.append(asp.fact("cause_needs_float", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a little karaoke league, a complaint, and a mystery solved in fable style."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--seeker", choices=SEEKERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.venue and args.item and args.cause:
        if not cause_fits(VENUES[args.venue], ITEMS[args.item], CAUSES[args.cause]):
            raise StoryError(explain_rejection(VENUES[args.venue], ITEMS[args.item], CAUSES[args.cause]))

    combos = [
        c for c in valid_combos()
        if (args.venue is None or c[0] == args.venue)
        and (args.item is None or c[1] == args.item)
        and (args.cause is None or c[2] == args.cause)
    ]
    if not combos:
        venue = VENUES[args.venue] if args.venue else next(iter(VENUES.values()))
        item = ITEMS[args.item] if args.item else next(iter(ITEMS.values()))
        cause = CAUSES[args.cause] if args.cause else next(iter(CAUSES.values()))
        raise StoryError(explain_rejection(venue, item, cause))

    venue_id, item_id, cause_id = rng.choice(sorted(combos))
    seeker_id = args.seeker or rng.choice(sorted(SEEKERS))
    leader = rng.choice(LEADER_NAMES)
    complainer = rng.choice([n for n in COMPLAINER_NAMES if n != leader])
    detective = rng.choice([n for n in DETECTIVE_NAMES if n not in {leader, complainer}])
    return StoryParams(venue_id, item_id, cause_id, seeker_id, leader, complainer, detective)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        VENUES[params.venue],
        ITEMS[params.item],
        CAUSES[params.cause],
        SEEKERS[params.seeker],
        params.leader,
        params.complainer,
        params.detective,
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
        print(asp_program("", "#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, item, cause) combos:\n")
        for venue, item, cause in combos:
            print(f"  {venue:8} {item:10} {cause}")
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
            header = f"### {p.venue}: {p.item} mystery caused by {p.cause}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
