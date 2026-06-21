#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/don_ankylosaurus_press_sharing_conflict_quest_fable.py

A small fable-like storyworld about Don, a young ankylosaurus, a flower press,
and a quest that turns into a sharing conflict.

The world models a simple truth: some treasures must be handled gently and in
time. Don and a friend go looking for a special plant for the valley's picture
book. They have only one press. If Don clutches it selfishly, a second find may
curl and wilt before it can be saved. If he shares, both can bring something
beautiful home.

Run it
------
python storyworlds/worlds/gpt-5.4/don_ankylosaurus_press_sharing_conflict_quest_fable.py
python storyworlds/worlds/gpt-5.4/don_ankylosaurus_press_sharing_conflict_quest_fable.py --all
python storyworlds/worlds/gpt-5.4/don_ankylosaurus_press_sharing_conflict_quest_fable.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/don_ankylosaurus_press_sharing_conflict_quest_fable.py --asp
python storyworlds/worlds/gpt-5.4/don_ankylosaurus_press_sharing_conflict_quest_fable.py --verify
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

# Make the shared result containers importable when this script is run directly:
# this file lives in storyworlds/worlds/gpt-5.4/, so add storyworlds/ to sys.path.
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
        female = {"girl", "mother", "hen", "ewe", "doe"}
        male = {"boy", "father", "rooster", "ram", "stag"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    path_text: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Specimen:
    id: str
    label: str
    phrase: str
    plural: str
    habitat_line: str
    need: int
    size: int
    fragility: int
    moral: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PressTool:
    id: str
    label: str
    phrase: str
    gentleness: int
    width: int
    speed: int
    success_text: str
    share_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Companion:
    id: str
    type: str
    intro: str
    warning: str
    wisdom: int
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_delay_hurts(world: World) -> list[str]:
    out: list[str] = []
    if "companion_find" not in world.entities:
        return out
    cf = world.get("companion_find")
    if cf.meters["waiting"] < THRESHOLD:
        return out
    specimen = world.facts["specimen_cfg"]
    press = world.facts["press_cfg"]
    if cf.meters["pressed"] >= THRESHOLD:
        return out
    sig = ("delay_hurts", specimen.id, int(cf.meters["waiting"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if specimen.fragility > press.speed:
        cf.meters["wilted"] += 1
        out.append("__wilt__")
    return out


CAUSAL_RULES = [
    Rule(name="delay_hurts", tag="physical", apply=_r_delay_hurts),
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


PLACES = {
    "fern_hill": Place(
        id="fern_hill",
        label="Fern Hill",
        path_text="a winding path up Fern Hill, where the wind combed the grass",
        affords={"moonleaf", "goldfern"},
        tags={"hill", "quest"},
    ),
    "reed_bank": Place(
        id="reed_bank",
        label="Reed Bank",
        path_text="a pebbly path to Reed Bank beside the slow river",
        affords={"river_reed", "moonleaf"},
        tags={"river", "quest"},
    ),
    "sun_meadow": Place(
        id="sun_meadow",
        label="Sun Meadow",
        path_text="a bright trail into Sun Meadow, where bees hummed over the clover",
        affords={"goldfern", "river_reed"},
        tags={"meadow", "quest"},
    ),
}

SPECIMENS = {
    "moonleaf": Specimen(
        id="moonleaf",
        label="moonleaf",
        phrase="a silver moonleaf",
        plural="moonleaves",
        habitat_line="The moonleaf grew thin and round, and it curled at the edges if left alone too long.",
        need=3,
        size=2,
        fragility=3,
        moral="gentle",
        tags={"plant", "leaf"},
    ),
    "goldfern": Specimen(
        id="goldfern",
        label="gold fern",
        phrase="a gold fern frond",
        plural="gold ferns",
        habitat_line="The gold fern was wide and feathery, handsome but easy to bend.",
        need=2,
        size=3,
        fragility=2,
        moral="care",
        tags={"plant", "fern"},
    ),
    "river_reed": Specimen(
        id="river_reed",
        label="river reed",
        phrase="a striped river reed",
        plural="river reeds",
        habitat_line="The river reed was long and neat, and it kept its shape better than the others.",
        need=1,
        size=1,
        fragility=1,
        moral="patience",
        tags={"plant", "reed"},
    ),
}

PRESSES = {
    "oak_press": PressTool(
        id="oak_press",
        label="oak press",
        phrase="an oak press with smooth boards and soft paper",
        gentleness=3,
        width=3,
        speed=3,
        success_text="laid the leaves between soft papers and tightened the oak press with careful paws",
        share_text="There was room enough in the oak press for both finds if Don made space.",
        tags={"press", "sharing"},
    ),
    "strap_press": PressTool(
        id="strap_press",
        label="strap press",
        phrase="a little strap press with two flat boards",
        gentleness=2,
        width=2,
        speed=2,
        success_text="slid the find into the strap press and pulled the leather ties snug",
        share_text="The strap press could save one find quickly, but it asked for turns and patience.",
        tags={"press", "sharing"},
    ),
    "stone_press": PressTool(
        id="stone_press",
        label="stone press",
        phrase="a heavy stone press with rough felt",
        gentleness=1,
        width=3,
        speed=1,
        success_text="tucked the stem under the rough felt and leaned the stone press down",
        share_text="The stone press was broad, but it worked slowly and was not kind to tender things.",
        tags={"press", "sharing"},
    ),
}

COMPANIONS = {
    "wren": Companion(
        id="wren",
        type="bird",
        intro="a small wren named Pip who carried bits of string and bright ideas",
        warning="Pip fluttered to the side and said that a tool used alone can make two empty hands.",
        wisdom=3,
        tags={"bird", "friend"},
    ),
    "tortoise": Companion(
        id="tortoise",
        type="tortoise",
        intro="a young tortoise named Tavi who noticed every stone and every shortcut",
        warning="Tavi blinked slowly and said that slow sharing still reaches home sooner than proud delay.",
        wisdom=2,
        tags={"tortoise", "friend"},
    ),
    "goat": Companion(
        id="goat",
        type="goat",
        intro="a sure-footed goat named Miri who could spot rare plants from far away",
        warning="Miri stamped once and said that a path is shorter when friends carry the work together.",
        wisdom=1,
        tags={"goat", "friend"},
    ),
}

DON_NAMES = ["Don", "Don"]
TRAITS = ["proud", "eager", "careful", "stubborn", "thoughtful"]


def specimen_fits(place: Place, specimen: Specimen) -> bool:
    return specimen.id in place.affords


def press_suits(press: PressTool, specimen: Specimen) -> bool:
    return press.gentleness >= specimen.need and press.width >= specimen.size


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for specimen_id, specimen in SPECIMENS.items():
            for press_id, press in PRESSES.items():
                if specimen_fits(place, specimen) and press_suits(press, specimen):
                    out.append((place_id, specimen_id, press_id))
    return out


def would_share_early(trait: str, companion: Companion) -> bool:
    base = 0
    if trait in {"careful", "thoughtful"}:
        base += 2
    if trait == "eager":
        base += 1
    if trait == "proud":
        base -= 2
    if trait == "stubborn":
        base -= 1
    base += companion.wisdom
    return base >= 3


def companion_saved(share_early: bool, specimen: Specimen, press: PressTool) -> bool:
    if share_early:
        return True
    return specimen.fragility <= press.speed


@dataclass
class StoryParams:
    place: str
    specimen: str
    press: str
    companion: str
    don_name: str
    don_trait: str
    seed: Optional[int] = None


def introduction(world: World, don: Entity, companion: Entity, place: Place, press: PressTool) -> None:
    world.say(
        f"In a green valley lived {don.id}, a young ankylosaurus with a broad back and a serious little frown when he was thinking."
    )
    world.say(
        f"He owned {press.phrase}, and he liked the quiet square shape it gave to wild leaves."
    )
    world.say(
        f"One morning he set out with {companion.attrs['intro']} along {place.path_text}."
    )


def quest(world: World, don: Entity, companion: Entity, specimen: Specimen) -> None:
    don.memes["purpose"] += 1
    companion.memes["purpose"] += 1
    world.say(
        f"They were on a quest to bring {specimen.phrase} back for the valley's winter picture book, so the smallest children could learn the shapes of the hills."
    )
    world.say(specimen.habitat_line)


def find_both(world: World, don: Entity, companion: Entity, specimen: Specimen) -> None:
    df = world.add(Entity(id="don_find", type="specimen", label=specimen.label, phrase=specimen.phrase))
    cf = world.add(Entity(id="companion_find", type="specimen", label=specimen.label, phrase=specimen.phrase))
    df.meters["fresh"] += 1
    cf.meters["fresh"] += 1
    world.say(
        f"At last Don found {specimen.phrase}, and almost at the same moment {companion.id} found another, just as fine."
    )
    world.say(
        "Then both of them looked at the single press, and the trail grew smaller between them."
    )


def warning(world: World, don: Entity, companion: Entity, press: PressTool) -> None:
    companion.memes["caution"] += 1
    world.say(
        f'{companion.id} said, "{press.share_text} If we take turns kindly, both treasures may reach home flat and fair."'
    )
    world.say(companion.attrs["warning"])


def grab_first(world: World, don: Entity, press: PressTool) -> None:
    don.memes["greed"] += 1
    don.memes["conflict"] += 1
    world.say(
        f'But Don pressed his paw over the straps of the {press.label} and said, "I found mine first. I will use the press first too."'
    )
    world.say(
        "A tool that should have helped the road now sat between friends like a shut gate."
    )


def share_first(world: World, don: Entity, companion: Entity, press: PressTool) -> None:
    don.memes["sharing"] += 1
    don.memes["conflict"] = 0.0
    companion.memes["relief"] += 1
    world.say(
        f"Don looked at the press, then at {companion.id}'s hopeful face, and his hard thought softened."
    )
    world.say(
        f'He said, "Let us use the {press.label} together. A find kept only for myself would feel smaller by supper."'
    )


def press_both(world: World, don: Entity, companion: Entity, press: PressTool) -> None:
    world.get("don_find").meters["pressed"] += 1
    world.get("companion_find").meters["pressed"] += 1
    don.memes["joy"] += 1
    companion.memes["joy"] += 1
    world.say(
        f"Side by side they {press.success_text}. Soon both leaves lay flat as green stars in a book."
    )
    world.say(
        "When they started home, the path seemed wider, as if sharing had moved the stones apart."
    )


def selfish_delay(world: World, don: Entity, companion: Entity, press: PressTool) -> None:
    world.get("don_find").meters["pressed"] += 1
    world.get("companion_find").meters["waiting"] += 1
    world.say(
        f"Don hurried to save his own find. He {press.success_text} while {companion.id} waited with careful hands."
    )
    propagate(world, narrate=False)


def see_loss(world: World, don: Entity, companion: Entity, specimen: Specimen) -> None:
    companion.memes["sadness"] += 1
    don.memes["shame"] += 1
    world.say(
        f"By the time Don turned back, {companion.id}'s {specimen.label} had curled at the edges."
    )
    world.say(
        f'{companion.id} did not scold. {companion.pronoun().capitalize()} only whispered, "A treasure can spoil while pride is being fed."'
    )


def late_share(world: World, don: Entity, companion: Entity, press: PressTool) -> None:
    don.memes["sharing"] += 1
    don.memes["lesson"] += 1
    world.say(
        f"Don lowered his head until his club tail rested still in the dust. Then he pushed the {press.label} toward {companion.id}."
    )
    world.say(
        f'"Please use it now," he said. "A friend should not have to wait behind my pride."'
    )


def save_after_wait(world: World, don: Entity, companion: Entity, press: PressTool) -> None:
    world.get("companion_find").meters["pressed"] += 1
    companion.memes["relief"] += 1
    don.memes["lesson"] += 1
    world.say(
        f"{companion.id} slipped the second find into the press just in time."
    )
    world.say(
        "It came out a little tired but still lovely, and Don learned that quick sharing can mend what quick greed almost ruins."
    )


def home_good(world: World, don: Entity, companion: Entity, specimen: Specimen) -> None:
    don.memes["love"] += 1
    companion.memes["love"] += 1
    world.say(
        f"That evening they carried two flat {specimen.plural} to the valley school, and the teacher smiled to see a page rich enough for everyone to admire."
    )
    world.say(
        "Don noticed that the best part of the journey was not the rare plant alone, but the friend who walked home beside him."
    )


def home_sad(world: World, don: Entity, companion: Entity, specimen: Specimen) -> None:
    don.memes["lesson"] += 1
    world.say(
        f"That evening they carried home only one handsome {specimen.label} and one curled lesson."
    )
    world.say(
        "Don kept the good leaf, but it did not feel grand in his paws. He understood at last that a gift held too tightly can grow smaller than it was."
    )


def tell(place: Place, specimen: Specimen, press: PressTool, companion_cfg: Companion,
         don_name: str = "Don", don_trait: str = "thoughtful") -> World:
    world = World()
    don = world.add(Entity(
        id=don_name,
        kind="character",
        type="ankylosaurus",
        label=don_name,
        role="hero",
        traits=[don_trait],
        attrs={"species": "ankylosaurus"},
        tags={"don", "ankylosaurus"},
    ))
    companion = world.add(Entity(
        id=companion_cfg.id.capitalize(),
        kind="character",
        type=companion_cfg.type,
        label=companion_cfg.id.capitalize(),
        role="companion",
        traits=["friend"],
        attrs={"intro": companion_cfg.intro, "warning": companion_cfg.warning},
        tags=set(companion_cfg.tags),
    ))
    world.facts.update(
        place=place,
        specimen_cfg=specimen,
        press_cfg=press,
        companion_cfg=companion_cfg,
        don=don,
        companion=companion,
    )

    introduction(world, don, companion, place, press)
    quest(world, don, companion, specimen)

    world.para()
    find_both(world, don, companion, specimen)
    warning(world, don, companion, press)

    share_early = would_share_early(don_trait, companion_cfg)
    saved = True

    world.para()
    if share_early:
        share_first(world, don, companion, press)
        press_both(world, don, companion, press)
    else:
        grab_first(world, don, press)
        selfish_delay(world, don, companion, press)
        saved = companion_saved(False, specimen, press)
        if saved:
            late_share(world, don, companion, press)
            save_after_wait(world, don, companion, press)
        else:
            see_loss(world, don, companion, specimen)
            late_share(world, don, companion, press)

    world.para()
    if saved:
        home_good(world, don, companion, specimen)
        outcome = "shared_success" if share_early else "late_success"
    else:
        home_sad(world, don, companion, specimen)
        outcome = "wilted_loss"

    world.facts.update(
        share_early=share_early,
        companion_saved=saved,
        outcome=outcome,
        don_find_pressed=world.get("don_find").meters["pressed"] >= THRESHOLD,
        companion_find_pressed=world.get("companion_find").meters["pressed"] >= THRESHOLD,
        companion_find_wilted=world.get("companion_find").meters["wilted"] >= THRESHOLD,
    )
    return world


def explain_rejection(place: Place, specimen: Specimen, press: PressTool) -> str:
    if not specimen_fits(place, specimen):
        return (
            f"(No story: {specimen.phrase} does not grow at {place.label}, so the quest has no honest object there.)"
        )
    if press.width < specimen.size:
        return (
            f"(No story: the {press.label} is too small for {specimen.label}, so it cannot press the find properly.)"
        )
    if press.gentleness < specimen.need:
        return (
            f"(No story: the {press.label} is too rough for {specimen.label}, which needs a gentler press.)"
        )
    return "(No story: this combination does not fit the world's rules.)"


def outcome_of(params: StoryParams) -> str:
    companion = COMPANIONS[params.companion]
    specimen = SPECIMENS[params.specimen]
    press = PRESSES[params.press]
    share_early = would_share_early(params.don_trait, companion)
    if share_early:
        return "shared_success"
    if companion_saved(False, specimen, press):
        return "late_success"
    return "wilted_loss"


KNOWLEDGE = {
    "press": [
        (
            "What is a flower or leaf press?",
            "A press is a tool with flat sides that gently squeezes leaves or flowers so they dry flat. People use one when they want to keep a plant neat and uncurled."
        )
    ],
    "ankylosaurus": [
        (
            "What was an ankylosaurus?",
            "An ankylosaurus was a dinosaur with a heavy body, armor plates, and a club on its tail. It looked strong and sturdy."
        )
    ],
    "sharing": [
        (
            "Why is sharing useful on a trip?",
            "Sharing lets more than one person use what the group needs. It saves time, keeps friends from fighting, and often protects fragile things."
        )
    ],
    "fern": [
        (
            "What is a fern?",
            "A fern is a green plant with many small leaflets on a frond. Some ferns bend easily, so they need to be handled with care."
        )
    ],
    "reed": [
        (
            "What is a reed?",
            "A reed is a tall, thin plant that often grows near water. It bends in the wind and can be used for weaving or study."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey with a clear goal, like finding something important or helping someone. It is more than a walk because the travelers are trying to achieve something."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    don = f["don"]
    companion = f["companion"]
    place = f["place"]
    specimen = f["specimen_cfg"]
    press = f["press_cfg"]
    outcome = f["outcome"]
    if outcome == "wilted_loss":
        end = "and one find is spoiled before they can both use the press"
    elif outcome == "late_success":
        end = "and Don learns to share just before the second find is lost"
    else:
        end = "and both friends succeed because Don shares the press"
    return [
        f'Write a short fable for young children about {don.id}, an ankylosaurus, who goes on a quest to {place.label} with a friend carrying {press.phrase}.',
        f'Write a story that includes the words "don", "ankylosaurus", and "press", and centers on Sharing, Conflict, and Quest as Don and {companion.id} search for {specimen.phrase}.',
        f"Tell a gentle animal fable where two friends find special leaves on the same trip, but there is only one {press.label}, {end}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    don = f["don"]
    companion = f["companion"]
    specimen = f["specimen_cfg"]
    press = f["press_cfg"]
    place = f["place"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {don.id}, a young ankylosaurus, and {companion.id}, a friend who goes on the quest with him. They travel to {place.label} carrying a single {press.label}."
        ),
        (
            "What was their quest?",
            f"They wanted to bring {specimen.phrase} home for the valley's winter picture book. That gave the trip a clear purpose, not just a walk."
        ),
        (
            f"Why did the {press.label} matter?",
            f"It could keep the fragile plant flat and beautiful. Without the press, a find might curl or spoil before they reached home."
        ),
    ]
    if outcome == "shared_success":
        qa.append(
            (
                f"How did Don solve the conflict with {companion.id}?",
                f"Don chose to share the press right away. Because he made room for both finds, the friendship stayed warm and both plants were saved."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"They carried two flat {specimen.plural} to the school. The ending shows that sharing made the quest richer for everyone."
            )
        )
    elif outcome == "late_success":
        qa.append(
            (
                f"What mistake did Don make first?",
                f"He grabbed the press for himself and made {companion.id} wait. That delay almost ruined the second find because fragile plants cannot always wait."
            )
        )
        qa.append(
            (
                f"What changed before the end?",
                f"Don felt ashamed and pushed the press toward {companion.id}. They still saved the second plant, so the lesson arrived in time."
            )
        )
    else:
        qa.append(
            (
                f"What happened while {companion.id} was waiting?",
                f"The second {specimen.label} curled and wilted before it could be pressed. Don's selfish delay caused the loss, even though he finally offered the press afterward."
            )
        )
        qa.append(
            (
                "What lesson did Don learn?",
                f"He learned that pride can spoil a good thing before kindness gets its turn. The single fine leaf at the end felt smaller because it had not been shared."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    specimen = f["specimen_cfg"]
    tags = {"press", "ankylosaurus", "sharing", "quest"}
    if "fern" in specimen.tags:
        tags.add("fern")
    if "reed" in specimen.tags:
        tags.add("reed")
    order = ["press", "ankylosaurus", "sharing", "quest", "fern", "reed"]
    out: list[tuple[str, str]] = []
    for tag in order:
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:14} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="fern_hill",
        specimen="moonleaf",
        press="oak_press",
        companion="wren",
        don_name="Don",
        don_trait="thoughtful",
    ),
    StoryParams(
        place="sun_meadow",
        specimen="goldfern",
        press="strap_press",
        companion="goat",
        don_name="Don",
        don_trait="stubborn",
    ),
    StoryParams(
        place="reed_bank",
        specimen="moonleaf",
        press="oak_press",
        companion="goat",
        don_name="Don",
        don_trait="proud",
    ),
    StoryParams(
        place="reed_bank",
        specimen="river_reed",
        press="stone_press",
        companion="tortoise",
        don_name="Don",
        don_trait="eager",
    ),
]


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
fits(P, S) :- place(P), specimen(S), grows(P, S).
suited(Pr, S) :- press(Pr), specimen(S), gentleness(Pr, G), need(S, N), G >= N,
                 width(Pr, W), size(S, Z), W >= Z.
valid(P, S, Pr) :- fits(P, S), suited(Pr, S).

% --- outcome model ---------------------------------------------------------
base(2)  :- trait(careful).
base(2)  :- trait(thoughtful).
base(1)  :- trait(eager).
base(-2) :- trait(proud).
base(-1) :- trait(stubborn).
base(0)  :- trait(T), not trait(careful), not trait(thoughtful),
            not trait(eager), not trait(proud), not trait(stubborn).

score(B + W) :- base(B), wisdom(W).
share_early :- score(S), S >= 3.

companion_saved :- share_early.
companion_saved :- not share_early, fragility(F), speed(S), F <= S.

outcome(shared_success) :- share_early.
outcome(late_success)   :- not share_early, companion_saved.
outcome(wilted_loss)    :- not share_early, not companion_saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for place_id, place in PLACES.items():
        for specimen_id in sorted(place.affords):
            lines.append(asp.fact("grows", place_id, specimen_id))
    for specimen_id, specimen in SPECIMENS.items():
        lines.append(asp.fact("specimen", specimen_id))
        lines.append(asp.fact("need", specimen_id, specimen.need))
        lines.append(asp.fact("size", specimen_id, specimen.size))
        lines.append(asp.fact("fragility_of", specimen_id, specimen.fragility))
    for press_id, press in PRESSES.items():
        lines.append(asp.fact("press", press_id))
        lines.append(asp.fact("gentleness", press_id, press.gentleness))
        lines.append(asp.fact("width", press_id, press.width))
        lines.append(asp.fact("speed_of", press_id, press.speed))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait_name", trait))
    for companion_id, companion in COMPANIONS.items():
        lines.append(asp.fact("companion", companion_id))
        lines.append(asp.fact("wisdom_of", companion_id, companion.wisdom))
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
            asp.fact("trait", params.don_trait),
            asp.fact("wisdom", COMPANIONS[params.companion].wisdom),
            asp.fact("fragility", SPECIMENS[params.specimen].fragility),
            asp.fact("speed", PRESSES[params.press].speed),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break

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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable storyworld: Don the ankylosaurus, one press, a quest, and a sharing conflict."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--specimen", choices=SPECIMENS)
    ap.add_argument("--press", choices=PRESSES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--name")
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
    if args.place and args.specimen and args.press:
        place = PLACES[args.place]
        specimen = SPECIMENS[args.specimen]
        press = PRESSES[args.press]
        if not (specimen_fits(place, specimen) and press_suits(press, specimen)):
            raise StoryError(explain_rejection(place, specimen, press))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.specimen is None or c[1] == args.specimen)
        and (args.press is None or c[2] == args.press)
    ]
    if not combos:
        if args.place and args.specimen and args.press:
            raise StoryError(explain_rejection(PLACES[args.place], SPECIMENS[args.specimen], PRESSES[args.press]))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, specimen_id, press_id = rng.choice(sorted(combos))
    companion_id = args.companion or rng.choice(sorted(COMPANIONS))
    trait = args.trait or rng.choice(TRAITS)
    don_name = args.name or rng.choice(DON_NAMES)
    return StoryParams(
        place=place_id,
        specimen=specimen_id,
        press=press_id,
        companion=companion_id,
        don_name=don_name,
        don_trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.specimen not in SPECIMENS:
        raise StoryError(f"(Unknown specimen: {params.specimen})")
    if params.press not in PRESSES:
        raise StoryError(f"(Unknown press: {params.press})")
    if params.companion not in COMPANIONS:
        raise StoryError(f"(Unknown companion: {params.companion})")
    if params.don_trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.don_trait})")

    place = PLACES[params.place]
    specimen = SPECIMENS[params.specimen]
    press = PRESSES[params.press]
    if not (specimen_fits(place, specimen) and press_suits(press, specimen)):
        raise StoryError(explain_rejection(place, specimen, press))

    world = tell(
        place=place,
        specimen=specimen,
        press=press,
        companion_cfg=COMPANIONS[params.companion],
        don_name=params.don_name,
        don_trait=params.don_trait,
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
        print(f"{len(combos)} compatible (place, specimen, press) combos:\n")
        for place, specimen, press in combos:
            print(f"  {place:10} {specimen:11} {press}")
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
            header = f"### {p.don_name}: {p.specimen} at {p.place} with {p.press} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
