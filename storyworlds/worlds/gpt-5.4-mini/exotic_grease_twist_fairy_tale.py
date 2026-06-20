#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/exotic_grease_twist_fairy_tale.py
==================================================================

A standalone story world for a tiny fairy-tale domain about a child, a stubborn
twist, and a jar of exotic grease that solves the problem in a careful, magical
way.

Seed idea
---------
A small fairy-tale problem needs a practical fix: a castle's twisty gate or
wind-up treasure box is stuck. The child wants to force it, but a gentle helper
knows a better way: use a little exotic grease. The story turns on the idea that
a strange-looking tool can be useful when used wisely, and that the wrong amount
makes a mess.

This world is built as a classical simulation:
- typed entities with physical meters and emotional memes
- forward-chained causal rules
- a reasonableness gate
- a Python gate plus an inline ASP twin
- grounded prompts and QA from world state, not from rendered English

It supports:
    - default random generation
    - -n
    - --all
    - --seed
    - --trace
    - --qa
    - --json
    - --asp
    - --verify
    - --show-asp
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "princess", "woman"}
        male = {"boy", "father", "king", "prince", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "queen": "queen",
                "king": "king"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    scene: str
    mood: str
    dark_spot: str

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
    description: str
    stuck_part: str
    spread_part: str
    need: str
    twisty: bool = True
    greasy: bool = True

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
class Grease:
    id: str
    label: str
    phrase: str
    origin: str
    shine: str
    slip: str
    safe_amount: str
    makes_mess: bool = True

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
class Fix:
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


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["greasy"] < THRESHOLD:
            continue
        sig = ("mess", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["mess"] += 1
        e.memes["embarrassment"] += 1
        out.append("__mess__")
    return out


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["slippery"] < THRESHOLD:
            continue
        sig = ("slip", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "hero" in world.entities:
            world.get("hero").memes["surprise"] += 1
        out.append("__slip__")
    return out


CAUSAL_RULES = [
    Rule("mess", "physical", _r_mess),
    Rule("slip", "physical", _r_slip),
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


def reasonableness(problem: Problem, grease: Grease, fix: Fix) -> bool:
    return problem.twisty and problem.greasy and fix.sense >= SENSE_MIN and grease.makes_mess


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PROBLEMS:
            for g in GREASES:
                for f in FIXES.values():
                    if reasonableness(p, g, f):
                        combos.append((s, p, g, f))
    return combos


def is_success(problem: Problem, fix: Fix, delay: int) -> bool:
    return fix.power >= problem_difficulty(problem, delay)


def problem_difficulty(problem: Problem, delay: int) -> int:
    return 1 + delay


def _apply_problem(world: World, problem: Problem) -> None:
    hero = world.get("hero")
    target = world.get("problem")
    target.meters["stuck"] += 1
    hero.memes["frustration"] += 1
    if problem.twisty:
        target.meters["twist"] += 1
    propagate(world, narrate=False)


def introduce(world: World, hero: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"Once in {setting.place}, {hero.id} and {helper.id} came to {setting.scene}. "
        f"The day felt {setting.mood}, and {setting.dark_spot} held a little secret."
    )


def state_problem(world: World, hero: Entity, problem: Problem) -> None:
    world.say(
        f"They found {problem.description}. {hero.id} tugged at it, but it would not move."
    )
    hero.memes["curiosity"] += 1


def want_fix(world: World, hero: Entity, helper: Entity, grease: Grease, problem: Problem) -> None:
    hero.memes["desire"] += 1
    world.say(
        f'"We should force it open," {hero.id} said. But {helper.id} shook {helper.pronoun("possessive")} head and held up {grease.phrase}.'
    )
    world.say(
        f'"This came from {grease.origin}," {helper.id} said. "A tiny bit can make the twisty part glide."'
    )


def warn(world: World, helper: Entity, hero: Entity, grease: Grease, problem: Problem) -> None:
    hero.memes["warning"] += 1
    world.say(
        f'{helper.id} pointed to the {problem.stuck_part} and warned, "If we use too much, it will get {grease.slip} and messy instead of fixed."'
    )


def use_grease(world: World, problem: Problem, grease: Grease) -> None:
    world.get("problem").meters["greasy"] += 1
    world.get("problem").meters["slippery"] += 1
    world.say(
        f"{grease.safe_amount.capitalize()}, {grease.shine}. {grease.label.capitalize()} went on the {problem.stuck_part}, and the twisty part began to turn."
    )


def twist_open(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At last, {hero.id} gave the {problem.label} one careful twist. It opened with a soft click, like a fairy tale answering kindly."
    )


def grease_mess(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    world.say(
        f"But a shiny smear spilled onto the floor stones, and the whole spot became slippery."
    )
    hero.memes["alarm"] += 1
    helper.memes["care"] += 1


def rescue(world: World, fix: Fix) -> None:
    world.say(
        f"A nearby cloth caught the extra grease, and the little mess was wiped away."
    )
    world.say(
        f"{fix.text}."
    )


def ending(world: World, hero: Entity, helper: Entity, problem: Problem, fix: Fix, success: bool) -> None:
    if success:
        world.say(
            f"In the end, {hero.id} and {helper.id} left the place tidy, and {problem.label} stood open and kind."
        )
    else:
        world.say(
            f"In the end, they stood safely aside, and the {problem.label} stayed shut until a steadier plan could help."
        )


def tell(setting: Setting, problem: Problem, grease: Grease, fix: Fix,
         hero_name: str = "Mara", helper_name: str = "Twist",
         hero_gender: str = "girl", helper_gender: str = "fox",
         parent_type: str = "queen", delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Queen", kind="character", type=parent_type, role="parent", label="the queen"))
    target = world.add(Entity(id="problem", type="thing", label=problem.label))
    world.facts["parent"] = parent
    world.facts["setting"] = setting
    world.facts["problem_cfg"] = problem
    world.facts["grease_cfg"] = grease
    world.facts["fix"] = fix
    world.facts["delay"] = delay

    introduce(world, hero, helper, setting)
    state_problem(world, hero, problem)
    world.para()
    want_fix(world, hero, helper, grease, problem)
    warn(world, helper, hero, grease, problem)

    success = is_success(problem, fix, delay)
    if success:
        use_grease(world, problem, grease)
        twist_open(world, hero, helper, problem)
        rescue(world, fix)
    else:
        use_grease(world, problem, grease)
        grease_mess(world, hero, helper, problem)
    world.para()
    ending(world, hero, helper, problem, fix, success)

    world.facts.update(hero=hero, helper=helper, target=target, success=success)
    return world


SETTINGS = {
    "tower": Setting("tower", "the old tower", "the old tower hall", "golden and quiet", "a twisty iron gate"),
    "garden": Setting("garden", "the moon garden", "the moon garden path", "soft and bright", "a curled rose latch"),
    "castle": Setting("castle", "the castle cellar", "the castle cellar corridor", "cool and hush-quiet", "a spiral door"),
}

PROBLEMS = {
    "gate": Problem("gate", "twisty iron gate", "a twisty iron gate", "gate hinge", "gate hinge", "open the way"),
    "latch": Problem("latch", "curled rose latch", "a curled rose latch", "latch spring", "latch spring", "unlock the door"),
    "door": Problem("door", "spiral door", "a spiral door", "door wheel", "door wheel", "turn the wheel"),
}

GREASES = {
    "exotic": Grease("exotic", "exotic grease", "a tiny jar of exotic grease", "the faraway spice road", "silver-bright", "slippery", "just a pea-sized dab"),
    "honey": Grease("honey", "golden grease", "a spoon of golden grease", "the beekeeper's hill", "amber-bright", "slick", "only a little"),
    "lantern": Grease("lantern", "lantern grease", "a small tin of lantern grease", "the lamp room", "warm and glowing", "slippy", "a careful swipe"),
}

FIXES = {
    "brush": Fix("brush", 3, 3, "They used a tiny brush, and the grease stayed where it belonged", "They used a tiny brush, but the twist still fought back", "used a tiny brush"),
    "cloth": Fix("cloth", 2, 2, "They folded a cloth under the latch and wiped away the extra shine", "They tried to wipe it clean, but the mechanism stayed stuck", "wiped away the extra shine"),
    "dab": Fix("dab", 3, 4, "They dabbed only a little, and the twisty part turned sweetly at once", "They dabbed, but the mechanism would not budge", "dabbed only a little"),
}

GIRL_NAMES = ["Mara", "Lina", "Elsa", "Nora", "Iris", "Anya", "Clara", "Rose"]
BOY_NAMES = ["Owen", "Finn", "Evan", "Theo", "Bram", "Silas", "Leo", "Jasper"]


def valid_combos_simple() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid in PROBLEMS:
            for gid in GREASES:
                for fid in FIXES:
                    if reasonableness(PROBLEMS[pid], GREASES[gid], FIXES[fid]):
                        combos.append((sid, pid, gid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    problem: str
    grease: str
    fix: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    delay: int = 0
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


KNOWLEDGE = {
    "grease": [("What does grease do?",
                "Grease helps moving parts slide more easily instead of rubbing and sticking.")],
    "exotic": [("What does exotic mean?",
                "Exotic means unusual or from far away, like something that feels rare and special.")],
    "twist": [("What is a twisty thing?",
               "A twisty thing turns around instead of moving straight, like a curly latch or a spinning wheel.")],
    "gate": [("What is a gate?",
             "A gate is a door or barrier that can open and close a path.")],
    "latch": [("What is a latch?",
               "A latch is a little device that keeps a door or gate shut until you lift or turn it.")],
    "door": [("What is a door wheel?",
              "A door wheel is a round part you turn with your hand to open a door or window.")],
    "mess": [("Why can grease be messy?",
              "Grease can be messy because it is slippery and can smear onto floors and hands.")],
}
KNOWLEDGE_ORDER = ["grease", "exotic", "twist", "gate", "latch", "door", "mess"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prob = f["problem_cfg"]
    grease = f["grease_cfg"]
    return [
        f'Write a fairy-tale story for a 3-to-5-year-old that includes the words "{grease.label}" and "{prob.label}".',
        f"Tell a gentle story where {helper.id} shows {hero.id} how to fix {prob.description} with {grease.phrase}, and include a small twist.",
        f'Write a magical story about a stubborn {prob.label} and a little jar of {grease.label} that ends with a safe, happy fix.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    prob = f["problem_cfg"]
    grease = f["grease_cfg"]
    fix = f["fix"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, {helper.id}, and {parent.label_word}. They all take part in the small fairy-tale problem and its fix."),
        ("What was stuck?",
         f"{prob.description} was stuck. It would not turn until they found the right way to help it move."),
        ("What did the helper suggest?",
         f"{helper.id} suggested using {grease.phrase} carefully instead of forcing the {prob.label}. That was the wise way to handle the twisty part."),
    ]
    if f.get("success"):
        qa.append((
            "How did they solve the problem?",
            f"They solved it by {fix.qa_text} and then giving the {prob.label} one careful twist. The little change was enough to open the way without making a big mess."
        ))
        qa.append((
            "How did the story end?",
            f"It ended happily. {hero.id} and {helper.id} left the place tidy, and the {prob.label} opened as if it had been waiting for a gentle hand."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended with the problem still stuck, but everyone stayed safe. They learned that a twisty thing needs a careful plan, not a rushed pull."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["problem_cfg"].id for _ in [0])
    tags.add(world.facts["grease_cfg"].id)
    tags.add(world.facts["fix"].id)
    tags.add("grease")
    tags.add("twist")
    tags.add("exotic")
    out: list[tuple[str, str]] = []
    for k in KNOWLEDGE_ORDER:
        if k in tags and k in KNOWLEDGE:
            out.extend(KNOWLEDGE[k])
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("tower", "gate", "exotic", "brush", "Mara", "girl", "Twist", "fox", "queen", 0),
    StoryParams("garden", "latch", "honey", "cloth", "Lina", "girl", "Twist", "fox", "mother", 1),
    StoryParams("castle", "door", "lantern", "dab", "Owen", "boy", "Twist", "fox", "father", 0),
]


def explain_rejection(problem: Problem, grease: Grease) -> str:
    return (
        f"(No story: this setup is not reasonable enough. The {problem.label} is twisty, "
        f"but the chosen plan would not make a clear, gentle fix. Try one of the curated twisty gates, latches, or doors with {grease.label}.)"
    )


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense (sense={fix.sense} < {SENSE_MIN}). "
        f"A fairy-tale story should prefer a wiser, steadier fix.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "fixed" if is_success(PROBLEMS[params.problem], FIXES[params.fix], params.delay) else "messy"


ASP_RULES = r"""
valid(S, P, G) :- setting(S), problem(P), grease(G),
                  twisty(P), greasy(P), fix_ok(P, G).
fixed(P, F) :- fix(F), sense(F, N), sense_min(M), N >= M.
outcome(fixed) :- chosen_problem(P), chosen_fix(F), power(F, Pow), difficulty(P, D), Pow >= D.
outcome(messy) :- chosen_problem(P), chosen_fix(F), power(F, Pow), difficulty(P, D), Pow < D.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if p.twisty:
            lines.append(asp.fact("twisty", pid))
        if p.greasy:
            lines.append(asp.fact("greasy", pid))
        lines.append(asp.fact("difficulty", pid, 1))
    for gid in GREASES:
        lines.append(asp.fact("grease", gid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
        asp.fact("chosen_fix", params.fix),
        asp.fact("difficulty", params.problem, 1),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        if a - b:
            print("  only in clingo:", sorted(a - b))
        if b - a:
            print("  only in python:", sorted(b - a))
    smoke = generate(CURATED[0])
    if not smoke.story.strip():
        print("MISMATCH: smoke story is empty.")
        return 1
    print("OK: smoke generation produced a story.")
    cases = [p for p in CURATED]
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} curated cases.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale story world about exotic grease and a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--grease", choices=GREASES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["queen", "king", "mother", "father"])
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
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))
    if args.grease and args.problem:
        pass
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.grease is None or c[2] == args.grease)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, grease = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    if FIXES[fix].sense < SENSE_MIN:
        fix = "brush"
    hero_name = rng.choice(GIRL_NAMES if rng.random() < 0.5 else BOY_NAMES)
    hero_gender = "girl" if hero_name in GIRL_NAMES else "boy"
    helper_name = "Twist"
    helper_gender = "fox"
    parent = args.parent or rng.choice(["queen", "king", "mother", "father"])
    delay = rng.randint(0, 1)
    return StoryParams(setting, problem, grease, fix, hero_name, hero_gender, helper_name, helper_gender, parent, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], GREASES[params.grease],
                 FIXES[params.fix], params.hero_name, params.helper_name,
                 params.hero_gender, params.helper_gender, params.parent, params.delay)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show fixed/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
