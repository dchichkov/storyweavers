#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/found_moral_value_whodunit.py
========================================================

A standalone storyworld about a tiny whodunit for young children: something
important seems to be missing, a child starts to wonder who took it, and clues
from the world reveal a kinder truth. The moral value is simple and concrete:
do not blame people before you know what happened; look carefully, tell the
truth, and apologize when you are wrong.

Run it
------
    python storyworlds/worlds/gpt-5.4/found_moral_value_whodunit.py
    python storyworlds/worlds/gpt-5.4/found_moral_value_whodunit.py --place classroom --item badge
    python storyworlds/worlds/gpt-5.4/found_moral_value_whodunit.py --item lunch_note --hiding flour_bin
    python storyworlds/worlds/gpt-5.4/found_moral_value_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/found_moral_value_whodunit.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/found_moral_value_whodunit.py --qa --json
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher", "baker"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"teacher": "teacher", "baker": "baker", "mother": "mom", "father": "dad"}.get(
            self.type, self.type
        )


@dataclass
class Place:
    id: str
    label: str
    keeper_type: str
    keeper_label: str
    scene: str
    bustle: str
    activity: str
    affordances: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    size: str
    owner_kind: str
    shine: str
    use_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    surface: str
    fits: set[str] = field(default_factory=set)
    needs: set[str] = field(default_factory=set)
    clue: str = ""
    reveal: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class SuspectStyle:
    id: str
    line: str
    reason: str
    apology: str
    calm_line: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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
    item = world.get("item")
    detective = world.get("detective")
    keeper = world.get("keeper")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["worry"] += 1
    detective.memes["mystery"] += 1
    keeper.memes["concern"] += 1
    return []


def _r_rash_accuse(world: World) -> list[str]:
    detective = world.get("detective")
    suspect = world.get("suspect")
    if detective.memes["suspicion"] < THRESHOLD or detective.memes["patience"] >= THRESHOLD:
        return []
    sig = ("rash_accuse", detective.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.memes["hurt"] += 1
    detective.memes["guilt_seed"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    item = world.get("item")
    detective = world.get("detective")
    suspect = world.get("suspect")
    keeper = world.get("keeper")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["relief"] += 1
    detective.memes["lesson"] += 1
    suspect.memes["relief"] += 1
    keeper.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotion", apply=_r_missing_worry),
    Rule(name="rash_accuse", tag="social", apply=_r_rash_accuse),
    Rule(name="found_relief", tag="emotion", apply=_r_found_relief),
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
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def hiding_plausible(place: Place, item: MissingItem, hiding: HidingPlace) -> bool:
    if item.size not in hiding.fits:
        return False
    return hiding.needs.issubset(place.affordances)


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            for hiding_id, hiding in HIDING_PLACES.items():
                if hiding_plausible(place, item, hiding):
                    out.append((place_id, item_id, hiding_id))
    return out


def explain_rejection(place: Place, item: MissingItem, hiding: HidingPlace) -> str:
    if item.size not in hiding.fits:
        return (
            f"(No story: {item.phrase} is too {item.size} to be reasonably found in "
            f"{hiding.phrase}. Pick a hiding place that can hold something that size.)"
        )
    missing = sorted(hiding.needs - place.affordances)
    if missing:
        need_text = ", ".join(missing)
        return (
            f"(No story: {hiding.phrase} only makes sense where {need_text} exists, "
            f"but {place.label} does not have that. Pick a matching place or hiding spot.)"
        )
    return "(No story: that combination is not reasonable.)"


def introduce(world: World, detective: Entity, suspect: Entity, keeper: Entity, item: MissingItem) -> None:
    place = world.place
    world.say(
        f"In {place.label}, {detective.id} loved small mysteries almost as much as {item.phrase}. "
        f"{place.scene} {place.bustle}"
    )
    world.say(
        f"{suspect.id} was there too, busy with {place.activity}, while the {keeper.label_word} "
        f"kept the room humming along."
    )
    world.say(
        f"{detective.id} used {item.label} whenever {detective.pronoun()} wanted to {item.use_text}."
    )


def setup_loss(world: World, detective: Entity, item: Entity, suspect_style: SuspectStyle) -> None:
    item.meters["missing"] += 1
    detective.memes["suspicion"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {detective.id} reached for {detective.pronoun('possessive')} {item.label}, it was gone."
    )
    world.say(
        f'"My {item.label} is missing," {detective.pronoun()} whispered, eyes wide. '
        f"{suspect_style.reason}"
    )


def gentle_question(world: World, detective: Entity, suspect: Entity, suspect_style: SuspectStyle) -> None:
    detective.memes["patience"] += 1
    world.say(
        f'{detective.id} took a small breath. "{suspect_style.calm_line}" '
        f"{detective.pronoun()} asked {suspect.id}."
    )
    world.say(
        f'{suspect.id} blinked. "No," {suspect.pronoun()} said. "But I can help you look."'
    )


def rash_blame(world: World, detective: Entity, suspect: Entity, suspect_style: SuspectStyle) -> None:
    propagate(world, narrate=False)
    world.say(
        f'{detective.id} forgot to slow down. "{suspect_style.line}" {detective.pronoun()} burst out.'
    )
    if suspect.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{suspect.id}'s face fell. {suspect.pronoun().capitalize()} had not taken anything at all."
        )


def clue_appears(world: World, detective: Entity, keeper: Entity, hiding: HidingPlace) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"Then {detective.id} noticed {hiding.clue} on {hiding.surface}. That was the first real clue."
    )
    world.say(
        f'The {keeper.label_word} nodded. "A good detective follows clues, not guesses," '
        f"{keeper.pronoun()} said."
    )


