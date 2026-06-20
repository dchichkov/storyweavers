#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/zither_mystery_to_solve_detective_story.py
=====================================================================

A standalone story world for a gentle detective-style mystery built around a
zither. A child notices that a small important thing has gone missing just
before music time, studies clues near the zither, and solves what really
happened.

The world model prefers a few physically sensible mysteries over broad coverage:
a breeze can only carry light flat things, a kitten can bat little objects into
reachable nooks, and a toddler can stash something in a basket while "helping."
The clues, search path, and ending all come from simulated state rather than
slot-swapped prose.

Run it
------
    python storyworlds/worlds/gpt-5.4/zither_mystery_to_solve_detective_story.py
    python storyworlds/worlds/gpt-5.4/zither_mystery_to_solve_detective_story.py --cause breeze --item bell_charm
    python storyworlds/worlds/gpt-5.4/zither_mystery_to_solve_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/zither_mystery_to_solve_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/zither_mystery_to_solve_detective_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "teacher", "aunt", "grandmother"}
        male = {"boy", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "teacher": "teacher",
            "aunt": "aunt",
            "grandfather": "grandpa",
            "grandmother": "grandma",
            "friend": "friend",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    intro: str
    zither_spot: str
    affordances: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    actor: str
    phrase: str
    clue: str
    clue_detail: str
    move_verb: str
    motive: str
    movable_items: set[str] = field(default_factory=set)
    hiding_spots: set[str] = field(default_factory=set)
    difficulty: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    light: bool
    flat: bool
    special: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingSpot:
    id: str
    label: str
    phrase: str
    fit_items: set[str] = field(default_factory=set)
    found_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperDef:
    id: str
    name: str
    type: str
    cue: str
    boost: int
    nudge: str
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
    child = world.get("child")
    item = world.get("item")
    if item.meters["missing"] >= THRESHOLD and ("missing_worry",) not in world.fired:
        world.fired.add(("missing_worry",))
        child.memes["worry"] += 1
    return []


def _r_clue_certainty(world: World) -> list[str]:
    child = world.get("child")
    if world.facts.get("clue_found") and ("clue_certainty",) not in world.fired:
        world.fired.add(("clue_certainty",))
        child.memes["certainty"] += 1
        child.memes["curiosity"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    child = world.get("child")
    item = world.get("item")
    if item.meters["found"] >= THRESHOLD and ("found_relief",) not in world.fired:
        world.fired.add(("found_relief",))
        child.memes["worry"] = 0.0
        child.memes["relief"] += 1
        child.memes["pride"] += 1
    return []


CAUSAL_RULES = [
    Rule("missing_worry", "emotional", _r_missing_worry),
    Rule("clue_certainty", "emotional", _r_clue_certainty),
    Rule("found_relief", "emotional", _r_found_relief),
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


PLACES = {
    "music_room": Place(
        "music_room",
        "the music room",
        "Sunlight lay in stripes across the floor, and the old zither waited on its stand by the low window.",
        "on its stand by the low window",
        affordances={"breeze", "kitten", "toddler"},
        tags={"music_room"},
    ),
    "parlor": Place(
        "parlor",
        "the parlor",
        "The parlor smelled like lemon polish, and a honey-colored zither rested beside the armchair.",
        "beside the armchair",
        affordances={"breeze", "kitten", "toddler"},
        tags={"parlor"},
    ),
    "library_corner": Place(
        "library_corner",
        "the library corner",
        "The little library corner was quiet except for page rustles, and a school zither leaned near the curtain.",
        "near the curtain",
        affordances={"breeze", "toddler"},
        tags={"library"},
    ),
}

CAUSES = {
    "breeze": Cause(
        "breeze",
        "a breeze",
        "a sly little breeze from the open window",
        "A page of music was fluttering, and one ribbon of dust pointed toward the curtain.",
        "the open window and dancing pages",
        "lifted",
        "The room had seemed still, but the window had been left open just enough for a draft.",
        movable_items={"ribbon", "music_card"},
        hiding_spots={"curtain_fold", "under_cushion"},
        difficulty=1,
        tags={"breeze", "window"},
    ),
    "kitten": Cause(
        "kitten",
        "the kitten",
        "the house kitten with bright marble eyes",
        "A tiny paw print showed in the dust, and one string on the zither still trembled.",
        "the paw print and the trembling string",
        "batted",
        "The kitten had heard the zing of the zither string and turned the mystery into a game.",
        movable_items={"ribbon", "music_card", "bell_charm"},
        hiding_spots={"under_cushion", "sheet_basket"},
        difficulty=2,
        tags={"kitten", "pet"},
    ),
    "toddler": Cause(
        "toddler",
        "the toddler",
        "a small toddler trying very hard to help",
        "A little chair was crooked, and a sticky finger mark shone on the zither case.",
        "the crooked chair and the sticky finger mark",
        "tucked",
        "The toddler had wanted to tidy up and had hidden the item in the nearest basket.",
        movable_items={"ribbon", "music_card", "bell_charm"},
        hiding_spots={"sheet_basket"},
        difficulty=2,
        tags={"toddler", "family"},
    ),
}

ITEMS = {
    "ribbon": MissingItem(
        "ribbon",
        "blue ribbon",
        "a blue ribbon that the child tied to the music book for luck",
        light=True,
        flat=True,
        special="It was the bright ribbon the child always touched before playing the first note.",
        tags={"ribbon"},
    ),
    "music_card": MissingItem(
        "music_card",
        "music card",
        "a small card with the first tune written on it in neat pencil",
        light=True,
        flat=True,
        special="Without it, the child might forget the opening line of the tune.",
        tags={"music", "card"},
    ),
    "bell_charm": MissingItem(
        "bell_charm",
        "bell charm",
        "a tiny silver bell charm that hung from the zither case",
        light=False,
        flat=False,
        special="It gave one soft tinkle whenever the case was opened, and the child loved that sound.",
        tags={"bell"},
    ),
}

HIDING_SPOTS = {
    "under_cushion": HidingSpot(
        "under_cushion",
        "under the zither cushion",
        "under the little cushion that protected the zither",
        fit_items={"ribbon", "music_card", "bell_charm"},
        found_line="There it was, caught where the soft cushion curled over the wood.",
        tags={"cushion"},
    ),
    "sheet_basket": HidingSpot(
        "sheet_basket",
        "in the sheet-music basket",
        "in the wicker basket of sheet music",
        fit_items={"ribbon", "music_card", "bell_charm"},
        found_line="There it was, tucked between two song sheets like it had been put to bed.",
        tags={"basket"},
    ),
    "curtain_fold": HidingSpot(
        "curtain_fold",
        "inside the curtain fold",
        "inside the heavy fold of the curtain",
        fit_items={"ribbon", "music_card"},
        found_line="There it was, resting in the cloth fold where a draft could carry something light.",
        tags={"curtain"},
    ),
}

HELPERS = {
    "teacher": HelperDef(
        "teacher",
        "Ms. Vale",
        "teacher",
        "calm teacher eyes",
        1,
        '"Good detectives do not guess. They notice what the room is already telling them."',
        tags={"teacher"},
    ),
    "grandpa": HelperDef(
        "grandpa",
        "Grandpa Reed",
        "grandfather",
        "slow patient steps",
        1,
        '"Listen first, then look. A clue likes to be found in the quiet."',
        tags={"grandpa"},
    ),
    "friend": HelperDef(
        "friend",
        "Pip",
        "friend",
        "eager friend energy",
        0,
        '"Let us search where the clue points, not everywhere at once."',
        tags={"friend"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Sophie", "Tess", "Nora", "Eva", "Lucy", "June"]
BOY_NAMES = ["Owen", "Max", "Theo", "Ben", "Milo", "Eli", "Finn", "Sam"]
TRAITS = ["observant", "careful", "bold", "curious", "patient", "thoughtful"]
KEEN_TRAITS = {"observant", "careful", "thoughtful"}


def item_fits(item: MissingItem, hiding: HidingSpot) -> bool:
    return item.id in hiding.fit_items


def cause_can_move(cause: Cause, item: MissingItem) -> bool:
    return item.id in cause.movable_items


def cause_can_hide(cause: Cause, hiding: HidingSpot) -> bool:
    return hiding.id in cause.hiding_spots


def place_allows(place: Place, cause: Cause) -> bool:
    return cause.id in place.affordances


def valid_story(place: Place, cause: Cause, item: MissingItem, hiding: HidingSpot) -> bool:
    return (
        place_allows(place, cause)
        and cause_can_move(cause, item)
        and item_fits(item, hiding)
        and cause_can_hide(cause, hiding)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for cause_id, cause in CAUSES.items():
            for item_id, item in ITEMS.items():
                for hiding_id, hiding in HIDING_SPOTS.items():
                    if valid_story(place, cause, item, hiding):
                        combos.append((place_id, cause_id, item_id, hiding_id))
    return combos


def detective_score(trait: str, helper: HelperDef) -> int:
    return (1 if trait in KEEN_TRAITS else 0) + helper.boost


def outcome_of(params: "StoryParams") -> str:
    score = detective_score(params.trait, HELPERS[params.helper])
    diff = CAUSES[params.cause].difficulty
    return "solo" if score >= diff else "helped"


def predict_solution(world: World, cause_id: str, hiding_id: str) -> dict:
    sim = world.copy()
    sim.facts["clue_found"] = True
    propagate(sim)
    sure = sim.get("child").memes["certainty"] >= THRESHOLD
    return {"clue_points": cause_id, "search": hiding_id, "sure": sure}


def introduce(world: World, child: Entity, helper: Entity, place: Place, item: MissingItem) -> None:
    trait = child.traits[0]
    world.say(
        f"{child.id} liked mysteries almost as much as music. In {place.label}, {child.pronoun()} was known for {trait} eyes and soft detective steps."
    )
    world.say(place.intro)
    world.say(
        f"Today was zither day, and {child.id} had brought {item.phrase}. {item.special}"
    )
    world.say(
        f"{helper.id} was nearby with {helper.attrs.get('cue', 'kind attention')}, ready to hear the tune when it began."
    )


def notice_loss(world: World, child: Entity, item_ent: Entity) -> None:
    item_ent.meters["missing"] += 1
    propagate(world)
    world.say(
        f"But when {child.id} reached for the {item_ent.label}, it was gone."
    )
    world.say(
        f"{child.pronoun().capitalize()} went still. This was not a loud kind of emergency, but it was a real mystery all the same."
    )


def examine_zither(world: World, child: Entity, cause: Cause) -> None:
    pred = predict_solution(world, cause.id, world.facts["hiding"].id)
    world.facts["predicted_search"] = pred["search"]
    world.say(
        f'"Detective {child.id} is on the case," {child.pronoun()} whispered, kneeling beside the zither.'
    )
    world.say(
        f"There {child.pronoun()} found the first clue: {cause.clue}"
    )
    world.facts["clue_found"] = True
    propagate(world)


def reflect(world: World, child: Entity, cause: Cause) -> None:
    world.say(
        f"{child.id} did not poke at every corner. {child.pronoun().capitalize()} studied {cause.clue_detail} and let the room grow quiet enough for thinking."
    )


def helper_nudge(world: World, helper: Entity, cause: Cause, hiding: HidingSpot) -> None:
    helper.memes["support"] += 1
    world.say(f"{helper.id} bent close and said, {helper.attrs['nudge']}")
    world.say(
        f'"If that clue is true," {helper.pronoun()} added, "where would something be if it were {cause.move_verb} {hiding.phrase}?"'
    )


def child_infers(world: World, child: Entity, cause: Cause, hiding: HidingSpot, solo: bool) -> None:
    child.memes["certainty"] += 1
    if solo:
        world.say(
            f'"I know now," {child.id} said. "{cause.phrase.capitalize()} must have {cause.move_verb} it {hiding.phrase}."'
        )
    else:
        world.say(
            f"{child.id}'s eyes widened. The clue and the question clicked together."
        )
        world.say(
            f'"Then {cause.phrase} must have {cause.move_verb} it {hiding.phrase}!" {child.pronoun()} cried.'
        )


def search_and_find(world: World, child: Entity, item_ent: Entity, hiding: HidingSpot) -> None:
    world.say(
        f"{child.id} reached carefully {hiding.phrase}."
    )
    item_ent.meters["missing"] = 0.0
    item_ent.meters["found"] += 1
    propagate(world)
    world.say(hiding.found_line)
    world.say(
        f"{child.pronoun().capitalize()} lifted out the {item_ent.label} and held it up like proof at the end of a case."
    )


def explain_case(world: World, child: Entity, cause: Cause) -> None:
    world.say(
        f"No thief had been hiding in the shadows after all. {cause.motive}"
    )
    world.say(
        f"{child.id} smiled, because a solved mystery felt better than a scary one."
    )


def ending(world: World, child: Entity, helper: Entity, item_ent: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Soon the {item_ent.label} was back where it belonged, and the first bright note of the zither rang across the room."
    )
    world.say(
        f"{helper.id} listened while {child.id} played, and the mystery seemed to fold itself small and gentle inside the music."
    )
    world.say(
        f"From then on, whenever {child.id} heard a twang, a flutter, or a tiny scrape near the zither, {child.pronoun()} looked for clues before making fears."
    )


def tell(
    place: Place,
    cause: Cause,
    item: MissingItem,
    hiding: HidingSpot,
    helper_def: HelperDef,
    name: str = "Lila",
    gender: str = "girl",
    trait: str = "observant",
) -> World:
    world = World()
    child = world.add(Entity(id=name, kind="character", type=gender, role="detective", traits=[trait]))
    helper = world.add(
        Entity(
            id=helper_def.name,
            kind="character",
            type=helper_def.type,
            role="helper",
            attrs={"cue": helper_def.cue, "nudge": helper_def.nudge},
        )
    )
    zither = world.add(Entity(id="zither", type="instrument", label="zither", phrase="the old zither"))
    item_ent = world.add(Entity(id="item", type="item", label=item.label, phrase=item.phrase))
    room = world.add(Entity(id="room", type="room", label=place.label))
    world.facts.update(place=place, cause=cause, item_cfg=item, hiding=hiding, helper_def=helper_def)

    introduce(world, child, helper, place, item)
    world.para()
    notice_loss(world, child, item_ent)
    examine_zither(world, child, cause)
    reflect(world, child, cause)
    world.para()

    solo = outcome_of(StoryParams(place.id, cause.id, item.id, hiding.id, helper_def.id, name, gender, trait)) == "solo"
    if not solo:
        helper_nudge(world, helper, cause, hiding)
    child_infers(world, child, cause, hiding, solo)
    search_and_find(world, child, item_ent, hiding)
    explain_case(world, child, cause)
    world.para()
    ending(world, child, helper, item_ent)

    world.facts.update(
        child=child,
        helper=helper,
        zither=zither,
        item=item_ent,
        outcome="solo" if solo else "helped",
        resolved=item_ent.meters["found"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    cause: str
    item: str
    hiding: str
    helper: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "zither": [(
        "What is a zither?",
        "A zither is a string instrument with many strings stretched across a flat wooden body. You make music by plucking or strumming the strings."
    )],
    "breeze": [(
        "What is a breeze?",
        "A breeze is a soft moving bit of air. It can flutter paper or carry very light things a short distance."
    )],
    "kitten": [(
        "Why do kittens bat at little things?",
        "Kittens are playful and curious, so tiny moving objects can look like toys to them. They often swat first and think later."
    )],
    "toddler": [(
        "Why might a toddler hide something by accident?",
        "A toddler may try to help by tidying or carrying things away. They are not trying to be sneaky; they just do not always know the best place to put things."
    )],
    "curtain": [(
        "Why can a curtain hide a light object?",
        "A curtain has folds in the cloth. A light flat thing can slip into one of those folds and be hard to see."
    )],
    "basket": [(
        "Why do things get lost in baskets?",
        "Baskets hold many papers or toys together, so a small object can slide between them and disappear from sight."
    )],
    "clue": [(
        "What is a clue in a mystery?",
        "A clue is a sign that helps you understand what happened. Good detectives use clues to make a careful guess."
    )],
    "detective": [(
        "What does a detective do?",
        "A detective notices details, asks questions, and follows clues to solve a problem. A good detective stays calm and thinks step by step."
    )],
}
KNOWLEDGE_ORDER = ["zither", "detective", "clue", "breeze", "kitten", "toddler", "curtain", "basket"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    item = f["item_cfg"]
    cause = f["cause"]
    return [
        f'Write a short detective story for a 3-to-5-year-old that includes the word "zither" and a gentle mystery in {place.label}.',
        f"Tell a child-facing mystery where {child.id} notices a missing {item.label}, finds a clue near a zither, and works out what really happened.",
        f"Write a cozy detective-style story in which {cause.actor} causes trouble by accident, and the ending feels safe once the clue is understood.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    item = f["item_cfg"]
    cause = f["cause"]
    hiding = f["hiding"]
    outcome = f["outcome"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who likes solving little mysteries, and {helper.id}, who stays nearby while the case is solved."
        ),
        (
            f"What was missing?",
            f"The missing thing was the {item.label}. It mattered because {item.special.lower()}"
        ),
        (
            "Where did the mystery begin?",
            f"It began beside the zither, where {child.id} expected the {item.label} to be. That is why the zither became the first place to inspect."
        ),
        (
            f"What clue did {child.id} find?",
            f"{child.id} found this clue: {cause.clue} The clue mattered because it pointed toward what had really moved the {item.label}."
        ),
    ]
    if outcome == "solo":
        qa.append(
            (
                f"How did {child.id} solve the mystery?",
                f"{child.id} studied the clue and matched it to the room instead of searching wildly. That helped {child.pronoun('object')} work out that {cause.phrase} had {cause.move_verb} the {item.label} {hiding.phrase}."
            )
        )
    else:
        qa.append(
            (
                f"Did {child.id} solve the mystery alone?",
                f"Not quite. {helper.id} gave one careful nudge, and then {child.id} put the clue and the hiding place together. The answer was still grounded in what the room showed."
            )
        )
    qa.append(
        (
            f"Where was the {item.label}?",
            f"It was {hiding.phrase}. {hiding.found_line} That proved the clue had been leading the right way."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"The mystery ended safely, with the {item.label} back in place and the zither ringing out at last. The final music shows that worry turned into relief."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"zither", "detective", "clue"}
    cause = world.facts["cause"]
    hiding = world.facts["hiding"]
    if cause.id == "breeze":
        tags.add("breeze")
    if cause.id == "kitten":
        tags.add("kitten")
    if cause.id == "toddler":
        tags.add("toddler")
    if hiding.id == "curtain_fold":
        tags.add("curtain")
    if hiding.id == "sheet_basket":
        tags.add("basket")
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:12} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(k[0] for k in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("music_room", "kitten", "bell_charm", "under_cushion", "teacher", "Lila", "girl", "observant"),
    StoryParams("parlor", "breeze", "ribbon", "curtain_fold", "grandpa", "Owen", "boy", "curious"),
    StoryParams("library_corner", "toddler", "music_card", "sheet_basket", "friend", "Mina", "girl", "patient"),
    StoryParams("parlor", "kitten", "music_card", "sheet_basket", "friend", "Theo", "boy", "careful"),
]


def explain_rejection(place: Place, cause: Cause, item: MissingItem, hiding: HidingSpot) -> str:
    if not place_allows(place, cause):
        return (
            f"(No story: {cause.actor} does not belong in {place.label} here, so the mystery would not be physically grounded.)"
        )
    if not cause_can_move(cause, item):
        return (
            f"(No story: {cause.actor} would not sensibly move the {item.label}. Pick a lighter or more reachable item for that cause.)"
        )
    if not item_fits(item, hiding):
        return (
            f"(No story: the {item.label} would not sensibly fit {hiding.phrase}. The hiding place must be believable.)"
        )
    if not cause_can_hide(cause, hiding):
        return (
            f"(No story: {cause.actor} would not likely send the {item.label} {hiding.phrase}. Choose a hiding place that matches the cause.)"
        )
    return "(No story: this mystery combination is not reasonable.)"


ASP_RULES = r"""
valid(P, C, I, H) :- place(P), cause(C), item(I), hiding(H),
                     affords(P, C), movable(C, I), fits(I, H), can_hide(C, H).

keen(T) :- trait(T), keen_trait(T).
score(1) :- chosen_helper(H), helper_boost(H, 1), not keen(chosen_trait).
score(0) :- chosen_helper(H), helper_boost(H, 0), not keen(chosen_trait).
score(2) :- chosen_helper(H), helper_boost(H, 1), keen(chosen_trait).
score(1) :- chosen_helper(H), helper_boost(H, 0), keen(chosen_trait).

outcome(solo)   :- chosen_cause(C), difficulty(C, D), score(S), S >= D.
outcome(helped) :- chosen_cause(C), difficulty(C, D), score(S), S < D.
"""

# Note: ASP uses the chosen_trait/0 convenience fact below for simple comparisons.


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for c in sorted(place.affordances):
            lines.append(asp.fact("affords", pid, c))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("difficulty", cid, cause.difficulty))
        for i in sorted(cause.movable_items):
            lines.append(asp.fact("movable", cid, i))
        for h in sorted(cause.hiding_spots):
            lines.append(asp.fact("can_hide", cid, h))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for hid, hiding in HIDING_SPOTS.items():
        lines.append(asp.fact("hiding", hid))
        for i in sorted(hiding.fit_items):
            lines.append(asp.fact("fits", i, hid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_boost", hid, helper.boost))
    for tr in TRAITS:
        lines.append(asp.fact("trait", tr))
    for tr in sorted(KEEN_TRAITS):
        lines.append(asp.fact("keen_trait", tr))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    chosen_trait_rules = """
keen(chosen_trait) :- chosen_trait_name(T), keen_trait(T).
"""
    return f"{asp_facts()}\n{ASP_RULES}\n{chosen_trait_rules}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_cause", params.cause),
        asp.fact("chosen_helper", params.helper),
        asp.fact("chosen_trait_name", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(50):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during resolve_params seed={seed}")
            break

    mismatch = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatch:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatch)} outcome disagreements.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle detective-style mystery storyworld built around a zither."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hiding", choices=HIDING_SPOTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.cause and args.item and args.hiding:
        place = PLACES[args.place]
        cause = CAUSES[args.cause]
        item = ITEMS[args.item]
        hiding = HIDING_SPOTS[args.hiding]
        if not valid_story(place, cause, item, hiding):
            raise StoryError(explain_rejection(place, cause, item, hiding))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.cause is None or c[1] == args.cause)
        and (args.item is None or c[2] == args.item)
        and (args.hiding is None or c[3] == args.hiding)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, cause, item, hiding = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place, cause, item, hiding, helper, name, gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        CAUSES[params.cause],
        ITEMS[params.item],
        HIDING_SPOTS[params.hiding],
        HELPERS[params.helper],
        params.name,
        params.gender,
        params.trait,
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
        print(f"{len(combos)} compatible (place, cause, item, hiding) combos:\n")
        for place, cause, item, hiding in combos:
            print(f"  {place:14} {cause:8} {item:10} {hiding}")
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
            header = f"### {p.name}: {p.cause} / {p.item} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
