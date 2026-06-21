#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hernia_surprise_detective_story.py
=============================================================

A small storyworld about a child detective who notices clues, solves a family
mystery, and learns that the surprising answer is a real body problem called a
hernia. The world model tracks physical strain, caution, relief, and help.
State drives the prose: a grown-up strains while lifting something heavy, a
child notices clues, a helper explains the diagnosis, and the family changes
the plan in a safe way.

Run it
------
python storyworlds/worlds/gpt-5.4/hernia_surprise_detective_story.py
python storyworlds/worlds/gpt-5.4/hernia_surprise_detective_story.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/hernia_surprise_detective_story.py --all
python storyworlds/worlds/gpt-5.4/hernia_surprise_detective_story.py --qa
python storyworlds/worlds/gpt-5.4/hernia_surprise_detective_story.py --json
python storyworlds/worlds/gpt-5.4/hernia_surprise_detective_story.py --trace
python storyworlds/worlds/gpt-5.4/hernia_surprise_detective_story.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandma", "aunt", "doctor_f"}
        male = {"boy", "father", "dad", "man", "grandpa", "uncle", "doctor_m"}
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
            "grandma": "grandma",
            "grandpa": "grandpa",
            "uncle": "uncle",
            "aunt": "aunt",
        }.get(self.type, self.label or self.type)


@dataclass
class Setting:
    id: str
    label: str
    scene_open: str
    clue_spot: str
    closing_good: str
    closing_cozy: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Load:
    id: str
    label: str
    phrase: str
    weight: int
    awkward: str
    plan: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    label: str
    title: str
    explain: str
    reassurance: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Support:
    id: str
    label: str
    phrase: str
    power: int
    method: str
    ending_outdoor: str
    ending_cozy: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    action: str
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


