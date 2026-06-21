#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/moan_problem_solving_animal_story.py
===============================================================

A standalone storyworld for gentle animal stories about a small problem, a
worried moan, and a clever fix.

Premise
-------
A young animal hears a friend's moan, pauses to think, and solves the problem
with the right method and the right material from the setting. The world only
permits combinations that make physical sense: the hero must have the needed
skill, the place must provide the needed material, and the chosen method must
fit the actual problem.

Run it
------
    python storyworlds/worlds/gpt-5.4/moan_problem_solving_animal_story.py
    python storyworlds/worlds/gpt-5.4/moan_problem_solving_animal_story.py --place riverbank --problem mud_paw
    python storyworlds/worlds/gpt-5.4/moan_problem_solving_animal_story.py --method lever_stick
    python storyworlds/worlds/gpt-5.4/moan_problem_solving_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/moan_problem_solving_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/moan_problem_solving_animal_story.py --trace
    python storyworlds/worlds/gpt-5.4/moan_problem_solving_animal_story.py --asp
    python storyworlds/worlds/gpt-5.4/moan_problem_solving_animal_story.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        gender = self.attrs.get("gender", "")
        if gender == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    label: str
    opening: str
    materials: set[str] = field(default_factory=set)
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
class Species:
    id: str
    label: str
    skills: set[str] = field(default_factory=set)
    likes: str = ""
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
    intro: str
    moan_line: str
    risk_line: str
    solved_line: str
    ending_image: str
    needs_method: str
    severity: int = 1
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
    label: str
    material: str
    material_phrase: str
    solve_problem: str
    needed_skill: str
    gather_line: str
    action_line: str
    qa_text: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_trouble_distress(world: World) -> list[str]:
    out: list[str] = []
    friend = world.entities.get("friend")
    hero = world.entities.get("hero")
    if friend is None or hero is None:
        return out
    if friend.meters["trouble"] >= THRESHOLD:
        sig = ("trouble_distress", friend.id)
        if sig not in world.fired:
            world.fired.add(sig)
            friend.memes["fear"] += 1
            friend.memes["sadness"] += 1
            hero.memes["concern"] += 1
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    friend = world.entities.get("friend")
    hero = world.entities.get("hero")
    if friend is None or hero is None:
        return out
    if friend.meters["freed"] >= THRESHOLD:
        sig = ("relief", friend.id)
        if sig not in world.fired:
            world.fired.add(sig)
            friend.memes["relief"] += 1
            friend.memes["joy"] += 1
            hero.memes["joy"] += 1
            hero.memes["confidence"] += 1
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="trouble_distress", tag="emotional", apply=_r_trouble_distress),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def has_material(setting: Setting, method: Method) -> bool:
    return method.material in setting.materials


def hero_can_use(species: Species, method: Method) -> bool:
    return method.needed_skill in species.skills


def method_fits(problem: Problem, method: Method) -> bool:
    return method.id == problem.needs_method and method.solve_problem == problem.id


