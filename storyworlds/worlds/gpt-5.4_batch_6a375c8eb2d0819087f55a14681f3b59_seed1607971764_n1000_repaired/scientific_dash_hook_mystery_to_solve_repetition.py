#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/scientific_dash_hook_mystery_to_solve_repetition.py
==============================================================================

A standalone story world for a small child-facing mystery: a child hangs a
scientific project on a hook, the project goes missing, and repeated clues help
solve the puzzle. The world model tracks the physical cause of the disappearance
and whether the child investigates carefully or blurts out a blameful guess.

Features
--------
- Mystery to solve
- Repetition ("dash, dash, dash")
- Moral value: look carefully before blaming, and apologize when you are wrong

Run it
------
    python storyworlds/worlds/gpt-5.4/scientific_dash_hook_mystery_to_solve_repetition.py
    python storyworlds/worlds/gpt-5.4/scientific_dash_hook_mystery_to_solve_repetition.py --place porch --project seed_chart --disturbance wind
    python storyworlds/worlds/gpt-5.4/scientific_dash_hook_mystery_to_solve_repetition.py --project rock_report --disturbance wind
    python storyworlds/worlds/gpt-5.4/scientific_dash_hook_mystery_to_solve_repetition.py --all
    python storyworlds/worlds/gpt-5.4/scientific_dash_hook_mystery_to_solve_repetition.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/scientific_dash_hook_mystery_to_solve_repetition.py --verify
