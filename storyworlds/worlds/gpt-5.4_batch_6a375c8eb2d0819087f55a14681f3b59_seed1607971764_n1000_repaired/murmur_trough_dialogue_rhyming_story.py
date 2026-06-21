#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/murmur_trough_dialogue_rhyming_story.py
==================================================================

A standalone story world for a tiny rhyming farm tale: two children hear the
soft murmur of thirsty animals around a trough, one child reaches for a quick
but clumsy fix, and a calmer choice leads to clean water.

This world keeps the prose child-facing and musical, with dialogue in nearly
every beat, while the actual story comes from simulated state:

- typed entities with physical meters and emotional memes
- a small reasonableness gate over trough troubles and cleaning tools
- a three-way outcome model: averted spill, contained spill, or tipped trough
- grounded prompts, story QA, and world-knowledge QA
- an inline ASP twin for the gate and ending model

Run it
------
    python storyworlds/worlds/gpt-5.4/murmur_trough_dialogue_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/murmur_trough_dialogue_rhyming_story.py --animal ducklings --problem leaf_drift
    python storyworlds/worlds/gpt-5.4/murmur_trough_dialogue_rhyming_story.py --tool poke_stick
    python storyworlds/worlds/gpt-5.4/murmur_trough_dialogue_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/murmur_trough_dialogue_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/murmur_trough_dialogue_rhyming_story.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
BOLDNESS_INIT = 5.0
STEADY_TRAITS = {"careful", "patient", "steady", "thoughtful"}


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
    movable: bool = False
    drinker: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "farmer_woman", "woman"}
        male = {"boy", "father", "farmer_man", "man"}
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
            "farmer_woman": "farmer",
            "farmer_man": "farmer",
        }.get(self.type, self.type)
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
class Yard:
    id: str
    place: str
    sky: str
    ground: str
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
class AnimalGroup:
    id: str
    label: str
    phrase: str
    sound: str
    drink_style: str
    step_line: str
    plural: bool = True
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
class Problem:
    id: str
    label: str
    murmur_line: str
    look_line: str
    risk_line: str
    actions: set[str]
    severity: int
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
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    sense: int
    power: int
    success_text: str
    fail_text: str
    qa_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_animals_fuss(world: World) -> list[str]:
    out: list[str] = []
    trough = world.get("trough")
    animals = world.get("animals")
    if trough.meters["dirty"] >= THRESHOLD or trough.meters["blocked"] >= THRESHOLD or trough.meters["empty"] >= THRESHOLD:
        sig = ("fuss",)
        if sig not in world.fired:
            world.fired.add(sig)
            animals.memes["worry"] += 1
            animals.meters["thirst"] += 1
            out.append("__murmur__")
    return out


