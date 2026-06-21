#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/student_consecutive_gremlin_curiosity_twist_detective_story.py
=========================================================================================

A small storyworld for a child-facing detective story: a student notices two
consecutive classroom mishaps, follows concrete clues, and discovers that a tiny
gremlin caused the trouble for a simple need. The twist is not that the world is
magic for magic's sake, but that the "culprit" is small, worried, and easier to
help than to fear.

The world model tracks a handful of typed entities with physical meters and
emotional memes, plus a short causal chain:

    gremlin need active + tempting supply nearby -> first mischief
    same need still unmet                        -> second consecutive mischief
    student curiosity + clues                    -> investigation
    fitting help                                 -> need settles, mess stops

The reasonableness gate keeps the domain narrow: each place only supports some
kinds of mishap, and each gremlin motive only has one sensible fix. The ASP twin
mirrors that gate and the simple outcome model.

Run it
------
    python storyworlds/worlds/gpt-5.4/student_consecutive_gremlin_curiosity_twist_detective_story.py
    python storyworlds/worlds/gpt-5.4/student_consecutive_gremlin_curiosity_twist_detective_story.py --place classroom --mishap pencils --motive nest
    python storyworlds/worlds/gpt-5.4/student_consecutive_gremlin_curiosity_twist_detective_story.py --motive cold --fix snack
    python storyworlds/worlds/gpt-5.4/student_consecutive_gremlin_curiosity_twist_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/student_consecutive_gremlin_curiosity_twist_detective_story.py --verify
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

