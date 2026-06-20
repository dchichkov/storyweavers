#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dress_gerund_tolerate_airport_problem_solving_mystery.py
====================================================================================

A standalone story world for a small airport mystery: a child detective notices
that the family's travel bag is missing, follows concrete clues through the
terminal, asks a calm airport worker for help, and solves the problem in a way
that changes the ending image.

The seed asked for:
- words: dressing, tolerate
- setting: airport
- features: Problem Solving, Mystery to Solve
- style: Mystery

This script rebuilds that seed as a compact simulation rather than a frozen
template. The world models typed entities with physical meters and emotional
memes, runs a small causal system, checks reasonableness in Python and ASP, and
renders complete child-facing stories plus three grounded Q&A sets.

Run it
------
    python storyworlds/worlds/gpt-5.4/dress_gerund_tolerate_airport_problem_solving_mystery.py
    python storyworlds/worlds/gpt-5.4/dress_gerund_tolerate_airport_problem_solving_mystery.py --bag red_suitcase --clue ribbon --helper desk_agent
    python storyworlds/worlds/gpt-5.4/dress_gerund_tolerate_airport_problem_solving_mystery.py --bag paper_cup
    python storyworlds/worlds/gpt-5.4/dress_gerund_tolerate_airport_problem_solving_mystery.py --all --qa
    python storyworlds/worlds/gpt-5.4/dress_gerund_tolerate_airport_problem_solving_mystery.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
