#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pastel_publish_curiosity_inner_monologue_moral_value.py

A standalone storyworld about a child who makes a pastel picture and badly wants
to publish it on a school board. Curiosity pulls the child toward a funny
shortcut, a kind grown-up explains the real way, and the ending proves that
honesty and patient asking turn curiosity into something useful.

Run it
------
python storyworlds/worlds/gpt-5.4/pastel_publish_curiosity_inner_monologue_moral_value.py
python storyworlds/worlds/gpt-5.4/pastel_publish_curiosity_inner_monologue_moral_value.py --place library --temptation copier
python storyworlds/worlds/gpt-5.4/pastel_publish_curiosity_inner_monologue_moral_value.py --all
python storyworlds/worlds/gpt-5.4/pastel_publish_curiosity_inner_monologue_moral_value.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/pastel_publish_curiosity_inner_monologue_moral_value.py --qa --json
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
CAREFUL_TRAITS = {"careful", "patient", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    touches_art: bool = False
    safe_for_pastel: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian", "teacher"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    board_name: str
    affords: set[str] = field(default_factory=set)
    helper_type: str = "teacher"
    helper_label: str = "the teacher"


@dataclass
class Subject:
    id: str
    noun: str
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Temptation:
    id: str
    label: str
    phrase: str
    machine_noise: str
    touch_verb: str
    warning: str
    touches_art: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class PublishMethod:
    id: str
    label: str
    phrase: str
    action: str
    result: str
    safe_for_pastel: bool = True
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_smudge(world: World) -> list[str]:
    art = world.get("art")
    machine = world.get("temptation")
    if art.meters["rolled"] < THRESHOLD or not machine.touches_art:
        return []
    sig = ("smudge", art.id, machine.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    art.meters["smudged"] += 1
    art.meters["dusty"] += 1
    world.get("room").meters["mess"] += 1
    hero = world.get("hero")
    hero.memes["embarrassment"] += 1
    hero.memes["alarm"] += 1
    return ["__smudge__"]


def _r_publish(world: World) -> list[str]:
    art = world.get("art")
    method = world.get("publish")
    if art.meters["captured"] < THRESHOLD or not method.safe_for_pastel:
        return []
    sig = ("publish", art.id, method.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    art.meters["published"] += 1
    hero = world.get("hero")
    hero.memes["pride"] += 1
    hero.memes["relief"] += 1
    return ["__published__"]


CAUSAL_RULES = [
    Rule(name="smudge", tag="physical", apply=_r_smudge),
    Rule(name="publish", tag="social", apply=_r_publish),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for item in produced:
            if item == "__smudge__":
                art = world.get("art")
                world.say(
                    f"A soft streak slid across the paper. A puff of pastel dust kissed "
                    f"{world.get('hero').id}'s nose, and suddenly {art.label} looked a little blurry."
                )
            elif item == "__published__":
                world.say(world.facts.get("published_line", "Soon the picture was up for everyone to see."))
    return produced


def valid_combo(place: str, temptation: str, publish: str) -> bool:
    if place not in SETTINGS or temptation not in TEMPTATIONS or publish not in PUBLISH_METHODS:
        return False
    setting = SETTINGS[place]
    tempt = TEMPTATIONS[temptation]
    method = PUBLISH_METHODS[publish]
    return (
        temptation in setting.affords
        and publish in setting.affords
        and tempt.touches_art
        and method.safe_for_pastel
        and temptation != publish
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for temptation in TEMPTATIONS:
            for publish in PUBLISH_METHODS:
                if valid_combo(place, temptation, publish):
                    combos.append((place, temptation, publish))
    return combos


def would_ask_first(friend_age: int, hero_age: int, trait: str) -> bool:
    careful = trait in CAREFUL_TRAITS
    friend_older = friend_age > hero_age
    return careful or friend_older


def predict_smudge(world: World) -> bool:
    sim = world.copy()
    art = sim.get("art")
    art.meters["rolled"] += 1
    propagate(sim, narrate=False)
    return art.meters["smudged"] >= THRESHOLD


def introduce(world: World, hero: Entity, friend: Entity, subject: Subject) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"After snack time in {world.setting.place}, {hero.id} sat beside {friend.id} and made "
        f"a pastel picture of {subject.detail}. The whole page glowed in soft peach, mint, and lilac."
    )
    world.say(
        f"{friend.id} leaned over and grinned. \"That {subject.noun} looks like it might wink at us,\" "
        f"{friend.pronoun()} said."
    )


def announce_board(world: World, hero: Entity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"At the front of the room stood {world.setting.board_name}, a place where children could publish "
        f"one special picture each week. {hero.id} looked at it and felt {hero.pronoun('possessive')} stomach "
        f"do a tiny happy flip."
    )


def inner_monologue(world: World, hero: Entity, subject: Subject) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f'Inside, {hero.id} thought, "If I can publish my pastel {subject.noun} right now, maybe everyone '
        f'will stop and laugh at the silly tail first."'
    )


def notice_machine(world: World, hero: Entity, temptation: Temptation) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"Near the wall sat {temptation.phrase}. It {temptation.machine_noise}, which made it sound important "
        f"and a little bossy."
    )
    world.say(
        f'Inside, {hero.id} thought, "Maybe that machine knows how to publish things faster than grown-ups do."'
    )


def warning(world: World, friend: Entity, temptation: Temptation) -> None:
    if predict_smudge(world):
        friend.memes["care"] += 1
        world.say(
            f'{friend.id} squinted at the picture. "{temptation.warning}," {friend.pronoun()} said. '
            f'"Pastel can rub off if something grabs it."'
        )


def back_down(world: World, hero: Entity, friend: Entity, helper: Entity, publish: PublishMethod) -> None:
    hero.memes["patience"] += 1
    hero.memes["honesty"] += 1
    world.say(
        f"{hero.id} reached toward the machine, then stopped. The curious feeling stayed, but it stopped marching "
        f"and started listening."
    )
    world.say(
        f'{hero.id} took a breath. "I want to know how to publish it the right way," {hero.pronoun()} said, '
        f"and carried the picture to {helper.label_word}."
    )
    world.say(
        f"{helper.label_word.capitalize()} smiled instead of scolding. {helper.pronoun().capitalize()} explained "
        f"that pastel dust is soft and easy to smear, so gentle tools are best."
    )
    publish_art(world, helper, publish, smudged=False)


def sneak(world: World, hero: Entity, temptation: Temptation) -> None:
    hero.memes["impatience"] += 1
    world.say(
        f'{hero.id} glanced at the board, glanced at the door, and whispered, "Just a teeny shortcut."'
    )
    world.say(
        f"{hero.pronoun().capitalize()} fed the page toward {temptation.phrase}, hoping it would {temptation.touch_verb} and make "
        f"everything official."
    )
    art = world.get("art")
    art.meters["rolled"] += 1
    propagate(world, narrate=True)


def confess(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["honesty"] += 1
    world.say(
        f"{hero.id} stared at the smudge and felt hot all the way to {hero.pronoun('possessive')} ears."
    )
    world.say(
        f'Inside, {hero.id} thought, "I could hide this behind my back... but then it would still be smudged, and I would still know."'
    )
    world.say(
        f'{hero.id} marched over to {helper.label_word} and blurted, "I tried the machine without asking, and my picture got messy."'
    )
    world.say(
        f"{helper.label_word.capitalize()} knelt beside {hero.pronoun('object')} and nodded. "
        f"\"Thank you for telling the truth first,\" {helper.pronoun()} said."
    )


def publish_art(world: World, helper: Entity, publish: PublishMethod, smudged: bool) -> None:
    art = world.get("art")
    art.meters["sleeved"] += 1
    art.meters["captured"] += 1
    if smudged:
        art.meters["repaired"] += 1
        world.say(
            f"{helper.label_word.capitalize()} laid a clean sheet over the picture, tapped away the loose dust, "
            f"and saved the best bright parts."
        )
    world.say(
        f"Then {helper.pronoun()} used {publish.phrase} and {publish.action}."
    )
    world.facts["published_line"] = publish.result
    propagate(world, narrate=True)


def ending(world: World, hero: Entity, friend: Entity, subject: Subject, smudged: bool) -> None:
    hero.memes["lesson"] += 1
    if smudged:
        world.say(
            f"By afternoon, the published picture still showed {subject.noun}, though now the tail looked extra swishy. "
            f"{friend.id} said it was funnier that way, and {hero.id} finally laughed too."
        )
    else:
        world.say(
            f"By afternoon, the published picture of {subject.detail} glowed on the board as neatly as a little flag."
        )
    world.say(
        f'{hero.id} learned that curiosity was not the problem. The trick was to let curiosity hold hands with honesty and asking.'
    )


def tell(
    setting: Setting,
    subject: Subject,
    temptation: Temptation,
    publish: PublishMethod,
    hero_name: str = "Mina",
    hero_gender: str = "girl",
    friend_name: str = "Ben",
    friend_gender: str = "boy",
    helper_type: str = "teacher",
    trait: str = "careful",
    hero_age: int = 5,
    friend_age: int = 6,
) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=setting.helper_label, role="helper"))
    art = world.add(
        Entity(
            id="art",
            kind="thing",
            type="picture",
            label="the picture",
            phrase=f"a pastel picture of {subject.detail}",
            owner="hero",
            tags=set(subject.tags) | {"pastel", "publish"},
        )
    )
    world.add(Entity(id="temptation", kind="thing", type="machine", label=temptation.label, phrase=temptation.phrase, touches_art=temptation.touches_art))
    world.add(Entity(id="publish", kind="thing", type="tool", label=publish.label, phrase=publish.phrase, safe_for_pastel=publish.safe_for_pastel))
    world.add(Entity(id="room", kind="thing", type="room", label=setting.place))
    hero.attrs.update({"age": hero_age, "trait": trait})
    friend.attrs.update({"age": friend_age})

    introduce(world, hero, friend, subject)
    announce_board(world, hero)
    world.para()
    inner_monologue(world, hero, subject)
    notice_machine(world, hero, temptation)
    warning(world, friend, temptation)
    world.para()

    ask_first = would_ask_first(friend_age=friend_age, hero_age=hero_age, trait=trait)
    if ask_first:
        back_down(world, hero, friend, helper, publish)
        smudged = False
        outcome = "asked_first"
    else:
        sneak(world, hero, temptation)
        world.para()
        confess(world, hero, helper)
        publish_art(world, helper, publish, smudged=True)
        smudged = True
        outcome = "smudged_then_fixed"

    world.para()
    ending(world, hero, friend, subject, smudged=smudged)
    world.facts.update(
        hero=hero,
        friend=friend,
        helper=helper,
        art=art,
        subject=subject,
        temptation_cfg=temptation,
        publish_cfg=publish,
        trait=trait,
        hero_age=hero_age,
        friend_age=friend_age,
        smudged=smudged,
        outcome=outcome,
    )
    return world


KNOWLEDGE = {
    "pastel": [
        (
            "What is pastel?",
            "Pastel is a soft art stick made of powder and color. It makes rich color, but it can rub off if you touch it too much.",
        )
    ],
    "publish": [
        (
            "What does publish mean?",
            "To publish something means to share it so other people can see or read it. A class board, a little paper, or a wall display can all publish work.",
        )
    ],
    "copier": [
        (
            "Why can a copier be hard on pastel art?",
            "A copier often pulls paper with rollers. If pastel dust is loose on top, the rollers can smear the colors.",
        )
    ],
    "scanner": [
        (
            "What does a scanner do?",
            "A scanner makes a careful copy of a picture without rubbing all over it. That can be safer for delicate art.",
        )
    ],
    "camera": [
        (
            "Why might a camera stand help publish art?",
            "A camera can take a picture of the artwork from above. That lets people share the art without squashing the dusty surface.",
        )
    ],
    "honesty": [
        (
            "Why is honesty important after a mistake?",
            "Honesty helps other people fix the real problem. Telling the truth quickly is often braver than hiding what happened.",
        )
    ],
    "curiosity": [
        (
            "Is curiosity good or bad?",
            "Curiosity is good when it helps you learn. It needs careful questions and safe choices so it does not turn into a risky shortcut.",
        )
    ],
}
KNOWLEDGE_ORDER = ["pastel", "publish", "copier", "scanner", "camera", "honesty", "curiosity"]


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="the classroom",
        board_name="the Bright Board",
        affords={"copier", "scanner", "camera_stand"},
        helper_type="teacher",
        helper_label="the teacher",
    ),
    "library": Setting(
        id="library",
        place="the library corner",
        board_name="the Reading Wall",
        affords={"copier", "scanner"},
        helper_type="librarian",
        helper_label="the librarian",
    ),
    "art_room": Setting(
        id="art_room",
        place="the art room",
        board_name="the Silly Gallery Sheet",
        affords={"copier", "camera_stand"},
        helper_type="teacher",
        helper_label="the art teacher",
    ),
}

