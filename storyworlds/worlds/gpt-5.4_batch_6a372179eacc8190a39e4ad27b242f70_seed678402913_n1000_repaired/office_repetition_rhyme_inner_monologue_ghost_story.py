#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/office_repetition_rhyme_inner_monologue_ghost_story.py
=================================================================================

A standalone storyworld for a gentle ghost story set in an office after hours.

Small domain
------------
A child stays in an office while a parent finishes one last job. The child loses
a paper keepsake. Then the office begins to whisper with repeating sounds:
tap-tap, blink-blink, swish-swish. The child wonders, in an inner monologue,
whether a ghost is near. In this world, there really is a small, friendly office
ghost, and the sounds are clues. Depending on the child's choice and courage,
the ghost is followed alone or together with the parent, and the lost item is
found.

The style stays close to a child-facing ghost story:
- office setting
- repetition in the sound motifs and some refrain lines
- rhyme in short paired phrases
- inner monologue during the fearful turn

Run it
------
python storyworlds/worlds/gpt-5.4/office_repetition_rhyme_inner_monologue_ghost_story.py
python storyworlds/worlds/gpt-5.4/office_repetition_rhyme_inner_monologue_ghost_story.py --area copy_room --sign copier_blink
python storyworlds/worlds/gpt-5.4/office_repetition_rhyme_inner_monologue_ghost_story.py --response run_lights
python storyworlds/worlds/gpt-5.4/office_repetition_rhyme_inner_monologue_ghost_story.py --all --qa
python storyworlds/worlds/gpt-5.4/office_repetition_rhyme_inner_monologue_ghost_story.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
class Area:
    id: str
    label: str
    phrase: str
    shadow: str
    hide_spot: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Sign:
    id: str
    label: str
    sound: str
    rhyme: str
    visual: str
    spooky: int
    clue_place: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LostItem:
    id: str
    label: str
    phrase: str
    use_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    label: str
    sense: int
    courage: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    area: str
    sign: str
    item: str
    response: str
    name: str
    gender: str
    parent: str
    trait: str
    note_kind: str
    seed: Optional[int] = None


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


def propagate(world: World) -> None:
    hero = world.get("hero")
    office = world.get("office")
    ghost = world.get("ghost")
    item = world.get("item")

    if ghost.meters["signaling"] >= THRESHOLD and ("spook",) not in world.fired:
        world.fired.add(("spook",))
        office.meters["spooky"] += ghost.attrs.get("spooky", 1)
        hero.memes["fear"] += 1
        hero.memes["wonder"] += 1

    if item.meters["found"] >= THRESHOLD and ("relief",) not in world.fired:
        world.fired.add(("relief",))
        hero.memes["relief"] += 1
        hero.memes["gratitude"] += 1
        hero.memes["fear"] = 0.0


AREAS = {
    "copy_room": Area(
        id="copy_room",
        label="copy room",
        phrase="the copy room at the end of the office",
        shadow="the glass door looked gray in the late light",
        hide_spot="under the copier tray",
        affords={"copier_blink", "paper_swish"},
        tags={"office", "copier"},
    ),
    "cubicles": Area(
        id="cubicles",
        label="cubicles",
        phrase="the row of sleepy cubicles",
        shadow="the tall walls made little squares of shadow",
        hide_spot="beside a rolling chair",
        affords={"chair_spin", "sticky_note_fall"},
        tags={"office", "desk"},
    ),
    "file_room": Area(
        id="file_room",
        label="file room",
        phrase="the narrow file room",
        shadow="the drawers stood in a quiet silver line",
        hide_spot="behind the bottom file drawer",
        affords={"drawer_tap", "paper_swish"},
        tags={"office", "files"},
    ),
}