# This file lives in storyworlds/worlds/gpt-5.4/, so the package dir is three
# levels up.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    movable: bool = True
    carries_tag: bool = False
    can_help_find: bool = False
    official: bool = False
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "agent_f"}
        male = {"boy", "father", "man", "agent_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class BagKind:
    id: str
    label: str
    phrase: str
    color: str
    clue_fit: set[str]
    story_use: str
    tags: set[str] = field(default_factory=set)
    movable: bool = True
    carries_tag: bool = True


@dataclass
class Clue:
    id: str
    label: str
    found_at: str
    text: str
    method: str
    works_for: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    place: str
    method: str
    sense: int
    works_on: set[str]
    type_name: str
    tags: set[str] = field(default_factory=set)
    can_help_find: bool = True
    official: bool = True


@dataclass
class Delay:
    id: str
    label: str
    patience_cost: int
    search_time: int
    ending: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_missing_worry(world: World) -> list[str]:
    bag = world.entities.get("bag")
    kid = world.entities.get("kid")
    parent = world.entities.get("parent")
    if not bag or not kid or not parent:
        return []
    if bag.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry", bag.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    kid.memes["worry"] += 1
    parent.memes["worry"] += 1
    return ["__missing__"]


def _r_clue_hope(world: World) -> list[str]:
    clue = world.entities.get("clue")
    kid = world.entities.get("kid")
    if not clue or not kid:
        return []
    if clue.meters["noticed"] < THRESHOLD:
        return []
    sig = ("clue_hope", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    kid.memes["curiosity"] += 1
    kid.memes["hope"] += 1
    return ["__clue__"]


def _r_help_calm(world: World) -> list[str]:
    helper = world.entities.get("helper")
    kid = world.entities.get("kid")
    parent = world.entities.get("parent")
    if not helper or not kid or not parent:
        return []
    if helper.meters["asked"] < THRESHOLD:
        return []
    sig = ("help_calm", helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    kid.memes["calm"] += 1
    parent.memes["calm"] += 1
    return ["__help__"]


def _r_found_relief(world: World) -> list[str]:
    bag = world.entities.get("bag")
    kid = world.entities.get("kid")
    parent = world.entities.get("parent")
    if not bag or not kid or not parent:
        return []
    if bag.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief", bag.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    kid.memes["relief"] += 1
    parent.memes["relief"] += 1
    kid.memes["pride"] += 1
    kid.memes["worry"] = 0.0
    parent.memes["worry"] = 0.0
    return ["__found__"]


CAUSAL_RULES = [
    Rule("missing_worry", "emotional", _r_missing_worry),
    Rule("clue_hope", "emotional", _r_clue_hope),
    Rule("help_calm", "social", _r_help_calm),
    Rule("found_relief", "emotional", _r_found_relief),
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
        for sent in produced:
            world.say(sent)
    return produced


def clue_matches(bag: BagKind, clue: Clue) -> bool:
    return clue.id in bag.clue_fit and bag.id in clue.works_for


def helper_is_sensible(helper: Helper) -> bool:
    return helper.sense >= SENSE_MIN


def helper_can_solve(helper: Helper, clue: Clue) -> bool:
    return helper.id in clue.tags or clue.id in helper.works_on


def valid_combo(bag: BagKind, clue: Clue, helper: Helper) -> bool:
    return bag.movable and bag.carries_tag and clue_matches(bag, clue) and helper_is_sensible(helper) and helper_can_solve(helper, clue)


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for bag_id, bag in BAGS.items():
        for clue_id, clue in CLUES.items():
            for helper_id, helper in HELPERS.items():
                if valid_combo(bag, clue, helper):
                    out.append((bag_id, clue_id, helper_id))
    return out


def predict_search(bag: BagKind, clue: Clue, helper: Helper, delay: Delay) -> dict:
    success = valid_combo(bag, clue, helper)
    calm = helper_is_sensible(helper)
    missed_flight = delay.search_time >= 3 and not success
    return {"success": success, "calm": calm, "missed_flight": missed_flight}


def intro(world: World, kid: Entity, parent: Entity, bag: BagKind, trip_word: str) -> None:
    world.say(
        f"{kid.id} and {kid.pronoun('possessive')} {parent.label_word} were in the airport long before sunrise, "
        f"ready for a trip to {trip_word}."
    )
    world.say(
        f"While dressing in the bright airport bathroom, {kid.id} had buttoned a small coat, tied one shoe twice, "
        f"and decided that the morning felt exactly right for a mystery."
    )
    world.say(
        f"They rolled {bag.phrase} beside them through the shiny terminal floor, and the bag held {bag.story_use}."
    )


def airport_color(world: World, kid: Entity) -> None:
    world.say(
        f"Everything around {kid.id} seemed full of clues already: wheels hummed, signs blinked, and a speaker kept clearing its throat over the gate."
    )


def disappearance(world: World, kid: Entity, parent: Entity, bag_ent: Entity, bag: BagKind) -> None:
    bag_ent.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When they stopped beside the check-in ropes, {kid.id} looked down and gave a small gasp. "
        f"{bag.phrase.capitalize()} was gone."
    )
    world.say(
        f'"I can tolerate a long line," said {parent.label_word} softly, looking around, "but I cannot tolerate losing our bag."'
    )
    world.say(
        f"{kid.id} pressed close to {parent.label_word} and scanned the floor where the wheels should have been."
    )


def spot_clue(world: World, kid: Entity, clue_ent: Entity, clue: Clue, bag: BagKind) -> None:
    clue_ent.meters["noticed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {kid.id} noticed {clue.text}. It was the sort of tiny thing that most people would miss."
    )
    world.say(
        f'"That belongs with the {bag.label}," {kid.pronoun()} whispered. "Maybe the bag went toward {clue.found_at}."'
    )


def parent_allows_search(world: World, parent: Entity, kid: Entity) -> None:
    world.say(
        f"{parent.label_word.capitalize()} took a slow breath instead of rushing in circles. "
        f'"Show me what you see," {parent.pronoun()} said. "We will solve this step by step."'
    )


def ask_helper(world: World, kid: Entity, helper_ent: Entity, helper: Helper, clue: Clue) -> None:
    helper_ent.meters["asked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They followed the clue to {helper.place}, where {helper.phrase} was helping other travelers."
    )
    world.say(
        f'{kid.id} pointed carefully. "We found {clue.label}. Can you help us?"'
    )
    world.say(
        f"{helper.label.capitalize()} listened to the whole story and nodded. {helper.method}."
    )


def recover_bag(world: World, kid: Entity, parent: Entity, bag_ent: Entity, bag: BagKind, delay: Delay) -> None:
    bag_ent.meters["found"] += 1
    bag_ent.meters["missing"] = 0.0
    bag_ent.location = "found_area"
    propagate(world, narrate=False)
    world.say(
        f"A little while later, they spotted {bag.phrase} exactly where the clue had promised."
    )
    world.say(
        f"It had been waiting near {delay.ending}, safe and quiet, as if it had been playing hide-and-seek."
    )
    world.say(
        f"{kid.id} hugged {parent.label_word}'s side, and {parent.label_word} squeezed {kid.pronoun('possessive')} shoulder. "
        f"The airport did not feel confusing anymore. It felt solved."
    )


def ending_image(world: World, kid: Entity, parent: Entity, bag: BagKind) -> None:
    world.say(
        f"Soon they were back at the gate with {bag.phrase}, and {kid.id} sat beside it like a real detective guarding the final clue."
    )


def tell(
    bag: BagKind,
    clue: Clue,
    helper: Helper,
    delay: Delay,
    kid_name: str = "Mina",
    kid_type: str = "girl",
    parent_type: str = "mother",
    trip_word: str = "Grandma's house",
) -> World:
    if not valid_combo(bag, clue, helper):
        raise StoryError(explain_rejection(bag, clue, helper))

    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_type, role="kid"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    bag_ent = world.add(Entity(
        id="bag",
        type="bag",
        label=bag.label,
        movable=bag.movable,
        carries_tag=bag.carries_tag,
        location="check_in",
    ))
    clue_ent = world.add(Entity(id="clue", type="clue", label=clue.label, location=clue.found_at))
    helper_ent = world.add(Entity(
        id="helper",
        kind="character",
        type=helper.type_name,
        label=helper.label,
        role="helper",
        location=helper.place,
        can_help_find=helper.can_help_find,
        official=helper.official,
    ))

    intro(world, kid, parent, bag, trip_word)
    airport_color(world, kid)

    world.para()
    disappearance(world, kid, parent, bag_ent, bag)
    spot_clue(world, kid, clue_ent, clue, bag)
    parent_allows_search(world, parent, kid)

    world.para()
    ask_helper(world, kid, helper_ent, helper, clue)
    recover_bag(world, kid, parent, bag_ent, bag, delay)
    ending_image(world, kid, parent, bag)

    world.facts.update(
        kid=kid,
        parent=parent,
        bag_cfg=bag,
        clue_cfg=clue,
        helper_cfg=helper,
        delay_cfg=delay,
        bag=bag_ent,
        clue=clue_ent,
        helper=helper_ent,
        solved=True,
        trip_word=trip_word,
        method=helper.method,
    )
    return world


BAGS = {
    "red_suitcase": BagKind(
        "red_suitcase",
        "red suitcase",
        "the red suitcase with a cloud sticker",
        "red",
        {"ribbon"},
        "their sweaters, a map book, and a wrapped birthday present",
        tags={"suitcase", "travel"},
    ),
    "blue_duffel": BagKind(
        "blue_duffel",
        "blue duffel bag",
        "the blue duffel bag with a squeaky wheel",
        "blue",
        {"wheel_mark"},
        "snacks, extra socks, and a tiny blanket for the flight",
        tags={"bag", "travel"},
    ),
    "green_backpack": BagKind(
        "green_backpack",
        "green backpack",
        "the green backpack with a silver star zipper",
        "green",
        {"zipper_charm"},
        "books, crayons, and a stuffed rabbit",
        tags={"backpack", "travel"},
    ),
    "paper_cup": BagKind(
        "paper_cup",
        "paper cup",
        "the paper cup from the waiting area",
        "white",
        set(),
        "nothing important at all",
        tags={"decoy"},
        movable=True,
        carries_tag=False,
    ),
}

CLUES = {
    "ribbon": Clue(
        "ribbon",
        "a loose red ribbon",
        "the oversize-baggage desk",
        "a loose red ribbon caught on the corner of a sign",
        "The desk agent checked the oversize corner, where bags were lined up by hand.",
        {"red_suitcase"},
        tags={"ribbon", "desk_agent"},
    ),
    "wheel_mark": Clue(
        "wheel_mark",
        "a squeaky wheel mark",
        "the elevator doors",
        "a thin gray wheel mark curving toward the elevator doors",
        "The cleaner recognized the squeaky trail and led them to the elevator landing.",
        {"blue_duffel"},
        tags={"wheel_mark", "cleaner"},
    ),
    "zipper_charm": Clue(
        "zipper_charm",
        "a silver star charm",
        "the family restroom",
        "a tiny silver star charm shining near the family restroom",
        "The security officer radioed the restroom area, where a traveler had turned in the backpack.",
        {"green_backpack"},
        tags={"zipper_charm", "security"},
    ),
}

HELPERS = {
    "desk_agent": Helper(
        "desk_agent",
        "desk agent",
        "a desk agent in a navy jacket",
        "the oversize-baggage desk",
        "The desk agent checked the oversize corner, where bags were lined up by hand",
        3,
        {"ribbon"},
        "agent_f",
        tags={"desk_agent", "airport"},
    ),
    "cleaner": Helper(
        "cleaner",
        "cleaner",
        "a cleaner pushing a humming floor machine",
        "the elevator hall",
        "The cleaner remembered hearing one wheel squeak again and again and pointed them the right way",
        2,
        {"wheel_mark"},
        "agent_m",
        tags={"cleaner", "airport"},
    ),
    "security": Helper(
        "security",
        "security officer",
        "a security officer beside the bright monitor wall",
        "the security desk",
        "The security officer called ahead and asked if anyone had turned in a green backpack with a silver star zipper",
        3,
        {"zipper_charm"},
        "agent_m",
        tags={"security", "airport"},
    ),
    "snack_vendor": Helper(
        "snack_vendor",
        "snack seller",
        "a snack seller balancing pretzels",
        "the snack stand",
        "The snack seller guessed and shrugged",
        1,
        set(),
        "agent_f",
        tags={"vendor"},
    ),
}

DELAYS = {
    "soon": Delay("soon", "soon", 0, 1, "the helper's desk", tags={"on_time"}),
    "wait": Delay("wait", "after a short wait", 1, 1, "a row of quiet lost bags", tags={"on_time"}),
    "long": Delay("long", "after a long, quiet wait", 2, 2, "the lost-and-found shelf by the window", tags={"delay"}),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ava", "Lucy", "Maya", "Zoe", "Ella"]
BOY_NAMES = ["Owen", "Ben", "Leo", "Max", "Finn", "Theo", "Eli", "Sam"]
TRIP_WORDS = ["Grandma's house", "a wedding by the sea", "a mountain trip", "their cousin's birthday"]


@dataclass
class StoryParams:
    bag: str
    clue: str
    helper: str
    delay: str
    name: str
    gender: str
    parent: str
    trip_word: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "airport": [(
        "What does an airport do?",
        "An airport is a place where people come to take airplane trips. It has gates, workers, bags, and lots of signs to help travelers find their way."
    )],
    "travel": [(
        "Why do people put tags on travel bags?",
        "A tag helps show who the bag belongs to and where it should go. If a bag gets moved, the tag gives workers a better chance to return it."
    )],
    "suitcase": [(
        "What is a suitcase for?",
        "A suitcase is a travel bag for clothes and other things you need on a trip. It usually has a handle and wheels so you can pull it through the airport."
    )],
    "backpack": [(
        "What is a backpack?",
        "A backpack is a bag you carry on your back with two straps. People often use one for books, snacks, and travel things they want close by."
    )],
    "ribbon": [(
        "Why can a ribbon help identify a bag?",
        "A ribbon stands out because it looks different from plain bag handles. A small bright thing can become a useful clue when many bags look alike."
    )],
    "wheel_mark": [(
        "How can a wheel mark be a clue?",
        "A wheel mark shows where something rolling may have gone. If one wheel squeaks or leaves a line, it can help someone trace the path."
    )],
    "zipper_charm": [(
        "Why is a zipper charm easy to notice?",
        "A zipper charm is small, but it can shine or swing in a way that catches your eye. Tiny special details often help people recognize their own things."
    )],
    "desk_agent": [(
        "How can a desk agent help with a lost bag?",
        "A desk agent knows where bags are checked, moved, and set aside. They can look in the right airport area instead of just guessing."
    )],
    "cleaner": [(
        "How can a cleaner notice clues in an airport?",
        "A cleaner moves through halls and floors all day, so they often notice marks, wheels, and where things were left. Watching carefully is part of their work."
    )],
    "security": [(
        "What does a security officer do when something is lost?",
        "A security officer helps keep the airport safe and can contact nearby areas. They can ask whether a turned-in item matches the description of the missing thing."
    )],
    "mystery": [(
        "What helps solve a mystery?",
        "A mystery is solved by noticing clues, asking careful questions, and checking one idea at a time. Calm thinking helps more than panicking."
    )],
}
KNOWLEDGE_ORDER = [
    "airport", "travel", "suitcase", "backpack", "ribbon", "wheel_mark",
    "zipper_charm", "desk_agent", "cleaner", "security", "mystery"
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid = f["kid"]
    bag = f["bag_cfg"]
    clue = f["clue_cfg"]
    helper = f["helper_cfg"]
    trip = f["trip_word"]
    return [
        'Write a short mystery story for a 3-to-5-year-old set in an airport that includes the words "dressing" and "tolerate".',
        f"Tell a gentle airport mystery where a {kid.type} named {kid.id} notices that {bag.phrase} is missing, finds {clue.label}, and solves the problem by asking a {helper.label} for help.",
        f"Write a child-facing problem-solving story about traveling to {trip}, losing a special bag, and following one clear clue to a safe, satisfying ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid = f["kid"]
    parent = f["parent"]
    bag = f["bag_cfg"]
    clue = f["clue_cfg"]
    helper = f["helper_cfg"]
    delay = f["delay_cfg"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {kid.id}, {kid.pronoun('possessive')} {pw}, and the airport helper who listened to their clue. Together they solved the mystery of the missing bag."
        ),
        (
            "What was the mystery?",
            f"The mystery was that {bag.phrase} disappeared at the airport. That mattered because it held {bag.story_use} for their trip."
        ),
        (
            f"What clue did {kid.id} find?",
            f"{kid.id} found {clue.label} {clue.found_at}. The clue mattered because it matched something special about the missing {bag.label}."
        ),
        (
            f"How did {kid.id} help solve the problem?",
            f"{kid.id} did not just guess. {kid.pronoun().capitalize()} noticed the clue, explained why it mattered, and showed it to the {helper.label} so the search could happen in the right place."
        ),
        (
            f"Why did they ask the {helper.label} for help?",
            f"They asked the {helper.label} for help because that worker knew the airport area linked to the clue. The helper turned one small clue into a real search instead of a worried scramble."
        ),
        (
            "How did the story end?",
            f"They found the bag and returned to the gate with it. At the end, the airport no longer felt confusing, because the mystery had been solved step by step."
        ),
    ]
    qa.append((
        f"What did {kid.id}'s {pw} mean by saying they could not tolerate losing the bag?",
        f"{pw.capitalize()} meant that waiting in line was manageable, but losing the bag was a real problem that needed action. The line could be endured, but the missing bag changed their trip and had to be solved."
    ))
    qa.append((
        "Where was the bag when they found it?",
        f"They found it near {delay.ending}. The clue and the helper's careful search led them there."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"airport", "travel", "mystery"}
    tags |= set(f["bag_cfg"].tags)
    tags |= set(f["clue_cfg"].tags)
    tags |= set(f["helper_cfg"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.location:
            bits.append(f"location={e.location}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [n for n, on in (
            ("movable", e.movable),
            ("carries_tag", e.carries_tag),
            ("can_help_find", e.can_help_find),
            ("official", e.official),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("red_suitcase", "ribbon", "desk_agent", "soon", "Mina", "girl", "mother", "Grandma's house"),
    StoryParams("blue_duffel", "wheel_mark", "cleaner", "wait", "Leo", "boy", "father", "a mountain trip"),
    StoryParams("green_backpack", "zipper_charm", "security", "long", "Ava", "girl", "mother", "their cousin's birthday"),
]


def explain_rejection(bag: BagKind, clue: Clue, helper: Helper) -> str:
    if not bag.carries_tag:
        return (
            f"(No story: {bag.phrase} is not modeled as a real tagged travel bag, so there is no sensible airport lost-bag mystery to solve.)"
        )
    if not clue_matches(bag, clue):
        return (
            f"(No story: {clue.label} does not fit {bag.phrase}. The clue should point honestly toward the missing bag, not randomly decorate the plot.)"
        )
    if not helper_is_sensible(helper):
        return (
            f"(Refusing helper '{helper.id}': this helper guesses instead of helping methodically. A problem-solving mystery should use a more sensible airport helper.)"
        )
    if not helper_can_solve(helper, clue):
        return (
            f"(No story: {helper.label} is not the right helper for {clue.label}. The airport solution should match the clue and the worker's role.)"
        )
    return "(No story: this combination does not make a reasonable airport mystery.)"


ASP_RULES = r"""
bag_real(B) :- bag(B), carries_tag(B), movable(B).
clue_match(B, C) :- clue_fits(B, C), works_for(C, B).
sensible_helper(H) :- helper(H), sense(H, S), sense_min(M), S >= M.
helper_can_solve(H, C) :- helper_works_on(H, C).
valid(B, C, H) :- bag_real(B), clue_match(B, C), sensible_helper(H), helper_can_solve(H, C).

solved(B, C, H, D) :- valid(B, C, H), delay(D).
outcome(B, C, H, D, solved) :- solved(B, C, H, D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for bid, bag in BAGS.items():
        lines.append(asp.fact("bag", bid))
        if bag.movable:
            lines.append(asp.fact("movable", bid))
        if bag.carries_tag:
            lines.append(asp.fact("carries_tag", bid))
        for clue_id in sorted(bag.clue_fit):
            lines.append(asp.fact("clue_fits", bid, clue_id))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for bag_id in sorted(clue.works_for):
            lines.append(asp.fact("works_for", cid, bag_id))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("sense", hid, helper.sense))
        for clue_id in sorted(helper.works_on):
            lines.append(asp.fact("helper_works_on", hid, clue_id))
    for did in DELAYS:
        lines.append(asp.fact("delay", did))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_bag", params.bag),
        asp.fact("chosen_clue", params.clue),
        asp.fact("chosen_helper", params.helper),
        asp.fact("chosen_delay", params.delay),
        "outcome_chosen(X) :- chosen_bag(B), chosen_clue(C), chosen_helper(H), chosen_delay(D), outcome(B,C,H,D,X).",
    ])
    model = asp.one_model(asp_program(extra, "#show outcome_chosen/1."))
    atoms = asp.atoms(model, "outcome_chosen")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "solved" if valid_combo(BAGS[params.bag], CLUES[params.clue], HELPERS[params.helper]) else "?"


def _smoke_emit(sample: StorySample) -> str:
    buf = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        emit(sample, trace=False, qa=False, header="")
    finally:
        sys.stdout = old
    return buf.getvalue()


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for p in cases:
        ao = asp_outcome(p)
        po = outcome_of(p)
        if ao != po:
            rc = 1
            print(f"MISMATCH outcome for {p}: asp={ao} python={po}")

    try:
        sample = generate(CURATED[0])
        text = _smoke_emit(sample)
        if not text.strip():
            raise RuntimeError("emit produced empty output")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an airport mystery solved by clues and calm problem solving. "
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--bag", choices=BAGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--delay", choices=DELAYS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.bag and args.clue and args.helper:
        bag = BAGS[args.bag]
        clue = CLUES[args.clue]
        helper = HELPERS[args.helper]
        if not valid_combo(bag, clue, helper):
            raise StoryError(explain_rejection(bag, clue, helper))
    if args.helper and HELPERS[args.helper].sense < SENSE_MIN:
        helper = HELPERS[args.helper]
        bag = BAGS[args.bag] if args.bag else next(iter(BAGS.values()))
        clue = CLUES[args.clue] if args.clue else next(iter(CLUES.values()))
        raise StoryError(explain_rejection(bag, clue, helper))

    combos = [
        c for c in valid_combos()
        if (args.bag is None or c[0] == args.bag)
        and (args.clue is None or c[1] == args.clue)
        and (args.helper is None or c[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    bag, clue, helper = rng.choice(sorted(combos))
    delay = args.delay or rng.choice(sorted(DELAYS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trip_word = rng.choice(TRIP_WORDS)
    return StoryParams(bag, clue, helper, delay, name, gender, parent, trip_word)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        BAGS[params.bag],
        CLUES[params.clue],
        HELPERS[params.helper],
        DELAYS[params.delay],
        kid_name=params.name,
        kid_type=params.gender,
        parent_type=params.parent,
        trip_word=params.trip_word,
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (bag, clue, helper) combos:\n")
        for bag, clue, helper in combos:
            print(f"  {bag:15} {clue:13} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.bag} + {p.clue} + {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
