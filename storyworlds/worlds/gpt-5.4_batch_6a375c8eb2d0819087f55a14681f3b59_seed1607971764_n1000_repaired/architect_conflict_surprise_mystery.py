#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/architect_conflict_surprise_mystery.py
=================================================================

A standalone story world for a tiny child-facing mystery about an architect,
a quarrel over a missing model, and a surprise that turns the conflict into a
kind ending.

Premise
-------
A child visits a bright studio where an architect is preparing a small model for
the town fair. The model seems to be missing or damaged. Suspicion falls on a
helper, feelings rise, and the child investigates simple clues. The mystery has
a grounded solution: the model was moved for a practical reason, not stolen.
A surprise gift or reveal at the end proves what changed.

Run it
------
python storyworlds/worlds/gpt-5.4/architect_conflict_surprise_mystery.py
python storyworlds/worlds/gpt-5.4/architect_conflict_surprise_mystery.py --place studio --problem moved
python storyworlds/worlds/gpt-5.4/architect_conflict_surprise_mystery.py --helper rival
python storyworlds/worlds/gpt-5.4/architect_conflict_surprise_mystery.py --all
python storyworlds/worlds/gpt-5.4/architect_conflict_surprise_mystery.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/architect_conflict_surprise_mystery.py --trace --seed 777
python storyworlds/worlds/gpt-5.4/architect_conflict_surprise_mystery.py --json
python storyworlds/worlds/gpt-5.4/architect_conflict_surprise_mystery.py --verify
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
KIND_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    movable: bool = False
    fragile: bool = False
    helpful: bool = False
    # physical and emotional state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Place:
    id: str
    label: str
    opening: str
    sound: str
    hiding_spot: str
    ending_image: str
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
class Problem:
    id: str
    label: str
    visible_sign: str
    true_cause: str
    clue: str
    moved_not_stolen: bool
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
class HelperRole:
    id: str
    label: str
    relation: str
    kindness: int
    reveal_line: str
    surprise_gift: str
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
class SearchTool:
    id: str
    label: str
    action: str
    clue_text: str
    safe_for_fragile: bool
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return World(
            entities=copy.deepcopy(self.entities),
            fired=set(self.fired),
            paragraphs=[[]],
            facts=copy.deepcopy(self.facts),
        )
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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    architect = world.get("architect")
    helper = world.get("helper")
    model = world.get("model")
    if architect.memes["accusing"] >= THRESHOLD and helper.memes["hurt"] < THRESHOLD:
        sig = ("conflict", helper.id)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["hurt"] += 1
            child.memes["worry"] += 1
            world.facts["conflict_happened"] = True
            out.append("__conflict__")
    if model.meters["found"] >= THRESHOLD and architect.memes["accusing"] >= THRESHOLD:
        sig = ("apology_ready", architect.id)
        if sig not in world.fired:
            world.fired.add(sig)
            architect.memes["regret"] += 1
            out.append("__regret__")
    return out


def _r_mystery(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("clue_seen") and not world.facts.get("solution_ready"):
        sig = ("solution", "ready")
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["solution_ready"] = True
            world.get("child").memes["curiosity"] += 1
            out.append("__solution__")
    return out


CAUSAL_RULES = [
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="mystery", tag="reasoning", apply=_r_mystery),
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
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "studio": Place(
        id="studio",
        label="the architect's studio",
        opening="sunlight made bright squares on the floor",
        sound="paper whispered under careful hands",
        hiding_spot="a tall shelf beside the rolled blueprints",
        ending_image="the little house model glowed under a warm lamp",
        tags={"studio", "blueprint"},
    ),
    "library": Place(
        id="library",
        label="the library craft room",
        opening="dusty light floated above the tables",
        sound="pages rustled and a clock ticked softly",
        hiding_spot="the map cabinet near the window",
        ending_image="the tiny town square stood neat beside a stack of books",
        tags={"library", "blueprint"},
    ),
    "hall": Place(
        id="hall",
        label="the town hall workshop",
        opening="the long room smelled like wood and clean glue",
        sound="a vent hummed over the workbench",
        hiding_spot="a high cupboard above the measuring tools",
        ending_image="the little bridge model shone by the open door",
        tags={"hall", "blueprint"},
    ),
}

