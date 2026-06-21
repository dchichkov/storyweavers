#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/calendar_suspense_repetition_ghost_story.py
======================================================================

A standalone story world for a gentle ghost story built around a calendar,
suspense, and repetition.

Premise
-------
A child in an old room keeps hearing the same soft calendar flutter at night.
Again and again, the page falls open to the same date. The repeated sign points
to a kind unfinished wish. When the child tells a grown-up and they answer that
wish in the right way, the room changes.

Run it
------
python storyworlds/worlds/gpt-5.4/calendar_suspense_repetition_ghost_story.py
python storyworlds/worlds/gpt-5.4/calendar_suspense_repetition_ghost_story.py --room attic --motive birthday --act cake
python storyworlds/worlds/gpt-5.4/calendar_suspense_repetition_ghost_story.py --motive planting --act stars
python storyworlds/worlds/gpt-5.4/calendar_suspense_repetition_ghost_story.py --all
python storyworlds/worlds/gpt-5.4/calendar_suspense_repetition_ghost_story.py --verify
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
from contextlib import redirect_stdout
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
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def helper_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Room:
    id: str
    place: str
    calendar_phrase: str
    hush: str
    moon: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Motive:
    id: str
    date_name: str
    clue_line: str
    wish_line: str
    needed_act: str
    patience: int
    closing_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Act:
    id: str
    label: str
    phrase: str
    result: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, room: Room) -> None:
        self.room_cfg = room
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World(self.room_cfg)
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


def _r_restless(world: World) -> list[str]:
    ghost = world.get("ghost")
    cal = world.get("calendar")
    child = world.get("child")
    room = world.get("room")
    if ghost.meters["restless"] < THRESHOLD:
        return []
    sig = ("restless", int(world.facts.get("night_count", 0)))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cal.meters["fluttered"] += 1
    room.meters["chill"] += 1
    child.memes["fear"] += 1
    return []


def _r_pattern(world: World) -> list[str]:
    child = world.get("child")
    if world.facts.get("night_count", 0) < 2 or child.memes["fear"] < THRESHOLD:
        return []
    sig = ("pattern", world.facts.get("night_count", 0))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    return []


