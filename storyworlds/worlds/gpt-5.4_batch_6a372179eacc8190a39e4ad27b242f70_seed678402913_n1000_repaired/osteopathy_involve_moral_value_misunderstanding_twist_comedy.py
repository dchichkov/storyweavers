#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/osteopathy_involve_moral_value_misunderstanding_twist_comedy.py
===========================================================================================

A standalone story world about a child who hears the word "osteopathy",
misunderstands it in a funny way, and learns that asking honest questions is
better than guessing. The comedy comes from the misunderstanding; the moral
value is truthfulness and speaking up when confused; the twist is that the
child's silly preparation accidentally helps once the real situation is clear.

Run it
------
    python storyworlds/worlds/gpt-5.4/osteopathy_involve_moral_value_misunderstanding_twist_comedy.py
    python storyworlds/worlds/gpt-5.4/osteopathy_involve_moral_value_misunderstanding_twist_comedy.py --misunderstanding toast
    python storyworlds/worlds/gpt-5.4/osteopathy_involve_moral_value_misunderstanding_twist_comedy.py --helper confetti
    python storyworlds/worlds/gpt-5.4/osteopathy_involve_moral_value_misunderstanding_twist_comedy.py --all
    python storyworlds/worlds/gpt-5.4/osteopathy_involve_moral_value_misunderstanding_twist_comedy.py --verify
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
        female = {"girl", "woman", "mother", "grandma", "aunt"}
        male = {"boy", "man", "father", "grandpa", "uncle"}
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
            "grandpa": "grandpa",
            "grandma": "grandma",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.label or self.type)


@dataclass
class Patient:
    id: str
    kin_type: str
    ache: str
    ache_phrase: str
    careful_move: str
    seat_need: str
    safe_help: str
    gratitude: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    heard_as: str
    belief: str
    idea_line: str
    prop_word: str
    prop_phrase: str
    prep_line: str
    clinic_reveal: str
    harmless: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    kindness: int = 2
    action_text: str = ""
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


def _r_ache_needs_care(world: World) -> list[str]:
    patient = world.entities.get("patient")
    helper = world.entities.get("helper_item")
    if patient is None or helper is None:
        return []
    if patient.meters["ache"] < THRESHOLD:
        return []
    if helper.attrs.get("supports_area") != patient.attrs.get("area"):
        return []
    sig = ("comforted", patient.id, helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    patient.meters["comfort"] += 1
    patient.meters["strain"] = max(0.0, patient.meters["strain"] - 1)
    return ["__comfort__"]


def _r_honesty_clears_worry(world: World) -> list[str]:
    child = world.entities.get("child")
    adult = world.entities.get("guide")
    if child is None or adult is None:
        return []
    if child.memes["honesty"] < THRESHOLD:
        return []
    sig = ("relief", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    adult.memes["warmth"] += 1
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="ache_needs_care", tag="physical", apply=_r_ache_needs_care),
    Rule(name="honesty_clears_worry", tag="social", apply=_r_honesty_clears_worry),
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


def helper_fits(patient: Patient, helper: Helper) -> bool:
    return patient.ache in helper.helps and helper.kindness >= KINDNESS_MIN


def misunderstanding_works(mis: Misunderstanding) -> bool:
    return mis.harmless


def sensible_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.kindness >= KINDNESS_MIN]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for patient_id, patient in PATIENTS.items():
        for helper_id, helper in HELPERS.items():
            if helper_fits(patient, helper):
                combos.append((patient_id, helper_id))
    return combos


