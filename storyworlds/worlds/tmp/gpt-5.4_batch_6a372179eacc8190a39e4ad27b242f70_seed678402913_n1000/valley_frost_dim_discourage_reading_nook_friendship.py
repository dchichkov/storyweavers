#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/valley_frost_dim_discourage_reading_nook_friendship.py
=================================================================================

A standalone story world about two friends in a reading nook on a winter day.
The nook is often frost-dim, one child can feel discouraged about reading aloud,
and the other friend helps in a funny, gentle way.

This world is built to satisfy a small, tight domain:

- setting: a reading nook
- required seed words woven naturally into the prose: valley, frost-dim, discourage
- features: Friendship, Flashback
- style: Comedy

The little simulation tracks physical state (light, props, pages) and emotional
state (confidence, embarrassment, relief, friendship), then renders prose from
that state instead of swapping nouns into a fixed paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/valley_frost_dim_discourage_reading_nook_friendship.py
    python storyworlds/worlds/gpt-5.4/valley_frost_dim_discourage_reading_nook_friendship.py --chapter valley --obstacle shy_flashback --helper puppet
    python storyworlds/worlds/gpt-5.4/valley_frost_dim_discourage_reading_nook_friendship.py --obstacle dim_text --helper puppet
    python storyworlds/worlds/gpt-5.4/valley_frost_dim_discourage_reading_nook_friendship.py --all
    python storyworlds/worlds/gpt-5.4/valley_frost_dim_discourage_reading_nook_friendship.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we need the storyworlds/
# directory itself on sys.path.
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Chapter:
    id: str
    title: str
    place_word: str
    picture: str
    funny_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    need: str
    title: str
    cue: str
    flashback: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    supports: set[str] = field(default_factory=set)
    move: str = ""
    ending: str = ""
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


def _r_dim_discourages(world: World) -> list[str]:
    out: list[str] = []
    room = world.entities.get("nook")
    reader = world.entities.get("reader")
    if room is None or reader is None:
        return out
    if room.meters["light"] >= THRESHOLD:
        return out
    if ("dim_discourages",) in world.fired:
        return out
    world.fired.add(("dim_discourages",))
    reader.memes["hesitation"] += 1
    out.append("__dim__")
    return out