def _r_precarious(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("instigator")
    trough = world.get("trough")
    if child.meters["on_rim"] >= THRESHOLD:
        sig = ("precarious",)
        if sig not in world.fired:
            world.fired.add(sig)
            trough.meters["wobble"] += 1
            child.memes["risk"] += 1
            out.append("__wobble__")
    return out


CAUSAL_RULES = [
    Rule(name="animals_fuss", tag="physical", apply=_r_animals_fuss),
    Rule(name="precarious", tag="physical", apply=_r_precarious),
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


def trouble_exists(problem: Problem) -> bool:
    return bool(problem.actions)


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sense >= SENSE_MIN]


def tool_fits(problem: Problem, tool: Tool) -> bool:
    return tool.action in problem.actions


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for yard_id in YARDS:
        for animal_id in ANIMALS:
            for problem_id, problem in PROBLEMS.items():
                if not trouble_exists(problem):
                    continue
                combos.append((yard_id, animal_id, problem_id))
    return combos


def spill_severity(problem: Problem, delay: int) -> int:
    return problem.severity + delay


def is_contained(tool: Tool, problem: Problem, delay: int) -> bool:
    return tool.power >= spill_severity(problem, delay)


def initial_steady(trait: str) -> float:
    return 5.0 if trait in STEADY_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_steady(trait) + 1.0 + (3.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BOLDNESS_INIT


def predict_spill(world: World) -> dict:
    sim = world.copy()
    child = sim.get("instigator")
    trough = sim.get("trough")
    child.meters["on_rim"] += 1
    trough.meters["sloshed"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": trough.meters["wobble"],
        "spill": trough.meters["wobble"] >= THRESHOLD,
    }


def opening(world: World, instigator: Entity, cautioner: Entity, yard: Yard, animals: AnimalGroup) -> None:
    for kid in (instigator, cautioner):
        kid.memes["joy"] += 1
    world.say(
        f"In {yard.place}, beneath a {yard.sky} sky, "
        f"{instigator.id} and {cautioner.id} came skipping by. "
        f"{yard.ground.capitalize()} seemed bright in the sun's warm trough of gold, "
        f"and morning felt merry, not hurried or cold."
    )
    world.say(
        f'By the old water trough stood {animals.phrase}, waiting in line. '
        f'"Look how they gather," said {cautioner.id}. "They all want a drink in good time."'
    )


def notice_problem(world: World, cautioner: Entity, problem: Problem, animals: AnimalGroup) -> None:
    trough = world.get("trough")
    if "dirty" in problem.actions:
        trough.meters["dirty"] += 1
    if "block" in problem.actions:
        trough.meters["blocked"] += 1
    if "rinse" in problem.actions:
        trough.meters["dirty"] += 1
    trough.meters["needs_fix"] += 1
    world.facts["problem_seen"] = True
    propagate(world, narrate=False)
    world.say(
        f'Then up rose a {problem.murmur_line} from {animals.label} by the rail. '
        f'"The trough looks wrong," said {cautioner.id}. "{problem.look_line}"'
    )


def tempt(world: World, instigator: Entity) -> None:
    instigator.memes["boldness"] += 1
    world.say(
        f'{instigator.id} tipped up {instigator.pronoun("possessive")} chin with a quick little laugh. '
        f'"I can hop on the rim," {instigator.pronoun()} said, "and swish it all clean in half!"'
    )


def warn(world: World, cautioner: Entity, instigator: Entity, problem: Problem, helper: Entity) -> None:
    pred = predict_spill(world)
    cautioner.memes["care"] += 1
    world.facts["predicted_wobble"] = pred["wobble"]
    extra = ""
    if cautioner.memes["steady"] >= 6:
        extra = f" {cautioner.id} planted both feet and would not give way."
    world.say(
        f'"Please don\'t," said {cautioner.id}. "The trough may tip, and the water may slide. '
        f'{problem.risk_line} Let\'s call {helper.label_word} and stand by the side."{extra}'
    )


def back_down(world: World, instigator: Entity, cautioner: Entity, helper: Entity) -> None:
    instigator.memes["boldness"] = 0.0
    instigator.memes["relief"] += 1
    cautioner.memes["relief"] += 1
    world.say(
        f'{instigator.id} looked at the rim, then looked at {cautioner.id} once more. '
        f'"All right," {instigator.pronoun()} whispered, "I won\'t make a splash on the floor."'
    )
    world.say(
        f'Together they called for the {helper.label_word}, calm and clear as a bell. '
        f'That asking-for-help was the brave little choice, and it suited them very well.'
    )


def climb(world: World, instigator: Entity) -> None:
    trough = world.get("trough")
    instigator.meters["on_rim"] += 1
    trough.meters["sloshed"] += 1
    propagate(world, narrate=False)
    world.say(
        f'But {instigator.id} put one boot on the rim with a hurry-up, show-off swing. '
        f'The trough gave a wobble and shivered around, and the water began to ring.'
    )


def alarm(world: World, cautioner: Entity, instigator: Entity, helper: Entity) -> None:
    world.say(
        f'"{instigator.id}, stop!" cried {cautioner.id}. "It\'s wobbling!" '
        f'Then both of them called, "{helper.label_word.capitalize()}, please come quick!"'
    )


def repair_success(world: World, helper: Entity, tool: Tool, animals: AnimalGroup, problem: Problem) -> None:
    trough = world.get("trough")
    trough.meters["dirty"] = 0.0
    trough.meters["blocked"] = 0.0
    trough.meters["wobble"] = 0.0
    trough.meters["sloshed"] = 0.0
    trough.meters["clean"] += 1
    trough.meters["full"] += 1
    animals.meters["thirst"] = 0.0
    animals.memes["worry"] = 0.0
    world.say(
        f'{helper.label_word.capitalize()} came fast with {tool.phrase} and {tool.success_text}. '
        f'The trough settled still; not a drop more was lost, and the clean water shone with a gloss.'
    )
    world.say(
        f'"There now," said the {helper.label_word}, "small hooves and small hands need a calmer command." '
        f'{animals.step_line.capitalize()} and drank in a line, each nose cool and grand.'
    )


def repair_fail(world: World, helper: Entity, tool: Tool, animals: AnimalGroup) -> None:
    trough = world.get("trough")
    trough.meters["tipped"] += 1
    trough.meters["empty"] += 1
    trough.meters["full"] = 0.0
    animals.meters["thirst"] += 1
    animals.memes["worry"] += 1
    world.say(
        f'{helper.label_word.capitalize()} came with {tool.phrase} and {tool.fail_text}. '
        f'But the trough lurched over with one muddy splash, and the last little puddle was spent.'
    )
    world.say(
        f'The ground drank the water before thirsty mouths could take one proper sup. '
        f'The {animals.label} stood waiting in a worried row while the pump had to fill the trough up.'
    )


def refill_after_tip(world: World, helper: Entity, animals: AnimalGroup) -> None:
    trough = world.get("trough")
    trough.meters["empty"] = 0.0
    trough.meters["tipped"] = 0.0
    trough.meters["wobble"] = 0.0
    trough.meters["clean"] += 1
    trough.meters["full"] += 1
    trough.meters["needs_fix"] = 0.0
    animals.meters["thirst"] = 0.0
    animals.memes["worry"] = 0.0
    world.say(
        f'So the {helper.label_word} pumped fresh water with a squeak and a song, '
        f'till the trough gleamed cool and deep. The children stood quiet and worked side by side, '
        f'for lessons that matter are lessons we keep.'
    )


def lesson(world: World, helper: Entity, instigator: Entity, cautioner: Entity) -> None:
    for kid in (instigator, cautioner):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["care"] += 1
    world.say(
        f'"When something is wobbly, muddy, or strange," said the {helper.label_word} with a smile, '
        f'"don\'t climb and don\'t thrash. Use patient hands, ask first for help, and wait just a little while."'
    )
    world.say(
        f'"We will," said {cautioner.id}. "{helper.label_word.capitalize()}, we will," '
        f'and {instigator.id} nodded too. The sharp little hurry had softened to thought, '
        f'and that was a kinder thing to do.'
    )


def ending_safe(world: World, instigator: Entity, cautioner: Entity, animals: AnimalGroup) -> None:
    for kid in (instigator, cautioner):
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
    world.say(
        f'Soon {animals.phrase} drank with a splash and a snuffle, content in the noon-day light. '
        f'"Hear that?" said {instigator.id}. "No worried murmur now." '
        f'"Only happy slurps," said {cautioner.id}. "And that sounds right."'
    )
    world.say(
        'They walked from the trough a little more slow, but also a little more wise, '
        'for asking before acting had turned the whole morning bright in their eyes.'
    )


def tell(
    yard: Yard,
    animals_cfg: AnimalGroup,
    problem: Problem,
    tool: Tool,
    instigator: str = "Nell",
    instigator_gender: str = "girl",
    cautioner: str = "Toby",
    cautioner_gender: str = "boy",
    trait: str = "careful",
    helper_type: str = "farmer_woman",
    delay: int = 0,
    instigator_age: int = 5,
    cautioner_age: int = 7,
    relation: str = "siblings",
) -> World:
    world = World()
    child_a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        role="instigator",
        age=instigator_age,
        attrs={"name": instigator, "relation": relation},
    ))
    child_b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"name": cautioner, "relation": relation},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label="the farmer",
        role="helper",
    ))
    animals = world.add(Entity(
        id="animals",
        type="animals",
        label=animals_cfg.label,
        movable=True,
        drinker=True,
    ))
    trough = world.add(Entity(
        id="trough",
        type="trough",
        label="the trough",
        movable=True,
    ))

    child_a.memes["boldness"] = BOLDNESS_INIT
    child_b.memes["steady"] = initial_steady(trait)
    trough.meters["full"] = 1.0
    trough.meters["clean"] = 1.0
    animals.meters["thirst"] = 1.0
    world.facts["delay"] = delay
    world.facts["relation"] = relation

    opening(world, child_a, child_b, yard, animals_cfg)
    world.para()
    notice_problem(world, child_b, problem, animals_cfg)
    tempt(world, child_a)
    warn(world, child_b, child_a, problem, helper)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, child_a, child_b, helper)
        world.para()
        repair_success(world, helper, tool, animals_cfg, problem)
        world.para()
        lesson(world, helper, child_a, child_b)
        ending_safe(world, child_a, child_b, animals_cfg)
        outcome = "averted"
    else:
        world.para()
        climb(world, child_a)
        alarm(world, child_b, child_a, helper)
        contained = is_contained(tool, problem, delay)
        world.para()
        if contained:
            repair_success(world, helper, tool, animals_cfg, problem)
            world.para()
            lesson(world, helper, child_a, child_b)
            ending_safe(world, child_a, child_b, animals_cfg)
            outcome = "contained"
        else:
            repair_fail(world, helper, tool, animals_cfg)
            world.para()
            refill_after_tip(world, helper, animals_cfg)
            lesson(world, helper, child_a, child_b)
            world.para()
            ending_safe(world, child_a, child_b, animals_cfg)
            outcome = "tipped"

    world.facts.update(
        yard=yard,
        animals_cfg=animals_cfg,
        problem=problem,
        tool=tool,
        instigator=child_a,
        cautioner=child_b,
        helper=helper,
        animals=animals,
        trough=trough,
        outcome=outcome,
        averted=(outcome == "averted"),
        contained=(outcome == "contained"),
        tipped=(outcome == "tipped"),
        severity=spill_severity(problem, delay),
        predicted_wobble=world.facts.get("predicted_wobble", 0.0),
    )
    return world


