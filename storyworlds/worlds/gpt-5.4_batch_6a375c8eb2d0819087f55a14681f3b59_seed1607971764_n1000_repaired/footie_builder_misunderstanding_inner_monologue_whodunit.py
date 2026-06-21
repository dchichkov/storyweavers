#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/footie_builder_misunderstanding_inner_monologue_whodunit.py
=======================================================================================

A standalone storyworld for a tiny whodunit-style misunderstanding: a child
building a block stadium for footie believes someone ruined it, gathers clues,
and then learns the "mystery" came from a helpful grown-up misunderstanding what
the child meant.

The world model tracks physical meters (fallen blocks, tidy level, clues found)
and emotional memes (pride, suspicion, worry, relief). The prose follows the
state: setup, apparent mystery, clue hunt with inner monologue, reveal, and a
resolution image proving what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/footie_builder_misunderstanding_inner_monologue_whodunit.py
    python storyworlds/worlds/gpt-5.4/footie_builder_misunderstanding_inner_monologue_whodunit.py --project stadium --helper father
    python storyworlds/worlds/gpt-5.4/footie_builder_misunderstanding_inner_monologue_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/footie_builder_misunderstanding_inner_monologue_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4/footie_builder_misunderstanding_inner_monologue_whodunit.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parameter registries
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
    goal: str
    pieces: str
    wrong_guess: str
    repaired_image: str
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
class MisreadAction:
    id: str
    tidy_verb: str
    tidy_result: str
    clue: str
    mistaken_meaning: str
    true_meaning: str
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
class HelperKind:
    id: str
    type: str
    label: str
    comfort: str
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
class Witness:
    id: str
    label: str
    kind_word: str
    observed: str
    innocent_line: str
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


PROJECTS = {
    "stadium": Project(
        id="stadium",
        label="stadium",
        phrase="a little block stadium for footie",
        goal="a grand place for a tiny footie final",
        pieces="rows of seats, two goals, and a tunnel for the players",
        wrong_guess="someone had wrecked the match before it could begin",
        repaired_image="the block stadium stood again, with a bright green paper field in the middle",
        tags={"blocks", "footie", "stadium"},
    ),
    "bridge": Project(
        id="bridge",
        label="bridge",
        phrase="a strong block bridge for toy players to cross to footie practice",
        goal="a safe crossing to the practice field",
        pieces="tall pillars, a flat top, and tiny flags at both ends",
        wrong_guess="someone had knocked the crossing apart on purpose",
        repaired_image="the bridge reached from one rug to the other, and tiny players marched over it",
        tags={"blocks", "bridge", "footie"},
    ),
    "tower": Project(
        id="tower",
        label="tower",
        phrase="a tall block tower to watch a footie game from above",
        goal="the best lookout in the room",
        pieces="a square base, a winding side wall, and a tiny flag on top",
        wrong_guess="someone had spoiled the lookout before the game even started",
        repaired_image="the tower rose beside the paper field, high enough to watch every pretend kick",
        tags={"blocks", "tower", "footie"},
    ),
}

MISREADS = {
    "sort_bins": MisreadAction(
        id="sort_bins",
        tidy_verb="sorted the blocks into color bins",
        tidy_result="the careful towers had vanished into neat little tubs",
        clue="the blocks were grouped by color, too neatly for a smash-and-run",
        mistaken_meaning='When I said I was "saving it for later," the grown-up heard "please put it away."',
        true_meaning='The child meant "leave it standing so I can finish later," but the grown-up heard a tidying request.',
        tags={"tidy", "misunderstanding"},
    ),
    "shelf_line": MisreadAction(
        id="shelf_line",
        tidy_verb="lined the blocks up on the shelf",
        tidy_result="the grand shape had turned into a quiet row of pieces",
        clue="the blocks were standing shoulder to shoulder on the shelf, which looked much too tidy for mischief",
        mistaken_meaning='Maybe saying "make it nice" sounded like "make it neat."',
        true_meaning='The child meant the build should stay nice and standing, but the grown-up thought neat meant put away.',
        tags={"tidy", "misunderstanding"},
    ),
    "box_lid": MisreadAction(
        id="box_lid",
        tidy_verb="placed the blocks back in the box and closed the lid",
        tidy_result="the whole mystery seemed to have disappeared into one plain cardboard box",
        clue="the box lid was shut gently, which felt more like helping than hurting",
        mistaken_meaning='Did "keep it safe" sound like "hide it so nothing happens to it"?',
        true_meaning='The child meant to keep the project standing and protected, but the grown-up thought safe meant packed away.',
        tags={"tidy", "misunderstanding"},
    ),
}

