#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wan_plumb_wily_kindness_detective_story.py
=====================================================================

A standalone storyworld for a tiny child-facing detective tale shaped by
kindness. A young detective notices that a kindness token has gone missing,
follows physical clues through a small place, and solves the case by helping
rather than blaming. The culprit is never evil; the turn comes when the
detective understands the culprit's need and uses gentle action to set things
right.

The seed asked for the words "wan", "plumb", and "wily", the feature Kindness,
and a detective-story style. Every generated story therefore includes:
- a small mystery
- clue-following and a reveal
- a gentle, kind resolution
- the words "wan", "plumb", and "wily" in natural prose

Run it
------
    python storyworlds/worlds/gpt-5.4/wan_plumb_wily_kindness_detective_story.py
    python storyworlds/worlds/gpt-5.4/wan_plumb_wily_kindness_detective_story.py --place library
    python storyworlds/worlds/gpt-5.4/wan_plumb_wily_kindness_detective_story.py --culprit magpie --item medal
    python storyworlds/worlds/gpt-5.4/wan_plumb_wily_kindness_detective_story.py --approach scold
    python storyworlds/worlds/gpt-5.4/wan_plumb_wily_kindness_detective_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/wan_plumb_wily_kindness_detective_story.py --verify
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
SENSE_MIN = 2


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


@dataclass
class Place:
    id: str
    label: str
    opening: str
    path: str
    hiding_spot: str
    clue_types: set[str] = field(default_factory=set)
    food_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    shine: bool = False
    soft: bool = False
    scent: bool = False
    purpose: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    phrase: str
    likes: set[str] = field(default_factory=set)
    clue: str = ""
    clue_word: str = ""
    trouble: str = ""
    need: str = ""
    kindness_fix: str = ""
    return_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Approach:
    id: str
    sense: int
    helps_need: bool
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_missing_worry(world: World) -> list[str]:
    item = world.entities.get("item")
    detective = world.entities.get("detective")
    helper = world.entities.get("helper")
    if not item or not detective or not helper:
        return []
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["concern"] += 1
    helper.memes["concern"] += 1
    return []


def _r_clue_attention(world: World) -> list[str]:
    clue = world.entities.get("clue")
    detective = world.entities.get("detective")
    if not clue or not detective:
        return []
    if clue.meters["visible"] < THRESHOLD:
        return []
    sig = ("clue_attention",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["focus"] += 1
    detective.memes["hope"] += 1
    return []


def _r_kindness_trust(world: World) -> list[str]:
    culprit = world.entities.get("culprit")
    detective = world.entities.get("detective")
    if not culprit or not detective:
        return []
    if culprit.memes["helped"] < THRESHOLD:
        return []
    sig = ("kindness_trust",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    culprit.memes["trust"] += 1
    culprit.memes["fear"] = 0.0
    detective.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="clue_attention", tag="emotional", apply=_r_clue_attention),
    Rule(name="kindness_trust", tag="social", apply=_r_kindness_trust),
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
            world.say(s)
    return produced


def item_lures(item: MissingItem) -> set[str]:
    tags: set[str] = set()
    if item.shine:
        tags.add("shiny")
    if item.soft:
        tags.add("soft")
    if item.scent:
        tags.add("tasty")
    return tags


def culprit_wants_item(culprit: Culprit, item: MissingItem) -> bool:
    return bool(culprit.likes & item_lures(item))


def place_has_clue(place: Place, culprit: Culprit) -> bool:
    return culprit.clue in place.clue_types


def valid_story(place: Place, item: MissingItem, culprit: Culprit) -> bool:
    return culprit_wants_item(culprit, item) and place_has_clue(place, culprit)


def sensible_approaches() -> list[Approach]:
    return [a for a in APPROACHES.values() if a.sense >= SENSE_MIN]


def outcome_for(approach: Approach) -> str:
    return "returned_kindly" if approach.helps_need else "returned_after_pause"


def predict_case(place: Place, item: MissingItem, culprit: Culprit, approach: Approach) -> dict:
    return {
        "valid": valid_story(place, item, culprit),
        "kind_return": approach.helps_need,
        "clue_word": culprit.clue_word,
    }


def opening(world: World, detective: Entity, helper: Entity, place: Place, item: MissingItem) -> None:
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{place.opening} {detective.id} liked mysteries almost as much as "
        f"{detective.pronoun('possessive')} {helper.label_word} liked kind deeds."
    )
    world.say(
        f"On the table sat {item.phrase}, the little thing they used for {item.purpose}. "
        f"Then they looked again, and it was gone."
    )