def _r_soothe(world: World) -> list[str]:
    ghost = world.get("ghost")
    room = world.get("room")
    child = world.get("child")
    if not world.facts.get("act_suitable"):
        return []
    if world.facts.get("act_done") is not True:
        return []
    sig = ("soothed", world.facts.get("chosen_act"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.meters["restless"] = 0.0
    ghost.meters["soothed"] += 1
    room.meters["chill"] = 0.0
    room.meters["peace"] += 1
    child.memes["relief"] += 1
    child.memes["fear"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="restless", tag="physical", apply=_r_restless),
    Rule(name="pattern", tag="emotional", apply=_r_pattern),
    Rule(name="soothe", tag="resolution", apply=_r_soothe),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = (dict(world.get("ghost").meters), dict(world.get("child").memes), dict(world.get("room").meters))
            rule.apply(world)
            after = (dict(world.get("ghost").meters), dict(world.get("child").memes), dict(world.get("room").meters))
            if before != after:
                changed = True


ROOMS = {
    "hallway": Room(
        id="hallway",
        place="the long upstairs hallway",
        calendar_phrase="a family calendar with squares big enough for birthdays and little notes",
        hush="the boards gave tiny creaks under the dark",
        moon="a strip of moonlight lay across the wall",
        tags={"hallway", "calendar"},
    ),
    "kitchen": Room(
        id="kitchen",
        place="the old kitchen",
        calendar_phrase="a paper calendar hanging beside the pantry door",
        hush="the clock ticked so softly it sounded shy",
        moon="pale window light touched the cupboards",
        tags={"kitchen", "calendar"},
    ),
    "attic": Room(
        id="attic",
        place="the slanted attic bedroom",
        calendar_phrase="an old calendar pinned beside the little bed",
        hush="the roof whispered whenever the wind moved past",
        moon="silver moonlight slid down the slanted ceiling",
        tags={"attic", "calendar"},
    ),
}

MOTIVES = {
    "birthday": Motive(
        id="birthday",
        date_name="a forgotten birthday",
        clue_line="the square for the twelfth had been circled in a fading blue ring",
        wish_line="someone had once wanted that day to be remembered with cake and candlelight",
        needed_act="cake",
        patience=1,
        closing_image="the calendar rested open on a bright square with a crumb of frosting on the sill",
        tags={"birthday", "memory"},
    ),
    "planting": Motive(
        id="planting",
        date_name="planting day",
        clue_line="the square for the seventh had a tiny pressed leaf tucked behind it",
        wish_line="someone had once meant to put bulbs into the earth before spring forgot them",
        needed_act="bulbs",
        patience=2,
        closing_image="the calendar hung still while damp flowerpots waited on the windowsill",
        tags={"garden", "memory"},
    ),
    "stars": Motive(
        id="stars",
        date_name="star night",
        clue_line="the square for the twenty-first held a small penciled star",
        wish_line="someone had once promised to hang paper stars before the longest night",
        needed_act="stars",
        patience=1,
        closing_image="the calendar no longer fluttered, and paper stars turned slowly in the quiet air",
        tags={"stars", "memory"},
    ),
}

ACTS = {
    "cake": Act(
        id="cake",
        label="a small cake",
        phrase="baked a small honey cake and set one neat slice beneath the calendar",
        result="The sweet smell warmed the room, as if an old party had finally been invited back in.",
        tags={"cake", "kindness"},
    ),
    "bulbs": Act(
        id="bulbs",
        label="spring bulbs",
        phrase="filled a pot with soil and planted three round bulbs by the window",
        result="A damp, earthy smell rose up, and the room felt as if it had taken a slow, happy breath.",
        tags={"garden", "kindness"},
    ),
    "stars": Act(
        id="stars",
        label="paper stars",
        phrase="cut paper stars and hung them on a thread above the bed",
        result="The stars swayed in the moonlight, and the shadows on the wall stopped looking lonely.",
        tags={"stars", "kindness"},
    ),
}

GIRL_NAMES = ["Lily", "Mina", "Nora", "Ava", "Lucy", "Ivy", "Ella", "Rose"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Noah", "Finn", "Max", "Theo", "Eli"]
HELPERS = ["mother", "father", "grandmother", "grandfather", "aunt", "uncle"]
TRAITS = ["careful", "quiet", "curious", "brave", "gentle", "thoughtful"]


def act_matches(motive: Motive, act: Act) -> bool:
    return motive.needed_act == act.id


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for room_id in ROOMS:
        for motive_id, motive in MOTIVES.items():
            for act_id, act in ACTS.items():
                if act_matches(motive, act):
                    combos.append((room_id, motive_id, act_id))
    return combos


@dataclass
class StoryParams:
    room: str
    motive: str
    act: str
    child_name: str
    child_gender: str
    helper: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        room="hallway",
        motive="birthday",
        act="cake",
        child_name="Lily",
        child_gender="girl",
        helper="grandmother",
        trait="careful",
        delay=0,
    ),
    StoryParams(
        room="attic",
        motive="planting",
        act="bulbs",
        child_name="Ben",
        child_gender="boy",
        helper="grandfather",
        trait="quiet",
        delay=1,
    ),
    StoryParams(
        room="kitchen",
        motive="stars",
        act="stars",
        child_name="Nora",
        child_gender="girl",
        helper="aunt",
        trait="curious",
        delay=2,
    ),
]


def outcome_of(params: StoryParams) -> str:
    motive = MOTIVES[params.motive]
    return "soothed" if params.delay <= motive.patience else "lingering"


def explain_rejection(motive: Motive, act: Act) -> str:
    return (
        f"(No story: {act.label} does not answer the clue for {motive.date_name}. "
        f"The ghost keeps pointing to one date for a reason, so the kindness must match that reason.)"
    )


def setup_story(world: World, child: Entity, helper: Entity, room_cfg: Room) -> None:
    world.say(
        f"{child.id} slept near {room_cfg.calendar_phrase} in {room_cfg.place}. "
        f"By day it was only paper and string, but at night {room_cfg.moon}, and {room_cfg.hush}."
    )
    world.say(
        f"{child.pronoun().capitalize()} was a {next(iter([t for t in child.attrs.get('traits', []) if t]), 'quiet')} child "
        f"who noticed little things other people missed."
    )


def spooky_night(world: World, child: Entity, motive: Motive, night_no: int) -> None:
    ghost = world.get("ghost")
    ghost.meters["restless"] += 1
    world.facts["night_count"] = night_no
    propagate(world)
    first = {1: "On the first night", 2: "On the second night", 3: "On the third night"}.get(
        night_no, f"On night {night_no}"
    )
    world.say(
        f"{first}, {child.id} woke to a papery whisper. The calendar rustled by itself, one page lifting, then another, then another."
    )
    world.say(
        f"When the sound stopped, the page hung open to the same square again. {motive.clue_line.capitalize()}."
    )
    if night_no == 1:
        world.say(
            f"{child.id} pulled the blanket up to {child.pronoun('possessive')} chin and listened for footsteps, but heard none."
        )
    elif night_no == 2:
        world.say(
            f"Again it had chosen the same date. That was the part that made the room feel colder than the dark."
        )
    else:
        world.say(
            f"Again. Always the same date. By then the repetition felt less like an accident and more like a knock from someone patient and sad."
        )


def confide(world: World, child: Entity, helper: Entity, motive: Motive) -> None:
    world.say(
        f"In the morning, {child.id} found {helper.helper_word} in the kitchen light and whispered everything."
    )
    world.say(
        f'"The calendar keeps turning to the same day," {child.pronoun()} said. "{motive.date_name.capitalize()}."'
    )
    world.say(
        f"{helper.helper_word.capitalize()} did not laugh. {helper.pronoun().capitalize()} went to look at the page with {child.id}, very slowly, as if quiet things deserved quiet manners."
    )


def investigate(world: World, child: Entity, helper: Entity, motive: Motive) -> None:
    child.memes["trust"] += 1
    helper.memes["care"] += 1
    world.say(
        f"Behind the curling page they found a faint note in old pencil, nearly rubbed away by years."
    )
    world.say(
        f"It said just enough to make the wish plain: {motive.wish_line}."
    )


def perform_act(world: World, helper: Entity, act: Act) -> None:
    world.facts["act_done"] = True
    world.say(
        f"So {helper.helper_word} and the child answered the sign the gentle way: they {act.phrase}."
    )
    world.say(act.result)
    propagate(world)


def soothed_ending(world: World, child: Entity, helper: Entity, motive: Motive) -> None:
    world.say(
        f"That night, {child.id} stayed awake for the whisper again."
    )
    world.say(
        "The room waited. The moon moved. The calendar gave one tiny shiver, as if someone had let out a last careful sigh."
    )
    world.say(
        f"Then it was still. No flipping pages. No cold draft on the cheek. Only the soft house settling around them."
    )
    world.say(
        f"{child.id} went to sleep smiling, because some ghosts, {child.pronoun()} thought, did not want to frighten anyone. They only wanted to be remembered kindly."
    )
    world.say(motive.closing_image.capitalize() + ".")
    world.facts["ending_image"] = motive.closing_image


def lingering_ending(world: World, child: Entity, helper: Entity, motive: Motive) -> None:
    world.say(
        f"That night, {child.id} listened hard for silence."
    )
    world.say(
        f"For a while there was only the dark and the moon. Then, very softly, the calendar turned one page by itself and stopped on the same date again."
    )
    world.say(
        f"It was not angry now, only sadder and fainter, as if the wish had been heard a little too late."
    )
    world.say(
        f"{helper.helper_word.capitalize()} squeezed {child.id}'s hand and promised they would keep honoring the date every year. After that, the room was gentler, but never quite ordinary."
    )
    world.say(
        f"Sometimes, when the house was very quiet, the calendar still gave a papery tap in the dark."
    )
    world.facts["ending_image"] = "the calendar gave a papery tap in the dark"


def tell(
    room_cfg: Room,
    motive: Motive,
    act: Act,
    child_name: str,
    child_gender: str,
    helper_type: str,
    trait: str,
    delay: int,
) -> World:
    world = World(room_cfg)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            attrs={"traits": [trait]},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
        )
    )
    world.add(Entity(id="room", type="room", label=room_cfg.place, tags=set(room_cfg.tags)))
    world.add(Entity(id="calendar", type="calendar", label="calendar", tags={"calendar"}))
    world.add(Entity(id="ghost", type="ghost", label="ghost", tags={"ghost"}))

    world.facts["night_count"] = 0
    world.facts["act_done"] = False
    world.facts["act_suitable"] = act_matches(motive, act)
    world.facts["chosen_act"] = act.id

    setup_story(world, child, helper, room_cfg)

    world.para()
    for night_no in range(1, min(delay + 2, 3) + 1):
        spooky_night(world, child, motive, night_no)

    world.para()
    confide(world, child, helper, motive)
    investigate(world, child, helper, motive)

    world.para()
    perform_act(world, helper, act)

    world.para()
    if delay <= motive.patience:
        soothed_ending(world, child, helper, motive)
        outcome = "soothed"
    else:
        lingering_ending(world, child, helper, motive)
        outcome = "lingering"

    world.facts.update(
        child=child,
        helper=helper,
        motive=motive,
        act=act,
        room_cfg=room_cfg,
        repeated_nights=min(delay + 2, 3),
        outcome=outcome,
        suitable=act_matches(motive, act),
        date_name=motive.date_name,
    )
    return world


