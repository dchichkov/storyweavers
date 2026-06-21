#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/complement_row_sound_effects_transformation_dialogue_nursery.py
==========================================================================================

A small nursery-rhyme-style story world about a shy bud in a row, a musical
helper, and a morning transformation. The required seed words appear naturally:
the flower grows in a row, and one sound is said to complement another.

The world model keeps simple physical meters (closed, warmed, open, singing)
and emotional memes (shy, hope, brave, joy, belonging). A helper encourages the
bud, the morning catalyst arrives, and the bud opens into a bell-like bloom.
The ending image proves the change by letting the new flower join the morning
music.

Run it
------
    python storyworlds/worlds/gpt-5.4/complement_row_sound_effects_transformation_dialogue_nursery.py
    python storyworlds/worlds/gpt-5.4/complement_row_sound_effects_transformation_dialogue_nursery.py --place pond_row --bloom lilybell --helper frog
    python storyworlds/worlds/gpt-5.4/complement_row_sound_effects_transformation_dialogue_nursery.py --place window_row --helper frog
    python storyworlds/worlds/gpt-5.4/complement_row_sound_effects_transformation_dialogue_nursery.py --all
    python storyworlds/worlds/gpt-5.4/complement_row_sound_effects_transformation_dialogue_nursery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/complement_row_sound_effects_transformation_dialogue_nursery.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "wren"}
        male = {"boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    row_phrase: str
    catalyst: str
    morning_line: str
    supports_blooms: set[str] = field(default_factory=set)
    supports_helpers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Bloom:
    id: str
    bud_label: str
    bloom_label: str
    phrase: str
    color: str
    chime: str
    open_sound: str
    transform_line: str
    compatible_helpers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    type: str
    label: str
    phrase: str
    arrive_sound: str
    song_sound: str
    speech: str
    reply: str
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


def _r_open(world: World) -> list[str]:
    bud = world.get("bud")
    if bud.meters["open"] >= THRESHOLD:
        return []
    if bud.meters["encouraged"] < THRESHOLD or bud.meters["warmed"] < THRESHOLD:
        return []
    sig = ("open", bud.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bud.meters["open"] += 1
    bud.meters["closed"] = 0.0
    bud.memes["shy"] = 0.0
    bud.memes["brave"] += 1
    bud.memes["joy"] += 1
    bloom_cfg: Bloom = world.facts["bloom_cfg"]
    world.facts["transformed"] = True
    return [f'{bloom_cfg.open_sound}! {bloom_cfg.transform_line}']


def _r_duet(world: World) -> list[str]:
    bud = world.get("bud")
    helper = world.get("helper")
    chorus = world.get("chorus")
    if bud.meters["open"] < THRESHOLD or helper.meters["singing"] < THRESHOLD:
        return []
    sig = ("duet", bud.id, helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    chorus.meters["music"] += 1
    bud.memes["belonging"] += 1
    helper.memes["joy"] += 1
    world.facts["duet"] = True
    return ["__duet__"]


CAUSAL_RULES = [
    Rule(name="open", tag="physical", apply=_r_open),
    Rule(name="duet", tag="social", apply=_r_duet),
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
    "garden_row": Place(
        id="garden_row",
        label="the garden path",
        row_phrase="a tidy row of clay pots by the garden path",
        catalyst="a pearl of dew and a stripe of sun",
        morning_line="Morning came with tiptoe light on the leaves.",
        supports_blooms={"bluebell", "butterbell"},
        supports_helpers={"bee", "cricket", "wren"},
        tags={"garden", "row"},
    ),
    "window_row": Place(
        id="window_row",
        label="the cottage window",
        row_phrase="a bright row of window boxes under the cottage sill",
        catalyst="a warm sunbeam and a small drink from the watering can",
        morning_line="Morning slid down the window in ribbons of gold.",
        supports_blooms={"bluebell", "morningbell"},
        supports_helpers={"bee", "wren"},
        tags={"window", "row"},
    ),
    "pond_row": Place(
        id="pond_row",
        label="the pond edge",
        row_phrase="a bobbing row of round green pads by the pond edge",
        catalyst="a soft ripple and a patch of warm light",
        morning_line="Morning woke the pond with silver circles.",
        supports_blooms={"lilybell", "reedbell"},
        supports_helpers={"frog", "cricket"},
        tags={"pond", "row"},
    ),
}

BLOOMS = {
    "bluebell": Bloom(
        id="bluebell",
        bud_label="blue bud",
        bloom_label="bluebell",
        phrase="a little blue bud",
        color="blue",
        chime="ting-ting",
        open_sound="plink-plink",
        transform_line="The little blue bud loosened its fold and became a true bluebell.",
        compatible_helpers={"bee", "wren", "cricket"},
        tags={"flower", "bluebell", "transformation"},
    ),
    "butterbell": Bloom(
        id="butterbell",
        bud_label="yellow bud",
        bloom_label="butterbell",
        phrase="a butter-yellow bud",
        color="yellow",
        chime="ding-ding",
        open_sound="ding-a-ling",
        transform_line="The butter-yellow bud stretched wide and turned into a bright butterbell.",
        compatible_helpers={"bee", "cricket", "wren"},
        tags={"flower", "yellow", "transformation"},
    ),
    "morningbell": Bloom(
        id="morningbell",
        bud_label="sleepy bud",
        bloom_label="morningbell",
        phrase="a sleepy little bud",
        color="pink",
        chime="tin-tin",
        open_sound="ping-ping",
        transform_line="The sleepy bud lifted its face and opened into a pink morningbell.",
        compatible_helpers={"bee", "wren"},
        tags={"flower", "pink", "transformation"},
    ),
    "lilybell": Bloom(
        id="lilybell",
        bud_label="pond bud",
        bloom_label="lilybell",
        phrase="a white pond bud",
        color="white",
        chime="plim-plim",
        open_sound="plim-plam",
        transform_line="The white pond bud uncurled and floated up as a shining lilybell.",
        compatible_helpers={"frog", "cricket"},
        tags={"flower", "pond", "transformation"},
    ),
    "reedbell": Bloom(
        id="reedbell",
        bud_label="reed bud",
        bloom_label="reedbell",
        phrase="a pale reed bud",
        color="green",
        chime="shing-shing",
        open_sound="shirr-shing",
        transform_line="The pale reed bud lifted on its stem and became a slim reedbell.",
        compatible_helpers={"frog", "cricket"},
        tags={"flower", "reed", "transformation"},
    ),
}

HELPERS = {
    "bee": Helper(
        id="bee",
        type="bee",
        label="bee",
        phrase="a round little bee",
        arrive_sound="buzz-buzz",
        song_sound="bmmm-bmmm",
        speech="Do not droop, little one. My hum will complement your chime.",
        reply="I want to sing in the morning row, but I am still folded tight.",
        tags={"bee", "sound"},
    ),
    "cricket": Helper(
        id="cricket",
        type="cricket",
        label="cricket",
        phrase="a green little cricket",
        arrive_sound="chirr-chirr",
        song_sound="chirr-ree",
        speech="Do not droop, little one. My fiddle-sound will complement your chime.",
        reply="I can hear the whole row, but my own small song is hiding.",
        tags={"cricket", "sound"},
    ),
    "frog": Helper(
        id="frog",
        type="frog",
        label="frog",
        phrase="a plump green frog",
        arrive_sound="ribbit-rubbit",
        song_sound="croak-crook",
        speech="Do not droop, little one. My low croak will complement your chime.",
        reply="The pond row is singing already, and I am only a folded bud.",
        tags={"frog", "sound"},
    ),
    "wren": Helper(
        id="wren",
        type="wren",
        label="wren",
        phrase="a brown little wren",
        arrive_sound="tweet-tweet",
        song_sound="trill-lill",
        speech="Do not droop, little one. My trill will complement your chime.",
        reply="I wish I were open enough to answer the day.",
        tags={"wren", "sound"},
    ),
}


def valid_combo(place_id: str, bloom_id: str, helper_id: str) -> bool:
    if place_id not in PLACES or bloom_id not in BLOOMS or helper_id not in HELPERS:
        return False
    place = PLACES[place_id]
    bloom = BLOOMS[bloom_id]
    return (
        bloom_id in place.supports_blooms
        and helper_id in place.supports_helpers
        and helper_id in bloom.compatible_helpers
    )


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id in sorted(PLACES):
        for bloom_id in sorted(BLOOMS):
            for helper_id in sorted(HELPERS):
                if valid_combo(place_id, bloom_id, helper_id):
                    out.append((place_id, bloom_id, helper_id))
    return out


@dataclass
class StoryParams:
    place: str
    bloom: str
    helper: str
    bud_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="garden_row", bloom="bluebell", helper="bee", bud_name="Mim"),
    StoryParams(place="garden_row", bloom="butterbell", helper="cricket", bud_name="Dot"),
    StoryParams(place="window_row", bloom="morningbell", helper="wren", bud_name="Pip"),
    StoryParams(place="pond_row", bloom="lilybell", helper="frog", bud_name="Nell"),
    StoryParams(place="pond_row", bloom="reedbell", helper="cricket", bud_name="Tib"),
]

NAMES = ["Mim", "Dot", "Pip", "Nell", "Tib", "May", "Kit", "Bess", "Tess", "Lark"]

KNOWLEDGE = {
    "row": [
        (
            "What is a row?",
            "A row is a line of things set one beside another. Flowerpots, boxes, or lily pads can all make a row.",
        )
    ],
    "complement": [
        (
            "What does complement mean when two sounds complement each other?",
            "It means the sounds go nicely together. One sound does not have to copy the other to make the music fuller.",
        )
    ],
    "bee": [
        (
            "Why does a bee buzz?",
            "A bee buzzes because its wings beat very fast. The air shakes and makes the buzzing sound.",
        )
    ],
    "cricket": [
        (
            "How does a cricket make a chirping sound?",
            "A cricket makes its song by rubbing parts of its wings together. That rubbing makes the chirr-chirr sound.",
        )
    ],
    "frog": [
        (
            "Why do frogs croak?",
            "Frogs croak to call out to other frogs. Their voices can sound low and bouncy near water.",
        )
    ],
    "wren": [
        (
            "What is a wren?",
            "A wren is a very small bird with a lively voice. Even tiny birds can sing bright, clear songs.",
        )
    ],
    "flower": [
        (
            "Why do flower buds open?",
            "Buds open as the plant grows and conditions are right. Warmth, water, and time help the petals unfold.",
        )
    ],
    "transformation": [
        (
            "What is a transformation?",
            "A transformation is a change from one state into another. In this story world, a closed bud transforms into an open flower.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "row",
    "complement",
    "bee",
    "cricket",
    "frog",
    "wren",
    "flower",
    "transformation",
]


def explain_rejection(place_id: str, bloom_id: str, helper_id: str) -> str:
    if place_id not in PLACES:
        return f"(No story: unknown place '{place_id}'.)"
    if bloom_id not in BLOOMS:
        return f"(No story: unknown bloom '{bloom_id}'.)"
    if helper_id not in HELPERS:
        return f"(No story: unknown helper '{helper_id}'.)"
    place = PLACES[place_id]
    bloom = BLOOMS[bloom_id]
    if bloom_id not in place.supports_blooms:
        return (
            f"(No story: {bloom.bloom_label} does not belong in {place.label} here. "
            f"Pick a bloom that reasonably grows in that row.)"
        )
    if helper_id not in place.supports_helpers:
        return (
            f"(No story: a {HELPERS[helper_id].label} would not sensibly lead the song in {place.label} here. "
            f"Pick a helper that fits the place.)"
        )
    return (
        f"(No story: the sound of a {HELPERS[helper_id].label} does not complement a "
        f"{bloom.bloom_label} in this little world.)"
    )


def introduce(world: World, place: Place, bloom: Bloom, bud: Entity) -> None:
    world.say(
        f"In {place.row_phrase} stood {bud.id}, {bloom.phrase}, tucked between its neighbors."
    )
    world.say(place.morning_line)
    bud.memes["shy"] += 1
    bud.meters["closed"] += 1
    world.say(
        f"All along the row, little leaves nodded, but {bud.id} kept {bud.pronoun('possessive')} petals folded small."
    )


def longing(world: World, place: Place, bloom: Bloom, bud: Entity) -> None:
    world.say(
        f'Softly {bud.id} whispered, "I hear the morning row, yet I cannot ring {bloom.chime}."'
    )
    world.say("The wish to join the song made the little stem tremble.")
    bud.memes["hope"] += 1


def helper_arrives(world: World, helper_cfg: Helper, helper: Entity, bud: Entity) -> None:
    world.say(
        f"Then came {helper_cfg.phrase} with a {helper_cfg.arrive_sound}, {helper_cfg.arrive_sound} by the row."
    )
    helper.meters["singing"] += 1
    helper.memes["kindness"] += 1
    world.say(f'"{helper_cfg.speech}"')
    world.say(f'"{helper_cfg.reply}" said {bud.id}.')
    bud.meters["encouraged"] += 1
    bud.memes["hope"] += 1


def morning_touch(world: World, place: Place, bud: Entity) -> None:
    world.say(
        f"Just then {place.catalyst} touched the little bud."
    )
    bud.meters["warmed"] += 1
    propagate(world, narrate=True)


def duet(world: World, bloom: Bloom, helper_cfg: Helper, bud: Entity, helper: Entity) -> None:
    propagate(world, narrate=False)
    if world.facts.get("duet"):
        bud.meters["singing"] += 1
        world.say(
            f'{helper_cfg.song_sound}! sang the {helper_cfg.label}. "{bloom.chime}, {bloom.chime}!" rang {bud.id}.'
        )
        world.say(
            f"The two sounds did not match exactly, and that was the best part of all: one did complement the other."
        )
        world.say(
            f"Soon the whole row swayed together, and {bud.id} no longer felt small or left out."
        )


def closing_image(world: World, place: Place, bloom: Bloom, bud: Entity) -> None:
    world.say(
        f"When the bright morning settled over {place.label}, {bud.id} stood open as a {bloom.bloom_label}, "
        f"ringing {bloom.chime} into the day."
    )


def tell(place: Place, bloom_cfg: Bloom, helper_cfg: Helper, bud_name: str) -> World:
    world = World()
    bud = world.add(
        Entity(
            id=bud_name,
            kind="character",
            type="flower",
            label=bloom_cfg.bud_label,
            phrase=bloom_cfg.phrase,
            role="bud",
            tags=set(bloom_cfg.tags),
        )
    )
    helper = world.add(
        Entity(
            id=helper_cfg.label.capitalize(),
            kind="character",
            type=helper_cfg.type,
            label=helper_cfg.label,
            phrase=helper_cfg.phrase,
            role="helper",
            tags=set(helper_cfg.tags),
        )
    )
    chorus = world.add(Entity(id="chorus", type="chorus", label="the morning chorus"))

    world.facts.update(
        place=place,
        bloom_cfg=bloom_cfg,
        helper_cfg=helper_cfg,
        bud=bud,
        helper=helper,
        transformed=False,
        duet=False,
    )

    introduce(world, place, bloom_cfg, bud)
    longing(world, place, bloom_cfg, bud)

    world.para()
    helper_arrives(world, helper_cfg, helper, bud)
    morning_touch(world, place, bud)

    world.para()
    duet(world, bloom_cfg, helper_cfg, bud, helper)
    closing_image(world, place, bloom_cfg, bud)

    world.facts["joined"] = bud.memes["belonging"] >= THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    place: Place = world.facts["place"]
    bloom: Bloom = world.facts["bloom_cfg"]
    helper: Helper = world.facts["helper_cfg"]
    bud: Entity = world.facts["bud"]
    return [
        'Write a nursery-rhyme-style story that uses the words "complement" and "row" and includes dialogue, sound effects, and a transformation.',
        f"Tell a gentle morning tale where a shy bud named {bud.id} in {place.row_phrase} is encouraged by a {helper.label} and opens into a {bloom.bloom_label}.",
        f'Write a tiny musical story for a young child where one sound does not copy another but does complement it, and the ending proves the little one has changed.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    place: Place = world.facts["place"]
    bloom: Bloom = world.facts["bloom_cfg"]
    helper: Helper = world.facts["helper_cfg"]
    bud: Entity = world.facts["bud"]
    transformed = world.facts.get("transformed", False)
    joined = world.facts.get("joined", False)

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {bud.id}, a shy little bud in a row, and a kind {helper.label} who stopped to help. The story follows how {bud.id} changed when morning and encouragement came together.",
        ),
        (
            "Why was the little bud sad at first?",
            f"{bud.id} wanted to join the morning row but was still folded shut. That made {bud.pronoun('object')} feel small and left out while the day was beginning.",
        ),
        (
            f"What did the {helper.label} say?",
            f'The {helper.label} told {bud.id} not to droop and said its own sound would complement the bud\'s chime. That promise mattered because it turned the helper into a friend instead of just a passerby.',
        ),
    ]
    if transformed:
        qa.append(
            (
                f"How did {bud.id} transform?",
                f"{place.catalyst.capitalize()} touched the bud after the helper had encouraged it, and the folded petals opened. {bud.id} changed from a closed little bud into a {bloom.bloom_label}.",
            )
        )
    if joined:
        qa.append(
            (
                "What does it mean that the sounds complement each other?",
                f"It means the flower's {bloom.chime} and the helper's {helper.song_sound} sound good together without sounding the same. Their different notes made the row feel fuller and happier.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with {bud.id} standing open in the row and ringing {bloom.chime} into the morning. The final image shows that {bud.pronoun()} was no longer shy or shut away.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"row", "complement", "flower", "transformation"}
    tags |= set(world.facts["helper_cfg"].tags)
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, B, H) :- place(P), bloom(B), helper(H),
                  supports_bloom(P, B),
                  supports_helper(P, H),
                  complements(B, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for bloom_id in sorted(place.supports_blooms):
            lines.append(asp.fact("supports_bloom", place_id, bloom_id))
        for helper_id in sorted(place.supports_helpers):
            lines.append(asp.fact("supports_helper", place_id, helper_id))
    for bloom_id, bloom in BLOOMS.items():
        lines.append(asp.fact("bloom", bloom_id))
        for helper_id in sorted(bloom.compatible_helpers):
            lines.append(asp.fact("complements", bloom_id, helper_id))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
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
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        default_args = build_parser().parse_args([])
        random_case = resolve_params(default_args, random.Random(123))
        smoke_cases.append(random_case)
    except StoryError as err:
        rc = 1
        print(f"SMOKE FAIL: resolve_params crashed: {err}")

    try:
        for params in smoke_cases:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            emit(sample, trace=False, qa=False, header="")
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    except Exception as err:
        rc = 1
        print(f"SMOKE FAIL: ordinary generation crashed: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: a shy bud in a row, a musical helper, and a morning transformation."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--bloom", choices=sorted(BLOOMS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--bud-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.bloom and args.helper and not valid_combo(args.place, args.bloom, args.helper):
        raise StoryError(explain_rejection(args.place, args.bloom, args.helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.bloom is None or combo[1] == args.bloom)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        place_id = args.place or next(iter(PLACES))
        bloom_id = args.bloom or next(iter(BLOOMS))
        helper_id = args.helper or next(iter(HELPERS))
        raise StoryError(explain_rejection(place_id, bloom_id, helper_id))

    place_id, bloom_id, helper_id = rng.choice(sorted(combos))
    bud_name = args.bud_name or rng.choice(NAMES)
    return StoryParams(
        place=place_id,
        bloom=bloom_id,
        helper=helper_id,
        bud_name=bud_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.bloom not in BLOOMS:
        raise StoryError(f"(No story: unknown bloom '{params.bloom}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if not valid_combo(params.place, params.bloom, params.helper):
        raise StoryError(explain_rejection(params.place, params.bloom, params.helper))

    world = tell(
        place=PLACES[params.place],
        bloom_cfg=BLOOMS[params.bloom],
        helper_cfg=HELPERS[params.helper],
        bud_name=params.bud_name,
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
        print(f"{len(combos)} compatible (place, bloom, helper) combos:\n")
        for place_id, bloom_id, helper_id in combos:
            print(f"  {place_id:11} {bloom_id:12} {helper_id}")
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
            header = f"### {p.bud_name}: {p.bloom} in {p.place} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
