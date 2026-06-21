#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fold_gamut_cheese_dim_kindness_sharing_rhyming.py
============================================================================

A small rhyming storyworld about two children folding paper shapes at a table,
finding one special craft item, and solving the problem through kindness and
sharing.

Seed words carried into the prose:
- fold
- gamut
- cheese-dim

The world model tracks simple physical meters (who has the scarce item, who
finished a craft) and emotional memes (joy, left_out, guilt, kindness).  The
renderer tells a complete little tale from those changing states instead of
swapping nouns into one fixed paragraph.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly:
# add the package dir (storyworlds/) to the path from this nested directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
GENEROUS_TRAITS = {"kind", "gentle", "caring"}


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
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Project:
    id: str
    label: str
    plural_label: str
    verb: str
    folded_shape: str
    finish_place: str
    coop_ok: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class ScarceItem:
    id: str
    label: str
    phrase: str
    divisible: bool = False
    sparkle_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"chooser", "friend"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _r_left_out(world: World) -> list[str]:
    chooser = world.get("chooser")
    friend = world.get("friend")
    scarce = world.get("scarce")
    if scarce.meters["held_by_chooser"] < THRESHOLD:
        return []
    if scarce.meters["shared"] >= THRESHOLD or scarce.meters["used_together"] >= THRESHOLD:
        return []
    sig = ("left_out", friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["left_out"] += 1
    friend.memes["sad"] += 1
    return ["__left_out__"]


def _r_guilt(world: World) -> list[str]:
    chooser = world.get("chooser")
    friend = world.get("friend")
    if friend.memes["left_out"] < THRESHOLD:
        return []
    sig = ("guilt", chooser.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    chooser.memes["guilt"] += 1
    return ["__guilt__"]


def _r_shared_joy(world: World) -> list[str]:
    scarce = world.get("scarce")
    if scarce.meters["shared"] < THRESHOLD and scarce.meters["used_together"] < THRESHOLD:
        return []
    sig = ("shared_joy",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["kindness"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="left_out", tag="social", apply=_r_left_out),
    Rule(name="guilt", tag="social", apply=_r_guilt),
    Rule(name="shared_joy", tag="social", apply=_r_shared_joy),
]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    return produced


def shareable(project: Project, scarce: ScarceItem) -> bool:
    return scarce.divisible or project.coop_ok


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for pid, project in PROJECTS.items():
        for sid, scarce in SCARCE_ITEMS.items():
            if shareable(project, scarce):
                combos.append((pid, sid))
    return combos


def early_share(project: Project, scarce: ScarceItem, trait: str) -> bool:
    return trait in GENEROUS_TRAITS and shareable(project, scarce)


def outcome_of(params: "StoryParams") -> str:
    project = PROJECTS[params.project]
    scarce = SCARCE_ITEMS[params.scarce]
    if not shareable(project, scarce):
        return "invalid"
    return "early" if early_share(project, scarce, params.trait) else "prompted"


def explain_rejection(project: Project, scarce: ScarceItem) -> str:
    return (
        f"(No story: {scarce.phrase} cannot be shared reasonably with {project.plural_label}. "
        f"It is not divisible, and {project.plural_label} are not a one-together project. "
        f"Pick a divisible item like stickers or ribbon, or a project like a lantern "
        f"that two children can finish together.)"
    )


PROJECTS = {
    "boats": Project(
        id="boats",
        label="boat",
        plural_label="paper boats",
        verb="fold paper boats",
        folded_shape="boat",
        finish_place="a blue windowsill",
        coop_ok=False,
        tags={"boat", "folding"},
    ),
    "birds": Project(
        id="birds",
        label="bird",
        plural_label="paper birds",
        verb="fold paper birds",
        folded_shape="bird",
        finish_place="the curtain rod",
        coop_ok=False,
        tags={"bird", "folding"},
    ),
    "flowers": Project(
        id="flowers",
        label="flower",
        plural_label="paper flowers",
        verb="fold paper flowers",
        folded_shape="flower",
        finish_place="a jam-jar vase",
        coop_ok=False,
        tags={"flower", "folding"},
    ),
    "lantern": Project(
        id="lantern",
        label="lantern",
        plural_label="a folded lantern",
        verb="fold a paper lantern",
        folded_shape="lantern",
        finish_place="the middle hook by the window",
        coop_ok=True,
        tags={"lantern", "folding"},
    ),
}

SCARCE_ITEMS = {
    "stickers": ScarceItem(
        id="stickers",
        label="star stickers",
        phrase="one sheet of shining star stickers",
        divisible=True,
        sparkle_line="Each little star could shine on its own, like a tiny gold moon that had learned how to float.",
        tags={"stickers", "sharing"},
    ),
    "ribbon": ScarceItem(
        id="ribbon",
        label="silver ribbon",
        phrase="one curl of silver ribbon",
        divisible=True,
        sparkle_line="The ribbon made a soft bright loop with a swish and a sway, like moonlight practicing ballet.",
        tags={"ribbon", "sharing"},
    ),
    "goldpaper": ScarceItem(
        id="goldpaper",
        label="gold paper",
        phrase="one last sheet of gold paper",
        divisible=False,
        sparkle_line="It gleamed on the table with buttery light, warm and mellow and softly bright.",
        tags={"goldpaper"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["kind", "gentle", "caring", "eager", "hasty", "proud"]
STYLE_NAMES = ["Rhyming", "Singing", "Bouncy"]


@dataclass
class StoryParams:
    project: str
    scarce: str
    chooser_name: str
    chooser_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    trait: str
    style_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        project="boats",
        scarce="stickers",
        chooser_name="Lily",
        chooser_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        parent="mother",
        trait="kind",
        style_name="Rhyming",
    ),
    StoryParams(
        project="birds",
        scarce="ribbon",
        chooser_name="Max",
        chooser_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        parent="father",
        trait="hasty",
        style_name="Bouncy",
    ),
    StoryParams(
        project="lantern",
        scarce="goldpaper",
        chooser_name="Ella",
        chooser_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        parent="mother",
        trait="gentle",
        style_name="Singing",
    ),
    StoryParams(
        project="lantern",
        scarce="goldpaper",
        chooser_name="Noah",
        chooser_gender="boy",
        friend_name="Zoe",
        friend_gender="girl",
        parent="father",
        trait="proud",
        style_name="Rhyming",
    ),
]


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def intro(world: World, chooser: Entity, friend: Entity, parent: Entity, project: Project, scarce: ScarceItem) -> None:
    for kid in (chooser, friend):
        kid.memes["joy"] += 1
    world.say(
        f"On a rainy after-school day, {chooser.id} and {friend.id} sat by the kitchen lamp, all snug and prim; "
        f"the little shade cast a cheese-dim gleam, soft as butter in a dream."
    )
    world.say(
        f"Between them lay a gamut of papers—reds, blues, greens, and rose—while {parent.label_word} set out glue and said, "
        f'"Let happy hands go slow and close."'
    )
    world.say(
        f'The two friends longed to {project.verb}. Each first neat fold was crisp and bright, and made the gray room feel alight.'
    )
    world.facts["seed_words_used"] = {"fold", "gamut", "cheese-dim"}
    world.facts["scarce_line"] = scarce.sparkle_line


def find_scarce(world: World, chooser: Entity, friend: Entity, scarce: ScarceItem) -> None:
    world.say(
        f"Then {friend.id} looked up with a small surprise, for there in the middle, before both pairs of eyes, "
        f"lay {scarce.phrase}."
    )
    if scarce.sparkle_line:
        world.say(scarce.sparkle_line)
    chooser.memes["desire"] += 1


def take_first(world: World, chooser: Entity, scarce_ent: Entity, scarce: ScarceItem) -> None:
    scarce_ent.meters["held_by_chooser"] += 1
    chooser.memes["grabby"] += 1
    world.say(
        f"{chooser.id} reached first and held {scarce.label} near. "
        f'"Oh, this would make my {world.facts["project"].folded_shape} look grand," {chooser.pronoun()} said, half-glad and half-dear.'
    )
    propagate(world)


def gentle_hurt(world: World, friend: Entity, project: Project, scarce: ScarceItem) -> None:
    if friend.memes["left_out"] >= THRESHOLD:
        world.say(
            f"{friend.id} folded one more corner, then grew still as a chair. "
            f'Without {scarce.label}, {friend.pronoun("possessive")} {project.folded_shape} could not wear the same bright air.'
        )


def share_now(world: World, chooser: Entity, friend: Entity, scarce_ent: Entity, scarce: ScarceItem, project: Project) -> None:
    scarce_ent.meters["shared"] += 1
    chooser.memes["sharing"] += 1
    friend.memes["sharing"] += 1
    chooser.memes["kindness"] += 1
    world.say(
        f"But {chooser.id} paused before the moment grew small. "
        f'{chooser.pronoun().capitalize()} saw {friend.id} waiting and heard kindness call.'
    )
    if scarce.divisible:
        world.say(
            f'"Let us share," said {chooser.id}. "There is enough if we part it with care." '
            f'So they split the {scarce.label} into two fair shares.'
        )
    else:
        world.say(
            f'"Let us use it together," said {chooser.id}. "One shining piece can still belong to two." '
            f'So their smiles leaned close, and their hands did too.'
        )
    propagate(world)


def prompt_by_parent(world: World, parent: Entity, chooser: Entity, friend: Entity, scarce: ScarceItem, project: Project) -> None:
    chooser.memes["noticed_hurt"] += 1
    world.say(
        f"{parent.label_word.capitalize()} noticed the hush at the table and spoke in a voice both low and light: "
        f'"A lovely craft grows lovelier still when we make a little room for another child\'s delight."'
    )
    if friend.memes["left_out"] >= THRESHOLD:
        world.say(
            f"{chooser.id} looked at {friend.id}'s face and felt the tug between being first and being fair. "
            f"Guilt sat where pride had been, a quiet weight in the air."
        )


def mend_with_sharing(world: World, chooser: Entity, friend: Entity, scarce_ent: Entity, scarce: ScarceItem, project: Project) -> None:
    scarce_ent.meters["shared"] += 1 if scarce.divisible else 0
    scarce_ent.meters["used_together"] += 0 if scarce.divisible else 1
    chooser.memes["sharing"] += 1
    friend.memes["sharing"] += 1
    chooser.memes["kindness"] += 1
    friend.memes["relief"] += 1
    chooser.memes["relief"] += 1
    if scarce.divisible:
        world.say(
            f'"You can have half," said {chooser.id}, turning back at once. '
            f'"Then both our folds can sparkle, and neither heart will dunce."'
        )
    else:
        world.say(
            f'"I was thinking too small," said {chooser.id}. "Come close to me. '
            f'We can make one fine {project.folded_shape} together, and let it belong to we."'  # deliberate rhyme voice
        )
    propagate(world)


def finish_story(world: World, chooser: Entity, friend: Entity, project: Project, scarce: ScarceItem) -> None:
    scarce_ent = world.get("scarce")
    if scarce_ent.meters["used_together"] >= THRESHOLD:
        chooser.meters["finished"] += 1
        friend.meters["finished"] += 1
        world.say(
            f"Soon one grand {project.folded_shape} rose from their laps, all crease and curl and careful flair. "
            f"They carried it to {project.finish_place}, and both stood proudly there."
        )
    else:
        chooser.meters["finished"] += 1
        friend.meters["finished"] += 1
        world.say(
            f"Soon two {project.plural_label} rested side by side, each one neatly folded, each one bright with pride. "
            f"They set them on {project.finish_place}, where evening light could play."
        )
    world.say(
        f"Then they shared the last two crackers on one small plate, and laughter came back, early though it was late."
    )
    world.say(
        f"Under the cheese-dim lamp, the room looked mild and wide. "
        f"What had been one small treasure became enough when kindness sat beside."
    )


def tell(
    project: Project,
    scarce: ScarceItem,
    chooser_name: str,
    chooser_gender: str,
    friend_name: str,
    friend_gender: str,
    parent_type: str,
    trait: str,
    style_name: str,
) -> World:
    world = World()
    chooser = world.add(
        Entity(
            id=chooser_name,
            kind="character",
            type=chooser_gender,
            role="chooser",
            traits=[trait],
            tags={"child"},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            role="friend",
            traits=["hopeful"],
            tags={"child"},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
            tags={"adult"},
        )
    )
    scarce_ent = world.add(
        Entity(
            id="scarce",
            kind="thing",
            type="craft_item",
            label=scarce.label,
            phrase=scarce.phrase,
            tags=set(scarce.tags),
        )
    )

    world.facts.update(
        chooser=chooser,
        friend=friend,
        parent=parent,
        project=project,
        scarce_cfg=scarce,
        style_name=style_name,
        valid=shareable(project, scarce),
    )

    intro(world, chooser, friend, parent, project, scarce)
    world.para()
    find_scarce(world, chooser, friend, scarce)

    if early_share(project, scarce, trait):
        if scarce.divisible:
            scarce_ent.meters["shared"] += 1
        else:
            scarce_ent.meters["used_together"] += 1
        share_now(world, chooser, friend, scarce_ent, scarce, project)
        outcome = "early"
    else:
        take_first(world, chooser, scarce_ent, scarce)
        gentle_hurt(world, friend, project, scarce)
        world.para()
        prompt_by_parent(world, parent, chooser, friend, scarce, project)
        mend_with_sharing(world, chooser, friend, scarce_ent, scarce, project)
        outcome = "prompted"

    world.para()
    finish_story(world, chooser, friend, project, scarce)

    world.facts.update(
        outcome=outcome,
        shared=scarce_ent.meters["shared"] >= THRESHOLD or scarce_ent.meters["used_together"] >= THRESHOLD,
        together=scarce_ent.meters["used_together"] >= THRESHOLD,
        left_out=friend.memes["left_out"] >= THRESHOLD,
        kindness=chooser.memes["kindness"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "folding": [
        (
            "What does it mean to fold paper?",
            "To fold paper means to bend it carefully so one part lies over another part. A few neat folds can turn a flat sheet into a shape like a boat, bird, flower, or lantern.",
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting another person use part of something you have, or using it together. It helps everyone feel included instead of left out.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to be gentle, fair, and helpful to another person. Sometimes it means noticing someone else's feelings and changing what you do.",
        )
    ],
    "stickers": [
        (
            "Why are stickers easy to share?",
            "A sheet of stickers has many small pieces on it, so two children can each use some. That makes stickers easy to divide fairly.",
        )
    ],
    "ribbon": [
        (
            "How can ribbon be shared?",
            "A long ribbon can be cut or split into shorter pieces. Then more than one craft can use it.",
        )
    ],
    "goldpaper": [
        (
            "Why is one sheet of gold paper harder to share?",
            "One sheet of paper is only one piece, so it cannot always be given to two separate crafts at once. Children may need to make one shared project together instead.",
        )
    ],
    "lantern": [
        (
            "What is a paper lantern?",
            "A paper lantern is a folded paper decoration that can hang up and glow softly when light shines near it. It is often made by curling or folding paper into a round or tall shape.",
        )
    ],
    "boat": [
        (
            "What is a paper boat?",
            "A paper boat is a little folded shape made from paper. Children often make one by folding corners and edges into a pointed top and a flat bottom.",
        )
    ],
    "bird": [
        (
            "What is a paper bird?",
            "A paper bird is a folded paper shape with wings or a beak. It is a pretend bird made by careful creases.",
        )
    ],
    "flower": [
        (
            "What is a paper flower?",
            "A paper flower is a folded craft that looks like petals and a bloom. It stays pretty without needing water.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    chooser = f["chooser"]
    friend = f["friend"]
    project = f["project"]
    scarce = f["scarce_cfg"]
    outcome = f["outcome"]
    if outcome == "early":
        return [
            f'Write a rhyming story for a 3-to-5-year-old that includes the words "fold", "gamut", and "cheese-dim".',
            f"Tell a gentle rhyming story where {chooser.id} and {friend.id} want to {project.verb}, find {scarce.phrase}, and solve the problem at once by sharing.",
            f"Write a tiny story about kindness and sharing at a craft table, ending with folded paper and a warm evening picture.",
        ]
    return [
        f'Write a rhyming story for a 3-to-5-year-old that includes the words "fold", "gamut", and "cheese-dim".',
        f"Tell a rhyming story where {chooser.id} first grabs {scarce.label}, then notices {friend.id}'s feelings and chooses kindness.",
        f"Write a short child-facing story about sharing one special craft item so two children can finish a folded project happily.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    chooser = f["chooser"]
    friend = f["friend"]
    parent = f["parent"]
    project = f["project"]
    scarce = f["scarce_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {chooser.id} and {friend.id}, two children making folded crafts at the kitchen table, and their {parent.label_word} nearby. The grown-up helps them notice how to be fair.",
        ),
        (
            f"What were {chooser.id} and {friend.id} trying to make?",
            f"They were trying to {project.verb}. Their careful folds turned plain paper into something special by the end.",
        ),
        (
            f"What special thing did they find on the table?",
            f"They found {scarce.phrase}. That one shiny item became the small problem in the middle of the story.",
        ),
    ]
    if outcome == "early":
        if f["together"]:
            qa.append(
                (
                    f"How did {chooser.id} show kindness right away?",
                    f"{chooser.id} did not keep the special item alone. Instead, {chooser.pronoun()} invited {friend.id} to use it together, so both children could belong to the same happy project.",
                )
            )
        else:
            qa.append(
                (
                    f"How did {chooser.id} solve the problem right away?",
                    f"{chooser.id} paused and shared the special item before {friend.id} felt left out. That quick choice turned one treasure into enough for both children.",
                )
            )
    else:
        qa.append(
            (
                f"Why did {friend.id} feel hurt?",
                f"{friend.id} felt hurt because {chooser.id} picked up {scarce.label} first and the craft no longer felt fair. Without sharing, {friend.id}'s own folded {project.folded_shape} could not shine in the same way.",
            )
        )
        qa.append(
            (
                f"What changed {chooser.id}'s mind?",
                f"{chooser.id} noticed the quiet at the table and listened when {parent.label_word} spoke gently about making room for another child's delight. Then guilt turned into kindness, and {chooser.pronoun()} chose to share.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the children finishing their folded craft and setting it at {project.finish_place}. The final picture shows that sharing changed the whole room from tense to warm.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    project = f["project"]
    scarce = f["scarce_cfg"]
    tags = {"kindness", "sharing", "folding"} | set(project.tags) | set(scarce.tags)
    order = ["folding", "sharing", "kindness", "stickers", "ribbon", "goldpaper", "lantern", "boat", "bird", "flower"]
    out: list[tuple[str, str]] = []
    for tag in order:
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
shareable(P, S) :- project(P), scarce(S), divisible(S).
shareable(P, S) :- project(P), scarce(S), coop_ok(P).
valid(P, S) :- shareable(P, S).

easy_share(P, S) :- valid(P, S), divisible(S).
easy_share(P, S) :- valid(P, S), coop_ok(P).

generous_now(T) :- generous_trait(T).

outcome(early) :- chosen_project(P), chosen_scarce(S), chosen_trait(T),
                  valid(P, S), generous_now(T), easy_share(P, S).
outcome(prompted) :- chosen_project(P), chosen_scarce(S), chosen_trait(T),
                     valid(P, S), not outcome(early).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, project in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        if project.coop_ok:
            lines.append(asp.fact("coop_ok", pid))
    for sid, scarce in SCARCE_ITEMS.items():
        lines.append(asp.fact("scarce", sid))
        if scarce.divisible:
            lines.append(asp.fact("divisible", sid))
    for trait in sorted(GENEROUS_TRAITS):
        lines.append(asp.fact("generous_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_project", params.project),
            asp.fact("chosen_scarce", params.scarce),
            asp.fact("chosen_trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("(Smoke test failed: empty story.)")
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases: list[StoryParams] = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
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
        _smoke_test()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Rhyming storyworld: folded paper, one special craft item, kindness through sharing."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--scarce", choices=SCARCE_ITEMS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.scarce:
        project = PROJECTS[args.project]
        scarce = SCARCE_ITEMS[args.scarce]
        if not shareable(project, scarce):
            raise StoryError(explain_rejection(project, scarce))

    combos = [
        c
        for c in valid_combos()
        if (args.project is None or c[0] == args.project)
        and (args.scarce is None or c[1] == args.scarce)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project_id, scarce_id = rng.choice(sorted(combos))
    chooser_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    chooser_name = _pick_name(rng, chooser_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=chooser_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    style_name = rng.choice(STYLE_NAMES)
    return StoryParams(
        project=project_id,
        scarce=scarce_id,
        chooser_name=chooser_name,
        chooser_gender=chooser_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        trait=trait,
        style_name=style_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.scarce not in SCARCE_ITEMS:
        raise StoryError(f"(Unknown scarce item: {params.scarce})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    project = PROJECTS[params.project]
    scarce = SCARCE_ITEMS[params.scarce]
    if not shareable(project, scarce):
        raise StoryError(explain_rejection(project, scarce))

    world = tell(
        project=project,
        scarce=scarce,
        chooser_name=params.chooser_name,
        chooser_gender=params.chooser_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        trait=params.trait,
        style_name=params.style_name,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (project, scarce) combos:\n")
        for project, scarce in combos:
            print(f"  {project:8} {scarce}")
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
            header = f"### {p.chooser_name} & {p.friend_name}: {p.project} with {p.scarce} ({outcome_of(p)})"
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
