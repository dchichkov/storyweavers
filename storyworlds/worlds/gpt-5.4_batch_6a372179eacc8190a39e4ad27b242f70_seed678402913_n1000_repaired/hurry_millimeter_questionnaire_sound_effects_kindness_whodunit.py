#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hurry_millimeter_questionnaire_sound_effects_kindness_whodunit.py
=============================================================================================

A standalone story world about a tiny mystery in a child-friendly setting:
someone seems to have "spoiled" a classroom questionnaire game, but the truth is
gentler. A child detective notices a millimeter-sized clue, follows soft sound
effects through the room, and learns that kindness solves the whodunit better
than blame.

The domain uses a small simulated state:
- physical meters: hidden, found, torn, worried, noisy
- emotional memes: hurry, suspicion, guilt, relief, kindness, trust
- concrete entities: children, clue, questionnaire sheets, prop box, helper item

The core tension is not "who was bad?" but "what really happened, and can the
children respond kindly once they know?"  A hurried mistake causes a problem,
sound leads the detective to the hiding place, and a compassionate ending
restores the group activity.

Run it
------
    python storyworlds/worlds/gpt-5.4/hurry_millimeter_questionnaire_sound_effects_kindness_whodunit.py
    python storyworlds/worlds/gpt-5.4/hurry_millimeter_questionnaire_sound_effects_kindness_whodunit.py --setting classroom --cause hurry_trip
    python storyworlds/worlds/gpt-5.4/hurry_millimeter_questionnaire_sound_effects_kindness_whodunit.py --cause prank
    python storyworlds/worlds/gpt-5.4/hurry_millimeter_questionnaire_sound_effects_kindness_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/hurry_millimeter_questionnaire_sound_effects_kindness_whodunit.py --qa
    python storyworlds/worlds/gpt-5.4/hurry_millimeter_questionnaire_sound_effects_kindness_whodunit.py --verify
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
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/ to
# the path by walking up three directories.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
KINDNESS_MIN = 2


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
        female = {"girl", "mother", "woman", "teacher_f"}
        male = {"boy", "father", "man", "teacher_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"teacher_f": "teacher", "teacher_m": "teacher"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    host: str
    storage: str
    sound_source: str
    hide_spot: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    blameless: bool
    noise: str
    clue: str
    clue_size_mm: int
    action: str
    confession: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SheetSet:
    id: str
    label: str
    phrase: str
    purpose: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundTrail:
    id: str
    effect: str
    verb: str
    source: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    line: str
    repair: str
    lesson: str
    tags: set[str] = field(default_factory=set)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for cause_id, cause in CAUSES.items():
            for sheets_id in SHEETS:
                for sound_id in SOUNDS:
                    sound = SOUNDS[sound_id]
                    if cause.noise == sound.source:
                        combos.append((setting_id, cause_id, sheets_id, sound_id))
    return combos


def kind_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= KINDNESS_MIN]


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


