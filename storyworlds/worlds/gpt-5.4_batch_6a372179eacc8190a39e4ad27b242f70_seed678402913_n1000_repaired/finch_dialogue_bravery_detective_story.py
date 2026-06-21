#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/finch_dialogue_bravery_detective_story.py
====================================================================

A standalone storyworld for a gentle detective story about a child noticing a
small mystery, asking brave questions, and solving it with careful observation.

Seed requirements:
- word: finch
- features: Dialogue, Bravery
- style: Detective Story

Premise
-------
A child has made a tiny detective office. Something shiny or important seems to
be missing. The child follows clues through a yard or park, grows brave enough
to inspect a dark hiding place, speaks kindly with a helper, and discovers that
a little finch carried the object away for its nest. The ending proves the
mystery changed the world: the child returns or replaces the object and leaves a
safe gift for the bird.

The world model uses:
- typed entities with physical meters and emotional memes
- a small forward-chaining rule engine
- explicit reasonableness checks
- an inline ASP twin for the validity gate and the outcome model
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
# from a nested world directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_NEED = 2
HELP_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"             # "character" | "thing" | "animal"
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    dark_spot: str
    ground_detail: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    shiny: bool = False
    light: bool = False
    nest_safe: bool = True
    clue: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    dark: bool = True
    clue_kind: str = ""
    risk: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperMode:
    id: str
    label: str
    sense: int
    comfort: int
    action: str
    qa_action: str
    tags: set[str] = field(default_factory=set)


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


def _r_notice_clue(world: World) -> list[str]:
    out: list[str] = []
    sleuth = world.get("sleuth")
    clue = world.get("clue")
    if clue.meters["visible"] >= THRESHOLD and sleuth.meters["looked"] >= THRESHOLD:
        sig = ("notice_clue",)
        if sig not in world.fired:
            world.fired.add(sig)
            sleuth.meters["has_clue"] += 1
            sleuth.memes["curiosity"] += 1
            out.append("__clue__")
    return out


def _r_dark_fear(world: World) -> list[str]:
    out: list[str] = []
    sleuth = world.get("sleuth")
    hide = world.get("hiding")
    if sleuth.meters["at_hiding"] >= THRESHOLD and hide.meters["shadowy"] >= THRESHOLD:
        sig = ("dark_fear",)
        if sig not in world.fired:
            world.fired.add(sig)
            sleuth.memes["fear"] += 1
            out.append("__fear__")
    return out


def _r_bravery_unlocks_search(world: World) -> list[str]:
    out: list[str] = []
    sleuth = world.get("sleuth")
    if sleuth.memes["brave"] >= BRAVERY_NEED and sleuth.meters["at_hiding"] >= THRESHOLD:
        sig = ("search",)
        if sig not in world.fired:
            world.fired.add(sig)
            sleuth.meters["searched"] += 1
            out.append("__searched__")
    return out