YARDS = {
    "barnyard": Yard(
        id="barnyard",
        place="the barnyard",
        sky="butter-blue",
        ground="the straw and stones",
        tags={"farm"},
    ),
    "orchard": Yard(
        id="orchard",
        place="the orchard lane",
        sky="apple-bright",
        ground="the grass by the fence",
        tags={"farm", "orchard"},
    ),
    "meadow": Yard(
        id="meadow",
        place="the meadow gate",
        sky="cloud-soft",
        ground="the clover path",
        tags={"farm", "meadow"},
    ),
}

ANIMALS = {
    "ducklings": AnimalGroup(
        id="ducklings",
        label="ducklings",
        phrase="a row of ducklings",
        sound="peep-peep",
        drink_style="dabbling beaks",
        step_line="they bobbed their heads",
        tags={"ducklings", "trough", "water"},
    ),
    "lambs": AnimalGroup(
        id="lambs",
        label="lambs",
        phrase="two woolly lambs",
        sound="maa-maa",
        drink_style="soft pink mouths",
        step_line="they trotted close",
        tags={"lambs", "trough", "water"},
    ),
    "calves": AnimalGroup(
        id="calves",
        label="calves",
        phrase="three patchy calves",
        sound="moo-moo",
        drink_style="velvet noses",
        step_line="they clopped in gently",
        tags={"calves", "trough", "water"},
    ),
}

