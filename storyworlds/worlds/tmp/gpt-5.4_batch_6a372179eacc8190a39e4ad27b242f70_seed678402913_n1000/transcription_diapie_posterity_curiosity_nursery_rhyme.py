#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/transcription_diapie_posterity_curiosity_nursery_rhyme.py
====================================================================================

A standalone story world about a curious child in a nursery, an odd old rhyme,
and a gentle effort to keep it for posterity.

The family has an old nursery rhyme written on some fragile keepsake. One line
contains the funny old baby-talk word "diapie", which sparks the child's
curiosity. The child wants to copy the rhyme before it fades, but reaches for a
drippy paintbrush that would blur the keepsake. A calm grown-up stops the risky
move, explains the old word, and helps the child make a safe transcription to
hang up in the nursery.

The reasonableness gate is small and explicit:
- not every copying method is safe for every source material
- only sensible methods are allowed
- the ASP twin mirrors that compatibility check exactly

Run it
------
python storyworlds/worlds/gpt-5.4/transcription_diapie_posterity_curiosity_nursery_rhyme.py
python storyworlds/worlds/gpt-5.4/transcription_diapie_posterity_curiosity_nursery_rhyme.py --source sampler --method tracing
python storyworlds/worlds/gpt-5.4/transcription_diapie_posterity_curiosity_nursery_rhyme.py --method paint_copy
python storyworlds/worlds/gpt-5.4/transcription_diapie_posterity_curiosity_nursery_rhyme.py --all --qa
python storyworlds/worlds/gpt-5.4/transcription_diapie_posterity_curiosity_nursery_rhyme.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Source:
    id: str
    label: str
    phrase: str
    material: str
    found: str
    odd_line: str
    meaning: str
    safe_pose: str
    tags: set[str] = field(default_factory=set)
    fragile: bool = True


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    verb: str
    detail: str
    sense: int
    safe_for: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Display:
    id: str
    label: str
    phrase: str
    place: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    source: str
    method: str
    display: str
    child: str
    gender: str
    caregiver: str
    trait: str
    seed: Optional[int] = None


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


