#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/vision_suey_craft_workshop_kindness_transformation_rhyme.py
======================================================================================

A standalone storyworld about a small mystery in a craft workshop: a child hears a
strange rhyme, follows the clue with kindness, and helps a neglected craft become
something bright again.

The world is deliberately narrow and state-driven:

* A child comes to a craft workshop to finish a display piece.
* A hidden breeze makes a nearby craft whisper a little rhyme that includes the
  words "vision" and "suey".
* The child may choose a kind repair or an impatient shortcut.
* A kind repair transforms the neglected craft and solves the mystery happily.
* A careless shortcut is explicitly refused by the reasonableness gate.

The story uses:
    - setting: craft workshop
    - words: vision, suey
    - features: kindness, transformation, rhyme
    - style: mystery
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    fragile: bool = False
    # physical / emotional axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Project:
    id: str
    label: str
    phrase: str
    broken_part: str
    transformed_into: str
    whisper_from: str
    rhyme_tail: str
    material: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Clue:
    id: str
    hiding_place: str
    breeze_from: str
    note_line: str
    reveal: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Method:
    id: str
    sense: int
    gentle: bool
    fixes_fragile: bool
    text: str
    qa_text: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World container
# ---------------------------------------------------------------------------
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_whisper(world: World) -> list[str]:
    out: list[str] = []
    workshop = world.get("workshop")
    project = world.get("project")
    if workshop.meters["draft"] < THRESHOLD or project.meters["neglected"] < THRESHOLD:
        return out
    sig = ("whisper", project.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    project.memes["mystery"] += 1
    child = world.get("child")
    child.memes["wonder"] += 1
    out.append("__whisper__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    project = world.get("project")
    child = world.get("child")
    if project.meters["mended"] < THRESHOLD or project.meters["clean"] < THRESHOLD:
        return out
    sig = ("transform", project.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    project.meters["transformed"] += 1
    child.memes["pride"] += 1
    child.memes["kindness"] += 1
    out.append("__transform__")
    return out


RULES = [
    Rule(name="whisper", tag="mystery", apply=_r_whisper),
    Rule(name="transform", tag="craft", apply=_r_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Constraints / outcome model
# ---------------------------------------------------------------------------
def method_works(project: Project, method: Method) -> bool:
    return project.material == "fragile" and method.fixes_fragile


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for project_id in PROJECTS:
        for clue_id in CLUES:
            for method_id, method in METHODS.items():
                if method.sense >= SENSE_MIN and method_works(PROJECTS[project_id], method):
                    combos.append((project_id, clue_id, method_id))
    return combos


def explain_project_method(project: Project, method: Method) -> str:
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method.id}': it is too careless for a story about "
            f"kind repair in a craft workshop. Try one of: "
            f"{', '.join(sorted(m.id for m in sensible_methods()))}.)"
        )
    if not method_works(project, method):
        return (
            f"(No story: {project.phrase} is too delicate for {method.id}. "
            f"The fix should be gentle enough to mend {project.broken_part} "
            f"instead of damaging it.)"
        )
    return "(No story: this combination is not supported.)"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_kind_repair(world: World, method_id: str) -> dict:
    sim = world.copy()
    project = sim.get("project")
    method = METHODS[method_id]
    if method_works(PROJECTS[sim.facts["project_cfg"].id], method):
        project.meters["mended"] += 1
        project.meters["clean"] += 1
        propagate(sim, narrate=False)
    return {
        "transformed": project.meters["transformed"] >= THRESHOLD,
        "mystery": project.memes["mystery"],
    }


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, grownup: Entity, project: Project) -> None:
    world.say(
        f"After school, {child.id} stepped into the craft workshop with "
        f"{child.pronoun('possessive')} {grownup.label_word}. Shelves of ribbon, "
        f"buttons, and paint pots made the room feel full of tiny secrets."
    )
    world.say(
        f"{child.id} had come to finish {project.phrase} for the workshop display."
    )


def discover(world: World, child: Entity, project: Project) -> None:
    item = world.get("project")
    item.meters["neglected"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"But when {child.pronoun()} reached the worktable, {project.phrase} was slumped "
        f"beside the glue jar. {project.broken_part.capitalize()} was bent, and a soft "
        f"dusty line ran along the edge as if no one had cared for it all day."
    )


def whisper(world: World, child: Entity, project: Project, clue: Clue) -> None:
    workshop = world.get("workshop")
    workshop.meters["draft"] += 1
    propagate(world, narrate=False)
    child.memes["mystery"] += 1
    world.say(
        f"Then a hushy sound slipped across the room from {project.whisper_from}. "
        f'It sounded almost like a tiny voice saying, "{clue.note_line} {project.rhyme_tail}"'
    )
    world.say(
        f'{child.id} froze. "Did you hear that? It said vision... and suey," '
        f"{child.pronoun()} whispered."
    )


def search(world: World, child: Entity, grownup: Entity, clue: Clue) -> None:
    child.memes["care"] += 1
    world.say(
        f"{child.id} did not laugh or snatch at the crooked craft. Instead "
        f"{child.pronoun()} looked slowly around the workshop, following the little draft "
        f"to {clue.hiding_place}."
    )
    world.say(
        f"There, tucked behind a tin of beads, was a paper note. "
        f"{clue.reveal}"
    )
    world.facts["found_note"] = True


def choose_kind_method(world: World, child: Entity, project: Project, method: Method) -> None:
    pred = predict_kind_repair(world, method.id)
    world.facts["predicted_transform"] = pred["transformed"]
    item = world.get("project")
    item.meters["mended"] += 1
    item.meters["clean"] += 1
    child.memes["kindness"] += 1
    child.memes["patience"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{child.id} nodded. "It is not trying to scare us," {child.pronoun()} said. '
        f'"It needs help."'
    )
    world.say(
        f"Very gently, {child.pronoun()} {method.text}."
    )


def transform(world: World, child: Entity, project: Project, clue: Clue, method: Method) -> None:
    item = world.get("project")
    if item.meters["transformed"] >= THRESHOLD:
        world.say(
            f"At once the whole piece seemed to wake up. What had looked tired and crooked "
            f"now became {project.transformed_into}, and the mystery stopped feeling spooky "
            f"and started feeling bright."
        )
    world.say(
        f"The note's rhyme made sense at last: the whisper had only been the breeze from "
        f"{clue.breeze_from}, teasing through the torn edge and making a tiny {project.label} sound."
    )
    world.say(
        method.ending_image
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(project: Project, clue: Clue, method: Method,
         child_name: str = "Mina", child_gender: str = "girl",
         grownup_type: str = "mother", trait: str = "gentle") -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
    ))
    grownup = world.add(Entity(
        id="Parent",
        kind="character",
        type=grownup_type,
        role="grownup",
        label="the grown-up",
    ))
    workshop = world.add(Entity(
        id="workshop",
        type="room",
        label="craft workshop",
        attrs={"place": "craft workshop"},
    ))
    item = world.add(Entity(
        id="project",
        type="craft",
        label=project.label,
        fragile=True,
        attrs={"material": project.material},
    ))

    # initialize values read by rules / QA
    workshop.meters["draft"] = 0.0
    item.meters["neglected"] = 0.0
    item.meters["mended"] = 0.0
    item.meters["clean"] = 0.0
    item.meters["transformed"] = 0.0
    item.memes["mystery"] = 0.0
    child.memes["wonder"] = 0.0
    child.memes["kindness"] = 0.0

    world.facts.update(
        project_cfg=project,
        clue_cfg=clue,
        method_cfg=method,
        child=child,
        grownup=grownup,
        found_note=False,
    )

    introduce(world, child, grownup, project)
    world.para()
    discover(world, child, project)
    whisper(world, child, project, clue)
    world.para()
    search(world, child, grownup, clue)
    choose_kind_method(world, child, project, method)
    world.para()
    transform(world, child, project, clue, method)

    world.facts.update(
        solved=True,
        transformed=item.meters["transformed"] >= THRESHOLD,
        rhyme_heard=workshop.meters["draft"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PROJECTS = {
    "pig_puppet": Project(
        id="pig_puppet",
        label="pig puppet",
        phrase="a pink paper-bag pig puppet",
        broken_part="one floppy ear",
        transformed_into="a perky puppet with both ears standing up and a shiny button nose",
        whisper_from="the puppet's crinkled snout",
        rhyme_tail="Suey-suey, mend me truly.",
        material="fragile",
        tags={"pig", "puppet", "transformation"},
    ),
    "paper_lantern_pig": Project(
        id="paper_lantern_pig",
        label="paper lantern pig",
        phrase="a round paper lantern painted like a pig",
        broken_part="a torn side seam",
        transformed_into="a glowing lantern pig, round and smooth again",
        whisper_from="the slit in its paper seam",
        rhyme_tail="Suey-suey, stitch me newly.",
        material="fragile",
        tags={"pig", "lantern", "transformation"},
    ),
    "pig_mask": Project(
        id="pig_mask",
        label="pig mask",
        phrase="a rosy pig mask cut from card",
        broken_part="one loose ribbon tie",
        transformed_into="a bright pig mask with neat ribbons and cheerful cheeks",
        whisper_from="the curled snout hole",
        rhyme_tail="Suey-suey, tie me truly.",
        material="fragile",
        tags={"pig", "mask", "transformation"},
    ),
}

CLUES = {
    "bead_tin": Clue(
        id="bead_tin",
        hiding_place="the bead shelf",
        breeze_from="the cracked high window",
        note_line="Use kind vision, not collision.",
        reveal="In tidy pencil it read: \"Use kind vision, not collision.\"",
        tags={"vision", "breeze"},
    ),
    "button_drawer": Clue(
        id="button_drawer",
        hiding_place="the half-open button drawer",
        breeze_from="the little fan by the drying rack",
        note_line="Use kind vision for revision.",
        reveal="The note said: \"Use kind vision for revision.\"",
        tags={"vision", "fan"},
    ),
    "ribbon_jar": Clue(
        id="ribbon_jar",
        hiding_place="the ribbon corner",
        breeze_from="the vent above the sink",
        note_line="Use kind vision for a new edition.",
        reveal="On the note, in looping letters, were the words: \"Use kind vision for a new edition.\"",
        tags={"vision", "vent"},
    ),
}

METHODS = {
    "patch_and_brush": Method(
        id="patch_and_brush",
        sense=3,
        gentle=True,
        fixes_fragile=True,
        text="smoothed the rumpled paper, brushed off the dust, and patched the hurt place with careful paste",
        qa_text="smoothed it, cleaned it, and patched the damaged part with care",
        ending_image="When the display lamp clicked on, the mended craft shone on the shelf, and even the workshop shadows looked friendly.",
        tags={"repair", "kindness"},
    ),
    "retie_and_polish": Method(
        id="retie_and_polish",
        sense=3,
        gentle=True,
        fixes_fragile=True,
        text="retied the loose part, wiped away the dust, and pressed every edge flat with patient fingers",
        qa_text="retied the loose part and cleaned it with patient, gentle hands",
        ending_image="Soon it sat tall on the table, so neat and bright that the mystery had turned into a little triumph.",
        tags={"repair", "kindness"},
    ),
    "snip_fast": Method(
        id="snip_fast",
        sense=1,
        gentle=False,
        fixes_fragile=False,
        text="reached for the scissors to snip off the bent piece",
        qa_text="cut the damaged part off quickly",
        ending_image="",
        tags={"careless"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Ruby", "Tess"]
BOY_NAMES = ["Owen", "Finn", "Eli", "Noah", "Max", "Leo"]
TRAITS = ["gentle", "careful", "kind", "patient", "thoughtful"]


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    project: str
    clue: str
    method: str
    child_name: str
    child_gender: str
    grownup: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "vision": [
        (
            "What can the word vision mean in a story?",
            "Vision can mean seeing with your eyes, but it can also mean imagining what something could become. In this kind story, vision means looking past the damage and seeing the hidden good shape."
        )
    ],
    "suey": [
        (
            "Why does the story use the word suey?",
            "Suey is a playful pig sound in this story's rhyme. It helps make the mystery clue sound odd and memorable."
        )
    ],
    "repair": [
        (
            "Why is a gentle repair better than a rough fix for a paper craft?",
            "Paper crafts can tear more if you yank or cut them too fast. Gentle hands help mend the weak part without making a bigger rip."
        )
    ],
    "kindness": [
        (
            "How can kindness help solve a problem?",
            "Kindness helps someone slow down and notice what is really needed. That often leads to a better fix than rushing or getting cross."
        )
    ],
    "breeze": [
        (
            "Why can a breeze make a paper craft sound spooky?",
            "Air moving through a crack or torn edge can make a soft whistling sound. In a quiet room, that can feel mysterious even when it has a simple cause."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    project = f["project_cfg"]
    clue = f["clue_cfg"]
    return [
        'Write a gentle mystery story for a 3-to-5-year-old set in a craft workshop that includes the words "vision" and "suey".',
        f"Tell a rhyming workshop mystery where {child.id} hears a strange whisper near {project.phrase}, follows a clue, and solves the problem with kindness.",
        f'Write a child-facing story in which a spooky little rhyme from {clue.hiding_place} leads not to danger, but to a transformation brought about by gentle repair.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    project = f["project_cfg"]
    clue = f["clue_cfg"]
    method = f["method_cfg"]
    pw = grownup.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} in a craft workshop with {child.pronoun('possessive')} {pw}. {child.id} finds a neglected craft and chooses to help it."
        ),
        (
            "What made the workshop feel mysterious?",
            f"A soft whisper seemed to come from {project.whisper_from}, and the rhyme mentioned vision and suey. That odd sound made the room feel full of clues instead of ordinary craft noise."
        ),
        (
            "What clue did the child find?",
            f"{child.id} followed the draft to {clue.hiding_place} and found a note. The note said, \"{clue.note_line}\" which explained that the mystery was really asking for a kind repair."
        ),
        (
            f"How did {child.id} solve the mystery?",
            f"{child.id} {method.qa_text}. That helped the broken craft become {project.transformed_into}, so the mystery ended with a transformation instead of a scare."
        ),
        (
            "Why was kindness important in the story?",
            f"Kindness made {child.id} slow down and notice what the craft needed. Because of that, {child.pronoun()} chose a gentle fix instead of a rough one, and the hidden beauty could come back."
        ),
        (
            "What was really causing the whisper?",
            f"The whisper came from air moving in from {clue.breeze_from}. The breeze slipped through the damaged part and made the craft sound like it was speaking."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"vision", "suey", "repair", "kindness", "breeze"}
    out: list[tuple[str, str]] = []
    order = ["vision", "suey", "repair", "kindness", "breeze"]
    for tag in order:
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        project="pig_puppet",
        clue="bead_tin",
        method="patch_and_brush",
        child_name="Mina",
        child_gender="girl",
        grownup="mother",
        trait="gentle",
    ),
    StoryParams(
        project="paper_lantern_pig",
        clue="button_drawer",
        method="retie_and_polish",
        child_name="Owen",
        child_gender="boy",
        grownup="father",
        trait="careful",
    ),
    StoryParams(
        project="pig_mask",
        clue="ribbon_jar",
        method="patch_and_brush",
        child_name="Ruby",
        child_gender="girl",
        grownup="mother",
        trait="thoughtful",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% reasonable combinations
valid(P, C, M) :- project(P), clue(C), method(M), sensible(M), fragile(P), fixes_fragile(M).

% outcome for this world: every valid scenario is transformed successfully
transformed :- chosen_project(P), chosen_method(M), fragile(P), fixes_fragile(M), sensible(M).
outcome(happy) :- transformed.

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PROJECTS:
        lines.append(asp.fact("project", pid))
        lines.append(asp.fact("fragile", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        if method.sense >= SENSE_MIN:
            lines.append(asp.fact("sensible", mid))
        if method.fixes_fragile:
            lines.append(asp.fact("fixes_fragile", mid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_project", params.project),
        asp.fact("chosen_method", params.method),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    cases = list(CURATED)
    for s in range(25):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print("resolve_params unexpectedly failed during verification.")
            break
    mismatches = 0
    for p in cases:
        py = "happy"
        asp_res = asp_outcome(p)
        if asp_res != py:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a craft-workshop mystery solved with kindness."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true", help="render curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.method:
        project = PROJECTS[args.project]
        method = METHODS[args.method]
        if not (method.sense >= SENSE_MIN and method_works(project, method)):
            raise StoryError(explain_project_method(project, method))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        # caught above when project is pinned; keep separate for method-only pins
        raise StoryError(explain_project_method(PROJECTS[next(iter(PROJECTS))], METHODS[args.method]))

    combos = [
        c for c in valid_combos()
        if (args.project is None or c[0] == args.project)
        and (args.clue is None or c[1] == args.clue)
        and (args.method is None or c[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project_id, clue_id, method_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    grownup = args.grownup or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        project=project_id,
        clue=clue_id,
        method=method_id,
        child_name=child_name,
        child_gender=gender,
        grownup=grownup,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    project = PROJECTS[params.project]
    clue = CLUES[params.clue]
    method = METHODS[params.method]
    if not (method.sense >= SENSE_MIN and method_works(project, method)):
        raise StoryError(explain_project_method(project, method))

    world = tell(
        project=project,
        clue=clue,
        method=method,
        child_name=params.child_name,
        child_gender=params.child_gender,
        grownup_type=params.grownup,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (project, clue, method) combos:\n")
        for project, clue, method in combos:
            print(f"  {project:18} {clue:14} {method}")
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
            header = f"### {p.child_name}: {p.project} with {p.clue} ({p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
