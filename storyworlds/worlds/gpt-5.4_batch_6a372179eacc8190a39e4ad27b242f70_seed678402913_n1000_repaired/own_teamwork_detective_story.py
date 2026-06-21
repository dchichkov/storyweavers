#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/own_teamwork_detective_story.py
==========================================================

A standalone story world for a tiny **teamwork detective story**: a child loses
their own special thing, jumps to a worried guess, then works with a friend to
follow clues and solve the small mystery. The ending proves that sharing ideas
beats blaming.

This world aims for a child-facing detective tone without danger or cruelty:
magnifying-glass curiosity, clue trails, whispered guesses, and a warm reveal.

Run it
------
    python storyworlds/worlds/gpt-5.4/own_teamwork_detective_story.py
    python storyworlds/worlds/gpt-5.4/own_teamwork_detective_story.py --place classroom --missing notebook --cause fan_blew
    python storyworlds/worlds/gpt-5.4/own_teamwork_detective_story.py --cause puppy_tugged --place classroom
    python storyworlds/worlds/gpt-5.4/own_teamwork_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/own_teamwork_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/own_teamwork_detective_story.py --trace
    python storyworlds/worlds/gpt-5.4/own_teamwork_detective_story.py --json
    python storyworlds/worlds/gpt-5.4/own_teamwork_detective_story.py --verify
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
# This file lives under storyworlds/worlds/gpt-5.4/, so climb three levels to
# the storyworlds/ package directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # girl, boy, item, place, clue, pet
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    label: str
    opening: str
    search_area: str
    ambient: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingThing:
    id: str
    label: str
    phrase: str
    special: str
    pronoun_word: str = "it"
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    mover: str
    trail: str
    clue_word: str
    clue_mark: str
    moved_sentence: str
    hideout: str
    reveal: str
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Skill:
    id: str
    label: str
    notice_text: str
    solve_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    missing: str
    cause: str
    helper_skill: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_hidden_item_worry(world: World) -> list[str]:
    hero = world.get("hero")
    item = world.get("item")
    if item.meters["hidden"] < THRESHOLD:
        return []
    sig = ("worry", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    return ["__missing__"]


def _r_clue_hope(world: World) -> list[str]:
    clue = world.get("clue")
    helper = world.get("helper")
    hero = world.get("hero")
    if clue.meters["noticed"] < THRESHOLD:
        return []
    sig = ("hope", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["focus"] += 1
    hero.memes["hope"] += 1
    return ["__clue__"]


def _r_found_relief(world: World) -> list[str]:
    item = world.get("item")
    hero = world.get("hero")
    helper = world.get("helper")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("relief", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["hidden"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["pride"] += 1
    hero.memes["trust"] += 1
    return ["__found__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="hidden_item_worry", tag="emotional", apply=_r_hidden_item_worry),
    Rule(name="clue_hope", tag="emotional", apply=_r_clue_hope),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
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
            if not sent.startswith("__"):
                world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Constraints and prediction
# ---------------------------------------------------------------------------
def valid_combo(place: str, cause: str) -> bool:
    return cause in SETTINGS[place].supports


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, setting in SETTINGS.items():
        for cause_id in CAUSES:
            if cause_id in setting.supports:
                combos.append((place_id, cause_id))
    return combos


def predict_path(world: World, cause: Cause) -> dict:
    sim = world.copy()
    sim.get("item").meters["hidden"] += 1
    sim.get("clue").attrs["trail"] = cause.trail
    sim.get("clue").attrs["mark"] = cause.clue_mark
    sim.get("clue").attrs["word"] = cause.clue_word
    propagate(sim, narrate=False)
    return {
        "trail": sim.get("clue").attrs.get("trail", ""),
        "worry": sim.get("hero").memes["worry"],
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def opening(world: World, hero: Entity, helper: Entity, item: Entity, setting: Setting) -> None:
    hero.memes["care"] += 1
    helper.memes["friendship"] += 1
    world.say(
        f"{setting.opening} {hero.id} carried {hero.pronoun('possessive')} own {item.label} "
        f"everywhere. {item.special}"
    )
    world.say(
        f"{helper.id} liked mysteries too, so the two friends had a habit of whispering, "
        f'"Case of the Day," whenever something puzzling happened.'
    )
    world.say(setting.ambient)


def disappearance(world: World, hero: Entity, item: Entity, cause: Cause, setting: Setting) -> None:
    item.meters["hidden"] += 1
    world.get("clue").attrs["trail"] = cause.trail
    world.get("clue").attrs["mark"] = cause.clue_mark
    world.get("clue").attrs["word"] = cause.clue_word
    propagate(world, narrate=False)
    world.say(
        f"When {hero.id} reached for {hero.pronoun('possessive')} {item.label} again, it was gone."
    )
    world.say(
        f"{hero.id} looked through {setting.search_area} and made a small, shocked circle with "
        f"{hero.pronoun('possessive')} mouth."
    )


def worried_guess(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    hero.memes["suspicion"] += 1
    world.say(
        f'"This is strange," {hero.id} whispered. "I had my own {item.label} right here."'
    )
    world.say(
        f"For one worried moment, {hero.pronoun()} wondered if somebody had taken it by mistake."
    )
    helper.memes["calm"] += 1
    world.say(
        f'But {helper.id} touched {hero.pronoun("possessive")} sleeve and said, '
        f'"Real detectives look for clues before they blame anyone."'
    )


def notice_clue(world: World, hero: Entity, helper: Entity, skill: Skill, clue: Entity, cause: Cause) -> None:
    pred = predict_path(world, cause)
    clue.meters["noticed"] += 1
    propagate(world, narrate=False)
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f"Then {helper.id} crouched low. {skill.notice_text} Near the floor was {cause.trail}."
    )
    world.say(
        f'"{cause.clue_word.capitalize()}!" {helper.id} said. "That is our first clue."'
    )
    hero.memes["suspicion"] = 0.0
    hero.memes["focus"] += 1


def follow_trail(world: World, hero: Entity, helper: Entity, cause: Cause, setting: Setting) -> None:
    hero.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    world.say(
        f"{hero.id} and {helper.id} became a detective team at once. "
        f"One pointed out where the marks began, and the other checked where they led."
    )
    world.say(
        f"They followed the trail past {setting.search_area} until it ended by {cause.hideout}."
    )


def solve_case(world: World, hero: Entity, helper: Entity, item: Entity, cause: Cause, skill: Skill) -> None:
    world.say(skill.solve_text.format(cause_mover=cause.mover, hideout=cause.hideout))
    item.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        cause.reveal.format(item=item.label)
    )
    world.say(
        f"{hero.id} hugged the {item.label} to {hero.pronoun('possessive')} chest and let out a happy laugh."
    )


def lesson(world: World, hero: Entity, helper: Entity, parent: Entity, item: Entity) -> None:
    hero.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    hero.memes["gratitude"] += 1
    world.say(
        f'"We solved it," {hero.id} said, grinning. "It was not a thief at all. It was a clue trail."'
    )
    world.say(
        f'{parent.label_word.capitalize()} smiled and said, "That is what good detectives do. '
        f'They use patient eyes, kind words, and help from a friend."'
    )
    world.say(
        f"{helper.id} gave a tiny bow. {hero.id} promised to check carefully next time before worrying "
        f"about {hero.pronoun('possessive')} own missing things."
    )


def ending_image(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"After that, they made a paper sign that said DETECTIVE CLUB and set {item.phrase} in the middle "
        f"like a solved treasure."
    )
    world.say(
        f"The mystery was over, but the team stayed: two small detectives, one found clue, and one very safe "
        f"{item.label} resting where everyone could see it."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    missing_cfg: MissingThing,
    cause: Cause,
    skill: Skill,
    hero_name: str,
    hero_gender: str,
    helper_name: str,
    helper_gender: str,
    parent_type: str,
) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_gender,
        label=helper_name,
        phrase=helper_name,
        role="helper",
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        phrase="the parent",
        role="parent",
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        label=missing_cfg.label,
        phrase=missing_cfg.phrase,
        role="missing",
        owner="hero",
        tags=set(missing_cfg.tags),
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label="clue",
        phrase="a clue",
        role="clue",
        tags=set(cause.tags),
    ))

    opening(world, hero, helper, item, setting)
    world.para()
    disappearance(world, hero, item, cause, setting)
    worried_guess(world, hero, helper, item)
    world.para()
    notice_clue(world, hero, helper, skill, clue, cause)
    follow_trail(world, hero, helper, cause, setting)
    world.para()
    solve_case(world, hero, helper, item, cause, skill)
    lesson(world, hero, helper, parent, item)
    world.para()
    ending_image(world, hero, helper, item)

    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        item=item,
        clue=clue,
        setting=setting,
        missing_cfg=missing_cfg,
        cause=cause,
        skill=skill,
        solved=item.meters["found"] >= THRESHOLD,
        worried_first=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "classroom": Setting(
        id="classroom",
        label="classroom",
        opening="On a bright school morning in the classroom,",
        search_area="the reading rug, the cubbies, and the art shelf",
        ambient="Sunlight lay on the tables, and the little room felt full of secrets worth solving.",
        supports={"fan_blew", "teacher_stack"},
        tags={"classroom"},
    ),
    "library": Setting(
        id="library",
        label="library",
        opening="One quiet afternoon in the library corner,",
        search_area="the beanbag chair, the low shelf, and the book cart",
        ambient="The pages around them gave soft paper sighs, like a room whispering clues.",
        supports={"fan_blew", "book_cart_bump"},
        tags={"library"},
    ),
    "yard": Setting(
        id="yard",
        label="school yard",
        opening="At recess in the school yard,",
        search_area="the bench, the sandbox edge, and the little fence",
        ambient="Leaves skipped over the ground, and every corner looked like part of a puzzle.",
        supports={"wind_skipped", "puppy_tugged"},
        tags={"yard"},
    ),
}

MISSING = {
    "notebook": MissingThing(
        id="notebook",
        label="notebook",
        phrase="the striped detective notebook",
        special="Inside it, there were careful drawings of clues, suspects, and snack crumbs.",
        tags={"notebook", "writing"},
    ),
    "magnifier": MissingThing(
        id="magnifier",
        label="magnifying glass",
        phrase="the round magnifying glass",
        special="It made small specks look huge, which felt very important to a young detective.",
        tags={"magnifier", "detective"},
    ),
    "badge": MissingThing(
        id="badge",
        label="detective badge",
        phrase="the shiny paper detective badge",
        special="It had a gold star drawn in marker and the words BEST CLUE FINDER across the middle.",
        tags={"badge", "detective"},
    ),
}

CAUSES = {
    "fan_blew": Cause(
        id="fan_blew",
        mover="a whirring fan",
        trail="a fluttering paper edge and a line of tiny slides in the dust",
        clue_word="paper marks",
        clue_mark="slides",
        moved_sentence="A fan breeze can push light things away from the spot where they were left.",
        hideout="the leg of a low shelf",
        reveal="There was the {item}, slid neatly under the shelf where the breeze had shushed it away.",
        needs={"classroom", "library"},
        tags={"fan", "air"},
    ),
    "teacher_stack": Cause(
        id="teacher_stack",
        mover="a careful stack of class papers",
        trail="a corner peeking from under a tidy pile",
        clue_word="peek",
        clue_mark="peek",
        moved_sentence="When papers are gathered into a stack, one small thing can hide under them without anyone noticing.",
        hideout="a tall stack of worksheets",
        reveal="Tucked under the stack was the {item}, flat and patient, waiting to be noticed.",
        needs={"classroom"},
        tags={"papers", "classroom"},
    ),
    "book_cart_bump": Cause(
        id="book_cart_bump",
        mover="a rolling book cart",
        trail="little wheel lines and one bright corner near the shelf",
        clue_word="wheel lines",
        clue_mark="wheels",
        moved_sentence="A moving cart can nudge a small object until it slips into a narrow space.",
        hideout="the shadow behind the book cart",
        reveal="Behind the cart gleamed the {item}, bumped into hiding but safe all along.",
        needs={"library"},
        tags={"books", "wheels"},
    ),
    "wind_skipped": Cause(
        id="wind_skipped",
        mover="a playful gust of wind",
        trail="dancing leaf scratches leading away from the bench",
        clue_word="leaf scratches",
        clue_mark="leaves",
        moved_sentence="A gust can make a light object skitter and skip farther than a child expects.",
        hideout="the roots beside the little fence",
        reveal="By the roots rested the {item}, where the wind had skipped it and left it still.",
        needs={"yard"},
        tags={"wind", "leaves"},
    ),
    "puppy_tugged": Cause(
        id="puppy_tugged",
        mover="the teacher's puppy",
        trail="small paw prints and a chewed ribbon scrap",
        clue_word="paw prints",
        clue_mark="paws",
        moved_sentence="A curious puppy may tug a dangling thing and carry it to a cozy corner.",
        hideout="the shady spot under the bench",
        reveal="Under the bench lay the {item}, beside a wagging puppy who looked very pleased with the mystery.",
        needs={"yard"},
        tags={"puppy", "paw"},
    ),
}

SKILLS = {
    "sharp_eyes": Skill(
        id="sharp_eyes",
        label="sharp eyes",
        notice_text="With sharp eyes, the helper noticed the smallest crooked bit that did not belong",
        solve_text="Using {cause_mover} as the answer, the team checked {hideout} next.",
        tags={"observation"},
    ),
    "good_memory": Skill(
        id="good_memory",
        label="good memory",
        notice_text="Because the helper had a good memory, the helper remembered exactly what the floor had looked like a minute before",
        solve_text="Remembering what had changed, the team guessed that {cause_mover} had sent the object toward {hideout}.",
        tags={"memory"},
    ),
    "careful_listening": Skill(
        id="careful_listening",
        label="careful listening",
        notice_text="With careful listening, the helper matched the little sounds in the room to the mystery",
        solve_text="They listened, thought, and decided that {cause_mover} fit the clue trail leading to {hideout}.",
        tags={"listening"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "detective": [(
        "What does a detective do?",
        "A detective looks carefully for clues and uses those clues to solve a mystery. Good detectives do not just guess; they notice, think, and check."
    )],
    "magnifier": [(
        "What is a magnifying glass for?",
        "A magnifying glass makes small things look bigger so you can see details more clearly. People use it to inspect tiny marks and clues."
    )],
    "notebook": [(
        "Why do detectives use notebooks?",
        "A notebook helps detectives remember clues, questions, and ideas. Writing things down keeps small details from being forgotten."
    )],
    "badge": [(
        "What is a badge?",
        "A badge is a small sign or token that shows a job, team, or role. In pretend play, a detective badge helps children feel ready for a case."
    )],
    "fan": [(
        "How can a fan move paper?",
        "A fan pushes air, and moving air can slide or flutter light paper across a table or floor. That is why loose papers can travel when a fan is on."
    )],
    "wind": [(
        "What can wind do to light things?",
        "Wind can lift, push, or skip light things across the ground. Leaves, paper, and ribbons can move farther than you expect."
    )],
    "paw": [(
        "What are paw prints?",
        "Paw prints are the marks an animal's feet leave behind on dust, mud, or sand. They can show where the animal walked."
    )],
    "teamwork": [(
        "What is teamwork?",
        "Teamwork is when two or more people help each other to do something well. One person may notice one part, and another person may notice another part."
    )],
    "library": [(
        "Why is a library a good place to read?",
        "A library is full of books and is usually calm and quiet. That makes it a good place to sit, read, and think."
    )],
    "classroom": [(
        "What do children do in a classroom?",
        "Children learn, read, write, and work together in a classroom. It is a place for lessons, questions, and sharing ideas."
    )],
    "yard": [(
        "What can you find in a school yard?",
        "A school yard often has open space to run and play, plus benches, fences, and leaves or sand. Those things can also leave interesting little clues."
    )],
}
KNOWLEDGE_ORDER = [
    "detective", "teamwork", "magnifier", "notebook", "badge",
    "fan", "wind", "paw", "library", "classroom", "yard",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item = f["item"]
    setting = f["setting"]
    cause = f["cause"]
    return [
        f'Write a short detective story for a 3-to-5-year-old that includes the word "own" and shows teamwork.',
        f"Tell a gentle mystery where {hero.label} loses {hero.pronoun('possessive')} own {item.label} in the {setting.label}, and a friend helps solve the case by following clues.",
        f"Write a child-facing detective story in which {helper.label} helps notice {cause.clue_word}, the mystery is solved kindly, and nobody is blamed unfairly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    item = f["item"]
    setting = f["setting"]
    cause = f["cause"]
    skill = f["skill"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, {helper.label}, and {hero.label}'s missing {item.label}. They become a detective team in the {setting.label}."
        ),
        (
            f"What went missing?",
            f"{hero.label}'s own {item.label} went missing. That is why the small detective mystery began."
        ),
        (
            f"Why was {hero.label} worried at first?",
            f"{hero.label} had just had the {item.label}, and then it was suddenly gone. For a moment, {hero.pronoun()} worried that somebody had taken it by mistake before any clues were checked."
        ),
        (
            f"How did {helper.label} help solve the mystery?",
            f"{helper.label} used {skill.label} to notice {cause.clue_word}. That clue changed the search from a worried guess into a real investigation."
        ),
        (
            "What clue did they follow?",
            f"They followed {cause.trail}. The trail showed that something in the place had moved the {item.label} instead of a person stealing it."
        ),
        (
            "Where did they find the missing thing?",
            f"They found it by {cause.hideout}. It had been moved there by {cause.mover}, which matched the clue trail they noticed."
        ),
        (
            "What did the children learn?",
            f"They learned to work together and look for clues before blaming anyone. Teamwork helped them solve the mystery kindly and calmly."
        ),
    ]
    if parent.type in {"mother", "father"}:
        qa.append((
            f"What did {parent.label_word} say at the end?",
            f"{parent.label_word.capitalize()} said that good detectives use patient eyes, kind words, and help from a friend. That made the ending feel proud and safe instead of scary."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"detective", "teamwork"}
    tags |= set(f["missing_cfg"].tags)
    tags |= set(f["cause"].tags)
    tags |= set(f["setting"].tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="classroom",
        missing="notebook",
        cause="teacher_stack",
        helper_skill="sharp_eyes",
        hero_name="Lily",
        hero_gender="girl",
        helper_name="Max",
        helper_gender="boy",
        parent="mother",
    ),
    StoryParams(
        place="library",
        missing="magnifier",
        cause="book_cart_bump",
        helper_skill="good_memory",
        hero_name="Ben",
        hero_gender="boy",
        helper_name="Mia",
        helper_gender="girl",
        parent="father",
    ),
    StoryParams(
        place="yard",
        missing="badge",
        cause="wind_skipped",
        helper_skill="careful_listening",
        hero_name="Nora",
        hero_gender="girl",
        helper_name="Theo",
        helper_gender="boy",
        parent="mother",
    ),
    StoryParams(
        place="yard",
        missing="notebook",
        cause="puppy_tugged",
        helper_skill="sharp_eyes",
        hero_name="Sam",
        hero_gender="boy",
        helper_name="Lucy",
        helper_gender="girl",
        parent="father",
    ),
]


# ---------------------------------------------------------------------------
# Rejections
# ---------------------------------------------------------------------------
def explain_rejection(place: str, cause: str) -> str:
    setting = SETTINGS[place]
    cause_cfg = CAUSES[cause]
    return (
        f"(No story: {cause_cfg.mover} does not fit the {setting.label}. "
        f"Choose a cause the place can honestly support.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
supports_place(P, C) :- setting(P), cause(C), allowed(P, C).
valid(P, C) :- supports_place(P, C).

solved :- chosen_place(P), chosen_cause(C), valid(P, C).
:- chosen_place(P), chosen_cause(C), not valid(P, C).

outcome(solved) :- solved.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in SETTINGS:
        lines.append(asp.fact("setting", place_id))
    for cause_id in CAUSES:
        lines.append(asp.fact("cause", cause_id))
    for place_id, setting in SETTINGS.items():
        for cause_id in sorted(setting.supports):
            lines.append(asp.fact("allowed", place_id, cause_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_cause", params.cause),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    for params in CURATED[:2]:
        expected = "solved"
        actual = asp_outcome(params)
        if actual != expected:
            rc = 1
            print(f"MISMATCH in outcome for {params.place}/{params.cause}: {actual} != {expected}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        emit(sample, trace=False, qa=False, header="### verify smoke test")
        print("OK: smoke test story generated and emitted.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Teamwork detective story world. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--helper-skill", choices=SKILLS, dest="helper_skill")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.cause and not valid_combo(args.place, args.cause):
        raise StoryError(explain_rejection(args.place, args.cause))

    allowed_places = [p for p in SETTINGS if args.place is None or p == args.place]
    allowed_causes = [c for c in CAUSES if args.cause is None or c == args.cause]
    pair_choices = [(p, c) for (p, c) in valid_combos() if p in allowed_places and c in allowed_causes]
    if not pair_choices:
        raise StoryError("(No valid combination matches the given options.)")

    place, cause = rng.choice(sorted(pair_choices))
    missing = args.missing or rng.choice(sorted(MISSING))
    helper_skill = args.helper_skill or rng.choice(sorted(SKILLS))
    hero_name, hero_gender = _pick_child(rng)
    helper_name, helper_gender = _pick_child(rng, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        missing=missing,
        cause=cause,
        helper_skill=helper_skill,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.missing not in MISSING:
        raise StoryError(f"(Unknown missing thing: {params.missing})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.helper_skill not in SKILLS:
        raise StoryError(f"(Unknown helper skill: {params.helper_skill})")
    if not valid_combo(params.place, params.cause):
        raise StoryError(explain_rejection(params.place, params.cause))

    world = tell(
        setting=SETTINGS[params.place],
        missing_cfg=MISSING[params.missing],
        cause=CAUSES[params.cause],
        skill=SKILLS[params.helper_skill],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
    )
    # Patch labels for prose/QA readability while keeping stable ids in the world.
    world.get("hero").label = params.hero_name
    world.get("hero").phrase = params.hero_name
    world.get("helper").label = params.helper_name
    world.get("helper").phrase = params.helper_name

    story = world.render().replace("hero", params.hero_name).replace("helper", params.helper_name)

    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, cause) combos:\n")
        for place, cause in combos:
            print(f"  {place:10} {cause}")
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
            header = f"### {p.hero_name} and {p.helper_name}: {p.missing} at {p.place} ({p.cause})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
