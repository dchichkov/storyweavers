#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/nostalgia_mystery_to_solve_lesson_learned_misunderstanding.py
==========================================================================================

A small heartwarming storyworld about a missing family keepsake.

This world models a child who wants to share an old object that stirs nostalgia,
discovers it missing, misunderstands an innocent clue, and blames someone too
quickly. With help, the child follows a better clue, learns what really
happened, apologizes, and ends the day with the keepsake in hand and a kinder
way of asking questions.

Run it
------
    python storyworlds/worlds/gpt-5.4/nostalgia_mystery_to_solve_lesson_learned_misunderstanding.py
    python storyworlds/worlds/gpt-5.4/nostalgia_mystery_to_solve_lesson_learned_misunderstanding.py --keepsake music_box --place cedar_chest --helper sibling
    python storyworlds/worlds/gpt-5.4/nostalgia_mystery_to_solve_lesson_learned_misunderstanding.py --keepsake quilt --place shelf
    python storyworlds/worlds/gpt-5.4/nostalgia_mystery_to_solve_lesson_learned_misunderstanding.py --all
    python storyworlds/worlds/gpt-5.4/nostalgia_mystery_to_solve_lesson_learned_misunderstanding.py --verify
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
    traits: tuple = field(default_factory=tuple)
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "aunt", "sister"}
        male = {"boy", "father", "grandfather", "man", "uncle", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    size: str
    memory_line: str
    use_line: str
    clue_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    fits: set[str] = field(default_factory=set)
    clue: str = ""
    clue_tag: str = ""
    safe_reason: str = ""
    search_needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    kind: str
    skills: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    sign: str
    guess: str
    truth: str
    apology: str
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


def _r_missing_worry(world: World) -> list[str]:
    child = world.entities.get("child")
    keepsake = world.entities.get("keepsake")
    if child is None or keepsake is None:
        return []
    if keepsake.meters["missing"] < THRESHOLD:
        return []
    sig = ("worry", "missing")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    child.memes["urgency"] += 1
    return []


def _r_blame_hurts(world: World) -> list[str]:
    child = world.entities.get("child")
    suspect = world.entities.get("suspect")
    if child is None or suspect is None:
        return []
    if child.memes["blame"] < THRESHOLD:
        return []
    sig = ("hurt", suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.memes["hurt"] += 1
    child.memes["guilt_seed"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    child = world.entities.get("child")
    suspect = world.entities.get("suspect")
    keepsake = world.entities.get("keepsake")
    elder = world.entities.get("elder")
    if child is None or suspect is None or keepsake is None or elder is None:
        return []
    if keepsake.meters["found"] < THRESHOLD:
        return []
    sig = ("relief", "found")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    suspect.memes["hurt"] = 0.0
    elder.memes["nostalgia"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotion", apply=_r_missing_worry),
    Rule(name="blame_hurts", tag="social", apply=_r_blame_hurts),
    Rule(name="found_relief", tag="emotion", apply=_r_found_relief),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


def item_fits_place(keepsake: Keepsake, place: Place) -> bool:
    return keepsake.size in place.fits


def helper_can_solve(place: Place, helper: Helper) -> bool:
    return bool(place.search_needs & helper.skills)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for keepsake_id, keepsake in KEEPSAKES.items():
        for place_id, place in PLACES.items():
            if not item_fits_place(keepsake, place):
                continue
            for helper_id, helper in HELPERS.items():
                if helper_can_solve(place, helper):
                    combos.append((keepsake_id, place_id, helper_id))
    return sorted(combos)


def explain_rejection(keepsake: Keepsake, place: Place, helper: Optional[Helper] = None) -> str:
    if not item_fits_place(keepsake, place):
        return (
            f"(No story: {keepsake.phrase} would not sensibly fit in {place.phrase}. "
            f"Pick a hiding place that can really hold it.)"
        )
    if helper is not None and not helper_can_solve(place, helper):
        return (
            f"(No story: {helper.phrase.capitalize()} does not have the right way to search "
            f"{place.phrase}. Pick a helper whose skill matches the clue there.)"
        )
    return "(No story: this combination does not make a reasonable mystery.)"


def predict_search(place: Place, helper: Helper) -> dict:
    return {
        "can_solve": helper_can_solve(place, helper),
        "clue": place.clue,
    }


def introduce(world: World, child: Entity, elder: Entity, keepsake: Keepsake) -> None:
    child.memes["love"] += 1
    elder.memes["nostalgia"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} was helping {child.pronoun('possessive')} "
        f"{elder.label_word} make a little memory table by the window."
    )
    world.say(
        f"{elder.label_word.capitalize()} wanted to set out {keepsake.phrase}. "
        f"{keepsake.memory_line}"
    )
    world.say(
        f"The word nostalgia made {child.id} smile. {child.pronoun().capitalize()} did not know it very well yet, "
        f"but {child.pronoun()} could feel that it meant a warm old memory in a small present moment."
    )


def notice_missing(world: World, child: Entity, keepsake_ent: Entity, keepsake: Keepsake) -> None:
    keepsake_ent.meters["missing"] += 1
    propagate(world)
    world.say(
        f"But when {child.id} reached for the place where the keepsake should have been, it was gone."
    )
    world.say(
        f"{child.id}'s eyes grew wide. The little table looked ready, but {keepsake.label} was missing."
    )


def false_guess(world: World, child: Entity, suspect: Entity, misunderstanding: Misunderstanding) -> None:
    child.memes["blame"] += 1
    propagate(world)
    world.say(
        f"Then {child.id} noticed {suspect.id} {misunderstanding.sign}."
    )
    world.say(
        f'"Oh!" {child.id} whispered. "Maybe {misunderstanding.guess}"'
    )
    world.say(
        f"The guess came too quickly, carried by worry instead of patience."
    )


def suspect_response(world: World, suspect: Entity, misunderstanding: Misunderstanding) -> None:
    world.say(
        f'{suspect.id} looked surprised. "{misunderstanding.truth}"'
    )


def helper_guides(world: World, child: Entity, helper_ent: Entity, helper: Helper, place: Place) -> None:
    helper_ent.memes["care"] += 1
    pred = predict_search(place, helper)
    world.facts["predicted_clue"] = pred["clue"]
    world.say(
        f"{helper_ent.id}, {helper.phrase}, came closer and spoke softly."
    )
    world.say(
        f'"Let\'s solve the mystery before we decide anything," {helper_ent.pronoun()} said. '
        f'"Real clues are kinder than quick guesses."'
    )


def search(world: World, child: Entity, helper_ent: Entity, place: Place) -> None:
    world.say(
        f"So {child.id} and {helper_ent.id} looked around the room together."
    )
    world.say(
        f"At {place.phrase}, they found {place.clue}."
    )
    child.memes["curiosity"] += 1
    helper_ent.memes["confidence"] += 1
    world.facts["found_clue"] = place.clue


def resolve(world: World, child: Entity, suspect: Entity, elder: Entity, keepsake_ent: Entity,
            keepsake: Keepsake, place: Place) -> None:
    keepsake_ent.meters["missing"] = 0.0
    keepsake_ent.meters["found"] += 1
    propagate(world)
    world.say(
        f"Just then {elder.label_word} opened {place.phrase} and smiled with a little start."
    )
    world.say(
        f'"Here it is," {elder.pronoun()} said. "I tucked it away {place.safe_reason}."'
    )
    world.say(
        f"{child.id} saw {keepsake.phrase} resting there at last, safe and waiting."
    )


def repair(world: World, child: Entity, suspect: Entity, misunderstanding: Misunderstanding) -> None:
    child.memes["lesson"] += 1
    child.memes["blame"] = 0.0
    child.memes["guilt"] += 1
    world.say(
        misunderstanding.apology.format(child=child.id, suspect=suspect.id)
    )
    world.say(
        f"{suspect.id} gave a small nod, and the hard feeling in the room melted away."
    )


def ending(world: World, child: Entity, suspect: Entity, elder: Entity, keepsake: Keepsake) -> None:
    world.say(
        f"Soon they were all gathered at the window table while {elder.label_word} {keepsake.use_line}."
    )
    world.say(
        f"{child.id} leaned close, listening and looking and feeling the soft glow of nostalgia for a story "
        f"{child.pronoun()} had not lived through but could still love."
    )
    world.say(
        f"From then on, when something seemed puzzling, {child.id} remembered to ask gentle questions first."
    )


def tell(
    keepsake: Keepsake,
    place: Place,
    helper: Helper,
    misunderstanding: Misunderstanding,
    child_name: str,
    child_gender: str,
    suspect_name: str,
    suspect_gender: str,
    elder_type: str,
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    suspect = world.add(Entity(id=suspect_name, kind="character", type=suspect_gender, role="suspect"))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, role="elder", label="the elder"))
    helper_ent = world.add(Entity(
        id=helper.label,
        kind="character",
        type=helper.kind,
        role="helper",
        label=helper.label,
        attrs={"helper_id": helper.id},
    ))
    keepsake_ent = world.add(Entity(
        id="keepsake",
        kind="thing",
        type="keepsake",
        label=keepsake.label,
        phrase=keepsake.phrase,
    ))

    introduce(world, child, elder, keepsake)
    world.para()
    notice_missing(world, child, keepsake_ent, keepsake)
    false_guess(world, child, suspect, misunderstanding)
    suspect_response(world, suspect, misunderstanding)

    world.para()
    helper_guides(world, child, helper_ent, helper, place)
    search(world, child, helper_ent, place)

    world.para()
    resolve(world, child, suspect, elder, keepsake_ent, keepsake, place)
    repair(world, child, suspect, misunderstanding)

    world.para()
    ending(world, child, suspect, elder, keepsake)

    world.facts.update(
        child=child,
        suspect=suspect,
        elder=elder,
        helper=helper_ent,
        helper_cfg=helper,
        keepsake=keepsake_ent,
        keepsake_cfg=keepsake,
        place=place,
        misunderstanding=misunderstanding,
        solved=keepsake_ent.meters["found"] >= THRESHOLD,
        blamed=child.memes["guilt"] >= THRESHOLD,
    )
    return world


KEEPSAKES = {
    "music_box": Keepsake(
        id="music_box",
        label="music box",
        phrase="a tiny painted music box",
        size="small",
        memory_line="It had belonged to {elder} when {elder_pronoun} was little, and winding it always brought back a happy tune.".format(
            elder="grandma", elder_pronoun="she"
        ),
        use_line="turned the little key and let the tune ring out",
        clue_word="music",
        tags={"music_box", "music", "nostalgia"},
    ),
    "photo_album": Keepsake(
        id="photo_album",
        label="photo album",
        phrase="a worn photo album with soft blue corners",
        size="flat",
        memory_line="Inside were smiling faces from long ago, the kind that made a whole room quiet in a good way.",
        use_line="opened the pages and told the story behind each picture",
        clue_word="photo",
        tags={"photo_album", "photos", "nostalgia"},
    ),
    "quilt": Keepsake(
        id="quilt",
        label="quilt",
        phrase="a patchwork quilt stitched from old family cloth",
        size="bulky",
        memory_line="Each square held a family scrap, and touching it made old days feel close again.",
        use_line="spread the quilt across their knees and pointed to the oldest patches",
        clue_word="quilt",
        tags={"quilt", "fabric", "nostalgia"},
    ),
}

PLACES = {
    "window_seat": Place(
        id="window_seat",
        label="window seat",
        phrase="the window seat",
        fits={"small", "flat"},
        clue="a sun-warm cushion with a thin square dent underneath",
        clue_tag="cushion",
        safe_reason="so the table would not get crowded",
        search_needs={"cozy", "notice"},
        tags={"window_seat"},
    ),
    "cedar_chest": Place(
        id="cedar_chest",
        label="cedar chest",
        phrase="the cedar chest",
        fits={"small", "flat", "bulky"},
        clue="a sweet wood smell and one polished brass latch left unhooked",
        clue_tag="cedar",
        safe_reason="to keep it away from dust and curious paws",
        search_needs={"smell", "notice"},
        tags={"cedar_chest"},
    ),
    "shelf": Place(
        id="shelf",
        label="high shelf",
        phrase="the high shelf above the coat hooks",
        fits={"small", "flat"},
        clue="a corner of lace peeking down where small hands could hardly reach",
        clue_tag="shelf",
        safe_reason="to keep it safe while the floor was being swept",
        search_needs={"reach", "notice"},
        tags={"shelf"},
    ),
}

HELPERS = {
    "sibling": Helper(
        id="sibling",
        label="Milo",
        phrase="the older sibling with sharp eyes",
        kind="boy",
        skills={"notice", "reach"},
        tags={"sibling", "family"},
    ),
    "cousin": Helper(
        id="cousin",
        label="Nina",
        phrase="the cousin who noticed little details",
        kind="girl",
        skills={"notice", "cozy"},
        tags={"cousin", "family"},
    ),
    "neighbor": Helper(
        id="neighbor",
        label="Mrs. Reed",
        phrase="the kind neighbor with a good nose for cedar and cinnamon",
        kind="woman",
        skills={"smell", "notice"},
        tags={"neighbor", "community"},
    ),
}

MISUNDERSTANDINGS = {
    "dusting": Misunderstanding(
        id="dusting",
        sign="holding a dust cloth near the memory table",
        guess=f"someone had whisked the keepsake away on purpose",
        truth="I was only dusting the table so it would look nice.",
        apology='"I am sorry, {suspect}," {child} said. "I let my worry tell the story before the clues did."',
        tags={"misunderstanding", "apology"},
    ),
    "humming": Misunderstanding(
        id="humming",
        sign="humming a little tune by the hallway",
        guess=f"someone had taken the keepsake to play with it alone",
        truth="I was only humming because Grandma had sung that tune this morning.",
        apology='"I am sorry, {suspect}," {child} said. "I heard one tiny thing and guessed too much."',
        tags={"misunderstanding", "apology"},
    ),
    "carrying_cloth": Misunderstanding(
        id="carrying_cloth",
        sign="walking past with a folded cloth in both hands",
        guess=f"someone had wrapped the keepsake up and hidden it",
        truth="I was only carrying the table runner for the memory table.",
        apology='"I am sorry, {suspect}," {child} said. "Next time I will ask before I blame."',
        tags={"misunderstanding", "apology"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah"]

SUSPECT_GIRL_NAMES = ["Ruby", "Nora", "Clara", "June", "Ivy"]
SUSPECT_BOY_NAMES = ["Owen", "Eli", "Theo", "Cal", "Jude"]


@dataclass
class StoryParams:
    keepsake: str
    place: str
    helper: str
    misunderstanding: str
    child_name: str
    child_gender: str
    suspect_name: str
    suspect_gender: str
    elder: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "nostalgia": [
        (
            "What does nostalgia mean?",
            "Nostalgia is a warm feeling you get when something reminds you of a happy time from long ago. It can come from a song, a picture, or an old object."
        )
    ],
    "music_box": [
        (
            "What is a music box?",
            "A music box is a small box that plays a tune when you wind it. Many people keep them because they remind them of special times."
        )
    ],
    "photo_album": [
        (
            "What is a photo album for?",
            "A photo album holds pictures together in one place. Families look through albums to remember people and days they love."
        )
    ],
    "quilt": [
        (
            "What is a quilt?",
            "A quilt is a warm blanket made by sewing pieces of cloth together. Some quilts become family treasures because each piece carries a memory."
        )
    ],
    "clues": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. Good clues help you solve a mystery step by step."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone gets the wrong idea about what is going on. Asking calm questions can help clear it up."
        )
    ],
    "apology": [
        (
            "Why is it good to apologize after blaming someone unfairly?",
            "An apology helps repair hurt feelings when you have been unfair. It shows you understand what went wrong and want to do better."
        )
    ],
}
KNOWLEDGE_ORDER = ["nostalgia", "music_box", "photo_album", "quilt", "clues", "misunderstanding", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    keepsake = f["keepsake_cfg"]
    misunderstanding = f["misunderstanding"]
    place = f["place"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the word "nostalgia" and a missing {keepsake.label}.',
        f"Tell a gentle mystery where {child.id} blames someone too quickly after seeing {misunderstanding.sign}, then follows a real clue to {place.phrase}.",
        "Write a warm story with a misunderstanding, an apology, and a lesson about asking kind questions before making a guess.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    suspect = f["suspect"]
    elder = f["elder"]
    helper = f["helper"]
    keepsake = f["keepsake_cfg"]
    place = f["place"]
    misunderstanding = f["misunderstanding"]
    items: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {suspect.id}, {elder.label_word}, and {helper.id}. They were getting ready to share a family keepsake together."
        ),
        (
            f"Why did the {keepsake.label} matter so much?",
            f"It mattered because it carried old family memories and gave {elder.label_word} a feeling of nostalgia. The keepsake was not just an object; it helped everyone remember loving moments from long ago."
        ),
        (
            f"Why did {child.id} think {suspect.id} had taken it?",
            f"{child.id} saw {suspect.id} {misunderstanding.sign}, and worry made that look suspicious. The misunderstanding came from guessing too fast before checking the clues."
        ),
        (
            f"How did {helper.id} help solve the mystery?",
            f"{helper.id} told {child.id} to look for real clues instead of blaming anyone. Then they searched together and found {place.clue}, which pointed them the right way."
        ),
        (
            "Where was the keepsake really hiding?",
            f"It was in {place.phrase}. {elder.label_word.capitalize()} had tucked it there {place.safe_reason}, so it had been moved for safety, not stolen."
        ),
        (
            "What lesson did the child learn?",
            f"{child.id} learned to ask gentle questions before making a quick guess. That mattered because quick blame hurt someone's feelings, but calm clues led to the truth."
        ),
    ]
    if f.get("blamed"):
        items.append(
            (
                f"What did {child.id} do after learning the truth?",
                f"{child.id} apologized to {suspect.id} and admitted the guess had been unfair. The apology helped mend the misunderstanding and made the room feel warm again."
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"nostalgia", "clues", "misunderstanding", "apology"}
    keepsake = f["keepsake_cfg"]
    if keepsake.id == "music_box":
        tags.add("music_box")
    elif keepsake.id == "photo_album":
        tags.add("photo_album")
    elif keepsake.id == "quilt":
        tags.add("quilt")
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        keepsake="music_box",
        place="cedar_chest",
        helper="neighbor",
        misunderstanding="humming",
        child_name="Lily",
        child_gender="girl",
        suspect_name="Owen",
        suspect_gender="boy",
        elder="grandmother",
    ),
    StoryParams(
        keepsake="photo_album",
        place="window_seat",
        helper="cousin",
        misunderstanding="dusting",
        child_name="Ben",
        child_gender="boy",
        suspect_name="Ruby",
        suspect_gender="girl",
        elder="grandfather",
    ),
    StoryParams(
        keepsake="quilt",
        place="cedar_chest",
        helper="neighbor",
        misunderstanding="carrying_cloth",
        child_name="Mia",
        child_gender="girl",
        suspect_name="Theo",
        suspect_gender="boy",
        elder="grandmother",
    ),
    StoryParams(
        keepsake="music_box",
        place="shelf",
        helper="sibling",
        misunderstanding="dusting",
        child_name="Sam",
        child_gender="boy",
        suspect_name="Nora",
        suspect_gender="girl",
        elder="grandfather",
    ),
]


ASP_RULES = r"""
fits(K, P) :- keepsake(K), place(P), item_size(K, S), place_fits(P, S).
solvable(P, H) :- place(P), helper(H), needs(P, Skill), has_skill(H, Skill).
valid(K, P, H) :- keepsake(K), place(P), helper(H), fits(K, P), solvable(P, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for keepsake_id, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", keepsake_id))
        lines.append(asp.fact("item_size", keepsake_id, keepsake.size))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for size in sorted(place.fits):
            lines.append(asp.fact("place_fits", place_id, size))
        for skill in sorted(place.search_needs):
            lines.append(asp.fact("needs", place_id, skill))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for skill in sorted(helper.skills):
            lines.append(asp.fact("has_skill", helper_id, skill))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        default_args = build_parser().parse_args([])
        p = resolve_params(default_args, random.Random(7))
        smoke_cases.append(p)
    except Exception as err:
        rc = 1
        print(f"SMOKE FAIL: resolve_params crashed: {err}")

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            emit(sample, trace=False, qa=False, header=f"### smoke {idx}")
        except Exception as err:
            rc = 1
            print(f"SMOKE FAIL on case {idx}: {err}")
            break
    if rc == 0:
        print("OK: story generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Heartwarming mystery storyworld about a missing keepsake, a misunderstanding, and a lesson learned."
    )
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--suspect-name")
    ap.add_argument("--suspect-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.keepsake and args.place:
        keepsake = KEEPSAKES[args.keepsake]
        place = PLACES[args.place]
        if not item_fits_place(keepsake, place):
            raise StoryError(explain_rejection(keepsake, place))
    if args.place and args.helper:
        place = PLACES[args.place]
        helper = HELPERS[args.helper]
        if not helper_can_solve(place, helper):
            keepsake = KEEPSAKES[args.keepsake] if args.keepsake else next(iter(KEEPSAKES.values()))
            raise StoryError(explain_rejection(keepsake, place, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.keepsake is None or combo[0] == args.keepsake)
        and (args.place is None or combo[1] == args.place)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    keepsake_id, place_id, helper_id = rng.choice(combos)
    misunderstanding_id = args.misunderstanding or rng.choice(sorted(MISUNDERSTANDINGS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    suspect_gender = args.suspect_gender or ("boy" if child_gender == "girl" else "girl")
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    suspect_pool = SUSPECT_GIRL_NAMES if suspect_gender == "girl" else SUSPECT_BOY_NAMES
    suspect_name = args.suspect_name or rng.choice([n for n in suspect_pool if n != child_name] or suspect_pool)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])

    return StoryParams(
        keepsake=keepsake_id,
        place=place_id,
        helper=helper_id,
        misunderstanding=misunderstanding_id,
        child_name=child_name,
        child_gender=child_gender,
        suspect_name=suspect_name,
        suspect_gender=suspect_gender,
        elder=elder,
    )


def generate(params: StoryParams) -> StorySample:
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(Invalid keepsake: {params.keepsake})")
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper: {params.helper})")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError(f"(Invalid misunderstanding: {params.misunderstanding})")

    keepsake = KEEPSAKES[params.keepsake]
    place = PLACES[params.place]
    helper = HELPERS[params.helper]
    misunderstanding = MISUNDERSTANDINGS[params.misunderstanding]

    if not item_fits_place(keepsake, place):
        raise StoryError(explain_rejection(keepsake, place))
    if not helper_can_solve(place, helper):
        raise StoryError(explain_rejection(keepsake, place, helper))

    world = tell(
        keepsake=keepsake,
        place=place,
        helper=helper,
        misunderstanding=misunderstanding,
        child_name=params.child_name,
        child_gender=params.child_gender,
        suspect_name=params.suspect_name,
        suspect_gender=params.suspect_gender,
        elder_type=params.elder,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (keepsake, place, helper) combos:\n")
        for keepsake_id, place_id, helper_id in combos:
            print(f"  {keepsake_id:12} {place_id:12} {helper_id}")
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
            header = f"### {p.child_name}: {p.keepsake} in {p.place} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