PROBLEMS = {
    "moved": Problem(
        id="moved",
        label="missing",
        visible_sign="the model was gone from the middle table",
        true_cause="it had been moved away from a leaky window",
        clue="a line of raindrops on the table led toward the safer corner",
        moved_not_stolen=True,
        severity=1,
        tags={"moved", "rain", "mystery"},
    ),
    "covered": Problem(
        id="covered",
        label="missing",
        visible_sign="the model could not be seen anywhere on the workbench",
        true_cause="it had been tucked under a dust cloth to protect wet paint",
        clue="a corner of painted cardboard peeked out from under the cloth",
        moved_not_stolen=True,
        severity=1,
        tags={"covered", "paint", "mystery"},
    ),
    "cracked": Problem(
        id="cracked",
        label="ruined",
        visible_sign="one tiny tower was bent and the front door had fallen off",
        true_cause="the model had slipped when it was moved to safety",
        clue="a careful trail of glue dots led to the shelf where it had been repaired",
        moved_not_stolen=False,
        severity=2,
        tags={"cracked", "glue", "mystery"},
    ),
}

HELPERS = {
    "apprentice": HelperRole(
        id="apprentice",
        label="the architect's apprentice",
        relation="apprentice",
        kindness=3,
        reveal_line="I only wanted to keep the model safe until the paint dried.",
        surprise_gift="a tiny paper lamp for the model house",
        tags={"apprentice", "helper"},
    ),
    "caretaker": HelperRole(
        id="caretaker",
        label="the hall caretaker",
        relation="caretaker",
        kindness=3,
        reveal_line="I moved it because the window was dripping, and I did not want it to get spoiled.",
        surprise_gift="a little brass bell for the model door",
        tags={"caretaker", "helper"},
    ),
    "rival": HelperRole(
        id="rival",
        label="a young architect from the next table",
        relation="rival",
        kindness=2,
        reveal_line="I sounded cross before, but I never took it. I hid it under the cloth so nobody would smear the fresh paint.",
        surprise_gift="a neat paper flag for the roof",
        tags={"rival", "helper", "conflict"},
    ),
}