def valid_combo(place_id: str, hero_id: str, problem_id: str, method_id: str) -> bool:
    setting = SETTINGS[place_id]
    species = HERO_SPECIES[hero_id]
    problem = PROBLEMS[problem_id]
    method = METHODS[method_id]
    return (
        has_material(setting, method)
        and hero_can_use(species, method)
        and method_fits(problem, method)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in SETTINGS:
        for hero_id in HERO_SPECIES:
            for problem_id in PROBLEMS:
                for method_id in METHODS:
                    if valid_combo(place_id, hero_id, problem_id, method_id):
                        combos.append((place_id, hero_id, problem_id, method_id))
    return combos


def explain_invalid(place: Setting, hero: Species, problem: Problem, method: Method) -> str:
    reasons: list[str] = []
    if not method_fits(problem, method):
        reasons.append(
            f"{method.label} does not solve {problem.label}; that problem needs {METHODS[problem.needs_method].label}"
        )
    if not has_material(place, method):
        reasons.append(
            f"{place.label} does not have {method.material_phrase}"
        )
    if not hero_can_use(hero, method):
        reasons.append(
            f"a {hero.label} in this world is not the right kind of helper for {method.label}"
        )
    if not reasons:
        reasons.append("that combination is not reasonable in this storyworld")
    return "(No story: " + "; ".join(reasons) + ".)"


def predict_risk(world: World, problem: Problem) -> dict:
    sim = world.copy()
    friend = sim.get("friend")
    hero = sim.get("hero")
    friend.meters["pain"] += float(problem.severity)
    friend.memes["fear"] += 1
    hero.memes["concern"] += 1
    return {
        "pain": friend.meters["pain"],
        "fear": friend.memes["fear"],
        "line": problem.risk_line,
    }


def introduce(world: World, hero: Entity, hero_cfg: Species, friend: Entity, friend_cfg: Species) -> None:
    world.say(
        f"{world.setting.opening} {hero.id} the {hero_cfg.label} was out enjoying {hero_cfg.likes} "
        f"when {hero.pronoun('subject')} noticed that the morning felt especially bright."
    )
    world.say(
        f"Not far away, {friend.id} the {friend_cfg.label} was busy with a small, ordinary sort of day."
    )


def hear_moan(world: World, hero: Entity, friend: Entity, problem: Problem) -> None:
    friend.meters["trouble"] = float(problem.severity)
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"Then {hero.id} heard a soft moan from behind a tuft of grass. "
        f"{hero.pronoun('subject').capitalize()} hurried over and found {friend.id} there."
    )
    world.say(problem.intro)
    world.say(problem.moan_line)


def think_before_acting(world: World, hero: Entity, friend: Entity, problem: Problem) -> None:
    pred = predict_risk(world, problem)
    world.facts["predicted_pain"] = pred["pain"]
    world.facts["predicted_fear"] = pred["fear"]
    world.facts["risk_line"] = pred["line"]
    hero.memes["thoughtful"] += 1
    world.say(
        f"{hero.id} almost rushed in right away, but {hero.pronoun('subject')} stopped and looked carefully. "
        f'"If I do the wrong thing," {hero.pronoun("subject")} thought, "{pred["line"]}"'
    )


def gather_material(world: World, hero: Entity, method: Method) -> None:
    tool = world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=method.label,
            attrs={"material": method.material},
        )
    )
    tool.meters["ready"] = 1.0
    world.say(method.gather_line.format(hero=hero.id.lower(), place=world.setting.label))


def solve(world: World, hero: Entity, friend: Entity, problem: Problem, method: Method) -> None:
    friend.meters["trouble"] = 0.0
    friend.meters["pain"] = 0.0
    friend.meters["freed"] = 1.0
    propagate(world, narrate=False)
    world.say(method.action_line.format(friend=friend.id, hero=hero.id))
    world.say(problem.solved_line.format(friend=friend.id))
    if friend.memes["relief"] >= THRESHOLD:
        world.say(
            f"{friend.id} let out a long breath instead of another moan, and {friend.pronoun('possessive')} face softened with relief."
        )


def ending(world: World, hero: Entity, friend: Entity, problem: Problem) -> None:
    world.para()
    world.say(
        f'"Thank you," said {friend.id}. "{hero.id}, you did not just pull and hope. You thought first."'
    )
    world.say(
        f"{hero.id} smiled, and the two friends went on together. {problem.ending_image}"
    )