def _r_bulge(world: World) -> list[str]:
    out: list[str] = []
    patient = world.entities.get("patient")
    if patient is None:
        return out
    if patient.meters["strain"] < THRESHOLD:
        return out
    sig = ("bulge", patient.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    patient.meters["bulge"] += 1
    patient.memes["worry"] += 1
    detective = world.entities.get("detective")
    if detective is not None:
        detective.memes["curiosity"] += 1
    out.append("__bulge__")
    return out


def _r_rest(world: World) -> list[str]:
    out: list[str] = []
    patient = world.entities.get("patient")
    if patient is None:
        return out
    if patient.meters["bulge"] < THRESHOLD:
        return out
    sig = ("rest", patient.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    patient.memes["caution"] += 1
    patient.meters["lifting_stopped"] += 1
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="bulge", tag="physical", apply=_r_bulge),
    Rule(name="rest", tag="physical", apply=_r_rest),
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


def reasonable_load(load: Load) -> bool:
    return load.weight >= 2


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for load_id, load in LOADS.items():
            if not reasonable_load(load):
                continue
            for support_id in SUPPORTS:
                combos.append((setting_id, load_id, support_id))
    return combos


def support_succeeds(load: Load, support: Support) -> bool:
    return support.power >= load.weight


def outcome_of(params: "StoryParams") -> str:
    load = LOADS[params.load]
    support = SUPPORTS[params.support]
    return "outdoor" if support_succeeds(load, support) else "cozy"


def predict_trouble(world: World, load_id: str) -> dict:
    sim = world.copy()
    patient = sim.get("patient")
    load = LOADS[load_id]
    patient.meters["strain"] += float(load.weight)
    propagate(sim, narrate=False)
    return {
        "bulge": patient.meters["bulge"] >= THRESHOLD,
        "worry": patient.memes["worry"],
        "stopped": patient.meters["lifting_stopped"] >= THRESHOLD,
    }


def detective_setup(world: World, detective: Entity, patient: Entity, setting: Setting, load: Load) -> None:
    detective.memes["play"] += 1
    world.say(
        f"{setting.scene_open} {detective.id} had made a paper badge and whispered "
        f"that today {detective.pronoun()} was the best little detective in the house."
    )
    world.say(
        f"{patient.id} was getting ready to carry {load.phrase} for {load.plan}, "
        f"and everything looked ordinary at first."
    )


def lifting_incident(world: World, patient: Entity, load: Load) -> None:
    patient.meters["strain"] += float(load.weight)
    propagate(world, narrate=False)
    patient.memes["pain"] += 1
    world.say(
        f"But when {patient.id} lifted {load.phrase}, {patient.pronoun()} stopped in the middle of the step "
        f"and put a hand on {patient.pronoun('possessive')} middle. The {load.label} felt {load.awkward}, "
        f"and {patient.pronoun()} did not smile the way {patient.pronoun()} had a moment before."
    )
    if patient.meters["bulge"] >= THRESHOLD:
        world.say(
            f"{detective_name(world)} noticed one more clue: a small bump showed under "
            f"{patient.pronoun('possessive')} shirt when {patient.pronoun()} stood up straight."
        )


def detective_name(world: World) -> str:
    det = world.entities.get("detective")
    return det.id if det is not None else "The child"


def clue_search(world: World, detective: Entity, patient: Entity, setting: Setting) -> None:
    world.say(
        f"{detective.id} followed the mystery to {setting.clue_spot} and looked carefully at every clue. "
        f"There was no broken chair, no sneaky cat, and no missing treasure."
    )
    world.say(
        f'"Something is wrong, but it is not a thief case," {detective.id} said. '
        f'{detective.pronoun().capitalize()} pointed to {patient.pronoun("possessive")} careful steps and the hand on the tummy.'
    )


def question_patient(world: World, detective: Entity, patient: Entity) -> None:
    detective.memes["care"] += 1
    patient.memes["trust"] += 1
    world.say(
        f'{detective.id} came closer and asked in a soft detective voice, '
        f'"Did that lift hurt?"'
    )
    world.say(
        f'{patient.id} nodded. "A little. I felt a tug, and now I think I should sit down and get help."'
    )


def call_helper(world: World, detective: Entity, patient: Entity, helper: Entity, response: Response) -> None:
    detective.memes["responsible"] += 1
    patient.memes["relief"] += 1
    world.say(
        f"That was the surprising turn in the case: instead of hunting for a robber, "
        f"{detective.id} hurried to {response.action}."
    )
    world.say(
        f"Soon {helper.label} was listening, looking, and asking calm questions while "
        f"{patient.id} rested in a sturdy chair."
    )


def diagnose(world: World, helper: Entity, patient: Entity, detective: Entity, helper_cfg: HelperCfg) -> None:
    patient.meters["diagnosed"] += 1
    patient.memes["worry"] = 0.0
    patient.memes["relief"] += 1
    detective.memes["surprise"] += 1
    detective.memes["understanding"] += 1
    world.say(
        f'{helper.label} smiled gently. "{helper_cfg.explain} It may be a hernia," '
        f'{helper.pronoun()} said. "{helper_cfg.reassurance}"'
    )
    world.say(
        f"{detective.id}'s eyes grew wide. That was the answer to the whole detective story: "
        f"the mystery clue had a real name, and it was not anybody's fault."
    )


def safe_plan(world: World, detective: Entity, patient: Entity, setting: Setting, load: Load, support: Support) -> None:
    patient.meters["lifting_stopped"] += 1
    detective.memes["helpfulness"] += 1
    world.say(
        f"So the family changed the plan. {patient.id} would not lift {load.phrase} again that day, "
        f"and the case turned into a teamwork case instead."
    )
    if support_succeeds(load, support):
        patient.memes["hope"] += 1
        world.say(
            f"They used {support.phrase}, and {support.method}. "
            f"{support.ending_outdoor}"
        )
        world.say(setting.closing_good)
    else:
        patient.memes["calm"] += 1
        world.say(
            f"They looked at {support.phrase}, but it was not strong enough for {load.phrase}. "
            f"So nobody took a silly chance. {support.ending_cozy}"
        )
        world.say(setting.closing_cozy)


def closing_note(world: World, detective: Entity, patient: Entity) -> None:
    detective.memes["relief"] += 1
    patient.memes["gratitude"] += 1
    world.say(
        f"That night {patient.id} thanked {detective.id} for noticing the clues and speaking up. "
        f"The little detective touched the paper badge and felt proud, because solving a case could mean helping a person feel safe."
    )


def tell(
    setting: Setting,
    load: Load,
    helper_cfg: HelperCfg,
    support: Support,
    response: Response,
    detective_name_value: str = "Mia",
    detective_gender: str = "girl",
    patient_name: str = "Dad",
    patient_type: str = "father",
) -> World:
    world = World()
    detective = world.add(
        Entity(
            id=detective_name_value,
            kind="character",
            type=detective_gender,
            role="detective",
            label=detective_name_value,
            tags={"detective"},
        )
    )
    patient = world.add(
        Entity(
            id=patient_name,
            kind="character",
            type=patient_type,
            role="patient",
            label=patient_name,
            tags={"family"},
        )
    )
    helper_type = "doctor_f" if helper_cfg.id == "doctor_lee" else "doctor_m"
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label=helper_cfg.label,
            tags=set(helper_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="load",
            kind="thing",
            type="load",
            label=load.label,
            phrase=load.phrase,
            tags=set(load.tags),
        )
    )

    detective_setup(world, detective, patient, setting, load)
    world.para()
    lifting_incident(world, patient, load)
    clue_search(world, detective, patient, setting)
    question_patient(world, detective, patient)
    world.para()
    call_helper(world, detective, patient, helper, response)
    diagnose(world, helper, patient, detective, helper_cfg)
    world.para()
    safe_plan(world, detective, patient, setting, load, support)
    closing_note(world, detective, patient)

    world.facts.update(
        setting=setting,
        load=load,
        helper_cfg=helper_cfg,
        support=support,
        response=response,
        detective=detective,
        patient=patient,
        helper=helper,
        diagnosis="hernia",
        surprise=True,
        outcome="outdoor" if support_succeeds(load, support) else "cozy",
        support_worked=support_succeeds(load, support),
        called_helper=True,
        noticed_bump=patient.meters["bulge"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "garden": Setting(
        id="garden",
        label="the garden",
        scene_open="In the bright garden behind the house,",
        clue_spot="the back steps",
        closing_good="Soon the path was clear, the air smelled like tomatoes, and the case ended in warm sunshine instead of worry.",
        closing_cozy="Instead, they carried only light things inside and made hot cocoa while the big job waited for another day.",
        tags={"garden"},
    ),
    "attic": Setting(
        id="attic",
        label="the attic",
        scene_open="Up in the dusty attic,",
        clue_spot="the top stair",
        closing_good="Soon the old trunk was where it belonged, and the detective case ended with a happy little laugh in the quiet attic light.",
        closing_cozy="Instead, they stacked only soft blankets downstairs and turned the afternoon into a snug sorting game.",
        tags={"attic"},
    ),
    "porch": Setting(
        id="porch",
        label="the porch",
        scene_open="On the shady front porch,",
        clue_spot="the striped rug by the door",
        closing_good="Soon the picnic things were ready, and the porch mystery ended with birds singing in the hedge.",
        closing_cozy="Instead, they spread the cloth on the living-room floor and had the surprise picnic indoors.",
        tags={"porch"},
    ),
}

LOADS = {
    "book_box": Load(
        id="book_box",
        label="box of books",
        phrase="a box of old books",
        weight=2,
        awkward="heavy and hard to hold all at once",
        plan="making a reading corner",
        tags={"books", "lifting"},
    ),
    "cooler": Load(
        id="cooler",
        label="picnic cooler",
        phrase="the picnic cooler full of juice and fruit",
        weight=2,
        awkward="full and sloshy",
        plan="the family picnic",
        tags={"picnic", "lifting"},
    ),
    "soil_bag": Load(
        id="soil_bag",
        label="bag of garden soil",
        phrase="a giant bag of garden soil",
        weight=4,
        awkward="very heavy and floppy at the same time",
        plan="planting beans",
        tags={"garden", "lifting"},
    ),
    "trunk": Load(
        id="trunk",
        label="old trunk",
        phrase="an old trunk with brass corners",
        weight=4,
        awkward="big, stiff, and heavier than it looked",
        plan="tidying the attic",
        tags={"attic", "lifting"},
    ),
    "pillows": Load(
        id="pillows",
        label="armful of pillows",
        phrase="an armful of soft pillows",
        weight=0,
        awkward="soft but light",
        plan="making a reading nook",
        tags={"light", "lifting"},
    ),
}

HELPERS = {
    "doctor_lee": HelperCfg(
        id="doctor_lee",
        label="Dr. Lee",
        title="doctor",
        explain="Sometimes a weak spot in the tummy wall can make a little bulge after a heavy lift.",
        reassurance="That means we should rest, let a doctor keep checking it, and not strain the body.",
        tags={"doctor", "hernia"},
    ),
    "nurse_omar": HelperCfg(
        id="nurse_omar",
        label="Nurse Omar",
        title="nurse",
        explain="Sometimes a strong lift can push at a weak spot in the tummy and make a bump.",
        reassurance="That means rest first and let the clinic decide the next safe step.",
        tags={"nurse", "hernia"},
    ),
}

SUPPORTS = {
    "wagon": Support(
        id="wagon",
        label="wagon",
        phrase="the red wagon",
        power=3,
        method="the heavy things rolled along instead of being carried",
        ending_outdoor="The mystery did not stop the day; it only changed the way the work was done.",
        ending_cozy="They chose a smaller job and let the wagon wait by the wall.",
        tags={"wagon", "help"},
    ),
    "neighbor_team": Support(
        id="neighbor_team",
        label="neighbor team",
        phrase="two helpful neighbors with strong arms",
        power=5,
        method="the load moved safely while the patient kept both feet planted and hands empty",
        ending_outdoor="Everyone waved like a happy detective squad finishing the hardest part together.",
        ending_cozy="Even with help nearby, they decided the smartest clue to follow was rest, not hurry.",
        tags={"neighbors", "help"},
    ),
    "rolling_cart": Support(
        id="rolling_cart",
        label="rolling cart",
        phrase="a little rolling cart",
        power=2,
        method="the small wheels carried the weight over the floorboards",
        ending_outdoor="The job became quiet and easy, and the surprise of the case melted into relief.",
        ending_cozy="The cart could take only the lighter pieces, so the family changed the plan and kept the heavy part for later.",
        tags={"cart", "help"},
    ),
    "little_basket": Support(
        id="little_basket",
        label="little basket",
        phrase="a little reed basket",
        power=1,
        method="only tiny things could fit inside",
        ending_outdoor="Bit by bit, they still managed somehow.",
        ending_cozy="The basket was fine for napkins and crayons, but not for the real weight of the problem.",
        tags={"basket", "help"},
    ),
}

RESPONSES = {
    "clinic_call": Response(
        id="clinic_call",
        sense=3,
        action="call the clinic and ask for medical advice",
        qa_text="called the clinic and got medical help",
        tags={"doctor", "call_help"},
    ),
    "same_day_check": Response(
        id="same_day_check",
        sense=3,
        action="ask for a same-day check with a medical helper",
        qa_text="got a same-day medical check",
        tags={"doctor", "call_help"},
    ),
    "keep_lifting": Response(
        id="keep_lifting",
        sense=1,
        action="tell everyone to keep lifting and ignore the pain",
        qa_text="kept lifting even though it hurt",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Sam", "Leo", "Max", "Noah", "Eli"]

PATIENTS = {
    "father": ("Dad", "father"),
    "mother": ("Mom", "mother"),
    "grandpa": ("Grandpa", "grandpa"),
    "uncle": ("Uncle Ray", "uncle"),
}


@dataclass
class StoryParams:
    setting: str
    load: str
    helper: str
    support: str
    response: str
    detective_name: str
    detective_gender: str
    patient_role: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "hernia": [
        (
            "What is a hernia?",
            "A hernia is a problem where a weak spot in the body lets a bit inside push outward and make a bulge. A doctor should check it, especially if it hurts."
        )
    ],
    "doctor": [
        (
            "Why should a doctor check a painful lump or bulge?",
            "A doctor knows how to find out what the body needs and what should happen next. Getting help early can stop a small problem from getting worse."
        )
    ],
    "lifting": [
        (
            "Why can lifting something heavy hurt your body?",
            "Heavy lifting can strain muscles and put pressure on your middle. That is why people should stop and ask for help if something suddenly hurts."
        )
    ],
    "wagon": [
        (
            "What is a wagon good for?",
            "A wagon helps move heavy things by rolling them instead of carrying them. That makes the job easier on a person's body."
        )
    ],
    "neighbors": [
        (
            "Why is it good to ask neighbors or friends for help with a heavy job?",
            "More helpers can share the work so one person does not strain too hard. Asking for help is a smart choice, not a weak one."
        )
    ],
    "cart": [
        (
            "What does a rolling cart do?",
            "A rolling cart lets wheels carry the weight. Wheels can make a heavy job much safer and easier."
        )
    ],
    "call_help": [
        (
            "What should you do if someone suddenly has pain after lifting something heavy?",
            "Help them stop, sit or stand safely, and tell a grown-up or doctor right away. Do not ask them to keep lifting through the pain."
        )
    ],
}
KNOWLEDGE_ORDER = ["hernia", "doctor", "lifting", "wagon", "neighbors", "cart", "call_help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    patient = f["patient"]
    setting = f["setting"]
    load = f["load"]
    outcome = f["outcome"]
    ending = "outdoors" if outcome == "outdoor" else "with a cozy inside change of plan"
    return [
        f'Write a gentle detective story for a 3-to-5-year-old that includes the word "hernia".',
        f"Tell a surprise mystery where {detective.id}, a child detective, notices clues in {setting.label} after {patient.id} tries to lift {load.phrase}, and the answer turns out to be a hernia.",
        f"Write a child-facing detective-style story about a family mystery that ends {ending}, after the little detective helps the family get medical help and choose a safer plan.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    patient = f["patient"]
    helper = f["helper"]
    load = f["load"]
    support = f["support"]
    setting = f["setting"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child detective, and {patient.id}, who got hurt while lifting {load.phrase}. {helper.label} also helps explain the mystery."
        ),
        (
            "What was the mystery at the start?",
            f"The mystery was why {patient.id} suddenly stopped smiling and put a hand on {patient.pronoun('possessive')} middle while lifting {load.phrase}. {detective.id} could tell something had changed, but did not know the reason yet."
        ),
        (
            f"What clues did {detective.id} notice?",
            f"{detective.id} noticed {patient.id}'s careful steps, the hand on the tummy, and a small bump under the shirt. Those clues showed this was a body problem, not a missing-toy mystery."
        ),
        (
            "What was the surprise answer to the detective case?",
            f"The helper said the bump might be a hernia. That surprised {detective.id} because the mystery had a real medical answer instead of a sneaky culprit."
        ),
        (
            f"Why did they get medical help instead of waiting?",
            f"They got help because the pain started right after a heavy lift and there was a new bump to notice. Those clues made it important to stop and ask a medical helper what to do next."
        ),
    ]
    if outcome == "outdoor":
        qa.append(
            (
                "How did the family solve the problem after learning about the hernia?",
                f"They stopped asking {patient.id} to carry the heavy thing and used {support.phrase} instead. That let the family keep the day going while protecting {patient.pronoun('possessive')} body."
            )
        )
    else:
        qa.append(
            (
                "How did the family solve the problem after learning about the hernia?",
                f"They changed the plan and left the heavy job for later because {support.phrase} was not enough. The ending stayed happy because everyone chose safety instead of forcing the work."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"hernia", "lifting", "call_help"} | set(world.facts["response"].tags)
    tags |= set(world.facts["support"].tags)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden",
        load="soil_bag",
        helper="doctor_lee",
        support="neighbor_team",
        response="clinic_call",
        detective_name="Mia",
        detective_gender="girl",
        patient_role="father",
        seed=101,
    ),
    StoryParams(
        setting="porch",
        load="cooler",
        helper="nurse_omar",
        support="wagon",
        response="same_day_check",
        detective_name="Ben",
        detective_gender="boy",
        patient_role="mother",
        seed=102,
    ),
    StoryParams(
        setting="attic",
        load="trunk",
        helper="doctor_lee",
        support="rolling_cart",
        response="clinic_call",
        detective_name="Nora",
        detective_gender="girl",
        patient_role="grandpa",
        seed=103,
    ),
    StoryParams(
        setting="garden",
        load="book_box",
        helper="nurse_omar",
        support="little_basket",
        response="same_day_check",
        detective_name="Leo",
        detective_gender="boy",
        patient_role="uncle",
        seed=104,
    ),
]


def explain_rejection(load: Load) -> str:
    return (
        f"(No story: {load.phrase} is too light to make a believable lifting injury here. "
        f"Pick something heavier so the detective has a real mystery to solve.)"
    )


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    good = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it is too unsafe for this world "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {good}.)"
    )


ASP_RULES = r"""
reasonable_load(L) :- load(L), weight(L, W), W >= 2.
sensible_response(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, L, P) :- setting(S), support(P), reasonable_load(L).

outcome(outdoor) :- chosen_load(L), chosen_support(P), weight(L, W), power(P, Z), Z >= W.
outcome(cozy) :- chosen_load(L), chosen_support(P), weight(L, W), power(P, Z), Z < W.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for lid, load in LOADS.items():
        lines.append(asp.fact("load", lid))
        lines.append(asp.fact("weight", lid, load.weight))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for sid, support in SUPPORTS.items():
        lines.append(asp.fact("support", sid))
        lines.append(asp.fact("power", sid, support.power))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_response/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_response"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join(
        [
            asp.fact("chosen_load", params.load),
            asp.fact("chosen_support", params.support),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    c_valid, p_valid = set(asp_valid_combos()), set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {s}.")
            break
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification surface
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a little detective notices a medical mystery and helps the family choose a safer plan."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--load", choices=LOADS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--patient-role", choices=PATIENTS)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.load:
        load = LOADS[args.load]
        if not reasonable_load(load):
            raise StoryError(explain_rejection(load))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c
        for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.load is None or c[1] == args.load)
        and (args.support is None or c[2] == args.support)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, load_id, support_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    if args.detective_name:
        detective_name_value = args.detective_name
    else:
        detective_name_value = rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)
    patient_role = args.patient_role or rng.choice(sorted(PATIENTS))
    return StoryParams(
        setting=setting_id,
        load=load_id,
        helper=helper_id,
        support=support_id,
        response=response_id,
        detective_name=detective_name_value,
        detective_gender=detective_gender,
        patient_role=patient_role,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.load not in LOADS:
        raise StoryError(f"(Unknown load: {params.load})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.support not in SUPPORTS:
        raise StoryError(f"(Unknown support: {params.support})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.patient_role not in PATIENTS:
        raise StoryError(f"(Unknown patient role: {params.patient_role})")
    if not reasonable_load(LOADS[params.load]):
        raise StoryError(explain_rejection(LOADS[params.load]))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    patient_name, patient_type = PATIENTS[params.patient_role]
    world = tell(
        setting=SETTINGS[params.setting],
        load=LOADS[params.load],
        helper_cfg=HELPERS[params.helper],
        support=SUPPORTS[params.support],
        response=RESPONSES[params.response],
        detective_name_value=params.detective_name,
        detective_gender=params.detective_gender,
        patient_name=patient_name,
        patient_type=patient_type,
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
        print(asp_program("", "#show valid/3.\n#show sensible_response/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, load, support) combos:\n")
        for setting_id, load_id, support_id in combos:
            print(f"  {setting_id:8} {load_id:10} {support_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.detective_name}: {p.load} in {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