SIGNS = {
    "copier_blink": Sign(
        id="copier_blink",
        label="copier blink",
        sound="blink-blink",
        rhyme="glow and show",
        visual="the green copier button blinked in the dark",
        spooky=3,
        clue_place="the copier tray",
        tags={"copier", "light"},
    ),
    "paper_swish": Sign(
        id="paper_swish",
        label="paper swish",
        sound="swish-swish",
        rhyme="slide and guide",
        visual="one sheet of paper kept lifting and settling again",
        spooky=2,
        clue_place="a paper stack by the wall",
        tags={"paper", "office"},
    ),
    "chair_spin": Sign(
        id="chair_spin",
        label="chair spin",
        sound="creak-creak",
        rhyme="turn and learn",
        visual="a rolling chair turned a tiny half-circle by itself",
        spooky=2,
        clue_place="the chair wheels",
        tags={"chair", "desk"},
    ),
    "sticky_note_fall": Sign(
        id="sticky_note_fall",
        label="sticky note fall",
        sound="flip-flip",
        rhyme="drift and gift",
        visual="three sticky notes floated down in a crooked little trail",
        spooky=2,
        clue_place="a desk edge",
        tags={"paper", "desk"},
    ),
    "drawer_tap": Sign(
        id="drawer_tap",
        label="drawer tap",
        sound="tap-tap",
        rhyme="peek and seek",
        visual="the bottom file drawer shivered and tapped once, then twice",
        spooky=3,
        clue_place="the lowest drawer handle",
        tags={"files", "tap"},
    ),
}

ITEMS = {
    "drawing": LostItem(
        id="drawing",
        label="drawing",
        phrase="a moon-and-stars drawing",
        use_text="to show the parent on the drive home",
        tags={"paper", "drawing"},
    ),
    "badge": LostItem(
        id="badge",
        label="visitor badge",
        phrase="a paper visitor badge with a bright blue star",
        use_text="because wearing it made the child feel important",
        tags={"paper", "badge"},
    ),
    "note": LostItem(
        id="note",
        label="thank-you note",
        phrase="a folded thank-you note for the parent",
        use_text="to tuck beside the parent's keyboard as a surprise",
        tags={"paper", "note"},
    ),
}

RESPONSES = {
    "follow_whisper": Response(
        id="follow_whisper",
        label="follow the whisper",
        sense=3,
        courage=2,
        text="took a breath and followed the strange little clue",
        qa_text="followed the ghostly clue",
        tags={"brave"},
    ),
    "get_parent": Response(
        id="get_parent",
        label="get the parent",
        sense=3,
        courage=1,
        text="hurried back for a grown-up before following the sound",
        qa_text="asked a grown-up to come along",
        tags={"help"},
    ),
    "run_lights": Response(
        id="run_lights",
        label="run to the lights",
        sense=1,
        courage=0,
        text="ran for the bright front lights and stopped looking",
        qa_text="ran away from the clue",
        tags={"fear"},
    ),
}

NOTE_KINDS = {
    "smile": "a sticky note with a smiling face",
    "thanks": 'a sticky note that said "Thank you"',
    "moon": "a sticky note with a tiny silver moon",
}

TRAIT_BONUS = {
    "curious": 2,
    "steady": 2,
    "careful": 1,
    "dreamy": 1,
    "timid": 0,
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Finn", "Noah", "Eli", "Theo"]
TRAITS = sorted(TRAIT_BONUS)


def area_supports(area: Area, sign: Sign) -> bool:
    return sign.id in area.affords


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for area_id, area in AREAS.items():
        for sign_id, sign in SIGNS.items():
            if not area_supports(area, sign):
                continue
            for item_id in ITEMS:
                combos.append((area_id, sign_id, item_id))
    return combos


def bravery_total(trait: str, response: Response) -> int:
    return TRAIT_BONUS[trait] + response.courage


def outcome_of(params: StoryParams) -> str:
    response = RESPONSES[params.response]
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(response.id))
    if not area_supports(AREAS[params.area], SIGNS[params.sign]):
        raise StoryError(explain_rejection(AREAS[params.area], SIGNS[params.sign]))
    if response.id == "get_parent":
        return "together"
    sign = SIGNS[params.sign]
    return "alone" if bravery_total(params.trait, response) >= sign.spooky else "together"


