#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/snooze_transfix_segment_surprise_whodunit.py
=======================================================================

A small storyworld for a child-friendly whodunit: right before the surprise
segment of a school show, the class bell goes missing. A young detective notices
clues, rules out innocent suspects, and discovers who moved the bell and why.

The seed words are built into the story world itself:
- "snooze" appears in the suspects' behavior and in grounded Q&A.
- "transfix" appears in the puppet-stage distraction beat.
- "segment" is the named final part of the show that needs the bell.

Run it
------
    python storyworlds/worlds/gpt-5.4/snooze_transfix_segment_surprise_whodunit.py
    python storyworlds/worlds/gpt-5.4/snooze_transfix_segment_surprise_whodunit.py --culprit omar --reason rehearse --hide-place music_cubby
    python storyworlds/worlds/gpt-5.4/snooze_transfix_segment_surprise_whodunit.py --culprit omar --reason protect
    python storyworlds/worlds/gpt-5.4/snooze_transfix_segment_surprise_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/snooze_transfix_segment_surprise_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4/snooze_transfix_segment_surprise_whodunit.py --verify
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
        if self.type in {"mother", "teacher_f"}:
            return "teacher"
        if self.type in {"father", "teacher_m"}:
            return "teacher"
        return self.label or self.type


@dataclass
class SuspectSpec:
    id: str
    name: str
    type: str
    role_label: str
    intro: str
    tags: set[str] = field(default_factory=set)
    clue_line: str = ""


@dataclass
class Reason:
    id: str
    label: str
    wanted: str
    requires_any: set[str] = field(default_factory=set)
    place_needs_any: set[str] = field(default_factory=set)
    clue: str = ""
    find_line: str = ""
    confession: str = ""
    lesson: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class HidePlace:
    id: str
    label: str
    phrase: str
    where_line: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_missing_worry(world: World) -> list[str]:
    bell = world.entities.get("bell")
    if bell is None or bell.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    teacher = world.get("teacher")
    detective = world.get("detective")
    teacher.memes["worry"] += 1
    detective.memes["curiosity"] += 1
    for ent in world.characters():
        if ent.role == "suspect":
            ent.memes["nervous"] += 0.3
    return []