def tell(
    setting: Setting,
    hero_cfg: Species,
    friend_cfg: Species,
    problem: Problem,
    method: Method,
    hero_name: str = "Pip",
    hero_gender: str = "boy",
    friend_name: str = "Mina",
    friend_gender: str = "girl",
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_cfg.id,
            label=hero_cfg.label,
            role="hero",
            attrs={"gender": hero_gender, "skills": sorted(hero_cfg.skills)},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_cfg.id,
            label=friend_cfg.label,
            role="friend",
            attrs={"gender": friend_gender},
        )
    )
    place_ent = world.add(
        Entity(
            id="place",
            kind="thing",
            type="place",
            label=setting.label,
            attrs={"materials": sorted(setting.materials)},
        )
    )
    place_ent.meters["calm"] = 1.0

    introduce(world, hero, hero_cfg, friend, friend_cfg)
    hear_moan(world, hero, friend, problem)
    think_before_acting(world, hero, friend, problem)

    world.para()
    gather_material(world, hero, method)
    solve(world, hero, friend, problem, method)
    ending(world, hero, friend, problem)

    world.facts.update(
        hero=hero,
        friend=friend,
        hero_cfg=hero_cfg,
        friend_cfg=friend_cfg,
        setting=setting,
        problem=problem,
        method=method,
        solved=friend.meters["freed"] >= THRESHOLD,
        concern=hero.memes["concern"],
        materials=sorted(setting.materials),
    )
    return world


SETTINGS = {
    "riverbank": Setting(
        id="riverbank",
        label="the riverbank",
        opening="By the riverbank, the water slipped past smooth stones and the reeds whispered together.",
        materials={"reeds", "stones"},
        tags={"river", "reeds", "stones"},
    ),
    "meadow": Setting(
        id="meadow",
        label="the meadow edge",
        opening="At the meadow edge, buttercups nodded in the breeze and tall grass made little green tunnels.",
        materials={"reeds", "stick"},
        tags={"grass", "reeds", "stick"},
    ),
    "forest": Setting(
        id="forest",
        label="the forest path",
        opening="Along the forest path, fern shadows lay over the ground and old branches rested under the trees.",
        materials={"stick", "moss"},
        tags={"forest", "stick"},
    ),
    "orchard": Setting(
        id="orchard",
        label="the orchard lane",
        opening="In the orchard lane, round apples hung overhead and pebbly soil warmed in the sun.",
        materials={"stick", "stones"},
        tags={"orchard", "stick", "stones"},
    ),
}

HERO_SPECIES = {
    "rabbit": Species(
        id="rabbit",
        label="rabbit",
        skills={"patient"},
        likes="tender clover tips",
        tags={"rabbit"},
    ),
    "otter": Species(
        id="otter",
        label="otter",
        skills={"steady"},
        likes="smooth skipping stones",
        tags={"otter"},
    ),
    "beaver": Species(
        id="beaver",
        label="beaver",
        skills={"strong"},
        likes="cool bark and shiny streams",
        tags={"beaver"},
    ),
}

FRIEND_SPECIES = {
    "mouse": Species(
        id="mouse",
        label="mouse",
        skills=set(),
        likes="tiny seeds",
        tags={"mouse"},
    ),
    "duck": Species(
        id="duck",
        label="duck",
        skills=set(),
        likes="ripples and puddles",
        tags={"duck"},
    ),
    "mole": Species(
        id="mole",
        label="mole",
        skills=set(),
        likes="soft dark tunnels",
        tags={"mole"},
    ),
    "squirrel": Species(
        id="squirrel",
        label="squirrel",
        skills=set(),
        likes="nuts and bark",
        tags={"squirrel"},
    ),
}

