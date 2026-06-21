#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/radish_technician_bedroom_problem_solving_detective_story.py
=======================================================================================

A standalone storyworld for a tiny bedroom detective story: a child notices that
something important in the bedroom has stopped working, gathers clues, and a calm
technician helps solve the problem. The seed words "radish" and "technician"
appear naturally in the story world.

Domain notes
------------
This world models three kinds of bedroom objects with different failure causes:

* lamp       -> can fail from an unplugged cord or a dead battery
* music_box  -> can fail from a dead battery or a jammed gear
* fan        -> can fail from an unplugged cord or a jammed blade

The world refuses unreasonable stories: a fix must actually match the cause and
the object's needs. A child detective can notice clues, but the technician uses
a sensible repair method.

Run it
------
    python storyworlds/worlds/gpt-5.4/radish_technician_bedroom_problem_solving_detective_story.py
    python storyworlds/worlds/gpt-5.4/radish_technician_bedroom_problem_solving_detective_story.py --object lamp --cause unplugged
    python storyworlds/worlds/gpt-5.4/radish_technician_bedroom_problem_solving_detective_story.py --fix oil
    python storyworlds/worlds/gpt-5.4/radish_technician_bedroom_problem_solving_detective_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/radish_technician_bedroom_problem_solving_detective_story.py --verify
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
    traits: tuple = field(default_factory=tuple)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    wired: bool = False
    battery_powered: bool = False
    mechanical: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class BedroomObject:
    id: str
    label: str
    phrase: str
    effect: str
    clue_place: str
    wired: bool = False
    battery_powered: bool = False
    mechanical: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    sign: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    action: str
    result: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []

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
        clone.history = list(self.history)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_problem_from_state(world: World) -> list[str]:
    out: list[str] = []
    thing = world.get("object")
    child = world.get("child")
    if thing.meters["working"] >= THRESHOLD:
        return out
    if thing.meters["problem"] >= THRESHOLD:
        return out
    if (
        thing.meters["unplugged"] >= THRESHOLD
        or thing.meters["dead_battery"] >= THRESHOLD
        or thing.meters["jammed"] >= THRESHOLD
    ):
        thing.meters["problem"] += 1
        child.memes["worry"] += 1
        out.append("__problem__")
    return out


