#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/suspicious_squadron_conflict_kindness_space_adventure.py
===================================================================================

A standalone story world for a tiny space-adventure domain: two children on a
small outpost spot a suspicious squadron of little ships approaching in the
dark. One child wants to treat the visitors like a threat, but the other pauses
to read the signs. The ships are not attackers at all; they are in trouble, and
kindness becomes the brave solution.

This world models:
- a child-facing conflict ("they look suspicious" vs "let's understand first")
- a concrete need the incoming squadron has
- a reasonableness gate that only allows help that truly fits the need
- a declarative ASP twin that checks the same compatibility logic and outcome

Run it
------
    python storyworlds/worlds/gpt-5.4/suspicious_squadron_conflict_kindness_space_adventure.py
    python storyworlds/worlds/gpt-5.4/suspicious_squadron_conflict_kindness_space_adventure.py --setting moonbase --visitor glider_squadron --problem low_power --aid beacon
    python storyworlds/worlds/gpt-5.4/suspicious_squadron_conflict_kindness_space_adventure.py --problem torn_sail --aid beacon
    python storyworlds/worlds/gpt-5.4/suspicious_squadron_conflict_kindness_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/suspicious_squadron_conflict_kindness_space_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/suspicious_squadron_conflict_kindness_space_adventure.py --verify
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
KINDNESS_MIN = 2


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Setting:
    id: str
    place: str
    sky: str
    window: str
    floor: str
    ending: str
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
class Visitor:
    id: str
    label: str
    phrase: str
    squadron: str
    look: str
    motion: str
    purpose: str
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
    signal: str
    hint: str
    risk: str
    need: str
    consequence: str
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
class Aid:
    id: str
    label: str
    phrase: str
    helps: set[str]
    kindness: int
    action: str
    result: str
    qa_text: str
    ending_gift: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_visible_trouble(world: World) -> list[str]:
    squadron = world.get("squadron")
    if squadron.meters["incoming"] < THRESHOLD or squadron.meters["trouble"] < THRESHOLD:
        return []
    sig = ("visible_trouble", squadron.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    station = world.get("station")
    station.meters["danger"] += 1
    for child in world.characters():
        if child.role in {"watcher", "helper"}:
            child.memes["worry"] += 1
    return ["__trouble__"]


def _r_conflict(world: World) -> list[str]:
    watcher = world.get("watcher")
    helper = world.get("helper")
    if watcher.memes["suspect"] < THRESHOLD or helper.memes["kindness"] < THRESHOLD:
        return []
    sig = ("conflict", watcher.id, helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    watcher.memes["conflict"] += 1
    helper.memes["conflict"] += 1
    return ["__conflict__"]


def _r_rescue(world: World) -> list[str]:
    squadron = world.get("squadron")
    if squadron.meters["helped"] < THRESHOLD:
        return []
    sig = ("rescue", squadron.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    squadron.meters["trouble"] = 0.0
    squadron.meters["safe"] += 1
    station = world.get("station")
    station.meters["danger"] = 0.0
    for child in world.characters():
        if child.role in {"watcher", "helper"}:
            child.memes["relief"] += 1
    return ["__safe__"]


CAUSAL_RULES = [
    Rule(name="visible_trouble", tag="physical", apply=_r_visible_trouble),
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="rescue", tag="physical", apply=_r_rescue),
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


def aid_fits(problem: Problem, aid: Aid) -> bool:
    return problem.id in aid.helps


def kind_aids() -> list[Aid]:
    return [a for a in AIDS.values() if a.kindness >= KINDNESS_MIN]


def predict_need(world: World, problem: Problem, aid: Aid) -> dict:
    sim = world.copy()
    sim.facts["problem"] = problem.id
    squadron = sim.get("squadron")
    squadron.meters["incoming"] = 1
    squadron.meters["trouble"] = 1
    if aid_fits(problem, aid):
        squadron.meters["helped"] += 1
    propagate(sim, narrate=False)
    return {
        "solved": squadron.meters["safe"] >= THRESHOLD,
        "danger": sim.get("station").meters["danger"],
    }


def introduce(world: World, watcher: Entity, helper: Entity, setting: Setting) -> None:
    for child in (watcher, helper):
        child.memes["wonder"] += 1
    world.say(
        f"On {setting.place}, {watcher.id} and {helper.id} pressed their hands to "
        f"{setting.window} and watched {setting.sky}."
    )
    world.say(
        f"They had turned the {setting.floor} into a pretend launch deck with chalk stars, "
        f"bottle-cap planets, and a cardboard rover."
    )


def spot_squadron(world: World, watcher: Entity, visitor: Visitor) -> None:
    squadron = world.get("squadron")
    squadron.meters["incoming"] = 1
    watcher.memes["suspect"] += 1
    world.say(
        f"Then {watcher.id} saw {visitor.squadron}: {visitor.look}, {visitor.motion}. "
        f'"That looks suspicious," {watcher.pronoun()} whispered.'
    )


def worry_and_predict(world: World, helper: Entity, watcher: Entity, visitor: Visitor, problem: Problem, aid: Aid) -> None:
    squadron = world.get("squadron")
    squadron.meters["trouble"] = 1
    propagate(world, narrate=False)
    pred = predict_need(world, problem, aid)
    world.facts["predicted_danger"] = pred["danger"]
    helper.memes["kindness"] += 1
    world.say(
        f"{helper.id} squinted at the blinking lights. {problem.signal} "
        f'"Maybe they are not sneaking," {helper.pronoun()} said. "Maybe {visitor.purpose} and {problem.need}."'
    )
    if pred["solved"]:
        world.say(
            f'''{helper.id} pointed to the pattern again. \"If we help the right way, they can be safe before anything bumps the station.\"'''
        )


def argue(world: World, watcher: Entity, helper: Entity) -> None:
    propagate(world, narrate=False)
    world.say(
        f'''"But what if they are bad ships?" {watcher.id} asked. {watcher.pronoun().capitalize()} "'''
        f"took one step back from the glass."
    )
    world.say(
        f'"We should check before we shove them away," {helper.id} answered. '
        f"That made a small, hot argument spark between them."
    )


def choose_kindness(world: World, helper: Entity, watcher: Entity, aid: Aid) -> None:
    world.say(
        f"Instead of reaching for the alarm handle, {helper.id} reached for {aid.phrase}. "
        f"{watcher.id} watched, still unsure but no longer running to stop {helper.pronoun('object')}."
    )


def help_squadron(world: World, helper: Entity, visitor: Visitor, aid: Aid) -> None:
    squadron = world.get("squadron")
    squadron.meters["helped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} {aid.action}. Soon the little ships answered with brighter lights and steadier wings."
    )
    world.say(
        f"They were a {visitor.squadron}, but not an angry one. They were simply trying very hard to stay together."
    )


def reconcile(world: World, watcher: Entity, helper: Entity, visitor: Visitor, problem: Problem, aid: Aid) -> None:
    watcher.memes["kindness"] += 1
    watcher.memes["conflict"] = 0.0
    helper.memes["conflict"] = 0.0
    watcher.memes["trust"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"{watcher.id} let out a long breath. \"I thought the blinking made them look suspicious,\" "
        f'''{watcher.pronoun()} admitted. \"Really they were showing {problem.hint}.\"'''
    )
    world.say(
        f"{helper.id} smiled and bumped shoulders with {watcher.pronoun('object')}. "
        f"\"Sometimes the bravest space move is the kind one,\" {helper.pronoun()} said."
    )
    world.say(
        f"Together they watched as the squadron {aid.result}, and the dark outside did not feel so sharp anymore."
    )


def ending(world: World, watcher: Entity, helper: Entity, setting: Setting, aid: Aid) -> None:
    for child in (watcher, helper):
        child.memes["joy"] += 1
    world.say(
        f"Before drifting on, the visitors flashed a thank-you pattern across the window and left {aid.ending_gift} by the dock."
    )
    world.say(
        f"After that, whenever a strange light crossed {setting.place}, {watcher.id} and {helper.id} looked twice before calling it bad. "
        f"{setting.ending}"
    )
@dataclass
class StoryParams:
    setting: str
    visitor: str
    problem: str
    aid: str
    watcher_name: str
    watcher_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for visitor_id in VISITORS:
            for problem_id, problem in PROBLEMS.items():
                for aid_id, aid in AIDS.items():
                    if aid.kindness >= KINDNESS_MIN and aid_fits(problem, aid):
                        combos.append((setting_id, visitor_id, problem_id, aid_id))
    return combos


KNOWLEDGE = {
    "beacon": [(
        "What does a docking beacon do?",
        "A docking beacon is a bright guide light for ships. It helps pilots line up with a safe place to land."
    )],
    "map": [(
        "What is a star map?",
        "A star map shows where stars, stations, or routes are in space. Pilots use it so they do not get lost."
    )],
    "repair": [(
        "What is a repair patch?",
        "A repair patch is a small fix for a broken part. It covers a tear or crack so something can work safely again."
    )],
    "power": [(
        "Why do ships need power?",
        "Ships need power to run their lights and steering. Without enough power, they can drift the wrong way."
    )],
    "navigation": [(
        "Why can getting lost in space be dangerous?",
        "Space is very big, and safe routes matter. If a ship does not know where to go, it can waste power or hit something."
    )],
    "sail": [(
        "What is a solar sail?",
        "A solar sail is a thin shining sheet that catches light and helps a small ship move. If it tears, the ship can wobble or spin."
    )],
    "kindness": [(
        "What does kindness mean?",
        "Kindness means choosing to help instead of hurt. Sometimes kindness starts with stopping to understand what someone needs."
    )],
    "alarm": [(
        "What is an alarm for?",
        "An alarm warns people about danger. It is helpful when there is real danger, but it is not a kind first choice when someone just needs help."
    )],
}
KNOWLEDGE_ORDER = ["kindness", "power", "navigation", "sail", "beacon", "map", "repair", "alarm"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    watcher = f["watcher"]
    helper = f["helper"]
    visitor = f["visitor"]
    problem = f["problem_cfg"]
    aid = f["aid_cfg"]
    setting = f["setting"]
    return [
        f'Write a short Space Adventure story for a 3-to-5-year-old that includes the words "suspicious" and "squadron".',
        f"Tell a gentle conflict story on {setting.place} where {watcher.label} thinks {visitor.squadron} looks suspicious, but {helper.label} notices {problem.hint} and helps with {aid.label}.",
        "Write a child-friendly story where a scary first guess turns into kindness after the children understand what the visitors really need.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    watcher = f["watcher"]
    helper = f["helper"]
    visitor = f["visitor"]
    problem = f["problem_cfg"]
    aid = f["aid_cfg"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {watcher.label} and {helper.label} on {setting.place}. They saw {visitor.squadron} outside the window."
        ),
        (
            f"Why did {watcher.label} think the visitors looked suspicious?",
            f"{watcher.label} saw the flickering lights and shaky flying and first thought the ships might be bad. The dark outside made the strange pattern feel scarier than it really was."
        ),
        (
            f"What clue helped {helper.label} understand the truth?",
            f"{helper.label} noticed {problem.signal.lower()} That was a sign of {problem.hint}, not a sneaky attack."
        ),
        (
            "How did the children solve the problem?",
            f"They used {aid.label}. {aid.qa_text.capitalize()}, and that matched what the squadron needed."
        ),
        (
            "What happened after they helped?",
            f"The little ships became safe and steady instead of wobbling in danger. The children also stopped arguing, because kindness showed them what was really happening."
        ),
        (
            "What did the story teach them?",
            f"It taught them to look twice before calling someone bad. A suspicious sight can hide a real problem, and kindness can uncover the truth."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"kindness"} | set(f["problem_cfg"].tags) | set(f["aid_cfg"].tags)
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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="moonbase",
        visitor="glider_squadron",
        problem="low_power",
        aid="beacon",
        watcher_name="Nova",
        watcher_gender="girl",
        helper_name="Orin",
        helper_gender="boy",
        parent="mother",
    ),
    StoryParams(
        setting="ringport",
        visitor="seed_squadron",
        problem="lost_route",
        aid="star_map",
        watcher_name="Mira",
        watcher_gender="girl",
        helper_name="Kai",
        helper_gender="boy",
        parent="father",
    ),
    StoryParams(
        setting="canyon_colony",
        visitor="moth_squadron",
        problem="torn_sail",
        aid="repair_patch",
        watcher_name="Luna",
        watcher_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        parent="mother",
    ),
]


def explain_rejection(problem: Problem, aid: Aid) -> str:
    if aid.kindness < KINDNESS_MIN:
        return (
            f"(No story: '{aid.id}' is known to the world, but it is too unkind or panicky "
            f"for this domain. A kindness story should prefer calmer help.)"
        )
    return (
        f"(No story: {aid.label} does not solve {problem.id.replace('_', ' ')}. "
        f"The help in this world must match the squadron's actual need.)"
    )


ASP_RULES = r"""
kind_aid(A) :- aid(A), kindness(A,K), kindness_min(M), K >= M.
fits(P,A)   :- problem(P), aid(A), helps(A,P).
valid(S,V,P,A) :- setting(S), visitor(V), problem(P), aid(A), kind_aid(A), fits(P,A).

outcome(helped) :- chosen_problem(P), chosen_aid(A), kind_aid(A), fits(P,A).
:- chosen_problem(P), chosen_aid(A), not fits(P,A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for vid in VISITORS:
        lines.append(asp.fact("visitor", vid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("kindness", aid_id, aid.kindness))
        for help_id in sorted(aid.helps):
            lines.append(asp.fact("helps", aid_id, help_id))
    lines.append(asp.fact("kindness_min", KINDNESS_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_kind_aids() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show kind_aid/1."))
    return sorted(a for (a,) in asp.atoms(model, "kind_aid"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_aid", params.aid),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_kind = {a.id for a in kind_aids()}
    asp_kind = set(asp_kind_aids())
    if py_kind == asp_kind:
        print(f"OK: kind aids match ({sorted(py_kind)}).")
    else:
        rc = 1
        print(f"MISMATCH in kind aids: clingo={sorted(asp_kind)} python={sorted(py_kind)}")

    for params in CURATED:
        out = asp_outcome(params)
        if out != "helped":
            rc = 1
            print(f"MISMATCH: curated outcome for {params.problem}/{params.aid} was {out!r}, expected 'helped'.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a suspicious squadron, a conflict, and a kind space fix."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--watcher-name")
    ap.add_argument("--watcher-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.aid:
        problem = PROBLEMS[args.problem]
        aid = AIDS[args.aid]
        if not (aid.kindness >= KINDNESS_MIN and aid_fits(problem, aid)):
            raise StoryError(explain_rejection(problem, aid))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.visitor is None or c[1] == args.visitor)
        and (args.problem is None or c[2] == args.problem)
        and (args.aid is None or c[3] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, visitor_id, problem_id, aid_id = rng.choice(sorted(combos))
    watcher_gender = args.watcher_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    watcher_name = args.watcher_name or _pick_name(rng, watcher_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=watcher_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        visitor=visitor_id,
        problem=problem_id,
        aid=aid_id,
        watcher_name=watcher_name,
        watcher_gender=watcher_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        visitor = VISITORS[params.visitor]
        problem = PROBLEMS[params.problem]
        aid = AIDS[params.aid]
    except KeyError as exc:
        raise StoryError(f"(Unknown option: {exc.args[0]})") from None

    if not (aid.kindness >= KINDNESS_MIN and aid_fits(problem, aid)):
        raise StoryError(explain_rejection(problem, aid))

    world = tell(
        setting=setting,
        visitor=visitor,
        problem=problem,
        aid=aid,
        watcher_name=params.watcher_name,
        watcher_gender=params.watcher_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
    )

    return StorySample(
        params=params,
        story=world.render().replace("watcher", params.watcher_name).replace("helper", params.helper_name),
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
        print(asp_program("", "#show valid/4.\n#show kind_aid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"kind aids: {', '.join(asp_kind_aids())}\n")
        print(f"{len(combos)} valid (setting, visitor, problem, aid) combos:\n")
        for setting_id, visitor_id, problem_id, aid_id in combos:
            print(f"  {setting_id:14} {visitor_id:16} {problem_id:12} {aid_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.watcher_name} & {p.helper_name}: {p.visitor} / {p.problem} / {p.aid}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    setting: Setting,
    visitor: Visitor,
    problem: Problem,
    aid: Aid,
    watcher_name: str = "Nova",
    watcher_gender: str = "girl",
    helper_name: str = "Orin",
    helper_gender: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World(setting)
    watcher = world.add(Entity(id="watcher", kind="character", type=watcher_gender, label=watcher_name, role="watcher"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="adult"))
    station = world.add(Entity(id="station", type="station", label=setting.place))
    squadron = world.add(Entity(id="squadron", type="visitors", label=visitor.label))
    for ent in (watcher, helper, parent, station, squadron):
        ent.attrs = dict(ent.attrs)
        ent.meters["init"] += 0.0
        ent.memes["init"] += 0.0

    world.facts.update(
        setting=setting,
        visitor=visitor,
        problem_cfg=problem,
        aid_cfg=aid,
        watcher=watcher,
        helper=helper,
        parent=parent,
    )

    introduce(world, watcher, helper, setting)

    world.para()
    spot_squadron(world, watcher, visitor)
    worry_and_predict(world, helper, watcher, visitor, problem, aid)
    argue(world, watcher, helper)

    world.para()
    choose_kindness(world, helper, watcher, aid)
    help_squadron(world, helper, visitor, aid)
    reconcile(world, watcher, helper, visitor, problem, aid)

    world.para()
    ending(world, watcher, helper, setting, aid)

    world.facts.update(
        solved=squadron.meters["safe"] >= THRESHOLD,
        conflict_happened=watcher.memes["suspect"] >= THRESHOLD and helper.memes["kindness"] >= THRESHOLD,
        suspicious_first=watcher.memes["suspect"] >= THRESHOLD,
        kindness_used=aid.kindness >= KINDNESS_MIN,
        squadron=squadron,
        station=station,
        outcome="helped" if squadron.meters["safe"] >= THRESHOLD else "drifting",
        problem=problem,
        aid=aid,
        watcher_name=watcher_name,
        helper_name=helper_name,
    )
    return world


SETTINGS = {
    "moonbase": Setting(
        id="moonbase",
        place="the moonbase called Silver Lantern",
        sky="the black sky stitched with hard bright stars",
        window="the round observatory window",
        floor="quiet metal floor",
        ending="The moonbase lights blinked softly behind them like a friendly little constellation.",
        tags={"space", "moonbase"},
    ),
    "ringport": Setting(
        id="ringport",
        place="the ring station called Blue Orbit",
        sky="the curling blue edge of a faraway planet and the dark beyond it",
        window="the tall docking glass",
        floor="spinning station floor",
        ending="Below them, the planet rolled like a marble, and the whole station felt gentle again.",
        tags={"space", "station"},
    ),
    "canyon_colony": Setting(
        id="canyon_colony",
        place="the cliff colony above Mars's red canyon",
        sky="the dusty dusk and the first brave stars",
        window="the lookout dome",
        floor="warm stone floor",
        ending="Outside, the red canyon slept under starlight, and the dock lamps looked like tiny campfires that never burned anyone.",
        tags={"space", "mars"},
    ),
}

VISITORS = {
    "glider_squadron": Visitor(
        id="glider_squadron",
        label="glider squadron",
        phrase="a squadron of little silver gliders",
        squadron="a squadron of little silver gliders",
        look="their wing lights flickering unevenly",
        motion="tilting and wobbling in the dark",
        purpose="the travelers are trying to reach the dock",
        tags={"ships", "squadron"},
    ),
    "seed_squadron": Visitor(
        id="seed_squadron",
        label="seed squadron",
        phrase="a squadron of round seed-ships",
        squadron="a squadron of round seed-ships",
        look="their lantern bellies blinking like sleepy fireflies",
        motion="drifting in a tight loop above the antennae",
        purpose="the gardeners from orbit are trying to find the greenhouse bay",
        tags={"ships", "garden", "squadron"},
    ),
    "moth_squadron": Visitor(
        id="moth_squadron",
        label="moth squadron",
        phrase="a squadron of tiny moth-wing scouts",
        squadron="a squadron of tiny moth-wing scouts",
        look="their pale wings flashing and folding",
        motion="circling the station in a shaky ring",
        purpose="the scouts are trying to stay out of the debris stream",
        tags={"ships", "scouts", "squadron"},
    ),
}

PROBLEMS = {
    "low_power": Problem(
        id="low_power",
        signal="Their nose lights kept dimming and brightening, almost like tired eyes.",
        hint="a weak power call",
        risk="they may drift into the station wall",
        need="they need a bright docking beacon",
        consequence="without a bright path, they cannot line up safely",
        tags={"power", "beacon"},
    ),
    "lost_route": Problem(
        id="lost_route",
        signal="The ships flashed the same question-pattern again and again.",
        hint="a request for directions",
        risk="they may wander into the rock field",
        need="they need a clean star map ping",
        consequence="without directions, they will circle until something harder finds them first",
        tags={"map", "navigation"},
    ),
    "torn_sail": Problem(
        id="torn_sail",
        signal="One ship trailed a bright ribbon that fluttered the wrong way.",
        hint="a torn solar sail",
        risk="they may spin apart from one another",
        need="they need a repair patch and a careful guide-in",
        consequence="without a patch, the squadron cannot hold a steady line",
        tags={"repair", "sail"},
    ),
}

AIDS = {
    "beacon": Aid(
        id="beacon",
        label="beacon lamp",
        phrase="the beacon lamp switch",
        helps={"low_power"},
        kindness=3,
        action="clicked on the old beacon so a warm gold path spread from the dock into space",
        result="slipped one by one into a neat shining line beside the station",
        qa_text="turned on the docking beacon so the ships could see a safe path",
        ending_gift="a tiny moon-pearl sticker",
        tags={"beacon", "kindness"},
    ),
    "star_map": Aid(
        id="star_map",
        label="star map sender",
        phrase="the star map sender",
        helps={"lost_route"},
        kindness=3,
        action="sent a soft blue map-ping that sketched the safe route right into the dark",
        result="tipped their noses together and glided toward the proper bay",
        qa_text="sent a star map ping to show the visitors where to go",
        ending_gift="a folded paper-thin map of the nearby stars",
        tags={"map", "kindness"},
    ),
    "repair_patch": Aid(
        id="repair_patch",
        label="repair patch kit",
        phrase="the little repair patch kit",
        helps={"torn_sail"},
        kindness=3,
        action="launched the patch drone, and it pressed a silver square onto the torn sail",
        result="steadied themselves and flew as one bright ribbon again",
        qa_text="used a repair patch so the torn ship could hold steady again",
        ending_gift="a shiny spare sail clip",
        tags={"repair", "kindness"},
    ),
    "alarm_horn": Aid(
        id="alarm_horn",
        label="alarm horn",
        phrase="the red alarm horn",
        helps=set(),
        kindness=1,
        action="blared the alarm into the dock tunnel",
        result="jerked away in panic and scattered",
        qa_text="blew the alarm horn",
        ending_gift="nothing at all",
        tags={"alarm"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Zuri", "Ada", "Tess", "Rhea", "Ivy"]
BOY_NAMES = ["Orin", "Leo", "Finn", "Kai", "Milo", "Jude", "Niko", "Ezra"]

if __name__ == "__main__":
    main()