PROBLEMS = {
    "burr_tail": Problem(
        id="burr_tail",
        label="burrs tangled in a tail",
        intro="Tiny burrs had knotted themselves into the fur on the end of the tail, and every twitch made them pinch.",
        moan_line='"Oh dear," said {friend}, "my tail keeps catching. It hurts enough to make me moan."',
        risk_line="I might pull the burrs tighter and hurt my friend even more",
        solved_line="Soon the last burr slipped free, and {friend}'s tail swished softly instead of jerking with pain.",
        ending_image="A neat tail waved over the grass, and the morning felt gentle again.",
        needs_method="comb_reed",
        severity=1,
        tags={"burrs", "tail"},
    ),
    "mud_paw": Problem(
        id="mud_paw",
        label="a paw stuck in sticky mud",
        intro="One small paw was sunk deep in thick mud beside the path, and each wiggle only made the mud cling harder.",
        moan_line='"Ohhh," said {friend}, "I cannot lift my paw. I did not mean to make such a worried moan."',
        risk_line="I might tug too hard and make the paw ache while the mud still holds on",
        solved_line="Step by step, the path of stones gave {friend} a way to lean forward, and the muddy paw came free with a plop.",
        ending_image="A line of little stones crossed the mud, and the freed paw left tidy prints beside them.",
        needs_method="stone_path",
        severity=2,
        tags={"mud", "paw"},
    ),
    "branch_door": Problem(
        id="branch_door",
        label="a den door pinned by a fallen branch",
        intro="A heavy fallen branch had rolled across the little den door, trapping it shut so the friend could not get back inside.",
        moan_line='"This is awful," said {friend}. "My cozy den is right there, and all I can do is moan at the door."',
        risk_line="I might shove with my paws in the wrong place and make the branch roll harder against the door",
        solved_line="The branch lifted just enough, and {friend} nudged the door free with a relieved little hop.",
        ending_image="The den door stood open again, warm moss peeped from inside, and the path looked welcoming.",
        needs_method="lever_stick",
        severity=2,
        tags={"branch", "den"},
    ),
}

METHODS = {
    "comb_reed": Method(
        id="comb_reed",
        label="combing the tail with a reed",
        material="reeds",
        material_phrase="a long, smooth reed",
        solve_problem="burr_tail",
        needed_skill="patient",
        gather_line="So {hero} chose the longest, smoothest reed nearby and held it like a tiny comb.",
        action_line="{hero} worked slowly, easing the reed through the tangled fur one soft stroke at a time.",
        qa_text="used a long reed like a comb and worked slowly until the burrs came out",
        tags={"reeds", "careful"},
    ),
    "stone_path": Method(
        id="stone_path",
        label="making a stepping path of stones",
        material="stones",
        material_phrase="flat stepping stones",
        solve_problem="mud_paw",
        needed_skill="steady",
        gather_line="So {hero} gathered flat stones and laid them one by one over the stickiest part of the mud.",
        action_line="{hero} steadied the stones with careful paws and showed {friend} where to lean.",
        qa_text="laid flat stones over the mud so the stuck friend could step out without a hard yank",
        tags={"stones", "mud"},
    ),
    "lever_stick": Method(
        id="lever_stick",
        label="lifting with a strong stick",
        material="stick",
        material_phrase="a strong stick",
        solve_problem="branch_door",
        needed_skill="strong",
        gather_line="So {hero} found the strongest fallen stick nearby and wedged one end beneath the branch.",
        action_line="{hero} leaned down with all {hero}'s weight on the stick, and the branch rose a little.",
        qa_text="used a strong stick as a lever to lift the branch off the den door",
        tags={"stick", "lever"},
    ),
}

