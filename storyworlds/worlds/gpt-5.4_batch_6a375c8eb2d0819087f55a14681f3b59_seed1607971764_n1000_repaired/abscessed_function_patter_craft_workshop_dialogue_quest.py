#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/abscessed_function_patter_craft_workshop_dialogue_quest.py
=====================================================================================

A standalone story world for a tiny "space adventure in a craft workshop" domain.

Premise
-------
A child in a craft workshop is preparing a glowing space-themed project for a
school function. The project needs one special decorating supply, but the supply
is jammed or spoiled. The child begins a little "quest" to save the project.
A calm grown-up or older helper guides the child toward a sensible fix instead
of a forceful, messy, or unsafe one. The repaired craft then shines at the end,
proving what changed.

This world deliberately includes the words:
    abscessed, function, patter

The word "abscessed" appears only as part of a child's fanciful description of a
swollen glue cap; the story itself makes that image about a puffed-up craft
problem, not a frightening injury.

Run it
------
    python storyworlds/worlds/gpt-5.4/abscessed_function_patter_craft_workshop_dialogue_quest.py
    python storyworlds/worlds/gpt-5.4/abscessed_function_patter_craft_workshop_dialogue_quest.py --project lantern --supply glitter_glue
    python storyworlds/worlds/gpt-5.4/abscessed_function_patter_craft_workshop_dialogue_quest.py --fix yank
    python storyworlds/worlds/gpt-5.4/abscessed_function_patter_craft_workshop_dialogue_quest.py --all
    python storyworlds/worlds/gpt-5.4/abscessed_function_patter_craft_workshop_dialogue_quest.py --qa --json
    python storyworlds/worlds/gpt-5.4/abscessed_function_patter_craft_workshop_dialogue_quest.py --verify
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
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
@dataclass
class Project:
    id: str
    label: str
    phrase: str
    goal: str
    scene: str
    finish: str
    display: str
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
class Supply:
    id: str
    label: str
    phrase: str
    use_text: str
    jam_kind: str
    symptom: str
    puffy_line: str
    sound: str
    material: str
    needs_flow: bool = True
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
class Fix:
    id: str
    sense: int
    power: int
    gentle: bool
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
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


