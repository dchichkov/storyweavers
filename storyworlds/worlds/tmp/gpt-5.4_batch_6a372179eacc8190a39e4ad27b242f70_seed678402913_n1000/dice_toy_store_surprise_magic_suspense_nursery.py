#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dice_toy_store_surprise_magic_suspense_nursery.py
============================================================================

A standalone story world about a child in a toy store, a pair of magic dice,
and a hidden surprise that opens only with the right helper and enough twinkling
luck. The prose leans nursery-rhyme-soft: gentle repetition, bright images, and
a suspenseful pause before the surprise arrives.

The world model keeps the story grounded:

- each hidden cabinet has a practical need: it is high up, dark inside, or shy
- only a fitting helper makes the cabinet "ready"
- rolling the dice adds spark to the cabinet
- once the cabinet is ready and has enough spark, it opens and reveals the toy
- if the first two rolls are not enough, the child faces a short suspense beat
  and gets one last gentle roll that resolves the scene

Run it
------
    python storyworlds/worlds/gpt-5.4/dice_toy_store_surprise_magic_suspense_nursery.py
    python storyworlds/worlds/gpt-5.4/dice_toy_store_surprise_magic_suspense_nursery.py --cabinet moon_shelf --prize moon_bear --helper stool
    python storyworlds/worlds/gpt-5.4/dice_toy_store_surprise_magic_suspense_nursery.py --cabinet moon_shelf --helper lantern
    python storyworlds/worlds/gpt-5.4/dice_toy_store_surprise_magic_suspense_nursery.py --all
    python storyworlds/worlds/gpt-5.4/dice_toy_store_surprise_magic_suspense_nursery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/dice_toy_store_surprise_magic_suspense_nursery.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Cabinet:
    id: str
    label: str
    phrase: str
    place_line: str
    need: str
    threshold: int
    accepted_prizes: tuple[str, ...] = ()
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    reveal_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    solves: str
    action_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_rolls: list[int] = []

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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        other.trace_rolls = list(self.trace_rolls)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_ready(world: World) -> list[str]:
    cabinet = world.get("cabinet")
    helper = world.get("helper")
    if helper.attrs.get("solves") != cabinet.attrs.get("need"):
        return []
    sig = ("ready", helper.id, cabinet.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cabinet.meters["ready"] += 1
    world.get("child").memes["hope"] += 1
    return []


def _r_wait(world: World) -> list[str]:
    cabinet = world.get("cabinet")
    if cabinet.meters["open"] >= THRESHOLD:
        return []
    if cabinet.meters["spark"] < cabinet.attrs.get("threshold", 0):
        if len(world.trace_rolls) >= 2:
            sig = ("suspense", len(world.trace_rolls))
            if sig in world.fired:
                return []
            world.fired.add(sig)
            world.get("child").memes["suspense"] += 1
    return []


def _r_open(world: World) -> list[str]:
    cabinet = world.get("cabinet")
    prize = world.get("prize")
    if cabinet.meters["ready"] < THRESHOLD:
        return []
    if cabinet.meters["spark"] < cabinet.attrs.get("threshold", 0):
        return []
    sig = ("open", cabinet.id, prize.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cabinet.meters["open"] += 1
    prize.meters["revealed"] += 1
    child = world.get("child")
    child.memes["joy"] += 2
    child.memes["wonder"] += 1
    child.memes["suspense"] = 0.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="ready", tag="physical", apply=_r_ready),
    Rule(name="wait", tag="emotional", apply=_r_wait),
    Rule(name="open", tag="physical", apply=_r_open),
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
        if any(rule.apply(world) for rule in []):
            changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


CABINETS = {
    "moon_shelf": Cabinet(
        id="moon_shelf",
        label="moon shelf",
        phrase="a silver moon shelf with a tiny locked door",
        place_line="high above the jigsaw boxes",
        need="high",
        threshold=7,
        accepted_prizes=("moon_bear", "star_rattle"),
        tags={"moon", "high"},
    ),
    "shadow_nook": Cabinet(
        id="shadow_nook",
        label="shadow nook",
        phrase="a little velvet nook behind a starry curtain",
        place_line="in the dim corner by the dollhouse lamps",
        need="dark",
        threshold=6,
        accepted_prizes=("glow_train", "night_ball"),
        tags={"dark", "curtain"},
    ),
    "hush_drawer": Cabinet(
        id="hush_drawer",
        label="hush drawer",
        phrase="a painted drawer with a mouse-sized golden knob",
        place_line="under the tinkly music shelf",
        need="shy",
        threshold=5,
        accepted_prizes=("mouse_puppet", "tin_duck"),
        tags={"quiet", "drawer"},
    ),
}

PRIZES = {
    "moon_bear": Prize(
        id="moon_bear",
        label="moon bear",
        phrase="a moon bear with a blue satin bow",
        reveal_line="Out peeped a moon bear with a blue satin bow.",
        ending_line="The moon bear sat in the crook of the child's arm, soft as a cloud at bedtime.",
        tags={"bear", "moon"},
    ),
    "star_rattle": Prize(
        id="star_rattle",
        label="star rattle",
        phrase="a star rattle full of sleepy silver beads",
        reveal_line="Out slid a star rattle that chimed with a sleepy silver shake.",
        ending_line="The star rattle twinkled in the child's hand and made the whole aisle sound like a lullaby.",
        tags={"rattle", "star"},
    ),
    "glow_train": Prize(
        id="glow_train",
        label="glow train",
        phrase="a tiny glow train with lemon-yellow windows",
        reveal_line="Out rolled a tiny glow train with lemon-yellow windows.",
        ending_line="The glow train waited by the child's shoe, bright and brave and ready for track-time dreams.",
        tags={"train", "light"},
    ),
    "night_ball": Prize(
        id="night_ball",
        label="night ball",
        phrase="a night ball dotted with little painted stars",
        reveal_line="Out bounced a night ball dotted with little painted stars.",
        ending_line="The night ball shone like a pocket moon while the child held it close.",
        tags={"ball", "night"},
    ),
    "mouse_puppet": Prize(
        id="mouse_puppet",
        label="mouse puppet",
        phrase="a mouse puppet with whiskers as thin as thread",
        reveal_line="Out popped a mouse puppet with whiskers as thin as thread.",
        ending_line="The mouse puppet bobbed on the child's hand and seemed to whisper a secret rhyme.",
        tags={"mouse", "puppet"},
    ),
    "tin_duck": Prize(
        id="tin_duck",
        label="tin duck",
        phrase="a tiny tin duck on red wheels",
        reveal_line="Out waddled a tiny tin duck on red wheels.",
        ending_line="The tin duck clicked across the floor in the neatest little parade.",
        tags={"duck", "tin"},
    ),
}

HELPERS = {
    "stool": Helper(
        id="stool",
        label="stool",
        phrase="a little red step stool",
        solves="high",
        action_line="The keeper set down a little red step stool so small shoes could reach the moony shelf.",
        tags={"stool", "reach"},
    ),
    "lantern": Helper(
        id="lantern",
        label="lantern",
        phrase="a paper-star lantern",
        solves="dark",
        action_line="The keeper lit a paper-star lantern, and the dim nook turned soft and golden.",
        tags={"lantern", "light"},
    ),
    "music_box": Helper(
        id="music_box",
        label="music box",
        phrase="a tiny music box with a velvet crank",
        solves="shy",
        action_line="The keeper turned a tiny music box, and its hush-hush tune told the shy drawer it was safe to sing.",
        tags={"music", "gentle"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Nora"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Theo", "Finn", "Eli", "Noah"]
TRAITS = ["gentle", "curious", "bright-eyed", "patient", "bouncy", "soft-voiced"]


def helper_fits(cabinet: Cabinet, helper: Helper) -> bool:
    return cabinet.need == helper.solves


def prize_fits(cabinet: Cabinet, prize: Prize) -> bool:
    return prize.id in cabinet.accepted_prizes


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for cabinet_id, cabinet in CABINETS.items():
        for prize_id, prize in PRIZES.items():
            if not prize_fits(cabinet, prize):
                continue
            for helper_id, helper in HELPERS.items():
                if helper_fits(cabinet, helper):
                    combos.append((cabinet_id, prize_id, helper_id))
    return combos


@dataclass
class StoryParams:
    cabinet: str
    prize: str
    helper: str
    name: str
    gender: str
    keeper: str
    trait: str
    die1: int
    die2: int
    die3: int
    seed: Optional[int] = None


def _check_param_keys(params: StoryParams) -> None:
    if params.cabinet not in CABINETS:
        raise StoryError(f"(Unknown cabinet: {params.cabinet})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")


def explain_rejection(cabinet: Cabinet, prize: Prize, helper: Helper) -> str:
    if not prize_fits(cabinet, prize):
        good = ", ".join(cabinet.accepted_prizes)
        return (
            f"(No story: {prize.label} does not belong in the {cabinet.label}. "
            f"That cabinet sensibly reveals only: {good}.)"
        )
    if not helper_fits(cabinet, helper):
        return (
            f"(No story: the {cabinet.label} needs help for '{cabinet.need}', "
            f"but {helper.label} solves '{helper.solves}'. Pick a helper that fits the hiding place.)"
        )
    return "(No story: that combination is not reasonable in this toy store.)"


def suspense_kind(params: StoryParams) -> str:
    _check_param_keys(params)
    total = params.die1 + params.die2
    threshold = CABINETS[params.cabinet].threshold
    return "quick" if total >= threshold else "lingering"


def final_total(params: StoryParams) -> int:
    if suspense_kind(params) == "quick":
        return params.die1 + params.die2
    return params.die1 + params.die2 + params.die3


def _use_helper(world: World) -> None:
    helper = world.get("helper")
    child = world.get("child")
    child.memes["hope"] += 1
    world.say(helper.attrs["action_line"])
    propagate(world, narrate=False)


def _roll(world: World, value: int, ordinal: str) -> None:
    cabinet = world.get("cabinet")
    child = world.get("child")
    cabinet.meters["spark"] += value
    child.memes["wonder"] += 1
    world.trace_rolls.append(value)
    word = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}[value]
    world.say(
        f"The magic dice went clitter-clack, clitter-clack, and {ordinal} they showed {word}. "
        f"Little sparks ran round the lock like fireflies learning a tune."
    )
    propagate(world, narrate=False)


def tell(
    cabinet_cfg: Cabinet,
    prize_cfg: Prize,
    helper_cfg: Helper,
    *,
    name: str = "Lily",
    gender: str = "girl",
    keeper: str = "mother",
    trait: str = "curious",
    die1: int = 3,
    die2: int = 4,
    die3: int = 2,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            label=name,
            role="child",
            attrs={"trait": trait},
        )
    )
    keeper_ent = world.add(
        Entity(
            id="Keeper",
            kind="character",
            type=keeper,
            label="the keeper",
            role="keeper",
        )
    )
    cabinet = world.add(
        Entity(
            id="cabinet",
            type="cabinet",
            label=cabinet_cfg.label,
            phrase=cabinet_cfg.phrase,
            attrs={
                "need": cabinet_cfg.need,
                "threshold": cabinet_cfg.threshold,
                "place_line": cabinet_cfg.place_line,
            },
            tags=set(cabinet_cfg.tags),
        )
    )
    prize = world.add(
        Entity(
            id="prize",
            type="toy",
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            attrs={
                "reveal_line": prize_cfg.reveal_line,
                "ending_line": prize_cfg.ending_line,
            },
            tags=set(prize_cfg.tags),
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            type="helper",
            label=helper_cfg.label,
            phrase=helper_cfg.phrase,
            attrs={
                "solves": helper_cfg.solves,
                "action_line": helper_cfg.action_line,
            },
            tags=set(helper_cfg.tags),
        )
    )

    world.say(
        f"In the toy store, where teddies peeped and tin wheels shone, little {name} stood with a {trait} stare."
    )
    world.say(
        f"There, {cabinet_cfg.place_line}, was {cabinet_cfg.phrase}. It gave one tiny tremble, then was still."
    )
    world.say(
        f'"Tap-tap, hush-hush, what waits there?" whispered {name}.'
    )

    world.para()
    child.memes["desire"] += 1
    child.memes["suspense"] += 1
    world.say(
        f'{keeper_ent.label_word.capitalize()} smiled and opened a velvet tray. "A surprise waits inside," '
        f'{keeper_ent.pronoun()} said, "but only kind hands, the right help, and the magic dice may wake it."'
    )
    _use_helper(world)
    world.say(
        f'{name} held the dice in both hands. They felt cool as marbles and bright as wishes.'
    )

    world.para()
    _roll(world, die1, "first")
    _roll(world, die2, "next")

    quick = cabinet.meters["open"] >= THRESHOLD
    if not quick:
        world.say(
            "The lock gave a tiny ping, then waited. Not open yet. Not open yet."
        )
        world.say(
            f"{name}'s heart went tip-tip-tip. For one breath the whole toy store seemed to listen."
        )
        world.say(
            f'"One more roll," said {keeper_ent.label_word}, very softly. "Slow now. Low now. Let the little wonder grow now."'
        )
        world.para()
        _roll(world, die3, "last")

    if cabinet.meters["open"] < THRESHOLD:
        raise StoryError("(Story failed: the cabinet never opened. Check dice totals and helper.)")

    world.say(prize.attrs["reveal_line"])
    world.say(
        f'{name} laughed so softly that even the blocks on the next shelf seemed to smile.'
    )

    world.para()
    world.say(
        f'"A surprise for patient hands," said {keeper_ent.label_word}. "And a bright surprise too, because you listened before you looked."'
    )
    world.say(prize.attrs["ending_line"])
    world.say(
        "So clitter-clack went the dice, and soft-soft went the light, and the toy store kept its twinkly secret till just the proper night."
    )

    outcome = "quick" if suspense_kind(
        StoryParams(
            cabinet=cabinet_cfg.id,
            prize=prize_cfg.id,
            helper=helper_cfg.id,
            name=name,
            gender=gender,
            keeper=keeper,
            trait=trait,
            die1=die1,
            die2=die2,
            die3=die3,
            seed=None,
        )
    ) == "quick" else "lingering"

    world.facts.update(
        child=child,
        keeper=keeper_ent,
        cabinet_cfg=cabinet_cfg,
        prize_cfg=prize_cfg,
        helper_cfg=helper_cfg,
        outcome=outcome,
        rolls=list(world.trace_rolls),
        final_total=cabinet.meters["spark"],
        threshold=cabinet_cfg.threshold,
        opened=prize.meters["revealed"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "dice": [
        (
            "What are dice?",
            "Dice are small cubes with numbers or dots on their sides. People roll dice in games to see what number comes up."
        )
    ],
    "toy_store": [
        (
            "What is a toy store?",
            "A toy store is a shop where people can look at and buy toys. It often has shelves, boxes, and bright displays."
        )
    ],
    "magic": [
        (
            "What does magic mean in a story?",
            "Magic means something wonderful happens in a way that does not work like ordinary life. In stories, magic often makes a surprise feel bright and special."
        )
    ],
    "surprise": [
        (
            "What is a surprise?",
            "A surprise is something you do not know yet and then suddenly discover. A happy surprise can make people gasp, smile, or laugh."
        )
    ],
    "suspense": [
        (
            "What is suspense in a story?",
            "Suspense is the feeling of waiting and wondering what will happen next. It makes a story feel exciting and a little tingly."
        )
    ],
    "stool": [
        (
            "What is a step stool for?",
            "A step stool helps someone reach something high. It makes a small person taller for a moment."
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern gives light in a dim place. It helps people see what is hidden in the dark."
        )
    ],
    "music": [
        (
            "Why can music feel gentle in a story?",
            "Gentle music can calm a place down and make it feel safe. That is why a shy or quiet moment often goes with a soft tune."
        )
    ],
}
KNOWLEDGE_ORDER = ["toy_store", "dice", "magic", "surprise", "suspense", "stool", "lantern", "music"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    cabinet = f["cabinet_cfg"]
    prize = f["prize_cfg"]
    outcome = f["outcome"]
    prompt3 = (
        f'Write a nursery-rhyme-style story set in a toy store where {child.id} rolls magic dice '
        f'to open {cabinet.phrase} and finds {prize.phrase}.'
    )
    if outcome == "quick":
        prompt3 += " Keep the suspense gentle and the surprise swift."
    else:
        prompt3 += " Let there be a soft suspense beat before one last roll opens it."
    return [
        'Write a short nursery-rhyme-style story for a 3-to-5-year-old set in a toy store and include the word "dice".',
        f"Tell a gentle magical story where a child named {child.id} waits for a hidden toy-store surprise instead of peeking too soon.",
        prompt3,
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    keeper = f["keeper"]
    cabinet = f["cabinet_cfg"]
    prize = f["prize_cfg"]
    helper = f["helper_cfg"]
    rolls = f["rolls"]
    total = int(f["final_total"])
    threshold = f["threshold"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} in a toy store, and {child.pronoun('possessive')} {keeper.label_word} who guides the surprise game. Together they wait for a hidden toy to appear."
        ),
        (
            "What did the child find in the toy store?",
            f"{child.id} found {cabinet.phrase} {cabinet.place_line}. It seemed quiet at first, but it held a secret surprise inside."
        ),
        (
            "Why did they use the helper before rolling the dice?",
            f"They used {helper.phrase} because the hiding place needed that kind of help. The surprise could only wake properly when the cabinet was ready as well as magical."
        ),
        (
            "What happened when the child rolled the dice?",
            f"The dice added spark to the little lock until the cabinet opened. The numbers mattered because the hidden toy only came out once enough magic had gathered."
        ),
    ]

    if f["outcome"] == "lingering":
        qa.append(
            (
                "Why did the story feel suspenseful in the middle?",
                f"After the first two rolls, the lock only gave a tiny ping and stayed shut. That made {child.id} wait and wonder, because the magic total was only {rolls[0] + rolls[1]} and the cabinet needed {threshold}."
            )
        )
    else:
        qa.append(
            (
                "Was there suspense even though the surprise opened quickly?",
                f"Yes, a little. {child.id} still had to wait through the clitter-clack of the dice before knowing what would happen, but the first two rolls were already enough to wake the cabinet."
            )
        )

    qa.append(
        (
            "What was the surprise at the end?",
            f"The surprise was {prize.phrase}. It appeared only after the right help and the right amount of dice-magic worked together."
        )
    )
    qa.append(
        (
            "How did the child feel at the end?",
            f"{child.id} felt happy and full of wonder. The ending shows that patient waiting turned the suspense into a bright surprise."
        )
    )
    qa.append(
        (
            "How much magic did the dice make altogether?",
            f"The rolls made {total} points of spark altogether. That was enough to pass the cabinet's threshold of {threshold}, so the hidden toy came out."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"dice", "toy_store", "magic", "surprise", "suspense"}
    helper = world.facts["helper_cfg"]
    if helper.id == "stool":
        tags.add("stool")
    elif helper.id == "lantern":
        tags.add("lantern")
    elif helper.id == "music_box":
        tags.add("music")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  rolls: {world.trace_rolls}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        cabinet="moon_shelf",
        prize="moon_bear",
        helper="stool",
        name="Lily",
        gender="girl",
        keeper="mother",
        trait="bright-eyed",
        die1=4,
        die2=3,
        die3=1,
        seed=None,
    ),
    StoryParams(
        cabinet="shadow_nook",
        prize="glow_train",
        helper="lantern",
        name="Ben",
        gender="boy",
        keeper="father",
        trait="curious",
        die1=2,
        die2=2,
        die3=3,
        seed=None,
    ),
    StoryParams(
        cabinet="hush_drawer",
        prize="mouse_puppet",
        helper="music_box",
        name="Mia",
        gender="girl",
        keeper="mother",
        trait="gentle",
        die1=1,
        die2=3,
        die3=2,
        seed=None,
    ),
    StoryParams(
        cabinet="shadow_nook",
        prize="night_ball",
        helper="lantern",
        name="Theo",
        gender="boy",
        keeper="father",
        trait="patient",
        die1=5,
        die2=2,
        die3=1,
        seed=None,
    ),
    StoryParams(
        cabinet="hush_drawer",
        prize="tin_duck",
        helper="music_box",
        name="Nora",
        gender="girl",
        keeper="mother",
        trait="soft-voiced",
        die1=2,
        die2=1,
        die3=2,
        seed=None,
    ),
]


ASP_RULES = r"""
prize_fits(C, P) :- accepts(C, P).
helper_fits(C, H) :- needs(C, N), solves(H, N).
valid(C, P, H) :- cabinet(C), prize(P), helper(H), prize_fits(C, P), helper_fits(C, H).

two_total(D1 + D2) :- die1(D1), die2(D2).
three_total(D1 + D2 + D3) :- die1(D1), die2(D2), die3(D3).
quick :- chosen_cabinet(C), threshold(C, T), two_total(S), S >= T.
outcome(quick) :- quick.
outcome(lingering) :- not quick.

final_total(S) :- quick, two_total(S).
final_total(S) :- not quick, three_total(S).
opens :- chosen_cabinet(C), threshold(C, T), final_total(S), S >= T, chosen_helper(H), helper_fits(C, H), chosen_prize(P), prize_fits(C, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid, cabinet in CABINETS.items():
        lines.append(asp.fact("cabinet", cid))
        lines.append(asp.fact("threshold", cid, cabinet.threshold))
        lines.append(asp.fact("needs", cid, cabinet.need))
        for pid in cabinet.accepted_prizes:
            lines.append(asp.fact("accepts", cid, pid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("solves", hid, helper.solves))
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
            asp.fact("chosen_cabinet", params.cabinet),
            asp.fact("chosen_prize", params.prize),
            asp.fact("chosen_helper", params.helper),
            asp.fact("die1", params.die1),
            asp.fact("die2", params.die2),
            asp.fact("die3", params.die3),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1.\n#show opens/0."))
    outcome_atoms = asp.atoms(model, "outcome")
    opens = asp.atoms(model, "opens")
    if not opens:
        return "invalid"
    return outcome_atoms[0][0] if outcome_atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    rng = random.Random(123)
    for _ in range(20):
        params = resolve_params(build_parser().parse_args([]), rng)
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != suspense_kind(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome checks differed.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False, header="### smoke")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Toy-store nursery-rhyme story world with magic dice, suspense, and surprise."
    )
    ap.add_argument("--cabinet", choices=sorted(CABINETS))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--keeper", choices=["mother", "father"])
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("--die1", type=int, choices=[1, 2, 3, 4, 5, 6])
    ap.add_argument("--die2", type=int, choices=[1, 2, 3, 4, 5, 6])
    ap.add_argument("--die3", type=int, choices=[1, 2, 3, 4, 5, 6])
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
    if args.cabinet and args.prize and args.helper:
        cabinet = CABINETS[args.cabinet]
        prize = PRIZES[args.prize]
        helper = HELPERS[args.helper]
        if not (prize_fits(cabinet, prize) and helper_fits(cabinet, helper)):
            raise StoryError(explain_rejection(cabinet, prize, helper))
    elif args.cabinet and args.prize:
        cabinet = CABINETS[args.cabinet]
        prize = PRIZES[args.prize]
        helper = HELPERS[args.helper] if args.helper else next(iter(HELPERS.values()))
        if not prize_fits(cabinet, prize):
            raise StoryError(explain_rejection(cabinet, prize, helper))
    elif args.cabinet and args.helper:
        cabinet = CABINETS[args.cabinet]
        helper = HELPERS[args.helper]
        prize = PRIZES[args.prize] if args.prize else next(iter(PRIZES.values()))
        if not helper_fits(cabinet, helper):
            raise StoryError(explain_rejection(cabinet, prize, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.cabinet is None or combo[0] == args.cabinet)
        and (args.prize is None or combo[1] == args.prize)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    cabinet_id, prize_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)
    keeper = args.keeper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    die1 = args.die1 if args.die1 is not None else rng.randint(1, 6)
    die2 = args.die2 if args.die2 is not None else rng.randint(1, 6)
    die3 = args.die3 if args.die3 is not None else rng.randint(1, 6)

    params = StoryParams(
        cabinet=cabinet_id,
        prize=prize_id,
        helper=helper_id,
        name=name,
        gender=gender,
        keeper=keeper,
        trait=trait,
        die1=die1,
        die2=die2,
        die3=die3,
        seed=None,
    )
    if final_total(params) < CABINETS[cabinet_id].threshold:
        need = CABINETS[cabinet_id].threshold - (die1 + die2)
        if need > 0 and args.die3 is None:
            params.die3 = max(need, 1)
        elif final_total(params) < CABINETS[cabinet_id].threshold:
            raise StoryError("(No story: the chosen dice never make enough magic to open the surprise cabinet.)")
    return params


def generate(params: StoryParams) -> StorySample:
    _check_param_keys(params)
    cabinet = CABINETS[params.cabinet]
    prize = PRIZES[params.prize]
    helper = HELPERS[params.helper]
    if not prize_fits(cabinet, prize) or not helper_fits(cabinet, helper):
        raise StoryError(explain_rejection(cabinet, prize, helper))
    if final_total(params) < cabinet.threshold:
        raise StoryError("(No story: the dice total is too small to reveal the surprise.)")

    world = tell(
        cabinet,
        prize,
        helper,
        name=params.name,
        gender=params.gender,
        keeper=params.keeper,
        trait=params.trait,
        die1=params.die1,
        die2=params.die2,
        die3=params.die3,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1.\n#show opens/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (cabinet, prize, helper) combos:\n")
        for cabinet, prize, helper in combos:
            print(f"  {cabinet:12} {prize:12} {helper}")
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
            header = f"### {p.name}: {p.cabinet} -> {p.prize} with {p.helper} ({suspense_kind(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