def _r_hidden_worry(world: World) -> list[str]:
    out: list[str] = []
    sheets = world.get("sheets")
    helper = world.get("helper")
    if sheets.meters["hidden"] >= THRESHOLD:
        sig = ("hidden_worry", sheets.id)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_clue_points(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    detective = world.get("detective")
    if clue.meters["found"] >= THRESHOLD:
        sig = ("clue_points", clue.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["focus"] += 1
            out.append("__focus__")
    return out


def _r_kindness_relief(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    detective = world.get("detective")
    if detective.memes["kindness"] >= THRESHOLD and helper.memes["guilt"] >= THRESHOLD:
        sig = ("kindness_relief", helper.id)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["relief"] += 1
            helper.memes["trust"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="hidden_worry", tag="emotion", apply=_r_hidden_worry),
    Rule(name="clue_points", tag="attention", apply=_r_clue_points),
    Rule(name="kindness_relief", tag="social", apply=_r_kindness_relief),
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


def explain_rejection(cause: Cause, sound: SoundTrail) -> str:
    return (
        f"(No story: cause '{cause.id}' makes a {cause.noise} sound, but sound trail "
        f"'{sound.id}' follows {sound.source}. The clue and sound must point to the same hiding place.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in kind_responses()))
    return (
        f"(Refusing response '{rid}': it is not kind enough for this world "
        f"(sense={r.sense} < {KINDNESS_MIN}). Try one of: {better}.)"
    )


def sound_matches(cause: Cause, sound: SoundTrail) -> bool:
    return cause.noise == sound.source


def predict_truth(world: World) -> dict:
    sim = world.copy()
    sheets = sim.get("sheets")
    clue = sim.get("clue")
    helper = sim.get("helper")
    sheets.meters["hidden"] += 1
    clue.meters["found"] += 1
    helper.memes["guilt"] += 1
    propagate(sim, narrate=False)
    return {
        "missing": sheets.meters["hidden"] >= THRESHOLD,
        "guilty": helper.memes["guilt"] >= THRESHOLD,
        "worry": helper.memes["worry"],
    }


def introduce(world: World, detective: Entity, helper: Entity, teacher: Entity,
              setting: Setting, sheets: SheetSet) -> None:
    world.say(
        f"At {setting.place}, {teacher.id} set out {sheets.phrase} for a game. "
        f"Each child was meant to answer the questionnaire and then guess who liked which thing."
    )
    world.say(
        f"{detective.id} loved mysteries, and {helper.id} loved helping. "
        f'Today, {teacher.id} smiled and said, "{teacher.attrs.get("host_line", setting.host)}"'
    )


def start_activity(world: World, detective: Entity, helper: Entity, sheets: SheetSet) -> None:
    detective.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Soon pencils scratched across the {sheets.label}, and the room felt busy in a happy way."
    )
    world.say(
        f"{helper.id} gathered the finished sheets into a neat stack while {detective.id} watched for patterns."
    )


def hurry_mistake(world: World, helper: Entity, cause: Cause, setting: Setting) -> None:
    helper.memes["hurry"] += 1
    helper.memes["guilt"] += 1
    helper.meters["noisy"] += 1
    sheets = world.get("sheets")
    clue = world.get("clue")
    sheets.meters["hidden"] += 1
    clue.meters["found"] += 1
    clue.meters["tiny"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then there was a little burst of hurry. {helper.id} {cause.action}."
    )
    world.say(
        f'{cause.noise.capitalize()}! The stack slipped out of sight near {setting.storage}, and only {cause.clue} remained on the floor.'
    )


def notice_problem(world: World, teacher: Entity, helper: Entity, sheets: SheetSet) -> None:
    if world.get("sheets").meters["hidden"] >= THRESHOLD:
        world.say(
            f'"Oh dear," said {teacher.id}. "The {sheets.label} are missing, and we cannot play the guessing round without them."'
        )
        if helper.memes["worry"] >= THRESHOLD:
            world.say(
                f"{helper.id} went quiet and looked at {helper.pronoun('possessive')} shoes."
            )


def inspect_clue(world: World, detective: Entity, cause: Cause) -> None:
    clue = world.get("clue")
    clue.meters["measured"] += 1
    detective.memes["suspicion"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{detective.id} knelt down and picked up the clue. It was only a millimeter-sized bit of {cause.clue}."
    )
    world.say(
        f'"That is tiny," {detective.pronoun()} whispered. "But tiny clues can still tell the truth."'
    )


def follow_sound(world: World, detective: Entity, sound: SoundTrail, setting: Setting) -> None:
    detective.memes["focus"] += 1
    world.say(
        f"Then {detective.id} held still and listened. From {setting.sound_source} came {sound.effect}."
    )
    world.say(
        f"{detective.pronoun().capitalize()} {sound.verb} toward {sound.source}, following the sound like a real little detective."
    )


def find_sheets(world: World, detective: Entity, helper: Entity, setting: Setting) -> None:
    sheets = world.get("sheets")
    sheets.meters["found"] += 1
    sheets.meters["hidden"] = 0.0
    helper.memes["guilt"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Behind {setting.hide_spot}, {detective.id} found the missing questionnaire stack, a little bent but still usable."
    )
    world.say(
        f"{helper.id} gasped softly. {helper.pronoun().capitalize()} looked as if a secret had grown too heavy to hold."
    )


def gentle_question(world: World, detective: Entity, helper: Entity, response: Response) -> None:
    detective.memes["kindness"] += 1
    helper.memes["fear"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{detective.id} did not point or accuse. "{response.line}" {detective.pronoun()} said.'
    )


def confession(world: World, helper: Entity, cause: Cause) -> None:
    helper.memes["truth"] += 1
    world.say(
        f"{helper.id} took a breath. {cause.confession}"
    )


def repair(world: World, teacher: Entity, detective: Entity, helper: Entity,
           response: Response, setting: Setting, sheets: SheetSet) -> None:
    detective.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    helper.memes["guilt"] = 0.0
    helper.memes["fear"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{teacher.id} nodded and helped smooth the edges of the {sheets.label}. {response.repair}"
    )
    world.say(
        f"Together they set the stack back on the table, and the room felt lighter."
    )
    world.say(
        f"By the end, {setting.ending_image}"
    )


def tell(setting: Setting, cause: Cause, sheets_cfg: SheetSet, sound: SoundTrail,
         response: Response, detective_name: str = "Nora", detective_gender: str = "girl",
         helper_name: str = "Ben", helper_gender: str = "boy",
         teacher_name: str = "Ms. June", teacher_gender: str = "teacher_f") -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        role="detective",
        label=detective_name,
        traits=["observant", "gentle"],
        tags={"detective"},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        label=helper_name,
        traits=["helpful", "hurried"],
        tags={"helper"},
    ))
    teacher = world.add(Entity(
        id=teacher_name,
        kind="character",
        type=teacher_gender,
        role="teacher",
        label="the teacher",
        attrs={"host_line": setting.host},
        tags={"teacher"},
    ))
    world.add(Entity(
        id="sheets",
        type="paper",
        label=sheets_cfg.label,
        phrase=sheets_cfg.phrase,
        tags=set(sheets_cfg.tags),
    ))
    world.add(Entity(
        id="clue",
        type="clue",
        label="tiny clue",
        phrase="a tiny clue",
        tags={"clue"},
    ))
    world.add(Entity(
        id="sound",
        type="sound",
        label=sound.effect,
        phrase=sound.effect,
        tags=set(sound.tags),
    ))

    introduce(world, detective, helper, teacher, setting, sheets_cfg)
    start_activity(world, detective, helper, sheets_cfg)

    world.para()
    hurry_mistake(world, helper, cause, setting)
    notice_problem(world, teacher, helper, sheets_cfg)

    world.para()
    inspect_clue(world, detective, cause)
    follow_sound(world, detective, sound, setting)
    find_sheets(world, detective, helper, setting)

    world.para()
    gentle_question(world, detective, helper, response)
    confession(world, helper, cause)
    repair(world, teacher, detective, helper, response, setting, sheets_cfg)

    world.facts.update(
        detective=detective,
        helper=helper,
        teacher=teacher,
        setting=setting,
        cause=cause,
        sheets_cfg=sheets_cfg,
        sound=sound,
        response=response,
        clue_size_mm=cause.clue_size_mm,
        hidden_found=world.get("sheets").meters["found"] >= THRESHOLD,
        kindness_used=detective.memes["kindness"] >= THRESHOLD,
        blameless=cause.blameless,
    )
    return world


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="the sunny classroom",
        host=' "When every sheet is back, our whodunit game can begin."',
        storage="the art shelf",
        sound_source="the block corner",
        hide_spot="the rolling map stand",
        ending_image="the children sat in a circle, answering and guessing with smiles instead of worries",
        tags={"school"},
    ),
    "library": Setting(
        id="library",
        place="the little library room",
        host=' "We will trade questionnaires and make gentle guesses in a minute."',
        storage="the low return cart",
        sound_source="the puppet basket",
        hide_spot="the big cushion bin",
        ending_image="the children curled up by the rug, sharing answers while the puppet basket stayed still at last",
        tags={"library"},
    ),
    "clubroom": Setting(
        id="clubroom",
        place="the after-school clubroom",
        host=' "Fill these out, and then we will play our mystery matching game."',
        storage="the craft cupboard",
        sound_source="the dress-up box",
        hide_spot="the folded stage curtain",
        ending_image="the group leaned over the questionnaires together, and the room buzzed with playful guesses instead of blame",
        tags={"club"},
    ),
}