HELPERS = {
    "mother": HelperKind(
        id="mother",
        type="mother",
        label="the mother",
        comfort="knelt down and spoke softly",
        tags={"parent", "mother"},
    ),
    "father": HelperKind(
        id="father",
        type="father",
        label="the father",
        comfort="sat on the rug and listened carefully",
        tags={"parent", "father"},
    ),
    "grandpa": HelperKind(
        id="grandpa",
        type="man",
        label="Grandpa",
        comfort="adjusted his glasses and listened with a warm, calm face",
        tags={"grandparent"},
    ),
}

WITNESSES = {
    "cat": Witness(
        id="cat",
        label="the cat",
        kind_word="cat",
        observed="had only slept in a sun patch all morning",
        innocent_line="The cat was nearby, but it had not touched the blocks at all.",
        tags={"cat"},
    ),
    "sibling": Witness(
        id="sibling",
        label="the little brother",
        kind_word="brother",
        observed="had been drawing player shirts at the table",
        innocent_line="The little brother had busy crayons and clean hands, not block dust.",
        tags={"sibling"},
    ),
    "friend": Witness(
        id="friend",
        label="the neighbor friend",
        kind_word="friend",
        observed="had gone home before the mystery began",
        innocent_line="The neighbor friend was already gone, so there was no chance to knock anything over.",
        tags={"friend"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "curious", "thoughtful", "patient", "bright", "gentle"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for project_id in PROJECTS:
        for misread_id in MISREADS:
            for helper_id in HELPERS:
                for witness_id in WITNESSES:
                    combos.append((project_id, misread_id, helper_id, witness_id))
    return combos


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    project: str
    misread: str
    helper: str
    witness: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World and rules
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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


def _r_accuse(world: World) -> list[str]:
    hero = world.get("hero")
    project = world.get("project")
    if hero.memes["suspicion"] < THRESHOLD or project.meters["disturbed"] < THRESHOLD:
        return []
    sig = ("accuse", "project")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    world.facts["mystery_mode"] = True
    return ["__mystery__"]


def _r_clue_softens(world: World) -> list[str]:
    hero = world.get("hero")
    clue = world.get("clue")
    if clue.meters["found"] < THRESHOLD:
        return []
    sig = ("soften", "hero")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["certainty"] = 0.0
    hero.memes["doubt"] += 1
    return []


def _r_truth_relief(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    if helper.meters["explained"] < THRESHOLD:
        return []
    sig = ("relief", "hero")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["suspicion"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["trust"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="accuse", tag="social", apply=_r_accuse),
    Rule(name="clue_softens", tag="epistemic", apply=_r_clue_softens),
    Rule(name="truth_relief", tag="social", apply=_r_truth_relief),
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


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------
def predicted_misunderstanding(project: Project, misread: MisreadAction) -> bool:
    return bool(project.label and misread.id)


def solve_case(world: World) -> str:
    helper = world.get("helper")
    if helper.meters["explained"] >= THRESHOLD:
        return "misunderstanding"
    return "unknown"


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, project_cfg: Project) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} was a {next((t for t in hero.traits if t), 'careful')} little {hero.type} who loved making big things from small blocks."
    )
    world.say(
        f"That afternoon, {hero.pronoun()} was busy building {project_cfg.phrase}. "
        f"There were {project_cfg.pieces}, because {hero.pronoun()} wanted {project_cfg.goal}."
    )


def break_for_lunch(world: World, hero: Entity) -> None:
    world.say(
        f'At last {hero.pronoun()} stepped back and whispered, "Almost perfect."'
    )
    world.say(
        f"Then {hero.pronoun('possessive').capitalize()} tummy rumbled, so {hero.pronoun()} went to the kitchen for lunch."
    )


def leave_message(world: World, hero: Entity) -> None:
    hero.memes["hope"] += 1
    world.say(
        f'Before leaving, {hero.pronoun()} called, "Please save it for later!" and hurried off.'
    )
    world.history.append("hero_requested_saving")


def tidy_misread(world: World, helper: Entity, project: Entity, clue: Entity, misread_cfg: MisreadAction) -> None:
    project.meters["disturbed"] += 1
    project.meters["standing"] = 0.0
    project.meters["fallen"] += 1
    project.meters["tidy"] += 1
    clue.meters["present"] += 1
    helper.meters["helped"] += 1
    world.history.append("helper_tidied")
    world.facts["tidy_action"] = misread_cfg.tidy_verb
    world.facts["clue_text"] = misread_cfg.clue
    propagate(world, narrate=False)


def discover_scene(world: World, hero: Entity, project_cfg: Project, misread_cfg: MisreadAction) -> None:
    hero.memes["suspicion"] += 1
    hero.memes["certainty"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When {hero.pronoun()} came back, {misread_cfg.tidy_result}. {hero.id} stopped in the doorway as if a detective had just found the strangest clue in town."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} heart gave a small thump. {project_cfg.wrong_guess}."
    )


def inner_guess(world: World, hero: Entity, witness_cfg: Witness) -> None:
    hero.memes["suspects"] += 1
    world.say(
        f'Inside {hero.pronoun("possessive")} head came a quiet thought: "Who did this? Was it {witness_cfg.label}?"'
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} eyes narrowed in a very serious way, though only for a moment."
    )


def question_witness(world: World, hero: Entity, witness: Entity, witness_cfg: Witness) -> None:
    witness.meters["cleared"] += 1
    world.say(
        f"{hero.id} looked at {witness_cfg.label} and searched for signs of block trouble."
    )
    world.say(
        f"But {witness_cfg.label} {witness_cfg.observed}. {witness_cfg.innocent_line}"
    )


def find_clue(world: World, hero: Entity, clue: Entity, misread_cfg: MisreadAction) -> None:
    clue.meters["found"] += 1
    hero.memes["thinking"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.pronoun()} saw the real clue: {misread_cfg.clue}."
    )
    world.say(
        f'Another thought tiptoed through {hero.pronoun("possessive")} mind: "{misread_cfg.mistaken_meaning}"'
    )


