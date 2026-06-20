#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/smudge_pleasant_jubilee_magic_transformation_bedtime_story.py
========================================================================================

A standalone story world for a gentle bedtime tale about a child, a small smudge,
and a Moon Jubilee transformation. The world models a simple, reasoned domain:

- a child is getting ready for bed,
- a beloved bedtime object has a smudge,
- the child worries it will not be ready for the Moon Jubilee,
- a calm helper suggests a pleasant, suitable way to clean it,
- then a fitting kind of magic transforms the object into a glowing bedtime version,
- and the ending image proves the room, the child, and the object have changed.

The world refuses mismatched combinations. A paper moon crown cannot sensibly be
scrubbed with a wet sponge, and a wooden music box does not turn into a cloud
pillow. The model prefers fewer plausible variants over weak coverage.

Run it
------
    python storyworlds/worlds/gpt-5.4/smudge_pleasant_jubilee_magic_transformation_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/smudge_pleasant_jubilee_magic_transformation_bedtime_story.py --item pillow --magic moonbeam
    python storyworlds/worlds/gpt-5.4/smudge_pleasant_jubilee_magic_transformation_bedtime_story.py --item crown --cleaning sponge
    python storyworlds/worlds/gpt-5.4/smudge_pleasant_jubilee_magic_transformation_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/smudge_pleasant_jubilee_magic_transformation_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/smudge_pleasant_jubilee_magic_transformation_bedtime_story.py --verify
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
    material: str = ""
    owner: Optional[str] = None
    role: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class ItemKind:
    id: str
    label: str
    phrase: str
    material: str
    place: str
    worry: str
    transformed_label: str
    transformed_phrase: str
    transformed_image: str
    cleanings: set[str] = field(default_factory=set)
    magics: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Cleaning:
    id: str
    label: str
    phrase: str
    gentle: bool
    works_on: set[str]
    action: str
    trace: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicKind:
    id: str
    label: str
    phrase: str
    works_on: set[str]
    glow: str
    spell_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperKind:
    id: str
    type: str
    phrase: str
    entry: str
    comfort: str


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