def _r_clue_focus(world: World) -> list[str]:
    if world.facts.get("clue_found") is not True:
        return []
    sig = ("clue_focus",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective = world.get("detective")
    culprit = world.get(world.facts["culprit"].id)
    detective.memes["confidence"] += 1
    culprit.memes["guilt"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    bell = world.entities.get("bell")
    if bell is None or bell.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    teacher = world.get("teacher")
    detective = world.get("detective")
    teacher.memes["worry"] = 0.0
    teacher.memes["relief"] += 1
    detective.memes["relief"] += 1
    detective.memes["surprise"] += 1
    for ent in world.characters():
        if ent.role == "suspect":
            ent.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="social", apply=_r_missing_worry),
    Rule(name="clue_focus", tag="social", apply=_r_clue_focus),
    Rule(name="found_relief", tag="social", apply=_r_found_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            result = rule.apply(world)
            if result:
                produced.extend(result)
                changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SUSPECTS = {
    "june": SuspectSpec(
        id="june",
        name="June",
        type="girl",
        role_label="ribbon captain",
        intro="June stood by the craft table with a loop of blue ribbon around her wrist.",
        tags={"crafty", "careful"},
        clue_line="A tiny blue ribbon shaving curled near June's shoe.",
    ),
    "pip": SuspectSpec(
        id="pip",
        name="Pip",
        type="boy",
        role_label="cleanup helper",
        intro="Pip was carrying a dish towel and checking every wobbly cup like a tiny grown-up.",
        tags={"helper", "careful"},
        clue_line="One damp towel thread clung to Pip's sleeve.",
    ),
    "omar": SuspectSpec(
        id="omar",
        name="Omar",
        type="boy",
        role_label="drum helper",
        intro="Omar sat near the curtain, fighting a little snooze after drum practice.",
        tags={"performer", "sleepy"},
        clue_line="A chalky music note smudged the side of Omar's hand.",
    ),
}

REASONS = {
    "decorate": Reason(
        id="decorate",
        label="decorate",
        wanted="add a bow before the surprise segment",
        requires_any={"crafty", "helper"},
        place_needs_any={"craft", "backstage"},
        clue="a trail of blue ribbon snips",
        find_line="Inside was the bell, freshly polished and wearing a neat blue bow.",
        confession='"{bell_name} was too plain for the surprise segment," {culprit} admitted. "I only wanted it to look special."',
        lesson="A good surprise still needs to be told to the teacher first.",
        tags={"ribbon", "surprise"},
    ),
    "protect": Reason(
        id="protect",
        label="protect",
        wanted="keep the bell safe from a spill",
        requires_any={"careful", "helper"},
        place_needs_any={"safe"},
        clue="a damp towel thread and a dry ring on the table",
        find_line="There was the bell, tucked away where no juice or paint could splash it.",
        confession='"{bell_name} was right beside the wobbling juice pitcher," {culprit} said. "I moved it so it would not get sticky."',
        lesson="Helping is kind, but secret helping can still scare everyone.",
        tags={"safety", "spill"},
    ),
    "rehearse": Reason(
        id="rehearse",
        label="rehearse",
        wanted="practice the entrance chime",
        requires_any={"performer"},
        place_needs_any={"music", "backstage"},
        clue="a chalky music note and the faintest little ding",
        find_line="The bell was there beside the practice drum, ready for one more tiny chime.",
        confession=''"I wanted the opening ding to sound perfect," {culprit} whispered. "I was going to bring it right back."',
        lesson="Practice is fine, but borrowed things must be borrowed out loud.",
        tags={"music", "practice"},
    ),
}

HIDE_PLACES = {
    "costume_box": HidePlace(
        id="costume_box",
        label="costume box",
        phrase="the starry costume box by the curtain",
        where_line="The clue pointed to the starry costume box by the curtain.",
        tags={"craft", "backstage"},
    ),
    "window_shelf": HidePlace(
        id="window_shelf",
        label="window shelf",
        phrase="the high window shelf near the paper stars",
        where_line="The clue led to the high window shelf near the paper stars.",
        tags={"craft", "safe"},
    ),
    "teacher_cabinet": HidePlace(
        id="teacher_cabinet",
        label="teacher cabinet",
        phrase="the short teacher cabinet beside the sink",
        where_line="The clue led straight to the short teacher cabinet beside the sink.",
        tags={"safe"},
    ),
    "music_cubby": HidePlace(
        id="music_cubby",
        label="music cubby",
        phrase="the music cubby behind the little drum",
        where_line="The clue drifted toward the music cubby behind the little drum.",
        tags={"music", "backstage"},
    ),
}


@dataclass
class StoryParams:
    culprit: str
    reason: str
    hide_place: str
    detective_name: str
    detective_gender: str
    teacher_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        culprit="june",
        reason="decorate",
        hide_place="costume_box",
        detective_name="Mina",
        detective_gender="girl",
        teacher_type="teacher_f",
    ),
    StoryParams(
        culprit="pip",
        reason="protect",
        hide_place="teacher_cabinet",
        detective_name="Nico",
        detective_gender="boy",
        teacher_type="teacher_m",
    ),
    StoryParams(
        culprit="omar",
        reason="rehearse",
        hide_place="music_cubby",
        detective_name="Tara",
        detective_gender="girl",
        teacher_type="teacher_f",
    ),
    StoryParams(
        culprit="june",
        reason="decorate",
        hide_place="window_shelf",
        detective_name="Leo",
        detective_gender="boy",
        teacher_type="teacher_m",
    ),
]

DETECTIVE_NAMES_GIRL = ["Mina", "Tara", "Lila", "Eva", "Nora", "Sana"]
DETECTIVE_NAMES_BOY = ["Nico", "Arlo", "Ben", "Milo", "Theo", "Evan"]


def suspect_can_do(suspect_id: str, reason_id: str) -> bool:
    suspect = SUSPECTS[suspect_id]
    reason = REASONS[reason_id]
    return bool(suspect.tags & reason.requires_any)


def place_fits(reason_id: str, hide_place_id: str) -> bool:
    reason = REASONS[reason_id]
    place = HIDE_PLACES[hide_place_id]
    return bool(place.tags & reason.place_needs_any)


def valid_combo(culprit: str, reason: str, hide_place: str) -> bool:
    return culprit in SUSPECTS and reason in REASONS and hide_place in HIDE_PLACES and suspect_can_do(culprit, reason) and place_fits(reason, hide_place)


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for culprit in SUSPECTS:
        for reason in REASONS:
            for hide_place in HIDE_PLACES:
                if valid_combo(culprit, reason, hide_place):
                    out.append((culprit, reason, hide_place))
    return out


