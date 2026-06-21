#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/suction_spigot_mystery_to_solve_cautionary_comedy.py
================================================================================

A standalone storyworld about a funny household mystery: water keeps vanishing
from a bucket during play, a child blames silly suspects, and a careful grown-up
helps solve the mystery. The real cause is suction from a hose attached to a
spigot. The cautionary lesson is that children should not turn spigots and hoses
into guessing games on their own; they should call a grown-up when water starts
moving in a strange way.

The world model tracks:
- physical meters: wetness, water flow, bucket level, splash, puddle
- emotional memes: curiosity, worry, relief, pride, trust

The story shape is:
- premise: playful setup with a water game
- tension: mysterious disappearing water
- turn: the child tests the wrong idea and makes the mess worse
- resolution: a grown-up notices the hose and explains suction
- ending image: the children use the water safely for a proper game

Run it
------
python storyworlds/worlds/gpt-5.4/suction_spigot_mystery_to_solve_cautionary_comedy.py
python storyworlds/worlds/gpt-5.4/suction_spigot_mystery_to_solve_cautionary_comedy.py --mystery bucket --cause hose
python storyworlds/worlds/gpt-5.4/suction_spigot_mystery_to_solve_cautionary_comedy.py --test straw
python storyworlds/worlds/gpt-5.4/suction_spigot_mystery_to_solve_cautionary_comedy.py --test mouth_sip
python storyworlds/worlds/gpt-5.4/suction_spigot_mystery_to_solve_cautionary_comedy.py --all
python storyworlds/worlds/gpt-5.4/suction_spigot_mystery_to_solve_cautionary_comedy.py --verify
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
SAFE_MIN = 2


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
class PlayTheme:
    id: str
    scene: str
    props: str
    title: str
    job: str
    finish: str


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    container: str
    disappearing: str
    scene_line: str
    question: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    phrase: str
    path: str
    clue: str
    fix: str
    safe_tool: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TestIdea:
    id: str
    label: str
    safe: int
    splash: int
    text: str
    fail_text: str
    lesson: str
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
        out = World()
        out.entities = copy.deepcopy(self.entities)
        out.fired = set(self.fired)
        out.paragraphs = [[]]
        out.facts = copy.deepcopy(self.facts)
        return out


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_transfer(world: World) -> list[str]:
    out: list[str] = []
    bucket = world.entities.get("mystery")
    receiver = world.entities.get("receiver")
    hose = world.entities.get("hose")
    if not bucket or not receiver or not hose:
        return out
    if hose.meters["suction"] < THRESHOLD:
        return out
    sig = ("transfer",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bucket.meters["water"] -= 1
    receiver.meters["water"] += 1
    bucket.meters["mystery_loss"] += 1
    out.append("__flow__")
    return out


def _r_puddle(world: World) -> list[str]:
    out: list[str] = []
    floor = world.entities.get("floor")
    child = world.entities.get("child")
    if not floor or not child:
        return out
    if child.meters["splash"] < THRESHOLD:
        return out
    sig = ("puddle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    floor.meters["wet"] += 1
    child.memes["worry"] += 1
    out.append("__puddle__")
    return out


CAUSAL_RULES = [
    Rule(name="transfer", tag="physical", apply=_r_transfer),
    Rule(name="puddle", tag="physical", apply=_r_puddle),
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
            if sent == "__flow__":
                cause = world.facts["cause_cfg"]
                mystery = world.facts["mystery_cfg"]
                world.say(
                    f"Without anyone noticing, the water slid {cause.path}, and {mystery.container} began to look emptier."
                )
            elif sent == "__puddle__":
                world.say("A shiny little puddle spread across the floor, which made the game feel much less funny.")
    return produced


def valid_combo(mystery: Mystery, cause: Cause, test: TestIdea) -> bool:
    if cause.id not in {"hose", "watering_can"}:
        return False
    if test.safe < SAFE_MIN and test.id != "mouth_sip":
        return False
    if test.id == "mouth_sip" and cause.id not in {"hose", "watering_can"}:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mid, mystery in MYSTERIES.items():
        for cid, cause in CAUSES.items():
            for tid, test in TESTS.items():
                if valid_combo(mystery, cause, test):
                    combos.append((mid, cid, tid))
    return combos


def explain_test_rejection(test_id: str) -> str:
    test = TESTS[test_id]
    if test.id == "mouth_sip":
        return (
            "(No story: refusing test 'mouth_sip' because children should not put their mouths on a hose or mystery water. "
            "That is unsafe and the world prefers calling a grown-up or using a look-only test.)"
        )
    return (
        f"(No story: refusing test '{test_id}' because it scores too low on safety "
        f"(safe={test.safe} < {SAFE_MIN}). Pick a safer test such as mirror or straw.)"
    )


def predict_disappearing(world: World) -> dict:
    sim = world.copy()
    hose = sim.get("hose")
    hose.meters["suction"] += 1
    propagate(sim, narrate=False)
    bucket = sim.get("mystery")
    return {
        "bucket_lower": bucket.meters["mystery_loss"] >= THRESHOLD,
        "receiver_water": sim.get("receiver").meters["water"],
    }


def introduce(world: World, child: Entity, friend: Entity, theme: PlayTheme) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a warm afternoon, {child.id} and {friend.id} turned the yard into {theme.scene}. {theme.props}"
    )
    world.say(f'"{theme.title} {child.id}!" laughed {friend.id}. "And {theme.job} {child.id} knows where to look!"')


def setup_mystery(world: World, child: Entity, friend: Entity, mystery: Mystery) -> None:
    world.say(mystery.scene_line)
    world.say(
        f"{friend.id} blinked at {mystery.container}. \"{mystery.question}\""
    )
    child.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1


def silly_suspects(world: World, child: Entity, friend: Entity, mystery: Mystery) -> None:
    world.say(
        f'"Maybe a thirsty ant drank it," {child.id} guessed.'
    )
    world.say(
        f'"Or maybe the sun has tiny slippers and tiptoed off with it," {friend.id} said. They both stared at {mystery.container} as if it might confess.'
    )


def bad_test(world: World, child: Entity, test: TestIdea) -> None:
    child.memes["pride"] += 1
    child.meters["splash"] += float(test.splash)
    world.say(test.text)
    if test.splash > 0:
        propagate(world, narrate=True)
    world.say(test.fail_text)


def grownup_solves(world: World, parent: Entity, child: Entity, friend: Entity, mystery: Mystery, cause: Cause) -> None:
    hose = world.get("hose")
    hose.meters["suction"] += 1
    propagate(world, narrate=False)
    child.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came over, followed the line of water with calm eyes, and spotted {cause.clue}."
    )
    world.say(
        f"\"There is your mystery,\" {parent.pronoun()} said. \"The {cause.label} made suction and pulled the water away through {cause.path}.\""
    )
    world.say(
        f"{child.id} opened {child.pronoun('possessive')} mouth. \"So it was not a sneaky ant?\""
    )
    world.say(
        f"\"No,\" said {parent.label_word}. \"Just water moving the way water moves when a hose and a spigot are set up wrong.\""
    )


def caution_and_fix(world: World, parent: Entity, child: Entity, friend: Entity, cause: Cause, test: TestIdea) -> None:
    child.memes["relief"] += 1
    friend.memes["relief"] += 1
    child.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"{parent.label_word.capitalize()} turned the spigot off, {cause.fix}, and wiped the wet floor with an old towel."
    )
    world.say(
        f"Then {parent.pronoun()} knelt down and smiled. \"Strange water is a grown-up puzzle. You did the right thing by calling me before the yard turned into a lake.\""
    )
    world.say(
        f"\"Next time,\" {parent.pronoun()} added, \"do not try {test.lesson}. If water starts sneaking through a hose or a spigot, get a grown-up right away.\""
    )


