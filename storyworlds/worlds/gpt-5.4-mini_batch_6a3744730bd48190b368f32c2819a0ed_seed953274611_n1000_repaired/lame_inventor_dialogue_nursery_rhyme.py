#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lame_inventor_dialogue_nursery_rhyme.py
========================================================================

A small standalone storyworld for a nursery-rhyme-style tale about a young
inventor with a lame leg who builds a clever helper, meets a problem, and ends
with a brighter, kinder solution.

The world is intentionally tiny:
- one child inventor
- one helper
- one handmade device
- one problem the device must solve
- dialogue, rhyme-like cadence, and state-driven resolution

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/lame_inventor_dialogue_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4-mini/lame_inventor_dialogue_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4-mini/lame_inventor_dialogue_nursery_rhyme.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/lame_inventor_dialogue_nursery_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/lame_inventor_dialogue_nursery_rhyme.py --verify
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
        return self.label or self.type
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
class Thing:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    sound: str
    bright: str
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


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    cause: str
    consequence: str
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
class Solution:
    id: str
    label: str
    phrase: str
    method: str
    finish: str
    sense: int = 0
    power: int = 0
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
        self.entities: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_fear(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if getattr(e, "meters", {}).get("broken", 0) >= THRESHOLD and ("fear", e.id) not in world.fired:
            world.fired.add(("fear", e.id))
            if "child" in world.entities:
                world.get("child").memes["worry"] += 1
            out.append("")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


CAUSAL_RULES = [Rule("fear", "social", _r_fear)]


def sensible_responses() -> list[Solution]:
    return [s for s in SOLUTIONS.values() if s.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, p in PROBLEMS.items():
            for sol in SOLUTIONS.values():
                if sol.sense >= SENSE_MIN and sol.power >= 1:
                    combos.append((sid, pid, sol.id))
    return combos


def best_solution() -> Solution:
    return max(SOLUTIONS.values(), key=lambda s: s.sense)


def _do_problem(world: World, problem: Problem, narrate: bool = True) -> None:
    world.get("device").meters["broken"] += 1
    propagate(world, narrate=narrate)


def predict_problem(world: World, problem: Problem) -> dict:
    sim = world.copy()
    _do_problem(sim, problem, narrate=False)
    return {"broken": sim.get("device").meters["broken"] >= THRESHOLD}


def setup(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["hope"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"By the {setting.place}, where the breezes blew and the little bells went "
        f"ding, {child.id} sat with a hammer and dreamed of a shiny thing."
    )
    world.say(
        f'"Oh, {helper.id}," said {child.id}, "I am lame today, but I still can invent '
        f'a way to go and play."'
    )


def introduce_device(world: World, device: Thing) -> None:
    world.say(
        f"{child_name(world)} built {device.phrase}, and called it {device.label}."
    )


def child_name(world: World) -> str:
    return world.get("child").id


def need(world: World, helper: Entity, setting: Setting, goal: Thing) -> None:
    world.say(
        f'"But the path is long," said {helper.id}. "And the ground is rough as a '
        f"tumble of twigs.""
    )
    world.say(
        f'"I know," said {child_name(world)}. "The {goal.label} must roll soft and '
        f"safe, or it will bump and jig.""
    )


def test(world: World, child: Entity, device: Thing) -> None:
    child.memes["bravery"] += 1
    world.say(
        f'"Step right up," sang {child.id}, "I built it with wheels and a tiny bell!"'
    )
    world.say(
        f'But the first try went wobble-wobble; the {device.label} could not roll well.'
    )


def warn(world: World, helper: Entity, child: Entity, problem: Problem) -> None:
    pred = predict_problem(world, PROBLEM_PROXY[problem.id])
    helper.memes["care"] += 1
    world.facts["predicted_broken"] = pred["broken"]
    world.say(
        f'"Easy, easy," said {helper.id}, "if the wheel breaks, the plan will not '
        f"do.""
    )
    world.say(
        f'"Let us mend it kindly, and sing while we sew."'
    )


def mend(world: World, helper: Entity, child: Entity, device: Thing, solution: Solution) -> None:
    device.meters["broken"] = 0
    device.meters["fixed"] += 1
    child.memes["joy"] += 1
    world.say(
        f'Then {helper.id} tied on a {solution.label}, and {child.id} tapped the '
        f"bell."
    )
    world.say(
        f'"There, there," sang {child.id}, "now the little cart can go as well!"'
    )


def ending(world: World, child: Entity, helper: Entity, device: Thing, goal: Thing) -> None:
    child.memes["pride"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"So down they went in the evening light, with {device.label} squeak-squeak "
        f"bright."
    )
    world.say(
        f"The {goal.label} rode steady, and {child.id} laughed, " + '"What a merry '
        f"invention night!"'
    )


def tell(setting: Setting, problem: Problem, solution: Solution, name: str, helper_name: str) -> World:
    world = World()
    child = world.add(Entity(id=name, kind="character", type="boy", role="inventor", traits=["clever", "lame"]))
    helper = world.add(Entity(id=helper_name, kind="character", type="girl", role="helper", traits=["kind"]))
    goal = world.add(Thing(id="goal", label="toy cart", phrase="a little toy cart"))
    device = world.add(Thing(id="device", label="little wheel-cart", phrase="a little wheel-cart"))
    world.facts["problem"] = problem
    world.facts["solution"] = solution
    world.facts["setting"] = setting
    world.facts["goal"] = goal
    world.facts["device"] = device
    setup(world, child, helper, setting)
    world.para()
    introduce_device(world, device)
    need(world, helper, setting, goal)
    test(world, child, device)
    warn(world, helper, child, problem)
    world.para()
    mend(world, helper, child, device, solution)
    ending(world, child, helper, device, goal)
    device.meters["fixed"] = 1
    return world


SETTINGS = {
    "workshop": Setting(id="workshop", place="tiny workshop", sound="ding", bright="bright"),
    "garden": Setting(id="garden", place="garden gate", sound="chirp", bright="gold"),
}

PROBLEMS = {
    "wobble": Problem(id="wobble", label="wobbly wheel", phrase="a wobbly wheel", cause="wobble", consequence="bump"),
    "mud": Problem(id="mud", label="mud on the track", phrase="mud on the track", cause="mud", consequence="stick"),
}

SOLUTIONS = {
    "peg": Solution(id="peg", label="wooden peg", phrase="a wooden peg", method="pin", finish="mend", sense=3, power=1),
    "brace": Solution(id="brace", label="brass brace", phrase="a brass brace", method="stiffen", finish="steady", sense=4, power=2),
}

PROXY = {"wobble": PROBLEMS["wobble"], "mud": PROBLEMS["mud"]}

GIRL_NAMES = ["Maya", "Nina", "Lily", "Zoe"]
BOY_NAMES = ["Tom", "Theo", "Bram", "Finn"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    solution: str
    child: str
    child_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld with a lame inventor and dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--child", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.solution is None or c[2] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, solution = rng.choice(sorted(combos))
    child = args.child or rng.choice(GIRL_NAMES + BOY_NAMES)
    child_gender = args.gender or ("girl" if child in GIRL_NAMES else "boy")
    helper = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != child])
    return StoryParams(setting=setting, problem=problem, solution=solution, child=child, child_gender=child_gender, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme-style story with dialogue about {f["child"].id}, an inventor, and a helpful friend.',
        f'Include the words "lame" and "inventor" in a gentle little tale where a broken invention gets fixed.',
        f'Tell a rhyming story where the child says something, the helper answers, and the ending feels bright and cheerful.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    device = f["device"]
    return [
        QAItem(question="Who is the story about?", answer=f"It is about {child.id}, a little inventor, and {helper.id}, who helps fix the invention."),
        QAItem(question="What problem happened?", answer=f"The {f['problem'].label} made the little {device.label} stop rolling right. That turned the trip into a wobble and a worry."),
        QAItem(question="How did they solve the problem?", answer=f"{helper.id} helped mend the device with {f['solution'].label}, and then it could roll safely again."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does an inventor do?", answer="An inventor thinks up new things and builds them to solve a problem or make life easier."),
        QAItem(question="What does lame mean here?", answer="Here, lame means the child has a leg that hurts or does not work well, so walking is harder."),
        QAItem(question="Why are wheels useful?", answer="Wheels help things roll along more smoothly, so heavy or awkward things can move with less bumping."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in getattr(e, "meters", {}).items() if v}
        memes = {k: v for k, v in getattr(e, "memes", {}).items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({getattr(e, 'type', 'thing'):7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for sid in SOLUTIONS:
        s = SOLUTIONS[sid]
        lines.append(asp.fact("solution", sid))
        lines.append(asp.fact("sense", sid, s.sense))
        lines.append(asp.fact("power", sid, s.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,R) :- setting(S), problem(P), solution(R), sense(R, V), sense_min(M), V >= M, power(R, Pwr), Pwr >= 1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, solution=None, child=None, gender=None, helper=None), random.Random(0)))
        _ = sample.story
    except Exception as e:
        print(f"FAILED: normal generation crashed: {e}")
        return 1
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set != python_set:
        print("MISMATCH between clingo and python valid_combos")
        return 1
    print("OK: verify passed.")
    return 0


CURATED = [
    StoryParams(setting="workshop", problem="wobble", solution="brace", child="Bram", child_gender="boy", helper="Maya"),
    StoryParams(setting="garden", problem="mud", solution="peg", child="Lily", child_gender="girl", helper="Tom"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.solution not in SOLUTIONS:
        raise StoryError("invalid params")
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], SOLUTIONS[params.solution], params.child, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.question, answer=q.answer) for q in story_qa(world)],
        world_qa=[QAItem(question=q.question, answer=q.answer) for q in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