PROBLEMS = {
    "hay_clump": Problem(
        id="hay_clump",
        label="hay clump",
        murmur_line="worried murmur",
        look_line="A wad of hay is floating thick, and nobody wants that to drink.",
        risk_line="If you jolt it, more muck may swirl through the water.",
        actions={"scoop", "brush"},
        severity=2,
        tags={"hay", "clean_water"},
    ),
    "leaf_drift": Problem(
        id="leaf_drift",
        label="leaf drift",
        murmur_line="soft murmur",
        look_line="Brown leaves are crowding the edge, and the water looks tired and thin.",
        risk_line="One hard shove could spill the whole thing sideways.",
        actions={"scoop", "brush"},
        severity=1,
        tags={"leaves", "clean_water"},
    ),
    "mud_swirl": Problem(
        id="mud_swirl",
        label="mud swirl",
        murmur_line="low murmur",
        look_line="Mud has gone cloudy in circles, and clean sips cannot begin.",
        risk_line="If you stomp at it, the trough will turn murkier and tip.",
        actions={"rinse"},
        severity=3,
        tags={"mud", "clean_water"},
    ),
}

TOOLS = {
    "scoop_bucket": Tool(
        id="scoop_bucket",
        label="bucket",
        phrase="a little scoop bucket",
        action="scoop",
        sense=3,
        power=3,
        success_text="skimmed the mess away with careful lifts",
        fail_text="tried to scoop the mess away, but the rim lurched before the bucket could help",
        qa_text="used a little scoop bucket to lift the mess out",
        tags={"bucket", "cleaning"},
    ),
    "long_brush": Tool(
        id="long_brush",
        label="brush",
        phrase="a long trough brush",
        action="brush",
        sense=3,
        power=2,
        success_text="drew the leaves and hay to one side and swept the water clear",
        fail_text="reached with the brush, but the wobble had already grown too big",
        qa_text="used a long trough brush to sweep the mess aside",
        tags={"brush", "cleaning"},
    ),
    "rinse_pail": Tool(
        id="rinse_pail",
        label="pail",
        phrase="a clean rinse pail",
        action="rinse",
        sense=3,
        power=4,
        success_text="poured fresh water through the trough until the mud washed away",
        fail_text="started rinsing, but the trough tipped before the muddy water could clear",
        qa_text="rinsed the trough with fresh water until it cleared",
        tags={"pail", "cleaning"},
    ),
    "poke_stick": Tool(
        id="poke_stick",
        label="stick",
        phrase="a poking stick",
        action="poke",
        sense=1,
        power=1,
        success_text="jabbed at the mess until, by luck, some of it moved",
        fail_text="poked at the mess, which only made the trough wobble worse",
        qa_text="poked at the mess with a stick",
        tags={"stick"},
    ),
}

