#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/contour_whoop_medium_mystery_to_solve_curiosity.py
==============================================================================

A standalone story world about small animals solving a cozy mystery with
curiosity, clues, and kindness.

Seed ingredients rebuilt as a world model
-----------------------------------------
Words: contour, whoop, medium
Features: Mystery to Solve, Curiosity
Style: Animal Story

Premise
-------
A little animal notices that an important picnic object is missing. A soft
whoop comes from somewhere nearby. Instead of panicking, two curious friends
follow a clue with a clear contour and solve the mystery. The "culprit" is
never cruel -- only embarrassed, helpful, or busy -- so the resolution turns on
kindness as much as detection.

Why this world has a gate
-------------------------
Not every animal would plausibly borrow every object, and not every way of
investigating would honestly solve the mystery. This sketch refuses weak
pairings. A culprit must have a believable reason to borrow the missing item,
and the investigation method must match where that culprit actually lives.

Examples
--------
    python storyworlds/worlds/gpt-5.4/contour_whoop_medium_mystery_to_solve_curiosity.py
    python storyworlds/worlds/gpt-5.4/contour_whoop_medium_mystery_to_solve_curiosity.py --item bell --culprit owl
    python storyworlds/worlds/gpt-5.4/contour_whoop_medium_mystery_to_solve_curiosity.py --culprit beaver --method look_up
    python storyworlds/worlds/gpt-5.4/contour_whoop_medium_mystery_to_solve_curiosity.py --all
    python storyworlds/worlds/gpt-5.4/contour_whoop_medium_mystery_to_solve_curiosity.py --verify
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

# Make shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # character | thing
    type: str = "thing"          # rabbit, squirrel, owl, item, clue, place
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Place:
    id: str
    label: str
    opening: str
    search_path: str
    ending_image: str


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    type: str
    home: str
    entry: str
    whoop: str
    contour: str
    contour_shape: str
    method: str
    likes: set[str] = field(default_factory=set)
    reason: str = ""
    fix: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    action: str
    success: str


PLACES = {
    "berry_glade": Place(
        "berry_glade",
        "Berry Glade",
        "In Berry Glade, the grass was silver with morning dew and the berry leaves held tiny drops like beads.",
        "the winding path between berry bushes",
        "the picnic cloth lay smooth again under the berry bushes",
    ),
    "mossy_bank": Place(
        "mossy_bank",
        "Mossy Bank",
        "At Mossy Bank, the stream slid past smooth stones and the moss looked soft enough for a nap.",
        "the narrow path beside the stream",
        "the stream kept whispering while the friends sat together on the moss",
    ),
    "fern_ring": Place(
        "fern_ring",
        "Fern Ring",
        "In Fern Ring, tall ferns made green arches and every step stirred a cool leafy smell.",
        "the little trail between fern stems",
        "the ferns nodded over the happy little group",
    ),
}

ITEMS = {
    "bell": Item(
        "bell",
        "bell",
        "the brass picnic bell",
        "to ring everyone together for tea",
        tags={"shiny", "ringing"},
    ),
    "ribbon": Item(
        "ribbon",
        "ribbon",
        "the blue satin ribbon",
        "to tie the picnic napkins in a bright bow",
        tags={"soft", "tying"},
    ),
    "basket": Item(
        "basket",
        "basket",
        "the woven berry basket",
        "to carry berries and seed cakes",
        tags={"woven", "carrying"},
    ),
}

METHODS = {
    "look_up": Method(
        "look_up",
        "look up",
        "tilt their noses high and search the branches",
        "The clue pointed upward, so the branches were the sensible place to look.",
    ),
    "follow_water": Method(
        "follow_water",
        "follow the water",
        "pad along the wet edge of the stream",
        "The clue was damp and flat, so the streamside trail made the most sense.",
    ),
    "feel_breeze": Method(
        "feel_breeze",
        "feel for the breeze",
        "stand still until they felt tiny puffs of air from the ground",
        "The clue came with a low airy sound, so a breezy burrow was the sensible place to check.",
    ),
}