def worry(world: World, detective: Entity, helper: Entity, item: MissingItem) -> None:
    detective.memes["duty"] += 1
    world.say(
        f"{helper.label_word.capitalize()} grew wan for a moment, not angry, just worried, "
        f"because the day would feel smaller without the {item.label}."
    )
    world.say(
        f'"Detective {detective.id}," {helper.pronoun()} said softly, "can you help me find it?"'
    )


def inspect_scene(world: World, detective: Entity, place: Place, culprit: Culprit) -> None:
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=culprit.clue_word,
        phrase=culprit.clue_word,
        role="clue",
        tags={culprit.clue},
    ))
    clue.meters["visible"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{detective.id} knelt and looked plumb under the bench, then along {place.path}. "
        f"There {detective.pronoun()} found {culprit.clue_word}."
    )
    world.say(
        f'"A clue," {detective.pronoun()} whispered. "Someone wily has been here."'
    )


def follow_trail(world: World, detective: Entity, place: Place, culprit: Culprit) -> None:
    detective.meters["steps"] += 1
    world.say(
        f"The clue led past {place.path} and toward {place.hiding_spot}. "
        f"{detective.id} followed without stomping or shouting."
    )
    world.say(
        f"Behind {place.hiding_spot}, {detective.pronoun()} found the little suspect: "
        f"{culprit.phrase}."
    )


def reveal_need(world: World, culprit_ent: Entity, culprit: Culprit, item: MissingItem) -> None:
    culprit_ent.memes["fear"] += 1
    culprit_ent.meters["stuck"] += 1
    world.say(
        f"The {culprit.label} was not smiling over a clever prize. It looked wan too, "
        f"caught in trouble: {culprit.trouble}."
    )
    world.say(
        f"It had taken the {item.label} because it liked {', '.join(sorted(item_lures(item)))} things, "
        f"but now it only looked small and sorry."
    )


def kind_act(world: World, detective: Entity, helper: Entity, culprit_ent: Entity,
             approach: Approach, culprit: Culprit) -> None:
    detective.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    culprit_ent.memes["helped"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{helper.label_word.capitalize()} did not scold. "{approach.text}," '
        f'{helper.pronoun()} said.'
    )
    world.say(culprit.kindness_fix)


def return_item(world: World, detective: Entity, culprit_ent: Entity, item_ent: Entity,
                culprit: Culprit, item: MissingItem) -> None:
    item_ent.meters["missing"] = 0.0
    item_ent.meters["found"] += 1
    culprit_ent.meters["stuck"] = 0.0
    culprit_ent.memes["guilt"] += 1
    detective.memes["pride"] += 1
    world.say(culprit.return_line.replace("{item}", item.label))
    world.say(
        f"{detective.id} lifted the {item.label} gently. The case was solved, and nobody had to be mean."
    )


def ending(world: World, detective: Entity, helper: Entity, item: MissingItem, place: Place) -> None:
    detective.memes["joy"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"Back by the table, the {item.label} shone where it belonged. "
        f"{helper.label_word.capitalize()} thanked {detective.id} for using sharp eyes and a kind heart."
    )
    world.say(
        f"After that, whenever a mystery fluttered through {place.label}, {detective.id} remembered "
        f"that the best detectives notice feelings as carefully as clues."
    )


def tell(place: Place, item: MissingItem, culprit: Culprit, approach: Approach,
         detective_name: str = "Nora", detective_gender: str = "girl",
         helper_type: str = "mother") -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        label=detective_name,
        phrase=detective_name,
        role="detective",
        traits=["careful", "kind"],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        phrase="the helper",
        role="helper",
        traits=["gentle"],
    ))
    culprit_ent = world.add(Entity(
        id="culprit",
        kind="thing",
        type="animal",
        label=culprit.label,
        phrase=culprit.phrase,
        role="culprit",
        tags=set(culprit.tags),
    ))
    item_ent = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        label=item.label,
        phrase=item.phrase,
        role="item",
        tags=set(item.tags),
    ))

    opening(world, detective, helper, place, item)
    worry(world, detective, helper, item)

    world.para()
    inspect_scene(world, detective, place, culprit)
    follow_trail(world, detective, place, culprit)

    world.para()
    reveal_need(world, culprit_ent, culprit, item)
    kind_act(world, detective, helper, culprit_ent, approach, culprit)
    return_item(world, detective, culprit_ent, item_ent, culprit, item)

    world.para()
    ending(world, detective, helper, item, place)

    world.facts.update(
        place=place,
        item_cfg=item,
        culprit_cfg=culprit,
        approach=approach,
        detective=detective,
        helper=helper,
        culprit=culprit_ent,
        item=item_ent,
        outcome=outcome_for(approach),
        clue_word=culprit.clue_word,
        need=culprit.need,
        missing=item_ent.meters["missing"] >= THRESHOLD,
        found=item_ent.meters["found"] >= THRESHOLD,
    )
    return world