def search_and_find(world: World, detective: Entity, suspect: Entity, keeper: Entity,
                    item: Entity, hiding: HidingPlace) -> None:
    item.meters["missing"] = 0.0
    item.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{detective.id}, {suspect.id}, and the {keeper.label_word} hurried to {hiding.phrase}."
    )
    world.say(
        f"There, tucked {hiding.reveal}, they found the {item.label}."
    )
    world.say(
        f'"Found it!" cried {detective.id}. At once the room felt lighter.'
    )


def explain_truth(world: World, detective: Entity, suspect: Entity, keeper: Entity,
                  item: MissingItem, hiding: HidingPlace) -> None:
    world.say(
        f"The {keeper.label_word} looked at the clue again and smiled. "
        f'"No one stole it," {keeper.pronoun()} said. "It slipped there during {world.place.activity}, '
        f'and that is why it was hiding in {hiding.label}."'
    )
    world.say(
        f"{suspect.id} had only been nearby, which made {detective.id}'s first guess feel true even though it was not."
    )


def apology_or_pride(world: World, detective: Entity, suspect: Entity, suspect_style: SuspectStyle,
                     rushed: bool) -> None:
    if rushed:
        detective.memes["sorry"] += 1
        suspect.memes["forgiven"] += 1
        world.say(
            f'{detective.id} looked at {suspect.id} and spoke the truth. "{suspect_style.apology}"'
        )
        world.say(
            f'{suspect.id} gave a small nod. "Thank you for saying that," {suspect.pronoun()} said.'
        )
    else:
        world.say(
            f"{suspect.id} smiled because {detective.id} had asked kindly instead of blaming."
        )


def closing_lesson(world: World, detective: Entity, item: MissingItem, rushed: bool) -> None:
    detective.memes["lesson"] += 1
    if rushed:
        world.say(
            f"After that, {detective.id} still loved mysteries, but {detective.pronoun()} remembered that being quick is not the same as being right."
        )
    else:
        world.say(
            f"After that, {detective.id} felt proud in the warm, quiet way that comes from doing a careful thing."
        )
    world.say(
        f"The {item.label} was back where it belonged, and the best clue of all had been found: fairness matters more than guesses."
    )