def explain_rejection(culprit: str, reason: str, hide_place: str) -> str:
    if culprit in SUSPECTS and reason in REASONS and not suspect_can_do(culprit, reason):
        return (
            f"(No story: {SUSPECTS[culprit].name} is not the kind of child who would "
            f"{REASONS[reason].wanted}. Pick a culprit whose role fits that reason.)"
        )
    if reason in REASONS and hide_place in HIDE_PLACES and not place_fits(reason, hide_place):
        return (
            f"(No story: {HIDE_PLACES[hide_place].phrase} does not fit the reason "
            f'"{REASONS[reason].wanted}". The hiding place should match the clue and the plan.)'
        )
    return "(No valid combination matches the given options.)"


def missing_bell(world: World) -> None:
    bell = world.get("bell")
    bell.meters["missing"] += 1
    propagate(world, narrate=False)


def clue_search(world: World) -> None:
    world.facts["clue_found"] = True
    propagate(world, narrate=False)


def find_bell(world: World) -> None:
    bell = world.get("bell")
    bell.meters["missing"] = 0.0
    bell.meters["found"] += 1
    propagate(world, narrate=False)


def setup_story(world: World, detective: Entity, teacher: Entity) -> None:
    world.say(
        f"On the day of the class show, {detective.id} helped set tiny chairs in neat rows while "
        f"{teacher.label_word} pinned silver stars around the room."
    )
    world.say(
        'At the end of the show there would be a surprise segment, and one clear bell was supposed '
        "to ring at the very start."
    )
    world.say(
        f"{detective.id} loved mysteries, so {detective.pronoun()} watched everything with bright, quiet eyes."
    )


def suspects_scene(world: World) -> None:
    ordered = [SUSPECTS["june"], SUSPECTS["pip"], SUSPECTS["omar"]]
    for spec in ordered:
        world.say(spec.intro)
    world.say(
        "On the puppet stage, a cardboard dragon seemed to transfix the room whenever anyone looked its way."
    )


def bell_goes_missing(world: World, detective: Entity, teacher: Entity) -> None:
    missing_bell(world)
    world.say(
        f"When {teacher.label_word} reached for the bell, the velvet stool was empty."
    )
    world.say(
        f'"The surprise segment starts in a minute," {teacher.label_word} said. "Where did the bell go?"'
    )
    world.say(
        f"{detective.id} did not shout. {detective.pronoun().capitalize()} just stepped closer and looked for the smallest odd thing."
    )


def first_questions(world: World, detective: Entity) -> None:
    world.say(
        f'{detective.id} asked softly, "Who touched the stool after lunch?"'
    )
    world.say(
        "Nobody said, 'I took it.' That made the mystery feel even bigger."
    )


def inspect_clue(world: World, detective: Entity, reason: Reason, culprit_spec: SuspectSpec) -> None:
    clue_search(world)
    world.say(
        f"Near the stool, {detective.id} spotted {reason.clue}."
    )
    world.say(
        f"{culprit_spec.clue_line} That was enough to make {detective.pronoun('object')} think, but not enough to accuse anyone yet."
    )


def follow_clue(world: World, detective: Entity, place: HidePlace, reason: Reason) -> None:
    world.say(place.where_line)
    world.say(
        f"{detective.id} opened it carefully. {reason.find_line}"
    )


def reveal(world: World, detective: Entity, culprit: Entity, bell: Entity, reason: Reason, teacher: Entity) -> None:
    find_bell(world)
    culprit.memes["honesty"] += 1
    bell.attrs["location"] = "returned"
    culprit_name = culprit.id
    bell_name = bell.label
    world.say(
        f'{detective.id} turned and said, "I know who moved the {bell.label}."'
    )
    world.say(
        reason.confession.format(culprit=culprit_name, bell_name=bell_name)
    )
    world.say(
        f"{teacher.label_word.capitalize()} let out a slow breath. Nobody had stolen anything after all."
    )


def ending(world: World, detective: Entity, culprit: Entity, bell: Entity, reason: Reason, teacher: Entity) -> None:
    detective.memes["pride"] += 1
    culprit.memes["relief"] += 1
    world.say(
        f'{teacher.label_word.capitalize()} smiled a little and said, "Next time, tell me before you carry off the {bell.label}."'
    )
    world.say(
        f"{culprit.id} nodded hard. {reason.lesson}"
    )
    world.say(
        f"Then the bell rang bright and clear, the surprise segment began, and {detective.id} grinned because the room had gone from worried to warm again."
    )