def explain_rejection(area: Area, sign: Sign) -> str:
    return (
        f"(No story: {sign.label} does not belong in the {area.label}. "
        f"That office area cannot honestly make that repeating clue.)"
    )


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def introduce(world: World, hero: Entity, parent: Entity, area: Area) -> None:
    world.say(
        f"One evening, {hero.id} waited in an office while {hero.pronoun('possessive')} "
        f"{parent.label_word} finished one last job. Hush in the office, hush in the hall: "
        f"the phones were asleep, the desks stood tall."
    )
    world.say(
        f"They were near {area.phrase}, and {area.shadow}. Even the paper seemed to be listening."
    )


def prize_setup(world: World, hero: Entity, item: Entity, item_cfg: LostItem) -> None:
    world.say(
        f"{hero.id} carried {item_cfg.phrase} everywhere in both hands. "
        f"{hero.pronoun().capitalize()} had made it {item_cfg.use_text}."
    )


def lose_item(world: World, hero: Entity, item: Entity, area: Area) -> None:
    item.meters["lost"] += 1
    hero.memes["sadness"] += 1
    world.say(
        f"But when {hero.id} looked down again, the {item.label} was gone. "
        f"It had slipped away somewhere near {area.hide_spot}."
    )
    world.say(
        f"{hero.id} searched once, then twice. Hush in the office, hush in the hall."
    )


def first_sign(world: World, hero: Entity, ghost: Entity, sign: Sign) -> None:
    ghost.meters["signaling"] += 1
    ghost.attrs["spooky"] = sign.spooky
    propagate(world)
    world.say(
        f"Then came {sign.sound}... {sign.sound}. {sign.visual}. "
        f"It was not loud, but it was clear."
    )
    world.say(
        f"{hero.id} stood very still. {sign.sound}, {sign.sound} -- {sign.rhyme}."
    )


def inner_monologue(world: World, hero: Entity, area: Area, sign: Sign) -> None:
    fear = hero.memes["fear"]
    if fear >= THRESHOLD:
        world.say(
            f'{hero.id} thought, "Maybe this office has a ghost. Maybe the ghost is close. '
            f'{sign.sound} in the dark, and my heart goes thump-thump in the dark."'
        )
        world.say(
            f'{hero.id} thought again, "If I peek, will I find a fright? Or will a small light '
            f'make things right?"'
        )
    else:
        world.say(
            f'{hero.id} wondered, "What is making that little sound in {area.label}? '
            f'Why does it feel as if someone wants me to look?"'
        )


def choose_response(world: World, hero: Entity, parent: Entity, response: Response) -> None:
    if response.id == "follow_whisper":
        hero.memes["courage"] += 1
        world.say(
            f"{hero.id} {response.text}. Step by step, tip and toe, slow and low."
        )
    elif response.id == "get_parent":
        hero.memes["trust"] += 1
        world.say(
            f"{hero.id} {response.text}. {parent.label_word.capitalize()} set down the last folder at once."
        )
    else:
        raise StoryError(explain_response(response.id))


def reveal_alone(world: World, hero: Entity, ghost: Entity, item: Entity, area: Area, sign: Sign) -> None:
    item.meters["found"] += 1
    ghost.meters["seen"] += 1
    propagate(world)
    world.say(
        f"At {sign.clue_place}, a pale little shape rose from the office gloom. "
        f"It was no bigger than a coat, with paper-white cuffs and a soft blue glow."
    )
    world.say(
        f"It pointed one see-through finger toward {area.hide_spot}, and there lay the {item.label}."
    )
    world.say(
        f'The ghost gave the tiniest nod, as if to say, "There it is. No scare, just care."'
    )


def reveal_together(
    world: World,
    hero: Entity,
    parent: Entity,
    ghost: Entity,
    item: Entity,
    area: Area,
    sign: Sign,
) -> None:
    item.meters["found"] += 1
    ghost.meters["seen"] += 1
    hero.memes["trust"] += 1
    propagate(world)
    world.say(
        f"Together they followed the sound to {sign.clue_place}. There, in the dim office hush, "
        f"a small ghost shimmered like moonlight on clean paper."
    )
    world.say(
        f"It tipped its head toward {area.hide_spot}. {parent.label_word.capitalize()} reached down, "
        f"and the {item.label} was there."
    )
    world.say(
        f'"Well," {parent.label_word} whispered, "that was a very helpful ghost."'
    )


