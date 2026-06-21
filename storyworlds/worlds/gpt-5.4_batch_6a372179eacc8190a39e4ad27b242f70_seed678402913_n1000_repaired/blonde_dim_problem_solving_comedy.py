#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/blonde_dim_problem_solving_comedy.py
===============================================================

A small story world about a child building a blanket-fort clubhouse, hanging a
sign the silly wrong way, and then solving the problem with the right fastening
tool. The stories aim for gentle comedy: the sign keeps booping somebody on the
nose until the child and helper stop guessing and think about what the fort is
made of.

The seed word "blonde-dim" is included in the opening image as a soft, buttery
kind of dim light inside the fort.

Run it
------
    python storyworlds/worlds/gpt-5.4/blonde_dim_problem_solving_comedy.py
    python storyworlds/worlds/gpt-5.4/blonde_dim_problem_solving_comedy.py --mount chair_backs --sign fabric_flag
    python storyworlds/worlds/gpt-5.4/blonde_dim_problem_solving_comedy.py --mount chair_backs --fix tape_loop
    python storyworlds/worlds/gpt-5.4/blonde_dim_problem_solving_comedy.py --all
    python storyworlds/worlds/gpt-5.4/blonde_dim_problem_solving_comedy.py --qa --json
    python storyworlds/worlds/gpt-5.4/blonde_dim_problem_solving_comedy.py --verify
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
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class FortTheme:
    id: str
    scene: str
    title: str
    intro_props: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SignSpec:
    id: str
    label: str
    phrase: str
    slogan: str
    weight: int
    flat_back: bool = False
    tieable: bool = False
    floppy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class MountSpec:
    id: str
    label: str
    phrase: str
    mode: str = ""
    reason: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class FixSpec:
    id: str
    label: str
    phrase: str
    mode: str = ""
    capacity: int = 0
    sense: int = 2
    requires_flat: bool = False
    requires_tieable: bool = False
    attach_text: str = ""
    qa_text: str = ""
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


def _r_fall(world: World) -> list[str]:
    sign = world.get("sign")
    if sign.meters["propped"] < THRESHOLD or sign.meters["secure"] >= THRESHOLD:
        return []
    sig = ("fall", "sign")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    sign.meters["fallen"] += 1
    sign.meters["propped"] = 0.0
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["frustration"] += 1
    hero.memes["laughter"] += 1
    helper.memes["laughter"] += 1
    return ["__fall__"]


def _r_secure(world: World) -> list[str]:
    sign = world.get("sign")
    if sign.meters["secure"] < THRESHOLD:
        return []
    sig = ("secure", "sign")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    helper.memes["pride"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="fall", tag="physical", apply=_r_fall),
    Rule(name="secure", tag="social", apply=_r_secure),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


THEMES = {
    "spaceship": FortTheme(
        id="spaceship",
        scene="a spaceship made of sofa cushions and silver-gray blankets",
        title="Star Button Club",
        intro_props="One chair became a launch tower, a mixing bowl became a moon helmet, and a wooden spoon became the captain's pointer.",
        ending="Soon the clubhouse looked ready to blast off.",
        tags={"fort"},
    ),
    "bakery": FortTheme(
        id="bakery",
        scene="a tiny bakery made of quilts and upside-down laundry baskets",
        title="Crumb Palace",
        intro_props="A toy pan was the cookie counter, a pillow was the bread hill, and a striped towel hung like a grand shop curtain.",
        ending="Soon the clubhouse looked ready for a line of very serious pretend customers.",
        tags={"fort"},
    ),
    "castle": FortTheme(
        id="castle",
        scene="a castle made of chairs, blankets, and one brave couch pillow",
        title="Royal Blanket Hall",
        intro_props="A cardboard tube became a trumpet, a saucepan lid became a shield, and two socks sat by the door as the royal guard.",
        ending="Soon the clubhouse looked ready for a parade of giggling kings and queens.",
        tags={"fort"},
    ),
}