GIRL_NAMES = ["Nell", "Mira", "June", "Ava", "Elsie", "Ruby"]
BOY_NAMES = ["Toby", "Finn", "Milo", "Benji", "Otis", "Jude"]
TRAITS = ["careful", "patient", "steady", "thoughtful", "curious", "brisk"]


@dataclass
class StoryParams:
    yard: str
    animal: str
    problem: str
    tool: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    helper: str
    trait: str
    delay: int = 0
    instigator_age: int = 5
    cautioner_age: int = 7
    relation: str = "siblings"
    seed: Optional[int] = None
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
    "trough": [
        (
            "What is a trough?",
            "A trough is a long container that holds water or food for farm animals. Animals stand beside it to drink or eat."
        )
    ],
    "clean_water": [
        (
            "Why do animals need clean water?",
            "Animals need clean water so they can drink safely and stay healthy. Dirty water can taste bad and may not be safe to drink."
        )
    ],
    "ducklings": [
        (
            "How do ducklings drink?",
            "Ducklings dip their little beaks into water and sip small mouthfuls. They need water low enough and clean enough for their beaks."
        )
    ],
    "lambs": [
        (
            "What sound does a lamb make?",
            "A lamb often says 'maa' in a soft voice. It is the young of a sheep."
        )
    ],
    "calves": [
        (
            "What is a calf?",
            "A calf is a young cow. Calves often drink with soft noses and big careful sips."
        )
    ],
    "bucket": [
        (
            "What is a bucket used for?",
            "A bucket carries water or loose things from one place to another. On a farm, it can help scoop or carry water."
        )
    ],
    "brush": [
        (
            "What does a brush do?",
            "A brush sweeps dirt, hay, or leaves where hands cannot easily reach. A long brush helps someone clean without climbing in."
        )
    ],
    "pail": [
        (
            "What is a pail?",
            "A pail is another word for a bucket. People use it to carry water."
        )
    ],
    "ask_help": [
        (
            "Why is it good to ask for help?",
            "Asking for help lets a bigger problem get solved safely. It can stop a small wobble from turning into a bigger mess."
        )
    ],
}
KNOWLEDGE_ORDER = ["trough", "clean_water", "ducklings", "lambs", "calves", "bucket", "brush", "pail", "ask_help"]


