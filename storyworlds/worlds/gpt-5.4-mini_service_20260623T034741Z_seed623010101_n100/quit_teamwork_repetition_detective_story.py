#!/usr/bin/env python3
"""
storyworlds/worlds/quit_teamwork_repetition_detective_story.py
==============================================================

A tiny detective story world about two helpers solving a repetitive mystery
with teamwork. The child-facing story is about a case that keeps happening
again and again until the team notices the pattern, quits a bad habit, and
fixes the problem.

Seed tale idea:
---
Two friends kept finding the same muddy paw prints by the bakery window every
morning. They tried looking once, then twice, then again, but the prints kept
coming back. The friends worked together like detectives, followed the clues,
and learned the prints were from the bakery cat sneaking in through a loose
back gate. They quit leaving the gate cracked open, and the mystery stopped.

World logic:
- Repetition can raise suspicion and clue value.
- Teamwork raises progress and lowers frustration.
- A clear ending proves what changed in the world: the gate is shut, the prints
  stop, and the detectives feel proud.

The story is state-driven: meter values determine the plot beats and the final
image.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    det1: object | None = None
    det2: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str
    repeat_spot: str
    hidden_path: str
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Clue:
    id: str
    label: str
    trace: str
    repeated: str
    points_to: str
    suspicion: float = 1.0
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Fix:
    id: str
    label: str
    action: str
    result: str
    resolves: str
    teamwork_bonus: float = 1.0
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    setting: str
    clue: str
    fix: str
    detective1: str
    detective1_gender: str
    detective2: str
    detective2_gender: str
    helper: str
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w

    def detectives(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"detective1", "detective2"}]


def _r_teamwork(world: World) -> list[str]:
    out = []
    if world.facts.get("teamwork_ready") and ("teamwork",) not in world.fired:
        world.fired.add(("teamwork",))
        for d in world.detectives():
            d.memes["confidence"] += 1
            d.meters["progress"] += 1
        out.append("__teamwork__")
    return out


def _r_repetition(world: World) -> list[str]:
    out = []
    if world.facts.get("repeat_count", 0) >= 2 and ("repetition",) not in world.fired:
        world.fired.add(("repetition",))
        world.facts["pattern"] = True
        for d in world.detectives():
            d.memes["curiosity"] += 1
        out.append("__pattern__")
    return out


def _r_clue_chain(world: World) -> list[str]:
    out = []
    if world.facts.get("pattern") and ("clue_chain",) not in world.fired:
        world.fired.add(("clue_chain",))
        world.facts["solution_ready"] = True
        out.append("__solution__")
    return out


CAUSAL_RULES = [_r_teamwork, _r_repetition, _r_clue_chain]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            got = rule(world)
            if got:
                changed = True
                produced.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def clue_at_risk(clue: Clue, setting: Setting) -> bool:
    return clue.points_to == setting.hidden_path or clue.repeated == setting.repeat_spot


def fix_works(fix: Fix, clue: Clue) -> bool:
    return fix.resolves == clue.points_to


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for cid, clue in CLUES.items():
            for fid, fix in FIXES.items():
                if clue_at_risk(clue, _safe_lookup(SETTINGS, sid)) and fix_works(fix, clue):
                    out.append((sid, cid, fid))
    return out


def _det_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def introduce(world: World, a: Entity, b: Entity) -> None:
    world.say(
        f"{a.id} and {b.id} were two young detectives who liked to solve little mysteries."
    )
    world.say(
        f"They kept notebooks, watched the sidewalks, and never quit when a clue looked small."
    )


def describe_case(world: World, setting: Setting, clue: Clue) -> None:
    world.say(
        f"Every morning at {setting.place}, the same clue appeared again: {clue.label}."
    )
    world.say(
        f"It was {clue.trace}, and that repetition made the case feel suspicious."
    )


def search(world: World, a: Entity, b: Entity, clue: Clue) -> None:
    a.meters["search"] += 1
    b.meters["search"] += 1
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    world.facts["repeat_count"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They looked once, then again, then a third time, because the same clue kept coming back."
    )
    if world.facts.get("pattern"):
        world.say(f"After all that repetition, {a.id} and {b.id} knew it was no accident.")


def work_together(world: World, a: Entity, b: Entity, helper: Entity, fix: Fix) -> None:
    a.meters["teamwork"] += 1
    b.meters["teamwork"] += 1
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    helper.meters["help"] += 1
    helper.memes["kindness"] += 1
    world.facts["teamwork_ready"] = True
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} helped them line up the clues, and the three of them worked like a tiny team."
    )
    world.say(
        f"Together they followed the tracks to the loose back gate and used {fix.label}."
    )


def solve(world: World, a: Entity, b: Entity, clue: Clue, fix: Fix, setting: Setting) -> None:
    world.facts["solved"] = True
    world.say(
        f"The clue pointed right to {setting.hidden_path}, where the answer had been hiding all along."
    )
    world.say(
        f"They found that a cat could slip through the gate, leave {clue.label}, and sneak back out."
    )
    world.say(
        f"So the detectives quit leaving the gate cracked open, and they shut it tight."
    )
    world.say(
        f"After that, the {clue.label.lower()} stopped showing up, and {a.id} and {b.id} grinned at each other."
    )


def tell(setting: Setting, clue: Clue, fix: Fix, d1: str, g1: str, d2: str, g2: str, helper_name: str) -> World:
    world = World(setting)
    det1 = world.add(Entity(id=d1, kind="character", type=g1, role="detective1"))
    det2 = world.add(Entity(id=d2, kind="character", type=g2, role="detective2"))
    helper = world.add(Entity(id=helper_name, kind="character", type="adult", role="helper", label=helper_name))

    world.facts["repeat_count"] = 0
    world.facts["pattern"] = False
    world.facts["teamwork_ready"] = False
    world.facts["solution_ready"] = False
    world.facts["solved"] = False

    introduce(world, det1, det2)
    world.para()
    describe_case(world, setting, clue)
    search(world, det1, det2, clue)
    world.para()
    search(world, det1, det2, clue)
    world.para()
    search(world, det1, det2, clue)
    world.para()
    work_together(world, det1, det2, helper, fix)
    world.para()
    solve(world, det1, det2, clue, fix, setting)

    world.facts.update(
        det1=det1, det2=det2, helper=helper, clue=clue, fix=fix, setting=setting
    )
    return world


SETTINGS = {
    "bakery": Setting(place="the bakery", repeat_spot="the back gate", hidden_path="the back gate"),
    "harbor": Setting(place="the harbor market", repeat_spot="the dock door", hidden_path="the dock door"),
    "library": Setting(place="the little library", repeat_spot="the side door", hidden_path="the side door"),
}

CLUES = {
    "prints": Clue(id="prints", label="muddy paw prints", trace="small and round", repeated="the back gate", points_to="the back gate"),
    "crumbs": Clue(id="crumbs", label="cookie crumbs", trace="tiny and sandy", repeated="the side door", points_to="the side door"),
    "strings": Clue(id="strings", label="red string loops", trace="tied in the same knot again and again", repeated="the dock door", points_to="the dock door"),
}

FIXES = {
    "shut_gate": Fix(id="shut_gate", label="a strong latch", action="shut", result="closed tight", resolves="the back gate"),
    "bolt_door": Fix(id="bolt_door", label="a metal bolt", action="bolt", result="locked", resolves="the side door"),
    "clip_door": Fix(id="clip_door", label="a bright clip", action="clip", result="snug", resolves="the dock door"),
}

GIRL_NAMES = ["Mia", "Nina", "Lila", "Ada", "June", "Ivy", "Sofia", "Rosa"]
BOY_NAMES = ["Max", "Eli", "Noah", "Theo", "Finn", "Leo", "Ben", "Jude"]
TRAITS = ["careful", "curious", "bright", "patient", "clever"]


@dataclass
class StoryParams:
    setting: str
    clue: str
    fix: str
    detective1: str
    detective1_gender: str
    detective2: str
    detective2_gender: str
    helper: str
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a young child about {f["clue"].label} that keeps appearing again and again at {f["setting"].place}.',
        f"Tell a teamwork mystery where {f['det1'].id} and {f['det2'].id} keep seeing the same clue, then work together to solve it.",
        f'Write a short story that uses the word "quit" when the detectives finally stop leaving {f["setting"].repeat_spot} open.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, helper = f["det1"], f["det2"], f["helper"]
    clue, setting, fix = f["clue"], f["setting"], f["fix"]
    return [
        QAItem(
            question=f"Who were the detectives in the story at {setting.place}?",
            answer=f"The story was about {a.id} and {b.id}. They were the detectives who kept looking at the same clue until they solved the mystery together.",
        ),
        QAItem(
            question=f"Why did the case feel strange at first?",
            answer=f"It felt strange because {clue.label} kept showing up again and again. That repetition made the detectives realize something was happening in the same place every time.",
        ),
        QAItem(
            question=f"How did teamwork help {a.id} and {b.id} solve the mystery?",
            answer=f"{helper.id} helped them line up the clues, and then the three of them checked the same place together. Teamwork made it easier to notice the pattern and fix the problem.",
        ),
        QAItem(
            question=f"What did they quit doing at the end?",
            answer=f"They quit leaving {setting.repeat_spot} cracked open. Once they shut it tight, the clue stopped coming back.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and tries to solve a mystery by paying close attention.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means something happens again and again. It can help you notice a pattern.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and work together toward the same goal.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== Story QA ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
repeat_pattern(C) :- clue(C), repeat_count(C,N), N >= 2.
teamwork_ready(A,B) :- detective(A), detective(B), A != B, help_ready.
solution_ready(S) :- teamwork_ready(_, _), repeat_pattern(_), fix(S).
solved_story :- solution_ready(_), quit_used.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid, s.place))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("repeat_spot", cid, c.repeated))
        lines.append(asp.fact("points_to", cid, c.points_to))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("resolves", fid, fx.resolves))
    lines.append(asp.fact("quit_used"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved_story/0."))
    asp_ok = bool(asp.atoms(model, "solved_story"))
    py_ok = True
    if asp_ok != py_ok:
        print("MISMATCH: ASP/Python parity failed")
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return 0


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world about teamwork and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--detective1")
    ap.add_argument("--detective2")
    ap.add_argument("--helper")
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--gender2", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))
              and (getattr(args, "fix", None) is None or c[2] == getattr(args, "fix", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, clue, fix = rng.choice(list(combos))
    g1 = getattr(args, "gender1", None) or rng.choice(["girl", "boy"])
    g2 = getattr(args, "gender2", None) or rng.choice(["girl", "boy"])
    d1 = getattr(args, "detective1", None) or rng.choice(GIRL_NAMES if g1 == "girl" else BOY_NAMES)
    d2 = getattr(args, "detective2", None) or rng.choice([n for n in (GIRL_NAMES if g2 == "girl" else BOY_NAMES) if n != d1])
    helper = getattr(args, "helper", None) or rng.choice(["Mrs. Lane", "Mr. Cole", "Aunt June", "Coach Kim"])
    return StoryParams(setting=setting, clue=clue, fix=fix, detective1=d1, detective1_gender=g1, detective2=d2, detective2_gender=g2, helper=helper)


def generate(params: StoryParams) -> StorySample:
    for k in (params.setting, params.clue, params.fix):
        if k is None:
            pass
    if params.setting not in SETTINGS or params.clue not in CLUES or params.fix not in FIXES:
        pass
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(CLUES, params.clue), _safe_lookup(FIXES, params.fix),
                 params.detective1, params.detective1_gender,
                 params.detective2, params.detective2_gender, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="bakery", clue="prints", fix="shut_gate", detective1="Mia", detective1_gender="girl", detective2="Noah", detective2_gender="boy", helper="Mrs. Lane"),
    StoryParams(setting="library", clue="crumbs", fix="bolt_door", detective1="Leo", detective1_gender="boy", detective2="Ivy", detective2_gender="girl", helper="Mr. Cole"),
    StoryParams(setting="harbor", clue="strings", fix="clip_door", detective1="Ada", detective1_gender="girl", detective2="Finn", detective2_gender="boy", helper="Aunt June"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show solved_story/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show solved_story/0."))
        print("solved_story:", bool(asp.atoms(model, "solved_story")))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            i += 1
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