def safe_ending(world: World, child: Entity, friend: Entity, theme: PlayTheme, mystery: Mystery, cause: Cause) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"A little later, {parent_word(world).capitalize()} helped them use {cause.safe_tool} the safe way, and soon the game was funny again."
    )
    world.say(
        f"They filled {mystery.container} on purpose this time, splashed only where they were allowed, and announced that the case of the disappearing water was closed."
    )
    world.say(theme.finish)


def parent_word(world: World) -> str:
    parent = world.facts["parent"]
    return parent.label_word


def tell(
    theme: PlayTheme,
    mystery: Mystery,
    cause: Cause,
    test: TestIdea,
    child_name: str,
    child_gender: str,
    friend_name: str,
    friend_gender: str,
    parent_type: str,
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", label=child_name))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend", label=friend_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="mystery", type="container", label=mystery.label, phrase=mystery.phrase))
    world.add(Entity(id="hose", type="hose", label="hose"))
    world.add(Entity(id="receiver", type="receiver", label="flower bed"))
    world.add(Entity(id="floor", type="ground", label="stone path"))

    world.facts.update(
        child=child,
        friend=friend,
        parent=parent,
        theme=theme,
        mystery_cfg=mystery,
        cause_cfg=cause,
        test_cfg=test,
    )

    introduce(world, child, friend, theme)
    setup_mystery(world, child, friend, mystery)
    world.para()
    silly_suspects(world, child, friend, mystery)
    pred = predict_disappearing(world)
    world.facts["predicted_bucket_lower"] = pred["bucket_lower"]
    world.facts["predicted_receiver_water"] = pred["receiver_water"]
    if test.id == "mouth_sip":
        raise StoryError(explain_test_rejection(test.id))
    bad_test(world, child, test)
    world.para()
    grownup_solves(world, parent, child, friend, mystery, cause)
    caution_and_fix(world, parent, child, friend, cause, test)
    world.para()
    safe_ending(world, child, friend, theme, mystery, cause)

    world.facts.update(
        solved=True,
        puddle=world.get("floor").meters["wet"] >= THRESHOLD,
        mystery_loss=world.get("mystery").meters["mystery_loss"] >= THRESHOLD,
    )
    return world