def ask_helper(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f'So {hero.id} padded over to {helper.label_word if helper.id == "helper" else helper.id} and asked, "Did you see what happened to my blocks?"'
    )


def reveal(world: World, hero: Entity, helper: Entity, misread_cfg: MisreadAction) -> None:
    helper.meters["explained"] += 1
    propagate(world, narrate=False)
    helper_name = helper.id if helper.id != "helper" else helper.label_word.capitalize()
    world.say(
        f"{helper_name} {helper.attrs.get('comfort', 'listened carefully')} and blinked. "
        f'"Oh!" {helper.pronoun()} said. "I thought you wanted me to put them away and keep them safe."'
    )
    world.say(
        f"{misread_cfg.true_meaning}"
    )


def mend_feelings(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} let out a slow breath. The mystery was not meanness at all. It was a misunderstanding."
    )
    world.say(
        f'{helper.pronoun("subject").capitalize()} smiled and said, "Next time, tell me if you want it left standing."'
    )


def rebuild(world: World, hero: Entity, helper: Entity, project: Entity, project_cfg: Project) -> None:
    project.meters["standing"] += 1
    project.meters["fallen"] = 0.0
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    helper.memes["care"] += 1
    world.say(
        f"Then {helper.pronoun()} helped {hero.pronoun('object')} rebuild. Together they stacked the pieces one by one, slower now, and laughing at the mystery that had looked so dark a minute before."
    )
    world.say(
        f"By the end, {project_cfg.repaired_image}. {hero.id} knew exactly who had touched the blocks, and why."
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(
    project_cfg: Project,
    misread_cfg: MisreadAction,
    helper_cfg: HelperKind,
    witness_cfg: Witness,
    hero_name: str = "Lily",
    hero_gender: str = "girl",
    trait: str = "curious",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=[trait]))
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_cfg.type,
            role="helper",
            label=helper_cfg.label,
            attrs={"comfort": helper_cfg.comfort, "helper_kind": helper_cfg.id},
        )
    )
    witness = world.add(
        Entity(
            id="witness",
            kind="character" if witness_cfg.id != "cat" else "thing",
            type="cat" if witness_cfg.id == "cat" else "child",
            role="witness",
            label=witness_cfg.label,
            attrs={"observed": witness_cfg.observed},
        )
    )
    project = world.add(Entity(id="project", type="build", label=project_cfg.label, role="project"))
    clue = world.add(Entity(id="clue", type="clue", label="clue", role="clue"))

    world.facts.update(
        project_cfg=project_cfg,
        misread_cfg=misread_cfg,
        helper_cfg=helper_cfg,
        witness_cfg=witness_cfg,
        hero=hero,
        helper=helper,
        witness=witness,
        project=project,
        clue=clue,
        solution="unknown",
        mystery_mode=False,
    )

    hero.memes["suspicion"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["certainty"] = 0.0
    hero.memes["doubt"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["trust"] = 0.0
    project.meters["disturbed"] = 0.0
    clue.meters["found"] = 0.0
    helper.meters["explained"] = 0.0

    introduce(world, hero, project_cfg)
    break_for_lunch(world, hero)
    leave_message(world, hero)

    world.para()
    tidy_misread(world, helper, project, clue, misread_cfg)
    discover_scene(world, hero, project_cfg, misread_cfg)
    inner_guess(world, hero, witness_cfg)

    world.para()
    question_witness(world, hero, witness, witness_cfg)
    find_clue(world, hero, clue, misread_cfg)
    ask_helper(world, hero, helper)
    reveal(world, hero, helper, misread_cfg)

    world.para()
    mend_feelings(world, hero, helper)
    rebuild(world, hero, helper, project, project_cfg)

    world.facts["solution"] = solve_case(world)
    world.facts["resolved"] = world.facts["solution"] == "misunderstanding"
    world.facts["suspected_witness"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "footie": [
        (
            "What is footie?",
            "Footie is a child-friendly word for football or a pretend kicking game with goals and players. Children often use tiny balls, paper fields, or toy teams when they play it indoors.",
        )
    ],
    "builder": [
        (
            "What does a builder do?",
            "A builder makes something by putting pieces together in a careful way. A child can be a builder too when they use blocks to make towers, bridges, or stadiums.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when one person means one thing, but another person hears it a different way. Nobody has to be mean for a misunderstanding to cause a problem.",
        )
    ],
    "clue": [
        (
            "What is a clue in a mystery?",
            "A clue is a small sign that helps you figure out what really happened. Good clues make you slow down and think instead of guessing too fast.",
        )
    ],
    "apology": [
        (
            "How can people fix a misunderstanding?",
            "They can stop, explain what they meant, and listen carefully to each other. After that, they can make a new plan together.",
        )
    ],
    "blocks": [
        (
            "Why do children build with blocks?",
            "Blocks are good for building because you can stack, sort, and move them into many shapes. They let children test ideas with their hands and eyes.",
        )
    ],
}

KNOWLEDGE_ORDER = ["footie", "builder", "blocks", "clue", "misunderstanding", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    project_cfg = f["project_cfg"]
    witness_cfg = f["witness_cfg"]
    return [
        f'Write a short whodunit-style story for a 3-to-5-year-old that includes the words "footie" and "builder".',
        f"Tell a gentle mystery about a little {hero.type} who builds {project_cfg.phrase}, thinks {witness_cfg.label} ruined it, and then discovers a misunderstanding instead.",
        "Write a story with inner monologue where the child quietly wonders who did it, finds a clue, and ends by understanding what really happened.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    witness_cfg: Witness = f["witness_cfg"]
    project_cfg: Project = f["project_cfg"]
    misread_cfg: MisreadAction = f["misread_cfg"]
    helper_cfg: HelperKind = f["helper_cfg"]
    helper_name = helper_cfg.label if helper_cfg.id != "grandpa" else "Grandpa"

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little builder who was making {project_cfg.phrase}. The story also includes {helper_name}, who tried to help, and {witness_cfg.label}, who was suspected for a moment.",
        ),
        (
            f"What was {hero.id} building?",
            f"{hero.pronoun('subject').capitalize()} was building {project_cfg.phrase}. The project had {project_cfg.pieces}, because {hero.pronoun()} wanted {project_cfg.goal}.",
        ),
        (
            f"Why did {hero.id} think there was a mystery?",
            f"When {hero.pronoun()} came back, the build was gone from its place, so it looked as if someone had ruined it. That sudden change made {hero.pronoun('object')} suspicious before {hero.pronoun()} knew the real reason.",
        ),
        (
            f"Who did {hero.id} suspect first?",
            f"{hero.pronoun('subject').capitalize()} wondered if it was {witness_cfg.label}. The story shows this in {hero.pronoun('possessive')} inner thought, when {hero.pronoun()} quietly asked who had done it.",
        ),
        (
            "What clue changed the case?",
            f"The clue was that {misread_cfg.clue}. That kind of neat, careful change looked more like tidying than smashing, so it pushed the mystery toward a misunderstanding.",
        ),
        (
            "What really happened to the blocks?",
            f"{helper_name} had {misread_cfg.tidy_verb} because the grown-up misunderstood what {hero.id} meant by asking to save the project for later. So the blocks were moved gently, not ruined in anger.",
        ),
        (
            "How was the mystery solved?",
            f"It was solved when {hero.id} asked a question and listened to the answer. Once the grown-up explained the mistake, the scary mystery turned into a mix-up that could be fixed together.",
        ),
        (
            "How did the story end?",
            f"It ended with the project rebuilt and both of them understanding each other better. The final picture proves the change, because {project_cfg.repaired_image}.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"footie", "builder", "misunderstanding", "clue", "apology", "blocks"}
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  history: {world.history}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
combo(P,M,H,W) :- project(P), misread(M), helper(H), witness(W).

requested_save.
tidied_after_request :- requested_save, chosen_misread(M), misread(M).
misunderstanding :- tidied_after_request, chosen_helper(H), helper(H).
solution(misunderstanding) :- misunderstanding.

#show combo/4.
#show solution/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for project_id in PROJECTS:
        lines.append(asp.fact("project", project_id))
    for misread_id in MISREADS:
        lines.append(asp.fact("misread", misread_id))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    for witness_id in WITNESSES:
        lines.append(asp.fact("witness", witness_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "combo")))


def asp_solution(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_project", params.project),
            asp.fact("chosen_misread", params.misread),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_witness", params.witness),
        ]
    )
    model = asp.one_model(asp_program(extra))
    got = asp.atoms(model, "solution")
    return got[0][0] if got else "unknown"


def python_solution(params: StoryParams) -> str:
    if predicted_misunderstanding(PROJECTS[params.project], MISREADS[params.misread]):
        return "misunderstanding"
    return "unknown"


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
    for params in cases:
        if asp_solution(params) != python_solution(params):
            rc = 1
            print("MISMATCH in solution:", params)
            break
    else:
        print(f"OK: solution model matches on {len(cases)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        project="stadium",
        misread="sort_bins",
        helper="mother",
        witness="cat",
        name="Lily",
        gender="girl",
        trait="curious",
        seed=1,
    ),
    StoryParams(
        project="bridge",
        misread="shelf_line",
        helper="father",
        witness="sibling",
        name="Ben",
        gender="boy",
        trait="thoughtful",
        seed=2,
    ),
    StoryParams(
        project="tower",
        misread="box_lid",
        helper="grandpa",
        witness="friend",
        name="Maya",
        gender="girl",
        trait="careful",
        seed=3,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a tiny whodunit about a footie builder, a misunderstanding, and a clue-driven reveal."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--misread", choices=MISREADS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--witness", choices=WITNESSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c
        for c in valid_combos()
        if (args.project is None or c[0] == args.project)
        and (args.misread is None or c[1] == args.misread)
        and (args.helper is None or c[2] == args.helper)
        and (args.witness is None or c[3] == args.witness)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project_id, misread_id, helper_id, witness_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        project=project_id,
        misread=misread_id,
        helper=helper_id,
        witness=witness_id,
        name=name,
        gender=gender,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.project not in PROJECTS:
        raise StoryError(f"Unknown project: {params.project}")
    if params.misread not in MISREADS:
        raise StoryError(f"Unknown misread: {params.misread}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")
    if params.witness not in WITNESSES:
        raise StoryError(f"Unknown witness: {params.witness}")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"Unknown gender: {params.gender}")

    world = tell(
        project_cfg=PROJECTS[params.project],
        misread_cfg=MISREADS[params.misread],
        helper_cfg=HELPERS[params.helper],
        witness_cfg=WITNESSES[params.witness],
        hero_name=params.name,
        hero_gender=params.gender,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (project, misread, helper, witness) combos:\n")
        for project_id, misread_id, helper_id, witness_id in combos:
            print(f"  {project_id:8} {misread_id:10} {helper_id:8} {witness_id}")
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
            header = f"### {p.name}: {p.project} / {p.misread} / {p.helper} / {p.witness}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