KNOWLEDGE = {
    "calendar": [
        (
            "What is a calendar?",
            "A calendar is a chart of days and months. People use it to remember birthdays, holidays, and other important dates.",
        )
    ],
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a spooky story about a spirit or haunting. In gentle ghost stories, the ghost is often sad or lonely instead of mean.",
        )
    ],
    "birthday": [
        (
            "Why do people mark birthdays on a calendar?",
            "People mark birthdays on a calendar so they remember to celebrate on the right day. A date can feel very important when it belongs to someone special.",
        )
    ],
    "garden": [
        (
            "Why do people plant bulbs before spring?",
            "Bulbs are planted early so they can rest in the soil and grow when the weather warms. Planting at the right time helps flowers bloom later.",
        )
    ],
    "stars": [
        (
            "Why do paper stars glow in moonlight?",
            "Paper stars do not make light of their own, but moonlight can shine on them and make them look bright and floaty in a dark room.",
        )
    ],
    "kindness": [
        (
            "Can kindness solve a problem in a scary story?",
            "Sometimes it can. If the scary thing is really a lonely or unfinished feeling, a kind act can change what happens.",
        )
    ],
}
KNOWLEDGE_ORDER = ["calendar", "ghost", "birthday", "garden", "stars", "kindness"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    motive = world.facts["motive"]
    act = world.facts["act"]
    room_cfg = world.facts["room_cfg"]
    outcome = world.facts["outcome"]
    if outcome == "lingering":
        ending = "end with a gentle but still-spooky image that shows the house is not fully ordinary again"
    else:
        ending = "end with the room turning peaceful after the clue is understood"
    return [
        (
            f'Write a gentle ghost story for a 3-to-5-year-old that includes the word "calendar", '
            f'uses repetition, and takes place in {room_cfg.place}.'
        ),
        (
            f"Tell a suspenseful story where a {child.type} named {child.id} hears the same calendar page turn again and again, "
            f"until the repeated date leads to {motive.date_name} and a kind act with {act.label}."
        ),
        (
            f"Write a child-facing ghost story with three repeated nighttime signs, a caring grown-up, and {ending}."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    motive = world.facts["motive"]
    act = world.facts["act"]
    room_cfg = world.facts["room_cfg"]
    repeated = world.facts["repeated_nights"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who slept near a calendar in {room_cfg.place}, and {helper.helper_word}, who listened carefully. The story follows them as they figure out why the same date keeps returning.",
        ),
        (
            "What made the story feel spooky?",
            f"The calendar kept rustling and opening to the same date at night, even when nobody was touching it. The repetition made the sign feel purposeful instead of accidental.",
        ),
        (
            "Why was the repeated date important?",
            f"It pointed to {motive.date_name}. When {child.id} and {helper.helper_word} looked closely, they realized the ghost was trying to remind someone of an unfinished wish.",
        ),
        (
            f"What did {child.id} do when the calendar kept moving?",
            f"{child.id} told {helper.helper_word} instead of hiding the secret alone. That mattered because the grown-up helped turn fear into understanding.",
        ),
        (
            f"How did they answer the ghost's clue?",
            f"They {act.phrase}. The act matched the meaning of the date, so it answered the ghost in a kind and respectful way.",
        ),
    ]
    if outcome == "soothed":
        qa.append(
            (
                "How did the story end?",
                f"After {repeated} spooky nights, the calendar finally stayed still. The ending proves something changed because the room felt warm and peaceful instead of cold and watchful.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"They helped as best they could, and the room grew gentler, but the calendar still moved once in the dark. That ending shows the wish was heard, though not completely settled.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    motive = world.facts["motive"]
    act = world.facts["act"]
    tags = {"calendar", "ghost", "kindness"} | set(motive.tags) | set(act.tags)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if entity.role:
            bits.append(f"role={entity.role}")
        if entity.attrs:
            shown = {k: v for k, v in entity.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {entity.id:8} ({entity.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
matches(M, A) :- motive(M), needed_act(M, A).
valid(R, M, A) :- room(R), motive(M), act(A), matches(M, A).

soothed :- chosen_motive(M), chosen_delay(D), patience(M, P), D <= P.
lingering :- chosen_motive(M), chosen_delay(D), patience(M, P), D > P.

outcome(soothed) :- soothed.
outcome(lingering) :- lingering.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for room_id in ROOMS:
        lines.append(asp.fact("room", room_id))
    for motive_id, motive in MOTIVES.items():
        lines.append(asp.fact("motive", motive_id))
        lines.append(asp.fact("needed_act", motive_id, motive.needed_act))
        lines.append(asp.fact("patience", motive_id, motive.patience))
    for act_id in ACTS:
        lines.append(asp.fact("act", act_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_motive", params.motive),
            asp.fact("chosen_delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a calendar clue, and a gentle ghost."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--motive", choices=MOTIVES)
    ap.add_argument("--act", choices=ACTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="nights waited before fully acting on the clue")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.motive and args.act:
        if not act_matches(MOTIVES[args.motive], ACTS[args.act]):
            raise StoryError(explain_rejection(MOTIVES[args.motive], ACTS[args.act]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.room is None or combo[0] == args.room)
        and (args.motive is None or combo[1] == args.motive)
        and (args.act is None or combo[2] == args.act)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, motive_id, act_id = rng.choice(sorted(combos))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.child_name or rng.choice(name_pool)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])
    return StoryParams(
        room=room_id,
        motive=motive_id,
        act=act_id,
        child_name=child_name,
        child_gender=gender,
        helper=helper,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"(Invalid room: {params.room})")
    if params.motive not in MOTIVES:
        raise StoryError(f"(Invalid motive: {params.motive})")
    if params.act not in ACTS:
        raise StoryError(f"(Invalid act: {params.act})")
    motive = MOTIVES[params.motive]
    act = ACTS[params.act]
    if not act_matches(motive, act):
        raise StoryError(explain_rejection(motive, act))

    world = tell(
        room_cfg=ROOMS[params.room],
        motive=motive,
        act=act,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper,
        trait=params.trait,
        delay=params.delay,
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


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = CURATED[0]
        smoke_sample = generate(smoke_params)
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(smoke_sample, trace=False, qa=False)
        if not smoke_sample.story.strip():
            raise StoryError("empty story in smoke test")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (room, motive, act) combos:\n")
        for room_id, motive_id, act_id in combos:
            print(f"  {room_id:8} {motive_id:9} {act_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            params = sample.params
            header = f"### {params.child_name}: {params.motive} in {params.room} ({outcome_of(params)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