def _r_blocked_frustrates(world: World) -> list[str]:
    out: list[str] = []
    supply = world.get("supply")
    child = world.get("child")
    if supply.meters["blocked"] < THRESHOLD:
        return out
    sig = ("frustrated", supply.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["frustration"] += 1
    out.append("__blocked__")
    return out


def _r_force_makes_mess(world: World) -> list[str]:
    out: list[str] = []
    supply = world.get("supply")
    project = world.get("project")
    child = world.get("child")
    if supply.meters["forced"] < THRESHOLD or supply.meters["blocked"] < THRESHOLD:
        return out
    sig = ("mess", supply.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    supply.meters["spilled"] += 1
    project.meters["messy"] += 1
    child.memes["worry"] += 1
    out.append("__mess__")
    return out


def _r_fix_restores(world: World) -> list[str]:
    out: list[str] = []
    supply = world.get("supply")
    project = world.get("project")
    child = world.get("child")
    if supply.meters["cleared"] < THRESHOLD:
        return out
    sig = ("restored", supply.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    supply.meters["blocked"] = 0.0
    project.meters["ready"] += 1
    child.memes["relief"] += 1
    child.memes["hope"] += 1
    out.append("__restored__")
    return out


CAUSAL_RULES = [
    Rule(name="blocked_frustrates", tag="emotional", apply=_r_blocked_frustrates),
    Rule(name="force_makes_mess", tag="physical", apply=_r_force_makes_mess),
    Rule(name="fix_restores", tag="physical", apply=_r_fix_restores),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def needs_clearing(supply: Supply) -> bool:
    return supply.needs_flow


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def jam_severity(supply: Supply) -> int:
    return 2 if supply.jam_kind in {"dried_tip", "thick_glitter"} else 1


def fix_works(fix: Fix, supply: Supply) -> bool:
    return fix.power >= jam_severity(supply)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for project_id in PROJECTS:
        for supply_id, supply in SUPPLIES.items():
            if needs_clearing(supply):
                combos.append((project_id, supply_id))
    return combos


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    better = " / ".join(sorted(x.id for x in sensible_fixes()))
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). A better story uses a calmer fix, "
        f"such as: {better}.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_fix(world: World, fix: Fix, supply: Supply) -> dict:
    sim = world.copy()
    _attempt_fix(sim, fix, supply, narrate=False)
    return {
        "works": sim.get("supply").meters["blocked"] < THRESHOLD,
        "mess": sim.get("project").meters["messy"],
    }


# ---------------------------------------------------------------------------
# Verbs / beats
# ---------------------------------------------------------------------------
def setup_workshop(world: World, child: Entity, helper: Entity, project: Project) -> None:
    child.memes["joy"] += 1
    helper.memes["care"] += 1
    world.say(
        f"In the craft workshop, {child.id} felt as if {child.pronoun()} had stepped onto "
        f"a tiny starship deck. Foil stars winked from jars, paper moons swung on strings, "
        f"and the soft patter on the skylight sounded like rain tapping on a spaceship hull."
    )
    world.say(
        f'{helper.id} smiled at the crowded table. "Commander {child.id}," {helper.pronoun()} said, '
        f'"our quest is to finish {project.phrase} for the school function."'
    )
    world.say(
        f"{child.id} looked at {project.phrase} and grinned. {project.goal.capitalize()} felt close enough to touch."
    )


def choose_supply(world: World, child: Entity, supply: Supply) -> None:
    world.say(
        f'"We only need {supply.phrase} to {supply.use_text}," {child.id} said. '
        f'{child.pronoun().capitalize()} reached for it with careful hands.'
    )


def discover_jam(world: World, child: Entity, helper: Entity, supply_ent: Entity, supply: Supply) -> None:
    supply_ent.meters["blocked"] += 1
    supply_ent.meters["puffy"] += 1
    world.facts["problem_seen"] = True
    propagate(world, narrate=False)
    world.say(
        f"But the {supply.label} would not {supply.sound}. {supply.symptom.capitalize()}, "
        f"and the cap looked {supply.puffy_line}."
    )
    world.say(
        f'{child.id} blinked. "It looks almost abscessed," {child.pronoun()} whispered, '
        f'trying out a big word for the swollen little cap. "{helper.id}, how can our rocket work now?"'
    )


def warn_against_force(world: World, helper: Entity, child: Entity, supply: Supply) -> None:
    cautious = predict_fix(world, FIXES["soak"], supply)
    world.facts["predicted_gentle_fix"] = cautious["works"]
    world.say(
        f'{helper.id} knelt beside {child.id}. "Not by squeezing harder," {helper.pronoun()} said. '
        f'"When a {supply.label} is blocked, force usually makes a mess before it makes progress."'
    )


def decide_force(world: World, child: Entity) -> None:
    child.memes["impatience"] += 1
    world.say(
        f'{child.id} bit {child.pronoun("possessive")} lip. "But the function starts soon," '
        f'{child.pronoun()} said. "I want to save the mission now."'
    )


def _attempt_fix(world: World, fix: Fix, supply: Supply, narrate: bool = True) -> None:
    supply_ent = world.get("supply")
    if fix.id == "yank":
        supply_ent.meters["forced"] += 1
        propagate(world, narrate=False)
        if narrate:
            world.say(fix.fail.format(supply=supply.label))
        return
    if fix_works(fix, supply):
        supply_ent.meters["cleared"] += 1
        propagate(world, narrate=False)
        if narrate:
            world.say(fix.text.format(supply=supply.label))
        return
    if narrate:
        world.say(fix.fail.format(supply=supply.label))


def fail_mess(world: World, child: Entity, project: Entity, supply: Supply) -> None:
    if project.meters["messy"] < THRESHOLD:
        return
    child.memes["sadness"] += 1
    world.say(
        f"A blob of {supply.material} splatted across the table instead. Some of it streaked the "
        f"project, and for a moment the brave little spacecraft looked more stuck than splendid."
    )


def helper_quest(world: World, helper: Entity, child: Entity, fix: Fix, supply: Supply) -> None:
    world.say(
        f'"New plan," {helper.id} said. "Every captain needs a calm check before the next move. '
        f'Our quest is to help the {supply.label} function again."'
    )
    _attempt_fix(world, fix, supply, narrate=True)
    if world.get("supply").meters["blocked"] < THRESHOLD:
        world.say(
            f'{child.id} leaned close and gasped. "It works!" {child.pronoun()} said. '
            f'"The supply can flow like stardust again."'
        )


def finish_project(world: World, child: Entity, helper: Entity, project: Project, supply: Supply) -> None:
    project_ent = world.get("project")
    child.memes["joy"] += 1
    project_ent.meters["finished"] += 1
    world.say(
        f"Together they added the last shining lines of {supply.material}. "
        f"{project.finish.capitalize()} made the whole craft workshop feel like mission control."
    )
    world.say(
        f"That evening, {project.display} at the school function, and {child.id} stood a little taller beside it."
    )


def lesson(world: World, helper: Entity, child: Entity, supply: Supply) -> None:
    child.memes["lesson"] += 1
    helper.memes["pride"] += 1
    world.say(
        f'{helper.id} gave {child.id} a side hug. "Today you learned a real maker lesson," '
        f'{helper.pronoun()} said. "When tools or supplies get stubborn, gentle thinking helps them function better than rushing."'
    )
    world.say(
        f'{child.id} nodded. "Next time I will ask for help, slow down, and fix the problem before I squeeze," '
        f'{child.pronoun()} said.'
    )


def tell(
    project: Project,
    supply: Supply,
    fix: Fix,
    *,
    child_name: str = "Nova",
    child_gender: str = "girl",
    helper_name: str = "Uncle Ray",
    helper_type: str = "man",
    parent_type: str = "mother",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            traits=["eager", "creative"],
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_type,
            label=helper_name,
            role="helper",
            traits=["calm", "patient"],
        )
    )
    world.add(
        Entity(
            id="project",
            kind="thing",
            type="project",
            label=project.label,
            phrase=project.phrase,
            role="project",
            tags=set(project.tags),
        )
    )
    world.add(
        Entity(
            id="supply",
            kind="thing",
            type="supply",
            label=supply.label,
            phrase=supply.phrase,
            role="supply",
            tags=set(supply.tags),
        )
    )

    setup_workshop(world, child, helper, project)
    choose_supply(world, child, supply)

    world.para()
    discover_jam(world, child, helper, world.get("supply"), supply)
    warn_against_force(world, helper, child, supply)
    decide_force(world, child)

    world.para()
    if fix.id == "yank":
        _attempt_fix(world, fix, supply, narrate=True)
        fail_mess(world, child, world.get("project"), supply)
        world.para()
        helper_quest(world, helper, child, FIXES["soak"], supply)
    else:
        helper_quest(world, helper, child, fix, supply)

    world.para()
    finish_project(world, child, helper, project, supply)
    lesson(world, helper, child, supply)

    outcome = "rescued"
    world.facts.update(
        child=child,
        helper=helper,
        project_cfg=project,
        supply_cfg=supply,
        fix=fix,
        outcome=outcome,
        project=world.get("project"),
        supply=world.get("supply"),
        had_mess=world.get("project").meters["messy"] >= THRESHOLD,
        worked=world.get("supply").meters["blocked"] < THRESHOLD,
        school_function=True,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PROJECTS = {
    "lantern": Project(
        id="lantern",
        label="star lantern",
        phrase="a silver star lantern",
        goal="make the lantern glow like a tiny moon",
        scene="moonlight across foil wings",
        finish="silver specks twirled over the paper stars",
        display="the lantern glowed softly on the long display table",
        tags={"lantern", "craft", "function"},
    ),
    "rocket": Project(
        id="rocket",
        label="cardboard rocket",
        phrase="a cardboard rocket with round windows",
        goal="make the rocket blaze with a tail of comet sparkle",
        scene="comet light across a paper hull",
        finish="a bright comet tail curled behind the rocket",
        display="the rocket stood proud near the front of the hall",
        tags={"rocket", "craft", "function"},
    ),
    "mobile": Project(
        id="mobile",
        label="planet mobile",
        phrase="a hanging planet mobile",
        goal="set the planets spinning in a bright little galaxy",
        scene="tiny worlds turning above the table",
        finish="small planets shimmered as they began to spin",
        display="the mobile turned slowly over the craft corner",
        tags={"mobile", "craft", "function"},
    ),
}

SUPPLIES = {
    "glitter_glue": Supply(
        id="glitter_glue",
        label="glitter glue bottle",
        phrase="the glitter glue bottle",
        use_text="draw the last star trail",
        jam_kind="thick_glitter",
        symptom="Nothing came out except one tired wobble",
        puffy_line="puffed and swollen with dried silver glue",
        sound="squeeze a shining line",
        material="silver glue",
        tags={"glue", "glitter"},
    ),
    "paint_pen": Supply(
        id="paint_pen",
        label="paint pen",
        phrase="the gold paint pen",
        use_text="ring the windows with gold",
        jam_kind="dried_tip",
        symptom="Its tip stayed dry and scratchy",
        puffy_line="a little too puffy around the cap",
        sound="draw a bright stripe",
        material="gold paint",
        tags={"paint", "pen"},
    ),
    "star_paste": Supply(
        id="star_paste",
        label="star paste tube",
        phrase="the star paste tube",
        use_text="paste the last bright stars in place",
        jam_kind="dried_tip",
        symptom="Only a tiny bump of paste stuck at the mouth",
        puffy_line="lumpy and swollen with crusted paste",
        sound="press out a neat bead",
        material="shining paste",
        tags={"paste", "stars"},
    ),
}

FIXES = {
    "soak": Fix(
        id="soak",
        sense=3,
        power=3,
        gentle=True,
        text='They set the tip in warm water, wiped it clean, and turned the cap slowly until the {supply} opened with a soft little pop.',
        fail='They tried warm water on the {supply}, but the clog still held fast.',
        qa_text="They loosened the dried tip with warm water and opened it carefully",
        tags={"warm_water", "gentle_fix"},
    ),
    "pin": Fix(
        id="pin",
        sense=2,
        power=2,
        gentle=True,
        text='With a grown-up hand guiding the work, they used a tiny pin to clear the tip of the {supply} and let the line flow again.',
        fail='Even after they checked the tip of the {supply}, nothing flowed yet.',
        qa_text="They carefully cleared the tip with a tiny pin while a grown-up helped",
        tags={"pin", "gentle_fix"},
    ),
    "yank": Fix(
        id="yank",
        sense=1,
        power=0,
        gentle=False,
        text='',
        fail='Instead of opening, the {supply} squirted sideways when it was yanked and squeezed too hard.',
        qa_text="The child yanked and squeezed too hard, which made a mess instead of helping",
        tags={"messy_fix"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Ava", "Zoe", "Tess"]
BOY_NAMES = ["Leo", "Milo", "Finn", "Jace", "Eli", "Noah"]
HELPERS = [
    {"name": "Uncle Ray", "type": "man"},
    {"name": "Aunt May", "type": "woman"},
    {"name": "Dad", "type": "father"},
    {"name": "Mom", "type": "mother"},
]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    project: str
    supply: str
    fix: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_type: str
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
    "glue": [
        (
            "Why can a glue bottle get blocked?",
            "Glue can dry at the tip when a little bit is left in the opening. Then the next squeeze cannot push the fresh glue out easily."
        )
    ],
    "paint": [
        (
            "Why does a paint pen sometimes stop working?",
            "A paint pen can dry at the tip if it sits open too long. The color inside is still there, but the dry tip keeps it from coming out."
        )
    ],
    "warm_water": [
        (
            "Why can warm water help with dried craft goo?",
            "Warm water can soften dried glue or paste. When the dried bit softens, it is easier to wipe away without forcing the bottle."
        )
    ],
    "pin": [
        (
            "Why should a tiny pin be used carefully?",
            "A pin is small and sharp, so a grown-up should help. Careful hands keep the tool safe and stop the craft from getting torn or poked."
        )
    ],
    "gentle_fix": [
        (
            "Why is a gentle fix often better than forcing something?",
            "A gentle fix solves the real problem instead of making a bigger mess. Slowing down can protect both the tool and the project."
        )
    ],
    "function": [
        (
            "What is a school function?",
            "A school function is a special event at school, like a show, fair, or family night. People gather to see work, sing, talk, or celebrate together."
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light with a cover around it. A paper lantern can glow softly and make decorations look bright and warm."
        )
    ],
    "rocket": [
        (
            "What makes a rocket shape look fast?",
            "Pointed noses, fins, and long bright trails make a rocket look fast. Those shapes remind people of something zooming through space."
        )
    ],
    "mobile": [
        (
            "What is a mobile in a craft room?",
            "A mobile is something that hangs and moves gently in the air. People often make them with shapes on strings so they can turn and sway."
        )
    ],
}
KNOWLEDGE_ORDER = ["function", "glue", "paint", "warm_water", "pin", "gentle_fix", "lantern", "rocket", "mobile"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    project = f["project_cfg"]
    supply = f["supply_cfg"]
    fix = f["fix"]
    prompt_fix = "a calm repair" if fix.id != "yank" else "a messy false start and then a calm repair"
    return [
        f'Write a short space-adventure-style story set in a craft workshop where a child must finish {project.phrase} for a school function. Include the words "abscessed", "function", and "patter".',
        f"Tell a gentle quest story with dialogue where {child.id} and {helper.id} discover that {supply.phrase} is blocked and solve it with {prompt_fix}.",
        f"Write a child-facing story about making art for a school function, where a workshop problem interrupts the mission and the lesson learned is to slow down and ask for help.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    project = f["project_cfg"]
    supply = f["supply_cfg"]
    fix = f["fix"]
    had_mess = f["had_mess"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who was making {project.phrase} in the craft workshop, and {helper.id}, who helped with the problem."
        ),
        (
            "What was their quest?",
            f"Their quest was to finish {project.phrase} in time for the school function. They only needed {supply.phrase} to add the last important detail."
        ),
        (
            f"What problem did {child.id} find?",
            f"{child.id} found that {supply.phrase} was blocked and would not work. The swollen cap made the child describe it as almost abscessed, which showed how puffed-up and stubborn it looked."
        ),
    ]
    if had_mess:
        qa.append(
            (
                f"Why did the first try go wrong?",
                f"The first try went wrong because {child.id} rushed and squeezed too hard. That did not clear the blockage, and it made a messy splat on the project instead."
            )
        )
    qa.append(
        (
            f"How did they fix the supply?",
            f"{fix.qa_text}. They chose a careful method so the blockage could clear without hurting the project."
            if fix.id != "yank"
            else "After the messy squeeze failed, they used warm water to soften and clear the tip. The calmer method worked because it treated the dried clog instead of fighting it."
        )
    )
    qa.append(
        (
            "What lesson did the child learn?",
            f"{child.id} learned that rushing is not the best way to make things function again. Slowing down, asking for help, and using a gentle fix saved the craft."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"The project was finished and shown at the school function. Its shining final details proved that the problem had really been solved."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["project_cfg"].tags) | set(f["supply_cfg"].tags)
    tags.add("function")
    tags |= set(f["fix"].tags)
    if f["had_mess"]:
        tags.add("gentle_fix")
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
needs_story(P,S) :- project(P), supply(S), needs_flow(S).
sensible(F) :- fix(F), sense(F,Score), sense_min(Min), Score >= Min.
valid(P,S) :- needs_story(P,S).

severity(S,2) :- jam_kind(S, thick_glitter).
severity(S,2) :- jam_kind(S, dried_tip).
severity(S,1) :- jam_kind(S, mild_tip).

works(F,S) :- power(F,P), severity(S,Need), P >= Need.
bad_start :- chosen_fix(yank).
outcome(rescued) :- chosen_supply(S), chosen_fix(F), works(F,S), not bad_start.
outcome(rescued) :- chosen_supply(_), bad_start.
#show valid/2.
#show sensible/1.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PROJECTS:
        lines.append(asp.fact("project", pid))
    for sid, supply in SUPPLIES.items():
        lines.append(asp.fact("supply", sid))
        lines.append(asp.fact("needs_flow", sid))
        lines.append(asp.fact("jam_kind", sid, supply.jam_kind))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_supply", params.supply),
        asp.fact("chosen_fix", params.fix),
    ])
    model = asp.one_model(asp_program(extra))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if params.fix == "yank":
        return "rescued"
    return "rescued" if fix_works(FIXES[params.fix], SUPPLIES[params.supply]) else "rescued"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if asp_valid - py_valid:
            print("  only in asp:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {x.id for x in sensible_fixes()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible fixes match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: asp={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    for seed in range(20):
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
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space-adventure craft workshop storyworld. Unspecified options are chosen at random (seeded)."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--supply", choices=SUPPLIES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true", help="render curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="show ASP-derived valid combos")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.supply is None or combo[1] == args.supply)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project, supply = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(x.id for x in sensible_fixes()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.child_name or rng.choice(name_pool)
    helper_def = rng.choice(HELPERS)
    return StoryParams(
        project=project,
        supply=supply,
        fix=fix,
        child_name=child_name,
        child_gender=gender,
        helper_name=helper_def["name"],
        helper_type=helper_def["type"],
    )


def generate(params: StoryParams) -> StorySample:
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.supply not in SUPPLIES:
        raise StoryError(f"(Unknown supply: {params.supply})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if FIXES[params.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))

    world = tell(
        PROJECTS[params.project],
        SUPPLIES[params.supply],
        FIXES[params.fix],
        child_name=params.child_name,
        child_gender=params.child_gender,
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


CURATED = [
    StoryParams(
        project="lantern",
        supply="glitter_glue",
        fix="soak",
        child_name="Nova",
        child_gender="girl",
        helper_name="Aunt May",
        helper_type="woman",
    ),
    StoryParams(
        project="rocket",
        supply="paint_pen",
        fix="pin",
        child_name="Leo",
        child_gender="boy",
        helper_name="Dad",
        helper_type="father",
    ),
    StoryParams(
        project="mobile",
        supply="star_paste",
        fix="soak",
        child_name="Mira",
        child_gender="girl",
        helper_name="Uncle Ray",
        helper_type="man",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (project, supply) combos:\n")
        for project, supply in combos:
            print(f"  {project:8} {supply}")
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
            header = f"### {p.child_name}: {p.project} with {p.supply} ({p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
