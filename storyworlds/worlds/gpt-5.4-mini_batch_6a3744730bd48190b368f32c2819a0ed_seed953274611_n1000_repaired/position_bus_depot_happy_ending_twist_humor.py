#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/position_bus_depot_happy_ending_twist_humor.py
===============================================================================

A small Storyweavers storyworld for a slice-of-life scene at a bus depot.

Premise:
- A child or small family is waiting at a bus depot.
- A tiny problem appears around a "position" word: a sign, a seat, a suitcase,
  or where someone stands in line.
- The twist is gentle and humorous: a mistaken position turns out to be useful.
- The ending is happy: the right bus, seat, or place is found, and the day ends
  with a smile.

The world is intentionally compact:
- typed entities with physical meters and emotional memes
- state-driven prose
- a reasonableness gate
- inline ASP rules with parity verification
- three QA sets grounded in the simulated world

This script is standalone and stdlib-only apart from the shared Storyweavers
result containers and optional clingo usage through the shared ASP helper.
"""

from __future__ import annotations

import argparse
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
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
    label: str
    details: str
    quiet: bool = True
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
    trigger: str
    phrase: str
    location: str
    happens_when: str
    twist: str
    funny_detail: str
    risky: bool = False
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
class Fix:
    id: str
    text: str
    effect: str
    ending_image: str
    power: int
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
    setting: str = "bus_depot"
    problem: str = "wrong_bench"
    fix: str = "ask_driver"
    child_name: str = "Mia"
    child_gender: str = "girl"
    adult_name: str = "Dad"
    adult_gender: str = "man"
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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_humor(world: World) -> list[str]:
    out: list[str] = []
    p = world.facts.get("problem_obj")
    if not p:
        return out
    child = world.get("child")
    if child.memes["confusion"] < THRESHOLD:
        return out
    sig = ("humor", p.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["amused"] += 1
    out.append(p.funny_detail)
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    adult = world.get("adult")
    if world.facts.get("resolved") and ("relief", "done") not in world.fired:
        world.fired.add(("relief", "done"))
        child.memes["joy"] += 1
        adult.memes["joy"] += 1
        adult.memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("humor", "social", _r_humor), Rule("relief", "social", _r_relief)]


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


def reason_gate(problem: Problem, fix: Fix) -> bool:
    return (problem.risky and fix.power >= 1) or (not problem.risky and fix.power >= 0)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, prob in PROBLEMS.items():
            for fid, fx in FIXES.items():
                if reason_gate(prob, fx):
                    combos.append((sid, pid))
    return combos


def predict(world: World, problem: Problem, fix: Fix) -> dict:
    sim = world.copy()
    _act_problem(sim, sim.get("child"), problem, narrate=False)
    _apply_fix(sim, sim.get("adult"), fix, narrate=False)
    return {
        "resolved": sim.facts.get("resolved", False),
        "joy": sim.get("child").memes["joy"],
    }


def _act_problem(world: World, child: Entity, problem: Problem, narrate: bool = True) -> None:
    child.memes["curiosity"] += 1
    child.memes["confusion"] += 1
    world.facts["problem_obj"] = problem
    world.say(f"{child.id} noticed {problem.phrase} at the {problem.location}.")
    world.say(f"That {problem.happens_when}, and {problem.twist}")
    if narrate:
        propagate(world, narrate=narrate)


def _apply_fix(world: World, adult: Entity, fix: Fix, narrate: bool = True) -> None:
    child = world.get("child")
    child.meters["position"] += 1
    child.memes["calm"] += 1
    world.facts["resolved"] = True
    body = fix.text.replace("{child}", child.id)
    world.say(f"{adult.label_word.capitalize()} smiled and {body}.")
    world.say(fix.ending_image)
    if narrate:
        propagate(world, narrate=narrate)


def tell(setting: Setting, problem: Problem, fix: Fix, child_name: str, child_gender: str,
         adult_name: str, adult_gender: str) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name))
    adult = world.add(Entity(id="adult", kind="character", type=adult_gender, label=adult_name, role="helper"))
    world.add(Entity(id="depot", type="place", label=setting.label))
    child.memes["curiosity"] = 1.0

    world.say(
        f"At the bus depot, {child.id} and {adult.id} waited beside the timetable board. "
        f"{setting.details}"
    )
    world.say(
        f"{child.id} kept shifting {child.pronoun('possessive')} position while buses sighed at the curb."
    )
    world.para()
    _act_problem(world, child, problem)
    world.para()

    world.say(
        f"{adult.id} looked at the scene, then at {problem.trigger}. "
        f"'{problem.happens_when.capitalize()}, {problem.twist.lower()}'"
    )
    world.say(
        f"{adult.id} suggested they {fix.text}."
    )
    _apply_fix(world, adult, fix)
    world.para()

    world.say(
        f"In the end, {child.id} laughed, because the mistake had turned out useful."
        f" {fix.effect}"
    )

    world.facts.update(
        child=child,
        adult=adult,
        setting=setting,
        problem=problem,
        fix=fix,
        resolved=True,
    )
    return world


SETTINGS = {
    "bus_depot": Setting(
        id="bus_depot",
        label="bus depot",
        details="The benches were a little too shiny, the floor smelled faintly of rain, and the route signs clicked softly overhead.",
    )
}

PROBLEMS = {
    "wrong_bench": Problem(
        id="wrong_bench",
        trigger="the bench with the blue sticker",
        phrase="the bench with the blue sticker",
        location="wrong bench",
        happens_when="the bus for the zoo stopped at the far platform",
        twist="the blue sticker was on the bench for lost gloves, not lost people",
        funny_detail="A tiny paper tag fluttered up and read: LOST GLOVES, PLEASE RETURN TO THE NEAREST HAND.",
        risky=False,
        tags={"position", "humor", "twist"},
    ),
    "backwards_map": Problem(
        id="backwards_map",
        trigger="the route map turned upside down",
        phrase="the route map turned upside down",
        location="ticket table",
        happens_when="the arrows pointed in funny directions",
        twist="the map was not broken at all; it was just being dramatic",
        funny_detail="The map seemed to wave back, as if it wanted a better angle on the day.",
        risky=False,
        tags={"position", "humor", "twist"},
    ),
    "seat_swap": Problem(
        id="seat_swap",
        trigger="the seat marked for one passenger",
        phrase="the seat marked for one passenger",
        location="waiting row",
        happens_when="the bus arrived right on time",
        twist="the reserved seat belonged to a sleepy pigeon for exactly three seconds",
        funny_detail="A pigeon hopped off the seat as if it had been late for an important meeting.",
        risky=False,
        tags={"position", "humor", "twist"},
    ),
}

FIXES = {
    "ask_driver": Fix(
        id="ask_driver",
        text="ask the driver which line was theirs",
        effect="The driver pointed with a gloved finger, and the right bus rolled in with a cheerful hiss.",
        ending_image="Soon they were in the correct position by the correct door, smiling at the right bus.",
        power=1,
        tags={"help", "bus"},
    ),
    "check_board": Fix(
        id="check_board",
        text="read the board again and follow the arrows this time",
        effect="The new reading solved the puzzle at once, and the board felt almost proud of itself.",
        ending_image="The child stood in the correct position under the correct sign, grinning like a detective.",
        power=1,
        tags={"help", "sign"},
    ),
    "move_over": Fix(
        id="move_over",
        text="move one step over to the open spot",
        effect="That made room for everyone, and the tiny crowd puzzle clicked into place.",
        ending_image="By the end, the child was in the right position and the bench was finally behaving.",
        power=1,
        tags={"help", "space"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Theo", "Max"]


@dataclass
class StoryParams:
    setting: str = "bus_depot"
    problem: str = "wrong_bench"
    fix: str = "ask_driver"
    child_name: str = "Mia"
    child_gender: str = "girl"
    adult_name: str = "Dad"
    adult_gender: str = "man"
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
    ap = argparse.ArgumentParser(description="Slice-of-life bus depot storyworld with a gentle twist and happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult-name")
    ap.add_argument("--adult-gender", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.fix:
        if not reason_gate(PROBLEMS[args.problem], FIXES[args.fix]):
            raise StoryError("The chosen problem and fix do not make a sensible story.")
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    fix = args.fix or rng.choice(list(FIXES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    adult_gender = args.adult_gender or rng.choice(["man", "woman"])
    adult_name = args.adult_name or ("Dad" if adult_gender == "man" else "Mom")
    return StoryParams(
        setting=setting,
        problem=problem,
        fix=fix,
        child_name=child_name,
        child_gender=child_gender,
        adult_name=adult_name,
        adult_gender=adult_gender,
    )


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    problem = f["problem"]
    fix = f["fix"]
    return [
        (
            "What was the child doing at the bus depot?",
            f"{child.id} was waiting with {adult.id} and watching the buses, but {child.id} kept thinking about {problem.phrase}. The little mix-up gave the story its funny twist.",
        ),
        (
            "Why did the problem matter?",
            f"It mattered because {problem.twist}. That meant the child had to stop and figure out the real position instead of guessing.",
        ),
        (
            "How did the story end?",
            f"It ended happily, with {adult.id} helping {child.id} use a smarter plan: {fix.text}. After that, the child was in the right position and everyone could relax.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        (
            "What is a bus depot?",
            "A bus depot is a place where buses wait, turn around, or get ready for their next ride. People may stand there to catch a bus.",
        ),
        (
            "What does position mean?",
            "Position means where someone or something is placed or standing. It can mean being in the right spot in a line, on a seat, or near a sign.",
        ),
        (
            "Why can a timetable be helpful?",
            "A timetable shows when buses are supposed to come and go. It helps people know which bus to wait for.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story set at a bus depot that includes the word "position" and ends happily.',
        f"Tell a gentle humorous story where {f['child'].id} and {f['adult'].id} face a small mix-up about {f['problem'].phrase}, then fix it with a calm solution.",
        f"Write a short story with a twist and a happy ending at a bus depot, where a child learns what the right position is.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="bus_depot", problem="wrong_bench", fix="ask_driver", child_name="Mia", child_gender="girl", adult_name="Dad", adult_gender="man"),
    StoryParams(setting="bus_depot", problem="backwards_map", fix="check_board", child_name="Leo", child_gender="boy", adult_name="Mom", adult_gender="woman"),
    StoryParams(setting="bus_depot", problem="seat_swap", fix="move_over", child_name="Nora", child_gender="girl", adult_name="Dad", adult_gender="man"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if params.fix not in FIXES:
        raise StoryError("Unknown fix.")
    world = tell(
        SETTINGS[params.setting],
        PROBLEMS[params.problem],
        FIXES[params.fix],
        params.child_name,
        params.child_gender,
        params.adult_name,
        params.adult_gender,
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if p.risky:
            lines.append(asp.fact("risky", pid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P) :- setting(S), problem(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP parity failed.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as err:
        rc = 1
        print(f"MISMATCH: generation failed: {err}")
    print("OK" if rc == 0 else "FAILED")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
            header = f"### {p.child_name} at the bus depot ({p.problem} -> {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
