#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/chrysalis_school_repetition_curiosity_humor_nursery_rhyme.py
========================================================================================

A standalone storyworld about a school class discovering a chrysalis and learning
that curiosity can be gentle. The prose leans toward a nursery-rhyme lilt with
repetition and a few silly guesses, but the story is still driven by simulated
state: whether the chrysalis is kept still, how ripe it is, and whether the
class uses a sensible way to observe it.

Run it
------
    python storyworlds/worlds/gpt-5.4/chrysalis_school_repetition_curiosity_humor_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/chrysalis_school_repetition_curiosity_humor_nursery_rhyme.py --place classroom --support fern --tool magnifier
    python storyworlds/worlds/gpt-5.4/chrysalis_school_repetition_curiosity_humor_nursery_rhyme.py --support lunchbox
    python storyworlds/worlds/gpt-5.4/chrysalis_school_repetition_curiosity_humor_nursery_rhyme.py --tool drumstick
    python storyworlds/worlds/gpt-5.4/chrysalis_school_repetition_curiosity_humor_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/chrysalis_school_repetition_curiosity_humor_nursery_rhyme.py --qa --json
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher_f"}
        male = {"boy", "father", "man", "teacher_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "teacher_f": "teacher",
            "teacher_m": "teacher",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    affords: set[str] = field(default_factory=set)
    rhyme: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Support:
    id: str
    label: str
    phrase: str
    places: set[str] = field(default_factory=set)
    living: bool = True
    steady: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    sense: int = 2
    kind: str = "observe"
    line: str = ""
    tags: set[str] = field(default_factory=set)


PLACES = {
    "classroom": Place(
        id="classroom",
        label="classroom",
        scene="Room Nine with bright rugs, low hooks, and a sunny window",
        affords={"fern", "twig_jar", "windowsill_vine"},
        rhyme="In Room Nine, by the sunny shine",
        tags={"school", "classroom"},
    ),
    "library_corner": Place(
        id="library_corner",
        label="library corner",
        scene="the library corner with beanbags and a shelf of animal books",
        affords={"twig_jar", "windowsill_vine"},
        rhyme="In the reading nook, by the picture-book look",
        tags={"school", "library"},
    ),
    "school_garden": Place(
        id="school_garden",
        label="school garden",
        scene="the little school garden beside the fence",
        affords={"milkweed", "twig_jar"},
        rhyme="In the schoolyard green, where the leaves all lean",
        tags={"school", "garden"},
    ),
}

SUPPORTS = {
    "fern": Support(
        id="fern",
        label="fern",
        phrase="a feathery fern by the window",
        places={"classroom"},
        living=True,
        steady=True,
        tags={"plant", "leaf"},
    ),
    "twig_jar": Support(
        id="twig_jar",
        label="twig in a jar",
        phrase="a quiet twig standing in a jar of water",
        places={"classroom", "library_corner", "school_garden"},
        living=True,
        steady=True,
        tags={"twig", "plant"},
    ),
    "windowsill_vine": Support(
        id="windowsill_vine",
        label="vine",
        phrase="a curling vine on the windowsill",
        places={"classroom", "library_corner"},
        living=True,
        steady=True,
        tags={"plant", "vine"},
    ),
    "milkweed": Support(
        id="milkweed",
        label="milkweed stem",
        phrase="a milkweed stem near the stepping stones",
        places={"school_garden"},
        living=True,
        steady=True,
        tags={"plant", "milkweed"},
    ),
    "lunchbox": Support(
        id="lunchbox",
        label="lunchbox",
        phrase="a shiny lunchbox with a sandwich smell",
        places=set(),
        living=False,
        steady=False,
        tags={"lunchbox"},
    ),
}

TOOLS = {
    "magnifier": Tool(
        id="magnifier",
        label="magnifying glass",
        phrase="a round magnifying glass",
        sense=3,
        kind="observe",
        line='"Look with your eyes and the glass, not your fingers,"',
        tags={"magnifier", "observe"},
    ),
    "notebook": Tool(
        id="notebook",
        label="notebook",
        phrase="a little science notebook",
        sense=3,
        kind="observe",
        line='"We can draw what we notice and count while we wait,"',
        tags={"notebook", "observe"},
    ),
    "song": Tool(
        id="song",
        label="counting song",
        phrase="a soft counting song",
        sense=2,
        kind="observe",
        line='"We can sing and watch softly while the chrysalis rests,"',
        tags={"song", "observe"},
    ),
    "ruler_tap": Tool(
        id="ruler_tap",
        label="ruler",
        phrase="a long tapping ruler",
        sense=1,
        kind="poke",
        line='""',
        tags={"ruler", "poke"},
    ),
    "drumstick": Tool(
        id="drumstick",
        label="drumstick",
        phrase="a wooden drumstick from music time",
        sense=0,
        kind="poke",
        line='""',
        tags={"drum", "poke"},
    ),
}

STAGES = {
    "soon": {"label": "soon", "ripe": False},
    "today": {"label": "today", "ripe": True},
}

GUESS_SETS = [
    ("a sleepy pea", "a tiny green lantern", "the principal's button"),
    ("a hanging raisin", "a small gold shoe", "a wrapped-up pickle"),
    ("a pocket moon", "a bean in a coat", "a bug in pajamas"),
]

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Eli", "Theo"]
TEACHER_NAMES_F = ["Ms. Wren", "Ms. June", "Ms. Maple"]
TEACHER_NAMES_M = ["Mr. Reed", "Mr. Pine", "Mr. Dale"]
TRAITS = ["curious", "bouncy", "giggle-prone", "bright-eyed", "patient"]


@dataclass
class StoryParams:
    place: str
    support: str
    tool: str
    stage: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    teacher_name: str
    teacher_gender: str
    child_trait: str
    guess_set: int
    seed: Optional[int] = None


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


def _r_poke_wobble(world: World) -> list[str]:
    chrys = world.get("chrysalis")
    if chrys.meters["poked"] < THRESHOLD:
        return []
    sig = ("poke_wobble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    chrys.meters["wobble"] += 1
    world.get("child").memes["worry"] += 1
    world.get("friend").memes["worry"] += 1
    return ["__wobble__"]


def _r_still_ready(world: World) -> list[str]:
    chrys = world.get("chrysalis")
    if chrys.meters["still"] < THRESHOLD or chrys.attrs.get("ripe") is not True:
        return []
    sig = ("still_ready",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    chrys.meters["emerged"] += 1
    world.get("child").memes["wonder"] += 1
    world.get("friend").memes["wonder"] += 1
    world.get("teacher").memes["joy"] += 1
    return ["__emerge__"]


CAUSAL_RULES = [
    Rule(name="poke_wobble", tag="physical", apply=_r_poke_wobble),
    Rule(name="still_ready", tag="physical", apply=_r_still_ready),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                out.extend(bits)
    return out


def support_allowed(place: Place, support: Support) -> bool:
    return support.id in place.affords and place.id in support.places and support.living and support.steady


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN and tool.kind == "observe"]


def would_emerge(stage: str) -> bool:
    return STAGES[stage]["ripe"]


def explain_rejection(place: Place, support: Support) -> str:
    if support.id not in place.affords or place.id not in support.places:
        return (
            f"(No story: {support.phrase} does not belong in the {place.label} setup here. "
            f"Pick a support that this school place really has.)"
        )
    if not support.living:
        return (
            f"(No story: a chrysalis should be resting on a quiet plant or twig, not on {support.phrase}. "
            f"The class needs a believable place to discover it.)"
        )
    if not support.steady:
        return (
            f"(No story: {support.phrase} is too jiggly for a sensible school observation story. "
            f"The chrysalis needs a steady place to hang.)"
        )
    return "(No story: this school place and support do not make a believable chrysalis scene.)"


def explain_tool(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    better = ", ".join(sorted(t.id for t in sensible_tools()))
    return (
        f"(Refusing tool '{tool_id}': it is not a gentle observation tool "
        f"(sense={tool.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_disturbance(world: World, tool: Tool) -> dict:
    sim = world.copy()
    if tool.kind == "poke":
        sim.get("chrysalis").meters["poked"] += 1
        propagate(sim, narrate=False)
    return {
        "wobbles": sim.get("chrysalis").meters["wobble"] >= THRESHOLD,
        "still": sim.get("chrysalis").meters["still"] >= THRESHOLD,
    }


def school_opening(world: World, place: Place, child: Entity, friend: Entity, teacher: Entity) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{place.rhyme}, the morning class sat cross-legged in {place.scene}. "
        f"{teacher.id} clapped once for quiet, and even the crayons seemed to listen."
    )
    world.say(
        f"{child.id} and {friend.id} were meant to sort leaf shapes, but {child.id} was "
        f"the sort of {child.attrs.get('trait_word', 'curious')} child who noticed every tiny thing."
    )


def discover(world: World, place: Place, support: Support, child: Entity, friend: Entity) -> None:
    chrys = world.get("chrysalis")
    child.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"Then {child.id} pointed. Hanging from {support.phrase} was a chrysalis, "
        f"small and still and shiny as if somebody had polished a raindrop."
    )
    world.say(
        f'"A chrysalis! A chrysalis!" whispered {child.id}. '
        f'"A chrysalis in school!" echoed {friend.id}.'
    )


def guessing_rhyme(world: World, child: Entity, friend: Entity, guesses: tuple[str, str, str]) -> None:
    child.memes["laughter"] += 1
    friend.memes["laughter"] += 1
    g1, g2, g3 = guesses
    world.say(
        f'"What is this? What is this?" asked {child.id}. '
        f'"Is it {g1}? Is it {g2}? Is it {g3}?"'
    )
    world.say(
        f'{friend.id} giggled. "Not a pea, not a shoe, not a pickle too. '
        f"It is a chrysalis, hanging hush-hush-new."'
    )


def temptation(world: World, child: Entity, tool: Tool) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f'{child.id} leaned in till {child.pronoun("possessive")} nose almost wrinkled. '
        f'"If I just use {tool.phrase}," {child.pronoun()} murmured, "what will it do?"'
    )


def teacher_warning(world: World, teacher: Entity, tool: Tool) -> None:
    pred = predict_disturbance(world, tool)
    world.facts["predicted_wobble"] = pred["wobbles"]
    chrys = world.get("chrysalis")
    world.say(
        f'{teacher.id} knelt beside the pot and smiled. {tool.line} '
        f'"A chrysalis likes stillness. If we tap it, it may wobble when it needs to rest."'
    )
    teacher.memes["care"] += 1
    if pred["wobbles"]:
        chrys.memes["risk"] += 1


def choose_gentle_observation(world: World, child: Entity, friend: Entity, tool: Tool) -> None:
    world.get("chrysalis").meters["still"] += 1
    child.memes["patience"] += 1
    friend.memes["patience"] += 1
    world.say(
        f"So {child.id} tucked {child.pronoun("possessive")} hands behind {child.pronoun("possessive")} back, "
        f"and {friend.id} copied {child.pronoun('object')} at once."
    )
    if tool.id == "magnifier":
        world.say(
            f"They took turns with {tool.phrase}. Closer and closer they looked, yet softer and softer they stood."
        )
    elif tool.id == "notebook":
        world.say(
            f"They opened {tool.phrase} and drew its curve, its hook, and the tiny seam that looked like a secret zipper."
        )
    else:
        world.say(
            f"They kept time with {tool.phrase}: "One little wait, two little waits, three little waits in a row."'
        )


def tiny_move(world: World, child: Entity, friend: Entity) -> None:
    world.get("chrysalis").meters["wiggle"] += 1
    child.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    world.say(
        f"Then came a tiny twitch. Not a jump, not a bop, just a shy little wiggle. "
        f'"Did you see? Did you see?" cried {child.id}. "I did! I did!" cried {friend.id}.'
    )


def emerge(world: World, child: Entity, friend: Entity, teacher: Entity) -> None:
    butterfly = world.get("butterfly")
    butterfly.meters["visible"] += 1
    world.say(
        f"The chrysalis split with a hush. Out came a damp little butterfly, "
        f"folded and sleepy, like a crumpled note learning how to be a kite."
    )
    world.say(
        f'"A butterfly! A butterfly!" sang {child.id}. '
        f'"In school, in school!" sang {friend.id}.'
    )
    world.say(
        f"{teacher.id} held the class still as stones while the wings slowly opened, "
        f"orange and black by the bright school glass."
    )


def waiting_end(world: World, child: Entity, friend: Entity, teacher: Entity) -> None:
    child.memes["hope"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"The chrysalis did not open that minute, but it gave one brave little wiggle, "
        f"as if to say, Not yet, not yet."
    )
    world.say(
        f'{teacher.id} wrote a sign with the class: "Please watch. Please wait. '
        f'Please let the chrysalis be great."'
    )
    world.say(
        f"{child.id} and {friend.id} set the sign beside it and tiptoed away, "
        f"already planning to peek again after lunch."
    )


def tell(
    place: Place,
    support: Support,
    tool: Tool,
    stage: str,
    child_name: str,
    child_gender: str,
    friend_name: str,
    friend_gender: str,
    teacher_name: str,
    teacher_gender: str,
    child_trait: str,
    guess_set: int,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=[child_trait],
            attrs={"trait_word": child_trait},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            role="friend",
            traits=["helpful"],
        )
    )
    teacher_type = "teacher_f" if teacher_gender == "female" else "teacher_m"
    teacher = world.add(
        Entity(
            id=teacher_name,
            kind="character",
            type=teacher_type,
            role="teacher",
            label="the teacher",
        )
    )
    chrys = world.add(
        Entity(
            id="chrysalis",
            type="chrysalis",
            label="chrysalis",
            phrase="the little chrysalis",
            attrs={"ripe": STAGES[stage]["ripe"]},
            tags={"chrysalis"},
        )
    )
    butterfly = world.add(Entity(id="butterfly", type="butterfly", label="butterfly", tags={"butterfly"}))

    school_opening(world, place, child, friend, teacher)
    discover(world, place, support, child, friend)

    world.para()
    guesses = GUESS_SETS[guess_set]
    guessing_rhyme(world, child, friend, guesses)
    temptation(world, child, tool)
    teacher_warning(world, teacher, tool)

    world.para()
    choose_gentle_observation(world, child, friend, tool)
    tiny_move(world, child, friend)

    markers = propagate(world, narrate=False)
    if "__emerge__" in markers or would_emerge(stage):
        if world.get("chrysalis").meters["emerged"] < THRESHOLD:
            world.get("chrysalis").meters["still"] += 1
            markers = propagate(world, narrate=False)
        world.para()
        emerge(world, child, friend, teacher)
        outcome = "emerges"
    else:
        world.para()
        waiting_end(world, child, friend, teacher)
        outcome = "waits"

    world.facts.update(
        place=place,
        support=support,
        tool=tool,
        stage=stage,
        child=child,
        friend=friend,
        teacher=teacher,
        chrysalis=chrys,
        butterfly=butterfly,
        guesses=guesses,
        outcome=outcome,
        moved=world.get("chrysalis").meters["wiggle"] >= THRESHOLD,
        emerged=world.get("chrysalis").meters["emerged"] >= THRESHOLD,
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for support_id, support in SUPPORTS.items():
            if not support_allowed(place, support):
                continue
            for tool in sensible_tools():
                combos.append((place_id, support_id, tool.id))
    return combos


def outcome_of(params: StoryParams) -> str:
    return "emerges" if would_emerge(params.stage) else "waits"


KNOWLEDGE = {
    "chrysalis": [
        (
            "What is a chrysalis?",
            "A chrysalis is the hard case some caterpillars make around themselves while they change. Inside it, the caterpillar is turning into a butterfly.",
        )
    ],
    "butterfly": [
        (
            "Why are a butterfly's wings crumpled at first?",
            "When a butterfly first comes out, its wings are soft and folded. It needs a little time to stretch them open and let them dry.",
        )
    ],
    "magnifier": [
        (
            "What does a magnifying glass do?",
            "A magnifying glass makes small things look bigger, so you can see tiny details without touching them.",
        )
    ],
    "notebook": [
        (
            "Why do children use notebooks in science?",
            "A notebook helps children draw and write what they notice. It lets them remember details while keeping their hands gentle and still.",
        )
    ],
    "song": [
        (
            "How can a song help children wait?",
            "A soft song gives children something calm to do while they wait. The rhythm helps their bodies stay still.",
        )
    ],
    "school": [
        (
            "What can children learn by watching nature at school?",
            "They can learn to notice carefully, ask questions, and wait for changes. Nature lessons teach patience as well as facts.",
        )
    ],
    "plant": [
        (
            "Why do chrysalises hang from plants or twigs?",
            "Plants and twigs give them a quiet place to rest while they change. A steady place helps them stay safe.",
        )
    ],
    "wait": [
        (
            "Why is waiting important when you watch a chrysalis?",
            "A chrysalis needs time and stillness. If people keep bothering it, they may scare it or miss the gentle moment of change.",
        )
    ],
}
KNOWLEDGE_ORDER = ["chrysalis", "butterfly", "magnifier", "notebook", "song", "school", "plant", "wait"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    tool = f["tool"]
    place = f["place"]
    if f["outcome"] == "emerges":
        return [
            'Write a nursery-rhyme-style school story that includes the word "chrysalis" and uses repetition, curiosity, and humor.',
            f"Tell a gentle classroom story where {child.id} and {friend.id} find a chrysalis in the {place.label}, make silly guesses about it, and watch it become a butterfly.",
            f"Write a rhyming story where a curious child wants to look closely with {tool.phrase}, learns to be gentle, and ends with a butterfly opening its wings.",
        ]
    return [
        'Write a nursery-rhyme-style school story that includes the word "chrysalis" and uses repetition, curiosity, and humor.',
        f"Tell a gentle school story where {child.id} and {friend.id} find a chrysalis in the {place.label}, ask the same curious question again and again, and learn to wait kindly.",
        f"Write a playful classroom rhyme where children make funny guesses about a chrysalis, use {tool.phrase} to observe it, and end by leaving it a sign to rest.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    teacher = f["teacher"]
    place = f["place"]
    support = f["support"]
    tool = f["tool"]
    guesses = f["guesses"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {friend.id} at school, and {teacher.id}, their teacher. They are the ones who find the chrysalis and decide how to treat it.",
        ),
        (
            "Where did they find the chrysalis?",
            f"They found it in the {place.label}, hanging from {support.phrase}. That steady place is what made the discovery feel quiet and special.",
        ),
        (
            "What funny guesses did the children make?",
            f"They wondered if it was {guesses[0]}, {guesses[1]}, or {guesses[2]}. The silly guesses made them laugh, but they still kept asking what the chrysalis really was.",
        ),
        (
            f"Why did {teacher.id} tell them not to tap it?",
            f"{teacher.id} said a chrysalis likes stillness and may wobble if someone taps it. The class needed to be gentle so they could watch without bothering it.",
        ),
        (
            f"How did the children choose to observe the chrysalis?",
            f"They used {tool.phrase} and kept their hands to themselves. That let their curiosity stay lively while the chrysalis stayed still.",
        ),
    ]
    if f["outcome"] == "emerges":
        qa.append(
            (
                "What happened at the end of the story?",
                "At the end, the chrysalis opened and a little butterfly came out. The class stayed very still so they could watch its damp wings slowly spread.",
            )
        )
    else:
        qa.append(
            (
                "What happened at the end of the story?",
                "The chrysalis did not open yet, but it gave a tiny wiggle. The children made a sign asking everyone to watch and wait, which showed they had learned patience.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"chrysalis", "school", "plant", "wait"}
    tags |= set(world.facts["tool"].tags)
    if world.facts["outcome"] == "emerges":
        tags.add("butterfly")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        shown_attrs = {k: v for k, v in ent.attrs.items() if v not in ("", None, False)}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(name for (name, *_) in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
supported(P, S) :- place(P), support(S), affords(P, S), hangs_in(S, P), living(S), steady(S).
sensible(T) :- tool(T), sense(T, N), sense_min(M), N >= M, observe_tool(T).
valid(P, S, T) :- supported(P, S), sensible(T).

ripe(today).
not_ripe(soon).

outcome(emerges) :- chosen_stage(St), ripe(St).
outcome(waits) :- chosen_stage(St), not_ripe(St).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for support_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, support_id))
    for support_id, support in SUPPORTS.items():
        lines.append(asp.fact("support", support_id))
        for place_id in sorted(support.places):
            lines.append(asp.fact("hangs_in", support_id, place_id))
        if support.living:
            lines.append(asp.fact("living", support_id))
        if support.steady:
            lines.append(asp.fact("steady", support_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        if tool.kind == "observe":
            lines.append(asp.fact("observe_tool", tool_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for stage in sorted(STAGES):
        lines.append(asp.fact("stage", stage))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_tools() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_stage", params.stage)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    emit(sample, trace=False, qa=False, header="")


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

    py_tools = {tool.id for tool in sensible_tools()}
    asp_tools = set(asp_sensible_tools())
    if py_tools == asp_tools:
        print(f"OK: sensible tools match ({sorted(py_tools)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: python={sorted(py_tools)} clingo={sorted(asp_tools)}")

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke test story generation ran.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


CURATED = [
    StoryParams(
        place="classroom",
        support="fern",
        tool="magnifier",
        stage="today",
        child_name="Lily",
        child_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        teacher_name="Ms. Wren",
        teacher_gender="female",
        child_trait="curious",
        guess_set=0,
    ),
    StoryParams(
        place="library_corner",
        support="twig_jar",
        tool="notebook",
        stage="soon",
        child_name="Max",
        child_gender="boy",
        friend_name="Zoe",
        friend_gender="girl",
        teacher_name="Mr. Reed",
        teacher_gender="male",
        child_trait="giggle-prone",
        guess_set=1,
    ),
    StoryParams(
        place="school_garden",
        support="milkweed",
        tool="song",
        stage="today",
        child_name="Ava",
        child_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        teacher_name="Ms. Maple",
        teacher_gender="female",
        child_trait="bright-eyed",
        guess_set=2,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a school class discovers a chrysalis and learns that curiosity can be gentle."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--stage", choices=STAGES)
    ap.add_argument("--child-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--teacher-gender", choices=["female", "male"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, support, tool) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.support:
        if not support_allowed(PLACES[args.place], SUPPORTS[args.support]):
            raise StoryError(explain_rejection(PLACES[args.place], SUPPORTS[args.support]))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(args.tool))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.support is None or combo[1] == args.support)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, support, tool = rng.choice(sorted(combos))
    stage = args.stage or rng.choice(sorted(STAGES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=child_name)
    teacher_gender = args.teacher_gender or rng.choice(["female", "male"])
    teacher_name = rng.choice(TEACHER_NAMES_F if teacher_gender == "female" else TEACHER_NAMES_M)
    child_trait = rng.choice(TRAITS)
    guess_set = rng.randrange(len(GUESS_SETS))
    return StoryParams(
        place=place,
        support=support,
        tool=tool,
        stage=stage,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        teacher_name=teacher_name,
        teacher_gender=teacher_gender,
        child_trait=child_trait,
        guess_set=guess_set,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.support not in SUPPORTS:
        raise StoryError(f"(Unknown support: {params.support})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.stage not in STAGES:
        raise StoryError(f"(Unknown stage: {params.stage})")
    if not support_allowed(PLACES[params.place], SUPPORTS[params.support]):
        raise StoryError(explain_rejection(PLACES[params.place], SUPPORTS[params.support]))
    if TOOLS[params.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(params.tool))
    if not (0 <= params.guess_set < len(GUESS_SETS)):
        raise StoryError("(Invalid guess set.)")

    world = tell(
        place=PLACES[params.place],
        support=SUPPORTS[params.support],
        tool=TOOLS[params.tool],
        stage=params.stage,
        child_name=params.child_name,
        child_gender=params.child_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        teacher_name=params.teacher_name,
        teacher_gender=params.teacher_gender,
        child_trait=params.child_trait,
        guess_set=params.guess_set,
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
        combos = asp_valid_combos()
        print(f"sensible tools: {', '.join(asp_sensible_tools())}\n")
        print(f"{len(combos)} compatible (place, support, tool) combos:\n")
        for place, support, tool in combos:
            print(f"  {place:15} {support:14} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.child_name} at {p.place}: {p.support}, {p.tool}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