def _r_search_finds_item(world: World) -> list[str]:
    out: list[str] = []
    sleuth = world.get("sleuth")
    item = world.get("item")
    if sleuth.meters["searched"] >= THRESHOLD and item.attrs.get("location") == "nest":
        sig = ("found",)
        if sig not in world.fired:
            world.fired.add(sig)
            item.meters["found"] += 1
            sleuth.meters["solved"] += 1
            sleuth.memes["pride"] += 1
            out.append("__found__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="notice_clue", tag="detective", apply=_r_notice_clue),
    Rule(name="dark_fear", tag="emotion", apply=_r_dark_fear),
    Rule(name="bravery_unlocks_search", tag="emotion", apply=_r_bravery_unlocks_search),
    Rule(name="search_finds_item", tag="detective", apply=_r_search_finds_item),
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


def item_compatible(item: MissingItem, hiding: HidingPlace) -> bool:
    if hiding.clue_kind == "string" and item.id not in {"ribbon", "bell"}:
        return False
    if hiding.clue_kind == "glitter" and not item.shiny:
        return False
    if hiding.clue_kind == "soft" and item.id not in {"ribbon", "note"}:
        return False
    return item.nest_safe


def help_effect(mode: HelperMode) -> int:
    return mode.comfort


def brave_enough(trait: str, mode: HelperMode, hiding: HidingPlace) -> bool:
    base = 2 if trait in {"bold", "steady", "curious"} else 1
    return base + help_effect(mode) >= hiding.risk + 1


def outcome_of(params: "StoryParams") -> str:
    mode = HELPERS[params.helper]
    hiding = HIDING_PLACES[params.hiding_place]
    return "solved" if brave_enough(params.trait, mode, hiding) else "unsolved"


def predict_search(place: Place, item: MissingItem, hiding: HidingPlace, helper: HelperMode, trait: str) -> dict:
    return {
        "compatible": item_compatible(item, hiding),
        "brave_enough": brave_enough(trait, helper, hiding),
    }


def introduce_office(world: World, sleuth: Entity, item: Entity) -> None:
    world.say(
        f"After breakfast, {sleuth.id} opened a tiny detective office in {world.place.label}. "
        f"A paper badge hung from {sleuth.pronoun('possessive')} shirt, and {item.phrase} was the office treasure."
    )
    world.say(
        f'"Detective {sleuth.id} is on duty," {sleuth.pronoun()} whispered. '
        f'"No mystery is too small for me."'
    )


def vanish_item(world: World, sleuth: Entity, item: Entity) -> None:
    item.attrs["location"] = "missing"
    item.meters["missing"] += 1
    sleuth.memes["worry"] += 1
    world.say(
        f"But when {sleuth.pronoun()} reached for {item.label} again, it was gone. "
        f'The little office felt suddenly quiet. "{item.label.capitalize()}?" {sleuth.id} called.'
    )


def question_helper(world: World, sleuth: Entity, helper: Entity) -> None:
    sleuth.memes["curiosity"] += 1
    world.say(
        f'{sleuth.id} hurried to {helper.id}. "Did you see my {world.get("item").label}?" '
        f'{sleuth.pronoun()} asked.'
    )
    world.say(
        f'"Not yet," said {helper.id}, "but detectives start with clues, not guesses."'
    )


def reveal_clue(world: World, clue_text: str) -> None:
    clue = world.get("clue")
    clue.meters["visible"] += 1
    world.get("sleuth").meters["looked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They looked low by {world.place.ground_detail}, and there it was: {clue_text}. "
        "It was tiny, but it did not belong there."
    )


def follow_trail(world: World, sleuth: Entity, helper: Entity, hiding: HidingPlace) -> None:
    sleuth.meters["at_hiding"] += 1
    world.get("hiding").meters["shadowy"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"A real clue points somewhere," said {helper.id}. Together they followed it to {hiding.phrase}.'
    )
    world.say(
        f"{world.place.dark_spot.capitalize()} made the mystery feel bigger than before."
    )


def helper_support(world: World, sleuth: Entity, helper: Entity, mode: HelperMode) -> None:
    sleuth.memes["trust"] += 1
    sleuth.memes["brave"] += float(mode.comfort)
    world.say(
        f'{helper.id} {mode.action} "{sleuth.id}, I will stay right here with you. '
        f'You can be scared and brave at the same time."'
    )


def hesitate_or_search(world: World, sleuth: Entity, hiding: HidingPlace, solved: bool) -> None:
    if solved:
        world.say(
            f'{sleuth.id} swallowed hard and nodded. "Then I am going in," {sleuth.pronoun()} said.'
        )
        propagate(world, narrate=False)
    else:
        world.say(
            f'{sleuth.id} took one step toward {hiding.label}, then stopped. '
            f'"It looks too dark," {sleuth.pronoun()} admitted.'
        )


def find_truth(world: World, sleuth: Entity, item: Entity, finch: Entity, hiding: HidingPlace) -> None:
    item.attrs["location"] = "nest"
    propagate(world, narrate=False)
    world.say(
        f"Inside {hiding.phrase}, {sleuth.id} found a neat little nest. "
        f"There sat a finch, bright-eyed and still."
    )
    world.say(
        f"Beside the twigs lay {item.phrase}. The bird had carried it away because {item.attrs['reason']}."
    )
    world.say(
        f'"So that was the thief," {sleuth.id} whispered, and then smiled. '
        f'"Not mean. Just busy."'
    )
    finch.memes["safe"] += 1


def kind_resolution(world: World, sleuth: Entity, helper: Entity, item: Entity, replacement_text: str) -> None:
    sleuth.memes["relief"] += 1
    sleuth.memes["kindness"] += 1
    world.say(
        f'{helper.id} knelt beside {sleuth.id}. "A good detective tells the true story," '
        f'{helper.pronoun()} said. "And a kind detective thinks about everyone in it."'
    )
    world.say(
        f"So {sleuth.id} left the nest alone, brought back {replacement_text}, and let the finch keep "
        f"what it had already tucked in place."
    )
    world.say(
        f"Then {sleuth.pronoun()} pinned a new note on the detective office door: "
        f'"Mystery solved by brave eyes, quiet feet, and kind words."'
    )


def unsolved_end(world: World, sleuth: Entity, helper: Entity, hiding: HidingPlace, item: Entity) -> None:
    sleuth.memes["relief"] += 1
    world.say(
        f'{helper.id} squeezed {sleuth.pronoun("possessive")} hand. "We do not have to solve every mystery in one minute," '
        f'{helper.pronoun()} said.'
    )
    world.say(
        f"So they stood a safe distance from {hiding.label} and listened. A tiny rustle came from inside, "
        f"and {sleuth.id} guessed a bird might be there with {item.label}."
    )
    world.say(
        f"{sleuth.pronoun().capitalize()} did not crawl in that day. Instead, {sleuth.pronoun()} drew a careful map "
        f"of the place and promised to come back with more daylight and more courage."
    )


def tell(
    place: Place,
    item_cfg: MissingItem,
    hiding_cfg: HidingPlace,
    helper_mode: HelperMode,
    name: str = "Nora",
    gender: str = "girl",
    helper_name: str = "Dad",
    helper_type: str = "father",
    trait: str = "steady",
) -> World:
    world = World(place)
    sleuth = world.add(Entity(id="sleuth", kind="character", type=gender, label=name, role="sleuth", traits=[trait]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, role="helper"))
    item = world.add(Entity(id="item", kind="thing", type=item_cfg.id, label=item_cfg.label, phrase=item_cfg.phrase, tags=set(item_cfg.tags)))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=item_cfg.clue))
    hiding = world.add(Entity(id="hiding", kind="thing", type=hiding_cfg.id, label=hiding_cfg.label, phrase=hiding_cfg.phrase))
    finch = world.add(Entity(id="finch", kind="animal", type="finch", label="finch", phrase="a small finch"))
    sleuth.attrs["name"] = name
    helper.attrs["name"] = helper_name
    item.attrs["reason"] = {
        "ribbon": "its red strip looked like a soft nest string",
        "bell": "the thin string on top looked useful for tying twigs",
        "note": "the paper edge had been torn into soft nesting bits",
    }[item_cfg.id]

    introduce_office(world, sleuth, item)
    vanish_item(world, sleuth, item)

    world.para()
    question_helper(world, sleuth, helper)
    reveal_clue(world, item_cfg.clue)
    follow_trail(world, sleuth, helper, hiding_cfg)
    helper_support(world, sleuth, helper, helper_mode)

    solved = brave_enough(trait, helper_mode, hiding_cfg)

    world.para()
    hesitate_or_search(world, sleuth, hiding_cfg, solved)
    if solved:
        find_truth(world, sleuth, item, finch, hiding_cfg)
        world.para()
        replacement = {
            "ribbon": "a piece of yarn from the craft box",
            "bell": "a soft piece of string from the junk drawer",
            "note": "a little scrap of felt from the sewing basket",
        }[item_cfg.id]
        kind_resolution(world, sleuth, helper, item, replacement)
    else:
        world.para()
        unsolved_end(world, sleuth, helper, hiding_cfg, item)

    world.facts.update(
        sleuth=sleuth,
        helper=helper,
        item_cfg=item_cfg,
        hiding_cfg=hiding_cfg,
        helper_mode=helper_mode,
        place=place,
        solved=solved,
        brave=sleuth.memes["brave"] >= THRESHOLD,
        found=item.meters["found"] >= THRESHOLD,
        item=item,
        finch=finch,
        clue_text=item_cfg.clue,
        outcome="solved" if solved else "unsolved",
    )
    return world