NAMES_GIRL = ["Mina", "Tansy", "Poppy", "Lula", "Wren", "Nell", "Hazel", "Daisy"]
NAMES_BOY = ["Pip", "Moss", "Robin", "Toby", "Ash", "Finn", "Ollie", "Bram"]


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    problem: str
    method: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
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
    "burrs": [
        (
            "What are burrs?",
            "Burrs are tiny prickly seed pods that cling to fur, feathers, or clothes. They stick because they have little hooks."
        )
    ],
    "mud": [
        (
            "Why can mud trap a paw?",
            "Wet mud can be sticky and heavy. When a paw presses down, the mud grips around it and makes it hard to lift back out."
        )
    ],
    "branch": [
        (
            "What is a lever?",
            "A lever is a strong bar, like a stick, that helps you lift something heavy by pushing on one end. It lets a small animal move more than it could with bare paws alone."
        )
    ],
    "reeds": [
        (
            "What is a reed?",
            "A reed is a tall, bendy plant that grows near water. Some reeds are smooth enough to brush gently through fur."
        )
    ],
    "stones": [
        (
            "Why do flat stones help in mud?",
            "Flat stones spread your weight and make a firmer place to step. That keeps feet or paws from sinking so deeply."
        )
    ],
    "problem_solving": [
        (
            "What does it mean to solve a problem?",
            "Solving a problem means stopping to think about what is wrong and choosing a plan that really helps. A good plan is careful, not just quick."
        )
    ],
}
KNOWLEDGE_ORDER = ["problem_solving", "burrs", "mud", "branch", "reeds", "stones"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    problem = f["problem"]
    method = f["method"]
    setting = f["setting"]
    return [
        f'Write a gentle animal story for a 3-to-5-year-old that includes the word "moan" and a problem that must be solved thoughtfully.',
        f"Tell a story set at {setting.label} where {hero.id} hears {friend.id}'s moan, studies the trouble carefully, and fixes {problem.label} by {method.label}.",
        f"Write a child-friendly story about two animal friends where the hero does not rush, but thinks first and chooses the right way to help.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    hero_cfg = f["hero_cfg"]
    friend_cfg = f["friend_cfg"]
    problem = f["problem"]
    method = f["method"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero_cfg.label} and {friend.id} the {friend_cfg.label}. They are two animal friends at {setting.label}."
        ),
        (
            f"Why did {hero.id} hurry over?",
            f"{hero.id} heard a moan and knew something was wrong. The sound led {hero.pronoun('object')} to {friend.id}, who was having trouble with {problem.label}."
        ),
        (
            f"What problem did {friend.id} have?",
            problem.intro.replace("One small paw", f"{friend.id}'s paw").replace("the friend", friend.id)
            .replace("A heavy fallen branch", "A heavy fallen branch")
            + f" That was why {friend.pronoun('subject')} sounded so worried."
        ),
        (
            f"Why did {hero.id} stop to think before helping?",
            f"{hero.id} did not want to make the problem worse. {f['risk_line'][0].upper()}{f['risk_line'][1:]}, so stopping to think protected {friend.id} from more pain."
        ),
        (
            f"How did {hero.id} solve the problem?",
            f"{hero.id} {method.qa_text}. The plan matched both the problem and the things available in the setting, so it worked gently."
        ),
    ]
    if f.get("solved"):
        qa.append(
            (
                "How did the story end?",
                f"It ended peacefully, with the trouble gone and both friends feeling relieved. {problem.ending_image}"
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"problem_solving"}
    tags |= set(world.facts["problem"].tags)
    tags |= set(world.facts["method"].tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="riverbank",
        hero="rabbit",
        friend="mouse",
        problem="burr_tail",
        method="comb_reed",
        hero_name="Pip",
        hero_gender="boy",
        friend_name="Mina",
        friend_gender="girl",
    ),
    StoryParams(
        place="orchard",
        hero="otter",
        friend="duck",
        problem="mud_paw",
        method="stone_path",
        hero_name="Tansy",
        hero_gender="girl",
        friend_name="Robin",
        friend_gender="boy",
    ),
    StoryParams(
        place="forest",
        hero="beaver",
        friend="mole",
        problem="branch_door",
        method="lever_stick",
        hero_name="Bram",
        hero_gender="boy",
        friend_name="Hazel",
        friend_gender="girl",
    ),
    StoryParams(
        place="meadow",
        hero="rabbit",
        friend="squirrel",
        problem="burr_tail",
        method="comb_reed",
        hero_name="Nell",
        hero_gender="girl",
        friend_name="Ash",
        friend_gender="boy",
    ),
]