def ending(world: World, hero: Entity, parent: Entity, ghost: Entity, item: Entity, note_text: str, outcome: str) -> None:
    hero.memes["gratitude"] += 1
    world.say(
        f"{hero.id} hugged the {item.label} to {hero.pronoun('possessive')} chest so hard the paper softly crackled."
    )
    if outcome == "alone":
        world.say(
            f"When {hero.pronoun()} turned back, the little ghost was already fading, glow by glow, slow by slow."
        )
    else:
        world.say(
            f"The ghost gave one more shy blink, then melted into the office shadows as quietly as dust in moonlight."
        )
    world.say(
        f"Before they left, {hero.id} placed {note_text} on the nearest desk. "
        f"After that, the office did not feel empty. It felt watched over."
    )


def tell(
    area: Area,
    sign: Sign,
    item_cfg: LostItem,
    response: Response,
    name: str,
    gender: str,
    parent_type: str,
    trait: str,
    note_kind: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=name, phrase=name, role="hero"))
    hero.attrs["name"] = name
    hero.attrs["trait"] = trait
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    office = world.add(Entity(id="office", type="place", label="office", phrase="the office", role="office"))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="ghost", phrase="a little office ghost", role="ghost"))
    item = world.add(Entity(id="item", type="paper", label=item_cfg.label, phrase=item_cfg.phrase, role="item"))

    world.facts["area"] = area
    world.facts["sign"] = sign
    world.facts["item_cfg"] = item_cfg
    world.facts["response"] = response
    world.facts["note_text"] = NOTE_KINDS[note_kind]
    world.facts["hero_name"] = name
    world.facts["trait"] = trait

    introduce(world, hero, parent, area)
    prize_setup(world, hero, item, item_cfg)
    world.para()

    lose_item(world, hero, item, area)
    first_sign(world, hero, ghost, sign)
    inner_monologue(world, hero, area, sign)
    world.para()

    choose_response(world, hero, parent, response)
    outcome = "together" if response.id == "get_parent" else (
        "alone" if bravery_total(trait, response) >= sign.spooky else "together"
    )
    if outcome == "alone":
        reveal_alone(world, hero, ghost, item, area, sign)
    else:
        reveal_together(world, hero, parent, ghost, item, area, sign)
    world.para()

    ending(world, hero, parent, ghost, item, NOTE_KINDS[note_kind], outcome)

    world.facts.update(
        hero=hero,
        parent=parent,
        ghost=ghost,
        office=office,
        item=item,
        outcome=outcome,
        found=item.meters["found"] >= THRESHOLD,
        spooky=office.meters["spooky"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    area = world.facts["area"]
    sign = world.facts["sign"]
    item = world.facts["item_cfg"]
    name = world.facts["hero_name"]
    outcome = world.facts["outcome"]
    ending = "finds the lost paper with help from a friendly office ghost"
    if outcome == "alone":
        ending = "finds the lost paper by bravely following a friendly office ghost alone"
    return [
        'Write a child-friendly ghost story set in an office after hours. Use repetition, rhyme, and inner monologue.',
        f'Write a gentle ghost story where {name} loses {item.phrase} near the {area.label}, hears "{sign.sound}" repeated in the dark, and {ending}.',
        f'Write a short story with the word "office" that repeats a sound like "{sign.sound}" and makes the spooky part turn kind at the end.',
    ]


KNOWLEDGE = {
    "office": [
        (
            "What is an office?",
            "An office is a place where grown-ups do desk jobs, answer phones, write on computers, and keep papers in order.",
        )
    ],
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story with a spooky feeling and something mysterious that seems to move or appear in the dark.",
        )
    ],
    "copier": [
        (
            "What does a copier do?",
            "A copier makes paper copies of a page. In an office, it often hums and blinks when it is working.",
        )
    ],
    "files": [
        (
            "What is a file drawer for?",
            "A file drawer holds papers in folders so people can find them later.",
        )
    ],
    "sticky": [
        (
            "What is a sticky note?",
            "A sticky note is a small piece of paper with a strip of glue on the back, so you can leave a quick message.",
        )
    ],
    "badge": [
        (
            "What is a visitor badge?",
            "A visitor badge shows that someone is allowed to be in a building for a little while.",
        )
    ],
    "drawing": [
        (
            "Why do children keep special drawings carefully?",
            "A special drawing can hold a memory or a feeling, so losing it can feel important even though it is only paper.",
        )
    ],
}