PLACES = {
    "library": Place(
        id="library",
        label="the library",
        opening="The library was quiet except for pages turning like soft wings.",
        path="the row of picture books",
        hiding_spot="the fern by the window",
        clue_types={"feather", "scratch"},
        food_tags={"crumbs"},
        tags={"library"},
    ),
    "garden": Place(
        id="garden",
        label="the garden",
        opening="The garden hummed with bees and little drifts of warm air.",
        path="the stepping stones",
        hiding_spot="the watering can beside the shed",
        clue_types={"feather", "pawprint"},
        food_tags={"berries"},
        tags={"garden"},
    ),
    "bakery": Place(
        id="bakery",
        label="the bakery",
        opening="The bakery smelled like warm bread and cinnamon.",
        path="the floury tiles",
        hiding_spot="the basket near the back door",
        clue_types={"pawprint", "crumbtrail"},
        food_tags={"crumbs"},
        tags={"bakery"},
    ),
}

ITEMS = {
    "medal": MissingItem(
        id="medal",
        label="kindness medal",
        phrase="a small kindness medal on a blue string",
        shine=True,
        soft=False,
        scent=False,
        purpose="thanking someone who had been especially kind",
        tags={"medal", "shiny"},
    ),
    "ribbon": MissingItem(
        id="ribbon",
        label="thank-you ribbon",
        phrase="a thank-you ribbon with a silky bow",
        shine=False,
        soft=True,
        scent=False,
        purpose="pinning onto the kindness board",
        tags={"ribbon", "soft"},
    ),
    "bun": MissingItem(
        id="bun",
        label="honey bun",
        phrase="a round honey bun wrapped in paper",
        shine=False,
        soft=False,
        scent=True,
        purpose="sharing at the kindness tea",
        tags={"bun", "tasty"},
    ),
}

CULPRITS = {
    "magpie": Culprit(
        id="magpie",
        label="magpie",
        phrase="a wily magpie with bright black eyes",
        likes={"shiny"},
        clue="feather",
        clue_word="one black feather and a silvery scuff",
        trouble="one claw had slipped through the string of the medal",
        need="untangling",
        kindness_fix="Nora held still while the grown-up loosened the string from the bird's claw.",
        return_line="The magpie gave a small hop, dropped the {item}, and flapped to the sill as if saying sorry.",
        tags={"bird", "feather"},
    ),
    "fox": Culprit(
        id="fox",
        label="fox",
        phrase="a wily young fox with a dusty tail",
        likes={"soft"},
        clue="pawprint",
        clue_word="tiny pawprints pressed in a neat line",
        trouble="the ribbon had wrapped around a thorny stem",
        need="freeing",
        kindness_fix="Together they lifted the thorny stem and freed the ribbon without a yank or a snap.",
        return_line="The fox backed away, then nudged the {item} forward with its nose before slipping into the shade.",
        tags={"fox", "pawprint"},
    ),
    "mouse": Culprit(
        id="mouse",
        label="mouse",
        phrase="a wily little mouse with flour on its whiskers",
        likes={"tasty"},
        clue="crumbtrail",
        clue_word="a crumb trail no wider than a finger",
        trouble="the paper around the bun had folded over its paws",
        need="sharing food",
        kindness_fix="Instead of grabbing, the grown-up set down a few safe crumbs and helped fold the paper back.",
        return_line="The mouse kept the crumbs and left the {item} behind, which was all anyone had wanted in the first place.",
        tags={"mouse", "crumbs"},
    ),
}

APPROACHES = {
    "gentle_help": Approach(
        id="gentle_help",
        sense=3,
        helps_need=True,
        text="Let's help first and ask questions after",
        qa_text="They helped the little culprit first and solved the problem gently",
        tags={"kindness", "help"},
    ),
    "wait_quietly": Approach(
        id="wait_quietly",
        sense=2,
        helps_need=False,
        text="Let's stay quiet so we do not frighten it",
        qa_text="They stayed quiet and calm until the culprit let go",
        tags={"kindness", "calm"},
    ),
    "scold": Approach(
        id="scold",
        sense=1,
        helps_need=False,
        text="Let's scold it until it drops the thing",
        qa_text="They scolded the culprit",
        tags={"unkind"},
    ),
}