def tell(place: Place, item_cfg: MissingItem, hiding: HidingPlace, suspect_style: SuspectStyle,
         detective_name: str = "Mina", detective_type: str = "girl",
         suspect_name: str = "Owen", suspect_type: str = "boy",
         detective_trait: str = "careful", suspect_trait: str = "quiet",
         rushed: bool = False) -> World:
    world = World(place)
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_type,
        role="detective",
        traits=[detective_trait],
    ))
    suspect = world.add(Entity(
        id=suspect_name,
        kind="character",
        type=suspect_type,
        role="suspect",
        traits=[suspect_trait],
    ))
    keeper = world.add(Entity(
        id="Keeper",
        kind="character",
        type=place.keeper_type,
        role="keeper",
        label=place.keeper_label,
    ))
    item = world.add(Entity(
        id="item",
        type="object",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        tags=set(item_cfg.tags),
    ))

    world.facts["rushed"] = rushed
    introduce(world, detective, suspect, keeper, item_cfg)
    world.para()
    setup_loss(world, detective, item, suspect_style)
    if rushed:
        rash_blame(world, detective, suspect, suspect_style)
    else:
        gentle_question(world, detective, suspect, suspect_style)
    world.para()
    clue_appears(world, detective, keeper, hiding)
    search_and_find(world, detective, suspect, keeper, item, hiding)
    explain_truth(world, detective, suspect, keeper, item_cfg, hiding)
    world.para()
    apology_or_pride(world, detective, suspect, suspect_style, rushed)
    closing_lesson(world, detective, item_cfg, rushed)

    world.facts.update(
        place=place,
        item_cfg=item_cfg,
        hiding=hiding,
        suspect_style=suspect_style,
        detective=detective,
        suspect=suspect,
        keeper=keeper,
        item=item,
        outcome="apology" if rushed else "careful",
        accused=rushed,
        found=item.meters["found"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    item: str
    hiding: str
    suspect_style: str
    detective_name: str
    detective_type: str
    suspect_name: str
    suspect_type: str
    detective_trait: str
    suspect_trait: str
    rushed: bool
    seed: Optional[int] = None


PLACES = {
    "classroom": Place(
        id="classroom",
        label="the sun-striped classroom",
        keeper_type="teacher",
        keeper_label="the teacher",
        scene="Paper stars hung over the windows, and the shelves were packed with books and puzzles.",
        bustle="Children were trading crayons, sliding chairs, and whispering over their work.",
        activity="clean-up time",
        affordances={"books", "paper", "shelf", "puzzle"},
        tags={"classroom"},
    ),
    "bakery": Place(
        id="bakery",
        label="the warm little bakery",
        keeper_type="baker",
        keeper_label="the baker",
        scene="The air smelled like bread, and soft flour clouds floated in the light.",
        bustle="Trays tapped, aprons swished, and cookie tins clicked shut.",
        activity="morning baking",
        affordances={"flour", "tray", "shelf", "apron"},
        tags={"bakery"},
    ),
    "art_room": Place(
        id="art_room",
        label="the bright art room",
        keeper_type="teacher",
        keeper_label="the art teacher",
        scene="Paint jars shone on the table, and paper waited in neat stacks.",
        bustle="Brushes swished in water cups, and big sheets of paper slid from hand to hand.",
        activity="painting time",
        affordances={"paper", "shelf", "apron", "tray"},
        tags={"art"},
    ),
}

ITEMS = {
    "badge": MissingItem(
        id="badge",
        label="helper badge",
        phrase="a shiny helper badge",
        size="small",
        owner_kind="child",
        shine="a small gold gleam",
        use_text="feel brave when jobs needed doing",
        tags={"badge", "honesty"},
    ),
    "bookmark": MissingItem(
        id="bookmark",
        label="star bookmark",
        phrase="a silver star bookmark",
        size="flat",
        owner_kind="child",
        shine="a thin silver flash",
        use_text="mark the best page in a story",
        tags={"bookmark", "books"},
    ),
    "lunch_note": MissingItem(
        id="lunch_note",
        label="heart note",
        phrase="a folded heart note",
        size="flat",
        owner_kind="child",
        shine="a pink corner",
        use_text="peek at a loving message from home",
        tags={"note", "kindness"},
    ),
    "cookie_cutter": MissingItem(
        id="cookie_cutter",
        label="star cutter",
        phrase="a little star cutter",
        size="small",
        owner_kind="kitchen",
        shine="a tin sparkle",
        use_text="make cookies with neat points",
        tags={"cookies", "sharing"},
    ),
}

HIDING_PLACES = {
    "book_pages": HidingPlace(
        id="book_pages",
        label="the middle of a giant picture book",
        phrase="the middle of a giant picture book on the reading rug",
        surface="the rug",
        fits={"flat"},
        needs={"books"},
        clue="a corner of paper peeking from a book that should have been closed",
        reveal="between two thick pages",
        tags={"books"},
    ),
    "paper_stack": HidingPlace(
        id="paper_stack",
        label="a stack of painted paper",
        phrase="the tallest stack of painted paper",
        surface="the art table",
        fits={"flat", "small"},
        needs={"paper"},
        clue="a little glimmer under the edge of the top sheets",
        reveal="under the last damp page",
        tags={"paper"},
    ),
    "flour_bin": HidingPlace(
        id="flour_bin",
        label="the flour bin",
        phrase="the round flour bin by the counter",
        surface="the counter",
        fits={"small"},
        needs={"flour"},
        clue="a tiny sparkle in a dusting of flour",
        reveal="inside the scoop handle",
        tags={"flour"},
    ),
    "apron_pocket": HidingPlace(
        id="apron_pocket",
        label="a hanging apron pocket",
        phrase="the blue apron hanging on its hook",
        surface="the wall hook",
        fits={"small", "flat"},
        needs={"apron"},
        clue="something making one pocket sag lower than the other",
        reveal="inside the deep front pocket",
        tags={"apron"},
    ),
    "supply_tray": HidingPlace(
        id="supply_tray",
        label="the supply tray",
        phrase="the metal supply tray near the shelf",
        surface="the shelf",
        fits={"small", "flat"},
        needs={"tray"},
        clue="a bright edge winking from under the tray paper",
        reveal="beneath the tray liner",
        tags={"tray"},
    ),
}

SUSPECT_STYLES = {
    "nearby_hands": SuspectStyle(
        id="nearby_hands",
        line="You were standing right there. I think you took it.",
        reason=f"Owen had been the closest one nearby, and that made the mystery feel easy to solve.",
        apology="I am sorry I blamed you before I knew the truth.",
        calm_line="Did you see where my thing went?",
    ),
    "pocket_guess": SuspectStyle(
        id="pocket_guess",
        line="I saw your pocket move. You must have hidden it.",
        reason=f"The suspect's pocket had swung when the room bustled, and that tiny motion grew too big in the detective's mind.",
        apology="I am sorry. I guessed instead of checking.",
        calm_line="Did anything brush against your pocket a moment ago?",
    ),
    "shelf_guess": SuspectStyle(
        id="shelf_guess",
        line="You were by the shelf, so you must know where it is.",
        reason=f"The suspect had been near the shelf, which was only a place, not proof.",
        apology="I am sorry for turning a guess into a blame.",
        calm_line="You were near the shelf. Did you notice any clue there?",
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tess", "Ava", "Ruby", "Ella", "June"]
BOY_NAMES = ["Owen", "Ben", "Theo", "Max", "Eli", "Sam", "Finn", "Jack"]
TRAITS = ["careful", "curious", "quiet", "kind", "thoughtful", "quick"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    item = f["item_cfg"]
    detective = f["detective"]
    suspect = f["suspect"]
    if f["accused"]:
        return [
            f'Write a gentle whodunit for a 3-to-5-year-old that includes the word "found" and ends with an apology.',
            f"Tell a small mystery set in {place.label} where {detective.id} wrongly blames {suspect.id} for a missing {item.label}, then the object is found and the truth is kinder than the guess.",
            f"Write a story that teaches children not to accuse people without proof, using a missing {item.label} and a calm grown-up guide.",
        ]
    return [
        f'Write a gentle whodunit for a 3-to-5-year-old that includes the word "found" and rewards careful thinking.',
        f"Tell a cozy mystery in {place.label} where {detective.id} looks for a missing {item.label}, asks kindly, and follows clues until it is found.",
        f"Write a child-facing mystery story that teaches fairness and honesty: clues matter more than guesses, and the ending should feel warm and true.",
    ]


KNOWLEDGE = {
    "honesty": [(
        "What does honesty mean?",
        "Honesty means telling what is true. It also means not pretending you know something when you only guessed."
    )],
    "fairness": [(
        "Why should we not blame someone before we know what happened?",
        "Because blaming can hurt someone's feelings when they did nothing wrong. It is fairer to look for clues and ask calm questions first."
    )],
    "apology": [(
        "What is an apology?",
        "An apology is when you say you are sorry for something unkind or wrong that you did. A real apology tells the truth and tries to make things better."
    )],
    "clue": [(
        "What is a clue?",
        "A clue is a small sign that helps you figure something out. Good detectives follow clues instead of wild guesses."
    )],
    "bookmark": [(
        "What does a bookmark do?",
        "A bookmark helps you remember your place in a book. You tuck it between pages so you can find your story again."
    )],
    "badge": [(
        "What is a badge?",
        "A badge is a small sign or pin that shows a job or a role. People often wear one to show they are helping."
    )],
    "flour": [(
        "What is flour?",
        "Flour is a soft powder made from ground grain. Bakers use it to make bread, cakes, and cookies."
    )],
    "apron": [(
        "What is an apron for?",
        "An apron protects clothes while you cook or paint. Some aprons have pockets that can hold small things."
    )],
    "paper": [(
        "Why can paper hide a small object?",
        "Because paper can cover flat or tiny things so well that they are hard to see. A little shine or corner sticking out can become an important clue."
    )],
}
KNOWLEDGE_ORDER = ["honesty", "fairness", "apology", "clue", "badge", "bookmark", "flour", "apron", "paper"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    suspect = f["suspect"]
    keeper = f["keeper"]
    item = f["item_cfg"]
    hiding = f["hiding"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, who tried to solve a small mystery, {suspect.id}, who got caught inside the mystery, and the {keeper.label_word}, who helped them slow down and look carefully."
        ),
        (
            f"What was missing?",
            f"The missing thing was {item.phrase}. It mattered because {detective.id} liked to use it to {item.use_text}."
        ),
        (
            "Why did it feel like a whodunit?",
            f"It felt like a whodunit because something was gone, one child seemed suspicious, and everyone had to follow a real clue to learn the truth. The mystery changed from 'who took it?' to 'where did it really go?'"
        ),
        (
            "What clue helped solve the mystery?",
            f"The clue was {hiding.clue}. That small sign pointed everyone toward {hiding.label} instead of toward another person's feelings."
        ),
        (
            f"Where was the missing object found?",
            f"It was found in {hiding.label}. The object had slipped there during {place.activity}, so it was hidden by accident, not by stealing."
        ),
    ]
    if f["accused"]:
        qa.append((
            f"Why did {detective.id} need to apologize to {suspect.id}?",
            f"{detective.id} blamed {suspect.id} before knowing the truth. When the object was found and everyone learned it had only slipped away, {detective.id} understood that a guess had hurt {suspect.id}'s feelings."
        ))
    else:
        qa.append((
            f"What did {detective.id} do right when the mystery began?",
            f"{detective.id} asked a calm question instead of throwing blame. That kindness kept the mystery safe to solve and helped {suspect.id} join the search."
        ))
    qa.append((
        "What is the lesson of the story?",
        f"The lesson is to look for clues, tell the truth, and treat people fairly. Being careful with other people's feelings matters as much as finding the missing thing."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"honesty", "fairness", "clue"}
    if f["accused"]:
        tags.add("apology")
    tags |= set(f["item_cfg"].tags)
    tags |= set(f["hiding"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="classroom",
        item="badge",
        hiding="apron_pocket",
        suspect_style="nearby_hands",
        detective_name="Mina",
        detective_type="girl",
        suspect_name="Owen",
        suspect_type="boy",
        detective_trait="careful",
        suspect_trait="quiet",
        rushed=False,
    ),
    StoryParams(
        place="art_room",
        item="bookmark",
        hiding="paper_stack",
        suspect_style="shelf_guess",
        detective_name="Ruby",
        detective_type="girl",
        suspect_name="Theo",
        suspect_type="boy",
        detective_trait="curious",
        suspect_trait="kind",
        rushed=True,
    ),
    StoryParams(
        place="bakery",
        item="cookie_cutter",
        hiding="flour_bin",
        suspect_style="pocket_guess",
        detective_name="Ben",
        detective_type="boy",
        suspect_name="Lila",
        suspect_type="girl",
        detective_trait="thoughtful",
        suspect_trait="quick",
        rushed=False,
    ),
    StoryParams(
        place="classroom",
        item="lunch_note",
        hiding="book_pages",
        suspect_style="nearby_hands",
        detective_name="Ella",
        detective_type="girl",
        suspect_name="Finn",
        suspect_type="boy",
        detective_trait="kind",
        suspect_trait="quiet",
        rushed=True,
    ),
]


ASP_RULES = r"""
plausible(P, I, H) :- place(P), item(I), hiding(H),
                      item_size(I, S), fits(H, S),
                      need(H, N), afford(P, N).
need_missing(H) :- hiding(H), not need(H, _).
plausible(P, I, H) :- place(P), item(I), hiding(H),
                      item_size(I, S), fits(H, S), need_missing(H).

outcome(apology) :- rushed.
outcome(careful) :- not rushed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for aff in sorted(place.affordances):
            lines.append(asp.fact("afford", pid, aff))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_size", iid, item.size))
    for hid, hiding in HIDING_PLACES.items():
        lines.append(asp.fact("hiding", hid))
        for fit in sorted(hiding.fits):
            lines.append(asp.fact("fits", hid, fit))
        for need in sorted(hiding.needs):
            lines.append(asp.fact("need", hid, need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show plausible/3."))
    return sorted(set(asp.atoms(model, "plausible")))


def asp_outcome(rushed: bool) -> str:
    import asp

    extra = asp.fact("rushed") if rushed else ""
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A child-facing whodunit storyworld about finding a missing object and learning fairness."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hiding", choices=HIDING_PLACES)
    ap.add_argument("--suspect-style", choices=SUSPECT_STYLES)
    ap.add_argument("--rushed", action="store_true", help="make the detective accuse before checking")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.hiding:
        place = PLACES[args.place]
        item = ITEMS[args.item]
        hiding = HIDING_PLACES[args.hiding]
        if not hiding_plausible(place, item, hiding):
            raise StoryError(explain_rejection(place, item, hiding))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.hiding is None or combo[2] == args.hiding)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, hiding_id = rng.choice(sorted(combos))
    suspect_style = args.suspect_style or rng.choice(sorted(SUSPECT_STYLES))
    detective_type = rng.choice(["girl", "boy"])
    suspect_type = "boy" if detective_type == "girl" else "girl"
    detective_name = _pick_name(rng, detective_type)
    suspect_name = _pick_name(rng, suspect_type, avoid=detective_name)
    return StoryParams(
        place=place_id,
        item=item_id,
        hiding=hiding_id,
        suspect_style=suspect_style,
        detective_name=detective_name,
        detective_type=detective_type,
        suspect_name=suspect_name,
        suspect_type=suspect_type,
        detective_trait=rng.choice(TRAITS),
        suspect_trait=rng.choice(TRAITS),
        rushed=bool(args.rushed or rng.choice([False, False, True])),
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        item = ITEMS[params.item]
        hiding = HIDING_PLACES[params.hiding]
        suspect_style = SUSPECT_STYLES[params.suspect_style]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter value: {exc.args[0]})") from None

    if not hiding_plausible(place, item, hiding):
        raise StoryError(explain_rejection(place, item, hiding))

    world = tell(
        place=place,
        item_cfg=item,
        hiding=hiding,
        suspect_style=suspect_style,
        detective_name=params.detective_name,
        detective_type=params.detective_type,
        suspect_name=params.suspect_name,
        suspect_type=params.suspect_type,
        detective_trait=params.detective_trait,
        suspect_trait=params.suspect_trait,
        rushed=params.rushed,
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo gate:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    if asp_outcome(True) == "apology" and asp_outcome(False) == "careful":
        print("OK: ASP outcome matches rushed/careful model.")
    else:
        rc = 1
        print("MISMATCH in ASP outcome model.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "found" not in sample.story.lower():
            raise StoryError("(Smoke test failed: generated story missing expected content.)")
        print("OK: smoke test generate() succeeded.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show plausible/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, hiding) combos:\n")
        for place, item, hiding in combos:
            print(f"  {place:10} {item:13} {hiding}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: {p.item} missing in {p.place} ({'apology' if p.rushed else 'careful'})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
