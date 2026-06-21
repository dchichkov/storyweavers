#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/doo_flashback_whodunit.py
====================================================

A small storyworld for a child-facing whodunit with a flashback reveal.

A snack goes missing during a rainy indoor gathering. A child detective notices
simple clues, asks calm questions, and works out who moved the missing treat.
The reveal includes a brief flashback that shows what really happened, turning a
mystery into a gentle lesson about asking before taking and telling the truth.

Run it
------
python storyworlds/worlds/gpt-5.4/doo_flashback_whodunit.py
python storyworlds/worlds/gpt-5.4/doo_flashback_whodunit.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/doo_flashback_whodunit.py --all
python storyworlds/worlds/gpt-5.4/doo_flashback_whodunit.py --qa
python storyworlds/worlds/gpt-5.4/doo_flashback_whodunit.py --json
python storyworlds/worlds/gpt-5.4/doo_flashback_whodunit.py --trace
python storyworlds/worlds/gpt-5.4/doo_flashback_whodunit.py --asp
python storyworlds/worlds/gpt-5.4/doo_flashback_whodunit.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    room: str
    weather: str
    sound: str
    find_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    crumbs: str
    smell: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Container:
    id: str
    label: str
    phrase: str
    open_text: str
    empty_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CluePath:
    id: str
    mark: str
    trail_text: str
    innocent_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CulpritNature:
    id: str
    motive: str
    hide_text: str
    confession_text: str
    lesson_text: str
    allowed_helpers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    role_name: str
    ask_text: str
    calm_text: str
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


def _r_missing_makes_mystery(world: World) -> list[str]:
    treat = world.get("treat")
    detective = world.get("detective")
    if treat.meters["missing"] < THRESHOLD:
        return []
    sig = ("mystery", "missing")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["curiosity"] += 1
    room = world.get("room")
    room.meters["mystery"] += 1
    return []


