#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stationery_persnickety_inner_monologue_bedtime_story.py
==================================================================================

A small bedtime-story world about a child who wants to finish a kind note before
sleep, becomes persnickety about the stationery, and learns that loving words
matter more than perfect-looking paper.

The domain uses:
- stationery as the concrete object world
- persnickety as a stateful emotional trait
- inner monologue as part of the rendered prose
- a bedtime-story tone with a calm ending image

Run it
------
    python storyworlds/worlds/gpt-5.4/stationery_persnickety_inner_monologue_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/stationery_persnickety_inner_monologue_bedtime_story.py --stationery moon_card --tool pencil --flaw crooked --fix erase
    python storyworlds/worlds/gpt-5.4/stationery_persnickety_inner_monologue_bedtime_story.py --stationery tiny_tag
    python storyworlds/worlds/gpt-5.4/stationery_persnickety_inner_monologue_bedtime_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/stationery_persnickety_inner_monologue_bedtime_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Stationery:
    id: str
    label: str
    phrase: str
    texture: str
    sheets: int
    capacity: int
    bedtime_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    erasable: bool
    ink: bool
    soft: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Flaw:
    id: str
    label: str
    line: str
    severity: int
    erasable: bool
    needs_ink: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    text: str
    qa_text: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_notice_flaw(world: World) -> list[str]:
    child = world.get("child")
    page = world.get("page")
    if page.meters["flawed"] < THRESHOLD:
        return []
    sig = ("notice_flaw",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["frustration"] += 1
    child.memes["persnickety"] += 1
    return []


def _r_bedtime_sleepy(world: World) -> list[str]:
    child = world.get("child")
    clock = world.get("clock")
    if clock.meters["late"] < THRESHOLD:
        return []
    sig = ("sleepy",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["sleepy"] += 1
    child.memes["worry"] += 1
    return []


def _r_finished_note(world: World) -> list[str]:
    child = world.get("child")
    page = world.get("page")
    if page.meters["finished"] < THRESHOLD:
        return []
    sig = ("pride",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["pride"] += 1
    child.memes["calm"] += 1
    return []


CAUSAL_RULES = [
    Rule("notice_flaw", "emotional", _r_notice_flaw),
    Rule("sleepy", "physical", _r_bedtime_sleepy),
    Rule("finished", "emotional", _r_finished_note),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
        if any(rule.apply(world) for rule in []):
            changed = True


def stationery_fits(stationery: Stationery) -> bool:
    return stationery.capacity >= 2


def flaw_possible(tool: Tool, flaw: Flaw) -> bool:
    if flaw.needs_ink and not tool.ink:
        return False
    return True


def fix_works(stationery: Stationery, tool: Tool, flaw: Flaw, fix: Fix) -> bool:
    if fix.id == "erase":
        return tool.erasable and flaw.erasable and flaw.severity <= 1
    if fix.id == "copy_fresh":
        return stationery.sheets >= 2
    if fix.id == "send_anyway":
        return flaw.severity <= 2 and flaw.id != "ink_blot"
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for sid, stationery in STATIONERY.items():
        for tid, tool in TOOLS.items():
            for fid, flaw in FLAWS.items():
                for xid, fix in FIXES.items():
                    if stationery_fits(stationery) and flaw_possible(tool, flaw) and fix_works(stationery, tool, flaw, fix):
                        out.append((sid, tid, fid, xid))
    return out


def explain_stationery_rejection(stationery: Stationery) -> str:
    return (
        f"(No story: {stationery.phrase} is too small for a whole bedtime note. "
        f"A note needs room for kind words, not just a tiny scribble.)"
    )


def explain_flaw_rejection(tool: Tool, flaw: Flaw) -> str:
    return (
        f"(No story: {flaw.label} does not fit {tool.label}. "
        f"That flaw only makes sense with a different writing tool.)"
    )


def explain_fix_rejection(stationery: Stationery, tool: Tool, flaw: Flaw, fix: Fix) -> str:
    if fix.id == "erase":
        return (
            f"(No story: {fix.label} would not really fix {flaw.label} on {stationery.label}. "
            f"It only works for a small erasable mistake made with a pencil.)"
        )
    if fix.id == "copy_fresh":
        return (
            f"(No story: {stationery.label} gives only one usable sheet, so starting over honestly is not possible.)"
        )
    return (
        f"(No story: {fix.label} is too weak for {flaw.label}. "
        f"This world only keeps the same page when the mistake is mild.)"
    )


def outcome_of(params: "StoryParams") -> str:
    if params.fix == "copy_fresh":
        return "redo"
    return "accept"


def predict_after_fix(world: World, fix: Fix) -> dict:
    sim = world.copy()
    page = sim.get("page")
    if fix.id == "copy_fresh":
        page.meters["flawed"] = 0.0
        page.meters["fresh_page_used"] += 1
    elif fix.id == "erase":
        page.meters["flawed"] = 0.0
        page.meters["erased"] += 1
    elif fix.id == "send_anyway":
        page.meters["flawed"] = 0.0
        page.meters["kept_imperfect"] += 1
    page.meters["finished"] += 1
    propagate(sim)
    return {
        "finished": page.meters["finished"] >= THRESHOLD,
        "sleepy": sim.get("child").meters["sleepy"],
    }


def opening(world: World, child: Entity, helper: Entity, stationery: Stationery, recipient: str) -> None:
    child.memes["care"] += 1
    world.say(
        f"The house had gone quiet, and the moon lay on the window like a silver button. "
        f"{child.id} was already in pajamas, but before bed {child.pronoun()} wanted to write a little note for {recipient} on {stationery.phrase}."
    )
    world.say(
        f"{helper.label_word.capitalize()} switched on the small bedside lamp, and the light made the {stationery.texture} look soft and important."
    )


def begin_note(world: World, child: Entity, stationery: Stationery, tool: Tool, recipient: str) -> None:
    page = world.get("page")
    page.meters["blank"] = 0.0
    world.say(
        f'{child.id} held {tool.phrase} very carefully and began: "Dear {recipient}..."'
    )
    world.say(
        f'Inside, {child.pronoun()} thought, "I want it to be just right. The stationery feels too lovely for a messy note."'
    )


def make_flaw(world: World, child: Entity, flaw: Flaw) -> None:
    page = world.get("page")
    clock = world.get("clock")
    page.meters["flawed"] += 1
    page.meters[flaw.id] += 1
    clock.meters["late"] += 1
    propagate(world)
    world.say(flaw.line)
    if child.memes["persnickety"] >= THRESHOLD:
        world.say(
            f'Inside, {child.pronoun()} thought, "Oh no. It is not neat anymore. Now it feels all wrong."'
        )


def fuss(world: World, child: Entity, helper: Entity, stationery: Stationery) -> None:
    child.memes["fussiness"] += 1
    world.say(
        f"{child.id} looked at the page and then at the next sheet, and then back again, as if the stationery itself might whisper an answer."
    )
    world.say(
        f'"It has to be perfect," {child.pronoun()} said in a very small voice. {helper.label_word.capitalize()} sat on the edge of the bed and waited a moment before answering.'
    )


def guide(world: World, child: Entity, helper: Entity, flaw: Flaw, fix: Fix) -> None:
    sleepy = world.get("child").meters["sleepy"] >= THRESHOLD
    extra = " The clock was growing late, and the room had that hushed bedtime feeling." if sleepy else ""
    world.say(
        f'"A kind note does not have to be a perfect note," {helper.label_word} said softly.{extra}'
    )
    if fix.id == "erase":
        world.say(
            f'{helper.label_word.capitalize()} tapped the page and smiled. "This is only a little {flaw.label}. We can rub it away and keep your sweet words."'
        )
    elif fix.id == "copy_fresh":
        world.say(
            f'{helper.label_word.capitalize()} turned the stack gently. "You have another sheet. Let us carry the good words over to a fresh page, one slow line at a time."'
        )
    else:
        world.say(
            f'{helper.label_word.capitalize()} traced the note with one finger. "The words are still loving. A tiny wobble can stay, and the love can stay too."'
        )


def apply_fix(world: World, child: Entity, helper: Entity, stationery: Stationery, flaw: Flaw, fix: Fix) -> None:
    page = world.get("page")
    if fix.id == "erase":
        page.meters["flawed"] = 0.0
        page.meters["erased"] += 1
        world.say(
            f"{child.id} erased the little mistake with slow careful strokes until the page looked smooth again."
        )
    elif fix.id == "copy_fresh":
        page.meters["flawed"] = 0.0
        page.meters["fresh_page_used"] += 1
        world.say(
            f"{helper.label_word.capitalize()} held the first sheet while {child.id} copied the note onto a fresh page. The second try came more slowly, and the letters settled down like ducks on a pond."
        )
    else:
        page.meters["flawed"] = 0.0
        page.meters["kept_imperfect"] += 1
        world.say(
            f"{child.id} took a long breath and kept the same page. The tiny flaw stayed there, but it no longer seemed like the biggest thing in the room."
        )
    page.meters["finished"] += 1
    child.memes["relief"] += 1
    child.memes["love"] += 1
    propagate(world)


def ending(world: World, child: Entity, helper: Entity, stationery: Stationery, recipient: str, fix: Fix) -> None:
    world.say(
        f'At the bottom, {child.id} added, "Love from me," and set the note beside the lamp for {recipient} to find in the morning.'
    )
    if fix.id == "send_anyway":
        world.say(
            f'Inside, {child.pronoun()} thought, "It is not perfect, but it is kind. That is enough."'
        )
    elif fix.id == "copy_fresh":
        world.say(
            f'Inside, {child.pronoun()} thought, "The paper is fresh now, but the nicest part is still the loving part."'
        )
    else:
        world.say(
            f'Inside, {child.pronoun()} thought, "I can fix a little mistake and still keep the good feeling in it."'
        )
    world.say(
        f"{helper.label_word.capitalize()} tucked the blanket around {child.id}. Soon the note rested on the {stationery.bedtime_image}, and {child.id}'s eyes fluttered shut, peaceful at last."
    )


def tell(stationery: Stationery, tool: Tool, flaw: Flaw, fix: Fix,
         child_name: str = "Mina", child_type: str = "girl",
         helper_type: str = "mother", recipient: str = "Grandma") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child", traits=["careful", "persnickety"]))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper", label="the parent"))
    page = world.add(Entity(id="page", type="paper", label=stationery.label))
    clock = world.add(Entity(id="clock", type="clock", label="the clock"))
    page.meters["blank"] = 1
    world.facts["recipient"] = recipient

    opening(world, child, helper, stationery, recipient)
    world.para()
    begin_note(world, child, stationery, tool, recipient)
    make_flaw(world, child, flaw)
    fuss(world, child, helper, stationery)
    world.para()
    guide(world, child, helper, flaw, fix)
    apply_fix(world, child, helper, stationery, flaw, fix)
    ending(world, child, helper, stationery, recipient, fix)

    world.facts.update(
        child=child,
        helper=helper,
        stationery=stationery,
        tool=tool,
        flaw=flaw,
        fix=fix,
        page=page,
        outcome=outcome_of(StoryParams(stationery.id, tool.id, flaw.id, fix.id, child_name, child_type, helper_type, recipient)),
        sleepy=child.meters["sleepy"] >= THRESHOLD,
        finished=page.meters["finished"] >= THRESHOLD,
    )
    return world


STATIONERY = {
    "moon_card": Stationery(
        "moon_card",
        "moon card",
        "a folded moon-and-stars card",
        "creamy paper with tiny silver stars",
        1,
        3,
        "pillow beside the lamp",
        tags={"stationery", "card"},
    ),
    "flower_pad": Stationery(
        "flower_pad",
        "flower stationery",
        "a pad of flowered stationery",
        "paper trimmed with pale blue flowers",
        4,
        3,
        "bedside table",
        tags={"stationery", "paper"},
    ),
    "animal_sheet": Stationery(
        "animal_sheet",
        "animal stationery",
        "a stack of animal stationery",
        "paper with sleepy rabbits in the corners",
        3,
        2,
        "nightstand",
        tags={"stationery", "paper"},
    ),
    "tiny_tag": Stationery(
        "tiny_tag",
        "gift tag",
        "a tiny gift tag with a gold string",
        "stiff little card",
        1,
        1,
        "bedside table",
        tags={"tag"},
    ),
}

TOOLS = {
    "pencil": Tool("pencil", "pencil", "a soft pencil", erasable=True, ink=False, tags={"pencil"}),
    "gel_pen": Tool("gel_pen", "gel pen", "a shiny gel pen", erasable=False, ink=True, tags={"pen"}),
    "fountain_pen": Tool("fountain_pen", "fountain pen", "a fountain pen", erasable=False, ink=True, tags={"pen", "ink"}),
    "crayon": Tool("crayon", "crayon", "a purple crayon", erasable=False, ink=False, soft=True, tags={"crayon"}),
}

FLAWS = {
    "crooked": Flaw(
        "crooked",
        "crooked letter",
        'But one letter leaned sideways. "Oh," whispered the child, staring at the crooked little shape.',
        1,
        True,
        tags={"mistake"},
    ),
    "smudge": Flaw(
        "smudge",
        "smudge",
        "A small smudge brushed across the page when a hand moved too quickly.",
        2,
        False,
        tags={"mistake", "smudge"},
    ),
    "ink_blot": Flaw(
        "ink_blot",
        "ink blot",
        "Then a dark ink blot landed with a plop, round and bold in the middle of the neat line.",
        3,
        False,
        needs_ink=True,
        tags={"mistake", "ink"},
    ),
}

FIXES = {
    "erase": Fix("erase", "erase it", 3, "erase", "erased the small mistake and kept the same page", tags={"erase"}),
    "copy_fresh": Fix("copy_fresh", "start on a fresh sheet", 3, "copy fresh", "copied the note onto a fresh sheet", tags={"redo"}),
    "send_anyway": Fix("send_anyway", "keep the page anyway", 2, "send anyway", "kept the same page and sent the kind note anyway", tags={"accept"}),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Eva", "June", "Ivy", "Tessa", "Lucy"]
BOY_NAMES = ["Owen", "Milo", "Ben", "Theo", "Arlo", "Jude", "Noah", "Finn"]
RECIPIENTS = ["Grandma", "Grandpa", "Aunt May", "Uncle Ben", "the teacher", "a neighbor"]


@dataclass
class StoryParams:
    stationery: str
    tool: str
    flaw: str
    fix: str
    child: str
    gender: str
    helper: str
    recipient: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "stationery": [(
        "What is stationery?",
        "Stationery is nice paper or cards used for writing letters and notes. People choose it when they want their words to feel special."
    )],
    "card": [(
        "What is a card?",
        "A card is a folded piece of thick paper for a message. People often use cards for kind notes and celebrations."
    )],
    "paper": [(
        "Why do people write notes on special paper?",
        "Special paper can make a note feel careful and important. It does not change the love in the words, but it can make the note feel extra thoughtful."
    )],
    "pencil": [(
        "Why is a pencil easy to fix mistakes with?",
        "A pencil mark can be rubbed away with an eraser. That is why pencils are helpful when you want to change a small mistake."
    )],
    "pen": [(
        "Why are pen mistakes harder to fix?",
        "Pen marks sink into the paper and do not erase easily. If a pen line goes wrong, people often have to start again or live with the mark."
    )],
    "crayon": [(
        "What does a crayon do?",
        "A crayon makes soft waxy color on paper. It is good for drawing, but it can also smudge if a hand rubs across it."
    )],
    "mistake": [(
        "Can a kind note still be good if it has a little mistake?",
        "Yes. A kind note is mostly about the loving words inside it. A small mistake does not take the kindness away."
    )],
    "smudge": [(
        "What is a smudge?",
        "A smudge is a blurry mark made when writing or drawing gets rubbed. It can make the page look less neat."
    )],
    "ink": [(
        "What is an ink blot?",
        "An ink blot is a drop of ink that lands in one spot and spreads. It can leave a dark mark on paper."
    )],
    "erase": [(
        "What does an eraser do?",
        "An eraser rubs away pencil marks. It works best on small pencil mistakes."
    )],
    "redo": [(
        "Why might someone use a fresh sheet of paper?",
        "A fresh sheet gives you a clean new start. People use one when the first page has a mistake they cannot easily fix."
    )],
    "accept": [(
        "What does it mean to accept something imperfect?",
        "It means you notice a small flaw and still decide it is good enough. Sometimes that helps you finish something kind and peaceful."
    )],
}
KNOWLEDGE_ORDER = ["stationery", "card", "paper", "pencil", "pen", "crayon", "mistake", "smudge", "ink", "erase", "redo", "accept"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    stationery = f["stationery"]
    flaw = f["flaw"]
    fix = f["fix"]
    recipient = f["recipient"]
    return [
        f'Write a gentle bedtime story that includes the words "stationery" and "persnickety" and uses inner monologue.',
        f"Tell a calm story about a {child.type} named {child.id} who becomes persnickety over {stationery.label} while writing a note for {recipient} before bed.",
        f"Write a bedtime story where a child makes a {flaw.label} on special stationery, worries about making it perfect, and then {fix.text}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    stationery = f["stationery"]
    tool = f["tool"]
    flaw = f["flaw"]
    fix = f["fix"]
    recipient = f["recipient"]
    outcome = f["outcome"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who wanted to write a bedtime note for {recipient}, and {child.pronoun('possessive')} {helper.label_word}, who helped {child.pronoun('object')} calm down."
        ),
        (
            "Why was the child using stationery before bed?",
            f"{child.id} wanted to leave a kind note for {recipient} to find in the morning. The special stationery made the note feel important and loving."
        ),
        (
            f"What went wrong on the page?",
            f"{child.id} made a {flaw.label} while writing with the {tool.label}. That small problem made {child.pronoun('object')} feel persnickety because {child.pronoun()} wanted the note to look exactly right."
        ),
        (
            f"Why did the mistake feel so big to {child.id}?",
            f"It felt big because {child.id} cared a lot about giving {recipient} a beautiful note. The page mattered to {child.pronoun('object')}, and bedtime was getting close, so the mistake seemed even larger."
        ),
    ]
    if outcome == "redo":
        qa.append((
            "How did they solve the problem?",
            f"They used a fresh sheet and copied the note over slowly. That worked because the first page could not be made neat enough, but the stationery pad still had another sheet."
        ))
    else:
        qa.append((
            "How did they solve the problem?",
            f"They did not chase perfect-looking paper forever. Instead, they {fix.qa_text}, and that let the loving message stay at the center of the story."
        ))
    qa.append((
        "What did the child learn by the end?",
        f"{child.id} learned that a kind note does not have to be flawless to be worth giving. The ending shows this because the note is finished and set out for morning, and {child.pronoun()} can finally rest."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["stationery"].tags) | set(world.facts["tool"].tags) | set(world.facts["flaw"].tags) | set(world.facts["fix"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moon_card", "pencil", "crooked", "erase", "Mina", "girl", "mother", "Grandma"),
    StoryParams("flower_pad", "fountain_pen", "ink_blot", "copy_fresh", "Owen", "boy", "father", "Grandpa"),
    StoryParams("animal_sheet", "crayon", "smudge", "send_anyway", "Lila", "girl", "mother", "the teacher"),
    StoryParams("flower_pad", "gel_pen", "smudge", "copy_fresh", "Theo", "boy", "father", "Aunt May"),
]


ASP_RULES = r"""
usable_stationery(S) :- stationery(S), capacity(S, C), C >= 2.
possible_flaw(T, F) :- tool(T), flaw(F), not needs_ink(F).
possible_flaw(T, F) :- tool(T), flaw(F), needs_ink(F), ink(T).

works(S, T, F, erase) :-
    usable_stationery(S), possible_flaw(T, F),
    erasable(T), flaw_erasable(F), severity(F, V), V <= 1.

works(S, T, F, copy_fresh) :-
    usable_stationery(S), possible_flaw(T, F), sheets(S, N), N >= 2.

works(S, T, F, send_anyway) :-
    usable_stationery(S), possible_flaw(T, F),
    severity(F, V), V <= 2, F != ink_blot.

valid(S, T, F, X) :- works(S, T, F, X).

outcome(redo) :- chosen_fix(copy_fresh).
outcome(accept) :- chosen_fix(erase).
outcome(accept) :- chosen_fix(send_anyway).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in STATIONERY.items():
        lines.append(asp.fact("stationery", sid))
        lines.append(asp.fact("sheets", sid, s.sheets))
        lines.append(asp.fact("capacity", sid, s.capacity))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.erasable:
            lines.append(asp.fact("erasable", tid))
        if t.ink:
            lines.append(asp.fact("ink", tid))
    for fid, f in FLAWS.items():
        lines.append(asp.fact("flaw", fid))
        lines.append(asp.fact("severity", fid, f.severity))
        if f.erasable:
            lines.append(asp.fact("flaw_erasable", fid))
        if f.needs_ink:
            lines.append(asp.fact("needs_ink", fid))
    for xid in FIXES:
        lines.append(asp.fact("fix", xid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("chosen_fix", params.fix)
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
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime storyworld: a child grows persnickety about stationery while finishing a kind note."
    )
    ap.add_argument("--stationery", choices=STATIONERY)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--flaw", choices=FLAWS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--child")
    ap.add_argument("--recipient")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.stationery and not stationery_fits(STATIONERY[args.stationery]):
        raise StoryError(explain_stationery_rejection(STATIONERY[args.stationery]))
    if args.tool and args.flaw and not flaw_possible(TOOLS[args.tool], FLAWS[args.flaw]):
        raise StoryError(explain_flaw_rejection(TOOLS[args.tool], FLAWS[args.flaw]))
    if args.stationery and args.tool and args.flaw and args.fix:
        s = STATIONERY[args.stationery]
        t = TOOLS[args.tool]
        f = FLAWS[args.flaw]
        x = FIXES[args.fix]
        if not (stationery_fits(s) and flaw_possible(t, f) and fix_works(s, t, f, x)):
            raise StoryError(explain_fix_rejection(s, t, f, x))

    combos = [
        c for c in valid_combos()
        if (args.stationery is None or c[0] == args.stationery)
        and (args.tool is None or c[1] == args.tool)
        and (args.flaw is None or c[2] == args.flaw)
        and (args.fix is None or c[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    stationery, tool, flaw, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    recipient = args.recipient or rng.choice(RECIPIENTS)
    return StoryParams(stationery, tool, flaw, fix, child, gender, helper, recipient)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        STATIONERY[params.stationery],
        TOOLS[params.tool],
        FLAWS[params.flaw],
        FIXES[params.fix],
        params.child,
        params.gender,
        params.helper,
        params.recipient,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (stationery, tool, flaw, fix) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{x:12}" for x in combo))
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
            header = f"### {p.child}: {p.stationery}, {p.tool}, {p.flaw}, {p.fix} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
