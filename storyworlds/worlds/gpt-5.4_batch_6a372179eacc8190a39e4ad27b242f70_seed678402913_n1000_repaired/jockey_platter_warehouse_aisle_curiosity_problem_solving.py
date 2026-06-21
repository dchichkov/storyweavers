#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/jockey_platter_warehouse_aisle_curiosity_problem_solving.py

A small storyworld for a gentle warehouse-aisle whodunit: a child notices a
missing party platter, studies a clue, reasons about where it could have gone,
and solves the mystery kindly. The turn is not danger but confusion, and the
moral value is honesty plus asking careful questions before blaming anyone.
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
HONESTY_CONFESS = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.label or self.type
        )


@dataclass
class Platter:
    id: str
    label: str
    phrase: str
    chilled: bool
    clue_ids: tuple[str, ...]
    spot_ids: tuple[str, ...]
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    line: str
    direct: bool
    platter_ids: tuple[str, ...]
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    cold_ok: bool
    scene: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    name: str
    role: str
    marker: str
    marker_word: str
    spot_ids: tuple[str, ...]
    honesty: int
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


def _r_reason(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["curiosity"] < THRESHOLD or child.meters["clue_seen"] < THRESHOLD:
        return []
    sig = ("reason",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["reasoning"] += 1
    return []


def _r_find_relief(world: World) -> list[str]:
    platter = world.get("platter")
    if platter.meters["found"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("child", "adult", "culprit"):
        if eid in world.entities:
            world.get(eid).memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="reason", tag="mind", apply=_r_reason),
    Rule(name="find_relief", tag="emotion", apply=_r_find_relief),
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


PLATTERS = {
    "cookies": Platter(
        id="cookies",
        label="cookie platter",
        phrase="a round cookie platter under clear wrap",
        chilled=False,
        clue_ids=("crumbs",),
        spot_ids=("napkins", "paper_towels"),
        tags={"cookies", "platter", "party_food"},
    ),
    "fruit": Platter(
        id="fruit",
        label="fruit platter",
        phrase="a cold fruit platter with bright grapes and melon",
        chilled=True,
        clue_ids=("grape", "drip"),
        spot_ids=("cooler",),
        tags={"fruit", "platter", "cold_food"},
    ),
    "sandwiches": Platter(
        id="sandwiches",
        label="sandwich platter",
        phrase="a chilled sandwich platter cut into little triangles",
        chilled=True,
        clue_ids=("olive", "drip"),
        spot_ids=("cooler", "juice_boxes"),
        tags={"sandwich", "platter", "cold_food"},
    ),
}

CLUES = {
    "crumbs": Clue(
        id="crumbs",
        label="cookie crumbs",
        line="tiny cookie crumbs glittered on the floor beside the empty space",
        direct=True,
        platter_ids=("cookies",),
        tags={"cookies", "clue"},
    ),
    "grape": Clue(
        id="grape",
        label="a lonely grape",
        line="one lonely grape sat by the wheel of a cart like a purple clue",
        direct=True,
        platter_ids=("fruit",),
        tags={"fruit", "clue"},
    ),
    "olive": Clue(
        id="olive",
        label="an olive ring",
        line="a green olive ring had slipped onto the polished floor",
        direct=True,
        platter_ids=("sandwiches",),
        tags={"sandwich", "clue"},
    ),
    "drip": Clue(
        id="drip",
        label="a cold drip",
        line="a string of cold drops shone on the floor and pointed away from the stack",
        direct=False,
        platter_ids=("fruit", "sandwiches"),
        tags={"cold_food", "clue"},
    ),
}

SPOTS = {
    "cooler": Spot(
        id="cooler",
        label="the cooler endcap",
        phrase="the cooler endcap humming with juice and yogurt",
        cold_ok=True,
        scene="cold air puffed out each time the door swung open",
        tags={"cold", "warehouse"},
    ),
    "juice_boxes": Spot(
        id="juice_boxes",
        label="the juice-box tower",
        phrase="a tall tower of juice boxes wrapped in shiny plastic",
        cold_ok=True,
        scene="the bright cartons made a little wall beside the aisle",
        tags={"drinks", "warehouse"},
    ),
    "napkins": Spot(
        id="napkins",
        label="the napkin display",
        phrase="the party napkin display with stripes and stars",
        cold_ok=False,
        scene="colorful packets rustled there like paper leaves",
        tags={"party", "warehouse"},
    ),
    "paper_towels": Spot(
        id="paper_towels",
        label="the paper-towel pallet",
        phrase="a giant pallet of paper towels stacked almost to the sign",
        cold_ok=False,
        scene="the white rolls looked like a wall of soft drums",
        tags={"paper", "warehouse"},
    ),
}

SUSPECTS = {
    "vale": Suspect(
        id="vale",
        name="Mr. Vale",
        role="shopper",
        marker="a tiny silver jockey charm clipped to his cart",
        marker_word="jockey",
        spot_ids=("cooler", "juice_boxes"),
        honesty=3,
        tags={"jockey", "shopper"},
    ),
    "nina": Suspect(
        id="nina",
        name="Nina",
        role="worker",
        marker="a strip of blue tape on her rolling ladder",
        marker_word="tape",
        spot_ids=("paper_towels", "cooler"),
        honesty=2,
        tags={"worker"},
    ),
    "tori": Suspect(
        id="tori",
        name="Tori",
        role="party shopper",
        marker="balloon ribbons looped through her cart handle",
        marker_word="ribbons",
        spot_ids=("napkins",),
        honesty=1,
        tags={"shopper", "party"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ava", "Lucy", "Ella", "Zoe", "Ivy"]
BOY_NAMES = ["Ben", "Theo", "Leo", "Sam", "Finn", "Noah", "Max", "Eli"]
TRAITS = ["careful", "bright", "patient", "curious", "thoughtful", "gentle"]


def clue_matches_platter(clue: Clue, platter: Platter) -> bool:
    return platter.id in clue.platter_ids


def spot_fits_platter(spot: Spot, platter: Platter) -> bool:
    if spot.id not in platter.spot_ids:
        return False
    if platter.chilled and not spot.cold_ok:
        return False
    return True


def suspect_reaches_spot(suspect: Suspect, spot: Spot) -> bool:
    return spot.id in suspect.spot_ids


def valid_combo(platter: Platter, clue: Clue, suspect: Suspect, spot: Spot) -> bool:
    return (
        clue_matches_platter(clue, platter)
        and spot_fits_platter(spot, platter)
        and suspect_reaches_spot(suspect, spot)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for platter_id, platter in PLATTERS.items():
        for clue_id, clue in CLUES.items():
            for suspect_id, suspect in SUSPECTS.items():
                for spot_id, spot in SPOTS.items():
                    if valid_combo(platter, clue, suspect, spot):
                        combos.append((platter_id, clue_id, suspect_id, spot_id))
    return combos


@dataclass
class StoryParams:
    platter: str
    clue: str
    suspect: str
    spot: str
    child_name: str
    child_gender: str
    adult_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        platter="fruit",
        clue="grape",
        suspect="vale",
        spot="cooler",
        child_name="Maya",
        child_gender="girl",
        adult_type="aunt",
        trait="curious",
    ),
    StoryParams(
        platter="cookies",
        clue="crumbs",
        suspect="nina",
        spot="paper_towels",
        child_name="Ben",
        child_gender="boy",
        adult_type="uncle",
        trait="careful",
    ),
    StoryParams(
        platter="cookies",
        clue="crumbs",
        suspect="tori",
        spot="napkins",
        child_name="Nora",
        child_gender="girl",
        adult_type="mother",
        trait="gentle",
    ),
    StoryParams(
        platter="sandwiches",
        clue="drip",
        suspect="vale",
        spot="juice_boxes",
        child_name="Theo",
        child_gender="boy",
        adult_type="father",
        trait="thoughtful",
    ),
]


def explain_rejection(platter: Platter, clue: Clue, suspect: Suspect, spot: Spot) -> str:
    if not clue_matches_platter(clue, platter):
        return (
            f"(No story: {clue.label} does not fit a {platter.label}. "
            "The clue has to come from the missing food, or the mystery makes no sense.)"
        )
    if not spot_fits_platter(spot, platter):
        if platter.chilled and not spot.cold_ok:
            return (
                f"(No story: a {platter.label} needs a cold place, but {spot.label} is not cold. "
                "The platter would not reasonably be left there.)"
            )
        return (
            f"(No story: {spot.label} is not a plausible place for a {platter.label} in this world.)"
        )
    if not suspect_reaches_spot(suspect, spot):
        return (
            f"(No story: {suspect.name} has no reason to move the platter toward {spot.label}. "
            "Pick a suspect whose errand actually matches that part of the aisle.)"
        )
    return "(No story: this mystery setup is unreasonable.)"


def outcome_of(params: StoryParams) -> str:
    suspect = SUSPECTS[params.suspect]
    clue = CLUES[params.clue]
    if suspect.honesty >= HONESTY_CONFESS:
        return "confessed"
    if clue.direct:
        return "traced"
    return "found"


def introduce(world: World, child: Entity, adult: Entity, platter: Platter) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} walked beside {child.pronoun('possessive')} {adult.label_word} down a wide warehouse aisle "
        f"where giant boxes rose like little buildings."
    )
    world.say(
        f"They had come for party food, and on the list was {platter.phrase}. "
        f"{child.id} liked errands because every shelf felt like a puzzle waiting to be noticed."
    )


def discover_missing(world: World, child: Entity, adult: Entity, platter: Platter) -> None:
    world.say(
        f"But when they reached the cold party shelf, there was an empty round space where one {platter.label} should have been."
    )
    world.say(
        f'"That is odd," said {adult.label_word}. "{platter.label.capitalize()} does not just vanish."'
    )
    world.get("platter").meters["missing"] += 1


def inspect_clue(world: World, child: Entity, clue: Clue) -> None:
    child.meters["clue_seen"] += 1
    world.say(
        f"{child.id} crouched down and looked carefully. {clue.line}."
    )
    propagate(world, narrate=False)
    if child.memes["reasoning"] >= THRESHOLD:
        world.say(
            f"That made {child.id}'s eyes shine. This was not a guessing game now. It was a real clue."
        )


def list_suspects(world: World, culprit: Suspect) -> None:
    others = [s for s in SUSPECTS.values() if s.id != culprit.id]
    one, two = others[0], others[1]
    world.say(
        f"Three people had been near the shelf: {culprit.name} with {culprit.marker}, "
        f"{one.name} with {one.marker}, and {two.name} with {two.marker}."
    )
    world.say("It looked like a tiny whodunit tucked between giant cartons.")


def reason_about_clue(world: World, child: Entity, platter: Platter, spot: Spot) -> None:
    child.meters["deduced"] += 1
    if platter.chilled:
        world.say(
            f'{child.id} whispered, "If the platter is cold, it would not stay by the warm paper goods. It must be near something cool."'
        )
    else:
        world.say(
            f'{child.id} whispered, "A dry platter would fit better near the party paper shelves than by the cold drinks."'
        )
    world.say(
        f"The clue and the shelves pointed together toward {spot.phrase}."
    )


def ask_kindly(world: World, child: Entity, culprit_ent: Entity, suspect: Suspect) -> None:
    child.memes["kindness"] += 1
    culprit_ent.memes["worry"] += 1
    world.say(
        f'{child.id} did not point or accuse. "{suspect.name}," {child.pronoun()} asked, '
        f'"did you maybe move a platter by mistake when you were reaching past the shelf?"'
    )


def confess(world: World, child: Entity, culprit_ent: Entity, suspect: Suspect, platter: Platter, spot: Spot) -> None:
    culprit_ent.memes["honesty"] += 1
    culprit_ent.meters["confessed"] += 1
    world.say(
        f'{suspect.name} looked at {suspect.marker} on {culprit_ent.pronoun("possessive")} cart, then nodded. '
        f'"I did," {culprit_ent.pronoun()} said. "I slid the {platter.label} aside while I reached for something else, '
        f'and I left it by {spot.label}. I should have told someone right away."'
    )
    world.say(
        f"Because {suspect.name} told the truth quickly, the mystery softened into a fixable mistake."
    )


def follow_trail(world: World, child: Entity, adult: Entity, spot: Spot) -> None:
    child.meters["trail_followed"] += 1
    world.say(
        f"So {child.id} and {adult.label_word} followed the clue past high stacks of boxes until they reached {spot.phrase}."
    )
    world.say(spot.scene.capitalize() + ".")


def find_platter(world: World, child: Entity, culprit_ent: Entity, platter: Platter, spot: Spot) -> None:
    platter_ent = world.get("platter")
    platter_ent.meters["found"] += 1
    platter_ent.meters["missing"] = 0.0
    platter_ent.attrs["location"] = spot.label
    propagate(world, narrate=False)
    world.say(
        f"There, tucked safely beside the display, was the missing {platter.label}."
    )
    world.say(
        f"{child.id} lifted one hand in triumph, but only for a moment. The best part was not winning. It was solving the puzzle."
    )
    if culprit_ent.memes["worry"] >= THRESHOLD:
        world.say(
            f"Seeing it found, {culprit_ent.id} let out a long breath."
        )


def admit_after_found(world: World, culprit_ent: Entity, suspect: Suspect, platter: Platter, spot: Spot) -> None:
    culprit_ent.memes["honesty"] += 1
    world.say(
        f'"I put it there when I was in a hurry," {suspect.name} admitted at last. '
        f'"I saw the {platter.label} beside {spot.label} and hoped someone else would fix it. That was not the right thing."'
    )


def return_and_resolve(world: World, child: Entity, adult: Entity, culprit_ent: Entity, platter: Platter) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    adult.memes["pride"] += 1
    culprit_ent.memes["relief"] += 1
    world.say(
        f"They carried the {platter.label} back to the party shelf where it belonged."
    )
    world.say(
        f'{adult.label_word.capitalize()} smiled at {child.id}. "You solved it by looking, thinking, and asking kindly," '
        f'{adult.pronoun()} said.'
    )
    world.say(
        f'{culprit_ent.id} thanked them and promised, "Next time I will speak up right away instead of leaving a mixed-up mess behind."'
    )
    world.say(
        f"As they rolled on down the warehouse aisle, the shelves no longer felt suspicious. They felt orderly again, and {child.id} felt quietly proud."
    )


def tell(
    platter: Platter,
    clue: Clue,
    suspect: Suspect,
    spot: Spot,
    child_name: str = "Maya",
    child_gender: str = "girl",
    adult_type: str = "aunt",
    trait: str = "curious",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="detective",
            traits=[trait],
            label=child_name,
        )
    )
    adult = world.add(
        Entity(
            id="Adult",
            kind="character",
            type=adult_type,
            role="guardian",
            label="the grown-up",
        )
    )
    culprit_ent = world.add(
        Entity(
            id=suspect.name,
            kind="character",
            type="man" if suspect.id == "vale" else "woman",
            role="suspect",
            label=suspect.name,
            attrs={"marker": suspect.marker},
        )
    )
    platter_ent = world.add(
        Entity(
            id="platter",
            kind="thing",
            type="platter",
            label=platter.label,
            phrase=platter.phrase,
            attrs={"chilled": platter.chilled, "location": "missing shelf"},
        )
    )
    world.add(Entity(id="aisle", kind="thing", type="place", label="warehouse aisle"))

    introduce(world, child, adult, platter)
    discover_missing(world, child, adult, platter)

    world.para()
    inspect_clue(world, child, clue)
    list_suspects(world, suspect)
    reason_about_clue(world, child, platter, spot)

    world.para()
    ask_kindly(world, child, culprit_ent, suspect)
    outcome = outcome_of(
        StoryParams(
            platter=platter.id,
            clue=clue.id,
            suspect=suspect.id,
            spot=spot.id,
            child_name=child_name,
            child_gender=child_gender,
            adult_type=adult_type,
            trait=trait,
        )
    )
    if outcome == "confessed":
        confess(world, child, culprit_ent, suspect, platter, spot)
        follow_trail(world, child, adult, spot)
        find_platter(world, child, culprit_ent, platter, spot)
    else:
        follow_trail(world, child, adult, spot)
        find_platter(world, child, culprit_ent, platter, spot)
        admit_after_found(world, culprit_ent, suspect, platter, spot)

    world.para()
    return_and_resolve(world, child, adult, culprit_ent, platter)

    world.facts.update(
        child=child,
        adult=adult,
        culprit=culprit_ent,
        platter_cfg=platter,
        clue_cfg=clue,
        suspect_cfg=suspect,
        spot_cfg=spot,
        outcome=outcome,
        found=platter_ent.meters["found"] >= THRESHOLD,
        honest=suspect.honesty >= HONESTY_CONFESS,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    platter = f["platter_cfg"]
    suspect = f["suspect_cfg"]
    return [
        f'Write a gentle whodunit for a 3-to-5-year-old set in a warehouse aisle that includes the words "jockey" and "platter".',
        f"Tell a story where {child.id} notices a missing {platter.label}, studies clues, and solves the mystery by thinking carefully instead of blaming people.",
        f"Write a child-facing mystery in which {suspect.name}'s {suspect.marker_word} clue appears, the problem is solved with kindness, and the ending teaches honesty.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    platter = f["platter_cfg"]
    clue = f["clue_cfg"]
    suspect = f["suspect_cfg"]
    spot = f["spot_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child in a warehouse aisle, and {adult.label_word} helping solve a small mystery. The missing object was a {platter.label}, so the errand turned into a whodunit.",
        ),
        (
            f"What made {child.id} curious?",
            f"{child.id} saw an empty space where the {platter.label} should have been. That odd missing spot made the aisle feel like a puzzle that needed careful thinking.",
        ),
        (
            "What clue did the child notice?",
            f"{child.id} noticed {clue.label}. The clue mattered because it matched the kind of platter that was missing and pointed away from the shelf.",
        ),
        (
            f"Why did {child.id} look near {spot.label}?",
            f"{child.id} used problem solving instead of guessing. The clue fit the missing food, and {spot.label} was the kind of place where that platter could reasonably have been left.",
        ),
    ]
    if outcome == "confessed":
        qa.append(
            (
                f"How was the mystery solved?",
                f"{suspect.name} told the truth when {child.id} asked kindly. Then they followed the clue to {spot.label} and found the platter there.",
            )
        )
    else:
        qa.append(
            (
                "How was the mystery solved?",
                f"{child.id} and {adult.label_word} followed the clue all the way to {spot.label} and found the platter. After it was found, {suspect.name} admitted making the mistake.",
            )
        )
    qa.append(
        (
            "What moral did the story teach?",
            f"It taught that people should speak up honestly when they make a mistake. It also showed that careful questions and kind words can solve a problem better than quick blame.",
        )
    )
    return qa


KNOWLEDGE = {
    "jockey": [
        (
            "What is a jockey?",
            "A jockey is a person who rides a racehorse in a race. In this story, the word appears on a tiny charm shaped like a jockey.",
        )
    ],
    "platter": [
        (
            "What is a platter?",
            "A platter is a big tray used to hold food like fruit, cookies, or sandwiches. People often bring one to a party so many people can share it.",
        )
    ],
    "warehouse": [
        (
            "What is a warehouse aisle?",
            "A warehouse aisle is a long path between very big shelves in a large store. People push carts down it to find things they need.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. In a mystery, clues help people solve the puzzle step by step.",
        )
    ],
    "honesty": [
        (
            "Why is honesty important after a mistake?",
            "Honesty helps people fix a problem faster because they know what really happened. Telling the truth also helps others trust you.",
        )
    ],
    "problem_solving": [
        (
            "What does problem solving mean?",
            "Problem solving means looking carefully, thinking about what fits, and trying a sensible answer. It is like putting puzzle pieces together in your mind.",
        )
    ],
    "cold_food": [
        (
            "Why do some platters need to stay cold?",
            "Some food stays fresh and safe when it is kept cold. That is why a chilled platter belongs near coolers or cold cases.",
        )
    ],
    "party_food": [
        (
            "Why do stores sell party platters?",
            "Party platters make it easy to share food with many people at once. They hold lots of small bites on one big tray.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "jockey",
    "platter",
    "warehouse",
    "clue",
    "problem_solving",
    "honesty",
    "cold_food",
    "party_food",
]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"warehouse", "clue", "problem_solving", "honesty", "platter", "jockey"}
    tags |= set(f["platter_cfg"].tags)
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
            shown = {k: v for k, v in ent.attrs.items() if v or v is False}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
clue_matches(C, P) :- clue_for(C, P).
spot_fits(S, P)    :- allowed_spot(P, S), not needs_cold(P).
spot_fits(S, P)    :- allowed_spot(P, S), needs_cold(P), cold_ok(S).
suspect_reaches(U, S) :- goes_to(U, S).

valid(P, C, U, S) :- platter(P), clue(C), suspect(U), spot(S),
                     clue_matches(C, P), spot_fits(S, P), suspect_reaches(U, S).

confessed :- chosen_suspect(U), honesty(U, H), confess_min(M), H >= M.
traced    :- not confessed, chosen_clue(C), direct(C).
found     :- not confessed, chosen_clue(C), not direct(C).

outcome(confessed) :- confessed.
outcome(traced)    :- traced.
outcome(found)     :- found.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for platter_id, platter in PLATTERS.items():
        lines.append(asp.fact("platter", platter_id))
        if platter.chilled:
            lines.append(asp.fact("needs_cold", platter_id))
        for clue_id in platter.clue_ids:
            lines.append(asp.fact("clue_for", clue_id, platter_id))
        for spot_id in platter.spot_ids:
            lines.append(asp.fact("allowed_spot", platter_id, spot_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        if clue.direct:
            lines.append(asp.fact("direct", clue_id))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        if spot.cold_ok:
            lines.append(asp.fact("cold_ok", spot_id))
    for suspect_id, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", suspect_id))
        lines.append(asp.fact("honesty", suspect_id, suspect.honesty))
        for spot_id in suspect.spot_ids:
            lines.append(asp.fact("goes_to", suspect_id, spot_id))
    lines.append(asp.fact("confess_min", HONESTY_CONFESS))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_suspect", params.suspect),
            asp.fact("chosen_clue", params.clue),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="A warehouse-aisle whodunit about a missing platter, a clue, and kind problem solving."
    )
    ap.add_argument("--platter", choices=PLATTERS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible mystery setups from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.platter and args.clue and not clue_matches_platter(CLUES[args.clue], PLATTERS[args.platter]):
        suspect = SUSPECTS[args.suspect] if args.suspect else next(iter(SUSPECTS.values()))
        spot = SPOTS[args.spot] if args.spot else next(iter(SPOTS.values()))
        raise StoryError(explain_rejection(PLATTERS[args.platter], CLUES[args.clue], suspect, spot))
    if args.platter and args.spot and not spot_fits_platter(SPOTS[args.spot], PLATTERS[args.platter]):
        clue = CLUES[args.clue] if args.clue else next(iter(CLUES.values()))
        suspect = SUSPECTS[args.suspect] if args.suspect else next(iter(SUSPECTS.values()))
        raise StoryError(explain_rejection(PLATTERS[args.platter], clue, suspect, SPOTS[args.spot]))
    if args.suspect and args.spot and not suspect_reaches_spot(SUSPECTS[args.suspect], SPOTS[args.spot]):
        platter = PLATTERS[args.platter] if args.platter else next(iter(PLATTERS.values()))
        clue = CLUES[args.clue] if args.clue else next(iter(CLUES.values()))
        raise StoryError(explain_rejection(platter, clue, SUSPECTS[args.suspect], SPOTS[args.spot]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.platter is None or combo[0] == args.platter)
        and (args.clue is None or combo[1] == args.clue)
        and (args.suspect is None or combo[2] == args.suspect)
        and (args.spot is None or combo[3] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    platter_id, clue_id, suspect_id, spot_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        platter=platter_id,
        clue=clue_id,
        suspect=suspect_id,
        spot=spot_id,
        child_name=name,
        child_gender=gender,
        adult_type=adult,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        platter = PLATTERS[params.platter]
        clue = CLUES[params.clue]
        suspect = SUSPECTS[params.suspect]
        spot = SPOTS[params.spot]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]!r})") from None

    if not valid_combo(platter, clue, suspect, spot):
        raise StoryError(explain_rejection(platter, clue, suspect, spot))

    world = tell(
        platter=platter,
        clue=clue,
        suspect=suspect,
        spot=spot,
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_type=params.adult_type,
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

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(p)

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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (platter, clue, suspect, spot) combos:\n")
        for platter, clue, suspect, spot in combos:
            print(f"  {platter:11} {clue:7} {suspect:7} {spot}")
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
            p = sample.params
            header = f"### {p.child_name}: {p.platter} mystery in the warehouse aisle ({p.suspect}, {outcome_of(p)})"
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
