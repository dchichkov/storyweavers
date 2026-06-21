#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/intelligent_bravery_dialogue_inner_monologue_fable.py
======================================================================================

A standalone story world for a tiny fable-like domain built from the seed words
"intelligent", "bravery", "dialogue", and "inner monologue".

This world generates short, child-facing fables about a small animal who must
solve a practical problem by thinking clearly, speaking bravely, and acting at
the right moment. The simulation tracks physical state with meters and emotional
state with memes, and the prose is driven from that state rather than from a
fixed paragraph template.

Core premise
------------
A small creature notices a problem in the village: a useful thing is stuck, lost,
or blocked, and a risky shortcut would make things worse. The creature first has
an inner monologue, then a dialogue beat with a warning or a helpful question,
then a brave action, and finally a resolution image that proves the change.

The fable tone comes from:
- simple animal characters with clear roles,
- a direct moral embedded in the ending,
- dialogue and reflective inner speech,
- a small, concrete turn from confusion to wise action.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/intelligent_bravery_dialogue_inner_monologue_fable.py
    python storyworlds/worlds/gpt-5.4-mini/intelligent_bravery_dialogue_inner_monologue_fable.py --all
    python storyworlds/worlds/gpt-5.4-mini/intelligent_bravery_dialogue_inner_monologue_fable.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/intelligent_bravery_dialogue_inner_monologue_fable.py --verify
    python storyworlds/worlds/gpt-5.4-mini/intelligent_bravery_dialogue_inner_monologue_fable.py --show-asp
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
BRAVERY_INIT = 6.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen", "rabbit", "mouse", "squirrel", "goat", "duck"}
        male = {"boy", "father", "dad", "man", "fox", "lion", "wolf", "crow", "tortoise", "bear"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    scene: str
    opening: str
    place_noun: str
    weather: str
    moral_image: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    risk: str
    cause: str
    symbol: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Solution:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["trouble"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["fixed"] < THRESHOLD:
            continue
        sig = ("relief", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("worry", "social", _r_worry),
    Rule("relief", "social", _r_relief),
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


def reasonableness(problem: Problem, solution: Solution) -> bool:
    return solution.sense >= SENSE_MIN and problem.id in PROBLEMS and solution.id in SOLUTIONS


def sensible_solutions() -> list[Solution]:
    return [s for s in SOLUTIONS.values() if s.sense >= SENSE_MIN]


def best_solution() -> Solution:
    return max(SOLUTIONS.values(), key=lambda s: s.sense)


def would_fix(problem: Problem, solution: Solution) -> bool:
    return solution.power >= 1


def predict_result(world: World, problem: Problem, solution: Solution) -> dict:
    sim = world.copy()
    _do_problem(sim, sim.get("hero_problem"), narrate=False)
    _do_solution(sim, sim.get("hero"), sim.get("friend"), problem, solution, narrate=False)
    return {
        "fixed": sim.get("hero").meters["fixed"] >= THRESHOLD,
        "trouble": sim.get("hero_problem").meters["trouble"] >= THRESHOLD,
    }


def _do_problem(world: World, thing: Entity, narrate: bool = True) -> None:
    thing.meters["trouble"] += 1
    thing.meters["stuck"] += 1
    propagate(world, narrate=narrate)


def think(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["thought"] += 1
    world.say(
        f"{hero.id} saw the {problem.label} and became very still. "
        f"Inside, {hero.pronoun()} thought, \"If I rush, I may make the {problem.label} worse. "
        f"But if I think carefully, I may find the wise way.\""
    )


def dialogue(world: World, hero: Entity, friend: Entity, problem: Problem) -> None:
    hero.memes["courage"] += 1
    friend.memes["concern"] += 1
    world.say(
        f"\"{problem.phrase},\" said {friend.id} softly. \"What will you do?\""
    )
    world.say(
        f"\"I will not be foolish,\" said {hero.id}. \"I will be intelligent and brave enough to ask for help if I need it.\""
    )


def brave_move(world: World, hero: Entity, friend: Entity, problem: Problem) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} took a breath, stepped closer, and tried the careful way instead of the quick way."
    )


def _do_solution(world: World, hero: Entity, friend: Entity, problem: Problem, solution: Solution, narrate: bool = True) -> None:
    if not would_fix(problem, solution):
        return
    hero.meters["fixed"] += 1
    hero.meters["trouble"] = 0.0
    friend.meters["fixed"] += 1
    propagate(world, narrate=narrate)


def resolve(world: World, hero: Entity, friend: Entity, setting: Setting, problem: Problem, solution: Solution) -> None:
    body = solution.text.replace("{problem}", problem.label)
    world.say(
        f"Together, {hero.id} and {friend.id} {body}."
    )
    world.say(
        f"{setting.moral_image} That is why the little fable remembered that intelligence and bravery can travel together."
    )


def tell(setting: Setting, problem: Problem, solution: Solution,
         hero_name: str = "Milo", hero_type: str = "mouse",
         friend_name: str = "Tara", friend_type: str = "sparrow") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", traits=["small", "intelligent"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend", traits=["kind"]))
    trouble = world.add(Entity(id="hero_problem", kind="thing", type="thing", label=problem.label, role="problem"))

    world.say(
        f"Once in {setting.scene}, {hero.id} lived where {setting.opening}."
    )
    world.say(
        f"{hero.id} was small, but {hero.pronoun()} was intelligent, and everyone knew {hero.pronoun()} noticed details other creatures missed."
    )
    world.say(
        f"{friend.id} stayed near, because little {friend.type}s and {hero.type}s were wise to listen to one another."
    )

    world.para()
    think(world, hero, problem)
    dialogue(world, hero, friend, problem)
    brave_move(world, hero, friend, problem)

    world.para()
    _do_problem(world, trouble)
    world.say(
        f"The {problem.label} became harder at once. {problem.risk} {problem.symbol}"
    )
    _do_solution(world, hero, friend, problem, solution)
    resolve(world, hero, friend, setting, problem, solution)

    world.facts.update(
        hero=hero,
        friend=friend,
        problem=problem,
        solution=solution,
        setting=setting,
        trouble=trouble,
        fixed=hero.meters["fixed"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "meadow": Setting(
        id="meadow",
        scene="a bright meadow beside a little village",
        opening="the flowers bent in the wind and the bees hummed near the clover",
        place_noun="meadow",
        weather="soft daylight",
        moral_image="By evening, the clover stood tall again.",
    ),
    "orchard": Setting(
        id="orchard",
        scene="an old orchard with silver grass under the trees",
        opening="the apples shone above and the grass hid little paths",
        place_noun="orchard",
        weather="golden afternoon",
        moral_image="Soon, the apples could be shared with a calm heart.",
    ),
    "brook": Setting(
        id="brook",
        scene="a narrow brook behind the hill",
        opening="the water whispered over stones while reeds leaned kindly",
        place_noun="brook",
        weather="cool morning",
        moral_image="In the end, the brook sang softly again.",
    ),
}

PROBLEMS = {
    "lost_keys": Problem(
        "lost_keys",
        "lost key",
        "the key is gone",
        "A gate can stay closed when the key is missing.",
        "A quick search might scatter the grass and waste time.",
        "key",
        {"search", "care", "help"},
    ),
    "fallen_basket": Problem(
        "fallen_basket",
        "fallen basket",
        "the basket has tipped over",
        "If no one fixes it, the berries spill into the dirt.",
        "A hasty tug could rip the handle.",
        "basket",
        {"berries", "care", "help"},
    ),
    "stuck_gate": Problem(
        "stuck_gate",
        "stuck gate",
        "the gate will not open",
        "A stuck gate can keep friends apart.",
        "Shoving it too hard may make the latch bend.",
        "gate",
        {"gate", "help", "care"},
    ),
    "heavy_branch": Problem(
        "heavy_branch",
        "heavy branch",
        "the branch has fallen across the path",
        "A blocked path can make travelers turn back.",
        "Pushing with one paw at once can only make the branch roll.",
        "branch",
        {"path", "help", "brave"},
    ),
}

SOLUTIONS = {
    "call_help": Solution(
        "call_help",
        3,
        3,
        "called the other animals and lifted the {problem} together, one careful pull at a time",
        "called out, but the {problem} stayed in place",
        "called the others and fixed the {problem}",
        {"help", "brave"},
    ),
    "look_closely": Solution(
        "look_closely",
        3,
        2,
        "looked closely, found the small trick, and moved the {problem} without making a fuss",
        "looked closely, but could not solve the {problem}",
        "looked closely and solved the {problem}",
        {"care", "intelligent"},
    ),
    "use_tool": Solution(
        "use_tool",
        2,
        2,
        "found a simple tool nearby and used it to nudge the {problem} into the right place",
        "used a tool, but it was not enough for the {problem}",
        "used a simple tool to fix the {problem}",
        {"tool", "brave"},
    ),
    "ask_advice": Solution(
        "ask_advice",
        3,
        2,
        "asked a wiser neighbor, listened well, and then solved the {problem} in the safe way",
        "asked for advice, but the answer did not fit the {problem}",
        "asked advice and solved the {problem}",
        {"dialogue", "intelligent"},
    ),
    "pull_together": Solution(
        "pull_together",
        2,
        2,
        "pulled steadily with a friend until the {problem} finally moved",
        "pulled steadily, but the {problem} was too heavy",
        "pulled the {problem} together with a friend",
        {"brave", "friendship"},
    ),
}



@dataclass
class StoryParams:
    setting: str
    problem: str
    solution: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")

CURATED = [
    ("meadow", "lost_keys", "look_closely"),
    ("orchard", "fallen_basket", "call_help"),
    ("brook", "stuck_gate", "ask_advice"),
    ("meadow", "heavy_branch", "pull_together"),
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid in PROBLEMS:
            for sol_id in SOLUTIONS:
                if would_fix(PROBLEMS[pid], SOLUTIONS[sol_id]):
                    combos.append((sid, pid, sol_id))
    return combos


KNOWLEDGE = {
    "intelligent": [(
        "What does intelligent mean?",
        "Intelligent means being good at understanding things, noticing patterns, and choosing smart answers. It helps a creature solve problems without rushing."
    )],
    "bravery": [(
        "What is bravery?",
        "Bravery is doing the right thing even when you feel worried or small. It does not mean never being afraid."
    )],
    "dialogue": [(
        "What is dialogue in a story?",
        "Dialogue is when characters speak to each other. It lets readers hear their thoughts and learn how they work together."
    )],
    "inner": [(
        "What is an inner monologue?",
        "An inner monologue is the quiet voice inside a character's head. It shows what the character is thinking before they speak or act."
    )],
    "fable": [(
        "What is a fable?",
        "A fable is a short story, often with animals, that teaches a lesson. The lesson usually comes at the end."
    )],
    "help": [(
        "Why do creatures ask for help?",
        "Creatures ask for help when a problem is too hard for one small pair of hands or paws. Asking can be wise, not weak."
    )],
    "gate": [(
        "Why can a gate matter in a story?",
        "A gate can keep a path open or closed. When it is stuck, the whole village may need a careful fix."
    )],
    "branch": [(
        "Why can a fallen branch block a path?",
        "A fallen branch can be heavy and wide, so it can stop animals from walking through. That makes the path hard to use."
    )],
    "basket": [(
        "What does a basket do?",
        "A basket carries things safely, like berries or bread. If it tips over, the things can spill out."
    )],
    "key": [(
        "What is a key for?",
        "A key opens a lock so a gate, door, or box can be used again. Losing it can stop a plan."
    )],
}
KNOWLEDGE_ORDER = ["intelligent", "bravery", "dialogue", "inner", "fable", "help", "gate", "branch", "basket", "key"]


def describe_problem(problem: Problem) -> str:
    return {
        "lost key": "the key was missing from the hook",
        "fallen basket": "the basket had tipped and berries were spilling",
        "stuck gate": "the gate would not swing open",
        "heavy branch": "a heavy branch lay across the path",
    }[problem.label]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    setting = f["setting"]
    return [
        f'Write a fable for a small child that includes the word "intelligent" and shows a brave little hero solving {problem.label}.',
        f"Tell a short animal fable where {hero.id} thinks silently first, then speaks to a friend, and finally solves the {problem.label} in {setting.place_noun}.",
        f"Write a gentle moral story with dialogue and inner monologue about a small animal who is intelligent enough to be brave when {describe_problem(problem)}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    problem = f["problem"]
    solution = f["solution"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"The story is about {hero.id}, a small {hero.type} who lives in {setting.scene}. {friend.id} stays near and helps with the problem."
        ),
        (
            f"What was the problem in the story?",
            f"The problem was {problem.phrase}. It made the path or village hard to use until someone fixed it."
        ),
        (
            f"What did {hero.id} do first?",
            f"First, {hero.id} listened to a quiet inner thought and looked carefully at the problem. That helped {hero.pronoun()} choose a smart next step."
        ),
        (
            "How did the characters speak to each other?",
            f"They had a short dialogue. {friend.id} asked a question, and {hero.id} answered bravely instead of rushing."
        ),
        (
            "Why was the hero brave?",
            f"{hero.id} was brave because {hero.pronoun()} faced the problem instead of hiding from it. {hero.pronoun().capitalize()} chose the careful way even though it took courage."
        ),
        (
            "How was the problem solved?",
            f"They {solution.qa_text.replace('{problem}', problem.label)}. That changed the world from stuck to fixed."
        ),
        (
            "How did the story end?",
            f"It ended with the {problem.label} no longer causing trouble, and the setting looking calm again. The last image shows that wisdom and bravery worked together."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["problem"].tags) | set(world.facts["solution"].tags)
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


def tell(setting: Setting, problem: Problem, solution: Solution,
         hero_name: str = "Milo", hero_type: str = "mouse",
         friend_name: str = "Tara", friend_type: str = "sparrow") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", traits=["small", "intelligent"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    trouble = world.add(Entity(id="hero_problem", kind="thing", type="thing", label=problem.label, role="problem"))

    world.say(
        f"Once there was {hero.id}, a little {hero.type} in {setting.scene}. "
        f"{setting.opening}."
    )
    world.say(
        f"Everyone knew {hero.id} was intelligent, but {hero.id} was also small, and small creatures still had to choose brave actions."
    )
    world.say(
        f"{friend.id} watched close by, because a good friend can make a hard day feel lighter."
    )

    world.para()
    think(world, hero, problem)
    dialogue(world, hero, friend, problem)
    brave_move(world, hero, friend, problem)

    world.para()
    _do_problem(world, trouble)
    world.say(
        f"The trouble grew clearer at once: {problem.risk} {problem.symbol}."
    )
    _do_solution(world, hero, friend, problem, solution)
    resolve(world, hero, friend, setting, problem, solution)

    world.facts.update(
        hero=hero,
        friend=friend,
        problem=problem,
        solution=solution,
        setting=setting,
        trouble=trouble,
        outcome="fixed" if hero.meters["fixed"] >= THRESHOLD else "unfixed",
    )
    return world


def think(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["thought"] += 1
    world.say(
        f"Inside, {hero.id} thought, \"If I hurry, I might only make the {problem.label} worse. "
        f"If I pause, I may find the best way.\""
    )


def dialogue(world: World, hero: Entity, friend: Entity, problem: Problem) -> None:
    friend.memes["curiosity"] += 1
    hero.memes["courage"] += 1
    world.say(
        f"\"What do you see?\" asked {friend.id}."
    )
    world.say(
        f"\"I see that {problem.phrase},\" said {hero.id}. \"I think the smart way is also the brave way.\""
    )


def brave_move(world: World, hero: Entity, friend: Entity, problem: Problem) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} took one brave breath and reached for the careful fix."
    )


def _do_solution(world: World, hero: Entity, friend: Entity, problem: Problem, solution: Solution, narrate: bool = True) -> None:
    if not would_fix(problem, solution):
        return
    hero.meters["fixed"] += 1
    friend.meters["fixed"] += 1
    hero.meters["trouble"] = 0.0
    world.get("hero_problem").meters["trouble"] = 0.0
    world.get("hero_problem").meters["stuck"] = 0.0
    propagate(world, narrate=narrate)


def resolve(world: World, hero: Entity, friend: Entity, setting: Setting, problem: Problem, solution: Solution) -> None:
    body = solution.text.replace("{problem}", problem.label)
    world.say(
        f"Together, {hero.id} and {friend.id} {body}."
    )
    world.say(
        f"{setting.moral_image} The fable's lesson was plain: a small creature may be tiny, but an intelligent heart can still be brave."
    )


def valid_story_params(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str]:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.solution is None or c[2] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    return rng.choice(sorted(combos))


def explain_rejection(problem: Problem, solution: Solution) -> str:
    return (
        f"(No story: the solution '{solution.id}' is not a sensible fit for {problem.label}. "
        f"A fable needs a clear problem and a believable wise action.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "fixed" if would_fix(PROBLEMS[params.problem], SOLUTIONS[params.solution]) else "unfixed"


def best_valid_solution_id() -> str:
    return best_solution().id


def valid_problem_solution_pairs() -> list[tuple[str, str]]:
    return [(p, s) for _, p, s in valid_combos()]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny fable about intelligent bravery, dialogue, and inner thought."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["mouse", "sparrow", "rabbit", "tortoise", "squirrel", "fox"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=["mouse", "sparrow", "rabbit", "tortoise", "squirrel", "fox"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.solution:
        if not would_fix(PROBLEMS[args.problem], SOLUTIONS[args.solution]):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], SOLUTIONS[args.solution]))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.solution is None or c[2] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, problem, solution = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["mouse", "sparrow", "rabbit", "tortoise", "squirrel", "fox"])
    friend_type = args.friend_type or rng.choice([t for t in ["mouse", "sparrow", "rabbit", "tortoise", "squirrel", "fox"] if t != hero_type])

    hero_pool = {
        "mouse": ["Milo", "Mina", "Pip", "Timo", "Nia"],
        "sparrow": ["Tara", "Sora", "Pia", "Bibi", "Nori"],
        "rabbit": ["Luna", "Poppy", "Wren", "Miri", "Hareta"],
        "tortoise": ["Toby", "Tessa", "Orin", "Uma", "Bram"],
        "squirrel": ["Suki", "Rolo", "Fenna", "Kiri", "Nico"],
        "fox": ["Fable", "Rin", "Vela", "Jorin", "Safi"],
    }
    friend_pool = {
        "mouse": ["Milo", "Mina", "Pip", "Timo", "Nia"],
        "sparrow": ["Tara", "Sora", "Pia", "Bibi", "Nori"],
        "rabbit": ["Luna", "Poppy", "Wren", "Miri", "Hareta"],
        "tortoise": ["Toby", "Tessa", "Orin", "Uma", "Bram"],
        "squirrel": ["Suki", "Rolo", "Fenna", "Kiri", "Nico"],
        "fox": ["Fable", "Rin", "Vela", "Jorin", "Safi"],
    }
    hero = args.hero or rng.choice(hero_pool[hero_type])
    friend_candidates = [n for n in friend_pool[friend_type] if n != hero]
    friend = args.friend or rng.choice(friend_candidates or friend_pool[friend_type])
    return StoryParams(setting, problem, solution, hero, hero_type, friend, friend_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], SOLUTIONS[params.solution], params.hero, params.hero_type, params.friend, params.friend_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, O) :- setting(S), problem(P), solution(O), fixable(P, O).
