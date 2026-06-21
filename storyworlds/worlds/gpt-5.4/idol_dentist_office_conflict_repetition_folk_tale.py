#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/idol_dentist_office_conflict_repetition_folk_tale.py
================================================================================

A standalone story world for a small folk-tale-like story set in a dentist
office. A child clings to a tiny idol for courage, refuses repeated requests to
set it aside, and a calm dentist solves the conflict with a repeated ritual that
proves the idol can "watch" safely from a clean special place.

This world models:
- typed entities with physical meters and emotional memes
- a short state-driven conflict with repetition
- a reasonableness gate over which comfort object, exam, and safe perch fit
- an inline ASP twin for parity with the Python gate and outcome model

Run it
------
    python storyworlds/worlds/gpt-5.4/idol_dentist_office_conflict_repetition_folk_tale.py
    python storyworlds/worlds/gpt-5.4/idol_dentist_office_conflict_repetition_folk_tale.py --idol lucky_elephant
    python storyworlds/worlds/gpt-5.4/idol_dentist_office_conflict_repetition_folk_tale.py --exam xray --perch tray
    python storyworlds/worlds/gpt-5.4/idol_dentist_office_conflict_repetition_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/idol_dentist_office_conflict_repetition_folk_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/idol_dentist_office_conflict_repetition_folk_tale.py --verify
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