SUBJECTS = {
    "dragon": Subject(id="dragon", noun="dragon", detail="a dragon wearing rain boots", tags={"curiosity"}),
    "cupcake": Subject(id="cupcake", noun="cupcake", detail="a cupcake with a surprised face", tags={"curiosity"}),
    "whale": Subject(id="whale", noun="whale", detail="a whale balancing a teacup", tags={"curiosity"}),
    "robot": Subject(id="robot", noun="robot", detail="a robot holding a flower", tags={"curiosity"}),
}

TEMPTATIONS = {
    "copier": Temptation(
        id="copier",
        label="copier",
        phrase="the humming copier",
        machine_noise="hummed and clicked",
        touch_verb="swallow the paper for one smart second",
        warning="That machine pulls paper with grippy rollers",
        touches_art=True,
        tags={"copier"},
    ),
    "stamp_press": Temptation(
        id="stamp_press",
        label="stamp press",
        phrase="the clunky stamp press",
        machine_noise="clunked like a giant metal frog",
        touch_verb="squash the paper and make it look official",
        warning="That press pushes hard on top of things",
        touches_art=True,
        tags={"copier"},
    ),
}

PUBLISH_METHODS = {
    "scanner": PublishMethod(
        id="scanner",
        label="scanner",
        phrase="the flat scanner",
        action="made a clean copy for the board",
        result="A crisp copy of the pastel picture went up on the board, while the real drawing rested safely on a shelf.",
        safe_for_pastel=True,
        tags={"scanner", "publish"},
    ),
    "camera_stand": PublishMethod(
        id="camera_stand",
        label="camera stand",
        phrase="the little camera stand",
        action="snapped a careful photo for the board",
        result="A bright photo of the pastel picture fluttered onto the board, and everyone could see every silly color.",
        safe_for_pastel=True,
        tags={"camera", "publish"},
    ),
}