SIGNS = {
    "paper_star": SignSpec(
        id="paper_star",
        label="paper star sign",
        phrase="a paper star sign",
        slogan="STAR BUTTON CLUB",
        weight=1,
        flat_back=True,
        tieable=False,
        floppy=False,
        tags={"paper", "sign"},
    ),
    "cardboard_moon": SignSpec(
        id="cardboard_moon",
        label="cardboard moon sign",
        phrase="a cardboard moon sign",
        slogan="MOON DOOR",
        weight=2,
        flat_back=True,
        tieable=False,
        floppy=False,
        tags={"cardboard", "sign"},
    ),
    "fabric_flag": SignSpec(
        id="fabric_flag",
        label="fabric flag",
        phrase="a fabric flag with stitched corners",
        slogan="WELCOME, VERY IMPORTANT CLUB",
        weight=1,
        flat_back=False,
        tieable=True,
        floppy=True,
        tags={"fabric", "sign"},
    ),
}

MOUNTS = {
    "blanket_flap": MountSpec(
        id="blanket_flap",
        label="blanket flap",
        phrase="the blanket flap over the doorway",
        mode="clip",
        reason="soft cloth is easy to pinch but hard to tape neatly",
        tags={"blanket"},
    ),
    "box_door": MountSpec(
        id="box_door",
        label="box doorway",
        phrase="the flat side of a big cardboard box doorway",
        mode="tape",
        reason="flat cardboard gives tape a place to hold",
        tags={"cardboard"},
    ),
    "chair_backs": MountSpec(
        id="chair_backs",
        label="chair backs",
        phrase="two chair backs with a gap between them",
        mode="tie",
        reason="there is nothing flat to stick to, but there is a good place to tie",
        tags={"chair"},
    ),
}

FIXES = {
    "clothespin": FixSpec(
        id="clothespin",
        label="clothespin",
        phrase="a wooden clothespin",
        mode="clip",
        capacity=2,
        sense=3,
        attach_text="pinched the sign to the blanket edge with a wooden clothespin",
        qa_text="used a clothespin to clip the sign to the blanket edge",
        tags={"clothespin"},
    ),
    "tape_loop": FixSpec(
        id="tape_loop",
        label="tape loop",
        phrase="a fat loop of tape",
        mode="tape",
        capacity=2,
        sense=3,
        requires_flat=True,
        attach_text="rolled a fat loop of tape and pressed the sign onto the box doorway",
        qa_text="used a loop of tape on the flat cardboard doorway",
        tags={"tape"},
    ),
    "yarn_bow": FixSpec(
        id="yarn_bow",
        label="yarn bow",
        phrase="a piece of yellow yarn",
        mode="tie",
        capacity=1,
        sense=3,
        requires_tieable=True,
        attach_text="threaded yellow yarn through the stitched corners and tied the sign between the chair backs",
        qa_text="tied the sign up with yellow yarn",
        tags={"knot", "yarn"},
    ),
    "chewing_gum": FixSpec(
        id="chewing_gum",
        label="chewing gum",
        phrase="a wad of chewing gum",
        mode="tape",
        capacity=0,
        sense=1,
        attach_text="squashed chewing gum against everything in sight",
        qa_text="tried to use chewing gum",
        tags={"gum"},
    ),
}


def sign_fits_fix(sign: SignSpec, fix: FixSpec) -> bool:
    if fix.requires_flat and not sign.flat_back:
        return False
    if fix.requires_tieable and not sign.tieable:
        return False
    return fix.capacity >= sign.weight