def predict_help(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    patient = sim.get("patient")
    return {
        "comforted": patient.meters["comfort"] >= THRESHOLD,
        "strain": patient.meters["strain"],
    }


def scene_setup(world: World, child: Entity, guide: Entity, patient: Entity, patient_cfg: Patient) -> None:
    child.memes["joy"] += 1
    guide.memes["care"] += 1
    patient.meters["ache"] += 1
    patient.meters["strain"] += 1
    world.say(
        f"On Saturday morning, {child.id} was helping {guide.label_word} by carrying a small bag to the clinic. "
        f"{patient.id} walked slowly beside them because {patient.pronoun('possessive')} {patient_cfg.ache_phrase} had been grumbling all week."
    )
    world.say(
        f'"We have an osteopathy visit," {guide.label_word} said, "and you can involve yourself by being my extra helper."'
    )


def mishear(world: World, child: Entity, mis: Misunderstanding) -> None:
    child.memes["confusion"] += 1
    child.memes["excitement"] += 1
    world.say(
        f"{child.id} heard the long word, blinked, and quietly turned it into {mis.heard_as} inside {child.pronoun('possessive')} head."
    )
    world.say(
        f"{mis.idea_line} {mis.prep_line}"
    )


def secret_prep(world: World, child: Entity, helper_ent: Entity, mis: Misunderstanding) -> None:
    child.memes["sneaky"] += 1
    helper_ent.meters["packed"] += 1
    world.say(
        f"Without telling anyone, {child.id} tucked {mis.prop_phrase} into the bag too, sure that every proper {mis.belief} ought to involve one."
    )


def arrival(world: World, child: Entity, guide: Entity, patient: Entity, mis: Misunderstanding) -> None:
    child.memes["worry"] += 1
    world.say(
        f"When they reached the clinic, there were no balloons, no toast plates, and no band. There was only a quiet room, a smiling osteopath, and a tall skeleton model in the corner."
    )
    world.say(
        f"{mis.clinic_reveal}"
    )
    world.say(
        f'{child.id} stopped so fast that {child.pronoun("possessive")} shoes squeaked. "Oh," {child.pronoun()} whispered.'
    )


def reveal_confusion(world: World, child: Entity, osteopath: Entity, mis: Misunderstanding) -> None:
    child.memes["honesty"] += 1
    child.memes["embarrassment"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The osteopath knelt until {osteopath.pronoun()} was eye to eye with {child.id}. "
        f'"You look as if a surprise jumped out of a cupboard," {osteopath.pronoun()} said kindly.'
    )
    world.say(
        f"{child.id} took a breath and told the truth. "
        f'"I thought osteopathy meant {mis.heard_as}, so I brought {mis.prop_phrase}," {child.pronoun()} admitted.'
    )


def kind_explanation(world: World, child: Entity, guide: Entity, patient: Entity, patient_cfg: Patient) -> None:
    guide.memes["warmth"] += 1
    patient.memes["amusement"] += 1
    world.say(
        f"Instead of scolding, the grown-ups smiled. The osteopath explained that osteopathy is a gentle kind of body care that helps sore muscles and stiff places move more comfortably."
    )
    world.say(
        f"{patient.id} chuckled so softly that even the skeleton seemed to grin. "
        f'"Good thing you asked," {patient.pronoun()} said. "Guessing can make very silly movies in your mind."'
    )


def twist_help(world: World, child: Entity, patient: Entity, helper_ent: Entity, helper_cfg: Helper, patient_cfg: Patient) -> None:
    helper_ent.attrs["supports_area"] = patient_cfg.ache
    helper_ent.meters["offered"] += 1
    patient.meters["ache"] += 0
    propagate(world, narrate=False)
    patient.memes["gratitude"] += 1
    child.memes["pride"] += 1
    world.say(
        f"Then came the funny twist. {patient.id} really did need help with {patient_cfg.safe_help}, and {child.id}'s {helper_cfg.label} turned out to be perfect."
    )
    world.say(
        f"{child.id} {helper_cfg.action_text}. {patient.id} smiled and said, "
        f'"{patient_cfg.gratitude}"'
    )


def ending(world: World, child: Entity, guide: Entity, patient: Entity, mis: Misunderstanding, helper_cfg: Helper) -> None:
    child.memes["lesson"] += 1
    child.memes["joy"] += 1
    guide.memes["pride"] += 1
    world.say(
        f"On the way home, {child.id} laughed at {child.pronoun('object')}self first. "
        f'"Next time I hear a giant word, I will ask what it means before I pack a surprise," {child.pronoun()} said.'
    )
    world.say(
        f'{guide.label_word.capitalize()} squeezed {child.pronoun("possessive")} hand. "That is the wise part," {guide.pronoun()} said. "And helping kindly is still a wonderful thing to involve yourself in."'
    )
    world.say(
        f"In the back seat, {patient.id} rested easier with the {helper_cfg.label} nearby, and {child.id} decided that honest questions were much less tiring than secret guesses."
    )


def tell(
    patient_cfg: Patient,
    mis: Misunderstanding,
    helper_cfg: Helper,
    *,
    child_name: str = "Milo",
    child_type: str = "boy",
    guide_type: str = "mother",
    osteopath_name: str = "Dr. June",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    guide = world.add(Entity(id="Guide", kind="character", type=guide_type, role="guide", label="the parent"))
    patient = world.add(
        Entity(
            id=patient_cfg.kin_type.capitalize() if patient_cfg.kin_type not in {"mom", "dad"} else patient_cfg.kin_type.capitalize(),
            kind="character",
            type=patient_cfg.kin_type,
            role="patient",
            attrs={"area": patient_cfg.ache},
        )
    )
    osteopath = world.add(Entity(id=osteopath_name, kind="character", type="woman", role="osteopath"))
    helper_ent = world.add(
        Entity(
            id="helper_item",
            kind="thing",
            type="helper",
            label=helper_cfg.label,
            phrase=helper_cfg.phrase,
            attrs={"supports_area": ""},
            tags=set(helper_cfg.tags),
        )
    )

    scene_setup(world, child, guide, patient, patient_cfg)
    world.para()
    mishear(world, child, mis)
    secret_prep(world, child, helper_ent, mis)
    world.para()
    arrival(world, child, guide, patient, mis)
    reveal_confusion(world, child, osteopath, mis)
    kind_explanation(world, child, guide, patient, patient_cfg)
    world.para()
    twist_help(world, child, patient, helper_ent, helper_cfg, patient_cfg)
    ending(world, child, guide, patient, mis, helper_cfg)

    predicted = predict_help(world)
    world.facts.update(
        child=child,
        guide=guide,
        patient=patient,
        osteopath=osteopath,
        helper_item=helper_ent,
        patient_cfg=patient_cfg,
        misunderstanding=mis,
        helper_cfg=helper_cfg,
        predicted_comfort=predicted["comforted"],
        patient_better=patient.meters["comfort"] >= THRESHOLD,
        moral="ask when you do not understand, and help honestly",
    )
    return world


@dataclass
class StoryParams:
    patient: str
    misunderstanding: str
    helper: str
    child_name: str
    child_type: str
    guide_type: str
    osteopath_name: str
    seed: Optional[int] = None


PATIENTS = {
    "grandpa_back": Patient(
        id="grandpa_back",
        kin_type="grandpa",
        ache="back",
        ache_phrase="back",
        careful_move="sat down carefully",
        seat_need="a gentle seat and a little support",
        safe_help="supporting his back in the chair",
        gratitude="That little cushion feels better than your giant guess.",
        tags={"back", "clinic", "family"},
    ),
    "mom_neck": Patient(
        id="mom_neck",
        kin_type="mother",
        ache="neck",
        ache_phrase="neck",
        careful_move="turned her head slowly",
        seat_need="a quiet moment and something soft",
        safe_help="supporting her neck while she waited",
        gratitude="This rolled scarf is exactly what my stiff neck wanted.",
        tags={"neck", "clinic", "family"},
    ),
    "aunt_shoulder": Patient(
        id="aunt_shoulder",
        kin_type="aunt",
        ache="shoulder",
        ache_phrase="shoulder",
        careful_move="lifted one arm carefully",
        seat_need="a gentle rest and a soft prop",
        safe_help="resting her shoulder while she filled in a form",
        gratitude="You brought the silliest bag and the handiest support.",
        tags={"shoulder", "clinic", "family"},
    ),
}

MISUNDERSTANDINGS = {
    "party": Misunderstanding(
        id="party",
        heard_as="a bone party",
        belief="bone party",
        idea_line="To {name}, that sounded like a party for bones, which seemed both unusual and important.",
        prop_word="paper crown",
        prop_phrase="a paper crown and two folded invitations",
        prep_line="At home, {name} had decorated the invitations with tiny dancing skeletons.",
        clinic_reveal="The skeleton was not the host. It was only a model, standing very still and not wearing a party hat.",
        harmless=True,
        tags={"mishearing", "skeleton", "party"},
    ),
    "toast": Misunderstanding(
        id="toast",
        heard_as="a toast party",
        belief="toast party",
        idea_line="To {name}, it sounded like someone had said toast-party, and toast parties surely needed good manners and jam.",
        prop_word="napkin",
        prop_phrase="a neatly wrapped slice of toast and a bright napkin",
        prep_line="At home, {name} had whispered, \"No one should celebrate on an empty tummy.\"",
        clinic_reveal="The waiting room smelled like soap, not breakfast. The skeleton was not holding a plate.",
        harmless=True,
        tags={"mishearing", "toast", "food"},
    ),
    "band": Misunderstanding(
        id="band",
        heard_as="a drum-and-bone show",
        belief="drum-and-bone show",
        idea_line="To {name}, the word sounded grand and musical, the sort of thing that should include a tiny parade.",
        prop_word="tambourine",
        prop_phrase="a tiny tambourine with one missing jingle",
        prep_line="At home, {name} had practiced one careful shake and decided that was enough rehearsal.",
        clinic_reveal="Nobody was tuning instruments. Even the skeleton had no drumsticks.",
        harmless=True,
        tags={"mishearing", "music", "parade"},
    ),
}

HELPERS = {
    "cushion": Helper(
        id="cushion",
        label="cushion",
        phrase="a small striped cushion",
        helps={"back", "shoulder"},
        kindness=3,
        action_text="slid the small striped cushion behind the sore spot just as the osteopath suggested",
        qa_text="used a small cushion to support the sore place while they waited",
        tags={"cushion", "support"},
    ),
    "scarf": Helper(
        id="scarf",
        label="scarf",
        phrase="a soft rolled scarf",
        helps={"neck", "shoulder"},
        kindness=3,
        action_text="rolled the soft scarf into a careful loop and tucked it where it could hold the stiff place gently",
        qa_text="rolled a soft scarf to support the stiff place",
        tags={"scarf", "support"},
    ),
    "water": Helper(
        id="water",
        label="water bottle",
        phrase="a cool water bottle",
        helps={"back", "neck", "shoulder"},
        kindness=2,
        action_text="passed over the water bottle and waited quietly while the grown-up took a slow sip and relaxed",
        qa_text="offered water and waited quietly",
        tags={"water", "kindness"},
    ),
    "confetti": Helper(
        id="confetti",
        label="confetti",
        phrase="a fistful of glittery confetti",
        helps=set(),
        kindness=0,
        action_text="never got to use the confetti because the clinic floor did not need sparkles",
        qa_text="brought confetti, which was not helpful in a clinic",
        tags={"confetti"},
    ),
}

GIRL_NAMES = ["Lina", "Mia", "Nora", "Tess", "Ruby", "June", "Ava", "Ella"]
BOY_NAMES = ["Milo", "Ben", "Theo", "Sam", "Leo", "Finn", "Max", "Owen"]
OSTEOPATH_NAMES = ["Dr. June", "Dr. Lee", "Dr. Rosa", "Dr. Arun"]


def valid_misunderstandings() -> list[str]:
    return sorted(mid for mid, mis in MISUNDERSTANDINGS.items() if misunderstanding_works(mis))


def materialize(text: str, name: str) -> str:
    return text.replace("{name}", name)


def _mis_copy(mis: Misunderstanding, name: str) -> Misunderstanding:
    return Misunderstanding(
        id=mis.id,
        heard_as=mis.heard_as,
        belief=mis.belief,
        idea_line=materialize(mis.idea_line, name),
        prop_word=mis.prop_word,
        prop_phrase=mis.prop_phrase,
        prep_line=materialize(mis.prep_line, name),
        clinic_reveal=mis.clinic_reveal,
        harmless=mis.harmless,
        tags=set(mis.tags),
    )


def pair_noun(patient: Entity) -> str:
    return {
        "grandpa": "grandpa",
        "mother": "mom",
        "aunt": "aunt",
    }.get(patient.type, patient.label_word)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    patient = f["patient"]
    mis = f["misunderstanding"]
    helper = f["helper_cfg"]
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the word "osteopathy" and the word "involve".',
        f"Tell a comedy where {child.id} misunderstands an osteopathy visit as {mis.heard_as}, then learns to ask what words mean instead of guessing.",
        f"Write a gentle moral story where a child brings {helper.phrase} for the wrong reason, but it becomes useful in a twist when {pair_noun(patient)} needs help.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    patient = f["patient"]
    mis = f["misunderstanding"]
    helper = f["helper_cfg"]
    patient_cfg = f["patient_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who goes to an osteopathy visit with {guide.label_word} and {pair_noun(patient)}. "
            f"The story follows {child.pronoun('object')} from a funny misunderstanding to an honest question."
        ),
        (
            f"What misunderstanding did {child.id} have?",
            f"{child.id} heard the word osteopathy and imagined {mis.heard_as}. "
            f"That is why {child.pronoun()} secretly packed {mis.prop_phrase} before the trip."
        ),
        (
            "Why was the clinic funny to the child at first?",
            f"The child expected something silly, but the clinic was calm and serious, with only a skeleton model in the corner. "
            f"The difference between the guess and the real place made the scene funny."
        ),
        (
            f"What good choice did {child.id} make when {child.pronoun()} realized the mistake?",
            f"{child.id} told the truth instead of hiding the mistake. "
            f"That honest moment mattered because the grown-ups could explain what osteopathy really was and help {child.pronoun('object')} feel better."
        ),
        (
            "What was the twist?",
            f"The twist was that {child.id}'s {helper.label} was useful after all. "
            f"It helped with {patient_cfg.safe_help}, even though {child.pronoun()} had packed it for the wrong reason."
        ),
        (
            "What lesson did the story teach?",
            f"It taught that asking questions is wiser than guessing, and kind help still matters. "
            f"Being honest turned an embarrassing mistake into a helpful moment."
        ),
    ]
    return qa


KNOWLEDGE = {
    "osteopathy": [
        (
            "What is osteopathy?",
            "Osteopathy is a kind of gentle health care where a trained practitioner helps sore or stiff parts of the body move more comfortably."
        )
    ],
    "mishearing": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone gets the wrong idea about what they heard or saw. Asking a question can clear it up."
        )
    ],
    "honesty": [
        (
            "Why is it good to tell the truth when you are confused?",
            "Telling the truth helps other people explain things clearly and help you. It also stops a wrong guess from growing into a bigger problem."
        )
    ],
    "skeleton": [
        (
            "Why do some clinics have a skeleton model?",
            "A skeleton model helps doctors and therapists show where bones and joints are. It is for learning, not for having a party."
        )
    ],
    "cushion": [
        (
            "What can a cushion do for a sore back or shoulder?",
            "A cushion can support a sore place and make sitting feel gentler. Soft support can help someone feel more comfortable."
        )
    ],
    "scarf": [
        (
            "How can a scarf help someone feel comfortable?",
            "A soft scarf can be rolled or folded to support a stiff place gently. It can also help someone stay warm and relaxed."
        )
    ],
    "water": [
        (
            "Why can a sip of water help when someone feels tense?",
            "A slow sip of water can help a person pause, breathe, and relax. Quiet care can make a waiting room feel easier."
        )
    ],
}
KNOWLEDGE_ORDER = ["osteopathy", "mishearing", "honesty", "skeleton", "cushion", "scarf", "water"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"osteopathy", "mishearing", "honesty"} | set(f["misunderstanding"].tags) | set(f["helper_cfg"].tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        patient="grandpa_back",
        misunderstanding="party",
        helper="cushion",
        child_name="Milo",
        child_type="boy",
        guide_type="mother",
        osteopath_name="Dr. June",
    ),
    StoryParams(
        patient="mom_neck",
        misunderstanding="toast",
        helper="scarf",
        child_name="Lina",
        child_type="girl",
        guide_type="father",
        osteopath_name="Dr. Rosa",
    ),
    StoryParams(
        patient="aunt_shoulder",
        misunderstanding="band",
        helper="water",
        child_name="Theo",
        child_type="boy",
        guide_type="mother",
        osteopath_name="Dr. Lee",
    ),
]