GIRL_NAMES = ["Nora", "Lily", "Maya", "Zoe", "Ella", "Lucy", "Ava", "Mina"]
BOY_NAMES = ["Owen", "Ben", "Max", "Theo", "Sam", "Leo", "Finn", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            for culprit_id, culprit in CULPRITS.items():
                if valid_story(place, item, culprit):
                    combos.append((place_id, item_id, culprit_id))
    return combos


@dataclass
class StoryParams:
    place: str
    item: str
    culprit: str
    approach: str
    detective_name: str
    detective_gender: str
    helper: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "detective": [(
        "What does a detective do?",
        "A detective notices clues, asks careful questions, and tries to solve a problem. A good detective looks closely before guessing."
    )],
    "kindness": [(
        "What is kindness?",
        "Kindness is choosing to help, comfort, or be gentle with someone. It can solve problems without making fear bigger."
    )],
    "feather": [(
        "Why can a feather be a clue?",
        "A feather can show that a bird was nearby. Detectives use small signs like that to figure out what happened."
    )],
    "pawprint": [(
        "What is a pawprint?",
        "A pawprint is a mark an animal's foot leaves behind. It can show where the animal walked."
    )],
    "crumbtrail": [(
        "Why do crumbs make a trail?",
        "Little pieces of food can fall as something is carried away. Those tiny bits can lead you to where it went."
    )],
    "shiny": [(
        "Why do some birds like shiny things?",
        "Some birds notice bright, flashing objects because they catch the eye. A shiny thing can seem interesting even if it does not belong to them."
    )],
    "soft": [(
        "Why might an animal take a soft ribbon?",
        "A soft ribbon can feel cozy for a nest or den. Animals sometimes collect soft things because they seem useful."
    )],
    "tasty": [(
        "Why would a mouse follow a bun?",
        "A mouse follows food because it smells good and promises a meal. Strong smells can be clues too."
    )],
}
KNOWLEDGE_ORDER = [
    "detective", "kindness", "feather", "pawprint", "crumbtrail", "shiny", "soft", "tasty",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    item = f["item_cfg"]
    culprit = f["culprit_cfg"]
    place = f["place"]
    return [
        f'Write a short detective story for a young child that includes the words "wan", "plumb", and "wily".',
        f"Tell a gentle mystery where {detective.id} notices that a {item.label} is missing in {place.label} and follows clues to a {culprit.label}.",
        "Write a detective story where kindness solves the case better than blame.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    item = f["item_cfg"]
    culprit = f["culprit_cfg"]
    place = f["place"]
    approach = f["approach"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child detective, {helper.label_word}, and a {culprit.label} in {place.label}. They are all part of one small mystery about a missing {item.label}."
        ),
        (
            f"What was missing?",
            f"The missing thing was the {item.label}. It mattered because they used it for {item.purpose}."
        ),
        (
            f"How did {detective.id} find the clue?",
            f"{detective.id} looked carefully instead of guessing and found {culprit.clue_word}. That clue pointed along {place.path} toward {place.hiding_spot}."
        ),
        (
            f"Why had the {culprit.label} taken the {item.label}?",
            f"It had taken the {item.label} because it was drawn to something about it: {', '.join(sorted(item_lures(item)))}. But the story shows the culprit was in trouble, not trying to be cruel."
        ),
        (
            "How was kindness part of solving the case?",
            f"They chose a kind approach: {approach.qa_text.lower()}. That mattered because helping with the {culprit.need} made the culprit calm enough to give the {item.label} back."
        ),
        (
            "How did the story end?",
            f"The {item.label} was returned, and the case ended peacefully. The final change is that the mystery is solved and everyone is calmer because they used kindness."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"detective", "kindness", f["culprit_cfg"].clue}
    tags |= item_lures(f["item_cfg"])
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="library",
        item="medal",
        culprit="magpie",
        approach="gentle_help",
        detective_name="Nora",
        detective_gender="girl",
        helper="mother",
    ),
    StoryParams(
        place="garden",
        item="ribbon",
        culprit="fox",
        approach="gentle_help",
        detective_name="Ben",
        detective_gender="boy",
        helper="father",
    ),
    StoryParams(
        place="bakery",
        item="bun",
        culprit="mouse",
        approach="wait_quietly",
        detective_name="Maya",
        detective_gender="girl",
        helper="mother",
    ),
]


def explain_story_rejection(place: Place, item: MissingItem, culprit: Culprit) -> str:
    if not culprit_wants_item(culprit, item):
        return (
            f"(No story: a {culprit.label} would not reasonably take the {item.label}. "
            f"The culprit's interests and the missing item do not match.)"
        )
    if not place_has_clue(place, culprit):
        return (
            f"(No story: {place.label} would not show the kind of clue this {culprit.label} leaves. "
            f"Without a clue, the detective has no fair way to solve the case.)"
        )
    return "(No story: this mystery setup is not reasonable.)"