PLACES = {
    "yard": Place(
        id="yard",
        label="the back yard",
        dark_spot="the shade under the old bench",
        ground_detail="the fence where dandelions leaned",
        affords={"bench", "hedge", "shed"},
        tags={"yard"},
    ),
    "park": Place(
        id="park",
        label="the park",
        dark_spot="the shadow by the blackberry hedge",
        ground_detail="the path beside the swings",
        affords={"hedge", "bench"},
        tags={"park"},
    ),
    "garden": Place(
        id="garden",
        label="the garden",
        dark_spot="the cool corner near the tool shed",
        ground_detail="the rows of marigolds",
        affords={"shed", "hedge"},
        tags={"garden"},
    ),
}

ITEMS = {
    "ribbon": MissingItem(
        id="ribbon",
        label="ribbon",
        phrase="a red ribbon with a gold edge",
        shiny=True,
        clue="a thread of red caught on a twig",
        tags={"ribbon", "nest"},
    ),
    "bell": MissingItem(
        id="bell",
        label="bell",
        phrase="a tiny silver bell from the detective bag",
        shiny=True,
        clue="a bright wink of silver near the grass",
        tags={"bell", "shiny", "nest"},
    ),
    "note": MissingItem(
        id="note",
        label="note",
        phrase="a folded detective note written in blue crayon",
        shiny=False,
        clue="a torn scrap of blue paper under a leaf",
        tags={"note", "paper", "nest"},
    ),
}