CULPRITS = {
    "owl": Culprit(
        "owl",
        "Old Nori the owl",
        "owl",
        "a fir-tree nest",
        "high in a fir tree",
        'From above came a round little "whoop."',
        "a feather-soft contour in the dust",
        "feather-soft",
        "look_up",
        likes={"shiny", "soft"},
        reason="was lining the nest and had borrowed it because it looked light and lovely",
        fix="carefully flew down and set it back on the picnic cloth",
        tags={"owl", "tree", "nest"},
    ),
    "beaver": Culprit(
        "beaver",
        "Bram the beaver",
        "beaver",
        "a snug dam-house",
        "by the bend of the stream",
        'From the reeds came a hollow "whoop" when the wind slid through them.',
        "a flat tail contour pressed into the mud",
        "flat-tailed",
        "follow_water",
        likes={"tying", "woven"},
        reason="was mending the dam and had borrowed it because it looked useful for tying and carrying",
        fix="hustled over with wet paws and returned it at once",
        tags={"beaver", "stream", "dam"},
    ),
    "mole": Culprit(
        "mole",
        "Pip the mole",
        "mole",
        "a neat burrow",
        "near a small hillock of crumbly earth",
        'From a tiny hole came a deep little "whoop" as the breeze puffed through.',
        "a rounded paw contour in the soft earth",
        "rounded-paw",
        "feel_breeze",
        likes={"carrying", "ringing"},
        reason="was tidying the burrow and had borrowed it because it helped carry pebbles or chimed when tunnel doors swung",
        fix="popped up, blushed, and pushed it back with both paws",
        tags={"mole", "burrow", "earth"},
    ),
}

GIRL_NAMES = ["Mimi", "Tansy", "Poppy", "Lulu", "Nell", "Daisy"]
BOY_NAMES = ["Pip", "Toby", "Moss", "Finn", "Rory", "Ollie"]
ANIMALS = ["rabbit", "squirrel", "mouse", "hedgehog"]


def compatible(culprit: Culprit, item: Item) -> bool:
    return bool(culprit.likes & item.tags)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place in PLACES:
        for item_id, item in ITEMS.items():
            for culprit_id, culprit in CULPRITS.items():
                if compatible(culprit, item):
                    combos.append((place, item_id, culprit_id, culprit.method))
    return combos


# ---------------------------------------------------------------------------
# World and rules
# ---------------------------------------------------------------------------
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


