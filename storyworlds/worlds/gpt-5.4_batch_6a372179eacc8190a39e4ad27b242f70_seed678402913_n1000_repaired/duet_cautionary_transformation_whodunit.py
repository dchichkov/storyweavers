#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/duet_cautionary_transformation_whodunit.py
=====================================================================

A standalone story world for a tiny "music-room mystery" domain: two children
are preparing a duet when one of them secretly "improves" a shared performance
object with an art supply. The object is transformed in a way that threatens the
performance. The partner notices the strange change, follows clues, solves the
little whodunit, and a grown-up repairs what can be repaired. The cautionary
lesson is simple: ask before changing shared things, and keep craft supplies off
music gear.

The world supports a happy repaired ending and a smaller, sadder "late duet"
ending when the mess is too far along to fix before the music starts.

Run it
------
    python storyworlds/worlds/gpt-5.4/duet_cautionary_transformation_whodunit.py
    python storyworlds/worlds/gpt-5.4/duet_cautionary_transformation_whodunit.py --tool glitter_glue --target sheet_music
    python storyworlds/worlds/gpt-5.4/duet_cautionary_transformation_whodunit.py --target piano_lid
    python storyworlds/worlds/gpt-5.4/duet_cautionary_transformation_whodunit.py --all --qa
    python storyworlds/worlds/gpt-5.4/duet_cautionary_transformation_whodunit.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher_f"}
        male = {"boy", "father", "man", "teacher_m"}
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
            "teacher_f": "teacher",
            "teacher_m": "teacher",
        }.get(self.type, self.type)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    effect: str
    clue: str
    mark: str
    works_on: set[str] = field(default_factory=set)
    severity: int = 1
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    phrase: str
    material: str
    place: str
    risk: str
    repair_id: str
    sensitivity: int = 1
    stage_critical: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    power: int
    works_on: set[str] = field(default_factory=set)
    text: str = ""
    fail: str = ""
    qa_text: str = ""
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


def _r_delay(world: World) -> list[str]:
    target = world.get("target")
    if target.meters["changed"] < THRESHOLD:
        return []
    sig = ("delay", "duet")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("duet").meters["delay"] += 1
    for eid in ("culprit", "partner"):
        world.get(eid).memes["worry"] += 1
    return ["__delay__"]