"""

from __future__ import annotations

import argparse
import copy
import contextlib
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
CALM_APPROACHES = {"investigate"}


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
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    affordances: set[str] = field(default_factory=set)
    hook_label: str = "brass hook"
    hiding_spot: str = ""
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
class Project:
    id: str
    label: str
    phrase: str
    material: str
    weight: int
    has_string: bool = False
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
class Disturbance:
    id: str
    label: str
    cause_line: str
    clue_text: str
    reveal_text: str
    repair_text: str
    requires_affordance: str
    max_weight: int = 9
    min_weight: int = 0
    material_ok: set[str] = field(default_factory=set)
    needs_string: bool = False
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
class StoryParams:
    place: str
    project: str
    disturbance: str
    approach: str
    name: str
    gender: str
    helper: str
    helper_gender: str
    grownup: str
    trait: str
    seed: Optional[int] = None
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_missing_worry(world: World) -> list[str]:
    out: list[str] = []
    project = world.get("project")
    hero = world.get("hero")
    helper = world.get("helper")
    room = world.get("room")
    if project.meters["missing"] >= THRESHOLD:
        sig = ("missing_worry", project.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] += 1
            helper.memes["curiosity"] += 1
            room.meters["mystery"] += 1
    return out


def _r_guess_hurts(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.memes["blame"] >= THRESHOLD:
        sig = ("guess_hurts", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["hurt"] += 1
            hero.memes["guilt"] += 1
    return out


def _r_found_relief(world: World) -> list[str]:
    out: list[str] = []
    project = world.get("project")
    hero = world.get("hero")
    helper = world.get("helper")
    if project.meters["found"] >= THRESHOLD:
        sig = ("found_relief", project.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["relief"] += 1
            helper.memes["relief"] += 1
            hero.memes["lesson"] += 1
    return out


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="guess_hurts", tag="social", apply=_r_guess_hurts),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "classroom": Place(
        id="classroom",
        label="the classroom",
        affordances={"breeze", "old_hooks"},
        hook_label="the brass wall hook",
        hiding_spot="behind the reading shelf",
        tags={"hook", "classroom"},
    ),
    "greenhouse": Place(
        id="greenhouse",
        label="the school greenhouse",
        affordances={"breeze", "pet"},
        hook_label="the green painted hook",
        hiding_spot="under the potting table",
        tags={"hook", "plants"},
    ),
    "porch": Place(
        id="porch",
        label="the back porch",
        affordances={"breeze", "pet", "old_hooks"},
        hook_label="the wooden hook by the door",
        hiding_spot="behind the rain barrel",
        tags={"hook", "breeze"},
    ),
}

PROJECTS = {
    "seed_chart": Project(
        id="seed_chart",
        label="seed chart",
        phrase="a scientific seed chart with neat rows and tiny labels",
        material="paper",
        weight=1,
        has_string=False,
        tags={"scientific", "paper", "seeds"},
    ),
    "moon_mobile": Project(
        id="moon_mobile",
        label="moon mobile",
        phrase="a scientific moon mobile with silver circles and a hanging string",
        material="card",
        weight=1,
        has_string=True,
        tags={"scientific", "moon", "string"},
    ),
    "rock_report": Project(
        id="rock_report",
        label="rock report",
        phrase="a scientific rock report on thick board with a stiff top loop",
        material="board",
        weight=3,
        has_string=False,
        tags={"scientific", "rocks"},
    ),
    "leaf_graph": Project(
        id="leaf_graph",
        label="leaf graph",
        phrase="a scientific leaf graph pressed flat on light card",
        material="card",
        weight=2,
        has_string=False,
        tags={"scientific", "leaves"},
    ),
}

DISTURBANCES = {
    "wind": Disturbance(
        id="wind",
        label="wind",
        cause_line="a cool breeze slipped through and worried the edges of the project",
        clue_text='Then they heard it again: "dash, dash, dash" went the paper as it tapped in a hidden spot.',
        reveal_text="The breeze had shaken it free and blown it where nobody first looked.",
        repair_text="They closed the window a little and fastened the project more snugly on the hook.",
        requires_affordance="breeze",
        max_weight=2,
        material_ok={"paper", "card"},
        needs_string=False,
        tags={"breeze"},
    ),
    "kitten": Disturbance(
        id="kitten",
        label="kitten",
        cause_line="the class kitten had spotted the dangling string and batted at it",
        clue_text='Across the floor ran a tiny muddy trail: dash, dash, dash, right toward the hiding place.',
        reveal_text="The kitten had tugged it down and chased it like a toy.",
        repair_text="They gave the kitten a yarn ball instead and hung the project where the string could not dangle.",
        requires_affordance="pet",
        max_weight=2,
        material_ok={"paper", "card"},
        needs_string=True,
        tags={"pet", "pawprints"},
    ),
    "loose_hook": Disturbance(
        id="loose_hook",
        label="loose hook",
        cause_line="the old hook had wiggled and finally tipped forward",
        clue_text='On the wall and floor they noticed a scrape, a tiny metal shine, and a soft slide that sounded like dash, dash, dash.',
        reveal_text="The hook itself had let go, so the project slipped down out of sight.",
        repair_text="The grown-up tightened the hook firmly before they hung the project back up.",
        requires_affordance="old_hooks",
        min_weight=2,
        material_ok={"board", "card"},
        needs_string=False,
        tags={"hook", "repair"},
    ),
}

APPROACHES = ["investigate", "accuse"]
TRAITS = ["careful", "curious", "patient", "hasty", "spirited", "thoughtful"]
GIRL_NAMES = ["Lina", "Maya", "Nora", "Ava", "Zoe", "Ella", "Iris", "Ruby"]
BOY_NAMES = ["Eli", "Noah", "Max", "Leo", "Finn", "Owen", "Theo", "Sam"]


def valid_combo(place: Place, project: Project, disturbance: Disturbance) -> bool:
    if disturbance.requires_affordance not in place.affordances:
        return False
    if project.material not in disturbance.material_ok:
        return False
    if not (disturbance.min_weight <= project.weight <= disturbance.max_weight):
        return False
    if disturbance.needs_string and not project.has_string:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for project_id, project in PROJECTS.items():
            for disturbance_id, disturbance in DISTURBANCES.items():
                if valid_combo(place, project, disturbance):
                    combos.append((place_id, project_id, disturbance_id))
    return combos


def explain_rejection(place: Place, project: Project, disturbance: Disturbance) -> str:
    if disturbance.requires_affordance not in place.affordances:
        return (
            f"(No story: {place.label} does not support the cause '{disturbance.id}'. "
            f"This mystery needs {disturbance.requires_affordance} to make the disappearance plausible.)"
        )
    if project.material not in disturbance.material_ok:
        return (
            f"(No story: {project.label} is made of {project.material}, but the cause "
            f"'{disturbance.id}' only works for {sorted(disturbance.material_ok)}.)"
        )
    if disturbance.needs_string and not project.has_string:
        return (
            f"(No story: the {disturbance.id} mystery needs a project with a dangling string, "
            f"and {project.label} does not have one.)"
        )
    if project.weight < disturbance.min_weight:
        return (
            f"(No story: {project.label} is too light for '{disturbance.id}'. "
            f"The cause only makes sense for projects weighing at least {disturbance.min_weight}.)"
        )
    if project.weight > disturbance.max_weight:
        return (
            f"(No story: {project.label} is too heavy for '{disturbance.id}'. "
            f"The cause only makes sense for projects weighing at most {disturbance.max_weight}.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


def outcome_of(params: StoryParams) -> str:
    return "kind" if params.approach in CALM_APPROACHES else "apology"


def predict_cause(world: World, disturbance: Disturbance) -> dict:
    sim = world.copy()
    apply_disturbance(sim, disturbance, narrate=False)
    project = sim.get("project")
    return {
        "missing": project.meters["missing"] >= THRESHOLD,
        "hiding_spot": sim.facts["hiding_spot"],
    }


def introduce(world: World, hero: Entity, helper: Entity, project: Entity, place: Place) -> None:
    world.say(
        f"{hero.id} had made {project.phrase}. All morning, {hero.pronoun()} kept checking the labels, "
        f"because {hero.pronoun('possessive')} scientific work mattered to {hero.pronoun('object')}."
    )
    world.say(
        f"When it was time to dry and display the project, {hero.id} and {helper.id} hung it on {place.hook_label} in {place.label}."
    )


def set_mystery(world: World, hero: Entity, helper: Entity, project: Entity, place: Place) -> None:
    world.say(
        f"Later, when they came back, the hook was empty."
    )
    world.say(
        f'"My {project.label} is gone," {hero.id} whispered. "{helper.id}, this is a mystery to solve."'
    )
    world.say(
        f"{helper.id} looked at the bare hook, then around {place.label}, and nodded."
    )


def apply_disturbance(world: World, disturbance: Disturbance, narrate: bool = True) -> None:
    project = world.get("project")
    project.meters["hanging"] = 0.0
    project.meters["missing"] += 1
    project.meters["moved"] += 1
    world.get("hook").meters["empty"] += 1
    world.get("room").meters["mystery"] += 1
    world.facts["hiding_spot"] = world.place.hiding_spot
    world.facts["cause_seen"] = disturbance.id
    if disturbance.id == "wind":
        world.get("window").meters["open"] += 1
        project.meters["behind_something"] += 1
        world.get("clue").meters["sound"] += 1
    elif disturbance.id == "kitten":
        world.get("pet").meters["playful"] += 1
        world.get("clue").meters["pawprints"] += 1
        project.meters["under_something"] += 1
    elif disturbance.id == "loose_hook":
        world.get("hook").meters["loose"] += 1
        world.get("clue").meters["scrape"] += 1
        project.meters["behind_something"] += 1
    propagate(world, narrate=False)
    if narrate:
        world.say(
            f"Before they returned, {disturbance.cause_line}."
        )


def clue_scene(world: World, disturbance: Disturbance, helper: Entity) -> None:
    helper.memes["focus"] += 1
    world.say(
        f'{helper.id} said, "Listen. Look. Listen again."'
    )
    world.say(disturbance.clue_text)


def accuse(world: World, hero: Entity, helper: Entity, project: Entity) -> None:
    hero.memes["blame"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} made a quick guess. "Did you move my {project.label}, {helper.id}?"'
    )
    world.say(
        f"{helper.id}'s face fell. {helper.pronoun().capitalize()} shook {helper.pronoun('possessive')} head at once."
    )


def investigate(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["patience"] += 1
    helper.memes["patience"] += 1
    world.say(
        f"Instead of guessing, the two children followed the little signs together."
    )


def find_project(world: World, hero: Entity, helper: Entity, project: Entity, disturbance: Disturbance) -> None:
    project.meters["found"] += 1
    project.meters["missing"] = 0.0
    world.facts["found_where"] = world.facts["hiding_spot"]
    propagate(world, narrate=False)
    world.say(
        f"They searched slowly until {helper.id} pointed. There, {world.facts['hiding_spot']}, was the {project.label}."
    )
    world.say(
        disturbance.reveal_text
    )


def apology_if_needed(world: World, hero: Entity, helper: Entity) -> None:
    if hero.memes["blame"] < THRESHOLD:
        return
    helper.memes["hurt"] = max(0.0, helper.memes["hurt"] - 1.0)
    hero.memes["kindness"] += 1
    world.say(
        f'"I am sorry I guessed before I looked," {hero.id} said.'
    )
    world.say(
        f'{helper.id} gave a small nod. "Mysteries go better when we are careful with people," {helper.pronoun()} said.'
    )


def repair_and_end(world: World, hero: Entity, helper: Entity, grownup: Entity, project: Entity, disturbance: Disturbance) -> None:
    project.meters["hanging"] = 1.0
    world.get("hook").meters["empty"] = 0.0
    world.get("room").meters["mystery"] = 0.0
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{grownup.label_word.capitalize()} came over, listened to the clues, and smiled at how carefully they had solved the puzzle."
    )
    world.say(disturbance.repair_text)
    world.say(
        f"Soon the {project.label} was hanging straight on the hook again."
    )
    world.say(
        f'As they stood back, {hero.id} whispered the clue one last time -- "dash, dash, dash" -- and this time both children laughed, because the mystery was not scary anymore.'
    )
    world.say(
        f"{hero.id} learned that careful looking is better than fast blaming, and {helper.id} stayed close beside {hero.pronoun('object')}."
    )


def tell(
    place: Place,
    project_cfg: Project,
    disturbance: Disturbance,
    approach: str,
    name: str = "Lina",
    gender: str = "girl",
    helper_name: str = "Eli",
    helper_gender: str = "boy",
    grownup_type: str = "mother",
    trait: str = "careful",
) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=name, phrase=name, role="hero", traits=[trait]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, phrase=helper_name, role="helper", traits=["observant"]))
    grownup = world.add(Entity(id="grownup", kind="character", type=grownup_type, label="the grown-up", phrase="the grown-up", role="grownup"))
    project = world.add(Entity(id="project", kind="thing", type="project", label=project_cfg.label, phrase=project_cfg.phrase))
    hook = world.add(Entity(id="hook", kind="thing", type="hook", label=place.hook_label, phrase=place.hook_label))
    room = world.add(Entity(id="room", kind="thing", type="room", label=place.label, phrase=place.label))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label="the clue"))
    window = world.add(Entity(id="window", kind="thing", type="window", label="the window"))
    pet = world.add(Entity(id="pet", kind="thing", type="pet", label="the kitten"))

    hero.memes["hope"] = 1.0
    helper.memes["trust"] = 1.0
    project.meters["hanging"] = 1.0
    hook.meters["empty"] = 0.0
    room.meters["mystery"] = 0.0
    clue.meters["sound"] = 0.0
    clue.meters["pawprints"] = 0.0
    clue.meters["scrape"] = 0.0
    window.meters["open"] = 0.0
    pet.meters["playful"] = 0.0
    world.facts["hiding_spot"] = place.hiding_spot
    world.facts["approach"] = approach

    introduce(world, hero, helper, project, place)

    world.para()
    apply_disturbance(world, disturbance, narrate=True)
    set_mystery(world, hero, helper, project, place)

    world.para()
    clue_scene(world, disturbance, helper)
    if approach == "accuse":
        accuse(world, hero, helper, project)
    else:
        investigate(world, hero, helper)

    world.para()
    find_project(world, hero, helper, project, disturbance)
    apology_if_needed(world, hero, helper)
    repair_and_end(world, hero, helper, grownup, project, disturbance)

    world.facts.update(
        hero=hero,
        helper=helper,
        grownup=grownup,
        project_cfg=project_cfg,
        disturbance=disturbance,
        place=place,
        project=project,
        clue=clue,
        outcome=outcome_of(
            StoryParams(
                place=place.id,
                project=project_cfg.id,
                disturbance=disturbance.id,
                approach=approach,
                name=name,
                gender=gender,
                helper=helper_name,
                helper_gender=helper_gender,
                grownup=grownup_type,
                trait=trait,
            )
        ),
        blamed=hero.memes["blame"] >= THRESHOLD,
        found_where=world.facts["found_where"],
    )
    return world


KNOWLEDGE = {
    "scientific": [
        (
            "What does scientific mean?",
            "Scientific means using careful looking, testing, and noticing facts. It is a way of learning about how the world works.",
        )
    ],
    "hook": [
        (
            "What is a hook for?",
            "A hook is a bent piece that holds something up, like a coat or a project. If the hook is loose or the thing slips, it can fall down.",
        )
    ],
    "breeze": [
        (
            "What can a breeze do to light paper?",
            "A breeze can flutter light paper and push it around. If the paper is only resting lightly, the breeze can blow it off.",
        )
    ],
    "pawprints": [
        (
            "What do pawprints tell you?",
            "Pawprints are clues that an animal walked there. They can help you follow where the animal went.",
        )
    ],
    "repair": [
        (
            "Why is it good to fix something after a problem?",
            "Fixing the cause helps the same problem happen less often again. It turns a mistake into a way to learn and make things safer.",
        )
    ],
    "kindness": [
        (
            "Why should you look carefully before blaming someone?",
            "Because a fast guess can hurt someone's feelings. Careful looking helps you find the truth and be fair.",
        )
    ],
    "apology": [
        (
            "What does an apology do?",
            "An apology tells the other person that you know you hurt them and want to make it right. It helps repair trust after a wrong guess or mistake.",
        )
    ],
}
KNOWLEDGE_ORDER = ["scientific", "hook", "breeze", "pawprints", "repair", "kindness", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    project_cfg = f["project_cfg"]
    disturbance = f["disturbance"]
    if f["outcome"] == "apology":
        return [
            f'Write a short mystery story for a 3-to-5-year-old that includes the words "scientific", "dash", and "hook".',
            f"Tell a gentle mystery where {hero.label}'s {project_cfg.label} goes missing from a hook, repeated clues help solve it, and {hero.label} must apologize for guessing too fast.",
            f'Write a child-facing mystery with repetition -- especially "dash, dash, dash" -- where careful looking matters more than blaming.',
        ]
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes the words "scientific", "dash", and "hook".',
        f"Tell a gentle mystery where {hero.label} and {helper.label} solve the disappearance of a scientific project from a hook by following repeated clues.",
        f'Write a mystery with the repeated sound "dash, dash, dash" and a moral about looking carefully for the truth.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    project_cfg = f["project_cfg"]
    disturbance = f["disturbance"]
    place = f["place"]
    out: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            f"The mystery was that {hero.label}'s {project_cfg.label} had vanished from the hook in {place.label}. It looked gone, so the children had to search for a real cause instead of only guessing.",
        ),
        (
            "What clue kept repeating?",
            f'The repeated clue was "dash, dash, dash." That sound or pattern helped the children slow down and notice where to look next.',
        ),
        (
            "Why did the project go missing?",
            f"It went missing because of {disturbance.label}. {disturbance.reveal_text}",
        ),
        (
            "Where did they find the project?",
            f"They found it {f['found_where']}. The hiding place matched the clue and showed that the project had moved, not disappeared by magic.",
        ),
    ]
    if f["outcome"] == "apology":
        out.append(
            (
                f"Why did {hero.label} apologize?",
                f"{hero.label} apologized because {hero.pronoun('subject')} guessed too fast and hurt {helper.label}'s feelings. After the clues showed what really happened, {hero.pronoun('subject')} understood that careful looking is kinder than blame.",
            )
        )
    else:
        out.append(
            (
                f"How did {hero.label} and {helper.label} solve the mystery?",
                f"They solved it by listening, looking, and following the repeated clue together. Because they stayed patient, they found the real cause without hurting anyone's feelings first.",
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["project_cfg"].tags) | set(f["place"].tags) | set(f["disturbance"].tags)
    tags.add("kindness")
    if f["outcome"] == "apology":
        tags.add("apology")
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Pl, Pr, Ds) :-
    place(Pl), project(Pr), disturbance(Ds),
    needs_affordance(Ds, A), affords(Pl, A),
    material(Pr, M), material_ok(Ds, M),
    weight(Pr, W), min_weight(Ds, Min), max_weight(Ds, Max), W >= Min, W <= Max,
    not needs_string(Ds).
valid(Pl, Pr, Ds) :-
    place(Pl), project(Pr), disturbance(Ds),
    needs_affordance(Ds, A), affords(Pl, A),
    material(Pr, M), material_ok(Ds, M),
    weight(Pr, W), min_weight(Ds, Min), max_weight(Ds, Max), W >= Min, W <= Max,
    needs_string(Ds), has_string(Pr).

outcome(kind) :- chosen_approach(investigate).
outcome(apology) :- chosen_approach(accuse).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for aff in sorted(place.affordances):
            lines.append(asp.fact("affords", place_id, aff))
    for project_id, project in PROJECTS.items():
        lines.append(asp.fact("project", project_id))
        lines.append(asp.fact("material", project_id, project.material))
        lines.append(asp.fact("weight", project_id, project.weight))
        if project.has_string:
            lines.append(asp.fact("has_string", project_id))
    for disturbance_id, disturbance in DISTURBANCES.items():
        lines.append(asp.fact("disturbance", disturbance_id))
        lines.append(asp.fact("needs_affordance", disturbance_id, disturbance.requires_affordance))
        lines.append(asp.fact("min_weight", disturbance_id, disturbance.min_weight))
        lines.append(asp.fact("max_weight", disturbance_id, disturbance.max_weight))
        if disturbance.needs_string:
            lines.append(asp.fact("needs_string", disturbance_id))
        for mat in sorted(disturbance.material_ok):
            lines.append(asp.fact("material_ok", disturbance_id, mat))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_approach", params.approach)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


CURATED = [
    StoryParams(
        place="classroom",
        project="seed_chart",
        disturbance="wind",
        approach="investigate",
        name="Lina",
        gender="girl",
        helper="Max",
        helper_gender="boy",
        grownup="mother",
        trait="careful",
    ),
    StoryParams(
        place="greenhouse",
        project="moon_mobile",
        disturbance="kitten",
        approach="accuse",
        name="Eli",
        gender="boy",
        helper="Nora",
        helper_gender="girl",
        grownup="father",
        trait="hasty",
    ),
    StoryParams(
        place="porch",
        project="rock_report",
        disturbance="loose_hook",
        approach="investigate",
        name="Maya",
        gender="girl",
        helper="Theo",
        helper_gender="boy",
        grownup="mother",
        trait="patient",
    ),
    StoryParams(
        place="porch",
        project="leaf_graph",
        disturbance="wind",
        approach="accuse",
        name="Sam",
        gender="boy",
        helper="Ruby",
        helper_gender="girl",
        grownup="father",
        trait="spirited",
    ),
    StoryParams(
        place="classroom",
        project="leaf_graph",
        disturbance="loose_hook",
        approach="investigate",
        name="Ava",
        gender="girl",
        helper="Finn",
        helper_gender="boy",
        grownup="mother",
        trait="thoughtful",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child solves a little mystery about a missing scientific project from a hook."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--disturbance", choices=DISTURBANCES)
    ap.add_argument("--approach", choices=APPROACHES, help="how the child responds first: investigate or accuse")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.project and args.disturbance:
        place = PLACES[args.place]
        project = PROJECTS[args.project]
        disturbance = DISTURBANCES[args.disturbance]
        if not valid_combo(place, project, disturbance):
            raise StoryError(explain_rejection(place, project, disturbance))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.project is None or combo[1] == args.project)
        and (args.disturbance is None or combo[2] == args.disturbance)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, project_id, disturbance_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    helper = args.helper or _pick_name(rng, helper_gender, avoid=name)
    grownup = args.grownup or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    approach = args.approach or rng.choice(APPROACHES)
    return StoryParams(
        place=place_id,
        project=project_id,
        disturbance=disturbance_id,
        approach=approach,
        name=name,
        gender=gender,
        helper=helper,
        helper_gender=helper_gender,
        grownup=grownup,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.disturbance not in DISTURBANCES:
        raise StoryError(f"(Unknown disturbance: {params.disturbance})")
    if params.approach not in APPROACHES:
        raise StoryError(f"(Unknown approach: {params.approach})")

    place = PLACES[params.place]
    project = PROJECTS[params.project]
    disturbance = DISTURBANCES[params.disturbance]
    if not valid_combo(place, project, disturbance):
        raise StoryError(explain_rejection(place, project, disturbance))

    world = tell(
        place=place,
        project_cfg=project,
        disturbance=disturbance,
        approach=params.approach,
        name=params.name,
        gender=params.gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
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
    for s in range(40):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolution failure for seed {s}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_sample = generate(smoke_params)
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke_sample, trace=True, qa=True)
        if not smoke_sample.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, project, disturbance) combos:\n")
        for place, project, disturbance in combos:
            print(f"  {place:10} {project:11} {disturbance}")
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
            header = f"### {p.name}: {p.project} at {p.place} ({p.disturbance}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