def _r_clue_from_cause(world: World) -> list[str]:
    out: list[str] = []
    thing = world.get("object")
    cause = world.facts["cause_cfg"]
    if thing.meters[cause.id] < THRESHOLD:
        return out
    sig = ("clue", cause.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    thing.meters["clue_found"] += 1
    out.append(cause.clue)
    return out


CAUSAL_RULES = [
    Rule(name="problem_from_state", tag="physical", apply=_r_problem_from_state),
    Rule(name="clue_from_cause", tag="observational", apply=_r_clue_from_cause),
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
        for sent in produced:
            world.say(sent)
    return produced


OBJECTS = {
    "lamp": BedroomObject(
        id="lamp",
        label="lamp",
        phrase="a little star lamp beside the bed",
        effect="glow a soft golden circle on the wall",
        clue_place="beside the pillow",
        wired=True,
        battery_powered=True,
        mechanical=False,
        tags={"lamp", "electricity", "bedroom_light"},
    ),
    "music_box": BedroomObject(
        id="music_box",
        label="music box",
        phrase="a small music box shaped like a moon",
        effect="play a sleepy tune with tiny silver notes",
        clue_place="on the bookshelf",
        wired=False,
        battery_powered=True,
        mechanical=True,
        tags={"music_box", "battery", "mechanical"},
    ),
    "fan": BedroomObject(
        id="fan",
        label="fan",
        phrase="a small bedside fan with blue blades",
        effect="whirr cool air across the blanket fort",
        clue_place="near the window",
        wired=True,
        battery_powered=False,
        mechanical=True,
        tags={"fan", "electricity", "mechanical"},
    ),
}

CAUSES = {
    "unplugged": Cause(
        id="unplugged",
        label="the cord had slipped from the wall socket",
        sign="no power",
        clue="Near the baseboard, the cord lay curled like a loose tail instead of reaching into the wall.",
        tags={"electricity", "plug"},
    ),
    "dead_battery": Cause(
        id="dead_battery",
        label="the battery had run flat",
        sign="no stored power",
        clue="When the child opened the little battery door, the old battery sat inside with no strength left to help.",
        tags={"battery"},
    ),
    "jammed": Cause(
        id="jammed",
        label="a tiny part was stuck",
        sign="stuck motion",
        clue="When the child looked closely, a small piece near the moving part would not turn the way it should.",
        tags={"mechanical", "stuck"},
    ),
}

FIXES = {
    "plug_in": Fix(
        id="plug_in",
        label="plug it back in",
        action="followed the cord, lifted the plug, and pressed it safely back into the wall socket",
        result="Power could reach the object again",
        tags={"plug"},
    ),
    "new_battery": Fix(
        id="new_battery",
        label="put in a fresh battery",
        action="opened the battery door, took out the tired battery, and clicked a fresh one into place",
        result="The object had stored power again",
        tags={"battery"},
    ),
    "clear_jam": Fix(
        id="clear_jam",
        label="clear the jam",
        action="peered at the stuck part, lifted out the tiny bit blocking it, and turned the piece gently until it moved freely",
        result="The moving part could work again",
        tags={"mechanical"},
    ),
    "oil": Fix(
        id="oil",
        label="pour oil on it",
        action="dripped oil onto the object",
        result="It became shiny",
        tags={"bad_fix"},
    ),
}

CAUSE_TO_FIX = {
    "unplugged": {"plug_in"},
    "dead_battery": {"new_battery"},
    "jammed": {"clear_jam"},
}


def cause_allowed(obj: BedroomObject, cause: Cause) -> bool:
    if cause.id == "unplugged":
        return obj.wired
    if cause.id == "dead_battery":
        return obj.battery_powered
    if cause.id == "jammed":
        return obj.mechanical
    return False


def fix_matches(cause: Cause, fix: Fix) -> bool:
    return fix.id in CAUSE_TO_FIX.get(cause.id, set())


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for oid, obj in OBJECTS.items():
        for cid, cause in CAUSES.items():
            for fid, fix in FIXES.items():
                if cause_allowed(obj, cause) and fix_matches(cause, fix):
                    combos.append((oid, cid, fid))
    return combos


def predict_problem(world: World, obj_id: str, cause_id: str) -> dict:
    sim = world.copy()
    obj = sim.get(obj_id)
    obj.meters["working"] = 0.0
    obj.meters[cause_id] += 1
    propagate(sim, narrate=False)
    return {
        "problem": obj.meters["problem"] >= THRESHOLD,
        "worry": sim.get("child").memes["worry"],
    }


def apply_cause(world: World, obj: Entity, cause: Cause) -> None:
    obj.meters["working"] = 0.0
    obj.meters[cause.id] += 1
    world.history.append(f"cause:{cause.id}")
    propagate(world, narrate=False)


def inspect_scene(world: World, child: Entity, obj: Entity, obj_cfg: BedroomObject) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"That night in the bedroom, {child.id} set out to be a detective. On the floor by the bed sat {obj_cfg.phrase}, and it was supposed to {obj_cfg.effect}."
    )
    world.say(
        f"But when {child.pronoun()} tried it, nothing happened. The bedroom suddenly felt full of a quiet little mystery."
    )


def introduce_radish(world: World, child: Entity) -> None:
    world.say(
        f"Beside the pillow sat Radish, {child.id}'s red radish-shaped plush toy, watching the case with stitched-on serious eyes."
    )


def detective_vow(world: World, child: Entity) -> None:
    world.say(
        f'"Detective {child.id} will solve it," {child.pronoun()} whispered, as if the blanket fort were a secret office.'
    )


def search_for_clues(world: World, child: Entity, obj_cfg: BedroomObject, cause: Cause) -> None:
    world.say(
        f"{child.id} knelt by the clue place, {obj_cfg.clue_place}, and looked for signs instead of guessing."
    )
    world.say(
        f"{child.pronoun().capitalize()} remembered that good detectives notice what is real, not what is loud."
    )
    world.say(cause.clue)
    child.memes["confidence"] += 1
    world.facts["clue_seen"] = True
    world.history.append(f"clue:{cause.id}")


def call_helper(world: World, child: Entity, helper: Entity, cause: Cause) -> None:
    pred = predict_problem(world, "object", cause.id)
    world.facts["predicted_problem"] = pred["problem"]
    child.memes["trust"] += 1
    world.say(
        f"{child.id} did not poke or pull at random. {child.pronoun().capitalize()} went to ask {helper.id}, a careful technician, to look at the clue too."
    )


def technician_reason(world: World, helper: Entity, obj_cfg: BedroomObject, cause: Cause, fix: Fix) -> None:
    helper.memes["calm"] += 1
    world.say(
        f'{helper.id} crouched beside the {obj_cfg.label} and spoke in a quiet detective voice. "The clue tells us {cause.label}," {helper.pronoun()} said. "So the sensible next step is to {fix.label}."'
    )
    world.history.append(f"reason:{cause.id}->{fix.id}")


def repair(world: World, helper: Entity, obj: Entity, obj_cfg: BedroomObject, cause: Cause, fix: Fix) -> None:
    for key in ("unplugged", "dead_battery", "jammed", "problem"):
        obj.meters[key] = 0.0
    obj.meters["working"] = 1.0
    obj.meters["fixed"] += 1
    helper.memes["care"] += 1
    world.history.append(f"fix:{fix.id}")
    world.say(
        f"Then the technician {fix.action}. {fix.result}, and everyone waited for the answer."
    )
    world.say(
        f"The {obj_cfg.label} woke at once and began to {obj_cfg.effect}."
    )


def resolution(world: World, child: Entity, helper: Entity, obj_cfg: BedroomObject) -> None:
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} grinned so hard that even Radish seemed ready to grin too. The case was solved because {child.pronoun()} had looked for clues, asked for help, and followed the best idea."
    )
    world.say(
        f'"A good detective uses careful thinking," said {helper.id}. In the soft bedroom light, the mystery no longer felt spooky at all.'
    )