THEMES = {
    "detectives": PlayTheme(
        id="detectives",
        scene="a grand detective headquarters behind the tomato pots",
        props="A bucket became the clue vault, a toy notebook became the case file, and a bent spoon became their official badge.",
        title="Captain",
        job="Detective",
        finish="With a proud click of the notebook, the two detectives marched off to solve easier mysteries, like who kept hiding the garden glove.",
    ),
    "harbor": PlayTheme(
        id="harbor",
        scene="a tiny harbor for toy boats",
        props="A wash tub became the sea, two sticks became docks, and a plastic cup became the mayor's lighthouse.",
        title="Harbor Chief",
        job="Dock Inspector",
        finish="Their boats bobbed in neat circles, and nobody blamed ants, moons, or invisible fish anymore.",
    ),
    "castle": PlayTheme(
        id="castle",
        scene="a royal castle with a moat",
        props="A bucket became the moat, a crate became the gate tower, and a wooden spoon became the royal trumpet.",
        title="King",
        job="Keeper of Clues",
        finish="The royal moat sparkled where it was supposed to, and the castle stayed cheerful instead of soggy.",
    ),
}

MYSTERIES = {
    "bucket": Mystery(
        id="bucket",
        label="bucket",
        phrase="the blue bucket",
        container="the blue bucket",
        disappearing="its water kept dropping",
        scene_line="They had just filled the blue bucket for their game, but every time they turned around, the water line sat a little lower.",
        question="Who keeps drinking our moat?",
        tags={"bucket", "water", "mystery"},
    ),
    "tub": Mystery(
        id="tub",
        label="wash tub",
        phrase="the round wash tub",
        container="the round wash tub",
        disappearing="its water kept slipping away",
        scene_line="The round wash tub looked full one moment and thinner the next, as if the water had learned to tiptoe.",
        question="Where did the harbor go?",
        tags={"tub", "water", "mystery"},
    ),
}