def valid_combo(sign: SignSpec, mount: MountSpec, fix: FixSpec) -> bool:
    return mount.mode == fix.mode and sign_fits_fix(sign, fix) and fix.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme_id in THEMES:
        for sign_id, sign in SIGNS.items():
            for mount_id, mount in MOUNTS.items():
                for fix_id, fix in FIXES.items():
                    if valid_combo(sign, mount, fix):
                        combos.append((theme_id, sign_id, mount_id, fix_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    sign: str
    mount: str
    fix: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    helper_role: str
    parent: str
    seed: Optional[int] = None


def _pair_noun(hero: Entity, helper: Entity, role: str) -> str:
    if role == "sibling":
        if hero.type == "boy" and helper.type == "boy":
            return "two brothers"
        if hero.type == "girl" and helper.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def _helper_phrase(helper: Entity, role: str) -> str:
    if role == "sibling":
        return f"{helper.id}, {helper.pronoun('possessive')} sibling"
    return f"{helper.id}, {helper.pronoun('possessive')} friend"


def explain_invalid(sign: SignSpec, mount: MountSpec, fix: FixSpec) -> str:
    if fix.sense < SENSE_MIN:
        return (
            f"(Refusing fix '{fix.id}': {fix.label} is too silly and too weak for a careful problem-solving story. "
            f"Pick a real fastening tool like clothespin, tape_loop, or yarn_bow.)"
        )
    if mount.mode != fix.mode:
        return (
            f"(No story: {fix.label} does not match {mount.phrase}. {mount.reason.capitalize()}, "
            f"so this problem needs a {mount.mode}-style fix instead.)"
        )
    if fix.requires_flat and not sign.flat_back:
        return (
            f"(No story: {sign.phrase} is floppy cloth, so tape will not hold it neatly. "
            f"Pick a tieable fix instead.)"
        )
    if fix.requires_tieable and not sign.tieable:
        return (
            f"(No story: {sign.phrase} has nowhere to tie yarn through. "
            f"Pick a sign with corners or loops, or choose a different mount.)"
        )
    if fix.capacity < sign.weight:
        return (
            f"(No story: {fix.label} is too weak for {sign.phrase}. "
            f"The sign would keep dropping instead of staying up.)"
        )
    return "(No story: that sign, mount, and fix do not make sense together.)"


def choose_silly_attempt(sign: SignSpec, mount: MountSpec) -> str:
    if mount.id == "chair_backs":
        return f"{sign.phrase} on a spoon balanced across the chairs"
    if mount.id == "box_door":
        return f"{sign.phrase} by leaning it on one wobbly block"
    return f"{sign.phrase} by tucking just one corner into the blanket fold"


def predict_solution(sign: SignSpec, mount: MountSpec) -> dict:
    options = [fix for fix in FIXES.values() if valid_combo(sign, mount, fix)]
    best = max(options, key=lambda x: x.capacity)
    return {"mode": mount.mode, "best_fix": best.id, "reason": mount.reason}


def build_fort(world: World, hero: Entity, helper: Entity, theme: FortTheme) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"One afternoon, {hero.id} and {helper.id} turned the living room into {theme.scene}. "
        f"{theme.intro_props}"
    )
    world.say(
        f"Inside, the light was blonde-dim, buttery and funny, as if the whole fort had been toasted."
    )


def make_sign(world: World, hero: Entity, sign: SignSpec, theme: FortTheme, mount: MountSpec) -> None:
    sign_ent = world.get("sign")
    sign_ent.meters["made"] += 1
    world.say(
        f'{hero.id} made {sign.phrase} and wrote "{sign.slogan}" in big hopeful letters. '
        f'"This will hang on {mount.phrase}," {hero.pronoun()} said.'
    )
    if sign.floppy:
        world.say("The sign drooped in the middle like a sleepy tongue.")
    else:
        world.say("The sign looked proud and straight in both hands.")


def prop_badly(world: World, hero: Entity, helper: Entity, sign: SignSpec, mount: MountSpec) -> None:
    sign_ent = world.get("sign")
    hero.memes["confidence"] += 1
    sign_ent.meters["propped"] += 1
    world.say(
        f"{hero.id} tried to hang it by balancing {choose_silly_attempt(sign, mount)}."
    )
    propagate(world, narrate=False)
    if sign_ent.meters["fallen"] >= THRESHOLD:
        hero.meters["bonked"] += 1
        world.say(
            f"For one excellent second it stayed. Then plip -- down it slid and booped {hero.id} on the nose."
        )
        world.say(
            f'{helper.id} clapped a hand over {helper.pronoun("possessive")} mouth, but a laugh still escaped. '
            f'Soon {hero.id} was laughing too, even while rubbing {hero.pronoun("possessive")} nose.'
        )


def inspect_problem(world: World, hero: Entity, helper: Entity, sign: SignSpec, mount: MountSpec) -> None:
    helper.memes["thoughtful"] += 1
    pred = predict_solution(sign, mount)
    world.facts["predicted_fix"] = pred["best_fix"]
    world.facts["problem_reason"] = pred["reason"]
    world.say(
        f'{helper.id} crouched by the doorway and squinted. "{mount.phrase.capitalize()} is the important part," '
        f'{helper.pronoun()} said. "It keeps failing because {mount.reason}."'
    )
    if sign.tieable:
        world.say(
            f'{hero.id} touched the stitched corners of the sign. "So the sign has to match the doorway too," '
            f'{hero.pronoun()} said.'
        )
    else:
        world.say(
            f'{hero.id} turned the sign over and over. "So wishing harder is not a tool," {hero.pronoun()} said.'
        )


def fetch_fix(world: World, parent: Entity, hero: Entity, helper: Entity, fix: FixSpec) -> None:
    world.say(
        f"{hero.id} and {helper.id} hurried to the hall basket, and {hero.id}'s {parent.label_word} pointed them to {fix.phrase}."
    )


def attach_right(world: World, hero: Entity, helper: Entity, sign: SignSpec, mount: MountSpec, fix: FixSpec) -> None:
    sign_ent = world.get("sign")
    sign_ent.meters["secure"] += 1
    sign_ent.meters["steady"] += 1
    world.get("mount").meters["holding"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they {fix.attach_text}. This time the sign gave one tiny wiggle and stayed put."
    )
    if mount.id == "chair_backs":
        world.say("It swung once like a tiny parade banner, then settled exactly in the middle.")
    elif mount.id == "blanket_flap":
        world.say("The blanket flap puffed, but the clothespin held on like a little wooden crab.")
    else:
        world.say("The cardboard doorway finally looked official instead of confused.")


def celebrate(world: World, hero: Entity, helper: Entity, theme: FortTheme, parent: Entity) -> None:
    world.say(
        f'"We solved it!" {hero.id} said. {helper.id} gave the sign a respectful nod, as if it had passed a difficult test.'
    )
    world.say(
        f"{parent.label_word.capitalize()} peeked in, read the sign, and smiled. {theme.ending}"
    )
    world.say(
        f"By the end, everyone ducked through the doorway carefully, because a clubhouse with a real sign deserved that kind of respect."
    )


def tell(
    theme: FortTheme,
    sign: SignSpec,
    mount: MountSpec,
    fix: FixSpec,
    *,
    hero_name: str = "Lily",
    hero_gender: str = "girl",
    helper_name: str = "Ben",
    helper_gender: str = "boy",
    helper_role: str = "friend",
    parent_type: str = "mother",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    sign_ent = world.add(Entity(id="sign", type="sign", label=sign.label, phrase=sign.phrase))
    mount_ent = world.add(Entity(id="mount", type="mount", label=mount.label, phrase=mount.phrase))
    fix_ent = world.add(Entity(id="fix", type="fix", label=fix.label, phrase=fix.phrase))
    hero.attrs["name"] = hero_name
    helper.attrs["name"] = helper_name
    helper.attrs["role_kind"] = helper_role

    build_fort(world, hero_name_entity(hero), helper_name_entity(helper), theme)
    make_sign(world, hero_name_entity(hero), sign, theme, mount)

    world.para()
    prop_badly(world, hero_name_entity(hero), helper_name_entity(helper), sign, mount)
    inspect_problem(world, hero_name_entity(hero), helper_name_entity(helper), sign, mount)
    fetch_fix(world, parent_name_entity(parent), hero_name_entity(hero), helper_name_entity(helper), fix)

    world.para()
    attach_right(world, hero_name_entity(hero), helper_name_entity(helper), sign, mount, fix)
    celebrate(world, hero_name_entity(hero), helper_name_entity(helper), theme, parent_name_entity(parent))

    outcome = "solved" if sign_ent.meters["secure"] >= THRESHOLD else "unsolved"
    world.facts.update(
        hero=hero_name_entity(hero),
        helper=helper_name_entity(helper),
        parent=parent_name_entity(parent),
        theme=theme,
        sign_cfg=sign,
        mount_cfg=mount,
        fix_cfg=fix,
        sign=sign_ent,
        mount=mount_ent,
        fix=fix_ent,
        helper_role=helper_role,
        outcome=outcome,
        boop=hero.meters["bonked"] >= THRESHOLD,
    )
    return world


def hero_name_entity(ent: Entity) -> Entity:
    clone = copy.copy(ent)
    clone.id = ent.attrs.get("name", ent.id)
    return clone


def helper_name_entity(ent: Entity) -> Entity:
    clone = copy.copy(ent)
    clone.id = ent.attrs.get("name", ent.id)
    return clone


def parent_name_entity(ent: Entity) -> Entity:
    clone = copy.copy(ent)
    clone.id = ent.label_word.capitalize()
    return clone


KNOWLEDGE = {
    "fort": [
        (
            "What is a blanket fort?",
            "A blanket fort is a play space children make by draping blankets over chairs or couches. It turns an ordinary room into a pretend place."
        )
    ],
    "clothespin": [
        (
            "What does a clothespin do?",
            "A clothespin pinches cloth so it stays in place. It is useful when you need to clip something to a blanket or a line."
        )
    ],
    "tape": [
        (
            "Why does tape work best on flat surfaces?",
            "Tape sticks best when it can lie flat and press down evenly. If the surface is lumpy or floppy, it peels away much more easily."
        )
    ],
    "knot": [
        (
            "Why is tying useful?",
            "Tying is useful when there is something to loop around and something to thread through. A knot can hold light things up without needing a flat wall."
        )
    ],
    "cardboard": [
        (
            "What is cardboard good for?",
            "Cardboard is light but stiff, so it is good for making signs and pretend doors. Tape also sticks to it better than it sticks to loose cloth."
        )
    ],
    "paper": [
        (
            "Why can paper signs fall down easily?",
            "Paper is light, but it bends and slides if it is only leaned somewhere. It usually needs tape or a clip to stay where you want it."
        )
    ],
    "fabric": [
        (
            "Why can a fabric flag be hard to tape up?",
            "Fabric moves and wrinkles, so tape does not always stay stuck to it. Tying or clipping it often works better."
        )
    ],
}
KNOWLEDGE_ORDER = ["fort", "clothespin", "tape", "knot", "cardboard", "paper", "fabric"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    theme = f["theme"]
    sign = f["sign_cfg"]
    mount = f["mount_cfg"]
    return [
        f'Write a funny problem-solving story for a 3-to-5-year-old that includes the word "blonde-dim" and takes place in {theme.scene}.',
        f"Tell a gentle comedy where {hero.id} and {helper.id} make a clubhouse sign, it keeps falling from {mount.phrase}, and they solve the problem by matching the right tool to the doorway.",
        f'Write a short story where a child learns that guessing is not enough: the sign must fit both the material and the place where it hangs. Include a {sign.label}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    theme = f["theme"]
    sign = f["sign_cfg"]
    mount = f["mount_cfg"]
    fix = f["fix_cfg"]
    role = f["helper_role"]
    pair = _pair_noun(hero, helper, role)
    qa = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.id} and {helper.id}, who built {theme.scene}. {parent.label_word.capitalize()} appears too, but the children do the main solving."
        ),
        (
            "What problem did they have?",
            f"They wanted to hang {sign.phrase} on {mount.phrase}, but it would not stay up. The sign kept slipping because the children first tried balancing it instead of fastening it the right way."
        ),
    ]
    if f.get("boop"):
        qa.append(
            (
                f"What happened when {hero.id} tried the first idea?",
                f"The sign slid down and booped {hero.id} on the nose. That funny little failure showed them the sign was not really attached at all."
            )
        )
    qa.append(
        (
            "How did they solve the problem?",
            f"They stopped guessing, looked at what the doorway was made of, and chose {fix.phrase}. They solved it by matching the tool to the mount instead of hoping the sign would somehow stay."
        )
    )
    qa.append(
        (
            f"Why was {fix.label} the right fix?",
            f"It fit the doorway and the sign. {mount.reason.capitalize()}, so {fix.label} could hold where the first silly try could not."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"The sign finally stayed up, and the clubhouse looked real at last. The ending proves the problem was solved because everyone could duck through the doorway under a sign that did not fall."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["theme"].tags) | set(f["sign_cfg"].tags) | set(f["fix_cfg"].tags)
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo", "Noah"]


CURATED = [
    StoryParams(
        theme="spaceship",
        sign="paper_star",
        mount="blanket_flap",
        fix="clothespin",
        hero="Lily",
        hero_gender="girl",
        helper="Ben",
        helper_gender="boy",
        helper_role="friend",
        parent="mother",
    ),
    StoryParams(
        theme="castle",
        sign="cardboard_moon",
        mount="box_door",
        fix="tape_loop",
        hero="Max",
        hero_gender="boy",
        helper="Maya",
        helper_gender="girl",
        helper_role="sibling",
        parent="father",
    ),
    StoryParams(
        theme="bakery",
        sign="fabric_flag",
        mount="chair_backs",
        fix="yarn_bow",
        hero="Ella",
        hero_gender="girl",
        helper="Lucy",
        helper_gender="girl",
        helper_role="friend",
        parent="mother",
    ),
]


ASP_RULES = r"""
valid(T, S, M, F) :- theme(T), sign(S), mount(M), fix(F),
                     mount_mode(M, Mode), fix_mode(F, Mode),
                     sensible(F),
                     sign_ok(S, F).

sensible(F) :- fix(F), sense(F, V), sense_min(Min), V >= Min.

sign_ok(S, F) :- weight(S, W), capacity(F, C), C >= W,
                 not needs_flat_fail(S, F), not needs_tie_fail(S, F).

needs_flat_fail(S, F) :- requires_flat(F), not flat_back(S).
needs_tie_fail(S, F)  :- requires_tieable(F), not tieable(S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for sign_id, sign in SIGNS.items():
        lines.append(asp.fact("sign", sign_id))
        lines.append(asp.fact("weight", sign_id, sign.weight))
        if sign.flat_back:
            lines.append(asp.fact("flat_back", sign_id))
        if sign.tieable:
            lines.append(asp.fact("tieable", sign_id))
    for mount_id, mount in MOUNTS.items():
        lines.append(asp.fact("mount", mount_id))
        lines.append(asp.fact("mount_mode", mount_id, mount.mode))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("fix_mode", fix_id, fix.mode))
        lines.append(asp.fact("capacity", fix_id, fix.capacity))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        if fix.requires_flat:
            lines.append(asp.fact("requires_flat", fix_id))
        if fix.requires_tieable:
            lines.append(asp.fact("requires_tieable", fix_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_fixes() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(fix for (fix,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    python_sensible = sorted(fix_id for fix_id, fix in FIXES.items() if fix.sense >= SENSE_MIN)
    clingo_sensible = asp_sensible_fixes()
    if python_sensible == clingo_sensible:
        print(f"OK: sensible fixes match ({', '.join(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: python={python_sensible} clingo={clingo_sensible}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated smoke-test story was empty.")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a funny blanket-fort sign problem solved with the right tool."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--mount", choices=MOUNTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_invalid(SIGNS[args.sign] if args.sign else next(iter(SIGNS.values())),
                                         MOUNTS[args.mount] if args.mount else next(iter(MOUNTS.values())),
                                         FIXES[args.fix]))
    if args.sign and args.mount and args.fix:
        sign = SIGNS[args.sign]
        mount = MOUNTS[args.mount]
        fix = FIXES[args.fix]
        if not valid_combo(sign, mount, fix):
            raise StoryError(explain_invalid(sign, mount, fix))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.sign is None or combo[1] == args.sign)
        and (args.mount is None or combo[2] == args.mount)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, sign_id, mount_id, fix_id = rng.choice(sorted(combos))
    hero, hero_gender = _pick_child(rng)
    helper, helper_gender = _pick_child(rng, avoid=hero)
    helper_role = rng.choice(["friend", "sibling"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        theme=theme_id,
        sign=sign_id,
        mount=mount_id,
        fix=fix_id,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        helper_role=helper_role,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.sign not in SIGNS:
        raise StoryError(f"(Unknown sign: {params.sign})")
    if params.mount not in MOUNTS:
        raise StoryError(f"(Unknown mount: {params.mount})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    sign = SIGNS[params.sign]
    mount = MOUNTS[params.mount]
    fix = FIXES[params.fix]
    if not valid_combo(sign, mount, fix):
        raise StoryError(explain_invalid(sign, mount, fix))

    world = tell(
        THEMES[params.theme],
        sign,
        mount,
        fix,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        helper_role=params.helper_role,
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
        print(asp_program("#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sensible = asp_sensible_fixes()
        print(f"sensible fixes: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (theme, sign, mount, fix) combos:\n")
        for theme, sign, mount, fix in combos:
            print(f"  {theme:10} {sign:15} {mount:13} {fix}")
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
            header = f"### {p.hero} & {p.helper}: {p.sign} on {p.mount} with {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