# Make the shared result containers importable when this script is run directly:
# add storyworlds/ to sys.path from this nested worlds/<subdir>/ location.
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
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "teacher_f"}
        male = {"boy", "man", "father", "teacher_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "teacher_f":
            return "teacher"
        if self.type == "teacher_m":
            return "teacher"
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    affords: set[str] = field(default_factory=set)
    detail: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Mishap:
    id: str
    label: str
    object_label: str
    object_phrase: str
    first_text: str
    second_text: str
    clue: str
    danger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Motive:
    id: str
    label: str
    want_text: str
    reveal_text: str
    calm_text: str
    fix_id: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    use_text: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[str] = []
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.history = list(self.history)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_second_mischief(world: World) -> list[str]:
    out: list[str] = []
    gremlin = world.entities.get("gremlin")
    thing = world.entities.get("thing")
    if gremlin is None or thing is None:
        return out
    if gremlin.meters["need"] < THRESHOLD or thing.meters["mischief1"] < THRESHOLD:
        return out
    sig = ("second_mischief", thing.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    thing.meters["mischief2"] += 1
    world.history.append("second_mischief")
    out.append("__second__")
    return out


def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    student = world.entities.get("student")
    thing = world.entities.get("thing")
    if student is None or thing is None:
        return out
    if thing.meters["mischief2"] < THRESHOLD:
        return out
    sig = ("curiosity", student.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    student.memes["curiosity"] += 2
    student.memes["detective"] += 1
    world.history.append("curiosity_raised")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    gremlin = world.entities.get("gremlin")
    student = world.entities.get("student")
    teacher = world.entities.get("teacher")
    if gremlin is None or student is None or teacher is None:
        return out
    if gremlin.meters["need"] > 0:
        return out
    sig = ("relief", gremlin.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    gremlin.memes["trust"] += 1
    student.memes["pride"] += 1
    teacher.memes["relief"] += 1
    world.history.append("need_solved")
    return out


CAUSAL_RULES = [
    Rule(name="second_mischief", tag="physical", apply=_r_second_mischief),
    Rule(name="curiosity", tag="emotional", apply=_r_curiosity),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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
        for sent in produced:
            if sent and not sent.startswith("__"):
                world.say(sent)
    return produced


PLACES = {
    "classroom": Place(
        id="classroom",
        label="classroom",
        phrase="the bright classroom",
        affords={"pencils", "chalkboard"},
        detail="Sunlight lay across the desks, and the class jobs chart hung straight on the wall.",
        tags={"school", "classroom"},
    ),
    "library": Place(
        id="library",
        label="library corner",
        phrase="the quiet library corner",
        affords={"bookmarks", "chalkboard"},
        detail="Low shelves made little aisles, and the rug smelled faintly like old paper.",
        tags={"school", "library"},
    ),
    "artroom": Place(
        id="artroom",
        label="art room",
        phrase="the busy art room",
        affords={"crayons", "pencils"},
        detail="Paint jars shone by the sink, and every table held cups of stubby crayons.",
        tags={"school", "art"},
    ),
}

MISHAPS = {
    "pencils": Mishap(
        id="pencils",
        label="missing pencils",
        object_label="pencils",
        object_phrase="the cup of sharpened pencils",
        first_text="three yellow pencils had vanished from the cup by the window",
        second_text="two more pencils had disappeared from the very same cup",
        clue="a trail of tiny gray fuzz and pencil shavings",
        danger="Without the pencils, the morning work could not begin neatly.",
        tags={"pencils", "school_supplies"},
    ),
    "chalkboard": Mishap(
        id="chalkboard",
        label="erased chalkboard notes",
        object_label="chalkboard",
        object_phrase="the chalkboard",
        first_text="the first row of spelling words had been rubbed away in the middle of the morning",
        second_text="the fresh math sums had been smudged off again right after the teacher rewrote them",
        clue="a powdery line of chalk dust and tiny handprints",
        danger="Without the board, the class kept losing its place.",
        tags={"chalk", "school_supplies"},
    ),
    "bookmarks": Mishap(
        id="bookmarks",
        label="missing bookmarks",
        object_label="bookmarks",
        object_phrase="the basket of paper bookmarks",
        first_text="the star-shaped bookmarks had gone missing from the reading basket",
        second_text="another little stack of bookmarks had vanished before the next story time",
        clue="a wrinkled paper scrap and tiny bent corners",
        danger="Without the bookmarks, the children would lose their pages in library books.",
        tags={"bookmarks", "paper"},
    ),
    "crayons": Mishap(
        id="crayons",
        label="mixed-up crayons",
        object_label="crayons",
        object_phrase="the rainbow crayon tray",
        first_text="the red and blue crayons had been swapped into silly little towers",
        second_text="the green and orange crayons had been stacked into new wobbly towers again",
        clue="a bright smear of wax and a line of tiny crumbs",
        danger="With the crayons mixed up, the art lesson kept stopping while everyone searched for colors.",
        tags={"crayons", "art"},
    ),
}

FIXES = {
    "scrap_bin": Fix(
        id="scrap_bin",
        label="a scrap-paper nest box",
        phrase="a small box of soft scrap paper",
        use_text="set out a small box of soft scrap paper under the shelf",
        ending_image="Inside the box, the gremlin curled into a neat paper nest and stopped dragging classroom things away.",
        tags={"paper", "nest"},
    ),
    "warm_sock": Fix(
        id="warm_sock",
        label="a warm sock bed",
        phrase="a tiny bed made from a clean striped sock",
        use_text="made a tiny bed from a clean striped sock near the heater",
        ending_image="The gremlin tucked itself into the warm sock bed, and no more little thefts happened that day.",
        tags={"warmth", "sock"},
    ),
    "crumb_plate": Fix(
        id="crumb_plate",
        label="a crumb plate",
        phrase="a saucer with apple bits and cracker crumbs",
        use_text="left a saucer with apple bits and cracker crumbs beside the wall",
        ending_image="The gremlin nibbled happily from the saucer, and the school supplies stayed right where they belonged.",
        tags={"food", "snack"},
    ),
}

MOTIVES = {
    "nest": Motive(
        id="nest",
        label="build a nest",
        want_text="wanted soft little things for a nest",
        reveal_text="The gremlin was not trying to be mean at all. It had been gathering soft bits to build a nest.",
        calm_text="Once it had a safe nest, it no longer needed to take classroom supplies.",
        fix_id="scrap_bin",
        tags={"nest", "paper"},
    ),
    "cold": Motive(
        id="cold",
        label="get warm",
        want_text="was cold and hunted for snug little corners",
        reveal_text="The twist came when the student saw the gremlin shivering behind the shelf. It had made mischief because it was cold, not because it liked trouble.",
        calm_text="When it had a warm place of its own, the sneaky visits stopped.",
        fix_id="warm_sock",
        tags={"cold", "warmth"},
    ),
    "hungry": Motive(
        id="hungry",
        label="find a snack",
        want_text="was hungry and kept sniffing for anything nibble-sized",
        reveal_text="The student expected a naughty culprit, but the twist was a hungry gremlin with a worried little face.",
        calm_text="After it had something safe to eat, it quit bothering the lesson.",
        fix_id="crumb_plate",
        tags={"food", "hungry"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Zoe", "Ella", "Ivy", "Ruby", "Tess"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Milo", "Theo", "Ben", "Owen", "Sam"]
TRAITS = ["careful", "curious", "patient", "observant", "quiet", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for mishap_id in sorted(place.affords):
            for motive_id in MOTIVES:
                if select_fix(MOTIVES[motive_id]) is not None:
                    combos.append((place_id, mishap_id, motive_id))
    return combos


def select_fix(motive: Motive) -> Optional[Fix]:
    return FIXES.get(motive.fix_id)


@dataclass
class StoryParams:
    place: str
    mishap: str
    motive: str
    fix: str
    student_name: str
    student_gender: str
    teacher_gender: str
    trait: str
    seed: Optional[int] = None


def _do_first_mischief(world: World, mishap: Mishap, narrate: bool = True) -> None:
    thing = world.get("thing")
    gremlin = world.get("gremlin")
    thing.meters["mischief1"] += 1
    gremlin.meters["need"] += 1
    world.history.append("first_mischief")
    propagate(world, narrate=False)
    if narrate:
        world.say(f"Before lessons properly began, {mishap.first_text}.")


def predict_consecutive(world: World, mishap: Mishap) -> dict:
    sim = world.copy()
    _do_first_mischief(sim, mishap, narrate=False)
    return {
        "second_happens": sim.get("thing").meters["mischief2"] >= THRESHOLD,
        "curiosity": sim.get("student").memes["curiosity"],
    }


def introduce(world: World, student: Entity, teacher: Entity, mishap: Mishap) -> None:
    world.say(
        f"{student.id} was a {student.attrs.get('trait', 'careful')} student who liked to notice small things."
    )
    world.say(
        f"On Monday morning in {world.place.phrase}, {teacher.label} was getting ready for class, and {mishap.object_phrase} sat in plain sight."
    )
    world.say(world.place.detail)


def first_case(world: World, teacher: Entity, mishap: Mishap) -> None:
    _do_first_mischief(world, mishap, narrate=True)
    world.say(f'"That is odd," {teacher.label} said. "{mishap.danger}"')


def second_case(world: World, student: Entity, teacher: Entity, mishap: Mishap) -> None:
    world.say(
        f"The very next day, a second surprise came: {mishap.second_text}."
    )
    thing = world.get("thing")
    thing.meters["mischief2"] += 1
    world.history.append("second_mischief")
    propagate(world, narrate=False)
    world.say(
        f"Two consecutive mishaps were too many for {student.id} to ignore. {student.pronoun().capitalize()} felt curiosity tug like a detective's tap on the shoulder."
    )
    world.say(f'"I think there are clues," {student.id} whispered.')


def inspect(world: World, student: Entity, mishap: Mishap, motive: Motive) -> None:
    student.memes["investigation"] += 1
    world.say(
        f"{student.id} knelt by {mishap.object_phrase} and found {mishap.clue}."
    )
    if motive.id == "hungry":
        world.say("The marks did not look like a storm or a careless shoe. They looked more like tiny nibbling work.")
    elif motive.id == "nest":
        world.say("The bits had been tugged away carefully, as if someone tiny had plans for them.")
    else:
        world.say("The clues curved toward the warmest corner of the room, not toward the door.")
    world.say(
        f"The mystery no longer felt wild. It felt as if someone small needed something."
    )


def reveal(world: World, student: Entity, teacher: Entity, motive: Motive) -> None:
    gremlin = world.get("gremlin")
    gremlin.memes["fear"] += 1
    world.say(
        f"Behind a low shelf, {student.id} saw two shiny eyes, a dusty cap, and a tiny gray gremlin hugging itself."
    )
    world.say(motive.reveal_text)
    world.say(
        f'{teacher.label} did not shout. "{gremlin.pronoun("subject").capitalize()} must have been scared too," {teacher.label} said softly.'
    )


def help_gremlin(world: World, student: Entity, teacher: Entity, motive: Motive, fix: Fix) -> None:
    gremlin = world.get("gremlin")
    world.say(
        f"Together, {student.id} and {teacher.label} {fix.use_text}."
    )
    gremlin.meters["need"] = 0.0
    gremlin.memes["fear"] = 0.0
    gremlin.memes["gratitude"] += 1
    world.history.append("help_offered")
    propagate(world, narrate=False)
    world.say(motive.calm_text)
    world.say(fix.ending_image)
    world.say(
        f"By afternoon, the case was closed. The room was calm again, and {student.id} had solved it with kindness instead of scolding."
    )


def tell(
    place: Place,
    mishap: Mishap,
    motive: Motive,
    fix: Fix,
    student_name: str = "Lina",
    student_gender: str = "girl",
    teacher_gender: str = "teacher_f",
    trait: str = "curious",
) -> World:
    world = World(place)
    student = world.add(
        Entity(
            id=student_name,
            kind="character",
            type=student_gender,
            label=student_name,
            role="student",
            attrs={"trait": trait},
        )
    )
    teacher_label = "Ms. Bell" if teacher_gender == "teacher_f" else "Mr. Bell"
    teacher = world.add(
        Entity(
            id="Teacher",
            kind="character",
            type=teacher_gender,
            label=teacher_label,
            role="teacher",
        )
    )
    gremlin = world.add(
        Entity(
            id="gremlin",
            kind="character",
            type="creature",
            label="the gremlin",
            role="gremlin",
            tags={"gremlin"},
        )
    )
    thing = world.add(
        Entity(
            id="thing",
            kind="thing",
            type=mishap.object_label,
            label=mishap.object_label,
            phrase=mishap.object_phrase,
            role="target",
        )
    )

    introduce(world, student, teacher, mishap)
    world.para()
    first_case(world, teacher, mishap)

    world.para()
    pred = predict_consecutive(world, mishap)
    world.facts["predicted_second"] = pred["second_happens"]
    second_case(world, student, teacher, mishap)
    inspect(world, student, mishap, motive)

    world.para()
    reveal(world, student, teacher, motive)
    help_gremlin(world, student, teacher, motive, fix)

    world.facts.update(
        place=place,
        mishap=mishap,
        motive=motive,
        fix=fix,
        student=student,
        teacher=teacher,
        gremlin=gremlin,
        consecutive=thing.meters["mischief2"] >= THRESHOLD,
        solved=gremlin.meters["need"] == 0,
        clue=mishap.clue,
    )
    return world


KNOWLEDGE = {
    "gremlin": [
        (
            "What is a gremlin in a pretend story?",
            "A gremlin is a tiny make-believe creature that often causes little mix-ups. In stories, a gremlin can feel silly or sneaky, but it can still have ordinary needs like warmth or food.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and asks what happened. Good detectives pay attention before they decide who is to blame.",
        )
    ],
    "consecutive": [
        (
            "What does consecutive mean?",
            "Consecutive means one right after another with no gap between. Two consecutive mishaps happen two times in a row.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. Footprints, crumbs, and smudges can all be clues.",
        )
    ],
    "kindness": [
        (
            "Why can kindness solve a problem better than yelling?",
            "Kindness can help you learn what someone really needs. When you understand the cause, you can fix the problem instead of only getting mad at it.",
        )
    ],
    "pencils": [
        (
            "Why do classrooms need pencils?",
            "Pencils help students write, draw, and finish their work. When they go missing, the class can have trouble getting started.",
        )
    ],
    "chalk": [
        (
            "Why is a chalkboard useful in class?",
            "A chalkboard shows the lesson where everyone can see it together. If the writing is rubbed away, children can lose their place.",
        )
    ],
    "bookmarks": [
        (
            "What is a bookmark for?",
            "A bookmark keeps your place in a book. It helps you come back to the exact page later.",
        )
    ],
    "crayons": [
        (
            "Why do children sort crayons by color?",
            "Sorted crayons are easy to find when you need a color quickly. Mixing them up can slow an art project down.",
        )
    ],
    "warmth": [
        (
            "Why do small creatures look for warm places?",
            "Small bodies can get cold quickly, so warm places help them feel safe and comfortable. Warmth can matter a lot to tiny animals or pretend creatures.",
        )
    ],
    "food": [
        (
            "Why do hungry creatures make poor choices sometimes?",
            "When something is hungry, it may grab the nearest food-like thing without thinking well. Helping with the need can stop the trouble.",
        )
    ],
    "paper": [
        (
            "Why might a tiny creature want soft paper?",
            "Soft paper can make a small nest or bed. It is light, easy to carry, and cozy when tucked together.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "gremlin",
    "detective",
    "consecutive",
    "clue",
    "kindness",
    "pencils",
    "chalk",
    "bookmarks",
    "crayons",
    "warmth",
    "food",
    "paper",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    student = f["student"]
    mishap = f["mishap"]
    motive = f["motive"]
    place = f["place"]
    return [
        'Write a short detective story for a 3-to-5-year-old that includes the words "student", "consecutive", and "gremlin".',
        f"Tell a gentle school mystery where a student notices two consecutive cases of {mishap.label} in {place.label} and follows clues to a surprising gremlin.",
        f"Write a curiosity-driven detective story with a twist: everyone expects simple mischief, but the real answer is that the gremlin {motive.want_text}. Let the student solve it kindly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    student = f["student"]
    teacher = f["teacher"]
    mishap = f["mishap"]
    motive = f["motive"]
    fix = f["fix"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {student.id}, a student who noticed a mystery at school, and {teacher.label}, who listened carefully. It is also about a tiny gremlin whose trouble had a reason behind it.",
        ),
        (
            "What made the student act like a detective?",
            f"{student.id} saw two consecutive mishaps with {mishap.object_phrase}. That pattern made {student.pronoun('object')} curious, because it did not seem like an accident anymore.",
        ),
        (
            "What clue helped solve the mystery?",
            f"The clue was {f['clue']}. It showed that something small had been there, so {student.id} looked for a tiny culprit instead of blaming a big person or the wind.",
        ),
        (
            "What was the twist in the story?",
            f"The twist was that the gremlin was not causing trouble just to be naughty. {motive.reveal_text.split('. ')[-1] if '. ' in motive.reveal_text else motive.reveal_text}",
        ),
        (
            "How did the student solve the case?",
            f"{student.id} solved the case by understanding what the gremlin needed and then helping with {fix.label}. That stopped the mischief because the real cause was solved, not just covered up.",
        ),
        (
            "How did the story end?",
            f"It ended calmly, with the classroom settled and the gremlin cared for. {fix.ending_image}",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"gremlin", "detective", "consecutive", "clue", "kindness"}
    mishap = world.facts["mishap"]
    motive = world.facts["motive"]
    if mishap.id == "pencils":
        tags.add("pencils")
    elif mishap.id == "chalkboard":
        tags.add("chalk")
    elif mishap.id == "bookmarks":
        tags.add("bookmarks")
    elif mishap.id == "crayons":
        tags.add("crayons")
    tags |= motive.tags
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for ent in world.entities.values():
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  history: {world.history}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="classroom",
        mishap="pencils",
        motive="hungry",
        fix="crumb_plate",
        student_name="Lina",
        student_gender="girl",
        teacher_gender="teacher_f",
        trait="observant",
    ),
    StoryParams(
        place="library",
        mishap="bookmarks",
        motive="nest",
        fix="scrap_bin",
        student_name="Eli",
        student_gender="boy",
        teacher_gender="teacher_f",
        trait="patient",
    ),
    StoryParams(
        place="artroom",
        mishap="crayons",
        motive="cold",
        fix="warm_sock",
        student_name="Nora",
        student_gender="girl",
        teacher_gender="teacher_m",
        trait="curious",
    ),
    StoryParams(
        place="classroom",
        mishap="chalkboard",
        motive="cold",
        fix="warm_sock",
        student_name="Theo",
        student_gender="boy",
        teacher_gender="teacher_m",
        trait="thoughtful",
    ),
]


def explain_rejection(place_id: Optional[str], mishap_id: Optional[str], motive_id: Optional[str], fix_id: Optional[str]) -> str:
    if motive_id and fix_id:
        motive = MOTIVES[motive_id]
        if motive.fix_id != fix_id:
            expected = motive.fix_id
            return (
                f"(No story: the motive '{motive_id}' needs fix '{expected}', not '{fix_id}'. "
                "The solution has to match what the gremlin actually needs.)"
            )
    if place_id and mishap_id:
        place = PLACES[place_id]
        if mishap_id not in place.affords:
            return (
                f"(No story: {place.label} does not naturally support the mishap '{mishap_id}'. "
                f"Try one of: {', '.join(sorted(place.affords))}.)"
            )
    return "(No valid combination matches the given options.)"


ASP_RULES = r"""
has_fix(M, F) :- motive(M), required_fix(M, F).
valid(P, Mh, M) :- place(P), mishap(Mh), motive(M), affords(P, Mh), has_fix(M, _).

matched_fix :- chosen_motive(M), chosen_fix(F), required_fix(M, F).
outcome(solved) :- valid_choice, matched_fix.
valid_choice :- chosen_place(P), chosen_mishap(Mh), chosen_motive(M), valid(P, Mh, M).
bad_choice(place_mismatch) :- chosen_place(P), chosen_mishap(Mh), not affords(P, Mh).
bad_choice(fix_mismatch) :- chosen_motive(M), chosen_fix(F), not required_fix(M, F).
#show valid/3.
#show outcome/1.
#show bad_choice/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for mid in sorted(place.affords):
            lines.append(asp.fact("affords", pid, mid))
    for mid in MISHAPS:
        lines.append(asp.fact("mishap", mid))
    for motive_id, motive in MOTIVES.items():
        lines.append(asp.fact("motive", motive_id))
        lines.append(asp.fact("required_fix", motive_id, motive.fix_id))
    for fix_id in FIXES:
        lines.append(asp.fact("fix", fix_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> tuple[set[tuple], set[tuple]]:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_mishap", params.mishap),
            asp.fact("chosen_motive", params.motive),
            asp.fact("chosen_fix", params.fix),
        ]
    )
    model = asp.one_model(asp_program(extra))
    return set(asp.atoms(model, "outcome")), set(asp.atoms(model, "bad_choice"))


def outcome_of(params: StoryParams) -> str:
    if params.place not in PLACES or params.motive not in MOTIVES or params.fix not in FIXES or params.mishap not in MISHAPS:
        return "invalid"
    if params.mishap not in PLACES[params.place].affords:
        return "invalid"
    if MOTIVES[params.motive].fix_id != params.fix:
        return "invalid"
    return "solved"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - asp_set:
            print("  only in python:", sorted(py - asp_set))
        if asp_set - py:
            print("  only in asp:", sorted(asp_set - py))

    cases = list(CURATED)
    rng = random.Random(123)
    parser = build_parser()
    for i in range(12):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(rng.randint(0, 999999)))
        except StoryError:
            continue
        params.seed = i
        cases.append(params)

    for params in cases:
        py_out = outcome_of(params)
        asp_out, asp_bad = asp_outcome(params)
        asp_name = next(iter(asp_out))[0] if asp_out else "invalid"
        if py_out != asp_name:
            rc = 1
            print(f"MISMATCH outcome for {params}: python={py_out} asp={asp_name} bad={sorted(asp_bad)}")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a student detective solves two consecutive gremlin mishaps with curiosity and a twist."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--motive", choices=MOTIVES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--student-name")
    ap.add_argument("--student-gender", choices=["girl", "boy"])
    ap.add_argument("--teacher-gender", choices=["teacher_f", "teacher_m"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, mishap, motive) combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mishap and args.mishap not in PLACES[args.place].affords:
        raise StoryError(explain_rejection(args.place, args.mishap, args.motive, args.fix))
    if args.motive and args.fix and MOTIVES[args.motive].fix_id != args.fix:
        raise StoryError(explain_rejection(args.place, args.mishap, args.motive, args.fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.mishap is None or combo[1] == args.mishap)
        and (args.motive is None or combo[2] == args.motive)
    ]
    if not combos:
        raise StoryError(explain_rejection(args.place, args.mishap, args.motive, args.fix))

    place_id, mishap_id, motive_id = rng.choice(sorted(combos))
    motive = MOTIVES[motive_id]
    fix_id = args.fix or motive.fix_id
    if motive.fix_id != fix_id:
        raise StoryError(explain_rejection(place_id, mishap_id, motive_id, fix_id))

    student_gender = args.student_gender or rng.choice(["girl", "boy"])
    student_name = args.student_name or rng.choice(GIRL_NAMES if student_gender == "girl" else BOY_NAMES)
    teacher_gender = args.teacher_gender or rng.choice(["teacher_f", "teacher_m"])
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        mishap=mishap_id,
        motive=motive_id,
        fix=fix_id,
        student_name=student_name,
        student_gender=student_gender,
        teacher_gender=teacher_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.mishap not in MISHAPS:
        raise StoryError(f"Unknown mishap: {params.mishap}")
    if params.motive not in MOTIVES:
        raise StoryError(f"Unknown motive: {params.motive}")
    if params.fix not in FIXES:
        raise StoryError(f"Unknown fix: {params.fix}")
    if params.mishap not in PLACES[params.place].affords:
        raise StoryError(explain_rejection(params.place, params.mishap, params.motive, params.fix))
    if MOTIVES[params.motive].fix_id != params.fix:
        raise StoryError(explain_rejection(params.place, params.mishap, params.motive, params.fix))

    world = tell(
        place=PLACES[params.place],
        mishap=MISHAPS[params.mishap],
        motive=MOTIVES[params.motive],
        fix=FIXES[params.fix],
        student_name=params.student_name,
        student_gender=params.student_gender,
        teacher_gender=params.teacher_gender,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, mishap, motive) combos:\n")
        for place, mishap, motive in combos:
            print(f"  {place:10} {mishap:10} {motive}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.student_name}: {p.mishap} at {p.place} ({p.motive})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