fixable(P, O) :- problem(P), solution(O), power(O, Pow), Pow >= 1.
outcome(fixed) :- chosen_problem(P), chosen_solution(O), fixable(P, O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for oid, sol in SOLUTIONS.items():
        lines.append(asp.fact("solution", oid))
        lines.append(asp.fact("power", oid, sol.power))
        lines.append(asp.fact("sense", oid, sol.sense))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_solution", params.solution),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        print("  only in python:", sorted(py - cl))
        print("  only in clingo:", sorted(cl - py))
    cases = [StoryParams(s, p, o, "Milo", "mouse", "Tara", "sparrow") for s, p, o in CURATED]
    bad = sum(1 for c in cases if asp_outcome(c) != outcome_of(c))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} curated scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad} curated outcomes differ.")
    return rc


def explain_solution(rid: str) -> str:
    sol = SOLUTIONS[rid]
    better = " / ".join(sorted(x.id for x in sensible_solutions()))
    return (
        f"(Refusing solution '{rid}': it scores too low on common sense "
        f"(sense={sol.sense} < {SENSE_MIN}). A fable should prefer a wise and usable response. Try: {better}.)"
    )


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_show_program() -> str:
    return asp_program("", "#show valid/3.\n#show sensible/1.")


def world_knowledge_focus(params: StoryParams) -> list[str]:
    return sorted(set(PROBLEMS[params.problem].tags) | set(SOLUTIONS[params.solution].tags) | {"intelligent", "bravery", "dialogue", "inner", "fable"})


def format_header(params: StoryParams) -> str:
    return f"### {params.hero}: {params.problem} with {params.solution} ({params.setting})"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_show_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible solutions: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, problem, solution) combos:\n")
        for s, p, o in combos:
            print(f"  {s:9} {p:14} {o}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(s, p, o, "Milo", "mouse", "Tara", "sparrow"))
                   for s, p, o in CURATED]
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
            header = format_header(p)
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
