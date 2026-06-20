#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/anesthetist_gooshy_didey_cautionary_fable.py
=======================================================================

A standalone story world for a cautionary fable about **Didey**, a small animal
child who is told not to touch a grown-up clinic tool, ignores the warning, and
learns why careful hands matter. The word **anesthetist** appears naturally as
the calm clinic grown-up; the word **gooshy** appears in the safe comfort object
and in the sticky medicine-gel setting.

World premise
-------------
Didey visits a woodland clinic. A patient needs help, and the anesthetist has
set out a delicate breathing tool used to help patients sleep safely during a
small procedure. Didey wants to touch or play with it because it looks soft or
interesting. A helper warns Didey not to. If Didey ignores the warning, the tool
is spoiled or delayed, and the patient has to wait while the grown-up fixes the
problem. The lesson is simple and cautionary: clinic tools are not toys.

This world models:
- typed entities with physical `meters` and emotional `memes`
- a reasonableness gate over clinic tools, risks, and fixes
- a causal rule engine for contamination / delay / fear / relief
- state-driven prose with a beginning, turn, and ending image
- three QA sets grounded in simulated state
- an inline ASP twin for parity checks with `--verify`
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
IMPULSE_INIT = 6.0
CAREFUL_TRAITS = {"careful", "patient", "gentle", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    sterile: bool = False
    medical: bool = False
    comfort: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "hen", "doe", "vixen"}
        male = {"boy", "father", "uncle", "buck", "fox"}
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
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    smell: str
    waiting_detail: str
    patient_kind: str
    patient_name: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    touch_text: str
    danger_reason: str
    failure: str
    repair_need: str
    sterile: bool = True
    medical: bool = True
    fragility: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Mischief:
    id: str
    verb: str
    act_text: str
    contamination: int
    delay: int
    roughness: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    text: str
    qa_text: str
    fail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    texture: str
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