def _r_support_helps(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("helper")
    reader = world.entities.get("reader")
    if helper is None or reader is None:
        return out
    if helper.meters["used"] < THRESHOLD:
        return out
    if ("support_helps",) in world.fired:
        return out
    world.fired.add(("support_helps",))
    reader.memes["confidence"] += 2
    reader.memes["hesitation"] = max(0.0, reader.memes["hesitation"] - 1.0)
    reader.memes["joy"] += 1
    helper.memes["friendship"] += 1
    out.append("__help__")
    return out


CAUSAL_RULES = [
    Rule(name="dim_discourages", tag="emotional", apply=_r_dim_discourages),
    Rule(name="support_helps", tag="emotional", apply=_r_support_helps),
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
        for s in produced:
            world.say(s)
    return produced


CHAPTERS = {
    "valley": Chapter(
        id="valley",
        title="The Tiny Valley Map",
        place_word="valley",
        picture="a tiny valley with blueberry bushes and a goat in a scarf",
        funny_word="velvet-valley",
        tags={"valley", "book"},
    ),
    "moon_stairs": Chapter(
        id="moon_stairs",
        title="The Moon Stairs",
        place_word="stairs",
        picture="silver stairs climbing past a sleepy owl",
        funny_word="moon-macaroni",
        tags={"book"},
    ),
    "pancake_castle": Chapter(
        id="pancake_castle",
        title="The Pancake Castle",
        place_word="castle",
        picture="a castle with syrup flags and a buttery moat",
        funny_word="pancakeapult",
        tags={"book"},
    ),
}

OBSTACLES = {
    "shy_flashback": Obstacle(
        id="shy_flashback",
        need="courage",
        title="a shy flashback",
        cue="The old memory came back at the exact wrong moment.",
        flashback="Last week, the tricky word wriggled away and came out as a very silly wrong word. Both children laughed then, but now the memory made the reader worry everyone would laugh again.",
        tags={"flashback", "confidence"},
    ),
    "dim_text": Obstacle(
        id="dim_text",
        need="light",
        title="dim text",
        cue="The letters looked sleepy in the weak light.",
        flashback="The reader remembered another winter afternoon when the words went fuzzy and a sentence had to be guessed. That memory made the page feel bigger and trickier than it really was.",
        tags={"flashback", "light"},
    ),
    "friend_blurt": Obstacle(
        id="friend_blurt",
        need="courage",
        title="a clumsy blurt",
        cue="The helper spoke too fast and nearly made things worse.",
        flashback="The reader remembered a school circle when someone had rushed them through a page. Nobody meant to discourage them, but the memory still pinched.",
        tags={"flashback", "confidence", "friendship"},
    ),
}

HELPERS = {
    "clip_lamp": Helper(
        id="clip_lamp",
        label="clip lamp",
        phrase="a little clip lamp shaped like a lemon",
        supports={"light"},
        move="clipped the lamp above the page until the words turned bright and sharp",
        ending="The lemon lamp made a sunny puddle on the blanket.",
        tags={"lamp", "light"},
    ),
    "puppet": Helper(
        id="puppet",
        label="sock puppet",
        phrase="a sock puppet with one button eye and one noodle eyebrow",
        supports={"courage"},
        move="popped up the sock puppet and gave it a pompous voice so silly that giggles chased the fear away",
        ending="The puppet ended up bowing so hard it tumbled into the cushion crack.",
        tags={"puppet", "courage"},
    ),
    "duet": Helper(
        id="duet",
        label="duet reading",
        phrase="a two-finger reading duet",
        supports={"courage", "light"},
        move="put one finger under each line and offered to read the hard bits together, turning the page into a team game",
        ending="Their two fingers marched down the page like tiny parade leaders.",
        tags={"duet", "courage", "light"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora", "Ruby", "Tessa"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Theo", "Eli"]
TRAITS = ["careful", "bouncy", "thoughtful", "curious", "cheerful", "dramatic"]


def valid_combo(chapter_id: str, obstacle_id: str, helper_id: str) -> bool:
    if chapter_id not in CHAPTERS or obstacle_id not in OBSTACLES or helper_id not in HELPERS:
        return False
    obstacle = OBSTACLES[obstacle_id]
    helper = HELPERS[helper_id]
    return obstacle.need in helper.supports


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for chapter_id in sorted(CHAPTERS):
        for obstacle_id in sorted(OBSTACLES):
            for helper_id in sorted(HELPERS):
                if valid_combo(chapter_id, obstacle_id, helper_id):
                    combos.append((chapter_id, obstacle_id, helper_id))
    return combos


@dataclass
class StoryParams:
    chapter: str
    obstacle: str
    helper: str
    reader_name: str
    reader_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    reader_trait: str
    friend_trait: str
    seed: Optional[int] = None


def explain_rejection(obstacle_id: str, helper_id: str) -> str:
    if obstacle_id not in OBSTACLES:
        return f"(No story: unknown obstacle '{obstacle_id}'.)"
    if helper_id not in HELPERS:
        return f"(No story: unknown helper '{helper_id}'.)"
    obstacle = OBSTACLES[obstacle_id]
    helper = HELPERS[helper_id]
    return (
        f"(No story: {helper.label} does not honestly solve {obstacle.title}. "
        f"The obstacle needs {obstacle.need}, but {helper.label} supports "
        f"{', '.join(sorted(helper.supports))}.)"
    )


def pair_label(reader: Entity, friend: Entity) -> str:
    if reader.type == "girl" and friend.type == "girl":
        return "two friends"
    if reader.type == "boy" and friend.type == "boy":
        return "two friends"
    return "two friends"


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def introduce(world: World, reader: Entity, friend: Entity, parent: Entity, chapter: Chapter) -> None:
    nook = world.get("nook")
    reader.memes["anticipation"] += 1
    friend.memes["anticipation"] += 1
    world.say(
        f"In the reading nook by the window, {reader.id} and {friend.id} tucked "
        f"themselves under one quilt while {parent.label_word} stacked library "
        f"books on the rug. Outside, the afternoon looked frost-dim, and the glass "
        f"made the world seem dusted with sugar."
    )
    world.say(
        f"On top of the pile lay {chapter.title}, with a picture of {chapter.picture}. "
        f'"Let\'s read the {chapter.place_word} part out loud," said {friend.id}.'
    )
    nook.meters["light"] = 0.0
    propagate(world, narrate=False)


def begin_reading(world: World, reader: Entity, chapter: Chapter) -> None:
    book = world.get("book")
    book.meters["open"] += 1
    reader.meters["holding_book"] += 1
    world.say(
        f"{reader.id} opened the book to the page with the {chapter.place_word}. "
        f"The blanket made a tent around the two friends, and for one warm second "
        f"the whole nook felt like a secret theater."
    )


def obstacle_beat(world: World, reader: Entity, friend: Entity, obstacle: Obstacle, chapter: Chapter) -> None:
    reader.memes["hesitation"] += 1
    world.say(obstacle.cue)
    if obstacle.id == "friend_blurt":
        friend.memes["oops"] += 1
        world.say(
            f'"Maybe skip the silly voice part," {friend.id} blurted. The words came '
            f"out too fast, and {friend.id} heard the problem at once. "
            f'"Oh no. I did not mean to discourage you," {friend.pronoun()} said.'
        )
    elif obstacle.id == "dim_text":
        world.say(
            f"{reader.id} squinted. The letters in the {chapter.place_word} chapter "
            f"looked as if they were hiding in tiny gray mittens."
        )
    else:
        world.say(
            f"{reader.id}'s mouth opened for the first line, then shut again with a "
            f"small squeak."
        )


def flashback(world: World, reader: Entity, obstacle: Obstacle, chapter: Chapter) -> None:
    reader.memes["embarrassment"] += 1
    world.say(
        f"For a blink, {reader.id} was not in the nook at all. {obstacle.flashback}"
    )
    world.say(
        f'Now the page waited with the word "{chapter.funny_word}," and {reader.id} '
        f"worried it might bounce wrong again."
    )


def apology_and_plan(world: World, friend: Entity, obstacle: Obstacle) -> None:
    friend.memes["care"] += 1
    if obstacle.id == "friend_blurt":
        world.say(
            f'{friend.id} pressed both hands to {friend.pronoun("possessive")} cheeks. '
            f'"I said that in the grumpiest way possible. Let me fix it."'
        )
    else:
        world.say(
            f'{friend.id} scooted closer until their shoulders bumped. '
            f'"We do not have to rush. We can make this easier together."'
        )


def use_helper(world: World, reader: Entity, friend: Entity, helper_cfg: Helper) -> None:
    helper = world.get("helper")
    helper.meters["used"] += 1
    if helper_cfg.id == "clip_lamp":
        world.get("nook").meters["light"] = 2.0
    world.say(
        f"Then {friend.id} {helper_cfg.move}."
    )
    propagate(world, narrate=False)


def successful_read(world: World, reader: Entity, friend: Entity, chapter: Chapter, helper_cfg: Helper) -> None:
    reader.meters["read_lines"] += 1
    reader.memes["confidence"] += 1
    reader.memes["relief"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{reader.id} tried again. This time the first line came out steady, then the next, "
        f"and soon the tiny {chapter.place_word} in the book sounded grand and ridiculous in "
        f"exactly the right way."
    )
    if helper_cfg.id == "puppet":
        world.say(
            f'The puppet gave the goat a mayor voice, then a pirate voice, then something that '
            f"sounded like a sneezy trumpet. {reader.id} laughed so hard that the hard word lost "
            f"all its teeth."
        )
    elif helper_cfg.id == "clip_lamp":
        world.say(
            f"The bright page stopped looking scary. Even the long twisty word sat still long "
            f"enough to be read properly."
        )
    else:
        world.say(
            f"Whenever a tricky bit appeared, the two friends read it together, which made the "
            f"sentence feel less like a wall and more like a bridge."
        )


def ending(world: World, reader: Entity, friend: Entity, parent: Entity, helper_cfg: Helper, chapter: Chapter) -> None:
    reader.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f'{parent.label_word.capitalize()} looked over from the rug and smiled. '
        f'"That nook sounds much braver now."'
    )
    world.say(
        f"{helper_cfg.ending} By the end of the page, {reader.id} was leaning forward instead "
        f"of shrinking back, and {friend.id} was grinning so hard the quilt kept slipping off "
        f"one shoulder."
    )
    world.say(
        f"They read all the way through the {chapter.place_word} scene together. The frost-dim "
        f"window stayed pale and wintry, but inside the nook the voices were warm, silly, and full "
        f"of friendship."
    )


def tell(
    chapter: Chapter,
    obstacle: Obstacle,
    helper_cfg: Helper,
    reader_name: str = "Lily",
    reader_gender: str = "girl",
    friend_name: str = "Tom",
    friend_gender: str = "boy",
    parent_type: str = "mother",
    reader_trait: str = "careful",
    friend_trait: str = "cheerful",
) -> World:
    world = World()
    reader = world.add(Entity(
        id=reader_name,
        kind="character",
        type=reader_gender,
        role="reader",
        traits=[reader_trait],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=[friend_trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    nook = world.add(Entity(
        id="nook",
        type="place",
        label="reading nook",
        phrase="the reading nook by the window",
        tags={"nook"},
    ))
    book = world.add(Entity(
        id="book",
        type="book",
        label="library book",
        phrase=chapter.title,
        tags=set(chapter.tags),
    ))
    helper = world.add(Entity(
        id="helper",
        type="helper",
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
        tags=set(helper_cfg.tags),
    ))

    introduce(world, reader, friend, parent, chapter)
    begin_reading(world, reader, chapter)

    world.para()
    obstacle_beat(world, reader, friend, obstacle, chapter)
    flashback(world, reader, obstacle, chapter)
    apology_and_plan(world, friend, obstacle)

    world.para()
    use_helper(world, reader, friend, helper_cfg)
    successful_read(world, reader, friend, chapter, helper_cfg)

    world.para()
    ending(world, reader, friend, parent, helper_cfg, chapter)

    world.facts.update(
        reader=reader,
        friend=friend,
        parent=parent,
        chapter=chapter,
        obstacle=obstacle,
        helper_cfg=helper_cfg,
        hesitation=reader.memes["hesitation"],
        confidence=reader.memes["confidence"],
        friendship=reader.memes["friendship"] + friend.memes["friendship"],
        recovered=reader.memes["confidence"] >= THRESHOLD,
        flashback_used=True,
    )
    return world


KNOWLEDGE = {
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a short look back at something that happened earlier. It helps readers understand why a character feels a certain way now."
        )
    ],
    "friendship": [
        (
            "What can a good friend do when someone feels discouraged?",
            "A good friend can notice the feeling, speak kindly, and help make the hard thing smaller. Friendship often means solving a problem together instead of pushing someone alone."
        )
    ],
    "light": [
        (
            "Why is it harder to read in dim light?",
            "Dim light makes letters harder to see clearly, so your eyes have to work more. Bright, steady light helps the words look sharper."
        )
    ],
    "lamp": [
        (
            "What does a reading lamp do?",
            "A reading lamp shines light right where the page is. That makes the words easier to see."
        )
    ],
    "puppet": [
        (
            "Why can a puppet make reading feel easier?",
            "A puppet can make reading feel like play instead of a test. When children laugh, their bodies often relax and the words feel less scary."
        )
    ],
    "duet": [
        (
            "What is duet reading?",
            "Duet reading means two people read together or take turns closely. It can help a nervous reader feel supported."
        )
    ],
    "book": [
        (
            "What is a reading nook?",
            "A reading nook is a small cozy place made for sitting with books. It often feels quiet, soft, and snug."
        )
    ],
}
KNOWLEDGE_ORDER = ["book", "flashback", "friendship", "light", "lamp", "puppet", "duet"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    reader = f["reader"]
    friend = f["friend"]
    chapter = f["chapter"]
    helper_cfg = f["helper_cfg"]
    obstacle = f["obstacle"]
    return [
        'Write a funny, gentle story for a 3-to-5-year-old set in a reading nook that includes the words "valley", "frost-dim", and "discourage".',
        f"Tell a friendship story where {reader.id} tries to read a page about a {chapter.place_word}, feels discouraged because of {obstacle.title}, and {friend.id} helps with {helper_cfg.phrase}.",
        "Write a short story with a flashback, a cozy winter window, and a comic ending where reading aloud becomes fun again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    reader = f["reader"]
    friend = f["friend"]
    parent = f["parent"]
    chapter = f["chapter"]
    obstacle = f["obstacle"]
    helper_cfg = f["helper_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_label(reader, friend)}, {reader.id} and {friend.id}, sitting in a reading nook with {reader.id}'s {parent.label_word} nearby."
        ),
        (
            "Where does the story happen?",
            "It happens in a cozy reading nook by the window. The afternoon outside is frost-dim, which helps make the nook feel snug and wintry."
        ),
        (
            f"What were {reader.id} and {friend.id} reading about?",
            f"They were reading a page about a {chapter.place_word}. The book picture showed {chapter.picture}, which made the whole scene feel funny and vivid."
        ),
        (
            f"Why did {reader.id} feel discouraged?",
            f"{reader.id} hesitated because of {obstacle.title}. A flashback to an earlier awkward reading moment made the page feel harder than it really was."
        ),
        (
            "How did the friend help?",
            f"{friend.id} helped by using {helper_cfg.phrase}. That changed the mood of the moment and gave {reader.id} enough confidence to try again."
        ),
        (
            "How did the story end?",
            f"It ended with the friends reading the page together and laughing in the nook. The window stayed frost-dim, but the reading itself became warm, silly, and brave."
        ),
    ]
    if obstacle.id == "friend_blurt":
        qa.append(
            (
                f"Did {friend.id} mean to discourage {reader.id}?",
                f"No. {friend.id} spoke too fast and realized it at once. {friend.pronoun().capitalize()} apologized and then helped repair the moment."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"book", "flashback", "friendship"}
    if f["obstacle"].need == "light":
        tags.add("light")
    if f["helper_cfg"].id == "clip_lamp":
        tags.add("lamp")
        tags.add("light")
    if f["helper_cfg"].id == "puppet":
        tags.add("puppet")
    if f["helper_cfg"].id == "duet":
        tags.add("duet")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        chapter="valley",
        obstacle="shy_flashback",
        helper="puppet",
        reader_name="Lily",
        reader_gender="girl",
        friend_name="Tom",
        friend_gender="boy",
        parent="mother",
        reader_trait="careful",
        friend_trait="dramatic",
    ),
    StoryParams(
        chapter="moon_stairs",
        obstacle="dim_text",
        helper="clip_lamp",
        reader_name="Ben",
        reader_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        parent="father",
        reader_trait="thoughtful",
        friend_trait="cheerful",
    ),
    StoryParams(
        chapter="pancake_castle",
        obstacle="friend_blurt",
        helper="duet",
        reader_name="Zoe",
        reader_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        parent="mother",
        reader_trait="curious",
        friend_trait="bouncy",
    ),
]


ASP_RULES = r"""
needs(O, N) :- obstacle(O), obstacle_need(O, N).
supports(H, N) :- helper(H), helper_supports(H, N).

valid(C, O, H) :- chapter(C), obstacle(O), helper(H), needs(O, N), supports(H, N).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for chapter_id in sorted(CHAPTERS):
        lines.append(asp.fact("chapter", chapter_id))
    for obstacle_id, obstacle in sorted(OBSTACLES.items()):
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("obstacle_need", obstacle_id, obstacle.need))
    for helper_id, helper in sorted(HELPERS.items()):
        lines.append(asp.fact("helper", helper_id))
        for support in sorted(helper.supports):
            lines.append(asp.fact("helper_supports", helper_id, support))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a frost-dim reading nook, a discouraged reader, and a funny friend-shaped fix."
    )
    ap.add_argument("--chapter", choices=CHAPTERS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--reader-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--reader-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.helper and not valid_combo(args.chapter or "valley", args.obstacle, args.helper):
        raise StoryError(explain_rejection(args.obstacle, args.helper))

    combos = [
        combo for combo in valid_combos()
        if (args.chapter is None or combo[0] == args.chapter)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    chapter_id, obstacle_id, helper_id = rng.choice(combos)

    reader_gender = args.reader_gender or rng.choice(["girl", "boy"])
    reader_name = args.reader_name or rng.choice(GIRL_NAMES if reader_gender == "girl" else BOY_NAMES)

    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    friend_name = args.friend_name
    if not friend_name:
        pool = GIRL_NAMES if friend_gender == "girl" else BOY_NAMES
        choices = [name for name in pool if name != reader_name]
        friend_name = rng.choice(choices)

    parent = args.parent or rng.choice(["mother", "father"])
    reader_trait = rng.choice(TRAITS)
    friend_trait = rng.choice(TRAITS)

    return StoryParams(
        chapter=chapter_id,
        obstacle=obstacle_id,
        helper=helper_id,
        reader_name=reader_name,
        reader_gender=reader_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        reader_trait=reader_trait,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.chapter not in CHAPTERS:
        raise StoryError(f"(No story: unknown chapter '{params.chapter}'.)")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(No story: unknown obstacle '{params.obstacle}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if not valid_combo(params.chapter, params.obstacle, params.helper):
        raise StoryError(explain_rejection(params.obstacle, params.helper))

    world = tell(
        chapter=CHAPTERS[params.chapter],
        obstacle=OBSTACLES[params.obstacle],
        helper_cfg=HELPERS[params.helper],
        reader_name=params.reader_name,
        reader_gender=params.reader_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        reader_trait=params.reader_trait,
        friend_trait=params.friend_trait,
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


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - explicit verify safety
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if "frost-dim" not in sample.story or "discourage" not in sample.story or "valley" not in sample.story:
            print("NOTE: default random sample need not use the valley chapter, so checking curated seed sample separately.")
        seed_sample = generate(CURATED[0])
        if not all(word in seed_sample.story for word in ["valley", "frost-dim", "discourage"]):
            raise StoryError("(Smoke test failed: seed words did not appear in the curated seed sample.)")
        print("OK: random resolve/generate smoke test succeeded.")
    except Exception as err:  # pragma: no cover - explicit verify safety
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (chapter, obstacle, helper) combos:\n")
        for chapter_id, obstacle_id, helper_id in combos:
            print(f"  {chapter_id:14} {obstacle_id:14} {helper_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.reader_name} & {p.friend_name}: {p.chapter}, {p.obstacle}, {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