CAUSES = {
    "hose": Cause(
        id="hose",
        label="hose",
        phrase="a green hose",
        path="the hose into the thirsty flower bed",
        clue="the end of the green hose lying lower than the bucket beside the marigolds",
        fix="lifted the hose up and set the loose end back inside the bucket",
        safe_tool="the hose after checking it together",
        tags={"hose", "suction", "spigot"},
    ),
    "watering_can": Cause(
        id="watering_can",
        label="watering can",
        phrase="a dented watering can",
        path="the hose into the waiting watering can",
        clue="a dented watering can sitting below the tub, quietly filling through the hose",
        fix="pulled the hose free and stood the watering can upright away from the tub",
        safe_tool="a proper little watering can",
        tags={"hose", "suction", "spigot", "watering"},
    ),
}

TESTS = {
    "mirror": TestIdea(
        id="mirror",
        label="mirror",
        safe=3,
        splash=0,
        text=''"I will inspect it like a real detective," the child said, crouching so low that the bucket nearly booped the end of their nose.'',
        fail_text="But staring hard at the water did not stop it from slipping away.",
        lesson="weird water experiments by yourself",
        tags={"look", "safe"},
    ),
    "straw": TestIdea(
        id="straw",
        label="straw",
        safe=2,
        splash=1,
        text=''"Maybe if I poke the water with this straw, it will tell me the truth," the child said, giving the bucket a tiny stir.'',
        fail_text="Instead, the straw flicked a cold dot of water onto the path, and the mystery only looked smugger.",
        lesson="poking and testing hoses on your own",
        tags={"straw", "caution"},
    ),
    "mouth_sip": TestIdea(
        id="mouth_sip",
        label="mouth sip",
        safe=0,
        splash=0,
        text=''"Maybe I should taste the clue," the child said.',
        fail_text="That was not a good plan at all.",
        lesson="put your mouth on a hose or mystery water",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]


@dataclass
class StoryParams:
    theme: str
    mystery: str
    cause: str
    test: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        theme="detectives",
        mystery="bucket",
        cause="hose",
        test="straw",
        child_name="Lily",
        child_gender="girl",
        friend_name="Tom",
        friend_gender="boy",
        parent="mother",
    ),
    StoryParams(
        theme="harbor",
        mystery="tub",
        cause="watering_can",
        test="mirror",
        child_name="Ben",
        child_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        parent="father",
    ),
    StoryParams(
        theme="castle",
        mystery="bucket",
        cause="hose",
        test="mirror",
        child_name="Ava",
        child_gender="girl",
        friend_name="Leo",
        friend_gender="boy",
        parent="mother",
    ),
]