ASP_RULES = r"""
valid(Place, Hero, Problem, Method) :-
    setting(Place), hero(Hero), problem(Problem), method(Method),
    solves(Method, Problem),
    requires_material(Method, Material), found_in(Place, Material),
    needs_skill(Method, Skill), has_skill(Hero, Skill).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for material in sorted(s.materials):
            lines.append(asp.fact("found_in", sid, material))
    for hid, hero in HERO_SPECIES.items():
        lines.append(asp.fact("hero", hid))
        for skill in sorted(hero.skills):
            lines.append(asp.fact("has_skill", hid, skill))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("solves", mid, method.solve_problem))
        lines.append(asp.fact("requires_material", mid, method.material))
        lines.append(asp.fact("needs_skill", mid, method.needed_skill))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    smoke_cases = [
        CURATED[0],
        StoryParams(
            place="riverbank",
            hero="rabbit",
            friend="mouse",
            problem="burr_tail",
            method="comb_reed",
            hero_name="Pip",
            hero_gender="boy",
            friend_name="Mina",
            friend_gender="girl",
        ),
    ]
    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            with contextlib.redirect_stdout(io.StringIO()):
                emit(sample, trace=True, qa=True, header=f"smoke {idx}")
        except Exception as err:
            rc = 1
            print(f"SMOKE TEST FAILED on case {idx}: {err}")
    if rc == 0:
        print("OK: smoke generation and emit passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal storyworld: a worried moan, a real problem, and a thoughtful fix."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HERO_SPECIES)
    ap.add_argument("--friend", choices=FRIEND_SPECIES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in (NAMES_GIRL if gender == "girl" else NAMES_BOY) if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.hero and args.problem and args.method:
        if not valid_combo(args.place, args.hero, args.problem, args.method):
            raise StoryError(
                explain_invalid(
                    SETTINGS[args.place],
                    HERO_SPECIES[args.hero],
                    PROBLEMS[args.problem],
                    METHODS[args.method],
                )
            )

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.hero is None or c[1] == args.hero)
        and (args.problem is None or c[2] == args.problem)
        and (args.method is None or c[3] == args.method)
    ]
    if not combos:
        if args.place and args.hero and args.problem and args.method:
            raise StoryError(
                explain_invalid(
                    SETTINGS[args.place],
                    HERO_SPECIES[args.hero],
                    PROBLEMS[args.problem],
                    METHODS[args.method],
                )
            )
        raise StoryError("(No valid combination matches the given options.)")

    place, hero, problem, method = rng.choice(sorted(combos))
    friend_choices = [k for k in FRIEND_SPECIES if k != hero]
    friend = args.friend or rng.choice(sorted(friend_choices))
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    hero_name = _pick_name(rng, hero_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=hero_name)
    return StoryParams(
        place=place,
        hero=hero,
        friend=friend,
        problem=problem,
        method=method,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place '{params.place}'.)")
    if params.hero not in HERO_SPECIES:
        raise StoryError(f"(Unknown hero '{params.hero}'.)")
    if params.friend not in FRIEND_SPECIES:
        raise StoryError(f"(Unknown friend '{params.friend}'.)")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem '{params.problem}'.)")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method '{params.method}'.)")

    setting = SETTINGS[params.place]
    hero_cfg = HERO_SPECIES[params.hero]
    friend_cfg = FRIEND_SPECIES[params.friend]
    problem = PROBLEMS[params.problem]
    method = METHODS[params.method]

    if not valid_combo(params.place, params.hero, params.problem, params.method):
        raise StoryError(explain_invalid(setting, hero_cfg, problem, method))

    world = tell(
        setting=setting,
        hero_cfg=hero_cfg,
        friend_cfg=friend_cfg,
        problem=problem,
        method=method,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
    )
    story_text = world.render()
    friend = world.facts["friend"]
    world.facts["problem"].moan_line.format(friend=friend.id)
    story_text = story_text.replace(problem.moan_line, problem.moan_line.format(friend=friend.id))

    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, hero, problem, method) combinations:\n")
        for place, hero, problem, method in combos:
            print(f"  {place:10} {hero:7} {problem:12} {method}")
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
            header = (
                f"### {p.hero_name} the {p.hero} helps {p.friend_name} with {p.problem} "
                f"at {p.place} using {p.method}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