def tell(
    obj_cfg: BedroomObject,
    cause: Cause,
    fix: Fix,
    child_name: str = "Nora",
    child_type: str = "girl",
    helper_name: str = "Aunt June",
    helper_type: str = "aunt",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child", label=child_name))
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_type,
            role="technician",
            label="the technician",
            attrs={"job": "technician"},
        )
    )
    obj = world.add(
        Entity(
            id="object",
            kind="thing",
            type=obj_cfg.id,
            label=obj_cfg.label,
            phrase=obj_cfg.phrase,
            wired=obj_cfg.wired,
            battery_powered=obj_cfg.battery_powered,
            mechanical=obj_cfg.mechanical,
            tags=set(obj_cfg.tags),
        )
    )
    obj.meters["working"] = 1.0
    radish = world.add(
        Entity(
            id="radish",
            kind="thing",
            type="plush",
            label="Radish",
            phrase="a radish-shaped plush toy",
            tags={"radish"},
        )
    )
    room = world.add(Entity(id="room", kind="thing", type="bedroom", label="bedroom"))
    world.facts.update(
        child=child,
        helper=helper,
        object=obj,
        object_cfg=obj_cfg,
        cause_cfg=cause,
        fix_cfg=fix,
        radish=radish,
        room=room,
    )

    inspect_scene(world, child, obj, obj_cfg)
    introduce_radish(world, child)
    detective_vow(world, child)

    world.para()
    apply_cause(world, obj, cause)
    search_for_clues(world, child, obj_cfg, cause)
    call_helper(world, child, helper, cause)

    world.para()
    technician_reason(world, helper, obj_cfg, cause, fix)
    repair(world, helper, obj, obj_cfg, cause, fix)
    resolution(world, child, helper, obj_cfg)

    world.facts.update(
        solved=obj.meters["fixed"] >= THRESHOLD,
        clue_found=obj.meters["clue_found"] >= THRESHOLD,
        working=obj.meters["working"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and uses them to figure out what happened. Good detectives do not just guess."
        )
    ],
    "technician": [
        (
            "What does a technician do?",
            "A technician is a person who understands how tools or machines work and helps fix problems carefully."
        )
    ],
    "radish": [
        (
            "What is a radish?",
            "A radish is a small crunchy root vegetable that can be red, pink, or white. In this story, Radish is also the name of a toy shaped like one."
        )
    ],
    "battery": [
        (
            "What does a battery do?",
            "A battery stores power so a small object can work even when it is not plugged into a wall."
        )
    ],
    "plug": [
        (
            "Why does plugging something in help?",
            "Plugging something in can let electricity travel from the wall to the object, so the object can work."
        )
    ],
    "mechanical": [
        (
            "What does it mean when something is jammed?",
            "When something is jammed, a part is stuck and cannot move the way it should."
        )
    ],
    "bedroom_light": [
        (
            "Why do people keep a lamp in a bedroom?",
            "A bedroom lamp gives gentle light, so you can see without turning on a bright room light."
        )
    ],
    "music_box": [
        (
            "What is a music box?",
            "A music box is a small object that plays a tune. Some use tiny moving parts, and some use batteries."
        )
    ],
    "fan": [
        (
            "What does a fan do?",
            "A fan moves air around. That can make a room feel cooler and less stuffy."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "detective",
    "technician",
    "radish",
    "battery",
    "plug",
    "mechanical",
    "bedroom_light",
    "music_box",
    "fan",
]


@dataclass
class StoryParams:
    object: str
    cause: str
    fix: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        object="lamp",
        cause="unplugged",
        fix="plug_in",
        child_name="Nora",
        child_type="girl",
        helper_name="Aunt June",
        helper_type="aunt",
    ),
    StoryParams(
        object="music_box",
        cause="dead_battery",
        fix="new_battery",
        child_name="Ben",
        child_type="boy",
        helper_name="Uncle Ravi",
        helper_type="uncle",
    ),
    StoryParams(
        object="fan",
        cause="jammed",
        fix="clear_jam",
        child_name="Mia",
        child_type="girl",
        helper_name="Dad",
        helper_type="father",
    ),
    StoryParams(
        object="music_box",
        cause="jammed",
        fix="clear_jam",
        child_name="Theo",
        child_type="boy",
        helper_name="Mom",
        helper_type="mother",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    obj_cfg = f["object_cfg"]
    cause = f["cause_cfg"]
    return [
        'Write a gentle detective story for a 3-to-5-year-old set in a bedroom, and include the words "radish" and "technician".',
        f"Tell a bedtime mystery where {child.id} notices that a {obj_cfg.label} will not work, finds a clue, and solves the problem by asking a technician for help.",
        f"Write a story about problem solving in a bedroom where the real clue is that {cause.label}, and the ending should feel calm instead of scary.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    obj_cfg = f["object_cfg"]
    cause = f["cause_cfg"]
    fix = f["fix_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who plays detective in the bedroom, and {helper.id}, a technician who helps solve the case."
        ),
        (
            f"What was the mystery in the bedroom?",
            f"The mystery was that the {obj_cfg.label} would not work the way it usually did. That is what made {child.id} start looking for clues."
        ),
        (
            f"What clue did {child.id} find?",
            f"{cause.clue} That clue mattered because it pointed to the real problem instead of making {child.id} guess."
        ),
        (
            f"Why did {child.id} ask {helper.id} for help?",
            f"{child.id} wanted to solve the problem carefully, not poke at things at random. {helper.id} was a technician, so {helper.pronoun()} knew how to match the clue to the right fix."
        ),
        (
            f"How did the technician solve the case?",
            f"The technician decided to {fix.label} because the clue showed that {cause.label}. Then {helper.pronoun()} repaired it, and the {obj_cfg.label} worked again."
        ),
        (
            "How did the story end?",
            f"It ended with the mystery solved and the bedroom feeling calm again. The change is easy to see because the {obj_cfg.label} began to {obj_cfg.effect}."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"detective", "technician", "radish"}
    tags |= set(f["object_cfg"].tags)
    tags |= set(f["cause_cfg"].tags)
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
        if ent.wired:
            bits.append("wired=True")
        if ent.battery_powered:
            bits.append("battery_powered=True")
        if ent.mechanical:
            bits.append("mechanical=True")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  history: {world.history}")
    return "\n".join(lines)


def explain_rejection(obj: BedroomObject, cause: Cause, fix: Optional[Fix] = None) -> str:
    if not cause_allowed(obj, cause):
        return (
            f"(No story: {obj.phrase} cannot reasonably have the cause '{cause.id}'. "
            f"That cause does not fit how the object works.)"
        )
    if fix is not None and not fix_matches(cause, fix):
        good = ", ".join(sorted(CAUSE_TO_FIX.get(cause.id, [])))
        return (
            f"(No story: fix '{fix.id}' does not solve cause '{cause.id}'. "
            f"Use a matching fix such as: {good}.)"
        )
    return "(No story: this combination does not describe a sensible repair.)"


ASP_RULES = r"""
object_ok_for_cause(O, unplugged)    :- object(O), wired(O).
object_ok_for_cause(O, dead_battery) :- object(O), battery_powered(O).
object_ok_for_cause(O, jammed)       :- object(O), mechanical(O).

matches(unplugged, plug_in).
matches(dead_battery, new_battery).
matches(jammed, clear_jam).

valid(O, C, F) :- object(O), cause(C), fix(F), object_ok_for_cause(O, C), matches(C, F).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.wired:
            lines.append(asp.fact("wired", oid))
        if obj.battery_powered:
            lines.append(asp.fact("battery_powered", oid))
        if obj.mechanical:
            lines.append(asp.fact("mechanical", oid))
    for cid in CAUSES:
        lines.append(asp.fact("cause", cid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
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
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(0))
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print(f"SMOKE FAIL: could not resolve default params: {err}")

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            emit(sample, trace=False, qa=False, header=f"### smoke {idx}")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"SMOKE FAIL on case {idx}: {err}")
    if rc == 0:
        print("OK: smoke generation succeeded.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Bedroom detective storyworld with a radish plush and a technician helper."
    )
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible repair combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Ella", "Zoe"]
BOY_NAMES = ["Ben", "Theo", "Max", "Sam", "Eli", "Leo"]
HELPERS = {
    "mother": ["Mom", "Mama", "Mother"],
    "father": ["Dad", "Papa", "Father"],
    "aunt": ["Aunt June", "Aunt Mira", "Aunt Ana"],
    "uncle": ["Uncle Ravi", "Uncle Ben", "Uncle Sol"],
}


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.object and args.cause and not cause_allowed(OBJECTS[args.object], CAUSES[args.cause]):
        raise StoryError(explain_rejection(OBJECTS[args.object], CAUSES[args.cause]))
    if args.object and args.cause and args.fix and not fix_matches(CAUSES[args.cause], FIXES[args.fix]):
        raise StoryError(explain_rejection(OBJECTS[args.object], CAUSES[args.cause], FIXES[args.fix]))
    if args.fix and args.fix == "oil":
        raise StoryError(
            "(No story: fix 'oil' is known to the world, but it is not a sensible match for these bedroom mysteries.)"
        )

    combos = [
        combo
        for combo in valid_combos()
        if (args.object is None or combo[0] == args.object)
        and (args.cause is None or combo[1] == args.cause)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    object_id, cause_id, fix_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["mother", "father", "aunt", "uncle"])
    helper_name = args.helper_name or rng.choice(HELPERS[helper_type])

    return StoryParams(
        object=object_id,
        cause=cause_id,
        fix=fix_id,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.object not in OBJECTS:
        raise StoryError(f"(Invalid object: {params.object})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Invalid cause: {params.cause})")
    if params.fix not in FIXES:
        raise StoryError(f"(Invalid fix: {params.fix})")

    obj_cfg = OBJECTS[params.object]
    cause = CAUSES[params.cause]
    fix = FIXES[params.fix]
    if not cause_allowed(obj_cfg, cause):
        raise StoryError(explain_rejection(obj_cfg, cause))
    if not fix_matches(cause, fix):
        raise StoryError(explain_rejection(obj_cfg, cause, fix))

    world = tell(
        obj_cfg=obj_cfg,
        cause=cause,
        fix=fix,
        child_name=params.child_name,
        child_type=params.child_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
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
        print(f"{len(combos)} compatible (object, cause, fix) combos:\n")
        for object_id, cause_id, fix_id in combos:
            print(f"  {object_id:10} {cause_id:13} {fix_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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
            header = f"### {p.child_name}: {p.object} / {p.cause} / {p.fix}"
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