KNOWLEDGE = {
    "suction": [
        (
            "What is suction?",
            "Suction is when something pulls air or water along because of pressure and position. In a hose, it can make water move from one place to another even when that feels surprising."
        )
    ],
    "spigot": [
        (
            "What is a spigot?",
            "A spigot is a little tap you turn to let water come out. Grown-ups use it to control water from a pipe or hose."
        )
    ],
    "hose": [
        (
            "What does a hose do?",
            "A hose carries water from one place to another. If it is left in the wrong place, the water can run where you did not mean it to go."
        )
    ],
    "bucket": [
        (
            "What is a bucket for?",
            "A bucket holds water or other things. It is useful, but it can spill or empty if water has a path out."
        )
    ],
    "water": [
        (
            "Why can water make a mess?",
            "Water spreads quickly across the floor or ground. That can make puddles, slippery spots, and extra cleanup."
        )
    ],
    "adult_help": [
        (
            "What should a child do if water is moving in a strange way?",
            "A child should stop touching it and call a grown-up. Strange water, hoses, and spigots can make a bigger mess fast."
        )
    ],
}
KNOWLEDGE_ORDER = ["suction", "spigot", "hose", "bucket", "water", "adult_help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    mystery = f["mystery_cfg"]
    cause = f["cause_cfg"]
    return [
        f'Write a funny cautionary mystery for ages 3 to 5 that includes the words "suction" and "spigot".',
        f"Tell a child-facing story where {child.id} and {friend.id} notice that water keeps disappearing from {mystery.container}, then learn that a {cause.label} and a spigot made the trouble.",
        "Write a comedy with a small wet mess, a wrong guess, a grown-up explanation, and a safe ending."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    parent = f["parent"]
    mystery = f["mystery_cfg"]
    cause = f["cause_cfg"]
    test = f["test_cfg"]
    items: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {friend.id}, two children playing a pretend game in the yard, and {parent.label_word} who helps them solve the mystery."
        ),
        (
            "What was the mystery?",
            f"The mystery was that water kept disappearing from {mystery.container}. It looked as if the bucket was emptying all by itself."
        ),
        (
            f"Why did the children think it was a mystery?",
            f"They could see the water line dropping, but they did not yet know about the hose and suction. That made room for silly guesses before the real clue was found."
        ),
        (
            f"What mistake did {child.id} make?",
            f"{child.id} tried {test.label} as a little test instead of calling a grown-up right away. That did not solve anything, and it added to the wet mess."
        ),
        (
            "How was the mystery solved?",
            f"{parent.label_word.capitalize()} followed the water path, spotted {cause.clue}, and explained that suction through the hose was pulling the water away. The answer came from looking at how the water was moving, not from guessing."
        ),
        (
            "What did the children learn?",
            f"They learned that a hose and a spigot can move water in surprising ways. They also learned to get a grown-up when a water problem starts acting sneaky."
        ),
    ]
    if f.get("puddle"):
        items.append(
            (
                "What changed at the end?",
                f"At first the path got wet and the game felt wobbly, but after {parent.label_word} fixed the hose, the children could play safely again. The ending proves the problem was really solved because the water stayed where it belonged."
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"suction", "spigot", "hose", "water", "adult_help"}
    mystery = world.facts["mystery_cfg"]
    if mystery.id == "bucket":
        tags.add("bucket")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(M, C, T) :- mystery(M), cause(C), test(T), allowed_cause(C), safe_test(T).
safe_test(mirror).
safe_test(straw).
allowed_cause(hose).
allowed_cause(watering_can).
unsafe_test(mouth_sip).

solved(M, C, T) :- valid(M, C, T).
rejected(T) :- test(T), unsafe_test(T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for cid in CAUSES:
        lines.append(asp.fact("cause", cid))
    for tid in TESTS:
        lines.append(asp.fact("test", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    pset = set(valid_combos())
    aset = set(asp_valid_combos())
    if pset == aset:
        print(f"OK: gate matches valid_combos() ({len(pset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if aset - pset:
            print("  only in clingo:", sorted(aset - pset))
        if pset - aset:
            print("  only in python:", sorted(pset - aset))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a funny cautionary water mystery with suction and a spigot."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--test", choices=TESTS)
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.test and args.test == "mouth_sip":
        raise StoryError(explain_test_rejection(args.test))

    combos = [
        combo for combo in valid_combos()
        if (args.mystery is None or combo[0] == args.mystery)
        and (args.cause is None or combo[1] == args.cause)
        and (args.test is None or combo[2] == args.test)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mystery_id, cause_id, test_id = rng.choice(sorted(combos))
    theme_id = args.theme or rng.choice(sorted(THEMES))
    child_name, child_gender = _pick_kid(rng)
    friend_name, friend_gender = _pick_kid(rng, avoid=child_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        theme=theme_id,
        mystery=mystery_id,
        cause=cause_id,
        test=test_id,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(No story: unknown theme '{params.theme}'.)")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"(No story: unknown mystery '{params.mystery}'.)")
    if params.cause not in CAUSES:
        raise StoryError(f"(No story: unknown cause '{params.cause}'.)")
    if params.test not in TESTS:
        raise StoryError(f"(No story: unknown test '{params.test}'.)")
    if params.test == "mouth_sip":
        raise StoryError(explain_test_rejection(params.test))

    if not valid_combo(MYSTERIES[params.mystery], CAUSES[params.cause], TESTS[params.test]):
        raise StoryError("(No story: those options do not make a reasonable water mystery.)")

    world = tell(
        theme=THEMES[params.theme],
        mystery=MYSTERIES[params.mystery],
        cause=CAUSES[params.cause],
        test=TESTS[params.test],
        child_name=params.child_name,
        child_gender=params.child_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/3.\n#show rejected/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mystery, cause, test) combos:\n")
        for mystery, cause, test in combos:
            print(f"  {mystery:8} {cause:12} {test}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} & {p.friend_name}: {p.mystery} / {p.cause} / {p.test}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