def explain_patient_helper(patient_id: str, helper_id: str) -> str:
    patient = PATIENTS[patient_id]
    helper = HELPERS[helper_id]
    if helper.kindness < KINDNESS_MIN:
        return (
            f"(No story: {helper.label} is too messy or unkind for a quiet clinic. "
            f"Choose a calmer helper like cushion / scarf / water.)"
        )
    return (
        f"(No story: {helper.label} does not sensibly help with a sore {patient.ache}. "
        f"Pick a helper that can support that area or make waiting gentler.)"
    )


def explain_misunderstanding(mid: str) -> str:
    mis = MISUNDERSTANDINGS[mid]
    return f"(No story: the misunderstanding '{mis.id}' is not harmless enough for this gentle comedy.)"


ASP_RULES = r"""
kind_helper(H) :- helper(H), kindness(H, K), kindness_min(M), K >= M.
fits(P, H) :- patient(P), kind_helper(H), ache(P, A), helps(H, A).
valid(P, H) :- patient(P), helper(H), fits(P, H).

usable_misunderstanding(M) :- misunderstanding(M), harmless(M).

% Any chosen story is reasonable only if the misunderstanding is harmless
% and the helper fits the patient's sore area.
reasonable_story(P, M, H) :- chosen_patient(P), chosen_misunderstanding(M), chosen_helper(H),
                             valid(P, H), usable_misunderstanding(M).

% Outcome for this world is always a good ending once the story is reasonable:
% the child tells the truth, the misunderstanding is cleared, and the helper
% turns out useful.
outcome(helpful_twist) :- reasonable_story(_, _, _).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("kindness_min", KINDNESS_MIN))
    for patient_id, patient in PATIENTS.items():
        lines.append(asp.fact("patient", patient_id))
        lines.append(asp.fact("ache", patient_id, patient.ache))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("kindness", helper_id, helper.kindness))
        for area in sorted(helper.helps):
            lines.append(asp.fact("helps", helper_id, area))
    for mid, mis in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", mid))
        if mis.harmless:
            lines.append(asp.fact("harmless", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_patient", params.patient),
            asp.fact("chosen_misunderstanding", params.misunderstanding),
            asp.fact("chosen_helper", params.helper),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if not misunderstanding_works(MISUNDERSTANDINGS[params.misunderstanding]):
        return "invalid"
    if not helper_fits(PATIENTS[params.patient], HELPERS[params.helper]):
        return "invalid"
    return "helpful_twist"


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

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story in smoke test")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Funny osteopathy misunderstanding world. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--patient", choices=PATIENTS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--guide-type", choices=["mother", "father"])
    ap.add_argument("--child-name")
    ap.add_argument("--osteopath-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid patient/helper combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.misunderstanding and not misunderstanding_works(MISUNDERSTANDINGS[args.misunderstanding]):
        raise StoryError(explain_misunderstanding(args.misunderstanding))
    if args.patient and args.helper:
        if not helper_fits(PATIENTS[args.patient], HELPERS[args.helper]):
            raise StoryError(explain_patient_helper(args.patient, args.helper))
    if args.helper and HELPERS[args.helper].kindness < KINDNESS_MIN:
        if args.patient:
            raise StoryError(explain_patient_helper(args.patient, args.helper))
        raise StoryError(
            "(No story: that helper is too disruptive for this gentle clinic comedy. Try cushion, scarf, or water.)"
        )

    combos = [
        c for c in valid_combos()
        if (args.patient is None or c[0] == args.patient)
        and (args.helper is None or c[1] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    patient_id, helper_id = rng.choice(sorted(combos))
    misunderstanding = args.misunderstanding or rng.choice(valid_misunderstandings())
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    guide_type = args.guide_type or rng.choice(["mother", "father"])
    osteopath_name = args.osteopath_name or rng.choice(OSTEOPATH_NAMES)

    return StoryParams(
        patient=patient_id,
        misunderstanding=misunderstanding,
        helper=helper_id,
        child_name=child_name,
        child_type=child_type,
        guide_type=guide_type,
        osteopath_name=osteopath_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.patient not in PATIENTS:
        raise StoryError(f"(Unknown patient '{params.patient}'.)")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError(f"(Unknown misunderstanding '{params.misunderstanding}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}'.)")

    patient_cfg = PATIENTS[params.patient]
    mis = MISUNDERSTANDINGS[params.misunderstanding]
    helper_cfg = HELPERS[params.helper]

    if not misunderstanding_works(mis):
        raise StoryError(explain_misunderstanding(params.misunderstanding))
    if not helper_fits(patient_cfg, helper_cfg):
        raise StoryError(explain_patient_helper(params.patient, params.helper))

    world = tell(
        patient_cfg=patient_cfg,
        mis=_mis_copy(mis, params.child_name),
        helper_cfg=helper_cfg,
        child_name=params.child_name,
        child_type=params.child_type,
        guide_type=params.guide_type,
        osteopath_name=params.osteopath_name,
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
        print(asp_program("", "#show valid/2.\n#show usable_misunderstanding/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (patient, helper) combos:\n")
        for patient_id, helper_id in combos:
            print(f"  {patient_id:14} {helper_id}")
        print("\nusable misunderstandings:")
        for mid in valid_misunderstandings():
            print(f"  {mid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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
            header = f"### {p.child_name}: {p.misunderstanding} + {p.helper} for {p.patient}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