def _r_smudge(world: World) -> list[str]:
    out: list[str] = []
    source = world.entities.get("source")
    child = world.entities.get("child")
    caregiver = world.entities.get("caregiver")
    if not source or not child or not caregiver:
        return out
    if source.meters["wet_touch"] < THRESHOLD:
        return out
    sig = ("smudge", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    source.meters["smudged"] += 1
    caregiver.memes["worry"] += 1
    child.memes["alarm"] += 1
    out.append("__smudge__")
    return out


def _r_preserve(world: World) -> list[str]:
    out: list[str] = []
    source = world.entities.get("source")
    copy_sheet = world.entities.get("copy")
    display = world.entities.get("display")
    child = world.entities.get("child")
    caregiver = world.entities.get("caregiver")
    if not source or not copy_sheet or not display or not child or not caregiver:
        return out
    if copy_sheet.meters["copied"] < THRESHOLD or display.meters["hung"] < THRESHOLD:
        return out
    sig = ("preserve", source.id, display.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    source.meters["preserved"] += 1
    child.memes["pride"] += 1
    caregiver.memes["relief"] += 1
    out.append("__preserved__")
    return out


CAUSAL_RULES = [
    Rule(name="smudge", tag="physical", apply=_r_smudge),
    Rule(name="preserve", tag="social", apply=_r_preserve),
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


SOURCES = {
    "sampler": Source(
        id="sampler",
        label="sampler",
        phrase="a stitched nursery sampler",
        material="cloth",
        found="above the little crib",
        odd_line='"Hush now, lambie, snug in diapie, moonbeams peep and sparrows sleep."',
        meaning="It was the family's old baby-talk word for a diaper.",
        safe_pose="laid it flat on the rocking-chair cushion so the stitches would not pull",
        tags={"sampler", "cloth", "nursery_rhyme", "diapie"},
        fragile=True,
    ),
    "card": Source(
        id="card",
        label="card",
        phrase="a faded rhyme card",
        material="paper",
        found="tucked inside the nursery songbook",
        odd_line='"Rock-a-ling baby, button your diapie, stars keep watch with a silver eye."',
        meaning="It was an old nursery nickname for a diaper, saved from when the family spoke to babies in soft silly sounds.",
        safe_pose="set it on the table under a small glass weight so the curling corners stayed still",
        tags={"paper", "card", "nursery_rhyme", "diapie"},
        fragile=True,
    ),
    "lid": Source(
        id="lid",
        label="music-box lid",
        phrase="a tiny music-box lid with carved words",
        material="wood",
        found="in the nursery drawer beside the blanket clips",
        odd_line='"Sleep, wee peeper, snug in diapie, hush till dawn comes skipping by."',
        meaning="It was an old family baby word for a diaper, carved there from long ago.",
        safe_pose="propped it under the lamp so every carved curl could be seen clearly",
        tags={"wood", "music_box", "nursery_rhyme", "diapie"},
        fragile=False,
    ),
}

METHODS = {
    "tracing": Method(
        id="tracing",
        label="tracing paper",
        phrase="a sheet of tracing paper and a soft pencil",
        verb="laid thin tracing paper above the rhyme and copied each curl slowly",
        detail="The paper floated light as onion skin, so the old words never had to bear a hard press.",
        sense=3,
        safe_for={"cloth", "paper", "wood"},
        tags={"tracing", "transcription"},
    ),
    "soft_pencil": Method(
        id="soft_pencil",
        label="soft pencil",
        phrase="a soft pencil and a clean notebook page",
        verb="looked carefully and wrote a neat copy in a clean notebook",
        detail="The pencil stayed dry and gentle, which suited a page that only needed watching and copying.",
        sense=3,
        safe_for={"paper", "wood"},
        tags={"pencil", "transcription"},
    ),
    "wax_rubbing": Method(
        id="wax_rubbing",
        label="wax rubbing",
        phrase="thin paper and a pale wax crayon",
        verb="rested thin paper on the carving and rubbed softly until the letters rose",
        detail="That only made sense on carved wood, where the shallow grooves could lift the shape without hurting anything.",
        sense=2,
        safe_for={"wood"},
        tags={"wax", "transcription"},
    ),
    "paint_copy": Method(
        id="paint_copy",
        label="paint copy",
        phrase="a wet paintbrush and a pot of blue paint",
        verb="dabbed wet paint right where the old words already were",
        detail="Wet paint is far too splashy for a fragile keepsake.",
        sense=1,
        safe_for=set(),
        tags={"paint"},
    ),
}

DISPLAYS = {
    "poster": Display(
        id="poster",
        label="poster",
        phrase="a bright nursery poster",
        place="by the window",
        ending="Soon the new poster bobbed by the window, and the old rhyme could be sung without touching the frail original.",
        tags={"poster", "posterity"},
    ),
    "bookpage": Display(
        id="bookpage",
        label="song page",
        phrase="a fresh page for the nursery songbook",
        place="inside the songbook basket",
        ending="Soon the fresh song page lay in the songbook basket, ready for many more bedtimes to come.",
        tags={"book", "posterity"},
    ),
    "frame": Display(
        id="frame",
        label="little frame",
        phrase="a little frame for the wall",
        place="above the toy chest",
        ending="Soon the little frame shone above the toy chest, and the copied rhyme looked ready to wink at tomorrow.",
        tags={"frame", "posterity"},
    ),
}

GIRL_NAMES = ["May", "Lila", "Nora", "Ivy", "Ella", "Mina", "Rose", "Ada"]
BOY_NAMES = ["Toby", "Milo", "Finn", "Leo", "Ben", "Owen", "Jude", "Max"]
TRAITS = ["curious", "bright-eyed", "careful", "wondering", "gentle", "eager"]


def compatible(source: Source, method: Method) -> bool:
    return method.sense >= SENSE_MIN and source.material in method.safe_for


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for source_id, source in SOURCES.items():
        for method_id, method in METHODS.items():
            if not compatible(source, method):
                continue
            for display_id in DISPLAYS:
                combos.append((source_id, method_id, display_id))
    return combos


def explain_rejection(source: Source, method: Method) -> str:
    if method.sense < SENSE_MIN:
        return (
            f"(No story: {method.label} is too messy and low-sense for preserving an old rhyme. "
            f"Choose a gentler method like tracing or a dry pencil transcription.)"
        )
    return (
        f"(No story: {method.label} is not a reasonable way to copy a {source.material} keepsake. "
        f"This world only allows methods that preserve the old rhyme while making a safe transcription.)"
    )


def predict_smudge(world: World) -> dict:
    sim = world.copy()
    source = sim.get("source")
    source.meters["wet_touch"] += 1
    propagate(sim, narrate=False)
    return {
        "smudged": source.meters["smudged"] >= THRESHOLD,
        "worry": sim.get("caregiver").memes["worry"],
    }


def introduce(world: World, child: Entity, source_cfg: Source) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} was a little {child.type} with a {next((t for t in child.traits if t), 'curious')} heart. "
        f"In the hush of the nursery, {child.pronoun()} noticed {source_cfg.phrase} {source_cfg.found}."
    )
    world.say(
        "The room was full of soft things and sleepy things: a moon lamp, a basket of books, and a chair that creaked in a kindly way."
    )


def discover(world: World, child: Entity, source_cfg: Source) -> None:
    source = world.get("source")
    source.meters["fading"] += 1
    world.say(
        f"On the old keepsake, one line still shone through the fading marks: {source_cfg.odd_line}"
    )
    world.say(
        f'"What is diapie?" {child.id} asked. "{child.pronoun().capitalize()} have never heard that word before."'
    )


def explain_old_word(world: World, caregiver: Entity, child: Entity, source_cfg: Source) -> None:
    caregiver.memes["tenderness"] += 1
    world.say(
        f'{caregiver.label_word.capitalize()} smiled and sat beside {child.id}. '
        f'"Diapie is a very old family baby word," {caregiver.pronoun()} said. "{source_cfg.meaning}"'
    )
    world.say(
        f'{child.id} leaned closer. Curiosity twinkled in {child.pronoun("possessive")} face like a candleless little light.'
    )


def wish_to_keep(world: World, child: Entity) -> None:
    child.memes["care"] += 1
    world.say(
        f'"Then let us keep it," said {child.id}. "If the old marks fade away, the song may slip."'
    )
    world.say(
        f'{child.pronoun().capitalize()} wanted a transcription for posterity, so even future babies could hear the same small rhyme.'
    )


def risky_reach(world: World, child: Entity, caregiver: Entity, source_cfg: Source) -> None:
    pred = predict_smudge(world)
    world.facts["predicted_smudge"] = pred["smudged"]
    world.facts["predicted_worry"] = pred["worry"]
    child.memes["impulse"] += 1
    caregiver.memes["care"] += 1
    world.say(
        f"But quick as a skip and bright as a wish, {child.id} reached for a drippy paintbrush. "
        f'"Blue paint will make the letters bold," {child.pronoun()} said.'
    )
    if pred["smudged"]:
        world.say(
            f'{caregiver.label_word.capitalize()} caught the little wrist before one wet bristle could touch the rhyme. '
            f'"No, my dear," {caregiver.pronoun()} said softly. "A wet brush would blur those old marks, and then the keepsake would lose part of its song."'
        )


def prepare_copy(world: World, caregiver: Entity, source_cfg: Source, method_cfg: Method) -> None:
    source = world.get("source")
    source.meters["secured"] += 1
    world.say(
        f'Instead, {caregiver.label_word} {source_cfg.safe_pose}.'
    )
    world.say(
        f'{caregiver.pronoun().capitalize()} brought {method_cfg.phrase}. {method_cfg.detail}'
    )


def transcribe(world: World, child: Entity, caregiver: Entity, method_cfg: Method) -> None:
    copy_sheet = world.get("copy")
    copy_sheet.meters["copied"] += 1
    child.memes["focus"] += 1
    caregiver.memes["pride"] += 1
    world.say(
        f"Then {child.id} and {caregiver.label_word} {method_cfg.verb}."
    )
    world.say(
        f"Line by line, loop by loop, the old nursery words found a fresh resting place."
    )


def display_copy(world: World, child: Entity, caregiver: Entity, display_cfg: Display) -> None:
    display = world.get("display")
    display.meters["hung"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When the work was done, they tucked the copy into {display_cfg.phrase} and set it {display_cfg.place}."
    )
    world.say(display_cfg.ending)
    world.say(
        f'That night, {child.id} whispered, "Diapie, diapie, moon so high," and the nursery seemed to keep the answer with a happy sigh.'
    )


def tell(
    source_cfg: Source,
    method_cfg: Method,
    display_cfg: Display,
    child_name: str = "May",
    gender: str = "girl",
    caregiver_type: str = "grandmother",
    trait: str = "curious",
) -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=gender,
        label=child_name,
        traits=[trait],
        role="child",
    ))
    caregiver = world.add(Entity(
        id="caregiver",
        kind="character",
        type=caregiver_type,
        label="the caregiver",
        role="caregiver",
    ))
    source = world.add(Entity(
        id="source",
        kind="thing",
        type=source_cfg.material,
        label=source_cfg.label,
        phrase=source_cfg.phrase,
        role="source",
        tags=set(source_cfg.tags),
    ))
    copy_sheet = world.add(Entity(
        id="copy",
        kind="thing",
        type="paper",
        label="copy",
        phrase="the fresh copy",
        role="copy",
    ))
    display = world.add(Entity(
        id="display",
        kind="thing",
        type=display_cfg.id,
        label=display_cfg.label,
        phrase=display_cfg.phrase,
        role="display",
        tags=set(display_cfg.tags),
    ))

    world.facts["child_name"] = child_name

    introduce(world, child, source_cfg)
    discover(world, child, source_cfg)

    world.para()
    explain_old_word(world, caregiver, child, source_cfg)
    wish_to_keep(world, child)
    risky_reach(world, child, caregiver, source_cfg)

    world.para()
    prepare_copy(world, caregiver, source_cfg, method_cfg)
    transcribe(world, child, caregiver, method_cfg)
    display_copy(world, child, caregiver, display_cfg)

    world.facts.update(
        child=child,
        caregiver=caregiver,
        source_cfg=source_cfg,
        source=source,
        method=method_cfg,
        display_cfg=display_cfg,
        copy=copy_sheet,
        preserved=source.meters["preserved"] >= THRESHOLD,
        copied=copy_sheet.meters["copied"] >= THRESHOLD,
        curious=child.memes["curiosity"] >= THRESHOLD,
        display_hung=display.meters["hung"] >= THRESHOLD,
        odd_word="diapie",
    )
    return world