KNOWLEDGE_ORDER = ["office", "ghost", "copier", "files", "sticky", "badge", "drawing"]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    area = world.facts["area"]
    sign = world.facts["sign"]
    item_cfg = world.facts["item_cfg"]
    outcome = world.facts["outcome"]
    name = hero.attrs["name"]
    pw = parent.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, {name}'s {pw}, and a little office ghost. The story happens in an office after hours, when everything feels extra quiet.",
        ),
        (
            f"What did {name} lose?",
            f"{name} lost {item_cfg.phrase}. It mattered because {hero.pronoun()} wanted to keep it safe and share it later.",
        ),
        (
            f"What made the office feel spooky?",
            f"The office was dark and quiet, and then the repeating sound {sign.sound} began. That rhythm made the silence feel alive, as if someone hidden was trying to speak.",
        ),
        (
            f"What was {name} thinking during the scary part?",
            f"{name} wondered if there was really a ghost in the office. The inner monologue shows fear first, but it also shows curiosity pulling {hero.pronoun('object')} forward.",
        ),
    ]
    if outcome == "alone":
        qa.append(
            (
                f"How did {name} find the {item_cfg.label}?",
                f"{name} followed the clue alone and found a friendly office ghost waiting near {sign.clue_place}. The ghost pointed toward {area.hide_spot}, which is where the lost {item_cfg.label} had slipped.",
            )
        )
    else:
        qa.append(
            (
                f"How did {name} and {name}'s {pw} find the {item_cfg.label}?",
                f"{name} chose to bring a grown-up along, and together they followed the ghostly clue. That made the moment feel safer, and the helpful ghost showed them exactly where the {item_cfg.label} was hiding.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the lost paper safely back in {name}'s hands and a thank-you note left behind for the ghost. The last image proves the office changed from a frightening place into a kindly, watchful one.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"office", "ghost"}
    item_cfg = world.facts["item_cfg"]
    area = world.facts["area"]
    sign = world.facts["sign"]

    if "copier" in area.tags or "copier" in sign.tags:
        tags.add("copier")
    if "files" in area.tags or "files" in sign.tags:
        tags.add("files")
    if sign.id == "sticky_note_fall" or world.facts["note_text"]:
        tags.add("sticky")
    if item_cfg.id == "badge":
        tags.add("badge")
    if item_cfg.id == "drawing":
        tags.add("drawing")

    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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


CURATED = [
    StoryParams(
        area="copy_room",
        sign="copier_blink",
        item="drawing",
        response="follow_whisper",
        name="Lily",
        gender="girl",
        parent="mother",
        trait="steady",
        note_kind="thanks",
    ),
    StoryParams(
        area="file_room",
        sign="drawer_tap",
        item="badge",
        response="get_parent",
        name="Ben",
        gender="boy",
        parent="father",
        trait="careful",
        note_kind="smile",
    ),
    StoryParams(
        area="cubicles",
        sign="sticky_note_fall",
        item="note",
        response="follow_whisper",
        name="Maya",
        gender="girl",
        parent="mother",
        trait="timid",
        note_kind="moon",
    ),
    StoryParams(
        area="cubicles",
        sign="chair_spin",
        item="drawing",
        response="follow_whisper",
        name="Theo",
        gender="boy",
        parent="father",
        trait="curious",
        note_kind="thanks",
    ),
]


ASP_RULES = r"""
valid(A, S, I) :- area(A), sign(S), item(I), affords(A, S).
sensible(R) :- response(R), sense(R, V), sense_min(M), V >= M.

trait_score(T, V) :- trait_bonus(T, V).
bravery(V) :- chosen_trait(T), trait_score(T, Tv), chosen_response(R), courage(R, Rc), V = Tv + Rc.
needed(V)  :- chosen_sign(S), spooky(S, V).

outcome(together) :- chosen_response(get_parent).
outcome(alone)    :- chosen_response(follow_whisper), bravery(B), needed(N), B >= N.
outcome(together) :- chosen_response(follow_whisper), bravery(B), needed(N), B < N.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for area_id, area in AREAS.items():
        lines.append(asp.fact("area", area_id))
        for sign_id in sorted(area.affords):
            lines.append(asp.fact("affords", area_id, sign_id))
    for sign_id, sign in SIGNS.items():
        lines.append(asp.fact("sign", sign_id))
        lines.append(asp.fact("spooky", sign_id, sign.spooky))
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("courage", response_id, response.courage))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for trait, bonus in TRAIT_BONUS.items():
        lines.append(asp.fact("trait_bonus", trait, bonus))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_sign", params.sign),
            asp.fact("chosen_response", params.response),
            asp.fact("chosen_trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story or not sample.story.strip():
        raise StoryError("Smoke test failed: generated story is empty.")
    if "office" not in sample.story.lower():
        raise StoryError("Smoke test failed: generated story does not mention the office.")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        emit(sample, trace=False, qa=False, header="")
    if not buf.getvalue().strip():
        raise StoryError("Smoke test failed: emit() produced no output.")


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if py_valid == clingo_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - py_valid:
            print("  only in clingo:", sorted(clingo_valid - py_valid))
        if py_valid - clingo_valid:
            print("  only in python:", sorted(py_valid - clingo_valid))

    py_sensible = {r.id for r in sensible_responses()}
    clingo_sensible = set(asp_sensible())
    if py_sensible == clingo_sensible:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} "
            f"python={sorted(py_sensible)}"
        )

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(seed))
            cases.append(params)
        except StoryError:
            continue

    bad = 0
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke test passed for generate()/emit().")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle office ghost story with repetition, rhyme, and inner monologue."
    )
    ap.add_argument("--area", choices=AREAS)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--note-kind", choices=NOTE_KINDS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible area/sign/item combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.area and args.sign:
        area = AREAS[args.area]
        sign = SIGNS[args.sign]
        if not area_supports(area, sign):
            raise StoryError(explain_rejection(area, sign))

    combos = [
        combo
        for combo in valid_combos()
        if (args.area is None or combo[0] == args.area)
        and (args.sign is None or combo[1] == args.sign)
        and (args.item is None or combo[2] == args.item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    area_id, sign_id, item_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    note_kind = args.note_kind or rng.choice(sorted(NOTE_KINDS))
    return StoryParams(
        area=area_id,
        sign=sign_id,
        item=item_id,
        response=response_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
        note_kind=note_kind,
    )


def generate(params: StoryParams) -> StorySample:
    if params.area not in AREAS:
        raise StoryError(f"(Unknown area: {params.area})")
    if params.sign not in SIGNS:
        raise StoryError(f"(Unknown sign: {params.sign})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.note_kind not in NOTE_KINDS:
        raise StoryError(f"(Unknown note kind: {params.note_kind})")
    if params.trait not in TRAIT_BONUS:
        raise StoryError(f"(Unknown trait: {params.trait})")

    area = AREAS[params.area]
    sign = SIGNS[params.sign]
    if not area_supports(area, sign):
        raise StoryError(explain_rejection(area, sign))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        area=area,
        sign=sign,
        item_cfg=ITEMS[params.item],
        response=RESPONSES[params.response],
        name=params.name,
        gender=params.gender,
        parent_type=params.parent,
        trait=params.trait,
        note_kind=params.note_kind,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (area, sign, item) combos:\n")
        for area, sign, item in combos:
            print(f"  {area:10} {sign:16} {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.name}: {p.item} in {p.area} "
                f"({p.sign}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