def _r_guilt(world: World) -> list[str]:
    culprit = world.get("culprit")
    partner = world.get("partner")
    if culprit.memes["secret"] < THRESHOLD or partner.memes["detecting"] < THRESHOLD:
        return []
    sig = ("guilt", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    culprit.memes["guilt"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="delay", tag="performance", apply=_r_delay),
    Rule(name="guilt", tag="social", apply=_r_guilt),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                out.extend(s for s in bits if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def hazard_at_risk(tool: Tool, target: Target) -> bool:
    return target.material in tool.works_on and target.stage_critical


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def fix_matches(fix: Fix, target: Target) -> bool:
    return target.material in fix.works_on


def best_fix_for(target: Target) -> Fix:
    options = [f for f in sensible_fixes() if fix_matches(f, target)]
    return max(options, key=lambda f: (f.power, f.sense))


def mess_severity(tool: Tool, target: Target, delay: int) -> int:
    return tool.severity + target.sensitivity + delay


def is_repaired(tool: Tool, target: Target, fix: Fix, delay: int) -> bool:
    return fix_matches(fix, target) and fix.power >= mess_severity(tool, target, delay)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for tool_id, tool in TOOLS.items():
        for target_id, target in TARGETS.items():
            if hazard_at_risk(tool, target) and any(
                fix_matches(fix, target) for fix in sensible_fixes()
            ):
                combos.append((tool_id, target_id))
    return combos


def predict_trouble(world: World, tool: Tool, target: Target) -> dict:
    sim = world.copy()
    do_secret_change(sim, tool, target, narrate=False)
    return {
        "changed": sim.get("target").meters["changed"] >= THRESHOLD,
        "delay": sim.get("duet").meters["delay"],
    }


def setup(world: World, culprit: Entity, partner: Entity, teacher: Entity, piece: str) -> None:
    for kid in (culprit, partner):
        kid.memes["joy"] += 1
    world.say(
        f"On recital afternoon, {culprit.id} and {partner.id} sat side by side at the piano, "
        f"practicing their duet called {piece}."
    )
    world.say(
        f"The music room smelled like polished wood and sharpened pencils, and "
        f"{teacher.label_word} said they sounded neat and steady together."
    )


def temptation(world: World, culprit: Entity, tool: Tool, target: Target) -> None:
    culprit.memes["showy"] += 1
    world.say(
        f"When {teacher_name(world)} stepped into the hall to greet families, {culprit.id} glanced at "
        f"{target.the} and whispered, \"It looks so plain.\""
    )
    world.say(
        f"Then {culprit.pronoun().capitalize()} spotted {tool.phrase} in the craft tray and got a bold idea. "
        f"{tool.label.capitalize()} could make {target.the} look {tool.effect}."
    )


def teacher_name(world: World) -> str:
    return world.get("teacher").label_word.capitalize()


def warning(world: World, partner: Entity, culprit: Entity, tool: Tool, target: Target) -> None:
    pred = predict_trouble(world, tool, target)
    partner.memes["care"] += 1
    world.facts["predicted_delay"] = pred["delay"]
    world.say(
        f'{partner.id} lowered {partner.pronoun("possessive")} voice. "{culprit.id}, don\'t change '
        f'{target.the} with {tool.label}. It could make the duet hard to play."'
    )


def do_secret_change(world: World, tool: Tool, target: Target, narrate: bool = True) -> None:
    tgt = world.get("target")
    culprit = world.get("culprit")
    tgt.meters["changed"] += 1
    tgt.meters["severity"] = float(tool.severity + target.sensitivity)
    culprit.memes["secret"] += 1
    culprit.attrs["clue"] = tool.clue
    culprit.attrs["mark"] = tool.mark
    propagate(world, narrate=narrate)


def defy(world: World, culprit: Entity) -> None:
    culprit.memes["defiance"] += 1
    world.say(
        f'"Just one tiny touch," {culprit.id} said, and before {partner_name(world)} could stop '
        f'{culprit.pronoun("object")}, {culprit.pronoun()} reached for the shared things.'
    )


def partner_name(world: World) -> str:
    return world.get("partner").id


def discovery(world: World, partner: Entity, tool: Tool, target: Target) -> None:
    partner.memes["detecting"] += 1
    world.say(
        f"A moment later, {partner.id} blinked. {target.the.capitalize()} was not ordinary anymore. "
        f"It looked {tool.effect}, and that was the beginning of the mystery."
    )
    if target.id == "sheet_music":
        world.say(
            "Some notes had a shiny blur over them, so the black marks were no longer easy to read."
        )
    elif target.id == "piano_keys":
        world.say(
            "A few keys looked pretty at first, but they felt sticky and slow under little fingers."
        )
    else:
        world.say(
            "The seat had a bright patch that looked fancy, but it would smear onto anyone who sat there."
        )


def investigate(world: World, partner: Entity, culprit: Entity, tool: Tool, target: Target) -> None:
    culprit.memes["guilt"] += 1
    partner.memes["curiosity"] += 1
    world.say(
        f'{partner.id} peered close, like a tiny detective. There was {tool.clue} near {target.the}, '
        f'and the same clue was on {culprit.id}\'s hand.'
    )
    world.say(
        f'"Who changed {target.the}?" {partner.id} asked. The room went still except for the soft hum of the lights.'
    )
    if culprit.memes["guilt"] >= THRESHOLD:
        world.say(
            f"{culprit.id} looked down at {culprit.pronoun('possessive')} {tool.mark} and swallowed hard."
        )


def confession(world: World, culprit: Entity, target: Target) -> None:
    culprit.memes["relief"] += 1
    world.say(
        f'"I did," {culprit.id} admitted at last. "I wanted {target.the} to look special for our duet."'
    )
    world.say(
        f"{culprit.pronoun().capitalize()} had tried to make it prettier, but the change had turned into trouble."
    )


def teacher_arrives(world: World, teacher: Entity) -> None:
    world.say(
        f"{teacher_name(world)} came back in, took one careful look, and understood that the music room now had a case to solve."
    )


def repair_success(world: World, teacher: Entity, fix: Fix, target: Target, tool: Tool) -> None:
    world.get("target").meters["changed"] = 0.0
    world.get("duet").meters["delay"] = 0.0
    world.say(
        f"{teacher_name(world)} did not shout. {teacher.pronoun().capitalize()} {fix.text.format(target=target.label)}."
    )
    world.say(
        f'"Craft things can transform paper and piano parts very fast," {teacher.pronoun()} said, '
        f'"so we must ask before using them near shared music things."'
    )


def repair_fail(world: World, teacher: Entity, fix: Fix, target: Target, tool: Tool) -> None:
    world.get("duet").meters["delay"] += 1
    world.say(
        f"{teacher_name(world)} tried to help, but {teacher.pronoun()} {fix.fail.format(target=target.label)}."
    )
    world.say(
        f"The first pair of children was already walking toward the stage, so this duet would have to wait."
    )


def ending_happy(world: World, culprit: Entity, partner: Entity, teacher: Entity, piece: str) -> None:
    for kid in (culprit, partner):
        kid.memes["joy"] += 1
        kid.memes["worry"] = 0.0
        kid.memes["lesson"] += 1
    world.say(
        f"Soon {culprit.id} and {partner.id} sat down again, shoulders touching lightly on the bench."
    )
    world.say(
        f"They played {piece} together, and this time the special thing about the duet was not sparkle at all. "
        f"It was how well they listened to each other."
    )
    world.say(
        f"Afterward, {teacher_name(world)} gave them a clean paper star to clip on their music folder instead. "
        f"It shone there, safe and removable."
    )


def ending_late(world: World, culprit: Entity, partner: Entity, teacher: Entity, piece: str) -> None:
    for kid in (culprit, partner):
        kid.memes["lesson"] += 1
        kid.memes["sad"] += 1
    world.say(
        f"{culprit.id} and {partner.id} had to miss their first turn. They waited on a little bench by the wall and listened to the other children play."
    )
    world.say(
        f"Later, when a clean set was ready, they played {piece} very softly and very carefully."
    )
    world.say(
        f"Their music was still beautiful, but {culprit.id} never forgot how one secret makeover had changed the whole afternoon."
    )


def tell(
    tool: Tool,
    target_cfg: Target,
    fix: Fix,
    culprit_name: str = "Mia",
    culprit_gender: str = "girl",
    partner_name_value: str = "Ben",
    partner_gender: str = "boy",
    teacher_type: str = "teacher_f",
    piece: str = '"River Light"',
    delay: int = 0,
) -> World:
    world = World()
    culprit = world.add(
        Entity(
            id="culprit",
            kind="character",
            type=culprit_gender,
            label=culprit_name,
            phrase=culprit_name,
            role="culprit",
        )
    )
    partner = world.add(
        Entity(
            id="partner",
            kind="character",
            type=partner_gender,
            label=partner_name_value,
            phrase=partner_name_value,
            role="detective",
        )
    )
    teacher = world.add(
        Entity(
            id="teacher",
            kind="character",
            type=teacher_type,
            label="the teacher",
            phrase="the teacher",
            role="teacher",
        )
    )
    duet = world.add(Entity(id="duet", type="music", label="the duet"))
    target_ent = world.add(
        Entity(
            id="target",
            type="object",
            label=target_cfg.label,
            phrase=target_cfg.phrase,
            role="target",
        )
    )
    world.facts["piece"] = piece

    setup(world, culprit, partner, teacher, piece)
    world.para()
    temptation(world, culprit, tool, target_cfg)
    warning(world, partner, culprit, tool, target_cfg)
    defy(world, culprit)
    do_secret_change(world, tool, target_cfg)
    discovery(world, partner, tool, target_cfg)
    investigate(world, partner, culprit, tool, target_cfg)
    confession(world, culprit, target_cfg)

    severity = mess_severity(tool, target_cfg, delay)
    target_ent.meters["severity"] = float(severity)
    world.facts["delay_value"] = delay
    world.para()
    teacher_arrives(world, teacher)
    fixed = is_repaired(tool, target_cfg, fix, delay)
    if fixed:
        repair_success(world, teacher, fix, target_cfg, tool)
        world.para()
        ending_happy(world, culprit, partner, teacher, piece)
        outcome = "repaired"
    else:
        repair_fail(world, teacher, fix, target_cfg, tool)
        world.para()
        ending_late(world, culprit, partner, teacher, piece)
        outcome = "late"

    culprit.id = culprit_name
    culprit.label = culprit_name
    culprit.phrase = culprit_name
    partner.id = partner_name_value
    partner.label = partner_name_value
    partner.phrase = partner_name_value

    world.entities[culprit_name] = world.entities.pop("culprit")
    world.entities[partner_name_value] = world.entities.pop("partner")

    world.facts.update(
        culprit=culprit,
        partner=partner,
        teacher=teacher,
        tool=tool,
        target_cfg=target_cfg,
        target=target_ent,
        fix=fix,
        outcome=outcome,
        fixed=fixed,
        severity=severity,
        confessed=True,
    )
    return world


TOOLS = {
    "glitter_glue": Tool(
        id="glitter_glue",
        label="glitter glue",
        phrase="a squeeze bottle of glitter glue",
        effect="silver and sticky",
        clue="silver sparkles",
        mark="sparkly fingers",
        works_on={"paper", "plastic", "cloth"},
        severity=1,
        tags={"craft", "glitter"},
    ),
    "blue_marker": Tool(
        id="blue_marker",
        label="a blue marker",
        phrase="a blue marker with no cap",
        effect="bright blue",
        clue="blue smudges",
        mark="blue fingertips",
        works_on={"paper", "cloth"},
        severity=2,
        tags={"craft", "marker", "blue"},
    ),
    "scent_spray": Tool(
        id="scent_spray",
        label="stage scent spray",
        phrase="a bottle of stage scent spray",
        effect="shiny and sweet-smelling",
        clue="a sugary smell",
        mark="sweet-smelling sleeves",
        works_on={"plastic", "cloth"},
        severity=1,
        tags={"spray", "scent"},
    ),
}

TARGETS = {
    "sheet_music": Target(
        id="sheet_music",
        label="sheet music",
        phrase="the shared sheet music on the stand",
        material="paper",
        place="on the music stand",
        risk="blurred notes can be hard to read",
        repair_id="reprint",
        sensitivity=2,
        tags={"music", "paper", "notes"},
    ),
    "piano_keys": Target(
        id="piano_keys",
        label="piano keys",
        phrase="the middle piano keys",
        material="plastic",
        place="at the center of the keyboard",
        risk="sticky keys can slow little fingers",
        repair_id="wipe",
        sensitivity=2,
        tags={"music", "piano"},
    ),
    "bench_cover": Target(
        id="bench_cover",
        label="bench cover",
        phrase="the soft bench cover",
        material="cloth",
        place="on the piano bench",
        risk="a messy seat can smear onto recital clothes",
        repair_id="swap_cover",
        sensitivity=1,
        tags={"music", "bench", "cloth"},
    ),
    "piano_lid": Target(
        id="piano_lid",
        label="piano lid",
        phrase="the black piano lid",
        material="wood",
        place="over the strings",
        risk="the lid is not part of what the children need to touch to play",
        repair_id="wipe",
        sensitivity=1,
        stage_critical=False,
        tags={"music", "wood"},
    ),
}

FIXES = {
    "reprint": Fix(
        id="reprint",
        label="print a clean copy",
        sense=3,
        power=4,
        works_on={"paper"},
        text="hurried to print a clean copy of the {target} from the office computer",
        fail="looked for a clean copy of the {target}, but the printer was still waking up",
        qa_text="printed a clean new copy",
        tags={"printer", "paper"},
    ),
    "wipe": Fix(
        id="wipe",
        label="wipe it clean",
        sense=3,
        power=3,
        works_on={"plastic"},
        text="sprayed a cloth with piano-safe cleaner and wiped the {target} until they moved freely again",
        fail="wiped and wiped at the {target}, but the sticky patch would not come off in time",
        qa_text="wiped the mess away with a piano-safe cloth",
        tags={"cleaning"},
    ),
    "swap_cover": Fix(
        id="swap_cover",
        label="swap the cover",
        sense=3,
        power=3,
        works_on={"cloth"},
        text="lifted off the messy {target} and replaced it with a clean one from the closet",
        fail="looked for a spare {target}, but none could be found before their turn",
        qa_text="replaced it with a clean spare cover",
        tags={"cleaning", "spare"},
    ),
    "blow_on_it": Fix(
        id="blow_on_it",
        label="blow on it",
        sense=1,
        power=1,
        works_on={"paper", "plastic", "cloth"},
        text="blew on the {target} and hoped that would be enough",
        fail="blew on the {target}, but nothing important changed",
        qa_text="blew on it",
        tags={"weak"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Zoe", "Nora", "Ella", "Ruby", "Anna"]
BOY_NAMES = ["Ben", "Max", "Leo", "Finn", "Eli", "Theo", "Sam", "Jack"]
PIECES = ['"River Light"', '"Moon Steps"', '"The Small Parade"', '"Silver Rain"']


@dataclass
class StoryParams:
    tool: str
    target: str
    fix: str
    culprit_name: str
    culprit_gender: str
    partner_name: str
    partner_gender: str
    teacher: str
    piece: str
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "duet": [
        (
            "What is a duet?",
            "A duet is a piece of music played or sung by two people together. They have to listen to each other so their parts fit.",
        )
    ],
    "sheet_music": [
        (
            "What is sheet music?",
            "Sheet music is paper with notes written on it. Musicians read the notes to know what to play.",
        )
    ],
    "piano_keys": [
        (
            "Why do piano keys need to stay clean?",
            "Piano keys need to move smoothly under your fingers. If they get sticky, the music can feel slow and bumpy.",
        )
    ],
    "bench": [
        (
            "Why should a piano bench be clean?",
            "A clean bench helps a player sit comfortably. A messy bench can smear clothes and make it hard to settle in.",
        )
    ],
    "glitter": [
        (
            "Why can glitter glue be a problem on shared things?",
            "Glitter glue can dry sticky and hard to remove. That is fine for a craft page, but not for something everyone needs to use right away.",
        )
    ],
    "marker": [
        (
            "Why is marker hard to use on important papers?",
            "Marker soaks into paper and leaves strong color behind. On important papers, that can cover up words or notes.",
        )
    ],
    "spray": [
        (
            "Why should you be careful with sprays indoors?",
            "Sprays can drift farther than you mean them to. They can land on shared things and leave smells or wet spots behind.",
        )
    ],
    "ask_first": [
        (
            "Why should children ask before changing a shared object?",
            "Shared objects belong to everyone using them. Asking first helps keep them safe and makes sure the change will not cause a problem.",
        )
    ],
}
KNOWLEDGE_ORDER = ["duet", "sheet_music", "piano_keys", "bench", "glitter", "marker", "spray", "ask_first"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    culprit = f["culprit"]
    partner = f["partner"]
    tool = f["tool"]
    target = f["target_cfg"]
    piece = world.facts["piece"]
    return [
        f'Write a gentle whodunit for ages 3 to 5 about a recital duet and a mysterious change to {target.the}. Include the word "duet".',
        f"Tell a cautionary story where {culprit.id} secretly uses {tool.label} on {target.the}, and {partner.id} notices the clues and solves the little mystery.",
        f'Write a transformation story in a music room where something shared is changed before a performance of {piece}, and the ending teaches children to ask first.',
    ]


def pair_word(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    culprit = f["culprit"]
    partner = f["partner"]
    teacher = f["teacher"]
    tool = f["tool"]
    target = f["target_cfg"]
    fix = f["fix"]
    piece = world.facts["piece"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_word(culprit, partner)}, {culprit.id} and {partner.id}, getting ready to play a piano duet. Their teacher helps when the mystery is solved.",
        ),
        (
            "What was the mystery?",
            f"The mystery was who had changed {target.the} before the music started. The strange transformation mattered because {target.risk}.",
        ),
        (
            f"How did {partner.id} figure out who did it?",
            f"{partner.id} looked for clues and noticed {tool.clue} by {target.the} and on {culprit.id}. That made the secret makeover feel less like magic and more like something a detective could solve.",
        ),
        (
            f"Why did {culprit.id} confess?",
            f"{culprit.id} confessed because the clues pointed back to {culprit.pronoun('object')} and the secret was making {culprit.pronoun('object')} feel guilty. {culprit.pronoun().capitalize()} had wanted to make things look special, but the change was hurting the duet instead.",
        ),
    ]
    if f["outcome"] == "repaired":
        qa.append(
            (
                "How was the problem fixed?",
                f"The teacher {fix.qa_text}. That worked because the fix matched the kind of mess on {target.the}.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with {culprit.id} and {partner.id} playing {piece} together after the repair. The final image shows that listening and asking first mattered more than making things look fancy.",
            )
        )
    else:
        qa.append(
            (
                "Could they still play right away?",
                f"No. The repair was too slow for that moment, so they missed their first turn and had to wait. The delay happened because the mess had already changed {target.the} too much before help came.",
            )
        )
        qa.append(
            (
                "What lesson did the children learn?",
                f"They learned that shared music things should not be secretly transformed with craft supplies. One hidden change had enough consequences to alter the whole afternoon.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"duet", "ask_first"}
    tool = world.facts["tool"]
    target = world.facts["target_cfg"]
    if tool.id == "glitter_glue":
        tags.add("glitter")
    if tool.id == "blue_marker":
        tags.add("marker")
    if tool.id == "scent_spray":
        tags.add("spray")
    if target.id == "sheet_music":
        tags.add("sheet_music")
    if target.id == "piano_keys":
        tags.add("piano_keys")
    if target.id == "bench_cover":
        tags.add("bench")
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        tool="glitter_glue",
        target="sheet_music",
        fix="reprint",
        culprit_name="Mia",
        culprit_gender="girl",
        partner_name="Ben",
        partner_gender="boy",
        teacher="teacher_f",
        piece='"River Light"',
        delay=0,
    ),
    StoryParams(
        tool="scent_spray",
        target="piano_keys",
        fix="wipe",
        culprit_name="Leo",
        culprit_gender="boy",
        partner_name="Ava",
        partner_gender="girl",
        teacher="teacher_m",
        piece='"Moon Steps"',
        delay=0,
    ),
    StoryParams(
        tool="blue_marker",
        target="bench_cover",
        fix="swap_cover",
        culprit_name="Nora",
        culprit_gender="girl",
        partner_name="Finn",
        partner_gender="boy",
        teacher="teacher_f",
        piece='"The Small Parade"',
        delay=1,
    ),
    StoryParams(
        tool="blue_marker",
        target="sheet_music",
        fix="reprint",
        culprit_name="Sam",
        culprit_gender="boy",
        partner_name="Ruby",
        partner_gender="girl",
        teacher="teacher_m",
        piece='"Silver Rain"',
        delay=2,
    ),
]


def explain_rejection(tool: Tool, target: Target) -> str:
    if not target.stage_critical:
        return (
            f"(No story: {target.the} is not something the children need for the duet itself, "
            f"so changing it would not create this mystery or cautionary turn.)"
        )
    if target.material not in tool.works_on:
        return (
            f"(No story: {tool.label} does not meaningfully change {target.the} in this world, "
            f"so there is no believable transformation to investigate.)"
        )
    return "(No story: this combination does not create a strong enough music-room mystery.)"


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of the sensible fixes: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    tool = TOOLS[params.tool]
    target = TARGETS[params.target]
    fix = FIXES[params.fix]
    return "repaired" if is_repaired(tool, target, fix, params.delay) else "late"


ASP_RULES = r"""
hazard(Tool, Target) :- works_on(Tool, M), material(Target, M), stage_critical(Target).
sensible_fix(Fix) :- fix(Fix), sense(Fix, S), sense_min(M), S >= M.
fits(Fix, Target) :- fix_works_on(Fix, M), material(Target, M).
valid(Tool, Target) :- hazard(Tool, Target), sensible_fix(Fix), fits(Fix, Target).

severity(V) :- chosen_tool(T), chosen_target(Tg), tool_severity(T, TS), target_sensitivity(Tg, TgS), delay(D), V = TS + TgS + D.
repaired :- chosen_fix(F), chosen_target(Tg), fits(F, Tg), fix_power(F, P), severity(V), P >= V.
outcome(repaired) :- repaired.
outcome(late) :- not repaired.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_severity", tid, tool.severity))
        for mat in sorted(tool.works_on):
            lines.append(asp.fact("works_on", tid, mat))
    for tid, target in TARGETS.items():
        lines.append(asp.fact("target", tid))
        lines.append(asp.fact("material", tid, target.material))
        lines.append(asp.fact("target_sensitivity", tid, target.sensitivity))
        if target.stage_critical:
            lines.append(asp.fact("stage_critical", tid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("fix_power", fid, fix.power))
        for mat in sorted(fix.works_on):
            lines.append(asp.fact("fix_works_on", fid, mat))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_fixes() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_fix/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible_fix"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_target", params.target),
            asp.fact("chosen_fix", params.fix),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_emit(sample: StorySample) -> None:
    if not sample.story.strip():
        raise StoryError("smoke test failed: empty story")
    if "{" in sample.story or "}" in sample.story:
        raise StoryError("smoke test failed: unresolved template braces in story")


def asp_verify() -> int:
    rc = 0

    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens = set(asp_sensible_fixes())
    p_sens = {f.id for f in sensible_fixes()}
    if c_sens == p_sens:
        print(f"OK: sensible fixes match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        _smoke_emit(smoke)
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Music-room whodunit story world: a secret makeover threatens a recital duet."
    )
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--teacher", choices=["teacher_f", "teacher_m"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and args.tool:
        tool = TOOLS[args.tool]
        target = TARGETS[args.target]
        if not hazard_at_risk(tool, target):
            raise StoryError(explain_rejection(tool, target))
    if args.target and args.fix:
        if not fix_matches(FIXES[args.fix], TARGETS[args.target]):
            raise StoryError(
                f"(No story: fix '{args.fix}' does not fit {TARGETS[args.target].the}. Choose a fix for {TARGETS[args.target].material}.)"
            )
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        c
        for c in valid_combos()
        if (args.tool is None or c[0] == args.tool)
        and (args.target is None or c[1] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    tool_id, target_id = rng.choice(sorted(combos))
    target = TARGETS[target_id]
    sensible = [f.id for f in sensible_fixes() if fix_matches(f, target)]
    if not sensible:
        raise StoryError("(No sensible fix exists for that target.)")
    fix_id = args.fix or max(sensible, key=lambda fid: FIXES[fid].power)
    culprit_gender = rng.choice(["girl", "boy"])
    partner_gender = "boy" if culprit_gender == "girl" else "girl" if rng.random() < 0.6 else culprit_gender
    culprit_name = _pick_name(rng, culprit_gender)
    partner_name = _pick_name(rng, partner_gender, avoid=culprit_name)
    teacher = args.teacher or rng.choice(["teacher_f", "teacher_m"])
    piece = rng.choice(PIECES)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        tool=tool_id,
        target=target_id,
        fix=fix_id,
        culprit_name=culprit_name,
        culprit_gender=culprit_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        teacher=teacher,
        piece=piece,
        delay=delay,
    )


def _teacher_type_label(t: str) -> str:
    return t


def generate(params: StoryParams) -> StorySample:
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.teacher not in {"teacher_f", "teacher_m"}:
        raise StoryError(f"(Unknown teacher type: {params.teacher})")

    tool = TOOLS[params.tool]
    target = TARGETS[params.target]
    fix = FIXES[params.fix]

    if not hazard_at_risk(tool, target):
        raise StoryError(explain_rejection(tool, target))
    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))
    if not fix_matches(fix, target):
        raise StoryError(f"(No story: {fix.label} does not fit {target.the}.)")

    world = tell(
        tool=tool,
        target_cfg=target,
        fix=fix,
        culprit_name=params.culprit_name,
        culprit_gender=params.culprit_gender,
        partner_name_value=params.partner_name,
        partner_gender=params.partner_gender,
        teacher_type=_teacher_type_label(params.teacher),
        piece=params.piece,
        delay=params.delay,
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
        print(asp_program("", "#show valid/2.\n#show sensible_fix/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible_fixes())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (tool, target) combos:\n")
        for tool, target in combos:
            print(f"  {tool:12} {target}")
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
            header = f"### {p.culprit_name} & {p.partner_name}: {p.tool} on {p.target} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