KNOWLEDGE = {
    "transcription": [
        (
            "What is a transcription?",
            "A transcription is a careful written copy of words that were somewhere else before. People make one so the words can be read again without harming the original."
        )
    ],
    "posterity": [
        (
            "What does posterity mean?",
            "Posterity means the people who will come after us later on. If you save something for posterity, you are keeping it for future children and families."
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to know more. It often begins with a question and then leads you to look, listen, or ask gently."
        )
    ],
    "diapie": [
        (
            "Why might a family have a funny old word like diapie?",
            "Families sometimes keep baby-talk words that sound silly and sweet. A word like diapie can stay in a rhyme long after everyday speech has changed."
        )
    ],
    "tracing": [
        (
            "What is tracing paper for?",
            "Tracing paper is very thin paper that lets you see shapes underneath. It helps you copy carefully without pressing hard on the original."
        )
    ],
    "pencil": [
        (
            "Why is a soft pencil gentler than wet paint for old papers?",
            "A soft pencil stays dry, so it does not soak into an old page. Wet paint can spread, wrinkle, or blur fragile writing."
        )
    ],
    "wax": [
        (
            "What is a wax rubbing?",
            "A wax rubbing is made by laying paper over a raised or carved surface and rubbing with wax so the shape shows through. It works best on solid things like carved wood."
        )
    ],
    "sampler": [
        (
            "What is a sampler?",
            "A sampler is a piece of cloth with words or patterns stitched into it. Families sometimes save samplers because they hold memories as well as decoration."
        )
    ],
    "music_box": [
        (
            "What is a music box?",
            "A music box is a small box that plays a tune when it is wound or opened. Some have little pictures or words carved on them too."
        )
    ],
    "poster": [
        (
            "Why hang a copy on the wall instead of touching the old original each time?",
            "A copy can be looked at and sung from again and again. That keeps the fragile original safer."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "curiosity",
    "diapie",
    "transcription",
    "posterity",
    "tracing",
    "pencil",
    "wax",
    "sampler",
    "music_box",
    "poster",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    source_cfg = f["source_cfg"]
    display_cfg = f["display_cfg"]
    return [
        'Write a short nursery-rhyme-style story for a 3-to-5-year-old that includes the exact words "transcription", "diapie", and "posterity".',
        f"Tell a gentle story where a curious {child.type} finds {source_cfg.phrase}, asks about the odd word diapie, and makes a safe transcription with {caregiver.label_word}.",
        f"Write a child-facing story in a sing-song style where an old nursery rhyme is copied carefully and ends with the new copy becoming {display_cfg.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    source_cfg = f["source_cfg"]
    method = f["method"]
    display_cfg = f["display_cfg"]
    child_name = f["child_name"]
    caregiver_word = caregiver.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a curious little {child.type} named {child_name} and {child.pronoun('possessive')} {caregiver_word}. Together they cared for an old nursery rhyme."
        ),
        (
            "What made the child curious?",
            f"{child_name} found {source_cfg.phrase} and noticed the strange old word diapie in one line. That odd word made {child.pronoun('object')} want to ask questions and learn more."
        ),
        (
            "What did diapie mean in the story?",
            f"In the story, diapie was an old family baby-talk word for a diaper. The grown-up explained it so the rhyme would make sense again."
        ),
        (
            "Why did the grown-up stop the paintbrush?",
            f"{caregiver_word.capitalize()} stopped the wet paintbrush because it would have blurred the old rhyme. The child wanted to help, but a splashy tool could have damaged the keepsake."
        ),
        (
            "How did they make the transcription safely?",
            f"They used {method.phrase} and copied the rhyme carefully instead of painting on the original. That gave the family a fresh transcription while leaving the old keepsake safer."
        ),
        (
            "Why did they want the copy for posterity?",
            f"They wanted future children to know the little nursery song too. Making the copy for posterity meant the words could last even if the old original kept fading."
        ),
        (
            "How did the story end?",
            f"They placed the new copy as {display_cfg.phrase}, and the nursery felt ready to sing the rhyme again. The ending shows that curiosity led to care, not damage."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"curiosity", "diapie", "transcription", "posterity"}
    tags |= set(f["source_cfg"].tags)
    tags |= set(f["method"].tags)
    tags |= set(f["display_cfg"].tags)
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
    for ent in world.entities.values():
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
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        source="sampler",
        method="tracing",
        display="poster",
        child="May",
        gender="girl",
        caregiver="grandmother",
        trait="curious",
    ),
    StoryParams(
        source="card",
        method="soft_pencil",
        display="bookpage",
        child="Toby",
        gender="boy",
        caregiver="mother",
        trait="bright-eyed",
    ),
    StoryParams(
        source="lid",
        method="wax_rubbing",
        display="frame",
        child="Nora",
        gender="girl",
        caregiver="father",
        trait="wondering",
    ),
    StoryParams(
        source="lid",
        method="tracing",
        display="poster",
        child="Finn",
        gender="boy",
        caregiver="grandmother",
        trait="gentle",
    ),
]


ASP_RULES = r"""
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
compatible(Src, M) :- source(Src), method(M), material(Src, Mat), safe_for(M, Mat), sensible(M).
valid(Src, M, D) :- source(Src), method(M), display(D), compatible(Src, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("material", source_id, source.material))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        for material in sorted(method.safe_for):
            lines.append(asp.fact("safe_for", method_id, material))
    for display_id in DISPLAYS:
        lines.append(asp.fact("display", display_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
        print("MISMATCH in valid combinations:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=False, header="### smoke")
        if not sample.story or "diapie" not in sample.story or "transcription" not in sample.story or "posterity" not in sample.story:
            raise StoryError("(Smoke test failed: generated story missed required seed words.)")
        print("OK: smoke generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a curious child preserves an old nursery rhyme with a safe transcription."
    )
    ap.add_argument("--source", choices=sorted(SOURCES))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--display", choices=sorted(DISPLAYS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father", "grandmother"])
    ap.add_argument("--child")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.method:
        source = SOURCES[args.source]
        method = METHODS[args.method]
        if not compatible(source, method):
            raise StoryError(explain_rejection(source, method))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        source = SOURCES[args.source] if args.source else next(iter(SOURCES.values()))
        raise StoryError(explain_rejection(source, METHODS[args.method]))

    combos = [
        combo for combo in valid_combos()
        if (args.source is None or combo[0] == args.source)
        and (args.method is None or combo[1] == args.method)
        and (args.display is None or combo[2] == args.display)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    source_id, method_id, display_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = args.caregiver or rng.choice(["mother", "father", "grandmother"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        source=source_id,
        method=method_id,
        display=display_id,
        child=child,
        gender=gender,
        caregiver=caregiver,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.display not in DISPLAYS:
        raise StoryError(f"(Unknown display: {params.display})")
    source_cfg = SOURCES[params.source]
    method_cfg = METHODS[params.method]
    if not compatible(source_cfg, method_cfg):
        raise StoryError(explain_rejection(source_cfg, method_cfg))

    world = tell(
        source_cfg=source_cfg,
        method_cfg=method_cfg,
        display_cfg=DISPLAYS[params.display],
        child_name=params.child,
        gender=params.gender,
        caregiver_type=params.caregiver,
        trait=params.trait,
    )
    # Replace internal ids with display names in prose after simulation is done.
    story = world.render().replace("child", params.child).replace("caregiver", world.get("caregiver").label_word)
    return StorySample(
        params=params,
        story=story,
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
        print(f"{len(combos)} compatible (source, method, display) combos:\n")
        for source_id, method_id, display_id in combos:
            print(f"  {source_id:8} {method_id:12} {display_id}")
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
            header = f"### {p.child}: {p.source} with {p.method} -> {p.display}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