def _r_contamination_delay(world: World) -> list[str]:
    out: list[str] = []
    tool = world.entities.get("tool")
    if tool is None:
        return out
    if tool.meters["contaminated"] < THRESHOLD:
        return out
    sig = ("delay_from_contamination", tool.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    patient = world.get("patient")
    patient.memes["worry"] += 1
    room = world.get("room")
    room.meters["delay"] += 1
    out.append("__delay__")
    return out


def _r_damage_delay(world: World) -> list[str]:
    out: list[str] = []
    tool = world.entities.get("tool")
    if tool is None:
        return out
    if tool.meters["damaged"] < THRESHOLD:
        return out
    sig = ("delay_from_damage", tool.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    patient = world.get("patient")
    patient.memes["fear"] += 1
    room = world.get("room")
    room.meters["delay"] += 1
    out.append("__delay__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("contamination_delay", "physical", _r_contamination_delay),
    Rule("damage_delay", "physical", _r_damage_delay),
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


def hazard_at_risk(tool: Tool, mischief: Mischief) -> bool:
    return tool.medical and (mischief.contamination > 0 or mischief.roughness >= tool.fragility)


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def impact_value(tool: Tool, mischief: Mischief) -> int:
    return max(mischief.contamination, mischief.delay + max(0, mischief.roughness - tool.fragility + 1))


def is_resolved(fix: Fix, tool: Tool, mischief: Mischief) -> bool:
    return fix.power >= impact_value(tool, mischief)


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, helper_age: int, didey_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > didey_age
    authority = initial_care(trait) + 1.0 + (4.0 if helper_older else 0.0)
    return helper_older and authority > IMPULSE_INIT


def predict_trouble(world: World, tool_id: str, mischief: Mischief) -> dict:
    sim = world.copy()
    _do_mischief(sim, sim.get(tool_id), mischief, narrate=False)
    tool = sim.get(tool_id)
    room = sim.get("room")
    return {
        "contaminated": tool.meters["contaminated"] >= THRESHOLD,
        "damaged": tool.meters["damaged"] >= THRESHOLD,
        "delay": room.meters["delay"],
    }


def _do_mischief(world: World, tool: Entity, mischief: Mischief, narrate: bool = True) -> None:
    tool.meters["contaminated"] += mischief.contamination
    if mischief.roughness >= tool.attrs.get("fragility", 1):
        tool.meters["damaged"] += 1
    tool.meters["delayed"] += mischief.delay
    propagate(world, narrate=narrate)


def opening(world: World, didey: Entity, helper: Entity, adult: Entity, setting: Setting) -> None:
    didey.memes["wonder"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"In {setting.place}, where {setting.smell}, little {didey.id} came padding beside "
        f"{helper.id}. They were there because {setting.patient_name}, {setting.patient_kind}, "
        f"had a thorn that needed gentle help."
    )
    world.say(
        f"At the far table stood {adult.id}, the anesthetist, laying out careful things for the patient. "
        f"{setting.waiting_detail}"
    )


def introduce_tool(world: World, didey: Entity, tool: Tool) -> None:
    didey.memes["curiosity"] += 1
    world.say(
        f"Among them sat {tool.phrase}. To {didey.id}, it looked interesting enough to poke, "
        f"because it was close at paw and nothing in the room seemed to be moving yet."
    )


def temptation(world: World, didey: Entity, tool: Tool, mischief: Mischief) -> None:
    didey.memes["impulse"] += 1
    world.say(
        f'"What if I just {mischief.verb} {tool.label}?" {didey.id} whispered. '
        f'The idea felt quick and clever for one small heartbeat.'
    )


def warning(world: World, helper: Entity, didey: Entity, adult: Entity, tool: Tool, mischief: Mischief) -> None:
    pred = predict_trouble(world, "tool", mischief)
    helper.memes["care"] += 1
    world.facts["predicted_delay"] = pred["delay"]
    detail = tool.danger_reason
    extra = ""
    if pred["contaminated"] and pred["damaged"]:
        extra = " It could make the tool dirty and spoil it."
    elif pred["contaminated"]:
        extra = " Touching it with playful paws could make it dirty."
    elif pred["damaged"]:
        extra = " Rough play could spoil it."
    world.say(
        f'{helper.id} shook {helper.pronoun("possessive")} head. "{didey.id}, do not touch {tool.label}," '
        f'{helper.pronoun()} said. "{adult.id} the anesthetist needs it clean and ready for {setting_name(world)}. '
        f'{detail}.{extra}"'
    )


def setting_name(world: World) -> str:
    return world.facts["setting"].patient_name


def defy(world: World, didey: Entity, helper: Entity, tool: Tool, mischief: Mischief) -> None:
    didey.memes["defiance"] += 1
    older_helper = didey.attrs.get("relation") == "siblings" and helper.age > didey.age
    if older_helper:
        world.say(
            f'"Only one tiny touch," said {didey.id}. Even though {helper.id} was older, '
            f'{didey.id} flicked {helper.pronoun("possessive")} tail and stepped closer anyway.'
        )
    else:
        world.say(
            f'"Only one tiny touch," said {didey.id}, and stepped closer before the warning could settle.'
        )
    world.say(mischief.act_text.format(name=didey.id, tool=tool.label))


def back_down(world: World, didey: Entity, helper: Entity, adult: Entity, tool: Tool, comfort: Comfort) -> None:
    didey.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'{didey.id} looked at {helper.id}, then at {tool.label}, and drew {didey.pronoun("possessive")} paw back. '
        f'"No," {didey.pronoun()} said at last. "Clinic things are for care, not for play."'
    )
    world.say(
        f'{adult.id} smiled and slid over {comfort.phrase}, a {comfort.texture} thing for waiting hands. '
        f'{didey.id} squeezed it instead and sat quietly while the room stayed ready.'
    )


def consequence(world: World, didey: Entity, adult: Entity, patient: Entity, tool: Tool) -> None:
    dirty = tool.meters["contaminated"] >= THRESHOLD
    broken = tool.meters["damaged"] >= THRESHOLD
    if dirty and broken:
        world.say(
            f"At once, {adult.id}'s ears lifted. {tool.failure} It was no longer clean, and part of it had gone crooked besides."
        )
    elif dirty:
        world.say(
            f"At once, {adult.id}'s ears lifted. {tool.failure} It was no longer clean enough to use."
        )
    else:
        world.say(
            f"At once, {adult.id}'s ears lifted. {tool.failure} It was no longer ready to use."
        )
    world.say(
        f"{patient.id} shrank closer to the blanket on the stool. Waiting had just grown longer, "
        f"and the room felt smaller and quieter than before."
    )
    didey.memes["guilt"] += 1
    patient.memes["worry"] += 1


def repair(world: World, adult: Entity, fix: Fix, tool: Tool, patient: Entity) -> None:
    body = fix.text.format(tool=tool.label, need=tool.repair_need, patient=patient.id)
    world.say(
        f"{adult.id}, the anesthetist, did not shout. {adult.pronoun().capitalize()} {body}."
    )
    world.get("room").meters["delay"] = 0.0
    tool_ent = world.get("tool")
    tool_ent.meters["contaminated"] = 0.0
    tool_ent.meters["damaged"] = 0.0
    patient.memes["fear"] = 0.0
    patient.memes["worry"] = 0.0
    didey = world.get("Didey")
    didey.memes["fear"] = 0.0
    didey.memes["relief"] += 1


def lesson(world: World, didey: Entity, helper: Entity, adult: Entity, tool: Tool) -> None:
    didey.memes["lesson"] += 1
    didey.memes["love"] += 1
    helper.memes["love"] += 1
    world.say(
        f'Then {adult.id} knelt so {adult.pronoun()} was eye to eye with {didey.id}. '
        f'"Little paws can make big trouble in a place of care," {adult.pronoun()} said gently. '
        f'"{tool.label.capitalize()} is not a toy. When we touch what we do not understand, someone waiting for help may have to wait even longer."'
    )
    world.say(
        f'{didey.id} lowered {didey.pronoun("possessive")} ears. "{patient_name(world)} had to wait because of me," '
        f'{didey.pronoun()} whispered. "{tool.label.capitalize()} is not for play."'
    )


def patient_name(world: World) -> str:
    return world.get("patient").id


def safe_end(world: World, didey: Entity, helper: Entity, adult: Entity, patient: Entity, comfort: Comfort) -> None:
    didey.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"When everything was ready again, {patient.id} took a brave breath, and {adult.id} used the clean tool with quiet skill. "
        f"Soon the thorn was out, and the patient could rest."
    )
    world.say(
        f'As they waited afterward, {adult.id} gave {didey.id} {comfort.phrase}. '
        f'It was so {comfort.texture} that {didey.id} smiled without reaching for any clinic thing again.'
    )
    world.say(
        f"From that day on, whenever Didey saw trays, masks, or bottles in a place of healing, "
        f"{didey.pronoun()} tucked {didey.pronoun('possessive')} paws close and remembered that careful waiting is a kind of kindness."
    )


def burned_end(world: World, didey: Entity, helper: Entity, adult: Entity, patient: Entity) -> None:
    didey.memes["lesson"] += 1
    didey.memes["sadness"] += 1
    world.say(
        f"But the fixing took too long. {patient.id} had to go home and come back another day, still carrying the thorn and the worry of it."
    )
    world.say(
        f'{adult.id} put away the spoiled things and said, "Hurry without wisdom can steal help from someone else." '
        f'Didey walked out slowly beside {helper.id}, with no song left in {didey.pronoun("possessive")} step.'
    )
    world.say(
        "After that, Didey never touched the tools of healers again. In fables, one foolish paw may delay a stranger's comfort, "
        "and that is sorrow enough to remember."
    )


def tell(
    setting: Setting,
    tool: Tool,
    mischief: Mischief,
    comfort: Comfort,
    fix: Fix,
    helper_name: str = "Mira",
    helper_type: str = "girl",
    adult_type: str = "aunt",
    helper_trait: str = "careful",
    didey_age: int = 4,
    helper_age: int = 6,
    relation: str = "siblings",
) -> World:
    world = World()
    didey = world.add(Entity(
        id="Didey",
        kind="character",
        type="child",
        role="hero",
        age=didey_age,
        attrs={"relation": relation},
        traits=["small", "quick"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        role="helper",
        age=helper_age,
        attrs={"relation": relation},
        traits=[helper_trait],
    ))
    adult = world.add(Entity(
        id="Aunt Brindle" if adult_type == "aunt" else "Uncle Brindle",
        kind="character",
        type=adult_type,
        role="anesthetist",
        label="the anesthetist",
    ))
    patient = world.add(Entity(
        id=setting.patient_name,
        kind="character",
        type=setting.patient_kind,
        role="patient",
    ))
    world.add(Entity(id="room", type="room", label=setting.place))
    tool_ent = world.add(Entity(
        id="tool",
        type="tool",
        label=tool.label,
        sterile=tool.sterile,
        medical=tool.medical,
        attrs={"fragility": tool.fragility},
    ))
    comfort_ent = world.add(Entity(
        id="comfort",
        type="comfort",
        label=comfort.label,
        comfort=True,
    ))

    opening(world, didey, helper, adult, setting)
    introduce_tool(world, didey, tool)

    world.para()
    temptation(world, didey, tool, mischief)
    world.facts["setting"] = setting
    warning(world, helper, didey, adult, tool, mischief)

    averted = would_avert(relation, helper_age, didey_age, helper_trait)
    if averted:
        back_down(world, didey, helper, adult, tool, comfort)
        world.para()
        world.say(
            f"{setting.patient_name} was helped without delay, and the whole room seemed to breathe easier."
        )
        world.say(
            f"Thus Didey learned the wiser way before harm was done: when a gentle grown-up says wait, waiting can protect more than oneself."
        )
        outcome = "averted"
    else:
        defy(world, didey, helper, tool, mischief)
        _do_mischief(world, tool_ent, mischief, narrate=False)

        world.para()
        consequence(world, didey, adult, patient, tool)
        resolved = is_resolved(fix, tool, mischief)
        if resolved:
            repair(world, adult, fix, tool, patient)
            lesson(world, didey, helper, adult, tool)
            world.para()
            safe_end(world, didey, helper, adult, patient, comfort)
            outcome = "contained"
        else:
            body = fix.fail.format(tool=tool.label, need=tool.repair_need, patient=patient.id)
            world.say(f"{adult.id} tried to {body}.")
            world.para()
            burned_end(world, didey, helper, adult, patient)
            outcome = "delayed_away"

    world.facts.update(
        didey=didey,
        helper=helper,
        adult=adult,
        patient=patient,
        tool_cfg=tool,
        mischief=mischief,
        comfort_cfg=comfort,
        fix=fix,
        outcome=outcome,
        relation=relation,
        impact=impact_value(tool, mischief),
        averted=averted,
        predicted=world.facts.get("predicted_delay", 0),
        harmed=tool_ent.meters["contaminated"] >= THRESHOLD or tool_ent.meters["damaged"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "moss_clinic": Setting(
        "moss_clinic",
        "the Moss Lantern Clinic",
        "the air smelled of mint leaves and clean linen",
        "On one shelf sat jars of bandage moss, and on another waited folded blankets for nervous paws.",
        "mouse",
        "Nib",
        tags={"clinic"},
    ),
    "reed_infirmary": Setting(
        "reed_infirmary",
        "the Reedbank Infirmary",
        "the air smelled of river reeds and soap",
        "Small lamps glowed in glass acorns, and a low stool stood ready for the next patient.",
        "otter",
        "Pipkin",
        tags={"clinic"},
    ),
    "hollow_hospital": Setting(
        "hollow_hospital",
        "the Hollow Tree Hospital",
        "the air smelled of pine and warm water",
        "Neat trays shone on a table, and a basket of folded wraps waited by the wall.",
        "hedgehog",
        "Bramble",
        tags={"clinic"},
    ),
}

TOOLS = {
    "sleepy_mask": Tool(
        "sleepy_mask",
        "the sleepy mask",
        "a little sleepy mask with a round, clear cup and a soft band",
        "pat it and peek inside",
        "It must stay clean so the patient can breathe through it safely",
        "The sleepy mask had picked up grubby smears",
        "fresh cleaning and a new band",
        fragility=1,
        tags={"anesthetist", "mask", "clinic"},
    ),
    "breathing_bag": Tool(
        "breathing_bag",
        "the breathing bag",
        "a pear-shaped breathing bag that looked soft enough to squeeze",
        "squeeze it hard and let it boing back",
        "It must stay clean and springy so the anesthetist can use it the right way",
        "The breathing bag sagged crookedly after the rough play",
        "a spare bag from the cabinet",
        fragility=1,
        tags={"anesthetist", "breathing_bag", "clinic"},
    ),
    "sleepy_tube": Tool(
        "sleepy_tube",
        "the sleepy tube",
        "a curled sleepy tube lying in a neat silver loop",
        "swing it like a vine",
        "It must stay clean and untangled before it is used",
        "The sleepy tube had been dragged askew and could not be trusted at once",
        "fresh cleaning and careful untwisting",
        fragility=2,
        tags={"anesthetist", "tube", "clinic"},
    ),
}

MISCHIEFS = {
    "pat": Mischief(
        "pat",
        "pat",
        "{name} gave {tool} two playful pats with sticky paws.",
        contamination=1,
        delay=1,
        roughness=0,
        tags={"sticky", "touch"},
    ),
    "squeeze": Mischief(
        "squeeze",
        "squeeze",
        "{name} grabbed {tool} and squeezed with both paws, just to see what it would do.",
        contamination=1,
        delay=1,
        roughness=2,
        tags={"touch", "rough"},
    ),
    "swing": Mischief(
        "swing",
        "swing",
        "{name} lifted {tool} and swung it in a quick little circle through the air.",
        contamination=1,
        delay=2,
        roughness=2,
        tags={"touch", "rough"},
    ),
}

FIXES = {
    "clean_replace": Fix(
        "clean_replace",
        3,
        3,
        "washed {tool}, fetched what was needed for {need}, and made the tray ready again before {patient} had to wait long",
        "cleaned the tool and replaced what needed replacing",
        "clean and replace {tool}, but the spoiled delay had already stretched too far for {patient}",
        tags={"cleaning", "replace"},
    ),
    "swap_spare": Fix(
        "swap_spare",
        3,
        2,
        "opened the cabinet, found a spare for {tool}, and checked everything twice before beginning",
        "brought out a spare tool and checked it carefully",
        "find a spare for {tool}, but there was no quick enough match for {patient} that day",
        tags={"spare"},
    ),
    "wipe_only": Fix(
        "wipe_only",
        1,
        1,
        "gave {tool} a quick wipe",
        "gave the tool a quick wipe",
        "give {tool} only a quick wipe, which was not enough for safe care of {patient}",
        tags={"wipe"},
    ),
}

COMFORTS = {
    "gooshy_star": Comfort(
        "gooshy_star",
        "gooshy star",
        "a gooshy star to squeeze",
        "soft and gooshy",
        tags={"gooshy", "comfort"},
    ),
    "gooshy_berry": Comfort(
        "gooshy_berry",
        "gooshy berry ball",
        "a gooshy berry ball for waiting paws",
        "round and gooshy",
        tags={"gooshy", "comfort"},
    ),
    "felt_mouse": Comfort(
        "felt_mouse",
        "felt mouse",
        "a tiny felt mouse",
        "small and comforting",
        tags={"comfort"},
    ),
}

HELPER_NAMES = ["Mira", "Tavi", "Lark", "Nell", "Pico", "Rill"]
HELPER_TYPES = ["girl", "boy"]
HELPER_TRAITS = ["careful", "patient", "gentle", "thoughtful", "curious", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_fixes():
        return combos
    for setting_id in SETTINGS:
        for tool_id, tool in TOOLS.items():
            for mischief_id, mischief in MISCHIEFS.items():
                if hazard_at_risk(tool, mischief):
                    combos.append((setting_id, tool_id, mischief_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    tool: str
    mischief: str
    comfort: str
    fix: str
    helper_name: str
    helper_type: str
    adult_type: str
    helper_trait: str
    didey_age: int = 4
    helper_age: int = 6
    relation: str = "siblings"
    seed: Optional[int] = None


KNOWLEDGE = {
    "anesthetist": [(
        "What does an anesthetist do?",
        "An anesthetist is a trained grown-up who helps a patient sleep safely or stay calm and comfortable during a medical procedure. They watch carefully so the patient can be helped in a safe way."
    )],
    "clinic": [(
        "Why should children leave clinic tools alone?",
        "Clinic tools must stay clean and ready so the grown-ups can use them to help patients. Touching them for fun can make care slower or less safe."
    )],
    "mask": [(
        "Why does a medical mask need to stay clean?",
        "A medical mask touches a patient's face and breathing, so it needs to be very clean. If it gets dirty, the grown-up may have to stop and clean or replace it."
    )],
    "breathing_bag": [(
        "What is a breathing bag for?",
        "A breathing bag is part of breathing equipment that a trained grown-up may use to help air move gently for a patient. It is not a toy, even if it looks soft."
    )],
    "tube": [(
        "Why is it bad to tangle a medical tube?",
        "A medical tube needs to be placed the right way and kept clean. If it is tangled or dragged around, the grown-up may need time to check it or replace it."
    )],
    "sticky": [(
        "Why can sticky paws cause trouble?",
        "Sticky paws leave smears and dirt behind. In a place where things must stay clean, even a little smear can matter."
    )],
    "cleaning": [(
        "Why is cleaning important in a clinic?",
        "Cleaning helps keep germs and dirt away from patients and tools. In a clinic, being clean helps care stay safe."
    )],
    "replace": [(
        "Why might a grown-up replace a spoiled tool?",
        "If a tool is dirty or bent, it may not be ready to use safely. A grown-up may bring a clean spare instead."
    )],
    "spare": [(
        "What is a spare tool?",
        "A spare tool is another clean tool kept ready in case the first one cannot be used. Spares help careful grown-ups solve problems safely."
    )],
    "gooshy": [(
        "What does gooshy mean?",
        "Gooshy means soft and squishy in a pleasantly smooshy way. A gooshy comfort toy is for squeezing, unlike delicate tools that should be left alone."
    )],
}
KNOWLEDGE_ORDER = [
    "anesthetist", "clinic", "mask", "breathing_bag", "tube",
    "sticky", "cleaning", "replace", "spare", "gooshy",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tool = f["tool_cfg"]
    fix = f["fix"]
    comfort = f["comfort_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            'Write a cautionary fable for ages 3 to 5 that includes the words "anesthetist", "gooshy", and "Didey".',
            f"Tell a fable where Didey wants to touch {tool.label} in a woodland clinic, but listens to an older helper and chooses a {comfort.label} instead.",
            f'Write a gentle cautionary story about waiting wisely in a clinic and learning that "{tool.label} is not a toy."',
        ]
    if outcome == "contained":
        return [
            'Write a cautionary fable for ages 3 to 5 that includes the words "anesthetist", "gooshy", and "Didey".',
            f"Tell a story where Didey ignores a warning, spoils {tool.label}, and the anesthetist must {fix.qa_text}.",
            "Write a fable with a calm grown-up lesson showing that touching special tools can delay help for someone else.",
        ]
    return [
        'Write a cautionary fable for ages 3 to 5 that includes the words "anesthetist", "gooshy", and "Didey".',
        f"Tell a sad cautionary fable where Didey spoils {tool.label} and the patient must go home and come back another day.",
        "Write a fable where impatience harms someone else's chance to be helped, and the lesson is remembered.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    didey = f["didey"]
    helper = f["helper"]
    adult = f["adult"]
    patient = f["patient"]
    tool = f["tool_cfg"]
    comfort = f["comfort_cfg"]
    fix = f["fix"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Didey, {helper.id}, and {adult.id} the anesthetist in a woodland clinic. "
            f"The patient {patient.id} matters too, because the whole problem turns on keeping help ready for {patient.pronoun('object')}."
        ),
        (
            f"Why did {helper.id} tell Didey not to touch {tool.label}?",
            f"{helper.id} knew {tool.label} had to stay clean and ready for {patient.id}. "
            f"If Didey played with it, the anesthetist might have to stop and fix the problem before helping the patient."
        ),
    ]
    if outcome == "averted":
        qa.append((
            "What did Didey do after the warning?",
            f"Didey pulled back {didey.pronoun('possessive')} paw and chose {comfort.phrase} instead. "
            f"That kept the room ready, so {patient.id} could be helped without delay."
        ))
        qa.append((
            "How did the story end?",
            f"It ended peacefully, with the clinic still calm and the patient helped on time. "
            f"Didey learned that careful waiting can protect another creature's comfort."
        ))
    elif outcome == "contained":
        qa.append((
            "What happened when Didey touched the tool?",
            f"Didey spoiled {tool.label}, so the anesthetist had to pause and {fix.qa_text}. "
            f"That made {patient.id} wait longer, which is why Didey felt sorry and listened to the lesson."
        ))
        qa.append((
            "What lesson did the anesthetist teach Didey?",
            f"{adult.id} taught that clinic tools are not toys and that one playful touch can delay help for someone else. "
            f"The lesson mattered because the waiting patient felt the consequence right away."
        ))
        qa.append((
            "Why was the gooshy toy important at the end?",
            f"It gave Didey a safe thing to squeeze with restless paws. "
            f"The gooshy comfort object met the need for touching without putting any patient or tool at risk."
        ))
    else:
        qa.append((
            "How did Didey's choice hurt someone else?",
            f"Didey's impatience spoiled the tool so badly that {patient.id} had to go home and come back another day. "
            f"The fable makes the harm clear by showing that foolish play can steal time from someone who needs care."
        ))
        qa.append((
            "How did the story end?",
            f"It ended sadly, with the patient still waiting for help and Didey walking away in shame. "
            f"That sorrow is the cautionary proof of what careless hands can cause."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["tool_cfg"].tags) | set(f["mischief"].tags) | set(f["comfort_cfg"].tags) | {"clinic"}
    if f["outcome"] != "averted":
        tags |= set(f["fix"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [n for n, on in (("sterile", e.sterile), ("medical", e.medical), ("comfort", e.comfort)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        "moss_clinic", "sleepy_mask", "pat", "gooshy_star", "clean_replace",
        "Mira", "girl", "aunt", "careful", didey_age=4, helper_age=7, relation="siblings"
    ),
    StoryParams(
        "reed_infirmary", "breathing_bag", "squeeze", "gooshy_berry", "swap_spare",
        "Tavi", "boy", "uncle", "gentle", didey_age=5, helper_age=5, relation="friends"
    ),
    StoryParams(
        "hollow_hospital", "sleepy_tube", "swing", "felt_mouse", "swap_spare",
        "Lark", "girl", "aunt", "thoughtful", didey_age=4, helper_age=5, relation="friends"
    ),
    StoryParams(
        "moss_clinic", "breathing_bag", "squeeze", "gooshy_star", "wipe_only",
        "Pico", "boy", "uncle", "patient", didey_age=5, helper_age=5, relation="friends"
    ),
]


def explain_rejection(tool: Tool, mischief: Mischief) -> str:
    return (
        f"(No story: {mischief.verb} with {tool.label} would not create enough real clinic trouble here. "
        f"A cautionary story needs a medical tool that can genuinely be contaminated or spoiled by the chosen mischief.)"
    )


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense (sense={fix.sense} < {SENSE_MIN}). "
        f"Try a safer fix such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.helper_age, params.didey_age, params.helper_trait):
        return "averted"
    resolved = is_resolved(FIXES[params.fix], TOOLS[params.tool], MISCHIEFS[params.mischief])
    return "contained" if resolved else "delayed_away"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(Tool, Mischief) :- medical(Tool), contamination(Mischief, C), C > 0.
hazard(Tool, Mischief) :- medical(Tool), roughness(Mischief, R), fragility(Tool, F), R >= F.
sensible(Fix) :- fix(Fix), sense(Fix, S), sense_min(M), S >= M.
valid(Setting, Tool, Mischief) :- setting(Setting), tool(Tool), mischief(Mischief), hazard(Tool, Mischief).

% --- impact and ending model -----------------------------------------------
impact(Tool, Mischief, C) :- contamination(Mischief, C), roughness(Mischief, R), fragility(Tool, F), R < F.
impact(Tool, Mischief, D + R - F + 1) :- delay(Mischief, D), roughness(Mischief, R), fragility(Tool, F), R >= F.
impact(Tool, Mischief, C) :- contamination(Mischief, C), delay(Mischief, D), roughness(Mischief, R), fragility(Tool, F), R >= F, C >= D + R - F + 1.
impact(Tool, Mischief, D + R - F + 1) :- contamination(Mischief, C), delay(Mischief, D), roughness(Mischief, R), fragility(Tool, F), R >= F, C < D + R - F + 1.

cautious_now(T) :- trait(T), is_careful(T).
init_care(5) :- trait(T), cautious_now(T).
init_care(3) :- trait(T), not cautious_now(T).
helper_older :- relation(siblings), helper_age(HA), didey_age(DA), HA > DA.
bonus(4) :- helper_older.
bonus(0) :- not helper_older.
authority(C + 1 + B) :- init_care(C), bonus(B).
averted :- helper_older, authority(A), impulse_init(I), A > I.

resolved :- chosen_tool(T), chosen_mischief(M), chosen_fix(Fx), impact(T, M, V), power(Fx, P), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, resolved.
outcome(delayed_away) :- not averted, not resolved.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if tool.medical:
            lines.append(asp.fact("medical", tid))
        lines.append(asp.fact("fragility", tid, tool.fragility))
    for mid, mischief in MISCHIEFS.items():
        lines.append(asp.fact("mischief", mid))
        lines.append(asp.fact("contamination", mid, mischief.contamination))
        lines.append(asp.fact("delay", mid, mischief.delay))
        lines.append(asp.fact("roughness", mid, mischief.roughness))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("impulse_init", int(IMPULSE_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("is_careful", trait))
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
    scenario = "\n".join([
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_mischief", params.mischief),
        asp.fact("chosen_fix", params.fix),
        asp.fact("relation", params.relation),
        asp.fact("helper_age", params.helper_age),
        asp.fact("didey_age", params.didey_age),
        asp.fact("trait", params.helper_trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {f.id for f in sensible_fixes()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible fixes match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    for s in range(100):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: Didey, a clinic tool, and a cautionary lesson. "
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--mischief", choices=MISCHIEFS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--adult", choices=["aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.mischief:
        tool = TOOLS[args.tool]
        mischief = MISCHIEFS[args.mischief]
        if not hazard_at_risk(tool, mischief):
            raise StoryError(explain_rejection(tool, mischief))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.tool is None or c[1] == args.tool)
        and (args.mischief is None or c[2] == args.mischief)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, tool, mischief = rng.choice(sorted(combos))
    comfort = rng.choice(sorted(COMFORTS))
    fix = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    helper_name = rng.choice(HELPER_NAMES)
    helper_type = rng.choice(HELPER_TYPES)
    adult_type = args.adult or rng.choice(["aunt", "uncle"])
    helper_trait = rng.choice(HELPER_TRAITS)
    relation = rng.choice(["siblings", "friends"])
    didey_age, helper_age = rng.sample([3, 4, 5, 6, 7], 2)
    return StoryParams(
        setting, tool, mischief, comfort, fix, helper_name, helper_type, adult_type, helper_trait,
        didey_age=didey_age, helper_age=helper_age, relation=relation
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        TOOLS[params.tool],
        MISCHIEFS[params.mischief],
        COMFORTS[params.comfort],
        FIXES[params.fix],
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        adult_type=params.adult_type,
        helper_trait=params.helper_trait,
        didey_age=params.didey_age,
        helper_age=params.helper_age,
        relation=params.relation,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, tool, mischief) combos:\n")
        for setting, tool, mischief in combos:
            print(f"  {setting:16} {tool:14} {mischief}")
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
            header = f"### Didey: {p.tool} + {p.mischief} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