CAUSES = {
    "hurry_trip": Cause(
        id="hurry_trip",
        label="hurried trip",
        blameless=True,
        noise="rattle",
        clue="a silver star sticker",
        clue_size_mm=1,
        action="hurried to carry too many things at once and bumped the storage shelf",
        confession='"I was in such a hurry to help that I dropped the stack, and I got embarrassed when it slid away," said the helper.',
        tags={"hurry", "accident"},
    ),
    "hurry_tidy": Cause(
        id="hurry_tidy",
        label="hurried tidy",
        blameless=True,
        noise="rustle",
        clue="a blue corner from one paper band",
        clue_size_mm=1,
        action="tried to tidy faster than careful hands could manage",
        confession='"I wanted the table to look perfect before anyone noticed the mess, so I tucked the stack away and then could not reach it," said the helper.',
        tags={"hurry", "mistake"},
    ),
    "prank": Cause(
        id="prank",
        label="small prank",
        blameless=False,
        noise="thump",
        clue="a red paper dot",
        clue_size_mm=1,
        action="hid the stack for one silly second, thinking it would be funny",
        confession='"I hid them as a prank, but as soon as everyone looked worried, I wished I had not done it," said the helper.',
        tags={"prank"},
    ),
}

SHEETS = {
    "favorites": SheetSet(
        id="favorites",
        label="questionnaire sheets",
        phrase="a neat pile of favorite-things questionnaire sheets",
        purpose="to help the children guess whose answers were whose",
        tags={"questionnaire", "paper"},
    ),
    "club_questions": SheetSet(
        id="club_questions",
        label="questionnaire cards",
        phrase="a stack of club questionnaire cards",
        purpose="to help the group learn kind little facts about one another",
        tags={"questionnaire", "cards"},
    ),
}