def _r_trail_points(world: World) -> list[str]:
    clue = world.get("clue")
    detective = world.get("detective")
    suspect = world.get("suspect")
    if clue.meters["seen"] < THRESHOLD:
        return []
    sig = ("pointed", suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.meters["suspected"] += 1
    detective.memes["focus"] += 1
    return []


def _r_kind_question_relieves(world: World) -> list[str]:
    helper = world.get("helper")
    suspect = world.get("suspect")
    if helper.meters["asked_kindly"] < THRESHOLD:
        return []
    if suspect.meters["suspected"] < THRESHOLD:
        return []
    sig = ("calm", suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.memes["fear"] = max(0.0, suspect.memes["fear"] - 1.0)
    suspect.memes["honesty"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_makes_mystery", tag="social", apply=_r_missing_makes_mystery),
    Rule(name="trail_points", tag="physical", apply=_r_trail_points),
    Rule(name="kind_question_relieves", tag="social", apply=_r_kind_question_relieves),
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
            world.say(sent)
    return produced


def valid_combo(culprit: str, helper: str) -> bool:
    if culprit not in CULPRIT_NATURES or helper not in HELPERS:
        return False
    return helper in CULPRIT_NATURES[culprit].allowed_helpers


def valid_combos() -> list[tuple[str, str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str, str]] = []
    for setting in SETTINGS:
        for treat in TREATS:
            for container in CONTAINERS:
                for clue in CLUE_PATHS:
                    for culprit in CULPRIT_NATURES:
                        for helper in HELPERS:
                            if valid_combo(culprit, helper):
                                combos.append((setting, treat, container, clue, culprit, helper))
    return combos


@dataclass
class StoryParams:
    setting: str
    treat: str
    container: str
    clue: str
    culprit: str
    helper: str
    detective_name: str
    detective_gender: str
    suspect_name: str
    suspect_gender: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the house",
        room="the warm kitchen",
        weather="rain tapped at the window",
        sound='the old oven timer said "doo-doo" from the counter',
        find_text="beside the bread box",
        tags={"home", "rain"},
    ),
    "clubhouse": Setting(
        id="clubhouse",
        place="the block club room",
        room="the little clubhouse kitchen",
        weather="wind fussed at the shutters",
        sound='the toy radio on the shelf made a tiny "doo-doo" sound',
        find_text="under the striped bench",
        tags={"clubhouse"},
    ),
    "library": Setting(
        id="library",
        place="the library meeting room",
        room="the cozy library snack corner",
        weather="soft gray light lay on the windowpanes",
        sound='the check-in scanner whispered "doo-doo" near the desk',
        find_text="behind the story cushion",
        tags={"library"},
    ),
}

TREATS = {
    "bun": Treat(
        id="bun",
        label="honey bun",
        phrase="a sticky honey bun",
        crumbs="a few shiny crumbs",
        smell="a sweet smell of honey",
        tags={"snack", "bun"},
    ),
    "tart": Treat(
        id="tart",
        label="berry tart",
        phrase="a little berry tart",
        crumbs="purple crumbs",
        smell="a jammy berry smell",
        tags={"snack", "berry"},
    ),
    "cookie": Treat(
        id="cookie",
        label="cinnamon cookie",
        phrase="a warm cinnamon cookie",
        crumbs="brown sugary crumbs",
        smell="a cinnamon smell",
        tags={"snack", "cookie"},
    ),
}

CONTAINERS = {
    "plate": Container(
        id="plate",
        label="plate",
        phrase="a blue plate",
        open_text="sat on a blue plate in the middle of the table",
        empty_text="The blue plate was empty",
        tags={"plate"},
    ),
    "tin": Container(
        id="tin",
        label="tin",
        phrase="a round tin",
        open_text="rested inside a round tin with a painted lid",
        empty_text="The round tin stood open and empty",
        tags={"tin"},
    ),
    "basket": Container(
        id="basket",
        label="basket",
        phrase="a red basket",
        open_text="waited in a red basket lined with a napkin",
        empty_text="The red basket held only a crumpled napkin",
        tags={"basket"},
    ),
}

CLUE_PATHS = {
    "crumbs": CluePath(
        id="crumbs",
        mark="crumbs",
        trail_text="The detective noticed a neat line of crumbs leading away from the table.",
        innocent_text="There were no muddy footprints, no torn napkins, only patient little crumbs.",
        tags={"crumbs"},
    ),
    "jam": CluePath(
        id="jam",
        mark="jam",
        trail_text="A shiny dot of jam gleamed on the table edge and another on the floor.",
        innocent_text="Nothing looked smashed or wild. The clue was small and careful, not rough.",
        tags={"jam"},
    ),
    "sugar": CluePath(
        id="sugar",
        mark="sugar",
        trail_text="A dusting of sugar sparkled in a tiny trail toward the corner.",
        innocent_text="The trail was light and tidy, as if someone had tiptoed with a full mouth.",
        tags={"sugar"},
    ),
}

CULPRIT_NATURES = {
    "hungry_child": CulpritNature(
        id="hungry_child",
        motive="was too hungry to wait",
        hide_text="curled up with sticky fingers and round guilty eyes",
        confession_text="thought the treat was only sitting there for anybody and took it without asking",
        lesson_text="If you want a snack, it is better to ask than to sneak.",
        allowed_helpers={"mother", "father"},
        tags={"asking", "truth"},
    ),
    "saving_for_friend": CulpritNature(
        id="saving_for_friend",
        motive="wanted to save a bite for a late friend",
        hide_text="held the missing treat in a napkin, trying to do a kind thing the secret way",
        confession_text="meant to share it later but forgot that hiding it would frighten everybody now",
        lesson_text="A kind idea still needs truthful words.",
        allowed_helpers={"mother", "father", "grandparent"},
        tags={"sharing", "truth"},
    ),
    "sleepy_sneak": CulpritNature(
        id="sleepy_sneak",
        motive="felt sleepy and took a nibble before thinking",
        hide_text="sat in the corner chewing slowly, as if the snack had walked there by itself",
        confession_text="took just one bite, then another, and then felt too embarrassed to say so",
        lesson_text="Small secrets can grow into big worries.",
        allowed_helpers={"grandparent"},
        tags={"sleepy", "truth"},
    ),
}

HELPERS = {
    "mother": Helper(
        id="mother",
        role_name="mom",
        ask_text='said, "Let us look before we scold. Clues can tell the truth if we listen."',
        calm_text='knelt beside the suspect and spoke in a soft voice',
        tags={"adult"},
    ),
    "father": Helper(
        id="father",
        role_name="dad",
        ask_text='said, "A good detective uses kind questions, not angry guesses."',
        calm_text='folded his arms gently and kept his voice low and steady',
        tags={"adult"},
    ),
    "grandparent": Helper(
        id="grandparent",
        role_name="grandma",
        ask_text='said, "Slow mysteries are often solved by slow eyes."',
        calm_text='sat down beside the suspect so the corner did not feel scary',
        tags={"adult"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Lucy", "Ella", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Finn", "Theo", "Jack", "Eli"]


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def setup_world(params: StoryParams) -> World:
    try:
        setting = SETTINGS[params.setting]
        treat = TREATS[params.treat]
        container = CONTAINERS[params.container]
        clue = CLUE_PATHS[params.clue]
        culprit_cfg = CULPRIT_NATURES[params.culprit]
        helper_cfg = HELPERS[params.helper]
    except KeyError as exc:
        raise StoryError(f"(Invalid story parameter: {exc.args[0]!r})") from exc

    if not valid_combo(params.culprit, params.helper):
        raise StoryError(
            f"(No story: helper '{params.helper}' does not fit culprit style '{params.culprit}'.)"
        )

    world = World()
    detective = world.add(
        Entity(
            id=params.detective_name,
            kind="character",
            type=params.detective_gender,
            role="detective",
            label=params.detective_name,
            phrase=params.detective_name,
            traits=["curious", "observant"],
        )
    )
    suspect = world.add(
        Entity(
            id=params.suspect_name,
            kind="character",
            type=params.suspect_gender,
            role="suspect",
            label=params.suspect_name,
            phrase=params.suspect_name,
            traits=["quiet"],
            attrs={"culprit_nature": params.culprit},
        )
    )
    parent_type = "mother" if params.parent == "mother" else "father"
    parent_label = "Mom" if parent_type == "mother" else "Dad"
    world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label=parent_label,
            phrase=parent_label,
        )
    )
    world.add(
        Entity(
            id="helper",
            kind="thing",
            type="helper",
            role="helper_cfg",
            label=helper_cfg.role_name,
            phrase=helper_cfg.role_name,
            attrs={"helper_id": params.helper},
        )
    )
    world.add(
        Entity(
            id="room",
            type="room",
            label=setting.room,
            phrase=setting.room,
        )
    )
    world.add(
        Entity(
            id="treat",
            type="treat",
            label=treat.label,
            phrase=treat.phrase,
            tags=set(treat.tags),
        )
    )
    world.add(
        Entity(
            id="container",
            type="container",
            label=container.label,
            phrase=container.phrase,
            tags=set(container.tags),
        )
    )
    world.add(
        Entity(
            id="clue",
            type="clue",
            label=clue.mark,
            phrase=clue.mark,
            tags=set(clue.tags),
        )
    )

    world.facts.update(
        setting=setting,
        treat_cfg=treat,
        container_cfg=container,
        clue_cfg=clue,
        culprit_cfg=culprit_cfg,
        helper_cfg=helper_cfg,
        detective=detective,
        suspect=suspect,
        parent=world.get("Parent"),
    )
    return world


def scene_open(world: World) -> None:
    f = world.facts
    setting = f["setting"]
    detective = f["detective"]
    suspect = f["suspect"]
    treat = f["treat_cfg"]
    container = f["container_cfg"]
    world.say(
        f"In {setting.room}, {detective.id} and {suspect.id} waited for snack time while {setting.weather}."
    )
    world.say(
        f"On the table, {treat.phrase} {container.open_text}, and {setting.sound}."
    )
    detective.memes["joy"] += 1
    suspect.memes["anticipation"] += 1


def discover_missing(world: World) -> None:
    container = world.get("container")
    treat = world.get("treat")
    container.meters["empty"] += 1
    treat.meters["missing"] += 1
    propagate(world, narrate=False)
    empty_text = world.facts["container_cfg"].empty_text
    world.say(
        f"When snack time finally came, {empty_text}. The {treat.label} was gone."
    )
    world.say("Nobody had seen anyone take it, and the room suddenly felt full of questions.")


def detective_notices(world: World) -> None:
    clue = world.get("clue")
    detective = world.get("detective")
    clue_cfg = world.facts["clue_cfg"]
    clue.meters["seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{detective.id} did not shout. {detective.pronoun().capitalize()} looked at the table, the floor, and the quiet corners."
    )
    world.say(clue_cfg.trail_text)
    world.say(clue_cfg.innocent_text)


def helper_guides(world: World) -> None:
    helper_cfg = world.facts["helper_cfg"]
    parent = world.get("Parent")
    detective = world.get("detective")
    world.say(f"{parent.label} {helper_cfg.ask_text}")
    detective.memes["confidence"] += 1


def ask_kindly(world: World) -> None:
    helper_cfg = world.facts["helper_cfg"]
    helper = world.get("helper")
    suspect = world.get("suspect")
    helper.meters["asked_kindly"] += 1
    suspect.memes["fear"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Following the little trail, they found {suspect.id} {world.facts['culprit_cfg'].hide_text} {world.facts['setting'].find_text}."
    )
    world.say(
        f"{world.get('Parent').label} {helper_cfg.calm_text}. {suspect.id} looked down at the floor."
    )


def flashback_reveal(world: World) -> None:
    detective = world.get("detective")
    suspect = world.get("suspect")
    treat = world.facts["treat_cfg"]
    culprit_cfg = world.facts["culprit_cfg"]
    suspect.meters["confessed"] += 1
    suspect.memes["honesty"] += 1
    world.say(
        f'Then {suspect.id} whispered that {suspect.pronoun()} {culprit_cfg.motive}.'
    )
    world.say(
        f"In a quick flashback, {detective.id} pictured it: a few minutes earlier, {suspect.id} had seen {treat.phrase}, glanced around, lifted it from the {world.facts['container_cfg'].label}, and tiptoed away with it."
    )
    world.say(
        f"The tiny trail made sense now. {suspect.id} {culprit_cfg.confession_text}."
    )


def resolution(world: World) -> None:
    detective = world.get("detective")
    suspect = world.get("suspect")
    parent = world.get("Parent")
    culprit_cfg = world.facts["culprit_cfg"]
    treat = world.facts["treat_cfg"]
    suspect.memes["relief"] += 1
    detective.memes["relief"] += 1
    detective.memes["kindness"] += 1
    world.say(
        f"{detective.id} solved the mystery at last, but {detective.pronoun()} did not crow or point. {detective.pronoun().capitalize()} only nodded."
    )
    world.say(
        f'"So that is what happened," {parent.label} said. "{culprit_cfg.lesson_text}"'
    )
    world.say(
        f"{suspect.id} broke the last piece of the {treat.label} in two and offered half to {detective.id}."
    )
    world.say(
        f"Soon the room felt warm again, and the mystery that had started with a little doo-doo sound ended with two children sharing a snack and telling the truth."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    scene_open(world)
    world.para()
    discover_missing(world)
    detective_notices(world)
    helper_guides(world)
    world.para()
    ask_kindly(world)
    flashback_reveal(world)
    world.para()
    resolution(world)

    suspect = world.get("suspect")
    detective = world.get("detective")
    world.facts.update(
        outcome="solved",
        used_flashback=True,
        confessed=suspect.meters["confessed"] >= THRESHOLD,
        detective_kind=detective.memes["kindness"] >= THRESHOLD,
        missing=world.get("treat").meters["missing"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    suspect = f["suspect"]
    treat = f["treat_cfg"]
    return [
        'Write a short whodunit for a 3-to-5-year-old that includes the word "doo" and uses a flashback reveal.',
        f"Tell a gentle mystery where {detective.id} notices clues after a missing {treat.label} disappears and calmly discovers what {suspect.id} did.",
        f"Write a child-facing story in whodunit style where a missing snack causes worry, then a flashback explains the truth and ends with sharing instead of punishment.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    suspect = f["suspect"]
    parent = f["parent"]
    treat = f["treat_cfg"]
    clue = f["clue_cfg"]
    culprit_cfg = f["culprit_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, who acts like a little detective, {suspect.id}, who hid the missing snack, and {parent.label}, who helps them ask calm questions.",
        ),
        (
            f"What was missing?",
            f"The missing thing was {treat.phrase}. It had been left out for snack time, so everyone noticed when it was gone.",
        ),
        (
            f"How did {detective.id} start solving the mystery?",
            f"{detective.id} looked carefully instead of guessing. The {clue.mark} clue showed that someone had carried the snack away quietly, so the mystery could be solved by paying attention.",
        ),
        (
            "Why was there a flashback in the story?",
            f"The flashback showed what had happened a few minutes earlier. It let the reader see how {suspect.id} took the {treat.label}, so the clue trail suddenly made sense.",
        ),
        (
            f"Why did {suspect.id} take the {treat.label}?",
            f"{suspect.id} took it because {suspect.pronoun()} {culprit_cfg.motive}. {suspect.pronoun().capitalize()} did not mean to start a big mystery, but hiding the snack made everyone worry.",
        ),
        (
            "How did the story end?",
            f"The truth came out, and the children shared what was left. The ending proves the room changed from worried and suspicious to warm and honest.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "crumbs": [
        (
            "What can crumbs tell you?",
            "Crumbs can show where food has been carried or eaten. Tiny pieces can act like a trail if you look carefully.",
        )
    ],
    "jam": [
        (
            "Why can a little drop of jam be a clue?",
            "A sticky drop can show where someone set food down or brushed against something. Even a very small mark can help solve a mystery.",
        )
    ],
    "sugar": [
        (
            "Why does spilled sugar make a trail?",
            "Sugar grains can fall a little at a time as someone walks. That is why a sweet trail can point from one place to another.",
        )
    ],
    "asking": [
        (
            "Why should you ask before taking a snack?",
            "Asking is respectful and helps everyone know what is happening. If you take food in secret, people may worry or feel upset.",
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting someone else have part of something good with you. It helps people feel included and cared for.",
        )
    ],
    "truth": [
        (
            "Why is telling the truth important?",
            "Telling the truth helps people trust you and solve problems faster. A true answer can make a scary mystery feel smaller right away.",
        )
    ],
    "sleepy": [
        (
            "Why do people sometimes make poor choices when they feel sleepy?",
            "Sleepy people may forget to stop and think first. That can make a quick choice seem easier than the right choice.",
        )
    ],
    "whodunit": [
        (
            "What is a whodunit story?",
            "A whodunit is a mystery story where people try to work out who did something. Clues help the reader and the detective discover the answer.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a short look back at something that happened earlier. It helps explain the present part of the story.",
        )
    ],
}
KNOWLEDGE_ORDER = ["whodunit", "flashback", "crumbs", "jam", "sugar", "asking", "sharing", "truth", "sleepy"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"whodunit", "flashback"} | set(f["clue_cfg"].tags) | set(f["culprit_cfg"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
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
        bits: list[str] = []
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
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="kitchen",
        treat="bun",
        container="plate",
        clue="crumbs",
        culprit="hungry_child",
        helper="mother",
        detective_name="Lily",
        detective_gender="girl",
        suspect_name="Ben",
        suspect_gender="boy",
        parent="mother",
    ),
    StoryParams(
        setting="library",
        treat="tart",
        container="tin",
        clue="jam",
        culprit="saving_for_friend",
        helper="grandparent",
        detective_name="Max",
        detective_gender="boy",
        suspect_name="Ava",
        suspect_gender="girl",
        parent="father",
    ),
    StoryParams(
        setting="clubhouse",
        treat="cookie",
        container="basket",
        clue="sugar",
        culprit="sleepy_sneak",
        helper="grandparent",
        detective_name="Zoe",
        detective_gender="girl",
        suspect_name="Finn",
        suspect_gender="boy",
        parent="mother",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child-friendly whodunit with a flashback reveal."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--clue", choices=CLUE_PATHS)
    ap.add_argument("--culprit", choices=CULPRIT_NATURES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--suspect-name")
    ap.add_argument("--suspect-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible scenarios from clingo")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.culprit and args.helper and not valid_combo(args.culprit, args.helper):
        raise StoryError(
            f"(No story: helper '{args.helper}' does not fit culprit style '{args.culprit}'.)"
        )

    combos = [
        c
        for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.treat is None or c[1] == args.treat)
        and (args.container is None or c[2] == args.container)
        and (args.clue is None or c[3] == args.clue)
        and (args.culprit is None or c[4] == args.culprit)
        and (args.helper is None or c[5] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, treat, container, clue, culprit, helper = rng.choice(sorted(combos))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    suspect_gender = args.suspect_gender or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or _pick_name(rng, detective_gender)
    suspect_name = args.suspect_name or _pick_name(rng, suspect_gender, avoid=detective_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting,
        treat=treat,
        container=container,
        clue=clue,
        culprit=culprit,
        helper=helper,
        detective_name=detective_name,
        detective_gender=detective_gender,
        suspect_name=suspect_name,
        suspect_gender=suspect_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.culprit, params.helper):
        raise StoryError(
            f"(No story: helper '{params.helper}' does not fit culprit style '{params.culprit}'.)"
        )
    world = tell(params)
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


ASP_RULES = r"""
valid_combo(C, H) :- culprit(C), helper(H), allows(C, H).

chosen_valid :- chosen_culprit(C), chosen_helper(H), valid_combo(C, H).
:- chosen_culprit(C), chosen_helper(H), not valid_combo(C, H).

outcome(solved) :- chosen_valid.
uses_flashback :- chosen_valid.
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TREATS:
        lines.append(asp.fact("treat", tid))
    for cid in CONTAINERS:
        lines.append(asp.fact("container", cid))
    for clid in CLUE_PATHS:
        lines.append(asp.fact("clue", clid))
    for culprit_id, culprit in CULPRIT_NATURES.items():
        lines.append(asp.fact("culprit", culprit_id))
        for helper in sorted(culprit.allowed_helpers):
            lines.append(asp.fact("allows", culprit_id, helper))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_culprit", params.culprit),
            asp.fact("chosen_helper", params.helper),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_pairs = sorted((c, h) for c in CULPRIT_NATURES for h in HELPERS if valid_combo(c, h))
    asp_pairs = sorted(asp_valid_combos())
    if asp_pairs == py_pairs:
        print(f"OK: ASP valid helpers match Python ({len(py_pairs)} pairs).")
    else:
        rc = 1
        print("MISMATCH in valid helper pairs:")
        only_asp = sorted(set(asp_pairs) - set(py_pairs))
        only_py = sorted(set(py_pairs) - set(asp_pairs))
        if only_asp:
            print("  only in ASP:", only_asp)
        if only_py:
            print("  only in Python:", only_py)

    for params in CURATED:
        outcome = asp_outcome(params)
        if outcome != "solved":
            rc = 1
            print(f"MISMATCH outcome for curated case {params}: ASP={outcome}")
            break

    try:
        sample = generate(CURATED[0])
        if not sample.story or "flashback" not in sample.story.lower():
            rc = 1
            print("Smoke test failed: generated story missing text or flashback beat.")
        else:
            print("OK: smoke test story generation passed.")
    except Exception as exc:  # pragma: no cover - verify path only
        rc = 1
        print(f"Smoke test failed with exception: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid_combo/2.\n#show outcome/1.\n#show uses_flashback/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_combos()
        print(f"{len(pairs)} compatible (culprit, helper) pairs:\n")
        for culprit, helper in pairs:
            print(f"  {culprit:16} {helper}")
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
            header = f"### {p.detective_name}: {p.treat} mystery in {p.setting} ({p.culprit}, helper: {p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