HIDING_PLACES = {
    "bench": HidingPlace(
        id="bench",
        label="the old bench",
        phrase="the dark space under the old bench",
        dark=True,
        clue_kind="string",
        risk=1,
        tags={"bench", "dark"},
    ),
    "hedge": HidingPlace(
        id="hedge",
        label="the hedge",
        phrase="the prickly hollow in the hedge",
        dark=True,
        clue_kind="soft",
        risk=2,
        tags={"hedge", "dark"},
    ),
    "shed": HidingPlace(
        id="shed",
        label="the tool shed doorway",
        phrase="the narrow gap beside the tool shed doorway",
        dark=True,
        clue_kind="glitter",
        risk=2,
        tags={"shed", "dark"},
    ),
}

HELPERS = {
    "kneel_and_wait": HelperMode(
        id="kneel_and_wait",
        label="kneel and wait",
        sense=3,
        comfort=1,
        action="knelt down so their shoulders were almost touching and said,",
        qa_action="knelt beside the child and stayed close",
        tags={"bravery", "adult_help"},
    ),
    "hold_hand": HelperMode(
        id="hold_hand",
        label="hold hand",
        sense=3,
        comfort=2,
        action="held out a hand and said,",
        qa_action="held out a hand and offered calm company",
        tags={"bravery", "adult_help"},
    ),
    "lantern": HelperMode(
        id="lantern",
        label="bring lantern",
        sense=2,
        comfort=2,
        action='set down a little battery lantern and said,',
        qa_action="brought a battery lantern and stayed nearby",
        tags={"bravery", "light"},
    ),
    "shoo_bird": HelperMode(
        id="shoo_bird",
        label="shoo bird loudly",
        sense=1,
        comfort=0,
        action='clapped once and said,',
        qa_action="made a loud fuss that could scare a small bird",
        tags={"bad_help"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Ella", "Lucy", "Rose", "Maya"]
BOY_NAMES = ["Ben", "Max", "Leo", "Finn", "Sam", "Theo", "Jack", "Noah"]
TRAITS = ["steady", "curious", "bold", "careful", "quiet"]
HELPER_NAMES = {
    "mother": ["Mom", "Mama"],
    "father": ["Dad", "Papa"],
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            for hiding_id, hiding in HIDING_PLACES.items():
                for helper_id, helper in HELPERS.items():
                    if hiding_id in place.affords and item_compatible(item, hiding) and helper.sense >= HELP_MIN:
                        combos.append((place_id, item_id, hiding_id, helper_id))
    return combos


@dataclass
class StoryParams:
    place: str
    item: str
    hiding_place: str
    helper: str
    name: str
    gender: str
    helper_type: str
    helper_name: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "finch": [
        (
            "What is a finch?",
            "A finch is a small bird with a short beak. Many finches gather grass, string, and soft bits to build nests."
        )
    ],
    "nest": [
        (
            "Why do birds build nests?",
            "Birds build nests to hold their eggs and keep their babies safe. They look for soft, light materials they can carry."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. Detectives look closely at clues instead of guessing."
        )
    ],
    "bravery": [
        (
            "Can someone feel scared and brave at the same time?",
            "Yes. Bravery does not mean having no fear; it means doing the careful right thing even while you feel afraid."
        )
    ],
    "light": [
        (
            "Why is a battery lantern useful in a dark place?",
            "A battery lantern helps you see without using fire. Good light can make a careful search safer."
        )
    ],
    "shiny": [
        (
            "Why might a bird notice something shiny?",
            "Shiny things catch the eye because they flash in the light. A bird may inspect them out of curiosity."
        )
    ],
}
KNOWLEDGE_ORDER = ["clue", "finch", "nest", "bravery", "light", "shiny"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sleuth = f["sleuth"]
    item = f["item_cfg"]
    hiding = f["hiding_cfg"]
    outcome = f["outcome"]
    prompts = [
        f'Write a short detective story for a 3-to-5-year-old that includes the word "finch".',
        f"Tell a gentle mystery where {sleuth.attrs['name']} follows a clue to {hiding.label} after {item.label} goes missing.",
        'Write a story with dialogue and bravery where a child solves a tiny outdoor mystery by looking closely and speaking kindly.',
    ]
    if outcome == "unsolved":
        prompts.append(
            f"Make the mystery end with a careful promise to come back later, instead of rushing into {hiding.label}."
        )
    else:
        prompts.append(
            f"End with the child learning that a finch took the {item.label} for its nest, and show a kind solution."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sleuth = f["sleuth"]
    helper = f["helper"]
    item_cfg = f["item_cfg"]
    hiding = f["hiding_cfg"]
    helper_mode = f["helper_mode"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {sleuth.attrs['name']}, a small detective, and {helper.attrs['name']}, who helps with the mystery. The missing thing is {item_cfg.phrase}."
        ),
        (
            f"What mystery did {sleuth.attrs['name']} try to solve?",
            f"{sleuth.attrs['name']} was trying to find the missing {item_cfg.label}. The search began when it vanished from the little detective office."
        ),
        (
            "What clue did they find?",
            f"They found {f['clue_text']}. That clue mattered because it pointed away from guessing and toward a real trail."
        ),
        (
            f"Why did {sleuth.attrs['name']} need bravery?",
            f"{sleuth.attrs['name']} had to go near {hiding.label}, which felt dark and a little scary. The brave part was looking carefully anyway instead of pretending the mystery was not there."
        ),
        (
            f"How did the helper support the detective?",
            f"{helper.attrs['name']} {helper_mode.qa_action}. That calm help made it easier for {sleuth.attrs['name']} to keep going."
        ),
    ]
    if f["outcome"] == "solved":
        out.append(
            (
                "Who took the missing thing?",
                f"A finch had carried it to a nest. The bird was not being naughty; it was gathering useful nest material."
            )
        )
        out.append(
            (
                "How did the story end?",
                f"The mystery was solved kindly. {sleuth.attrs['name']} left the nest alone and brought a safer replacement instead, which shows the detective cared about the finch too."
            )
        )
    else:
        out.append(
            (
                "Did the detective solve the mystery right away?",
                f"No. {sleuth.attrs['name']} stopped before going into the dark place. That choice was still brave because it kept the search careful and safe."
            )
        )
        out.append(
            (
                "How did the story end?",
                f"It ended with a plan instead of a full answer. {sleuth.attrs['name']} made a map and promised to come back with more light and more courage."
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"clue", "finch", "bravery", "nest"}
    if world.facts["helper_mode"].id == "lantern":
        tags.add("light")
    if world.facts["item_cfg"].shiny:
        tags.add("shiny")
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="yard",
        item="ribbon",
        hiding_place="bench",
        helper="hold_hand",
        name="Nora",
        gender="girl",
        helper_type="father",
        helper_name="Dad",
        trait="steady",
    ),
    StoryParams(
        place="park",
        item="note",
        hiding_place="hedge",
        helper="lantern",
        name="Ben",
        gender="boy",
        helper_type="mother",
        helper_name="Mom",
        trait="bold",
    ),
    StoryParams(
        place="garden",
        item="bell",
        hiding_place="shed",
        helper="kneel_and_wait",
        name="Mia",
        gender="girl",
        helper_type="father",
        helper_name="Papa",
        trait="careful",
    ),
    StoryParams(
        place="park",
        item="ribbon",
        hiding_place="hedge",
        helper="hold_hand",
        name="Leo",
        gender="boy",
        helper_type="mother",
        helper_name="Mama",
        trait="quiet",
    ),
]


def explain_combo(place: Place, item: MissingItem, hiding: HidingPlace, helper: HelperMode) -> str:
    if hiding.id not in place.affords:
        return f"(No story: {place.label} does not have a clue trail leading to {hiding.label}.)"
    if not item_compatible(item, hiding):
        return (
            f"(No story: {item.label} does not make a believable clue for {hiding.label}. "
            f"The mystery needs a trail a child could honestly follow.)"
        )
    if helper.sense < HELP_MIN:
        return (
            f"(No story: helper mode '{helper.id}' is too noisy or unhelpful for this gentle detective world. "
            f"Choose a calmer kind of help.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
allowed_place_hiding(P, H) :- place(P), hiding(H), affords(P, H).
compatible(I, H) :- item(I), hiding(H), clue_kind(H, string), string_item(I), nest_safe(I).
compatible(I, H) :- item(I), hiding(H), clue_kind(H, glitter), shiny(I), nest_safe(I).
compatible(I, H) :- item(I), hiding(H), clue_kind(H, soft), soft_item(I), nest_safe(I).

sensible_helper(M) :- helper(M), sense(M, S), help_min(Min), S >= Min.

valid(P, I, H, M) :- allowed_place_hiding(P, H), compatible(I, H), sensible_helper(M).

base_bravery(2) :- chosen_trait(T), strong_trait(T).
base_bravery(1) :- chosen_trait(T), not strong_trait(T).
brave_total(B + C) :- base_bravery(B), chosen_helper(M), comfort(M, C).
needed(R + 1) :- chosen_hiding(H), risk(H, R).

solved :- brave_total(BT), needed(N), BT >= N.
outcome(solved) :- solved.
outcome(unsolved) :- not solved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        for hid in sorted(PLACES[pid].affords):
            lines.append(asp.fact("affords", pid, hid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.shiny:
            lines.append(asp.fact("shiny", iid))
        if item.nest_safe:
            lines.append(asp.fact("nest_safe", iid))
        if iid in {"ribbon", "bell"}:
            lines.append(asp.fact("string_item", iid))
        if iid in {"ribbon", "note"}:
            lines.append(asp.fact("soft_item", iid))
    for hid, hiding in HIDING_PLACES.items():
        lines.append(asp.fact("hiding", hid))
        lines.append(asp.fact("clue_kind", hid, hiding.clue_kind))
        lines.append(asp.fact("risk", hid, hiding.risk))
    for mid, mode in HELPERS.items():
        lines.append(asp.fact("helper", mid))
        lines.append(asp.fact("sense", mid, mode.sense))
        lines.append(asp.fact("comfort", mid, mode.comfort))
    for tr in TRAITS:
        lines.append(asp.fact("trait", tr))
    for tr in {"bold", "steady", "curious"}:
        lines.append(asp.fact("strong_trait", tr))
    lines.append(asp.fact("help_min", HELP_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_trait", params.trait),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_hiding", params.hiding_place),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    mismatches = []
    for params in cases:
        ao = asp_outcome(params)
        po = outcome_of(params)
        if ao != po:
            mismatches.append((params, ao, po))
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny detective mystery with a finch, dialogue, and bravery."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hiding-place", dest="hiding_place", choices=HIDING_PLACES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", dest="helper_type", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.hiding_place and args.helper:
        place = PLACES[args.place]
        item = ITEMS[args.item]
        hiding = HIDING_PLACES[args.hiding_place]
        helper = HELPERS[args.helper]
        if not (args.hiding_place in place.affords and item_compatible(item, hiding) and helper.sense >= HELP_MIN):
            raise StoryError(explain_combo(place, item, hiding, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.hiding_place is None or combo[2] == args.hiding_place)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, hiding_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["mother", "father"])
    helper_name = rng.choice(HELPER_NAMES[helper_type])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        item=item_id,
        hiding_place=hiding_id,
        helper=helper_id,
        name=name,
        gender=gender,
        helper_type=helper_type,
        helper_name=helper_name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.item not in ITEMS:
        raise StoryError(f"Unknown item: {params.item}")
    if params.hiding_place not in HIDING_PLACES:
        raise StoryError(f"Unknown hiding place: {params.hiding_place}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")
    place = PLACES[params.place]
    item = ITEMS[params.item]
    hiding = HIDING_PLACES[params.hiding_place]
    helper_mode = HELPERS[params.helper]
    if not (params.hiding_place in place.affords and item_compatible(item, hiding) and helper_mode.sense >= HELP_MIN):
        raise StoryError(explain_combo(place, item, hiding, helper_mode))

    world = tell(
        place=place,
        item_cfg=item,
        hiding_cfg=hiding,
        helper_mode=helper_mode,
        name=params.name,
        gender=params.gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render().replace("sleuth", params.name),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    story = sample.story
    world = sample.world
    if world is not None:
        story = story.replace("sleuth", sample.params.name).replace("helper", sample.params.helper_name)
    if header:
        print(header)
    print(story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, hiding_place, helper) combos:\n")
        for place, item, hiding, helper in combos:
            print(f"  {place:7} {item:7} {hiding:6} {helper}")
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
            header = f"### {p.name}: {p.item} at {p.place} -> {p.hiding_place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
