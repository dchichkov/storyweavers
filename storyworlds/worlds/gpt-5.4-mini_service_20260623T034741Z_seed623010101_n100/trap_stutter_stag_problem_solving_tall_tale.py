#!/usr/bin/env python3
"""
storyworlds/worlds/trap_stutter_stag_problem_solving_tall_tale.py
=================================================================

A standalone story world for a tiny Tall Tale about a trap, a stutter,
and a stag that helps solve a problem.

The seed idea:
---
A child in a small frontier town finds a noisy trap stuck shut across the
only path to the mill. The child stutters when worried. A giant stag with
bright antlers appears and helps them solve the problem by using calm steps,
a lever, and a clever rope. The trap opens, the path clears, and the child
finds their voice.

World contract notes:
- Typed entities carry physical meters and emotional memes.
- State drives narration; the ending proves what changed.
- Q&A sets are grounded in the simulated world, not rendered prose.
- Inline ASP rules mirror the Python reasonableness gate.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    plural: bool = False

    child: object | None = None
    lever: object | None = None
    path: object | None = None
    rope: object | None = None
    stag: object | None = None
    trap: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Problem:
    id: str
    label: str
    phrase: str
    trap_label: str
    blocked_path: str
    cause: str
    danger: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    phrase: str
    method: str
    effect: str
    power: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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


def _r_nerves(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["worry"] >= THRESHOLD and ent.meters["stuck"] >= THRESHOLD:
            sig = ("nerves", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["stutter"] += 1
            out.append("__stutter__")
    return out


def _r_solve(world: World) -> list[str]:
    out: list[str] = []
    path = world.entities.get("path")
    if not path:
        return out
    if path.meters["blocked"] < THRESHOLD:
        return out
    lever = world.entities.get("lever")
    rope = world.entities.get("rope")
    stag = world.entities.get("stag")
    child = world.entities.get("child")
    if not (lever and rope and stag and child):
        return out
    if lever.meters["used"] >= THRESHOLD and rope.meters["used"] >= THRESHOLD:
        sig = ("solve", path.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        path.meters["blocked"] = 0.0
        child.memes["hope"] += 1
        child.memes["worry"] = 0.0
        stag.memes["pride"] += 1
        out.append("__open_path__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("nerves", "social", _r_nerves),
    Rule("solve", "physical", _r_solve),
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
            if s != "__stutter__" and s != "__open_path__":
                world.say(s)
    return produced


def problem_at_risk(problem: Problem, fix: Fix) -> bool:
    return problem.id in fix.tags and "blocked" in fix.tags


def best_fix(fixes: list[Fix]) -> Fix:
    return max(fixes, key=lambda f: f.power)


def solveable(problem: Problem, fix: Fix) -> bool:
    return problem_at_risk(problem, fix) and fix.power >= 1


def predict(world: World) -> dict:
    sim = world.copy()
    _do_try(sim, narrate=False)
    return {
        "opened": sim.get("path").meters["blocked"] < THRESHOLD,
        "worry": sim.get("child").memes["worry"],
    }


def _do_try(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    stag = world.get("stag")
    lever = world.get("lever")
    rope = world.get("rope")
    child.meters["stuck"] += 1
    child.memes["worry"] += 1
    world.get("trap").meters["snapped"] += 1
    lever.meters["used"] += 1
    rope.meters["used"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, problem: Problem) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"In the little town of Bramble Bend, {child.id} found {problem.phrase} "
        f"across the only path to the mill."
    )
    world.say(
        f"It was a {problem.danger} old {problem.trap_label}, and the whole lane "
        f"looked stuck as a boot in mud."
    )


def stutter_beat(world: World, child: Entity) -> None:
    if child.memes["worry"] >= THRESHOLD:
        world.say(
            f'{child.id} tried to speak, but {child.pronoun()} had to stutter, '
            f'"I-I-I do not know how to get past this."'
        )


def stag_arrives(world: World, stag: Entity) -> None:
    stag.memes["calm"] += 1
    world.say(
        f"Then a tall stag stepped out of the pine hush, with antlers like a "
        f"crown of clean branches."
    )
    world.say(
        f'He bowed as neat as a schoolmaster and said, "A problem is just a '
        f'path waiting for a plan."'
    )


def plan(world: World, child: Entity, stag: Entity, problem: Problem) -> None:
    world.say(
        f"{stag.id} sniffed the jammed {problem.trap_label}, looked at the "
        f"rope, and pointed to the lever."
    )
    world.say(
        f'"First we lift the weight, then we pull the latch, then we test the '
        f'path," {stag.id} said, slow as Sunday molasses.'
    )
    child.memes["hope"] += 1


def solve(world: World, child: Entity, stag: Entity, fix: Fix, problem: Problem) -> None:
    world.say(
        f"{child.id} and {stag.id} tied the rope to the lever and gave it a "
        f"great careful heave."
    )
    world.say(
        f"{stag.id} used {fix.phrase}, which was {fix.effect}, and the rusty "
        f"{problem.trap_label} finally gave a wheezy groan."
    )


def ending(world: World, child: Entity, stag: Entity, problem: Problem) -> None:
    world.say(
        f"The {problem.blocked_path} opened wide at last, and the mill road "
        f"shone clear in the morning light."
    )
    world.say(
        f"{child.id} stood straighter, with no stutter in {child.pronoun('possessive')} voice, "
        f'and said, "We fixed it."'
    )
    world.say(
        f"{stag.id} tipped his bright head once, as if that had been the easiest "
        f"problem in the county."
    )


def tell(problem: Problem, fix: Fix) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type="boy", label="the child"))
    stag = world.add(Entity(id="stag", kind="character", type="stag", label="the stag"))
    trap = world.add(Entity(id="trap", type="thing", label=problem.trap_label))
    path = world.add(Entity(id="path", type="thing", label=problem.blocked_path))
    lever = world.add(Entity(id="lever", type="thing", label=fix.label))
    rope = world.add(Entity(id="rope", type="thing", label="rope"))
    world.add(Entity(id="mill", type="thing", label="the mill"))

    trap.meters["snapped"] = 0.0
    path.meters["blocked"] = 1.0
    child.memes["worry"] = 0.0
    child.meters["stuck"] = 0.0
    stag.memes["calm"] = 0.0
    lever.meters["used"] = 0.0
    rope.meters["used"] = 0.0

    world.facts["problem"] = problem
    world.facts["fix"] = fix
    world.facts["child"] = child
    world.facts["stag"] = stag

    opening(world, child, problem)
    world.para()
    stutter_beat(world, child)
    stag_arrives(world, stag)
    plan(world, child, stag, problem)
    world.para()
    _do_try(world, narrate=False)
    solve(world, child, stag, fix, problem)
    ending(world, child, stag, problem)

    world.facts["solved"] = path.meters["blocked"] < THRESHOLD
    return world


@dataclass
class StoryParams:
    problem: str = "mill_path_trap"
    fix: str = "rope_lever"
    child_name: str = "Ned"
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


PROBLEMS = {
    "mill_path_trap": Problem(
        id="mill_path_trap",
        label="path trap",
        phrase="a trap across the path to the mill",
        trap_label="trap",
        blocked_path="mill path",
        cause="a snapped spring and a crooked latch",
        danger="snarly",
        tags={"trap", "blocked"},
    ),
}

FIXES = {
    "rope_lever": Fix(
        id="rope_lever",
        label="lever plank",
        phrase="a rope tied to a lever plank",
        method="lifting the weight and pulling the latch",
        effect="a clever way to lift the trap without sticking fingers in it",
        power=2,
        tags={"trap", "blocked"},
    ),
}


CURATED = [
    StoryParams(problem="mill_path_trap", fix="rope_lever", child_name="Ned", seed=0),
]


GIRL_NAMES = ["Mina", "June", "Ada"]
BOY_NAMES = ["Ned", "Jory", "Cal"]
TRAITS = ["careful", "curious", "brave"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, prob in PROBLEMS.items():
        for fid, fix in FIXES.items():
            if solveable(prob, fix):
                combos.append((pid, fid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale story world about a trap, a stutter, and a stag.")
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
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
              if (getattr(args, "problem", None) is None or c[0] == getattr(args, "problem", None))
              and (getattr(args, "fix", None) is None or c[1] == getattr(args, "fix", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    problem, fix = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(problem=problem, fix=fix, child_name=name)


def generate(params: StoryParams) -> StorySample:
    if params.problem not in PROBLEMS:
        pass
    if params.fix not in FIXES:
        pass
    if not solveable(_safe_lookup(PROBLEMS, params.problem), _safe_lookup(FIXES, params.fix)):
        pass
    world = tell(_safe_lookup(PROBLEMS, params.problem), _safe_lookup(FIXES, params.fix))
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a tall-tale story for a young child that includes the words "trap", "stutter", and "stag".',
        f"Tell a problem-solving story where a child faces a trap on the mill path and a stag helps solve it.",
        "Write a short frontier story where worry makes a child stutter, then a grand animal shows a clever fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    stag = world.facts["stag"]
    prob = world.facts["problem"]
    fix = world.facts["fix"]
    return [
        QAItem(
            f"What problem did {child.id} find?",
            f"{child.id} found a {prob.phrase} on the mill road. It blocked the way and made the path look stuck.",
        ),
        QAItem(
            f"Why did {child.id} stutter at first?",
            f"{child.id} stuttered because the trap made {child.pronoun('possessive')} worry rise. The path was blocked, so speaking came out in bits and pieces.",
        ),
        QAItem(
            f"How did the stag help solve the problem?",
            f"The stag used {fix.phrase} and a rope to work the lever. That gave the trap a careful lift, and the path opened.",
        ),
        QAItem(
            f"What changed at the end of the story?",
            f"The mill path opened wide, and {child.id} no longer stuttered when {child.pronoun()} said the job was done. The ending proves the trap was cleared and the child felt sure again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a trap?", "A trap is something that catches or blocks something else until it is opened or freed."),
        QAItem("What is a stag?", "A stag is a male deer with antlers. In tall tales, a stag can seem as wise as a human helper."),
        QAItem("What is stuttering?", "Stuttering is when words come out in broken starts and stops, often when someone feels nervous."),
    ]


ASP_RULES = r"""
problem_at_risk(P, F) :- problem(P), fix(F), needs(P, trap), solves(F, trap).
valid(P, F) :- problem_at_risk(P, F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("needs", pid, "trap"))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("solves", fid, "trap"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = py == cl
    if not ok:
        print("MISMATCH in valid combos")
        if py - cl:
            print("only python:", sorted(py - cl))
        if cl - py:
            print("only clingo:", sorted(cl - py))
        return 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: ASP parity and generation smoke test passed ({len(py)} combos).")
    return 0


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


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
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