def _r_smudge_clears(world: World) -> list[str]:
    item = world.entities.get("item")
    if item is None:
        return []
    if item.meters["polished"] < THRESHOLD or item.meters["smudged"] < THRESHOLD:
        return []
    sig = ("smudge_clears", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["smudged"] = 0.0
    item.meters["clean"] += 1.0
    return []


def _r_ready(world: World) -> list[str]:
    item = world.entities.get("item")
    if item is None:
        return []
    if item.meters["clean"] < THRESHOLD:
        return []
    sig = ("ready", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["ready"] += 1.0
    child = world.entities.get("child")
    if child is not None:
        child.memes["hope"] += 1.0
        child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
    return []


def _r_transform(world: World) -> list[str]:
    item = world.entities.get("item")
    if item is None:
        return []
    if item.meters["ready"] < THRESHOLD or item.meters["enchanted"] < THRESHOLD:
        return []
    sig = ("transform", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["transformed"] += 1.0
    room = world.entities.get("room")
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if room is not None:
        room.meters["glow"] += 1.0
    if child is not None:
        child.memes["calm"] += 1.0
        child.memes["joy"] += 1.0
        child.memes["sleepy"] += 1.0
    if helper is not None:
        helper.memes["relief"] += 1.0
    return []


CAUSAL_RULES = [
    Rule("smudge_clears", "physical", _r_smudge_clears),
    Rule("ready", "mixed", _r_ready),
    Rule("transform", "magic", _r_transform),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
        old_count = len(world.fired)
        for rule in CAUSAL_RULES:
            rule.apply(world)
        if len(world.fired) > old_count:
            changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


ITEMS = {
    "pillow": ItemKind(
        "pillow",
        "pillow",
        "a little moon pillow",
        "cloth",
        "on the bed",
        "it would not look ready for the Moon Jubilee",
        "cloud pillow",
        "a silver-cloud pillow",
        "The cloud pillow puffed softly beneath the child's cheek.",
        cleanings={"cloth", "brush"},
        magics={"moonbeam", "lullaby"},
        tags={"pillow", "cloth"},
    ),
    "blanket": ItemKind(
        "blanket",
        "blanket",
        "a starry blanket",
        "cloth",
        "at the foot of the bed",
        "the sleepy parade might pass it by",
        "night-sky blanket",
        "a deep blue night-sky blanket",
        "The night-sky blanket floated down in one smooth, cozy fold.",
        cleanings={"cloth", "brush"},
        magics={"stardust", "lullaby"},
        tags={"blanket", "cloth"},
    ),
    "crown": ItemKind(
        "crown",
        "paper moon crown",
        "a paper moon crown",
        "paper",
        "beside the lamp",
        "the moon guests might think it had lost its shine",
        "silver moon crown",
        "a silver moon crown",
        "The silver moon crown gleamed on the pillow like a tiny moon of its own.",
        cleanings={"brush"},
        magics={"moonbeam", "stardust"},
        tags={"paper", "crown"},
    ),
    "music_box": ItemKind(
        "music_box",
        "music box",
        "a small wooden music box",
        "wood",
        "on the shelf",
        "its song would feel too dull for the Moon Jubilee",
        "starlight music box",
        "a starlight music box",
        "The starlight music box chimed one round, pleasant note and the room grew hushed.",
        cleanings={"cloth"},
        magics={"lullaby", "stardust"},
        tags={"wood", "music_box"},
    ),
}

CLEANINGS = {
    "cloth": Cleaning(
        "cloth",
        "soft cloth",
        "a soft cloth",
        True,
        {"cloth", "wood"},
        "rubbed the smudge in slow little circles",
        "The soft cloth lifted the smudge without hurting the object.",
        tags={"cloth_cleaning"},
    ),
    "brush": Cleaning(
        "brush",
        "velvet brush",
        "a velvet brush",
        True,
        {"cloth", "paper"},
        "swept the smudge away with feathery strokes",
        "The velvet brush whisked away the smudge very gently.",
        tags={"brush"},
    ),
    "sponge": Cleaning(
        "sponge",
        "wet sponge",
        "a wet sponge",
        False,
        {"cloth"},
        "dabbed at the smudge with a wet plop",
        "The wet sponge was only sensible for sturdy cloth things, not delicate ones.",
        tags={"sponge"},
    ),
}

MAGICS = {
    "moonbeam": MagicKind(
        "moonbeam",
        "moonbeam magic",
        "a moonbeam whisper",
        {"cloth", "paper"},
        "a pearl-white glow",
        '"Moonbeam bright, make bedtime light,"',
        tags={"moonbeam"},
    ),
    "stardust": MagicKind(
        "stardust",
        "stardust magic",
        "a pinch of stardust",
        {"cloth", "paper", "wood"},
        "a gentle spray of tiny lights",
        '"Stardust sweep, while children sleep,"',
        tags={"stardust"},
    ),
    "lullaby": MagicKind(
        "lullaby",
        "lullaby magic",
        "a humming lullaby",
        {"cloth", "wood"},
        "a warm blue shimmer",
        '"Hush and sway till dreams can play,"',
        tags={"lullaby"},
    ),
}

HELPERS = {
    "grandma": HelperKind(
        "grandma", "grandmother", "Grandma", "Grandma came in with a lamp of honey-colored light.", "Her voice made the whole room feel pleasant and slow."
    ),
    "mom": HelperKind(
        "mom", "mother", "Mom", "Mom peeked in and smiled from the doorway.", "Her voice made the whole room feel pleasant and slow."
    ),
    "grandpa": HelperKind(
        "grandpa", "grandfather", "Grandpa", "Grandpa padded in wearing soft slippers.", "His voice made the whole room feel pleasant and slow."
    ),
}

GIRL_NAMES = ["Luna", "Mira", "Tessa", "Nora", "Ella", "Ivy", "Ruby", "Zoe"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Ben", "Finn", "Leo", "Noah", "Eli"]
TRAITS = ["gentle", "sleepy", "curious", "quiet", "soft-hearted", "dreamy"]


def valid_combo(item: ItemKind, cleaning: Cleaning, magic: MagicKind) -> bool:
    return (
        item.material in cleaning.works_on
        and cleaning.id in item.cleanings
        and item.material in magic.works_on
        and magic.id in item.magics
    )


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for item_id, item in ITEMS.items():
        for cleaning_id, cleaning in CLEANINGS.items():
            for magic_id, magic in MAGICS.items():
                if valid_combo(item, cleaning, magic):
                    out.append((item_id, cleaning_id, magic_id))
    return out


def explain_rejection(item: ItemKind, cleaning: Cleaning, magic: MagicKind) -> str:
    if item.material not in cleaning.works_on or cleaning.id not in item.cleanings:
        return (
            f"(No story: {cleaning.phrase} is not a sensible way to clean {item.phrase}. "
            f"This world only allows gentle cleaning that suits the object's material.)"
        )
    if item.material not in magic.works_on or magic.id not in item.magics:
        return (
            f"(No story: {magic.label} does not fit {item.phrase}. "
            f"This transformation only works when the bedtime magic matches the object.)"
        )
    return "(No story: that combination does not belong to this bedtime world.)"


def predict_success(item: ItemKind, cleaning: Cleaning, magic: MagicKind) -> bool:
    return valid_combo(item, cleaning, magic)


def introduce(world: World, child: Entity, item: Entity, item_cfg: ItemKind) -> None:
    trait = next((t for t in child.tags if t), "")
    style = f"little {trait} {child.type}".strip()
    world.say(
        f"In a quiet room with curtains like folded shadows, {child.id} was a {style} getting ready for bed."
    )
    world.say(
        f"{item_cfg.phrase} rested {item_cfg.place}, because tonight was the Moon Jubilee, the shy little bedtime parade that only tidy, treasured things were said to see."
    )


def discover_smudge(world: World, child: Entity, item: Entity, item_cfg: ItemKind) -> None:
    child.memes["love"] += 1.0
    child.memes["worry"] += 1.0
    item.meters["smudged"] += 1.0
    world.say(
        f"When {child.pronoun()} picked it up, {child.pronoun()} found a gray smudge near one edge."
    )
    world.say(
        f"{child.id} looked at it and whispered that maybe {item_cfg.worry}."
    )


def helper_enters(world: World, helper: Entity, helper_cfg: HelperKind) -> None:
    world.say(helper_cfg.entry)
    world.say(helper_cfg.comfort)


def worry_and_plan(world: World, child: Entity, helper: Entity, item_cfg: ItemKind, cleaning: Cleaning) -> None:
    world.say(
        f'"Do you think the Moon Jubilee will still come?" {child.id} asked.'
    )
    world.say(
        f'{helper.label_word.capitalize()} sat beside {child.pronoun("object")} and said, "A small smudge does not spoil a good bedtime. We can care for it the pleasant way, with {cleaning.phrase}."'
    )


def clean_item(world: World, child: Entity, helper: Entity, item: Entity, cleaning: Cleaning) -> None:
    child.memes["care"] += 1.0
    helper.memes["care"] += 1.0
    item.meters["polished"] += 1.0
    world.say(
        f"Together they used {cleaning.phrase}. {child.id} {cleaning.action}, and {helper.label_word} guided the careful hands."
    )
    propagate(world, narrate=False)
    if item.meters["clean"] >= THRESHOLD:
        world.say(cleaning.trace)


def cast_magic(world: World, child: Entity, helper: Entity, item: Entity, item_cfg: ItemKind, magic: MagicKind) -> None:
    item.meters["enchanted"] += 1.0
    world.say(
        f"Then {helper.label_word} tipped back the curtain just enough for the night to look in. {magic.spell_line} {helper.pronoun()} sang, and {magic.glow} settled over {item_cfg.label}."
    )
    propagate(world, narrate=False)
    if item.meters["transformed"] >= THRESHOLD:
        item.label = item_cfg.transformed_label
        item.phrase = item_cfg.transformed_phrase
        world.say(
            f"The old shape gave a tiny shiver, and the {item_cfg.label} became {item_cfg.transformed_phrase}."
        )


def bedtime_end(world: World, child: Entity, helper: Entity, item_cfg: ItemKind) -> None:
    world.say(item_cfg.transformed_image)
    world.say(
        f'{child.id} climbed into bed while the Moon Jubilee seemed to pass in the silver hush beyond the window.'
    )
    world.say(
        f'Soon {child.pronoun()} was smiling in the dark, calm and sleepy at last, while {helper.label_word} tucked the blanket smooth and the room held its soft glow.'
    )


def tell(item_cfg: ItemKind, cleaning: Cleaning, magic: MagicKind,
         name: str = "Luna", gender: str = "girl", helper_kind: str = "grandma",
         trait: str = "dreamy") -> World:
    world = World()
    child = world.add(Entity(id=name, kind="character", type=gender, label=name, role="child", tags={trait}))
    helper_cfg = HELPERS[helper_kind]
    helper = world.add(Entity(id="Helper", kind="character", type=helper_cfg.type, label="the helper", role="helper"))
    room = world.add(Entity(id="room", type="room", label="bedroom"))
    item = world.add(Entity(
        id="item",
        type=item_cfg.id,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        material=item_cfg.material,
        owner=child.id,
        tags=set(item_cfg.tags),
    ))

    introduce(world, child, item, item_cfg)
    discover_smudge(world, child, item, item_cfg)

    world.para()
    helper_enters(world, helper, helper_cfg)
    worry_and_plan(world, child, helper, item_cfg, cleaning)

    world.para()
    clean_item(world, child, helper, item, cleaning)
    cast_magic(world, child, helper, item, item_cfg, magic)

    world.para()
    bedtime_end(world, child, helper, item_cfg)

    world.facts.update(
        child=child,
        helper=helper,
        helper_cfg=helper_cfg,
        item=item,
        item_cfg=item_cfg,
        cleaning=cleaning,
        magic=magic,
        transformed=item.meters["transformed"] >= THRESHOLD,
        smudge_cleared=item.meters["smudged"] < THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    item: str
    cleaning: str
    magic: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "smudge": [
        ("What is a smudge?",
         "A smudge is a small dirty mark or blur on something. It can often be cleaned away gently.")
    ],
    "moonbeam": [
        ("What is a moonbeam?",
         "A moonbeam is a shaft of moonlight. In bedtime stories, it often feels soft and magical.")
    ],
    "stardust": [
        ("What is stardust in a story?",
         "Stardust is imaginary sparkling dust from the stars. Story magic uses it to make things glow and change.")
    ],
    "lullaby": [
        ("What is a lullaby?",
         "A lullaby is a soft song sung to help someone rest. It makes the room feel calm and sleepy.")
    ],
    "transformation": [
        ("What does transformation mean?",
         "Transformation means something changes into a new form. In a magic story, the change can happen in a glow or shimmer.")
    ],
    "jubilee": [
        ("What is a jubilee?",
         "A jubilee is a happy celebration. In this bedtime world, the Moon Jubilee is a gentle nighttime parade.")
    ],
    "pillow": [
        ("What is a pillow for?",
         "A pillow supports your head when you lie down. A soft pillow helps bedtime feel comfortable.")
    ],
    "blanket": [
        ("What does a blanket do?",
         "A blanket keeps you warm and cozy. It can make a bed feel safe and snug.")
    ],
    "crown": [
        ("What is a crown?",
         "A crown is something worn on the head like a sign of honor or play. A paper crown is light and delicate.")
    ],
    "music_box": [
        ("What is a music box?",
         "A music box is a small box that plays a tune. Its quiet notes can make bedtime feel peaceful.")
    ],
    "gentle_cleaning": [
        ("Why should delicate things be cleaned gently?",
         "Delicate things can bend, tear, or wear out if you scrub them too hard. Gentle cleaning helps them stay safe while the dirt comes off.")
    ],
}
KNOWLEDGE_ORDER = [
    "smudge", "jubilee", "transformation", "moonbeam", "stardust", "lullaby",
    "pillow", "blanket", "crown", "music_box", "gentle_cleaning",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    item_cfg = f["item_cfg"]
    cleaning = f["cleaning"]
    magic = f["magic"]
    return [
        'Write a bedtime story for a 3-to-5-year-old that includes the words "smudge", "pleasant", and "jubilee".',
        f"Tell a gentle magical bedtime story where {child.id} finds a smudge on {item_cfg.phrase}, cleans it with {cleaning.phrase}, and sees a transformation by {magic.label}.",
        f"Write a soft, sleepy story about the Moon Jubilee, a treasured bedtime object, and a pleasant bit of magic that turns worry into calm.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper_cfg = f["helper_cfg"]
    item_cfg = f["item_cfg"]
    cleaning = f["cleaning"]
    magic = f["magic"]
    item = f["item"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who was getting ready for bed, and {helper_cfg.phrase}, who came to help. The story also centers on {item_cfg.phrase}."
        ),
        (
            f"Why was {child.id} worried?",
            f"{child.id} saw a smudge on {item_cfg.phrase} and worried it would not feel ready for the Moon Jubilee. The worry came from loving the object and wanting it to be part of the bedtime celebration."
        ),
        (
            f"What did {helper_cfg.phrase} tell {child.id} to do?",
            f"{helper_cfg.phrase} said they could care for the object in a pleasant, gentle way with {cleaning.phrase}. That answer calmed the worry because it gave {child.id} a safe way to help."
        ),
        (
            "How did the smudge get fixed?",
            f"They used {cleaning.phrase}, and {child.id} cleaned it carefully until the smudge was gone. The cleaning worked because it suited the object and was gentle enough not to harm it."
        ),
    ]
    if f["transformed"]:
        qa.append((
            "What transformation happened?",
            f"After the cleaning, {magic.label} settled over the object and changed it into {item.phrase}. The transformation happened once the object was clean and ready for bedtime magic."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with {child.id} calm and sleepy in bed while the room glowed softly. The transformed object showed that the worry had turned into comfort."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"smudge", "jubilee", "transformation", "gentle_cleaning"}
    tags |= set(f["magic"].tags)
    tags |= set(f["item_cfg"].tags)
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
        if ent.material:
            bits.append(f"material={ent.material}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("pillow", "cloth", "moonbeam", "Luna", "girl", "grandma", "dreamy"),
    StoryParams("blanket", "brush", "stardust", "Milo", "boy", "mom", "quiet"),
    StoryParams("crown", "brush", "moonbeam", "Nora", "girl", "grandpa", "curious"),
    StoryParams("music_box", "cloth", "lullaby", "Theo", "boy", "grandma", "gentle"),
]


ASP_RULES = r"""
valid_cleaning(I, C) :- item(I), cleaning(C), item_material(I, M), works_on(C, M), allows_cleaning(I, C).
valid_magic(I, G)    :- item(I), magic(G), item_material(I, M), magic_works_on(G, M), allows_magic(I, G).
valid(I, C, G)       :- valid_cleaning(I, C), valid_magic(I, G).

transformation_ready :- chosen_item(I), chosen_cleaning(C), valid_cleaning(I, C).
transformation_done  :- chosen_item(I), chosen_cleaning(C), chosen_magic(G), valid(I, C, G).

outcome(success) :- transformation_done.
outcome(fail)    :- not transformation_done.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("item_material", item_id, item.material))
        for cid in sorted(item.cleanings):
            lines.append(asp.fact("allows_cleaning", item_id, cid))
        for gid in sorted(item.magics):
            lines.append(asp.fact("allows_magic", item_id, gid))
    for cid, cleaning in CLEANINGS.items():
        lines.append(asp.fact("cleaning", cid))
        for mat in sorted(cleaning.works_on):
            lines.append(asp.fact("works_on", cid, mat))
    for gid, magic in MAGICS.items():
        lines.append(asp.fact("magic", gid))
        for mat in sorted(magic.works_on):
            lines.append(asp.fact("magic_works_on", gid, mat))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_cleaning", params.cleaning),
        asp.fact("chosen_magic", params.magic),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    for params in CURATED:
        expected = "success"
        got = asp_outcome(params)
        if got != expected:
            rc = 1
            print(f"MISMATCH outcome for {params}: asp={got} python={expected}")

    # Smoke test normal generation.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime story world about a smudge, a pleasant fix, and a Moon Jubilee transformation."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cleaning", choices=CLEANINGS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.cleaning and args.magic:
        item = ITEMS[args.item]
        cleaning = CLEANINGS[args.cleaning]
        magic = MAGICS[args.magic]
        if not valid_combo(item, cleaning, magic):
            raise StoryError(explain_rejection(item, cleaning, magic))

    combos = [
        combo for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.cleaning is None or combo[1] == args.cleaning)
        and (args.magic is None or combo[2] == args.magic)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, cleaning_id, magic_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(sorted(HELPERS))
    trait = rng.choice(TRAITS)
    return StoryParams(item_id, cleaning_id, magic_id, name, gender, helper, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        ITEMS[params.item],
        CLEANINGS[params.cleaning],
        MAGICS[params.magic],
        params.name,
        params.gender,
        params.helper,
        params.trait,
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
        print(f"{len(combos)} compatible (item, cleaning, magic) combos:\n")
        for item, cleaning, magic in combos:
            print(f"  {item:10} {cleaning:8} {magic}")
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
            header = f"### {p.name}: {p.item} with {p.cleaning} and {p.magic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