def tell(params: StoryParams) -> World:
    culprit_spec = SUSPECTS[params.culprit]
    reason = REASONS[params.reason]
    place = HIDE_PLACES[params.hide_place]

    world = World()
    detective = world.add(
        Entity(
            id=params.detective_name,
            kind="character",
            type=params.detective_gender,
            role="detective",
            label=params.detective_name,
            traits=["observant", "kind"],
        )
    )
    teacher = world.add(
        Entity(
            id="Teacher",
            kind="character",
            type=params.teacher_type,
            role="teacher",
            label="the teacher",
            traits=["calm"],
        )
    )
    bell = world.add(
        Entity(
            id="bell",
            kind="thing",
            type="bell",
            label="silver bell",
            phrase="the silver bell",
            attrs={"location": "stool"},
        )
    )

    for sid, spec in SUSPECTS.items():
        world.add(
            Entity(
                id=spec.name,
                kind="character",
                type=spec.type,
                role="suspect",
                label=spec.name,
                phrase=spec.role_label,
                tags=set(spec.tags),
                attrs={"suspect_id": sid, "role_label": spec.role_label},
            )
        )

    setup_story(world, detective, teacher)
    world.para()
    suspects_scene(world)
    bell_goes_missing(world, detective, teacher)
    first_questions(world, detective)
    world.para()
    inspect_clue(world, detective, reason, culprit_spec)
    follow_clue(world, detective, place, reason)
    world.para()
    culprit_ent = world.get(culprit_spec.name)
    reveal(world, detective, culprit_ent, bell, reason, teacher)
    ending(world, detective, culprit_ent, bell, reason, teacher)

    world.facts.update(
        detective=detective,
        teacher=teacher,
        bell=bell,
        culprit=culprit_spec,
        reason=reason,
        hide_place=place,
        suspects=list(SUSPECTS.values()),
        solved=True,
        surprise=True,
        culprit_name=culprit_spec.name,
        clue=reason.clue,
        final_location=place.label,
    )
    return world