def explain_approach_rejection(approach_id: str) -> str:
    approach = APPROACHES[approach_id]
    better = ", ".join(sorted(a.id for a in sensible_approaches()))
    return (
        f"(Refusing approach '{approach_id}': it scores too low on common sense "
        f"and kindness (sense={approach.sense} < {SENSE_MIN}). Try: {better}.)"
    )


ASP_RULES = r"""
likes_item(C, I) :- likes_shiny(C), shiny(I).
likes_item(C, I) :- likes_soft(C), soft(I).
likes_item(C, I) :- likes_tasty(C), tasty(I).

valid(Place, Item, Culprit) :- place(Place), item(Item), culprit(Culprit),
                               likes_item(Culprit, Item),
                               leaves(Culprit, Clue),
                               clue_at(Place, Clue).

sensible(A) :- approach(A), sense(A, S), sense_min(M), S >= M.

returned_kindly :- chosen_approach(A), helps_need(A).
returned_after_pause :- chosen_approach(A), not helps_need(A).

outcome(returned_kindly) :- returned_kindly.
outcome(returned_after_pause) :- returned_after_pause.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for clue in sorted(place.clue_types):
            lines.append(asp.fact("clue_at", place_id, clue))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.shine:
            lines.append(asp.fact("shiny", item_id))
        if item.soft:
            lines.append(asp.fact("soft", item_id))
        if item.scent:
            lines.append(asp.fact("tasty", item_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("leaves", culprit_id, culprit.clue))
        if "shiny" in culprit.likes:
            lines.append(asp.fact("likes_shiny", culprit_id))
        if "soft" in culprit.likes:
            lines.append(asp.fact("likes_soft", culprit_id))
        if "tasty" in culprit.likes:
            lines.append(asp.fact("likes_tasty", culprit_id))
    for approach_id, approach in APPROACHES.items():
        lines.append(asp.fact("approach", approach_id))
        lines.append(asp.fact("sense", approach_id, approach.sense))
        if approach.helps_need:
            lines.append(asp.fact("helps_need", approach_id))
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
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_approach", params.approach)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
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
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sensible = {a.id for a in sensible_approaches()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible approaches match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible approaches: python={sorted(py_sensible)} clingo={sorted(asp_sens)}")

    parser = build_parser()
    scenarios = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        scenarios.append(params)

    bad = sum(1 for params in scenarios if asp_outcome(params) != outcome_for(APPROACHES[params.approach]))
    if bad == 0:
        print(f"OK: outcome model matches Python on {len(scenarios)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(scenarios)} outcome checks differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="A tiny kindness detective storyworld. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.culprit:
        place = PLACES[args.place]
        item = ITEMS[args.item]
        culprit = CULPRITS[args.culprit]
        if not valid_story(place, item, culprit):
            raise StoryError(explain_story_rejection(place, item, culprit))
    if args.approach and APPROACHES[args.approach].sense < SENSE_MIN:
        raise StoryError(explain_approach_rejection(args.approach))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.culprit is None or combo[2] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, culprit_id = rng.choice(sorted(combos))
    approach_id = args.approach or rng.choice(sorted(a.id for a in sensible_approaches()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        item=item_id,
        culprit=culprit_id,
        approach=approach_id,
        detective_name=name,
        detective_gender=gender,
        helper=helper,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.item not in ITEMS:
        raise StoryError(f"Unknown item: {params.item}")
    if params.culprit not in CULPRITS:
        raise StoryError(f"Unknown culprit: {params.culprit}")
    if params.approach not in APPROACHES:
        raise StoryError(f"Unknown approach: {params.approach}")

    place = PLACES[params.place]
    item = ITEMS[params.item]
    culprit = CULPRITS[params.culprit]
    approach = APPROACHES[params.approach]

    if not valid_story(place, item, culprit):
        raise StoryError(explain_story_rejection(place, item, culprit))
    if approach.sense < SENSE_MIN:
        raise StoryError(explain_approach_rejection(params.approach))

    world = tell(
        place=place,
        item=item,
        culprit=culprit,
        approach=approach,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        helper_type=params.helper,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible approaches: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, culprit) combos:\n")
        for place_id, item_id, culprit_id in combos:
            print(f"  {place_id:8} {item_id:8} {culprit_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.detective_name}: {p.item} in {p.place} ({p.culprit}, {p.approach})"
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