# Make storyworlds/results.py importable when run directly from this nested dir.
THIS = os.path.abspath(__file__)
STORYWORLDS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(THIS)))   # .../storyworlds
sys.path.insert(0, STORYWORLDS_DIR)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    clean: bool = False
    portable: bool = False
    xray_safe: bool = True
    # physical and emotional state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "dentist_f", "hygienist_f"}
        male = {"boy", "father", "man", "dentist_m", "hygienist_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "mother":
            return "mom"
        if self.type == "father":
            return "dad"
        if self.type.startswith("dentist"):
            return "dentist"
        return self.type


@dataclass
class Idol:
    id: str
    label: str
    phrase: str
    material: str
    tiny: bool = True
    xray_safe: bool = True
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Exam:
    id: str
    label: str
    chair_need: str
    opening_line: str
    requires_hands_free: bool
    metal_problem: bool
    touch_level: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Perch:
    id: str
    label: str
    phrase: str
    clean: bool
    near_child: bool
    safe_for_idol: bool
    sense: int
    watch_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PromiseRitual:
    id: str
    words: tuple[str, str, str]
    effect: int
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
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_cling_to_delay(world: World) -> list[str]:
    child = world.get("child")
    idol = world.get("idol")
    if child.memes["refusal"] >= THRESHOLD and idol.meters["in_hand"] >= THRESHOLD:
        sig = ("delay",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("room").meters["delay"] += 1
            return ["__delay__"]
    return []


def _r_exam_can_begin(world: World) -> list[str]:
    child = world.get("child")
    idol = world.get("idol")
    if child.memes["trust"] >= THRESHOLD and idol.meters["on_perch"] >= THRESHOLD:
        sig = ("begin",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("exam").meters["ready"] += 1
            return ["__ready__"]
    return []


def _r_calm_after_ready(world: World) -> list[str]:
    exam = world.get("exam")
    child = world.get("child")
    if exam.meters["ready"] >= THRESHOLD:
        sig = ("calm",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] = 0.0
            child.memes["calm"] += 1
            return []
    return []


CAUSAL_RULES = [
    Rule("cling_delay", "social", _r_cling_to_delay),
    Rule("exam_begin", "social", _r_exam_can_begin),
    Rule("calm_after_ready", "emotional", _r_calm_after_ready),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def exam_needs_setting_aside(exam: Exam, idol: Idol) -> bool:
    return exam.requires_hands_free or (exam.metal_problem and not idol.xray_safe)


def safe_perch(exam: Exam, perch: Perch, idol: Idol) -> bool:
    if perch.sense < SENSE_MIN:
        return False
    if not perch.clean or not perch.safe_for_idol or not perch.near_child:
        return False
    if exam.metal_problem and not idol.xray_safe and perch.id == "pocket":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for iid, idol in IDOLS.items():
        for eid, exam in EXAMS.items():
            if not exam_needs_setting_aside(exam, idol):
                continue
            for pid, perch in PERCHES.items():
                if safe_perch(exam, perch, idol):
                    out.append((iid, eid, pid))
    return out


def predict_ready(world: World, perch_id: str) -> bool:
    sim = world.copy()
    sim.get("idol").meters["in_hand"] = 0.0
    sim.get("idol").meters["on_perch"] += 1
    sim.get("child").memes["trust"] += 1
    sim.facts["perch"] = PERCHES[perch_id]
    propagate(sim, narrate=False)
    return sim.get("exam").meters["ready"] >= THRESHOLD


def introduce(world: World, child: Entity, parent: Entity, dentist: Entity, idol: Idol) -> None:
    world.say(
        f"In the bright dentist office there came {child.id}, walking close beside "
        f"{child.pronoun('possessive')} {parent.label_word} and holding {idol.phrase}."
    )
    world.say(
        f"{idol.phrase.capitalize()} was {child.id}'s idol for brave days, a tiny "
        f"{idol.material} friend that had listened to many worried breaths."
    )
    world.say(
        f"And in that place waited Dr. {dentist.id}, a gentle dentist with a lamp like a small white moon."
    )


def call_to_chair(world: World, child: Entity, exam: Exam) -> None:
    child.memes["fear"] += 1
    world.say(
        f'Dr. {world.get("dentist").id} smiled and said, "{exam.opening_line}"'
    )
    world.say(
        f"But when {child.id} saw the great chair and the silver tools, "
        f"{child.pronoun('possessive')} fingers closed tighter."
    )


def first_refusal(world: World, child: Entity, exam: Exam, idol: Idol) -> None:
    child.memes["refusal"] += 1
    idol.meters["in_hand"] += 1
    world.say(
        f'"You may sit in the chair," said the dentist, "but {idol.label} must rest while we {exam.label}."'
    )
    world.say(
        f'"No," said {child.id}. "My idol stays with me."'
    )
    propagate(world, narrate=False)


def second_refusal(world: World, child: Entity, parent: Entity, idol: Idol) -> None:
    child.memes["refusal"] += 1
    child.memes["fear"] += 1
    world.say(
        f'Then {child.pronoun("possessive")} {parent.label_word} spoke softly: '
        f'"Set {idol.pronoun("object")} down for one little while."'
    )
    world.say(
        f'Again {child.id} answered, "No. My idol stays with me."'
    )
    propagate(world, narrate=False)


def third_refusal(world: World, child: Entity, dentist: Entity, idol: Idol) -> None:
    child.memes["refusal"] += 1
    world.say(
        f'And for the third time Dr. {dentist.id} asked, "Shall your idol watch from nearby?"'
    )
    world.say(
        f'And for the third time {child.id} said, "No. My idol stays with me."'
    )
    propagate(world, narrate=False)


def explain_need(world: World, child: Entity, exam: Exam, idol: Idol) -> None:
    if exam.metal_problem and not idol.xray_safe:
        why = (
            f"{idol.label.capitalize()} had metal on it, and the dentist could not make a clear picture "
            f"while it was being held close."
        )
    else:
        why = (
            f"To {exam.label}, the dentist needed {child.id}'s hands still and free, "
            f"so the little idol could not be squeezed in the middle of the work."
        )
    world.say(why)
    world.facts["reason_line"] = why


def offer_perch(world: World, child: Entity, dentist: Entity, idol: Idol, perch: Perch, ritual: PromiseRitual) -> None:
    pred_ready = predict_ready(world, perch.id)
    world.facts["pred_ready"] = pred_ready
    world.say(
        f"Then Dr. {dentist.id} had a wiser thought. {dentist.pronoun('subject').capitalize()} set out {perch.phrase} "
        f"and said, \"Let your idol wait here. {perch.watch_line}\""
    )
    a, b, c = ritual.words
    world.say(
        f'To make the promise strong, the dentist said it three times: "{a}." "{b}." "{c}."'
    )


def accept_offer(world: World, child: Entity, idol: Entity, perch: Perch, ritual: PromiseRitual) -> None:
    idol.meters["in_hand"] = 0.0
    idol.meters["on_perch"] += 1
    child.memes["trust"] += ritual.effect
    child.memes["hope"] += 1
    child.memes["refusal"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"At last {child.id} opened {child.pronoun('possessive')} hand. "
        f"{idol.label.capitalize()} was placed on {perch.label}, where it seemed to keep watch without wiggling at all."
    )


def begin_exam(world: World, child: Entity, dentist: Entity, exam: Exam) -> None:
    world.say(
        f"Then {child.id} climbed into the chair, and Dr. {dentist.id} began to {exam.label}."
    )
    if exam.id == "xray":
        world.say(
            f"The machine hummed like a far bee, and the picture was taken quickly."
        )
    elif exam.id == "count":
        world.say(
            f"One tooth, two teeth, three teeth, the count went on like a small chant."
        )
    else:
        world.say(
            f"The shiny brush turned softly, and the visit grew easier with every breath."
        )


def return_idol(world: World, child: Entity, dentist: Entity, idol: Entity) -> None:
    idol.meters["returned"] += 1
    child.memes["joy"] += 1
    child.memes["bravery"] += 1
    world.say(
        f"When the work was done, Dr. {dentist.id} placed {idol.label} back into {child.id}'s hands."
    )
    world.say(
        f"And {child.id} laughed, for the idol had not been lost at all. It had watched, and {child.id} had been brave."
    )


def ending(world: World, child: Entity, parent: Entity, exam: Exam, idol: Idol, perch: Perch) -> None:
    world.say(
        f"From that day on, when {child.id} came to the dentist office, "
        f"{child.pronoun('subject')} remembered {perch.label} and the three calm words."
    )
    world.say(
        f"So the old quarrel grew small, and the child who once cried, "
        f'"My idol stays with me," could now say, "My idol can watch, and I can be brave."'
    )


IDOLS = {
    "sun_lion": Idol(
        "sun_lion", "the sun-lion idol", "a small sun-lion idol",
        "painted wood", True, True, {"idol", "comfort", "wood"}
    ),
    "lucky_elephant": Idol(
        "lucky_elephant", "the lucky elephant idol", "a lucky elephant idol",
        "smooth clay", True, True, {"idol", "comfort", "clay"}
    ),
    "gold_cat": Idol(
        "gold_cat", "the gold cat idol", "a gold cat idol",
        "gleaming metal", True, False, {"idol", "comfort", "metal"}
    ),
}

EXAMS = {
    "count": Exam(
        "count", "count the teeth", "sit still in the chair",
        "Come, little one. It is time to count your teeth.",
        True, False, 1, {"teeth", "count"}
    ),
    "cleaning": Exam(
        "cleaning", "clean the teeth", "open wide under the bright lamp",
        "Come, little one. We will clean your teeth till they shine.",
        True, False, 2, {"teeth", "clean"}
    ),
    "xray": Exam(
        "xray", "take a tooth picture", "bite gently on the picture tab",
        "Come, little one. We must make a picture of your tooth.",
        True, True, 2, {"xray", "picture"}
    ),
}

PERCHES = {
    "tray": Perch(
        "tray", "the clean tray", "a clean tray beside the chair",
        True, True, True, 3,
        "It will see you the whole time, and you will see it too.",
        {"tray", "clean"}
    ),
    "blue_napkin": Perch(
        "blue_napkin", "the folded blue napkin", "a folded blue napkin on the counter",
        True, True, True, 3,
        "It will rest like a little king and watch from there.",
        {"napkin", "clean"}
    ),
    "window_sill": Perch(
        "window_sill", "the sunny window sill", "the sunny window sill above the sink",
        True, False, True, 1,
        "It will have a fine view.",
        {"window"}
    ),
    "pocket": Perch(
        "pocket", "the dentist's pocket", "the dentist's pocket",
        False, True, False, 1,
        "It will stay with me.",
        {"pocket"}
    ),
}

RITUALS = {
    "watch_words": PromiseRitual(
        "watch_words",
        ("It can watch", "It can wait", "It can come back"),
        1,
        {"ritual", "repetition"}
    ),
    "brave_words": PromiseRitual(
        "brave_words",
        ("You are safe", "You are seen", "You are brave"),
        1,
        {"ritual", "repetition"}
    ),
}

CHILD_NAMES = ["Lina", "Mira", "Nora", "Tomas", "Eli", "Rosa", "Ada", "Ben"]
PARENT_TYPES = ["mother", "father"]
DENTISTS = [("Mora", "dentist_f"), ("Hale", "dentist_m")]
TRAITS = ["timid", "careful", "small", "watchful", "earnest"]


@dataclass
class StoryParams:
    idol: str
    exam: str
    perch: str
    ritual: str
    child_name: str
    child_gender: str
    parent: str
    dentist_name: str
    dentist_gender: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "idol": [(
        "What is an idol in this story?",
        "In this story, the idol is a tiny figure the child loves and trusts for comfort. It is not magic by itself; it helps because it makes the child feel less alone."
    )],
    "dentist": [(
        "What does a dentist do?",
        "A dentist looks at teeth, cleans them, and helps keep mouths healthy. Dentists also try to help children feel safe during a visit."
    )],
    "xray": [(
        "What is a tooth picture or x-ray?",
        "A tooth picture, or x-ray, is a special image that lets the dentist see parts of a tooth that eyes cannot see easily. The child has to stay still so the picture comes out clearly."
    )],
    "tray": [(
        "Why would a dentist use a clean tray?",
        "A clean tray gives small tools a safe, tidy place to rest. In this story it also gives the idol a nearby place to wait."
    )],
    "repetition": [(
        "Why do people repeat calm words?",
        "Repeating calm words can make a promise feel steady and easy to remember. Hearing the same kind words again and again can help fear shrink."
    )],
    "comfort": [(
        "Why do children bring comfort objects to appointments?",
        "A comfort object can help a child feel brave in an unfamiliar place. It gives the child something familiar when the room, sounds, or tools feel strange."
    )],
}
KNOWLEDGE_ORDER = ["idol", "comfort", "dentist", "xray", "tray", "repetition"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    idol = f["idol_cfg"]
    exam = f["exam_cfg"]
    return [
        f'Write a folk-tale style story for a 3-to-5-year-old set in a dentist office and include the word "idol".',
        f"Tell a repetitive conflict story where {child.id} refuses three times to set down {idol.label} before a gentle dentist finds a wiser plan during {exam.label}.",
        f"Write a simple folk tale about fear in a dentist office, an idol used for comfort, and a calm ending that turns a quarrel into courage.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    dentist = f["dentist"]
    idol = f["idol_cfg"]
    exam = f["exam_cfg"]
    perch = f["perch"]
    ritual = f["ritual"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who brought {idol.label} to the dentist office, along with {child.pronoun('possessive')} {parent.label_word} and Dr. {dentist.id}. The story follows how fear turned into bravery during the visit."
        ),
        (
            f"Why did {child.id} keep saying no?",
            f"{child.id} was afraid of the dentist chair and wanted to keep holding the idol for courage. The repeated 'no' came from worry, because the idol felt safe and familiar in a place full of bright tools."
        ),
        (
            "What was the conflict in the story?",
            f"The conflict was that the dentist needed the child's hands free for {exam.label}, but {child.id} did not want to let go of the idol. The trouble lasted until the adults found a safe nearby place where the idol could still 'watch.'"
        ),
        (
            "What happened three times?",
            f"The child refused three times to set the idol aside, and the dentist used repeated calm words to make a promise feel trustworthy. That repetition gives the tale its folk-tale rhythm and helps show how the fear slowly softens."
        ),
        (
            f"Why did the idol need to rest on {perch.label}?",
            f"{f['reason_line']} Putting the idol on {perch.label} solved the practical problem while still letting it stay near {child.id}."
        ),
        (
            f"How was the problem solved?",
            f"Dr. {dentist.id} offered {perch.phrase} as a special watching place and spoke the ritual words three times. After that, {child.id} trusted the plan, let go of the idol, and the exam could begin."
        ),
        (
            f"How did the story end?",
            f"The dentist returned the idol, and {child.id} felt brave instead of frightened. The ending image shows a change: the idol was still loved, but now {child.id} knew courage could stay even when the idol waited nearby."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"idol", "dentist", "comfort", "repetition"}
    if f["exam_cfg"].id == "xray":
        tags.add("xray")
    if f["perch"].id == "tray":
        tags.add("tray")
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


def tell(
    idol_cfg: Idol,
    exam_cfg: Exam,
    perch_cfg: Perch,
    ritual_cfg: PromiseRitual,
    child_name: str = "Lina",
    child_gender: str = "girl",
    parent_type: str = "mother",
    dentist_name: str = "Mora",
    dentist_gender: str = "dentist_f",
    trait: str = "timid",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name, kind="character", type=child_gender, role="child",
        traits=[trait], label=child_name
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, role="parent",
        label="the parent"
    ))
    dentist = world.add(Entity(
        id=dentist_name, kind="character", type=dentist_gender, role="dentist",
        label="the dentist"
    ))
    room = world.add(Entity(
        id="room", kind="thing", type="room", label="dentist office"
    ))
    idol = world.add(Entity(
        id="idol", kind="thing", type="idol", label=idol_cfg.label,
        portable=True, clean=True, xray_safe=idol_cfg.xray_safe
    ))
    exam = world.add(Entity(
        id="exam", kind="thing", type="exam", label=exam_cfg.label
    ))

    introduce(world, child, parent, dentist, idol_cfg)
    world.para()
    call_to_chair(world, child, exam_cfg)
    first_refusal(world, child, exam_cfg, idol_cfg)
    second_refusal(world, child, parent, idol_cfg)
    third_refusal(world, child, dentist, idol_cfg)
    explain_need(world, child, exam_cfg, idol_cfg)
    world.para()
    offer_perch(world, child, dentist, idol_cfg, perch_cfg, ritual_cfg)
    accept_offer(world, child, idol, perch_cfg, ritual_cfg)
    world.para()
    begin_exam(world, child, dentist, exam_cfg)
    return_idol(world, child, dentist, idol)
    ending(world, child, parent, exam_cfg, idol_cfg, perch_cfg)

    world.facts.update(
        child=child,
        parent=parent,
        dentist=dentist,
        idol_cfg=idol_cfg,
        exam_cfg=exam_cfg,
        perch=perch_cfg,
        ritual=ritual_cfg,
        delay=room.meters["delay"],
        ready=exam.meters["ready"] >= THRESHOLD,
        returned=idol.meters["returned"] >= THRESHOLD,
        outcome="resolved" if exam.meters["ready"] >= THRESHOLD else "stalled",
    )
    return world


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (
            ("clean", e.clean), ("portable", e.portable), ("xray_safe", e.xray_safe)
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("sun_lion", "count", "tray", "watch_words", "Lina", "girl", "mother", "Mora", "dentist_f", "timid"),
    StoryParams("lucky_elephant", "cleaning", "blue_napkin", "brave_words", "Ben", "boy", "father", "Hale", "dentist_m", "watchful"),
    StoryParams("gold_cat", "xray", "tray", "watch_words", "Mira", "girl", "mother", "Mora", "dentist_f", "careful"),
]


def explain_rejection(idol: Idol, exam: Exam, perch: Optional[Perch] = None) -> str:
    if not exam_needs_setting_aside(exam, idol):
        return (
            f"(No story: for {exam.label}, the child could reasonably keep holding {idol.label}, "
            f"so there is no honest conflict about setting it aside.)"
        )
    if perch is not None and not safe_perch(exam, perch, idol):
        return (
            f"(No story: {perch.label} is not a sensible nearby clean resting place for {idol.label} "
            f"during {exam.label}. Pick a clean perch like tray or blue_napkin.)"
        )
    return "(No story: that combination does not make a sensible conflict and fix.)"


ASP_RULES = r"""
needs_aside(I, E) :- idol(I), exam(E), requires_hands_free(E).
needs_aside(I, E) :- idol(I), exam(E), metal_problem(E), not xray_safe(I).

safe_perch_for(E, P, I) :- perch(P), clean(P), near_child(P), safe_for_idol(P),
                           sense(P, S), sense_min(M), S >= M,
                           not bad_pocket_xray(E, P, I).
bad_pocket_xray(E, pocket, I) :- metal_problem(E), not xray_safe(I).

valid(I, E, P) :- needs_aside(I, E), safe_perch_for(E, P, I).

outcome(resolved) :- chosen(I, E, P), valid(I, E, P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for iid, idol in IDOLS.items():
        lines.append(asp.fact("idol", iid))
        if idol.xray_safe:
            lines.append(asp.fact("xray_safe", iid))
    for eid, exam in EXAMS.items():
        lines.append(asp.fact("exam", eid))
        if exam.requires_hands_free:
            lines.append(asp.fact("requires_hands_free", eid))
        if exam.metal_problem:
            lines.append(asp.fact("metal_problem", eid))
    for pid, perch in PERCHES.items():
        lines.append(asp.fact("perch", pid))
        if perch.clean:
            lines.append(asp.fact("clean", pid))
        if perch.near_child:
            lines.append(asp.fact("near_child", pid))
        if perch.safe_for_idol:
            lines.append(asp.fact("safe_for_idol", pid))
        lines.append(asp.fact("sense", pid, perch.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
        asp.fact("chosen", params.idol, params.exam, params.perch),
    ])
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
    for seed in range(30):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"resolve_params failed during verify seed={seed}")
            break

    mismatches = []
    for p in cases:
        py = "resolved"
        cl = asp_outcome(p)
        if py != cl:
            mismatches.append((p, py, cl))
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child, an idol, and a repeated folk-tale conflict in a dentist office."
    )
    ap.add_argument("--idol", choices=IDOLS)
    ap.add_argument("--exam", choices=EXAMS)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--ritual", choices=RITUALS)
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
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
    if args.idol and args.exam and not exam_needs_setting_aside(EXAMS[args.exam], IDOLS[args.idol]):
        raise StoryError(explain_rejection(IDOLS[args.idol], EXAMS[args.exam]))
    if args.idol and args.exam and args.perch:
        if not safe_perch(EXAMS[args.exam], PERCHES[args.perch], IDOLS[args.idol]):
            raise StoryError(explain_rejection(IDOLS[args.idol], EXAMS[args.exam], PERCHES[args.perch]))

    combos = [
        c for c in valid_combos()
        if (args.idol is None or c[0] == args.idol)
        and (args.exam is None or c[1] == args.exam)
        and (args.perch is None or c[2] == args.perch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    idol, exam, perch = rng.choice(sorted(combos))
    ritual = args.ritual or rng.choice(sorted(RITUALS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    dentist_name, dentist_gender = rng.choice(DENTISTS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        idol=idol,
        exam=exam,
        perch=perch,
        ritual=ritual,
        child_name=child_name,
        child_gender=child_gender,
        parent=parent,
        dentist_name=dentist_name,
        dentist_gender=dentist_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        IDOLS[params.idol],
        EXAMS[params.exam],
        PERCHES[params.perch],
        RITUALS[params.ritual],
        params.child_name,
        params.child_gender,
        params.parent,
        params.dentist_name,
        params.dentist_gender,
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
        print(f"{len(combos)} compatible (idol, exam, perch) combos:\n")
        for idol, exam, perch in combos:
            print(f"  {idol:15} {exam:10} {perch}")
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
            header = f"### {p.child_name}: {p.idol} during {p.exam} ({p.perch})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