def relation_pair(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    yard = f["yard"]
    animals = f["animals_cfg"]
    problem = f["problem"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a short rhyming farm story for a 3-to-5-year-old that includes the words "murmur" and "trough" and uses dialogue.',
            f"Tell a rhyming story where {a.label} wants to climb onto a trough to help {animals.label}, but {b.label} talks {a.pronoun('object')} into asking for help first.",
            f"Write a gentle story in {yard.place} with dialogue, thirsty {animals.label}, a worried murmur, and a happy ending where no spill happens.",
        ]
    if outcome == "tipped":
        return [
            f'Write a rhyming story with dialogue where children try to help thirsty {animals.label} at a trough, but a wobble turns into a spill before the farmer fixes it.',
            f"Tell a farm story for young children that includes the words murmur and trough, with one child rushing and another warning, then a calm refill at the end.",
            f"Write a cautionary but gentle rhyming story in which {problem.label} makes the trough hard to use and a hurried choice makes more work.",
        ]
    return [
        f'Write a short rhyming story with dialogue that includes the words "murmur" and "trough".',
        f"Tell a farmyard story where {animals.label} are thirsty, one child rushes, another child warns them, and a farmer uses the right tool to help.",
        f"Write a child-facing rhyming tale set in {yard.place} with a worried murmur, a wobbling trough, and a calm, helpful ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    helper = f["helper"]
    animals = f["animals_cfg"]
    problem = f["problem"]
    tool = f["tool"]
    relation = f["relation"]
    pair = relation_pair(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.label} and {b.label}, and the thirsty {animals.label} by the trough. The farmer also helps when the children call."
        ),
        (
            "What was wrong at the trough?",
            f"There was a {problem.label} at the trough, so the water did not look right for drinking. That trouble made the animals gather in a worried murmur."
        ),
        (
            f"Why did {b.label} tell {a.label} not to climb on the rim?",
            f"{b.label} thought the trough might wobble or tip if someone climbed on it. {b.pronoun('subject').capitalize()} wanted to protect both the water and the thirsty animals."
        ),
    ]
    outcome = f["outcome"]
    if outcome == "averted":
        qa.append((
            f"What did {a.label} do after the warning?",
            f"{a.label} backed away from the rim and chose to ask the farmer for help instead. That kept the trough steady before any bigger mess could begin."
        ))
        qa.append((
            "How was the problem solved?",
            f"The farmer {tool.qa_text}. Because the children asked before acting, the water stayed in the trough and the animals could drink sooner."
        ))
    elif outcome == "contained":
        qa.append((
            "Did the trough spill over?",
            f"No, not all the way. It wobbled when {a.label} climbed up, but the farmer arrived in time and fixed the problem before the trough tipped."
        ))
        qa.append((
            f"How did the farmer fix it?",
            f'The farmer {tool.qa_text}. That was the right method for the {problem.label}, so the water became calm and clean again.'
        ))
    else:
        qa.append((
            "What happened when the fix was too late?",
            f"The trough tipped and the water splashed out before the problem could be fixed. That meant the animals had to wait while the farmer pumped fresh water back in."
        ))
        qa.append((
            "How did the story still end safely?",
            f"After the spill, the farmer refilled the trough and the children helped calmly. The ending shows they learned to ask for help before rushing."
        ))
    qa.append((
        "What lesson did the children learn?",
        "They learned that rushing at a wobbly problem can make it worse. Asking for help and using patient hands is safer and kinder."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"trough", "clean_water", "ask_help"}
    tags |= set(f["animals_cfg"].tags)
    tags |= set(f["problem"].tags)
    tags |= set(f["tool"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        yard="barnyard",
        animal="ducklings",
        problem="leaf_drift",
        tool="long_brush",
        instigator="Nell",
        instigator_gender="girl",
        cautioner="Toby",
        cautioner_gender="boy",
        helper="farmer_woman",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
    ),
    StoryParams(
        yard="orchard",
        animal="lambs",
        problem="hay_clump",
        tool="scoop_bucket",
        instigator="Milo",
        instigator_gender="boy",
        cautioner="Ruby",
        cautioner_gender="girl",
        helper="farmer_man",
        trait="thoughtful",
        delay=0,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
    ),
    StoryParams(
        yard="meadow",
        animal="calves",
        problem="mud_swirl",
        tool="rinse_pail",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Finn",
        cautioner_gender="boy",
        helper="farmer_woman",
        trait="steady",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
    ),
    StoryParams(
        yard="barnyard",
        animal="ducklings",
        problem="hay_clump",
        tool="long_brush",
        instigator="Jude",
        instigator_gender="boy",
        cautioner="Mira",
        cautioner_gender="girl",
        helper="farmer_man",
        trait="curious",
        delay=2,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
    ),
]


def explain_rejection(problem: Problem, tool: Tool) -> str:
    if tool.sense < SENSE_MIN:
        return (
            f"(Refusing tool '{tool.id}': it scores too low on common sense "
            f"(sense={tool.sense} < {SENSE_MIN}). A poking stick is more likely to make a trough wobble than to solve the problem.)"
        )
    if not tool_fits(problem, tool):
        needed = " / ".join(sorted(problem.actions))
        return (
            f"(No story: {tool.label} does not honestly fix {problem.label}. "
            f"This problem needs a tool with action {needed}.)"
        )
    return "(No valid combination matches the given options.)"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    tool = TOOLS[params.tool]
    problem = PROBLEMS[params.problem]
    return "contained" if is_contained(tool, problem, params.delay) else "tipped"


ASP_RULES = r"""
% --- valid story gate ------------------------------------------------------
trouble(P) :- problem(P).
sensible(T) :- tool(T), sense(T, S), sense_min(M), S >= M.
fits(P, T) :- problem(P), tool(T), needs(P, A), action(T, A).
valid(Y, A, P) :- yard(Y), animal(A), trouble(P).

% --- outcome model ---------------------------------------------------------
steady_now(T) :- trait(T), steady_trait(T).
init_steady(5) :- trait(T), steady_now(T).
init_steady(3) :- trait(T), not steady_now(T).

older_guard :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(3) :- older_guard.
bonus(0) :- not older_guard.
authority(S + 1 + B) :- init_steady(S), bonus(B).
averted :- older_guard, authority(A), boldness_init(B), A > B.

severity(V + D) :- chosen_problem(P), problem_severity(P, V), delay(D).
tool_power(Pw) :- chosen_tool(T), power(T, Pw).
contained :- fits(chosen_problem_id, chosen_tool_id), tool_power(Pw), severity(Sv), Pw >= Sv.

chosen_problem_id(P) :- chosen_problem(P).
chosen_tool_id(T) :- chosen_tool(T).

outcome(averted) :- averted.
outcome(contained) :- not averted, fits(chosen_problem_id, chosen_tool_id), contained.
outcome(tipped) :- not averted, fits(chosen_problem_id, chosen_tool_id), not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for yard_id in YARDS:
        lines.append(asp.fact("yard", yard_id))
    for animal_id in ANIMALS:
        lines.append(asp.fact("animal", animal_id))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("problem_severity", problem_id, problem.severity))
        for action in sorted(problem.actions):
            lines.append(asp.fact("needs", problem_id, action))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        lines.append(asp.fact("power", tool_id, tool.power))
        lines.append(asp.fact("action", tool_id, tool.action))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    for trait in sorted(STEADY_TRAITS):
        lines.append(asp.fact("steady_trait", trait))
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


def asp_fits(problem_id: str) -> list[str]:
    import asp

    extra = asp.fact("chosen_problem", problem_id)
    model = asp.one_model(asp_program(extra, "#show fits/2."))
    return sorted(t for (p, t) in asp.atoms(model, "fits") if p == problem_id)


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_tool", params.tool),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    cl_valid = set(asp_valid_combos())
    if py_valid == cl_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl_valid - py_valid:
            print("  only in clingo:", sorted(cl_valid - py_valid))
        if py_valid - cl_valid:
            print("  only in python:", sorted(py_valid - cl_valid))

    py_sensible = {tool.id for tool in sensible_tools()}
    cl_sensible = set(asp_sensible())
    if py_sensible == cl_sensible:
        print(f"OK: sensible tools match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: clingo={sorted(cl_sensible)} python={sorted(py_sensible)}")

    fit_bad = 0
    for pid, problem in PROBLEMS.items():
        py = sorted(tid for tid, tool in TOOLS.items() if tool_fits(problem, tool))
        cl = asp_fits(pid)
        if py != cl:
            fit_bad += 1
            print(f"MISMATCH in tool fit for {pid}: clingo={cl} python={py}")
    if fit_bad == 0:
        print(f"OK: tool-fit model matches for {len(PROBLEMS)} problems.")
    else:
        rc = 1

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if params.tool not in TOOLS or params.problem not in PROBLEMS:
            continue
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        assert sample.story
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: generate/emit smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming farm story world: a worried murmur, a trough, and a calmer choice."
    )
    ap.add_argument("--yard", choices=YARDS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=["farmer_woman", "farmer_man"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.tool:
        problem = PROBLEMS[args.problem]
        tool = TOOLS[args.tool]
        if tool.sense < SENSE_MIN or not tool_fits(problem, tool):
            raise StoryError(explain_rejection(problem, tool))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        problem = PROBLEMS[args.problem] if args.problem else next(iter(PROBLEMS.values()))
        raise StoryError(explain_rejection(problem, TOOLS[args.tool]))

    combos = [
        combo for combo in valid_combos()
        if (args.yard is None or combo[0] == args.yard)
        and (args.animal is None or combo[1] == args.animal)
        and (args.problem is None or combo[2] == args.problem)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    yard_id, animal_id, problem_id = rng.choice(sorted(combos))
    problem = PROBLEMS[problem_id]

    if args.tool:
        if not tool_fits(problem, TOOLS[args.tool]) or TOOLS[args.tool].sense < SENSE_MIN:
            raise StoryError(explain_rejection(problem, TOOLS[args.tool]))
        tool_id = args.tool
    else:
        fitting = [
            tid for tid, tool in TOOLS.items()
            if tool.sense >= SENSE_MIN and tool_fits(problem, tool)
        ]
        if not fitting:
            raise StoryError("(No sensible tool fits the chosen problem.)")
        tool_id = rng.choice(sorted(fitting))

    instigator, ig = _pick_child(rng)
    cautioner, cg = _pick_child(rng, avoid=instigator)
    helper = args.helper or rng.choice(["farmer_woman", "farmer_man"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)

    return StoryParams(
        yard=yard_id,
        animal=animal_id,
        problem=problem_id,
        tool=tool_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        helper=helper,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.yard not in YARDS:
        raise StoryError(f"(Unknown yard: {params.yard})")
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal group: {params.animal})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.helper not in {"farmer_woman", "farmer_man"}:
        raise StoryError(f"(Unknown helper type: {params.helper})")

    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    if tool.sense < SENSE_MIN or not tool_fits(problem, tool):
        raise StoryError(explain_rejection(problem, tool))

    world = tell(
        yard=YARDS[params.yard],
        animals_cfg=ANIMALS[params.animal],
        problem=problem,
        tool=tool,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        helper_type=params.helper,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show fits/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (yard, animal, problem) combos:\n")
        for yard, animal, problem in combos:
            fits = [tid for tid, tool in TOOLS.items() if tool.sense >= SENSE_MIN and tool_fits(PROBLEMS[problem], tool)]
            print(f"  {yard:9} {animal:10} {problem:10} [{', '.join(sorted(fits))}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = (
                f"### {p.instigator} & {p.cautioner}: {p.problem} at the {p.yard} "
                f"({p.animal}, {p.tool}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