@dataclass
class StoryParams:
    place: str
    subject: str
    temptation: str
    publish: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    trait: str
    helper_type: str
    hero_age: int
    friend_age: int
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="classroom",
        subject="dragon",
        temptation="copier",
        publish="scanner",
        hero_name="Mina",
        hero_gender="girl",
        friend_name="Ollie",
        friend_gender="boy",
        trait="careful",
        helper_type="teacher",
        hero_age=5,
        friend_age=6,
    ),
    StoryParams(
        place="library",
        subject="cupcake",
        temptation="copier",
        publish="scanner",
        hero_name="Ben",
        hero_gender="boy",
        friend_name="Lila",
        friend_gender="girl",
        trait="curious",
        helper_type="librarian",
        hero_age=6,
        friend_age=5,
    ),
    StoryParams(
        place="art_room",
        subject="whale",
        temptation="stamp_press",
        publish="camera_stand",
        hero_name="Ava",
        hero_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        trait="patient",
        helper_type="teacher",
        hero_age=5,
        friend_age=5,
    ),
]

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tess", "Poppy", "June", "Ivy", "Ruby"]
BOY_NAMES = ["Ben", "Max", "Ollie", "Leo", "Finn", "Theo", "Sam", "Milo"]
TRAITS = ["careful", "patient", "thoughtful", "curious", "bouncy", "bold"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    subject = f["subject"]
    temptation = f["temptation_cfg"]
    publish = f["publish_cfg"]
    outcome = f["outcome"]
    if outcome == "asked_first":
        return [
            f'Write a funny story for a 3-to-5-year-old that includes the words "pastel" and "publish". '
            f'The main child is curious about a machine but asks for help before using it.',
            f"Tell a gentle comedy where {hero.label} makes a pastel picture of {subject.detail}, wants to publish it, "
            f"and learns that asking first is smarter than taking a shortcut.",
            f"Write a child-facing story with inner monologue, curiosity, and a moral value about honesty and patience, "
            f"ending with {publish.label} helping the picture get published safely.",
        ]
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the words "pastel" and "publish". '
        f'A curious child tries {temptation.label} too soon, tells the truth, and a grown-up helps fix the problem.',
        f"Tell a comedy where {hero.label} wants to publish a pastel picture fast, makes a small smudgy mistake, "
        f"and learns that honesty helps more than hiding.",
        f"Write a simple story with inner monologue, curiosity, and a clear moral value: after a silly shortcut, "
        f"the child confesses and the picture is still shared in a safe way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    subject = f["subject"]
    temptation = f["temptation_cfg"]
    publish = f["publish_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who made a pastel picture of {subject.detail}, plus {friend.label} and {helper.label_word} who helped at the important moment.",
        ),
        (
            "Why did the child want to publish the picture?",
            f"{hero.label} felt proud of the pastel picture and wanted other people to see it on {world.setting.board_name}. The wish to share it made the shortcut look tempting.",
        ),
        (
            "What was the child thinking inside?",
            f"{hero.label} kept thinking about publishing the picture quickly and wondered if the machine could do it faster. Those inner thoughts show curiosity pushing the story forward.",
        ),
    ]
    if f["outcome"] == "asked_first":
        qa.append(
            (
                f"Why did {hero.label} stop before using the {temptation.label}?",
                f"{hero.label} listened instead of rushing. {friend.label}'s warning or {hero.pronoun('possessive')} own careful side made asking feel wiser than guessing.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The picture was published safely with the {publish.label}, and nothing got smeared. The ending proves that patient curiosity can still lead to something bright and funny.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.label} tried the {temptation.label}?",
                f"The pastel picture got smudged because the machine touched the dusty surface too roughly. A little cloud of color even landed on {hero.pronoun('possessive')} nose, which made the mistake feel funny and real.",
            )
        )
        qa.append(
            (
                f"Why was telling the truth important?",
                f"{hero.label} confessed right away, so {helper.label_word} could help save the picture. Honesty turned a bad shortcut into a fixable problem.",
            )
        )
        qa.append(
            (
                "How did the picture get published in the end?",
                f"{helper.label_word.capitalize()} used the {publish.label} to share the picture safely. Even after the smudge, the child still got to publish the art in a better way.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"pastel", "publish", "honesty", "curiosity"}
    tags |= set(world.facts["temptation_cfg"].tags)
    tags |= set(world.facts["publish_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.touches_art:
            bits.append("touches_art=True")
        if ent.safe_for_pastel:
            bits.append("safe_for_pastel=True")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: str, temptation: str, publish: str) -> str:
    if place not in SETTINGS:
        return "(No story: unknown place.)"
    setting = SETTINGS[place]
    if temptation not in setting.affords:
        return f"(No story: {setting.place} does not have a {temptation} for the child to fuss over.)"
    if publish not in setting.affords:
        return f"(No story: {setting.place} does not offer {publish} as the safe publishing method.)"
    if temptation == publish:
        return "(No story: the tempting shortcut and the safe publishing method cannot be the same tool, or there is no real turn in the story.)"
    return "(No story: this combination is not a reasonable pastel publishing setup.)"


ASP_RULES = r"""
tempting(Place, T) :- affords(Place, T), temptation(T), touches_art(T).
safe_publish(Place, P) :- affords(Place, P), publish_method(P), safe_for_pastel(P).
valid(Place, T, P) :- tempting(Place, T), safe_publish(Place, P), T != P.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for item in sorted(setting.affords):
            lines.append(asp.fact("affords", place, item))
    for temptation, cfg in TEMPTATIONS.items():
        lines.append(asp.fact("temptation", temptation))
        if cfg.touches_art:
            lines.append(asp.fact("touches_art", temptation))
    for publish, cfg in PUBLISH_METHODS.items():
        lines.append(asp.fact("publish_method", publish))
        if cfg.safe_for_pastel:
            lines.append(asp.fact("safe_for_pastel", publish))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    parser = build_parser()
    for seed in range(10):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            smoke_cases.append(params)
        except StoryError:
            rc = 1
            print(f"ERROR: resolve_params failed unexpectedly for seed {seed}.")
            break

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if "pastel" not in sample.story.lower() or "publish" not in sample.story.lower():
                raise StoryError("required seed words missing from rendered story")
        except Exception as err:
            rc = 1
            print(f"ERROR: story generation smoke test failed for {params}: {err}")
            break

    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child wants to publish a pastel picture and learns to pair curiosity with honesty."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--subject", choices=SUBJECTS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--publish", choices=PUBLISH_METHODS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.temptation and args.publish and not valid_combo(args.place, args.temptation, args.publish):
        raise StoryError(explain_rejection(args.place, args.temptation, args.publish))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.temptation is None or combo[1] == args.temptation)
        and (args.publish is None or combo[2] == args.publish)
    ]
    if not combos:
        chosen_place = args.place or next(iter(SETTINGS))
        chosen_temptation = args.temptation or next(iter(TEMPTATIONS))
        chosen_publish = args.publish or next(iter(PUBLISH_METHODS))
        raise StoryError(explain_rejection(chosen_place, chosen_temptation, chosen_publish))

    place, temptation, publish = rng.choice(sorted(combos))
    subject = args.subject or rng.choice(sorted(SUBJECTS))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or pick_name(rng, hero_gender)
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    friend_name = args.friend_name or pick_name(rng, friend_gender, avoid=hero_name)
    trait = rng.choice(TRAITS)
    hero_age, friend_age = rng.sample([4, 5, 6, 7], 2)
    helper_type = SETTINGS[place].helper_type
    return StoryParams(
        place=place,
        subject=subject,
        temptation=temptation,
        publish=publish,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        trait=trait,
        helper_type=helper_type,
        hero_age=hero_age,
        friend_age=friend_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.subject not in SUBJECTS:
        raise StoryError(f"(No story: unknown subject '{params.subject}'.)")
    if params.temptation not in TEMPTATIONS:
        raise StoryError(f"(No story: unknown temptation '{params.temptation}'.)")
    if params.publish not in PUBLISH_METHODS:
        raise StoryError(f"(No story: unknown publish method '{params.publish}'.)")
    if not valid_combo(params.place, params.temptation, params.publish):
        raise StoryError(explain_rejection(params.place, params.temptation, params.publish))

    world = tell(
        setting=SETTINGS[params.place],
        subject=SUBJECTS[params.subject],
        temptation=TEMPTATIONS[params.temptation],
        publish=PUBLISH_METHODS[params.publish],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        helper_type=params.helper_type,
        trait=params.trait,
        hero_age=params.hero_age,
        friend_age=params.friend_age,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, temptation, publish) combos:\n")
        for place, temptation, publish in combos:
            print(f"  {place:10} {temptation:12} {publish}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.subject} at {p.place} ({p.temptation} -> {p.publish})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