TOOLS = {
    "magnifier": SearchTool(
        id="magnifier",
        label="magnifying glass",
        action="knelt down and looked closely",
        clue_text="Through the magnifying glass, the small clue stopped looking messy and started looking meaningful.",
        safe_for_fragile=True,
        tags={"magnifier", "clue"},
    ),
    "flashlight": SearchTool(
        id="flashlight",
        label="flashlight",
        action="shined a soft circle of light under the tables",
        clue_text="The flashlight made a hidden edge shine in the dim corner.",
        safe_for_fragile=True,
        tags={"flashlight", "clue"},
    ),
    "ruler": SearchTool(
        id="ruler",
        label="ruler",
        action="used a ruler to point without touching",
        clue_text="Using the ruler kept curious fingers away from the fragile parts while the clue was checked.",
        safe_for_fragile=True,
        tags={"ruler", "clue"},
    ),
    "broom": SearchTool(
        id="broom",
        label="broom",
        action="swept around in a hurry",
        clue_text="The broom pushed paper scraps around, but it was too clumsy for a delicate mystery.",
        safe_for_fragile=False,
        tags={"broom"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Zoe", "Ava", "Ivy", "Nora", "Ella", "Lucy"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Eli", "Theo", "Finn", "Noah"]
ARCHITECT_NAMES = ["Arun", "Mina", "Tomas", "Clara", "Omar", "Sana"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for problem_id, problem in PROBLEMS.items():
            for helper_id, helper in HELPERS.items():
                for tool_id, tool in TOOLS.items():
                    if mystery_reasonable(problem, helper, tool):
                        combos.append((place_id, problem_id, helper_id, tool_id))
    return combos


def mystery_reasonable(problem: Problem, helper: HelperRole, tool: SearchTool) -> bool:
    if not tool.safe_for_fragile:
        return False
    if problem.id == "cracked" and helper.kindness < KIND_MIN:
        return False
    return True


def explain_rejection(problem: Problem, helper: HelperRole, tool: SearchTool) -> str:
    if not tool.safe_for_fragile:
        return (
            f"(No story: a {tool.label} is too clumsy around a delicate model. "
            f"This mystery needs a careful search tool, not something that might bump the evidence.)"
        )
    if problem.id == "cracked" and helper.kindness < KIND_MIN:
        return (
            f"(No story: the {helper.label} is not kind enough for the cracked-model version. "
            f"This world only tells repairable conflicts that can end in a sincere apology.)"
        )
    return "(No story: this combination does not fit the mystery logic.)"


def predict_solution(problem: Problem, tool: SearchTool) -> dict:
    return {
        "findable": tool.safe_for_fragile,
        "clue": problem.clue,
        "moved_not_stolen": problem.moved_not_stolen,
    }


def introduce(world: World, place: Place, child: Entity, architect: Entity, model: Entity) -> None:
    world.say(
        f"{child.id} visited {place.label} one gray afternoon. {place.opening}, and {place.sound}."
    )
    world.say(
        f"At the biggest table stood {architect.id}, an architect, beside {model.label}. "
        f"The small building had paper windows, tiny steps, and a roof no bigger than two hands."
    )


def admire(world: World, child: Entity, architect: Entity, place: Place) -> None:
    child.memes["wonder"] += 1
    architect.memes["pride"] += 1
    world.say(
        f'{architect.id} smiled and said, "I built this model for the town fair." '
        f"{child.id} loved how serious and secret the room felt, as if every ruler and roll of paper knew a clue."
    )


def problem_appears(world: World, architect: Entity, problem: Problem) -> None:
    world.say(
        f"But when {architect.id} turned back to the table, {problem.visible_sign}. "
        f'"Oh no," {architect.pronoun()} whispered.'
    )


def accuse(world: World, architect: Entity, helper: Entity, helper_cfg: HelperRole) -> None:
    architect.memes["accusing"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{architect.id} looked at {helper.id}, {helper_cfg.label}, and said, '
        f'"Did you take it?"'
    )
    if helper_cfg.relation == "rival":
        world.say(
            f"{helper.id}'s eyebrows jumped. The room suddenly felt sharper and colder."
        )
    else:
        world.say(
            f"{helper.id} looked hurt and shook {helper.pronoun('possessive')} head at once."
        )


def child_steps_in(world: World, child: Entity, architect: Entity) -> None:
    child.memes["brave"] += 1
    world.say(
        f'{child.id} tugged gently at {architect.id}\'s sleeve. "Maybe we should look for a clue first," '
        f"{child.pronoun()} said."
    )


def search(world: World, child: Entity, tool_cfg: SearchTool, place: Place, problem: Problem) -> None:
    world.facts["searched_with"] = tool_cfg.id
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} {tool_cfg.action}. {tool_cfg.clue_text}"
    )
    world.say(
        f"Near {place.hiding_spot}, {child.pronoun()} noticed {problem.clue}."
    )
    world.facts["clue_seen"] = True
    propagate(world, narrate=False)


def solve_mystery(world: World, child: Entity, architect: Entity, helper: Entity,
                  helper_cfg: HelperRole, place: Place, problem: Problem, model: Entity) -> None:
    model.meters["found"] += 1
    if problem.id == "moved":
        model.meters["safe"] += 1
        world.say(
            f'"The model was not stolen," {child.id} said. "It was moved because of the rain." '
            f"There, on {place.hiding_spot}, the little building sat dry and safe."
        )
    elif problem.id == "covered":
        model.meters["safe"] += 1
        world.say(
            f'{child.id} lifted one corner of the cloth. Under it waited the missing model. '
            f'"It was hiding, not gone," {child.pronoun()} said.'
        )
    else:
        model.meters["repaired"] += 1
        model.meters["safe"] += 1
        world.say(
            f"On {place.hiding_spot}, the model stood with its tiny tower straight again. "
            f"The little door had been glued back carefully."
        )
        world.say(
            f'"It was hurt, but someone tried to mend it," {child.id} said.'
        )
    propagate(world, narrate=False)
    world.facts["solution"] = problem.true_cause
    world.facts["found_by_child"] = True
    world.facts["surprise_gift"] = helper_cfg.surprise_gift


def reveal_and_apology(world: World, architect: Entity, helper: Entity,
                       helper_cfg: HelperRole, problem: Problem) -> None:
    helper.memes["honest"] += 1
    architect.memes["accusing"] = 0.0
    architect.memes["sorry"] += 1
    helper.memes["hurt"] = 0.0
    world.say(
        f'"{helper_cfg.reveal_line}" {helper.id} said.'
    )
    world.say(
        f'{architect.id} let out a long breath. "I am sorry I blamed you before I knew the truth," '
        f"{architect.pronoun()} said."
    )
    if problem.id == "cracked":
        world.say(
            f"{helper.id} nodded. The hard part of the mystery was not the cracked tower anymore. It was the feeling that came from being blamed."
        )


def surprise_ending(world: World, child: Entity, architect: Entity, helper: Entity,
                    helper_cfg: HelperRole, place: Place, problem: Problem, model: Entity) -> None:
    child.memes["joy"] += 1
    architect.memes["gratitude"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"Then came the surprise. {helper.id} reached into a paper box and took out {helper_cfg.surprise_gift}."
    )
    world.say(
        f'"For the best detective in the room," {helper.pronoun()} said, handing it to {child.id}.'
    )
    world.say(
        f"Together they placed it on the model, and suddenly the whole little building looked finished. "
        f"{place.ending_image}. The mystery was over, and the room felt gentle again."
    )
    world.facts["outcome"] = "reconciled"
    world.facts["gift_used"] = True


def tell(place: Place, problem: Problem, helper_cfg: HelperRole, tool_cfg: SearchTool,
         child_name: str = "Lina", child_gender: str = "girl",
         architect_name: str = "Mina", architect_gender: str = "woman",
         helper_name: str = "Jae", helper_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(
        id=child_name, kind="character", type=child_gender, role="child",
        traits=["curious"], attrs={}
    ))
    architect = world.add(Entity(
        id=architect_name, kind="character", type=architect_gender, role="architect",
        traits=["careful"], attrs={}
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type=helper_gender, role="helper",
        traits=[helper_cfg.relation], helpful=helper_cfg.kindness >= KIND_MIN, attrs={}
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, role="parent",
        label="the parent", attrs={}
    ))
    model = world.add(Entity(
        id="model", kind="thing", type="model", label="the tiny town model",
        role="object", movable=True, fragile=True, attrs={}
    ))

    world.facts.update(
        place=place,
        problem_cfg=problem,
        helper_cfg=helper_cfg,
        tool_cfg=tool_cfg,
        clue_seen=False,
        solution_ready=False,
        conflict_happened=False,
        outcome="mystery",
    )

    introduce(world, place, child, architect, model)
    admire(world, child, architect, place)

    world.para()
    problem_appears(world, architect, problem)
    accuse(world, architect, helper, helper_cfg)
    child_steps_in(world, child, architect)

    world.para()
    search(world, child, tool_cfg, place, problem)
    solve_mystery(world, child, architect, helper, helper_cfg, place, problem, model)

    world.para()
    reveal_and_apology(world, architect, helper, helper_cfg, problem)
    surprise_ending(world, child, architect, helper, helper_cfg, place, problem, model)

    world.facts.update(
        child=child,
        architect=architect,
        helper=helper,
        parent=parent,
        model=model,
        conflict=world.facts.get("conflict_happened", False),
        solved=model.meters["found"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "architect": [
        (
            "What does an architect do?",
            "An architect plans buildings before they are made. Architects draw ideas, measure carefully, and think about how rooms and walls should fit together."
        )
    ],
    "blueprint": [
        (
            "What is a blueprint?",
            "A blueprint is a careful plan for building something. It shows where parts should go before anyone starts the real work."
        )
    ],
    "magnifier": [
        (
            "What is a magnifying glass for?",
            "A magnifying glass helps you see tiny things more clearly. It is useful when a clue is small and easy to miss."
        )
    ],
    "flashlight": [
        (
            "Why can a flashlight help in a mystery?",
            "A flashlight shines light into dark corners. That can help you notice something hidden without touching it first."
        )
    ],
    "ruler": [
        (
            "Why would someone point with a ruler instead of a finger?",
            "A ruler can help someone point from a little distance away. That is useful when an object is fragile and should not be bumped."
        )
    ],
    "repair": [
        (
            "What does it mean to repair something?",
            "To repair something means to fix it after it is damaged. A careful repair tries to make the object safe and useful again."
        )
    ],
    "apology": [
        (
            "What is an apology?",
            "An apology is when you say you are sorry for something hurtful or unfair. A real apology tries to mend feelings, not just end the trouble."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. One clue may seem tiny, but it can lead to the truth."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "architect",
    "blueprint",
    "clue",
    "magnifier",
    "flashlight",
    "ruler",
    "repair",
    "apology",
]


@dataclass
class StoryParams:
    place: str
    problem: str
    helper: str
    tool: str
    child_name: str
    child_gender: str
    architect_name: str
    architect_gender: str
    helper_name: str
    helper_gender: str
    parent: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    architect = f["architect"]
    helper_cfg = f["helper_cfg"]
    place = f["place"]
    problem = f["problem_cfg"]
    return [
        (
            f'Write a gentle mystery story for a 3-to-5-year-old that includes the word "architect". '
            f"The setting is {place.label}, a model seems {problem.label}, and a child helps solve the problem."
        ),
        (
            f"Tell a mystery where {architect.id}, an architect, wrongly suspects {helper_cfg.label}, "
            f"but {child.id} follows a clue and finds a kinder truth."
        ),
        (
            f"Write a short story with conflict and surprise: a missing little building model, an apology, "
            f"and a final gift that makes the ending feel warm instead of scary."
        ),
    ]


def pair_word(entity: Entity) -> str:
    return "girl" if entity.type == "girl" else "boy" if entity.type == "boy" else "child"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    architect = f["architect"]
    helper = f["helper"]
    helper_cfg = f["helper_cfg"]
    place = f["place"]
    problem = f["problem_cfg"]
    tool_cfg = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a curious {pair_word(child)}, an architect named {architect.id}, and {helper.id}, {helper_cfg.label}. "
            f"They are all in {place.label} when the mystery begins."
        ),
        (
            f"What was the mystery?",
            f"The mystery was that {problem.visible_sign}. That made {architect.id} fear something had gone wrong with the fair model."
        ),
        (
            f"Why did the room feel tense?",
            f"The room felt tense because {architect.id} blamed {helper.id} before the truth was known. "
            f"That hurt feelings and turned a missing-model problem into a real conflict."
        ),
        (
            f"How did {child.id} help solve it?",
            f"{child.id} used the {tool_cfg.label} carefully and noticed a clue near {place.hiding_spot}. "
            f"The careful search mattered because the model was fragile, so solving the mystery meant looking closely instead of grabbing at things."
        ),
        (
            f"What was really happening to the model?",
            f"The model was not simply gone for no reason. {problem.true_cause}, and the clue pointed to that truth."
        ),
        (
            f"How was the conflict fixed?",
            f"The conflict was fixed when {helper.id} explained what had happened and {architect.id} apologized. "
            f"Once the truth came out, the problem was no longer about blame but about understanding."
        ),
        (
            "What was the surprise at the end?",
            f"The surprise was that {helper.id} gave {child.id} {helper_cfg.surprise_gift}. "
            f"Adding it to the model turned the solved mystery into a happy ending everyone could see."
        ),
    ]
    if problem.id == "cracked":
        qa.append(
            (
                "Was the model perfect when they found it?",
                f"No. One part had been damaged, but it had also been carefully mended. "
                f"That made the answer gentler than the first frightened guess."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"architect", "blueprint", "clue", "apology"}
    tool = f["tool_cfg"]
    problem = f["problem_cfg"]
    if tool.id in KNOWLEDGE:
        tags.add(tool.id)
    if problem.id == "cracked":
        tags.add("repair")
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
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        flags = [name for name, on in (
            ("movable", ent.movable),
            ("fragile", ent.fragile),
            ("helpful", ent.helpful),
        ) if on]
        if flags:
            parts.append(f"flags={flags}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="studio",
        problem="moved",
        helper="apprentice",
        tool="magnifier",
        child_name="Lina",
        child_gender="girl",
        architect_name="Mina",
        architect_gender="woman",
        helper_name="Jae",
        helper_gender="girl",
        parent="mother",
    ),
    StoryParams(
        place="library",
        problem="covered",
        helper="rival",
        tool="flashlight",
        child_name="Ben",
        child_gender="boy",
        architect_name="Clara",
        architect_gender="woman",
        helper_name="Tess",
        helper_gender="girl",
        parent="father",
    ),
    StoryParams(
        place="hall",
        problem="cracked",
        helper="caretaker",
        tool="ruler",
        child_name="Maya",
        child_gender="girl",
        architect_name="Omar",
        architect_gender="man",
        helper_name="Niko",
        helper_gender="boy",
        parent="mother",
    ),
    StoryParams(
        place="studio",
        problem="covered",
        helper="apprentice",
        tool="flashlight",
        child_name="Leo",
        child_gender="boy",
        architect_name="Sana",
        architect_gender="woman",
        helper_name="Pia",
        helper_gender="girl",
        parent="father",
    ),
    StoryParams(
        place="library",
        problem="moved",
        helper="caretaker",
        tool="magnifier",
        child_name="Ivy",
        child_gender="girl",
        architect_name="Tomas",
        architect_gender="man",
        helper_name="Rui",
        helper_gender="boy",
        parent="mother",
    ),
]


ASP_RULES = r"""
% Reasonableness gate
valid_tool(Tool) :- tool(Tool), safe_for_fragile(Tool).
kind_helper(Helper) :- helper(Helper), kindness(Helper, K), kind_min(M), K >= M.

valid(Place, Problem, Helper, Tool) :-
    place(Place), problem(Problem), helper(Helper), tool(Tool),
    valid_tool(Tool),
    not bad_cracked_combo(Problem, Helper).

bad_cracked_combo(cracked, Helper) :-
    helper(Helper), not kind_helper(Helper).

% Outcome model: every valid scenario ends reconciled after the clue is found.
clue_found :- chosen_tool(T), valid_tool(T).
solution_ready :- chosen_problem(P), clue_found, problem(P).
conflict_happened :- chosen_helper(H), helper(H).
outcome(reconciled) :- solution_ready, conflict_happened.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("kindness", hid, helper.kindness))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if tool.safe_for_fragile:
            lines.append(asp.fact("safe_for_fragile", tid))
    lines.append(asp.fact("kind_min", KIND_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_helper", params.helper),
        asp.fact("chosen_tool", params.tool),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "reconciled"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an architect, a small mystery, a conflict, and a surprise ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: Optional[set[str]] = None) -> str:
    avoid = avoid or set()
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.helper and args.tool:
        problem = PROBLEMS[args.problem]
        helper = HELPERS[args.helper]
        tool = TOOLS[args.tool]
        if not mystery_reasonable(problem, helper, tool):
            raise StoryError(explain_rejection(problem, helper, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.problem is None or combo[1] == args.problem)
        and (args.helper is None or combo[2] == args.helper)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, problem_id, helper_id, tool_id = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    architect_gender = rng.choice(["woman", "man"])
    helper_gender = rng.choice(["girl", "boy"])
    child_name = _pick_name(rng, child_gender)
    architect_name = rng.choice([n for n in ARCHITECT_NAMES if n != child_name])
    helper_name = _pick_name(rng, helper_gender, avoid={child_name})
    parent = args.parent or rng.choice(["mother", "father"])

    return StoryParams(
        place=place_id,
        problem=problem_id,
        helper=helper_id,
        tool=tool_id,
        child_name=child_name,
        child_gender=child_gender,
        architect_name=architect_name,
        architect_gender=architect_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        problem = PROBLEMS[params.problem]
        helper = HELPERS[params.helper]
        tool = TOOLS[params.tool]
    except KeyError as err:
        raise StoryError(f"(Invalid option: {err.args[0]})") from None

    if not mystery_reasonable(problem, helper, tool):
        raise StoryError(explain_rejection(problem, helper, tool))

    world = tell(
        place=place,
        problem=problem,
        helper_cfg=helper,
        tool_cfg=tool,
        child_name=params.child_name,
        child_gender=params.child_gender,
        architect_name=params.architect_name,
        architect_gender=params.architect_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
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
        params.seed = seed
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem, helper, tool) combos:\n")
        for place, problem, helper, tool in combos:
            print(f"  {place:8} {problem:8} {helper:10} {tool}")
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
            header = f"### {p.child_name}: {p.problem} at {p.place} ({p.helper}, {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