def _r_missing(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return []
    out: list[str] = []
    for eid in ("seeker", "helper"):
        ent = world.get(eid)
        sig = ("missing", eid)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 1
        ent.memes["curiosity"] += 1
        out.append("")
    return out


def _r_clue(world: World) -> list[str]:
    clue = world.get("clue")
    if clue.meters["seen"] < THRESHOLD:
        return []
    out: list[str] = []
    for eid in ("seeker", "helper"):
        ent = world.get(eid)
        sig = ("clue", eid)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["curiosity"] += 1
        ent.memes["certainty"] += 1
        out.append("")
    return out


def _r_solve(world: World) -> list[str]:
    if world.facts.get("method_ok") is not True:
        return []
    if world.get("trail").meters["followed"] < THRESHOLD:
        return []
    sig = ("solved",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("item").meters["found"] += 1
    world.get("culprit").memes["embarrassed"] += 1
    for eid in ("seeker", "helper"):
        world.get(eid).memes["certainty"] += 1
    return [""]


CAUSAL_RULES = [
    Rule("missing", "emotional", _r_missing),
    Rule("clue", "emotional", _r_clue),
    Rule("solve", "plot", _r_solve),
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
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Verbs and screenplay
# ---------------------------------------------------------------------------
def opening(world: World, place: Place, seeker: Entity, helper: Entity, item: Item) -> None:
    world.say(place.opening)
    world.say(
        f"{seeker.id} the {seeker.type} and {helper.id} the {helper.type} were laying out acorn cakes and berry tea."
    )
    world.say(
        f"They needed {item.phrase} {item.use}, but when {seeker.id} reached for it, the place where it belonged was empty."
    )
    world.get("item").meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{seeker.id}'s whiskers twitched. {helper.id}'s eyes grew round. A mystery had tiptoed into the morning."
    )


def hear_whoop(world: World, culprit: Culprit, seeker: Entity, helper: Entity) -> None:
    for eid in ("seeker", "helper"):
        world.get(eid).memes["curiosity"] += 1
    world.say(culprit.whoop)
    world.say(
        f'"Did you hear that whoop?" whispered {helper.id}. Instead of running away, the two friends leaned closer, curious.'
    )


def find_clue(world: World, culprit: Culprit) -> None:
    clue = world.get("clue")
    clue.meters["seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"On the ground nearby lay {culprit.contour}, clear enough to study. It made a medium curve in the dust, and its contour looked too careful to be an accident."
    )


def guess(world: World, seeker: Entity, helper: Entity, culprit: Culprit) -> None:
    seeker.memes["wonder"] += 1
    helper.memes["wonder"] += 1
    world.say(
        f'"Someone came this way on purpose," said {seeker.id}. "{culprit.contour_shape.capitalize()} marks do not walk all by themselves."'
    )
    world.say(
        f'{helper.id} nodded. "Let us keep our paws gentle and our eyes open. Curiosity can be brave when it is kind."'
    )


def follow(world: World, place: Place, method: Method) -> None:
    trail = world.get("trail")
    trail.meters["followed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So they chose to {method.action} along {place.search_path}. {method.success}"
    )


def reveal(world: World, culprit_cfg: Culprit, item_cfg: Item, seeker: Entity, helper: Entity) -> None:
    culprit = world.get("culprit")
    item = world.get("item")
    item.meters["borrowed"] += 1
    world.say(
        f"The trail led {helper.id} and {seeker.id} to {culprit_cfg.entry}. There they found {culprit_cfg.label} beside {item_cfg.phrase}."
    )
    world.say(
        f'{culprit_cfg.label} gave a small guilty blink and admitted that {culprit_cfg.reason}.'
    )
    culprit.memes["relief"] += 1
    culprit.memes["kindness_seen"] += 1


def ask_kindly(world: World, seeker: Entity, helper: Entity, culprit_cfg: Culprit, item_cfg: Item) -> None:
    for eid in ("seeker", "helper"):
        world.get(eid).memes["kindness"] += 1
    world.say(
        f'"We were worried," said {seeker.id}, "but we are glad we asked instead of guessing."'
    )
    world.say(
        f'"Could we please have {item_cfg.phrase} back for the picnic?" asked {helper.id}.'
    )
    world.say(
        f"Because their voices were gentle, {culprit_cfg.label} did not hide or huff."
    )


def restore(world: World, culprit_cfg: Culprit, item_cfg: Item, place: Place) -> None:
    item = world.get("item")
    item.meters["missing"] = 0.0
    item.meters["returned"] += 1
    for eid in ("seeker", "helper"):
        ent = world.get(eid)
        ent.memes["worry"] = 0.0
        ent.memes["relief"] += 1
        ent.memes["joy"] += 1
    world.get("culprit").memes["embarrassed"] = 0.0
    world.say(
        f"{culprit_cfg.label} {culprit_cfg.fix}. Soon the missing thing was back where it belonged."
    )
    world.say(
        f"By picnic time, {place.ending_image}, and the solved mystery felt warmer than the sun."
    )


def closing(world: World, seeker: Entity, helper: Entity, item_cfg: Item) -> None:
    world.say(
        f"{helper.id} rang, tied, or lifted {item_cfg.label} into place, and {seeker.id} gave a happy little laugh."
    )
    world.say(
        "They had learned that a strange sound and a curious contour did not have to mean danger. Sometimes they meant there was a question waiting for patient hearts."
    )


def tell(place: Place, item_cfg: Item, culprit_cfg: Culprit, method: Method,
         seeker_name: str = "Mimi", seeker_type: str = "rabbit",
         helper_name: str = "Pip", helper_type: str = "mouse",
         elder_type: str = "hedgehog") -> World:
    world = World()

    seeker = world.add(Entity(id=seeker_name, kind="character", type=seeker_type, role="seeker"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, role="elder", label="the elder"))
    item = world.add(Entity(id="item", kind="thing", type="item", label=item_cfg.label))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label="the clue"))
    trail = world.add(Entity(id="trail", kind="thing", type="trail", label="the trail"))
    culprit = world.add(Entity(id="culprit", kind="character", type=culprit_cfg.type, role="culprit", label=culprit_cfg.label))
    place_ent = world.add(Entity(id="place", kind="thing", type="place", label=place.label))

    world.facts["method_ok"] = method.id == culprit_cfg.method
    world.facts["compatible"] = compatible(culprit_cfg, item_cfg)
    if not world.facts["compatible"]:
        raise StoryError(explain_item_rejection(item_cfg, culprit_cfg))
    if not world.facts["method_ok"]:
        raise StoryError(explain_method_rejection(method, culprit_cfg))

    opening(world, place, seeker, helper, item_cfg)
    world.para()
    hear_whoop(world, culprit_cfg, seeker, helper)
    find_clue(world, culprit_cfg)
    guess(world, seeker, helper, culprit_cfg)
    world.para()
    follow(world, place, method)
    reveal(world, culprit_cfg, item_cfg, seeker, helper)
    ask_kindly(world, seeker, helper, culprit_cfg, item_cfg)
    world.para()
    restore(world, culprit_cfg, item_cfg, place)
    closing(world, seeker, helper, item_cfg)

    world.facts.update(
        place=place,
        item_cfg=item_cfg,
        culprit_cfg=culprit_cfg,
        method_cfg=method,
        seeker=seeker,
        helper=helper,
        elder=elder,
        item=item,
        clue=clue,
        culprit=culprit,
        solved=item.meters["returned"] >= THRESHOLD,
    )
    _ = place_ent
    return world


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    item: str
    culprit: str
    method: str
    seeker: str
    seeker_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "owl": [(
        "What kind of sound can an owl make?",
        "An owl can make a soft hoot or whoop. People often hear it best when everything else is quiet."
    )],
    "tree": [(
        "Why do birds build nests high up?",
        "High branches help keep a nest safe and dry. They also give the bird a good view of the ground."
    )],
    "beaver": [(
        "What does a beaver use to build a dam?",
        "A beaver uses sticks, mud, and other useful things it can carry or wedge into place. That helps slow the water and shape a safe home."
    )],
    "stream": [(
        "Why does wind sometimes make a whoop in the reeds?",
        "When air moves through hollow reeds, it can make a round hollow sound. The shape of the reeds changes the sound you hear."
    )],
    "mole": [(
        "Why do moles live underground?",
        "Moles dig burrows under the ground where the soil is soft. Underground tunnels help them move and hide safely."
    )],
    "burrow": [(
        "How can a burrow make a sound?",
        "If air moves through a small tunnel opening, the hole can whistle or whoop a little. The shape of the opening changes the sound."
    )],
    "shiny": [(
        "Why do some animals notice shiny things?",
        "Bright shiny objects stand out in the light, so they are easy to notice. Some animals become curious about them for that reason."
    )],
    "soft": [(
        "Why might an animal want something soft for a nest?",
        "Soft things can make a nest warmer and gentler. They help eggs or sleepy bodies rest comfortably."
    )],
    "woven": [(
        "Why is a basket good for carrying things?",
        "A basket has sides that hold many small things together. That makes it easier to carry berries, seeds, or pebbles."
    )],
    "curiosity": [(
        "What does curiosity mean?",
        "Curiosity means wanting to find out more. It can help you solve a mystery when you stay calm and careful."
    )],
}
KNOWLEDGE_ORDER = ["curiosity", "owl", "tree", "beaver", "stream", "mole", "burrow", "shiny", "soft", "woven"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker, helper = f["seeker"], f["helper"]
    item, culprit, place = f["item_cfg"], f["culprit_cfg"], f["place"]
    return [
        f'Write a gentle animal story for a 3-to-5-year-old about a mystery to solve with curiosity. Include the words "contour", "whoop", and "medium".',
        f"Tell a cozy mystery where {seeker.id} the {seeker.type} and {helper.id} the {helper.type} notice that {item.phrase} is missing in {place.label} and follow a clue to {culprit.label}.",
        f"Write a child-facing story where a strange whoop and a careful contour clue seem mysterious at first, but kindness helps the little animals solve the problem."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker, helper = f["seeker"], f["helper"]
    item, culprit, place, method = f["item_cfg"], f["culprit_cfg"], f["place"], f["method_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {seeker.id} the {seeker.type} and {helper.id} the {helper.type}. They were getting ready for a picnic in {place.label} when they found a mystery."
        ),
        (
            f"What was missing?",
            f"{item.phrase} was missing. They needed it {item.use}, so its empty place felt important right away."
        ),
        (
            "What clue did they find?",
            f"They heard a soft whoop and then saw {culprit.contour}. The medium curve of that contour told them someone had really passed that way."
        ),
        (
            f"How did they solve the mystery?",
            f"They chose to {method.label} and followed the clue in the most sensible direction. That led them to {culprit.label}, who had borrowed the missing item for a reason instead of stealing it meanly."
        ),
        (
            f"Why did {culprit.label} have the missing thing?",
            f"{culprit.label} had it because {culprit.reason}. The mystery looked scary at first, but the real cause was need and embarrassment, not cruelty."
        ),
        (
            "How did the story end?",
            f"The friends asked kindly, and {culprit.label} returned the item. The ending shows everyone calmer and happier because curiosity led to understanding."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    culprit = f["culprit_cfg"]
    item = f["item_cfg"]
    tags = set(culprit.tags) | {"curiosity"} | set(item.tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Explanations and outcome
# ---------------------------------------------------------------------------
def explain_item_rejection(item: Item, culprit: Culprit) -> str:
    return (
        f"(No story: {culprit.label} has no good reason to borrow {item.phrase}. "
        f"This world only allows pairings where the missing item matches the culprit's needs.)"
    )


def explain_method_rejection(method: Method, culprit: Culprit) -> str:
    return (
        f"(No story: the method '{method.id}' does not fit {culprit.label}. "
        f"A fair mystery should be solved by searching where that animal really lives; "
        f"try --method {culprit.method}.)"
    )


def outcome_of(params: StoryParams) -> str:
    item = ITEMS[params.item]
    culprit = CULPRITS[params.culprit]
    method = METHODS[params.method]
    if not compatible(culprit, item):
        return "invalid"
    if method.id != culprit.method:
        return "invalid"
    return "solved"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
compatible(C, I) :- culprit(C), item(I), likes(C, T), item_tag(I, T).
method_ok(C, M)  :- culprit(C), home_method(C, M).

valid(P, I, C, M) :- place(P), item(I), culprit(C), method(M),
                     compatible(C, I), method_ok(C, M).

outcome(solved) :- chosen_item(I), chosen_culprit(C), chosen_method(M),
                   compatible(C, I), method_ok(C, M).
outcome(invalid) :- chosen_item(I), chosen_culprit(C), chosen_method(M),
                    not compatible(C, I).
outcome(invalid) :- chosen_item(I), chosen_culprit(C), chosen_method(M),
                    compatible(C, I), not method_ok(C, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for tag in sorted(item.tags):
            lines.append(asp.fact("item_tag", iid, tag))
    for mid in METHODS:
        lines.append(asp.fact("method", mid))
    for cid, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        lines.append(asp.fact("home_method", cid, culprit.method))
        for tag in sorted(culprit.likes):
            lines.append(asp.fact("likes", cid, tag))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_culprit", params.culprit),
        asp.fact("chosen_method", params.method),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    cases: list[StoryParams] = list(CURATED)
    for seed in range(20):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during seeded resolve at seed={seed}.")
            break

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    # Smoke-test ordinary generation.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# CLI and interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams("berry_glade", "bell", "owl", "look_up", "Mimi", "rabbit", "Pip", "mouse"),
    StoryParams("mossy_bank", "ribbon", "beaver", "follow_water", "Tansy", "squirrel", "Moss", "hedgehog"),
    StoryParams("fern_ring", "basket", "mole", "feel_breeze", "Poppy", "mouse", "Finn", "rabbit"),
    StoryParams("berry_glade", "ribbon", "owl", "look_up", "Lulu", "rabbit", "Ollie", "squirrel"),
    StoryParams("mossy_bank", "basket", "beaver", "follow_water", "Nell", "hedgehog", "Rory", "mouse"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A cozy animal mystery storyworld with curiosity, clue-following, and kind resolutions."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--seeker")
    ap.add_argument("--seeker-type", choices=ANIMALS)
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=ANIMALS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    animal = rng.choice(ANIMALS)
    pool = [n for n in (GIRL_NAMES + BOY_NAMES) if n != avoid]
    return rng.choice(pool), animal


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.culprit:
        if not compatible(CULPRITS[args.culprit], ITEMS[args.item]):
            raise StoryError(explain_item_rejection(ITEMS[args.item], CULPRITS[args.culprit]))
    if args.culprit and args.method:
        if args.method != CULPRITS[args.culprit].method:
            raise StoryError(explain_method_rejection(METHODS[args.method], CULPRITS[args.culprit]))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.item is None or c[1] == args.item)
        and (args.culprit is None or c[2] == args.culprit)
        and (args.method is None or c[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, item, culprit, method = rng.choice(sorted(combos))
    seeker, seeker_type = (args.seeker, args.seeker_type) if args.seeker and args.seeker_type else pick_name(rng)
    helper, helper_type = (args.helper, args.helper_type) if args.helper and args.helper_type else pick_name(rng, avoid=seeker)
    if args.seeker and not args.seeker_type:
        seeker_type = rng.choice(ANIMALS)
    if args.seeker_type and not args.seeker:
        seeker = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != helper])
    if args.helper and not args.helper_type:
        helper_type = rng.choice(ANIMALS)
    if args.helper_type and not args.helper:
        helper = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != seeker])
    if seeker == helper:
        helper = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != seeker])
    return StoryParams(place, item, culprit, method, seeker, seeker_type, helper, helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        ITEMS[params.item],
        CULPRITS[params.culprit],
        METHODS[params.method],
        params.seeker,
        params.seeker_type,
        params.helper,
        params.helper_type,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, culprit, method) combos:\n")
        for place, item, culprit, method in combos:
            print(f"  {place:11} {item:7} {culprit:8} {method}")
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
            header = f"### {p.seeker} & {p.helper}: {p.item} / {p.culprit} / {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
