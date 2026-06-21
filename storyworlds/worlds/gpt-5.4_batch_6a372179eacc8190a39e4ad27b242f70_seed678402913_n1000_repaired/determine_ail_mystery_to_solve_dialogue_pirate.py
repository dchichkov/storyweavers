#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/determine_ail_mystery_to_solve_dialogue_pirate.py
============================================================================

A standalone storyworld for a tiny pirate mystery: two young pirates notice that
their little shipmate does not seem right, talk through clues, determine what
might ail the friend, and fix the problem in a simple child-facing way.

The domain is intentionally narrow. Each story is a complete miniature tale:

- a pirate-play setup,
- a small mystery about what may ail a shipmate or pet,
- dialogue-driven clue gathering,
- a sensible fix that matches the cause,
- and an ending image that proves the crew learned to look, listen, and help.

Run it
------
    python storyworlds/worlds/gpt-5.4/determine_ail_mystery_to_solve_dialogue_pirate.py
    python storyworlds/worlds/gpt-5.4/determine_ail_mystery_to_solve_dialogue_pirate.py --subject parrot --cause thirst
    python storyworlds/worlds/gpt-5.4/determine_ail_mystery_to_solve_dialogue_pirate.py --symptom limping --cause thirst
    python storyworlds/worlds/gpt-5.4/determine_ail_mystery_to_solve_dialogue_pirate.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/determine_ail_mystery_to_solve_dialogue_pirate.py --all
    python storyworlds/worlds/gpt-5.4/determine_ail_mystery_to_solve_dialogue_pirate.py --verify
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
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        animal = {"parrot", "monkey", "turtle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class SubjectCfg:
    id: str
    label: str
    phrase: str
    type: str
    perch: str
    move: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SymptomCfg:
    id: str
    label: str
    line: str
    question: str
    clue_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CauseCfg:
    id: str
    label: str
    needs: str
    symptom_ids: set[str]
    clue: str
    inspect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RemedyCfg:
    id: str
    label: str
    fixes: str
    action: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class DeckCfg:
    id: str
    scene: str
    rig: str
    mystery_place: str
    ending: str
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


def _r_ail_causes_worry(world: World) -> list[str]:
    subject = world.get("subject")
    if subject.meters["ailing"] < THRESHOLD:
        return []
    sig = ("ail_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("captain", "mate"):
        world.get(eid).memes["worry"] += 1
    return ["__worry__"]


def _r_help_brings_relief(world: World) -> list[str]:
    subject = world.get("subject")
    if subject.meters["comfort"] < THRESHOLD:
        return []
    sig = ("comfort_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("captain", "mate"):
        world.get(eid).memes["relief"] += 1
        world.get(eid).memes["joy"] += 1
    subject.meters["ailing"] = 0.0
    return ["__relief__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="ail_causes_worry", tag="emotional", apply=_r_ail_causes_worry),
    Rule(name="help_brings_relief", tag="emotional", apply=_r_help_brings_relief),
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


SUBJECTS = {
    "parrot": SubjectCfg(
        id="parrot",
        label="parrot",
        phrase="their green parrot, Pickle",
        type="parrot",
        perch="on the ship's rail",
        move="ruffled its feathers",
        tags={"parrot"},
    ),
    "monkey": SubjectCfg(
        id="monkey",
        label="monkey",
        phrase="their small monkey, Buttons",
        type="monkey",
        perch="by the rope ladder",
        move="curled its tail tight",
        tags={"monkey"},
    ),
    "turtle": SubjectCfg(
        id="turtle",
        label="turtle",
        phrase="their little turtle, Shellby",
        type="turtle",
        perch="beside the treasure chest",
        move="pulled its head halfway in",
        tags={"turtle"},
    ),
}

SYMPTOMS = {
    "quiet": SymptomCfg(
        id="quiet",
        label="too quiet",
        line="did not chirp or chatter at all",
        question="Why is our little shipmate so quiet?",
        clue_text="It was usually much noisier during pirate games.",
        tags={"quiet"},
    ),
    "limping": SymptomCfg(
        id="limping",
        label="limping",
        line="took tiny uneven steps and stopped after each one",
        question="Why is our little shipmate limping?",
        clue_text="Something seemed to bother one foot.",
        tags={"limping"},
    ),
    "droopy": SymptomCfg(
        id="droopy",
        label="droopy",
        line="looked droopy and kept its head low",
        question="Why does our little shipmate look so droopy?",
        clue_text="It did not look ready for games at all.",
        tags={"droopy"},
    ),
}

CAUSES = {
    "thirst": CauseCfg(
        id="thirst",
        label="thirst",
        needs="a drink of fresh water",
        symptom_ids={"quiet", "droopy"},
        clue="The water cup by the mast was empty.",
        inspect="They checked the little cup and found it dry.",
        tags={"thirst", "water"},
    ),
    "splinter": CauseCfg(
        id="splinter",
        label="a splinter",
        needs="a tiny splinter taken out",
        symptom_ids={"limping", "quiet"},
        clue="A tiny wood splinter was stuck near one foot.",
        inspect="They looked closely at the foot and saw a sharp splinter there.",
        tags={"splinter"},
    ),
    "heat": CauseCfg(
        id="heat",
        label="too much hot sun",
        needs="shade and a cool rest",
        symptom_ids={"droopy", "quiet"},
        clue="The deck in the noon sun felt hot, and the little shipmate was blinking slowly.",
        inspect="They touched the deck boards and found them warm from the sun.",
        tags={"heat", "shade"},
    ),
}

REMEDIES = {
    "water": RemedyCfg(
        id="water",
        label="fresh water",
        fixes="thirst",
        action="filled the little cup with cool water and held it steady",
        result="After a long drink, the little shipmate lifted its head again",
        tags={"water"},
    ),
    "tweezer": RemedyCfg(
        id="tweezer",
        label="careful tweezers",
        fixes="splinter",
        action="used a tiny pair of tweezers and pulled the splinter out very gently",
        result="Once the splinter was gone, the little shipmate tested the foot and stood much easier",
        tags={"tweezer", "splinter"},
    ),
    "shade": RemedyCfg(
        id="shade",
        label="a shady cloth tent",
        fixes="heat",
        action="spread a striped cloth to make a cool patch of shade",
        result="In the shade, the little shipmate blinked, stretched, and looked brighter",
        tags={"shade"},
    ),
}

DECKS = {
    "backyard_ship": DeckCfg(
        id="backyard_ship",
        scene="a pirate ship in the backyard",
        rig="A washing basket was the treasure chest, a blue sheet was the sea, and a broom stood tall like a mast.",
        mystery_place="near the mast",
        ending="sailed toward the pretend sunset with lighter hearts",
        tags={"pirate"},
    ),
    "attic_ship": DeckCfg(
        id="attic_ship",
        scene="a pirate ship under the attic beams",
        rig="An old trunk was the treasure chest, a striped blanket was the sea, and a cardboard wheel creaked softly on a chair.",
        mystery_place="under the little mast",
        ending="set their course for the make-believe moon",
        tags={"pirate"},
    ),
    "dock_ship": DeckCfg(
        id="dock_ship",
        scene="a pirate ship beside the little town dock",
        rig="A crate was the treasure chest, a coil of rope made a neat circle by the rail, and the boat bumped the wood with gentle knocks.",
        mystery_place="by the rail",
        ending="drifted home while the water flashed gold",
        tags={"pirate"},
    ),
}

CAPTAIN_NAMES = ["Lina", "Mira", "Ava", "Nora", "Lucy", "Maya", "Rose", "Ella", "Tom", "Finn", "Leo", "Sam"]
MATE_NAMES = ["Ben", "Jack", "Theo", "Noah", "Eli", "Mia", "Zoe", "Anna", "Lily", "Max", "Tess", "June"]
TRAITS = ["careful", "curious", "steady", "kind", "thoughtful", "clever"]


def valid_combo(subject_id: str, symptom_id: str, cause_id: str, remedy_id: str) -> bool:
    subject_ok = subject_id in SUBJECTS
    symptom_ok = symptom_id in SYMPTOMS
    cause_ok = cause_id in CAUSES
    remedy_ok = remedy_id in REMEDIES
    if not (subject_ok and symptom_ok and cause_ok and remedy_ok):
        return False
    cause = CAUSES[cause_id]
    remedy = REMEDIES[remedy_id]
    return symptom_id in cause.symptom_ids and remedy.fixes == cause_id


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for subject_id in SUBJECTS:
        for symptom_id in SYMPTOMS:
            for cause_id in CAUSES:
                for remedy_id in REMEDIES:
                    if valid_combo(subject_id, symptom_id, cause_id, remedy_id):
                        combos.append((subject_id, symptom_id, cause_id, remedy_id))
    return combos


def explain_rejection(symptom_id: str, cause_id: str, remedy_id: str) -> str:
    cause = CAUSES.get(cause_id)
    remedy = REMEDIES.get(remedy_id)
    if cause is not None and symptom_id not in cause.symptom_ids:
        return (
            f"(No story: the symptom '{symptom_id}' does not fit the cause '{cause_id}' "
            f"in this world. The crew must have honest clues to determine what may ail the little shipmate.)"
        )
    if cause is not None and remedy is not None and remedy.fixes != cause_id:
        return (
            f"(No story: the remedy '{remedy_id}' does not fix the cause '{cause_id}'. "
            f"The solution must actually help after the pirates determine the ail.)"
        )
    return "(No story: this combination does not form a sensible mystery.)"


@dataclass
class StoryParams:
    deck: str
    subject: str
    symptom: str
    cause: str
    remedy: str
    captain_name: str
    captain_gender: str
    mate_name: str
    mate_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def introduce(world: World, deck: DeckCfg, captain: Entity, mate: Entity, subject: Entity) -> None:
    captain.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"One bright afternoon, Captain {captain.id} and Mate {mate.id} turned the place around them into {deck.scene}. {deck.rig}"
    )
    world.say(
        f'With a stomp and a grin, {captain.id} cried, "Crew, set sail!"'
    )
    world.say(
        f"{subject.attrs['phrase'].capitalize()} perched {subject.attrs['perch']} and watched the game begin."
    )


def ail_appears(world: World, subject: Entity, symptom: SymptomCfg) -> None:
    subject.meters["ailing"] += 1
    subject.meters["symptom"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But soon the crew noticed something odd. {subject.label.capitalize()} {symptom.line}. {symptom.clue_text}"
    )


def wonder(world: World, captain: Entity, mate: Entity, symptom: SymptomCfg) -> None:
    captain.memes["curiosity"] += 1
    mate.memes["curiosity"] += 1
    world.say(
        f'"{symptom.question}" {mate.id} whispered.'
    )
    world.say(
        f'"Let us determine what may ail our friend," {captain.id} said. "Real pirates look before they guess."'
    )


def inspect(world: World, captain: Entity, mate: Entity, cause: CauseCfg) -> None:
    world.say(
        f"{captain.id} knelt down, and {mate.id} peered close. {cause.inspect}"
    )
    world.say(
        f'"Ahoy," said {mate.id}. "{cause.clue}"'
    )


def determine_cause(world: World, captain: Entity, mate: Entity, subject: Entity, cause: CauseCfg) -> None:
    world.facts["determined"] = cause.id
    subject.meters["understood"] += 1
    captain.memes["confidence"] += 1
    mate.memes["confidence"] += 1
    world.say(
        f'"Then that is it," said {captain.id}. "It is not treasure trouble at all. {subject.label.capitalize()} needs {cause.needs}."'
    )
    world.say(
        f'"So that is what can ail a small deck mate," said {mate.id}.'
    )


def help_subject(world: World, captain: Entity, mate: Entity, remedy: RemedyCfg) -> None:
    subject = world.get("subject")
    subject.meters["comfort"] += 1
    subject.meters["helped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Very gently, the two pirates {remedy.action}."
    )
    world.say(
        f"{remedy.result}."
    )


def ending(world: World, deck: DeckCfg, captain: Entity, mate: Entity, subject: Entity) -> None:
    captain.memes["care"] += 1
    mate.memes["care"] += 1
    subject.memes["trust"] += 1
    world.say(
        f'Soon {subject.label} was bright-eyed again. "{subject.label.capitalize()} is ready to sail," laughed {mate.id}.'
    )
    world.say(
        f'"And now we know to listen when a crew member seems strange," said {captain.id}.'
    )
    world.say(
        f"With the mystery solved, the little crew {deck.ending}, while {subject.label} {subject.attrs['move']} as if to say thank you."
    )


def tell(
    deck: DeckCfg,
    subject_cfg: SubjectCfg,
    symptom_cfg: SymptomCfg,
    cause_cfg: CauseCfg,
    remedy_cfg: RemedyCfg,
    captain_name: str,
    captain_gender: str,
    mate_name: str,
    mate_gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    captain = world.add(
        Entity(
            id=captain_name,
            kind="character",
            type=captain_gender,
            label=captain_name,
            role="captain",
            attrs={"trait": trait},
        )
    )
    mate = world.add(
        Entity(
            id=mate_name,
            kind="character",
            type=mate_gender,
            label=mate_name,
            role="mate",
            attrs={"trait": "observant"},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    subject = world.add(
        Entity(
            id="subject",
            kind="character",
            type=subject_cfg.type,
            label=subject_cfg.label,
            phrase=subject_cfg.phrase,
            role="subject",
            attrs={"phrase": subject_cfg.phrase, "perch": subject_cfg.perch, "move": subject_cfg.move},
            tags=set(subject_cfg.tags),
        )
    )

    introduce(world, deck, captain, mate, subject)

    world.para()
    ail_appears(world, subject, symptom_cfg)
    wonder(world, captain, mate, symptom_cfg)

    world.para()
    inspect(world, captain, mate, cause_cfg)
    determine_cause(world, captain, mate, subject, cause_cfg)

    world.para()
    help_subject(world, captain, mate, remedy_cfg)
    ending(world, deck, captain, mate, subject)

    world.facts.update(
        deck=deck,
        captain=captain,
        mate=mate,
        parent=parent,
        subject=subject,
        subject_cfg=subject_cfg,
        symptom=symptom_cfg,
        cause=cause_cfg,
        remedy=remedy_cfg,
        solved=subject.meters["helped"] >= THRESHOLD,
        ail_cleared=subject.meters["ailing"] < THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "parrot": [
        (
            "What is a parrot?",
            "A parrot is a bird with a curved beak and strong feet. Many parrots are noisy and like to perch high up."
        )
    ],
    "monkey": [
        (
            "What is a monkey?",
            "A monkey is an animal that can climb, grip, and move quickly. Many monkeys use their tails and hands to balance."
        )
    ],
    "turtle": [
        (
            "What is a turtle?",
            "A turtle is an animal with a hard shell. It can pull its head and legs in when it wants to feel safe."
        )
    ],
    "thirst": [
        (
            "What does thirst mean?",
            "Thirst means a body needs water. Drinking helps the body feel better and work properly again."
        )
    ],
    "splinter": [
        (
            "What is a splinter?",
            "A splinter is a tiny sharp piece of wood that gets stuck in skin. It can hurt, especially when you try to walk or hold something."
        )
    ],
    "heat": [
        (
            "Why can hot sun make someone droopy?",
            "Too much heat can make a body tired and slow. Shade and a cool rest can help."
        )
    ],
    "water": [
        (
            "Why does fresh water help when someone is thirsty?",
            "Water helps the body replace what it needs. After a drink, a thirsty person or animal often feels stronger."
        )
    ],
    "shade": [
        (
            "What does shade do on a hot day?",
            "Shade blocks the strong sun. It helps a body cool down and rest."
        )
    ],
    "tweezer": [
        (
            "What are tweezers for?",
            "Tweezers are small tools for gripping tiny things. A grown-up can use them carefully to remove a splinter."
        )
    ],
}
KNOWLEDGE_ORDER = ["parrot", "monkey", "turtle", "thirst", "splinter", "heat", "water", "shade", "tweezer"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    subject = f["subject_cfg"]
    cause = f["cause"]
    symptom = f["symptom"]
    return [
        f'Write a pirate tale for a 3-to-5-year-old that includes the words "determine" and "ail" and has a small mystery to solve through dialogue.',
        f"Tell a gentle pirate story where Captain {captain.id} and Mate {mate.id} notice that a {subject.label} seems {symptom.label}, determine what may ail it, and help it feel better.",
        f'Write a child-facing story with plenty of dialogue where young pirates solve the mystery of {cause.label} and end with their little crew safe and cheerful.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    subject = f["subject_cfg"]
    symptom = f["symptom"]
    cause = f["cause"]
    remedy = f["remedy"]
    deck = f["deck"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Captain {captain.id}, Mate {mate.id}, and their little {subject.label}. They were playing pirates when they noticed something was wrong."
        ),
        (
            "What was the mystery to solve?",
            f"The mystery was why the {subject.label} seemed {symptom.label}. The two children wanted to determine what might ail their little shipmate."
        ),
        (
            f"What clue helped {captain.id} and {mate.id} determine the problem?",
            f"They looked closely instead of guessing and found a clear clue: {cause.clue} That clue pointed them to {cause.label}."
        ),
        (
            f"How did the pirates help the {subject.label}?",
            f"They {remedy.action}. That helped because {remedy.label} matches the real problem, which was {cause.label}."
        ),
    ]
    if f.get("solved"):
        qa.append(
            (
                "How did the story end?",
                f"The mystery was solved, the {subject.label} felt better, and the crew went back to their pirate game. The ending image shows them on {deck.scene}, calmer and kinder because they had listened carefully."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set()
    f = world.facts
    tags |= set(f["subject_cfg"].tags)
    tags |= set(f["cause"].tags)
    tags |= set(f["remedy"].tags)
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        deck="backyard_ship",
        subject="parrot",
        symptom="quiet",
        cause="thirst",
        remedy="water",
        captain_name="Lina",
        captain_gender="girl",
        mate_name="Ben",
        mate_gender="boy",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        deck="dock_ship",
        subject="monkey",
        symptom="limping",
        cause="splinter",
        remedy="tweezer",
        captain_name="Tom",
        captain_gender="boy",
        mate_name="Mia",
        mate_gender="girl",
        parent="father",
        trait="curious",
    ),
    StoryParams(
        deck="attic_ship",
        subject="turtle",
        symptom="droopy",
        cause="heat",
        remedy="shade",
        captain_name="Nora",
        captain_gender="girl",
        mate_name="Eli",
        mate_gender="boy",
        parent="mother",
        trait="steady",
    ),
]


ASP_RULES = r"""
valid(Subject, Symptom, Cause, Remedy) :-
    subject(Subject),
    symptom(Symptom),
    cause(Cause),
    remedy(Remedy),
    cause_has_symptom(Cause, Symptom),
    fixes(Remedy, Cause).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for subject_id in SUBJECTS:
        lines.append(asp.fact("subject", subject_id))
    for symptom_id in SYMPTOMS:
        lines.append(asp.fact("symptom", symptom_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for symptom_id in sorted(cause.symptom_ids):
            lines.append(asp.fact("cause_has_symptom", cause_id, symptom_id))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("fixes", remedy_id, remedy.fixes))
    for deck_id in DECKS:
        lines.append(asp.fact("deck", deck_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


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

    try:
        sample = generate(CURATED[0])
        if not sample.story or "determine" not in sample.story.lower() or "ail" not in sample.story.lower():
            raise StoryError("(Smoke test failed: generated story was empty or missed required seed words.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pirate crew solves a small ail mystery through dialogue."
    )
    ap.add_argument("--deck", choices=DECKS)
    ap.add_argument("--subject", choices=SUBJECTS)
    ap.add_argument("--symptom", choices=SYMPTOMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid mystery combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, pool: list[str], avoid: str = "") -> tuple[str, str]:
    name = rng.choice([n for n in pool if n != avoid])
    girl_names = {"Lina", "Mira", "Ava", "Nora", "Lucy", "Maya", "Rose", "Ella", "Mia", "Zoe", "Anna", "Lily", "Tess", "June"}
    gender = "girl" if name in girl_names else "boy"
    return name, gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.symptom and args.cause and args.remedy:
        if not valid_combo(args.subject or next(iter(SUBJECTS)), args.symptom, args.cause, args.remedy):
            raise StoryError(explain_rejection(args.symptom, args.cause, args.remedy))
    elif args.cause and args.remedy and args.cause != REMEDIES[args.remedy].fixes:
        raise StoryError(explain_rejection(args.symptom or next(iter(SYMPTOMS)), args.cause, args.remedy))
    elif args.symptom and args.cause and args.symptom not in CAUSES[args.cause].symptom_ids:
        raise StoryError(explain_rejection(args.symptom, args.cause, args.remedy or next(iter(REMEDIES))))

    combos = [
        combo for combo in valid_combos()
        if (args.subject is None or combo[0] == args.subject)
        and (args.symptom is None or combo[1] == args.symptom)
        and (args.cause is None or combo[2] == args.cause)
        and (args.remedy is None or combo[3] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    subject_id, symptom_id, cause_id, remedy_id = rng.choice(sorted(combos))
    deck = args.deck or rng.choice(sorted(DECKS))
    captain_name, captain_gender = _pick_name(rng, CAPTAIN_NAMES)
    mate_name, mate_gender = _pick_name(rng, MATE_NAMES, avoid=captain_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        deck=deck,
        subject=subject_id,
        symptom=symptom_id,
        cause=cause_id,
        remedy=remedy_id,
        captain_name=captain_name,
        captain_gender=captain_gender,
        mate_name=mate_name,
        mate_gender=mate_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.deck not in DECKS:
        raise StoryError(f"(Invalid deck: {params.deck})")
    if params.subject not in SUBJECTS:
        raise StoryError(f"(Invalid subject: {params.subject})")
    if params.symptom not in SYMPTOMS:
        raise StoryError(f"(Invalid symptom: {params.symptom})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Invalid cause: {params.cause})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Invalid remedy: {params.remedy})")
    if not valid_combo(params.subject, params.symptom, params.cause, params.remedy):
        raise StoryError(explain_rejection(params.symptom, params.cause, params.remedy))

    world = tell(
        deck=DECKS[params.deck],
        subject_cfg=SUBJECTS[params.subject],
        symptom_cfg=SYMPTOMS[params.symptom],
        cause_cfg=CAUSES[params.cause],
        remedy_cfg=REMEDIES[params.remedy],
        captain_name=params.captain_name,
        captain_gender=params.captain_gender,
        mate_name=params.mate_name,
        mate_gender=params.mate_gender,
        parent_type=params.parent,
        trait=params.trait,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (subject, symptom, cause, remedy) combos:\n")
        for subject_id, symptom_id, cause_id, remedy_id in combos:
            print(f"  {subject_id:8} {symptom_id:8} {cause_id:8} {remedy_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.subject}: {p.symptom} from {p.cause} ({p.remedy})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