SOUNDS = {
    "rattle_blocks": SoundTrail(
        id="rattle_blocks",
        effect="rattle-rattle",
        verb="tiptoed",
        source="rattle",
        tags={"sound", "rattle"},
    ),
    "rustle_paper": SoundTrail(
        id="rustle_paper",
        effect="rustle-rustle",
        verb="crept",
        source="rustle",
        tags={"sound", "rustle"},
    ),
    "thump_box": SoundTrail(
        id="thump_box",
        effect="thump-thump",
        verb="padded",
        source="thump",
        tags={"sound", "thump"},
    ),
}

RESPONSES = {
    "gentle_check": Response(
        id="gentle_check",
        sense=3,
        line="I think something surprising happened. You can tell me, and I will listen kindly",
        repair="The helper helped pass the sheets out and said sorry to everyone.",
        lesson="Kind questions make it easier to tell the truth.",
        tags={"kindness", "truth"},
    ),
    "share_blame": Response(
        id="share_blame",
        sense=2,
        line="We can fix this together. Was it an accident, or did something feel hard to say",
        repair="The helper told the truth, and the detective stayed beside them while they fixed the problem.",
        lesson="Kindness can hold the truth steady.",
        tags={"kindness", "repair"},
    ),
    "sharp_accuse": Response(
        id="sharp_accuse",
        sense=1,
        line="You did it, and everyone knows it",
        repair="No one felt calm enough to explain right away.",
        lesson="Blame makes a mystery feel worse.",
        tags={"blame"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Anna", "Ella", "Maya"]
BOY_NAMES = ["Ben", "Theo", "Max", "Sam", "Leo", "Eli", "Noah", "Finn"]
TEACHERS_F = ["Ms. June", "Ms. Poppy", "Ms. Wren"]
TEACHERS_M = ["Mr. Reed", "Mr. Hale", "Mr. Moss"]


@dataclass
class StoryParams:
    setting: str
    cause: str
    sheets: str
    sound: str
    response: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    teacher_name: str
    teacher_gender: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "questionnaire": [
        (
            "What is a questionnaire?",
            "A questionnaire is a paper or card with questions on it. People fill it in so others can learn little facts about them."
        )
    ],
    "millimeter": [
        (
            "What is a millimeter?",
            "A millimeter is a very tiny unit of length. It is so small that a little paper speck can be only one millimeter wide."
        )
    ],
    "sound": [
        (
            "Why can sound help solve a mystery?",
            "Sound tells you where something is happening, even before you see it. Listening carefully can help you find a hidden thing."
        )
    ],
    "kindness": [
        (
            "Why does kindness help when someone made a mistake?",
            "Kindness helps people feel safe enough to tell the truth. Then everyone can fix the problem instead of staying scared."
        )
    ],
    "truth": [
        (
            "Why is it good to tell the truth after a mistake?",
            "Telling the truth helps people understand what happened. It is the first step toward making things right."
        )
    ],
    "hurry": [
        (
            "Why can hurry cause problems?",
            "When people rush, they may miss small details or drop things. Slowing down can help hands and minds stay careful."
        )
    ],
}
KNOWLEDGE_ORDER = ["questionnaire", "millimeter", "sound", "kindness", "truth", "hurry"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    setting = f["setting"]
    cause = f["cause"]
    sheets = f["sheets_cfg"]
    return [
        f'Write a child-friendly whodunit set in {setting.place} that includes the words "hurry", "millimeter", and "questionnaire".',
        f"Tell a gentle mystery where {detective.id} follows a tiny clue and a sound effect to find some missing {sheets.label}.",
        f"Write a small whodunit where {helper.id}'s {cause.label} causes trouble, but kindness helps the truth come out in the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    teacher = f["teacher"]
    setting = f["setting"]
    cause = f["cause"]
    sheets = f["sheets_cfg"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child who likes solving mysteries, and {helper.id}, who was trying to help during the questionnaire game. {teacher.id} also guided the room when the sheets went missing."
        ),
        (
            f"What went missing in {setting.place}?",
            f"The missing thing was the stack of {sheets.label}. Without them, the children could not finish their guessing game."
        ),
        (
            "What clue did the detective find?",
            f"{detective.id} found a clue only about {f['clue_size_mm']} millimeter wide: {cause.clue}. The tiny clue mattered because it showed where the missing stack had brushed past."
        ),
        (
            "How did sound help solve the mystery?",
            f"{detective.id} listened for {f['sound'].effect} and followed it carefully. The sound pointed toward the hiding place where the questionnaire stack had slipped."
        ),
        (
            f"Why were the sheets missing?",
            f"They were missing because {helper.id} {cause.action}. The trouble came from {cause.label}, not from a grand crime."
        ),
    ]
    if f["blameless"]:
        qa.append(
            (
                f"Was {helper.id} trying to be mean?",
                f"No. {helper.id} made a mistake while in a hurry and then felt too embarrassed to speak up at once. The story shows that accidents can still be fixed when people tell the truth."
            )
        )
    else:
        qa.append(
            (
                f"Did {helper.id} mean to hide the sheets?",
                f"Yes, but only as a brief prank, not to truly ruin the game. As soon as everyone looked worried, {helper.id} felt sorry and wished to fix it."
            )
        )
    qa.append(
        (
            "How was kindness part of the solution?",
            f"{detective.id} asked gently instead of accusing anyone. Because of that kind question, {helper.id} felt safe enough to tell the truth and help repair the problem."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"The sheets were returned, the children kept the game, and the room felt calm again. {response.lesson}"
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"questionnaire", "millimeter", "sound", "kindness", "truth"}
    if world.facts["cause"].id.startswith("hurry"):
        tags.add("hurry")
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
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="classroom",
        cause="hurry_trip",
        sheets="favorites",
        sound="rattle_blocks",
        response="gentle_check",
        detective_name="Nora",
        detective_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        teacher_name="Ms. June",
        teacher_gender="teacher_f",
    ),
    StoryParams(
        setting="library",
        cause="hurry_tidy",
        sheets="club_questions",
        sound="rustle_paper",
        response="share_blame",
        detective_name="Theo",
        detective_gender="boy",
        helper_name="Mia",
        helper_gender="girl",
        teacher_name="Mr. Reed",
        teacher_gender="teacher_m",
    ),
    StoryParams(
        setting="clubroom",
        cause="prank",
        sheets="favorites",
        sound="thump_box",
        response="gentle_check",
        detective_name="Ava",
        detective_gender="girl",
        helper_name="Leo",
        helper_gender="boy",
        teacher_name="Ms. Poppy",
        teacher_gender="teacher_f",
    ),
]


ASP_RULES = r"""
match_sound(C, S) :- cause(C), sound(S), noise_of(C, N), source_of(S, N).
kind_response(R)  :- response(R), sense(R, S), kindness_min(M), S >= M.
valid(St, C, Sh, So) :- setting(St), cause(C), sheets(Sh), sound(So), match_sound(C, So).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("noise_of", cid, cause.noise))
    for shid in SHEETS:
        lines.append(asp.fact("sheets", shid))
    for soid, sound in SOUNDS.items():
        lines.append(asp.fact("sound", soid))
        lines.append(asp.fact("source_of", soid, sound.source))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
    lines.append(asp.fact("kindness_min", KINDNESS_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_kind_responses() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show kind_response/1."))
    return sorted(r for (r,) in asp.atoms(model, "kind_response"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a gentle child whodunit with hurry, a millimeter clue, and a questionnaire."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--sheets", choices=SHEETS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--detective-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--teacher-gender", choices=["teacher_f", "teacher_m"])
    ap.add_argument("--teacher-name")
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def _pick_teacher(rng: random.Random, gender: str) -> str:
    return rng.choice(TEACHERS_F if gender == "teacher_f" else TEACHERS_M)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.sound:
        cause = CAUSES[args.cause]
        sound = SOUNDS[args.sound]
        if not sound_matches(cause, sound):
            raise StoryError(explain_rejection(cause, sound))
    if args.response and RESPONSES[args.response].sense < KINDNESS_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.cause is None or combo[1] == args.cause)
        and (args.sheets is None or combo[2] == args.sheets)
        and (args.sound is None or combo[3] == args.sound)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, cause_id, sheets_id, sound_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in kind_responses()))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or _pick_name(rng, detective_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=detective_name)
    teacher_gender = args.teacher_gender or rng.choice(["teacher_f", "teacher_m"])
    teacher_name = args.teacher_name or _pick_teacher(rng, teacher_gender)

    return StoryParams(
        setting=setting_id,
        cause=cause_id,
        sheets=sheets_id,
        sound=sound_id,
        response=response_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        teacher_name=teacher_name,
        teacher_gender=teacher_gender,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        cause = CAUSES[params.cause]
        sheets = SHEETS[params.sheets]
        sound = SOUNDS[params.sound]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from err

    if not sound_matches(cause, sound):
        raise StoryError(explain_rejection(cause, sound))
    if response.sense < KINDNESS_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        setting=setting,
        cause=cause,
        sheets_cfg=sheets,
        sound=sound,
        response=response,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        teacher_name=params.teacher_name,
        teacher_gender=params.teacher_gender,
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
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_kind = set(asp_kind_responses())
    p_kind = {r.id for r in kind_responses()}
    if c_kind == p_kind:
        print(f"OK: kind responses match ({sorted(c_kind)}).")
    else:
        rc = 1
        print(f"MISMATCH in kind responses: clingo={sorted(c_kind)} python={sorted(p_kind)}")

    smoke_cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            smoke_cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving params for seed {seed}.")
            break

    try:
        sample = generate(smoke_cases[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show kind_response/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"kind responses: {', '.join(asp_kind_responses())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, cause, sheets, sound) combos:\n")
        for setting_id, cause_id, sheets_id, sound_id in combos:
            print(f"  {setting_id:10} {cause_id:11} {sheets_id:14} {sound_id}")
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
            header = f"### {p.detective_name} and {p.helper_name}: {p.cause} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