KNOWLEDGE = {
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a problem with missing information. You solve it by noticing clues and thinking carefully."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. It does not shout the answer, but it points you in the right direction."
        )
    ],
    "surprise": [
        (
            "What is a surprise?",
            "A surprise is something you did not expect. A fun surprise should still be safe and should not make everyone worry."
        )
    ],
    "bell": [
        (
            "What does a bell do?",
            "A bell makes a clear ringing sound. People can use it to call attention or mark the start of something."
        )
    ],
    "backstage": [
        (
            "What does backstage mean?",
            "Backstage means the area behind or beside a stage where people keep props and get ready. It is often full of boxes, curtains, and waiting performers."
        )
    ],
    "practice": [
        (
            "Why do people practice before a show?",
            "People practice so they know what to do and when to do it. Practice helps a show feel smooth and confident."
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "clue", "surprise", "bell", "backstage", "practice"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    culprit = f["culprit"]
    reason = f["reason"]
    return [
        'Write a short whodunit story for a 3-to-5-year-old that includes the words "snooze", "transfix", and "segment".',
        f"Tell a gentle mystery where {detective.id} notices a missing bell just before a surprise segment and solves the case by following one small clue.",
        f"Write a child-friendly whodunit in which {culprit.name} moved the bell to {reason.wanted}, and the ending reveals the surprise was not a theft at all.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    teacher = f["teacher"]
    culprit = f["culprit"]
    reason = f["reason"]
    place = f["hide_place"]
    bell = f["bell"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child who likes mysteries, and a class getting ready for a show. It is also about {culprit.name}, who moved the {bell.label} for a secret reason."
        ),
        (
            f"What problem happened before the surprise segment?",
            f"The {bell.label} was missing right before the surprise segment was supposed to begin. That made the room feel worried because the bell was the signal for the show."
        ),
        (
            "What clue helped solve the mystery?",
            f"The clue was {reason.clue}. That small sign guided {detective.id} toward {place.phrase} instead of letting the mystery stay a guessing game."
        ),
        (
            f"Where was the bell found?",
            f"The bell was found in {place.phrase}. {detective.id} looked there because the clue matched that hiding place."
        ),
        (
            f"Why did {culprit.name} move the bell?",
            f"{culprit.name} moved it to {reason.wanted}. It was not meant as stealing, but keeping the plan secret made everyone think something was wrong."
        ),
        (
            f"How did the story use the words snooze and transfix?",
            f"Omar was fighting a little snooze by the curtain, and the puppet dragon could almost transfix the room. Those details made the mystery scene feel busy and lively while {detective.id} searched for the truth."
        ),
        (
            "How did the story end?",
            f"The bell came back, the teacher understood what had happened, and the surprise segment could begin. The ending shows that the room changed from worry to relief once the truth was spoken aloud."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mystery", "clue", "surprise", "bell"}
    place = world.facts["hide_place"]
    reason = world.facts["reason"]
    if "backstage" in place.tags or "music" in place.tags:
        tags.add("backstage")
    if reason.id == "rehearse":
        tags.add("practice")
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
can_do(S, R) :- suspect_tag(S, T), reason_needs(R, T).
place_ok(R, P) :- place_tag(P, T), reason_place(R, T).
valid(S, R, P) :- suspect(S), reason(R), hide_place(P), can_do(S, R), place_ok(R, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        for tag in sorted(suspect.tags):
            lines.append(asp.fact("suspect_tag", sid, tag))
    for rid, reason in REASONS.items():
        lines.append(asp.fact("reason", rid))
        for tag in sorted(reason.requires_any):
            lines.append(asp.fact("reason_needs", rid, tag))
        for tag in sorted(reason.place_needs_any):
            lines.append(asp.fact("reason_place", rid, tag))
    for pid, place in HIDE_PLACES.items():
        lines.append(asp.fact("hide_place", pid))
        for tag in sorted(place.tags):
            lines.append(asp.fact("place_tag", pid, tag))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - python_set:
            print("  only in clingo:", sorted(asp_set - python_set))
        if python_set - asp_set:
            print("  only in python:", sorted(python_set - asp_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    checked = 0
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Empty story in random smoke test.")
            checked += 1
        except Exception as err:
            rc = 1
            print(f"RANDOM SMOKE TEST FAILED at seed {seed}: {err}")
            break
    if rc == 0:
        print(f"OK: random smoke tests passed ({checked} scenarios).")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child-friendly whodunit with a missing bell before a surprise segment."
    )
    ap.add_argument("--culprit", choices=sorted(SUSPECTS))
    ap.add_argument("--reason", choices=sorted(REASONS))
    ap.add_argument("--hide-place", choices=sorted(HIDE_PLACES), dest="hide_place")
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--teacher", choices=["teacher_f", "teacher_m"], dest="teacher_type")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.culprit and args.reason and not suspect_can_do(args.culprit, args.reason):
        hide = args.hide_place or next(iter(HIDE_PLACES))
        raise StoryError(explain_rejection(args.culprit, args.reason, hide))
    if args.reason and args.hide_place and not place_fits(args.reason, args.hide_place):
        culprit = args.culprit or next(iter(SUSPECTS))
        raise StoryError(explain_rejection(culprit, args.reason, args.hide_place))

    combos = [
        combo
        for combo in valid_combos()
        if (args.culprit is None or combo[0] == args.culprit)
        and (args.reason is None or combo[1] == args.reason)
        and (args.hide_place is None or combo[2] == args.hide_place)
    ]
    if not combos:
        culprit = args.culprit or next(iter(SUSPECTS))
        reason = args.reason or next(iter(REASONS))
        hide_place = args.hide_place or next(iter(HIDE_PLACES))
        raise StoryError(explain_rejection(culprit, reason, hide_place))

    culprit, reason, hide_place = rng.choice(sorted(combos))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or rng.choice(
        DETECTIVE_NAMES_GIRL if detective_gender == "girl" else DETECTIVE_NAMES_BOY
    )
    teacher_type = args.teacher_type or rng.choice(["teacher_f", "teacher_m"])
    return StoryParams(
        culprit=culprit,
        reason=reason,
        hide_place=hide_place,
        detective_name=detective_name,
        detective_gender=detective_gender,
        teacher_type=teacher_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.culprit not in SUSPECTS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.reason not in REASONS:
        raise StoryError(f"(Unknown reason: {params.reason})")
    if params.hide_place not in HIDE_PLACES:
        raise StoryError(f"(Unknown hide place: {params.hide_place})")
    if not valid_combo(params.culprit, params.reason, params.hide_place):
        raise StoryError(explain_rejection(params.culprit, params.reason, params.hide_place))

    world = tell(params)
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (culprit, reason, hide_place) combos:\n")
        for culprit, reason, hide_place in combos:
            print(f"  {culprit:5} {reason:9} {hide_place}")
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
            header = f"### {p.detective_name}: {p.culprit} / {p.reason} / {p.hide_place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
