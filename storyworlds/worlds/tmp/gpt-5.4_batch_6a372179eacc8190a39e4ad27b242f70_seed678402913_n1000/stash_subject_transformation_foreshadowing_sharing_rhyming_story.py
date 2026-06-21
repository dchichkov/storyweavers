#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stash_subject_transformation_foreshadowing_sharing_rhyming_story.py
================================================================================================

A standalone storyworld about a child with a secret stash for a favorite
school subject. The child first hides the stash, a gentle hint foreshadows what
those little pieces could become, and sharing turns the lesson into a bright
group creation.

The prose aims for a light rhyming-story feel while still being driven by a
small simulated world: characters carry emotional memes, objects carry physical
meters, and simple causal rules decide when the board feels unfinished, when a
child feels left out, and when the shared pieces transform into a finished
classroom picture.

Run it
------
    python storyworlds/worlds/gpt-5.4/stash_subject_transformation_foreshadowing_sharing_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/stash_subject_transformation_foreshadowing_sharing_rhyming_story.py --subject science
    python storyworlds/worlds/gpt-5.4/stash_subject_transformation_foreshadowing_sharing_rhyming_story.py --stash shell_tiles
    python storyworlds/worlds/gpt-5.4/stash_subject_transformation_foreshadowing_sharing_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/stash_subject_transformation_foreshadowing_sharing_rhyming_story.py --verify
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
OPENHEARTED_TRAITS = {"kind", "sunny", "generous"}


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
        female = {"girl", "mother", "mom", "woman", "teacher_f"}
        male = {"boy", "father", "dad", "man", "teacher_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        if self.role == "teacher":
            return "teacher"
        return self.label or self.type


@dataclass
class SubjectTheme:
    id: str
    label: str
    room: str
    board_name: str
    hint: str
    result_phrase: str
    cheer: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StashKind:
    id: str
    label: str
    phrase: str
    unit: str
    plural_noun: str
    hide_place: str
    color: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    label: str
    phrase: str
    motion: str
    reveal: str
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


def _r_unfinished_board(world: World) -> list[str]:
    board = world.get("board")
    stash = world.get("stash")
    friend = world.get("friend")
    if board.meters["need"] < THRESHOLD or stash.meters["hidden"] < THRESHOLD:
        return []
    sig = ("unfinished",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    board.meters["plain"] += 1
    friend.memes["left_out"] += 1
    return ["__unfinished__"]


def _r_shared_help(world: World) -> list[str]:
    stash = world.get("stash")
    board = world.get("board")
    hero = world.get("hero")
    friend = world.get("friend")
    if stash.meters["shared"] < THRESHOLD or board.meters["need"] < THRESHOLD:
        return []
    sig = ("shared_help",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    board.meters["complete"] += 1
    board.meters["need"] = 0.0
    friend.memes["left_out"] = 0.0
    friend.memes["relief"] += 1
    hero.memes["generosity"] += 1
    return ["__shared__"]


def _r_transform(world: World) -> list[str]:
    board = world.get("board")
    display = world.get("display")
    hero = world.get("hero")
    friend = world.get("friend")
    if board.meters["complete"] < THRESHOLD:
        return []
    sig = ("transform",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    display.meters["transformed"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    return ["__transform__"]


CAUSAL_RULES = [
    Rule(name="unfinished_board", tag="social", apply=_r_unfinished_board),
    Rule(name="shared_help", tag="social", apply=_r_shared_help),
    Rule(name="transform", tag="physical", apply=_r_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for item in produced:
            if item.startswith("__"):
                continue
            world.say(item)
    return produced


SUBJECTS = {
    "science": SubjectTheme(
        id="science",
        label="science",
        room="the science corner",
        board_name="life-cycle board",
        hint="Tiny things can change in a surprising way when patient hands work together.",
        result_phrase="a bright butterfly garden",
        cheer="Science can shimmer and grow!",
        tags={"science", "sharing"},
    ),
    "reading": SubjectTheme(
        id="reading",
        label="reading",
        room="the reading rug",
        board_name="rhyme wall",
        hint="Little words may look small, but side by side they can sing.",
        result_phrase="a winding rhyme vine",
        cheer="Reading can ring and sing!",
        tags={"reading", "sharing", "rhyme"},
    ),
    "music": SubjectTheme(
        id="music",
        label="music",
        room="the music carpet",
        board_name="song board",
        hint="Single notes are quiet dots, but together they can dance.",
        result_phrase="a soaring song kite",
        cheer="Music can skip on the air!",
        tags={"music", "sharing"},
    ),
}

STASHES = {
    "seed_stars": StashKind(
        id="seed_stars",
        label="seed stars",
        phrase="a stash of tiny seed stars",
        unit="seed star",
        plural_noun="seed stars",
        hide_place="inside the front pocket of the desk",
        color="green and gold",
        tags={"science", "small", "stash"},
    ),
    "word_cards": StashKind(
        id="word_cards",
        label="word cards",
        phrase="a stash of little word cards",
        unit="word card",
        plural_noun="word cards",
        hide_place="under a blue notebook",
        color="cream and cherry-red",
        tags={"reading", "small", "stash", "rhyme"},
    ),
    "shell_tiles": StashKind(
        id="shell_tiles",
        label="shell tiles",
        phrase="a stash of shiny shell tiles",
        unit="shell tile",
        plural_noun="shell tiles",
        hide_place="in a round tin by the crayons",
        color="silver and sky-blue",
        tags={"science", "music", "stash", "shiny"},
    ),
    "note_ribbons": StashKind(
        id="note_ribbons",
        label="note ribbons",
        phrase="a stash of curling note ribbons",
        unit="note ribbon",
        plural_noun="note ribbons",
        hide_place="in a paper folder with bent corners",
        color="violet and gold",
        tags={"music", "stash", "shiny"},
    ),
}

TRANSFORMS = {
    "butterfly_garden": Transformation(
        id="butterfly_garden",
        label="butterfly garden",
        phrase="a butterfly garden",
        motion="seemed to flutter on the board",
        reveal="the little shapes no longer looked like scraps at all",
        tags={"science", "transformation"},
    ),
    "rhyme_vine": Transformation(
        id="rhyme_vine",
        label="rhyme vine",
        phrase="a rhyme vine",
        motion="curled from word to word like a green singing trail",
        reveal="the cards no longer looked lonely once their sounds held hands",
        tags={"reading", "transformation", "rhyme"},
    ),
    "song_kite": Transformation(
        id="song_kite",
        label="song kite",
        phrase="a song kite",
        motion="looked ready to lift and hum above the room",
        reveal="the pieces no longer looked flat once the tune-shape was clear",
        tags={"music", "transformation"},
    ),
    "ocean_mural": Transformation(
        id="ocean_mural",
        label="ocean mural",
        phrase="an ocean mural",
        motion="shimmered like a small tide under the lights",
        reveal="the shiny tiles no longer looked scattered once they became waves",
        tags={"science", "music", "transformation"},
    ),
}

SUPPORTS = {
    ("seed_stars", "science"),
    ("word_cards", "reading"),
    ("shell_tiles", "science"),
    ("shell_tiles", "music"),
    ("note_ribbons", "music"),
}

FITS = {
    ("butterfly_garden", "science"),
    ("rhyme_vine", "reading"),
    ("song_kite", "music"),
    ("ocean_mural", "science"),
    ("ocean_mural", "music"),
}

WORKS = {
    ("seed_stars", "butterfly_garden"),
    ("word_cards", "rhyme_vine"),
    ("shell_tiles", "ocean_mural"),
    ("note_ribbons", "song_kite"),
    ("shell_tiles", "song_kite"),
}

GIRL_NAMES = ["Lila", "Mina", "Poppy", "Nora", "Tessa", "Ivy", "Mara", "Elsie"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Jasper", "Evan", "Noel", "Rory", "Finn"]
TRAITS = ["kind", "careful", "shy", "sunny", "thoughtful", "generous"]
TEACHERS = [
    ("Ms. Wren", "teacher_f"),
    ("Mr. Reed", "teacher_m"),
]


@dataclass
class StoryParams:
    subject: str
    stash: str
    transformation: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    teacher_name: str
    teacher_gender: str
    trait: str
    seatmate: bool
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        subject="science",
        stash="seed_stars",
        transformation="butterfly_garden",
        hero_name="Lila",
        hero_gender="girl",
        friend_name="Owen",
        friend_gender="boy",
        teacher_name="Ms. Wren",
        teacher_gender="teacher_f",
        trait="kind",
        seatmate=True,
    ),
    StoryParams(
        subject="reading",
        stash="word_cards",
        transformation="rhyme_vine",
        hero_name="Milo",
        hero_gender="boy",
        friend_name="Poppy",
        friend_gender="girl",
        teacher_name="Mr. Reed",
        teacher_gender="teacher_m",
        trait="shy",
        seatmate=False,
    ),
    StoryParams(
        subject="music",
        stash="note_ribbons",
        transformation="song_kite",
        hero_name="Nora",
        hero_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        teacher_name="Ms. Wren",
        teacher_gender="teacher_f",
        trait="sunny",
        seatmate=True,
    ),
    StoryParams(
        subject="science",
        stash="shell_tiles",
        transformation="ocean_mural",
        hero_name="Finn",
        hero_gender="boy",
        friend_name="Ivy",
        friend_gender="girl",
        teacher_name="Mr. Reed",
        teacher_gender="teacher_m",
        trait="thoughtful",
        seatmate=False,
    ),
]


def valid_combo(subject: str, stash: str, transformation: str) -> bool:
    return (
        (stash, subject) in SUPPORTS
        and (transformation, subject) in FITS
        and (stash, transformation) in WORKS
    )


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for subject in SUBJECTS:
        for stash in STASHES:
            for transformation in TRANSFORMS:
                if valid_combo(subject, stash, transformation):
                    out.append((subject, stash, transformation))
    return out


def outcome_of(params: StoryParams) -> str:
    if params.trait in OPENHEARTED_TRAITS:
        return "early_share"
    if params.seatmate and params.trait != "shy":
        return "early_share"
    return "late_share"


def explain_rejection(subject: str, stash: str, transformation: str) -> str:
    if (stash, subject) not in SUPPORTS:
        return (
            f"(No story: {STASHES[stash].label} do not fit the {SUBJECTS[subject].label} "
            f"subject here, so the stash would feel random instead of part of the lesson.)"
        )
    if (transformation, subject) not in FITS:
        return (
            f"(No story: {TRANSFORMS[transformation].phrase} does not belong to the "
            f"{SUBJECTS[subject].label} lesson, so the ending would not feel earned.)"
        )
    return (
        f"(No story: {STASHES[stash].label} do not reasonably turn into "
        f"{TRANSFORMS[transformation].phrase} in this world.)"
    )


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def introduce(world: World, hero: Entity, subject: SubjectTheme) -> None:
    world.say(
        f"In {subject.room}, where soft pages swished and bright pencils brushed, "
        f"{hero.id} loved {subject.label} very much."
    )


def reveal_stash(world: World, hero: Entity, stash: StashKind) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} had {stash.phrase}, {stash.color} and small, tucked {stash.hide_place}. "
        f'"My secret stash for the {subject_word(world)} class," thought {hero.pronoun()}. '
        f'"I will keep every last little bit, every trim and every tidbit."'
    )


def teacher_hint(world: World, teacher: Entity, subject: SubjectTheme) -> None:
    world.get("board").meters["need"] += 1
    world.facts["hint_spoken"] = True
    world.say(
        f'That morning, {teacher.id} tapped the blank {subject.board_name} and said, '
        f'"{subject.hint}"'
    )


def subject_word(world: World) -> str:
    return world.facts["subject_cfg"].label


def ask_for_help(world: World, teacher: Entity, friend: Entity, subject: SubjectTheme) -> None:
    friend.memes["hope"] += 1
    world.say(
        f'When work time began, {teacher.id} smiled at {friend.id}. '
        f'"We are one piece short for our {subject.board_name}," {teacher.pronoun()} said. '
        f'"Could someone share a bit so our {subject.label} picture may glow and fit?"'
    )


def hide_stash(world: World, hero: Entity, stash: StashKind) -> None:
    world.get("stash").meters["hidden"] += 1
    hero.memes["guarded"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} felt the little {stash.plural_noun} rustle in the desk and kept a quiet face. "
        f"{hero.pronoun().capitalize()} folded {hero.pronoun('possessive')} hands and let the secret stay in place."
    )


def early_share(world: World, hero: Entity, friend: Entity, stash: StashKind) -> None:
    world.get("stash").meters["shared"] += 1
    world.facts["share_moment"] = "early"
    hero.memes["brave"] += 1
    world.say(
        f"But {hero.id}'s kind heart gave a thump-thump beat. "
        f'"I have some in my stash," {hero.pronoun()} said. "Please take what you need to make it sweet."'
    )
    world.say(
        f"{hero.id} slid two {stash.plural_noun} across the table to {friend.id}, "
        f"and the small kind act felt warm instead of little."
    )
    propagate(world, narrate=False)


def late_share_setup(world: World, hero: Entity, friend: Entity, subject: SubjectTheme) -> None:
    friend_left = world.get("friend").memes["left_out"] >= THRESHOLD
    if friend_left:
        world.say(
            f"{friend.id} looked at the plain board, then at {hero.id}, and gave a small sigh. "
            f"The room was not cross, only quiet, and quiet can ring louder than a bell."
        )
    world.say(
        f"Then {hero.id} remembered the {subject.label} hint from before. "
        f"Little things could change when patient hands worked together; the thought came back for more."
    )


def late_share(world: World, hero: Entity, friend: Entity, stash: StashKind) -> None:
    world.get("stash").meters["shared"] += 1
    world.facts["share_moment"] = "late"
    hero.memes["brave"] += 1
    world.say(
        f'"Wait," said {hero.id}. "My stash should not stay hid away. '
        f'It can help our picture bloom today."'
    )
    world.say(
        f"{hero.pronoun().capitalize()} opened the desk, drew out the {stash.plural_noun}, "
        f"and set them in {friend.id}'s hands with a soft and shining grin."
    )
    propagate(world, narrate=False)


def transformation_scene(
    world: World,
    hero: Entity,
    friend: Entity,
    teacher: Entity,
    subject: SubjectTheme,
    stash: StashKind,
    transformation: Transformation,
) -> None:
    display = world.get("display")
    if display.meters["transformed"] < THRESHOLD:
        raise StoryError("(Internal story error: transformation did not occur.)")
    world.say(
        f"Together they placed each {stash.unit} where it belonged, and the board changed as they worked along. "
        f"Soon it became {subject.result_phrase} -- {transformation.motion}."
    )
    world.say(
        f"{transformation.reveal}, and even the air felt bright and new. "
        f'{teacher.id} clapped once and said, "{subject.cheer}"'
    )
    world.say(
        f"{friend.id} beamed at {hero.id}. "
        f'"Your stash did more when we could share."'
    )


def ending(world: World, hero: Entity, friend: Entity, stash: StashKind) -> None:
    hero.memes["lesson"] += 1
    friend.memes["gratitude"] += 1
    world.say(
        f"{hero.id} laughed a little and did not hide the tin again. "
        f"{hero.pronoun().capitalize()} learned that a secret stash can look small when kept alone, "
        f"but shared with a friend it can sparkle like a song fully grown."
    )
    world.say(
        f"Side by side, {hero.id} and {friend.id} admired the wall before the bell, "
        f"and the class glowed kindly around them as the bright new picture shone so well."
    )


def tell(
    subject: SubjectTheme,
    stash_cfg: StashKind,
    transformation: Transformation,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    teacher_name: str,
    teacher_gender: str,
    trait: str,
    seatmate: bool,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            traits=[trait],
            attrs={"seatmate": seatmate},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            label=friend_name,
            role="friend",
            attrs={"seatmate": seatmate},
        )
    )
    teacher = world.add(
        Entity(
            id=teacher_name,
            kind="character",
            type=teacher_gender,
            label=teacher_name,
            role="teacher",
        )
    )
    stash = world.add(
        Entity(
            id="stash",
            type="stash",
            label=stash_cfg.label,
            phrase=stash_cfg.phrase,
            tags=set(stash_cfg.tags),
        )
    )
    board = world.add(
        Entity(
            id="board",
            type="board",
            label=subject.board_name,
            tags=set(subject.tags),
        )
    )
    display = world.add(
        Entity(
            id="display",
            type="display",
            label=transformation.label,
            tags=set(transformation.tags),
        )
    )
    world.facts.update(
        subject_cfg=subject,
        stash_cfg=stash_cfg,
        transformation_cfg=transformation,
        hero=hero,
        friend=friend,
        teacher=teacher,
        seatmate=seatmate,
        trait=trait,
        outcome=outcome_of(
            StoryParams(
                subject=subject.id,
                stash=stash_cfg.id,
                transformation=transformation.id,
                hero_name=hero_name,
                hero_gender=hero_gender,
                friend_name=friend_name,
                friend_gender=friend_gender,
                teacher_name=teacher_name,
                teacher_gender=teacher_gender,
                trait=trait,
                seatmate=seatmate,
            )
        ),
    )

    introduce(world, hero, subject)
    reveal_stash(world, hero, stash_cfg)

    world.para()
    teacher_hint(world, teacher, subject)
    ask_for_help(world, teacher, friend, subject)
    hide_stash(world, hero, stash_cfg)

    world.para()
    if world.facts["outcome"] == "early_share":
        early_share(world, hero, friend, stash_cfg)
    else:
        late_share_setup(world, hero, friend, subject)
        late_share(world, hero, friend, stash_cfg)

    world.para()
    transformation_scene(world, hero, friend, teacher, subject, stash_cfg, transformation)
    ending(world, hero, friend, stash_cfg)

    world.facts.update(
        share_moment=world.facts.get("share_moment", "early"),
        board_complete=world.get("board").meters["complete"] >= THRESHOLD,
        transformed=world.get("display").meters["transformed"] >= THRESHOLD,
        friend_left_out_before=friend.memes["gratitude"] >= THRESHOLD or ("unfinished",) in world.fired,
    )
    return world


KNOWLEDGE = {
    "science": [
        (
            "What is science class about?",
            "Science class is where children notice how things work and change. They might learn about plants, animals, weather, or light.",
        )
    ],
    "reading": [
        (
            "What is reading class for?",
            "Reading class helps children look at words, sounds, and stories. It teaches them how words work together to make meaning.",
        )
    ],
    "music": [
        (
            "What happens in music class?",
            "In music class, children listen, sing, clap, and learn about rhythm and notes. Small sounds can join to make a big tune.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words end with the same or almost the same sound, like cat and hat. Rhymes can make language feel playful and easy to remember.",
        )
    ],
    "sharing": [
        (
            "Why is sharing helpful in a classroom?",
            "Sharing lets everyone join in when something is needed. A small thing from one child can help the whole group finish together.",
        )
    ],
    "transformation": [
        (
            "What does transformation mean?",
            "Transformation means something changes into a new form or feels very different from before. A pile of little pieces can transform into one big picture.",
        )
    ],
    "stash": [
        (
            "What is a stash?",
            "A stash is a small hidden collection that someone keeps tucked away. It can be useful, but keeping it secret may stop others from using it.",
        )
    ],
}
KNOWLEDGE_ORDER = ["stash", "science", "reading", "music", "rhyme", "sharing", "transformation"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    subject = f["subject_cfg"]
    stash = f["stash_cfg"]
    transformation = f["transformation_cfg"]
    when = "right away" if f["share_moment"] == "early" else "after first hiding the stash"
    return [
        f'Write a short rhyming story for a 3-to-5-year-old that includes the words "stash" and "subject".',
        f"Tell a classroom story where {hero.id} loves {subject.label} as a school subject, keeps {stash.phrase}, and then shares it {when}.",
        f"Write a gentle rhyming tale with foreshadowing, sharing, and transformation, ending when little pieces become {transformation.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    teacher = f["teacher"]
    subject = f["subject_cfg"]
    stash = f["stash_cfg"]
    transformation = f["transformation_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child who loved {subject.label} as a school subject, and {friend.id}, a classmate who needed help. {teacher.id} guided the class without scolding anyone.",
        ),
        (
            f"What was in {hero.id}'s stash?",
            f"{hero.id} had {stash.phrase} hidden away. The stash mattered because the class was missing exactly the sort of piece that could help finish the board.",
        ),
        (
            "What was the foreshadowing hint?",
            f"{teacher.id} said that small things could change in a surprising way when people worked together. That hint came true later when the little pieces became {transformation.phrase}.",
        ),
    ]
    if f["share_moment"] == "early":
        qa.append(
            (
                f"Why did {hero.id} share so quickly?",
                f"{hero.id} felt the pull to keep the stash secret, but a kinder feeling won right away. Because {hero.pronoun('subject')} spoke up early, {friend.id} did not stay left out for long.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {hero.id} wait before sharing?",
                f"{hero.id} first hid the stash because it felt special and hard to give away. Then the plain board and {friend.id}'s quiet sadness made {hero.pronoun('object')} remember the teacher's hint, so {hero.pronoun('subject')} chose to share.",
            )
        )
    qa.append(
        (
            "How did sharing change the story?",
            f"Sharing turned an unfinished classroom problem into a finished picture. The little pieces did more together than they could have done alone, so the board transformed and both children felt glad.",
        )
    )
    qa.append(
        (
            f"What did the pieces become at the end?",
            f"They became {subject.result_phrase}. That ending image shows the transformation clearly, because the tiny separate pieces no longer looked like an ordinary stash.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"stash", "sharing", "transformation", world.facts["subject_cfg"].id}
    tags |= set(world.facts["stash_cfg"].tags)
    tags |= set(world.facts["transformation_cfg"].tags)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v is False}
            bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Su, St, Tr) :- subject(Su), stash(St), transform(Tr),
                     supports(St, Su), fits(Tr, Su), works(St, Tr).

early_share :- trait(T), openhearted(T).
early_share :- seatmate(yes), trait(T), not shy_trait(T).

outcome(early_share) :- early_share.
outcome(late_share)  :- not early_share.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SUBJECTS:
        lines.append(asp.fact("subject", sid))
    for stid in STASHES:
        lines.append(asp.fact("stash", stid))
    for tid in TRANSFORMS:
        lines.append(asp.fact("transform", tid))
    for stash, subject in sorted(SUPPORTS):
        lines.append(asp.fact("supports", stash, subject))
    for transform, subject in sorted(FITS):
        lines.append(asp.fact("fits", transform, subject))
    for stash, transform in sorted(WORKS):
        lines.append(asp.fact("works", stash, transform))
    for trait in sorted(OPENHEARTED_TRAITS):
        lines.append(asp.fact("openhearted", trait))
    lines.append(asp.fact("shy_trait", "shy"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("trait", params.trait),
            asp.fact("seatmate", "yes" if params.seatmate else "no"),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: valid-combo gate matches ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = []
    for params in cases:
        a = asp_outcome(params)
        b = outcome_of(params)
        if a != b:
            bad.append((params, a, b))
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} outcome differences.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a classroom stash, a favorite subject, a shared transformation."
    )
    ap.add_argument("--subject", choices=SUBJECTS)
    ap.add_argument("--stash", choices=STASHES)
    ap.add_argument("--transformation", choices=TRANSFORMS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--seatmate", choices=["yes", "no"])
    ap.add_argument("--teacher", choices=["Ms. Wren", "Mr. Reed"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (subject, stash, transformation) combos")
    ap.add_argument("--verify", action="store_true", help="check inline ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.subject and args.stash and args.transformation:
        if not valid_combo(args.subject, args.stash, args.transformation):
            raise StoryError(explain_rejection(args.subject, args.stash, args.transformation))

    combos = [
        combo
        for combo in valid_combos()
        if (args.subject is None or combo[0] == args.subject)
        and (args.stash is None or combo[1] == args.stash)
        and (args.transformation is None or combo[2] == args.transformation)
    ]
    if not combos:
        if args.subject and args.stash and args.transformation:
            raise StoryError(explain_rejection(args.subject, args.stash, args.transformation))
        raise StoryError("(No valid combination matches the given options.)")

    subject, stash, transformation = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or pick_name(rng, hero_gender)
    friend_name = args.friend_name or pick_name(rng, friend_gender, avoid=hero_name)
    teacher_name = args.teacher or rng.choice([t[0] for t in TEACHERS])
    teacher_gender = dict(TEACHERS)[teacher_name]
    trait = args.trait or rng.choice(TRAITS)
    seatmate = {"yes": True, "no": False}.get(args.seatmate, rng.choice([True, False]))
    return StoryParams(
        subject=subject,
        stash=stash,
        transformation=transformation,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        teacher_name=teacher_name,
        teacher_gender=teacher_gender,
        trait=trait,
        seatmate=seatmate,
    )


def generate(params: StoryParams) -> StorySample:
    if params.subject not in SUBJECTS:
        raise StoryError(f"(Invalid subject: {params.subject})")
    if params.stash not in STASHES:
        raise StoryError(f"(Invalid stash: {params.stash})")
    if params.transformation not in TRANSFORMS:
        raise StoryError(f"(Invalid transformation: {params.transformation})")
    if not valid_combo(params.subject, params.stash, params.transformation):
        raise StoryError(explain_rejection(params.subject, params.stash, params.transformation))

    world = tell(
        subject=SUBJECTS[params.subject],
        stash_cfg=STASHES[params.stash],
        transformation=TRANSFORMS[params.transformation],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        teacher_name=params.teacher_name,
        teacher_gender=params.teacher_gender,
        trait=params.trait,
        seatmate=params.seatmate,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (subject, stash, transformation) combos:\n")
        for subject, stash, transformation in combos:
            print(f"  {subject:8} {stash:12} {transformation}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = (
                f"### {p.hero_name} and {p.friend_name}: {p.subject} / {p.stash} / "
                f"{p.transformation} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
