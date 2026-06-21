#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/vehicle_safari_problem_solving_fairy_tale.py
=============================================================================

A standalone storyworld for a small fairy-tale problem-solving domain.

Premise:
- A child and a helper get ready for a safari ride in a vehicle.
- The vehicle breaks down or gets stuck.
- They solve the problem with a concrete tool and/or clever teamwork.
- The ending proves the change: the safari continues safely and joyfully.

This world keeps the prose child-facing, concrete, and state-driven. It also
includes a Python reasonableness gate plus an inline ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    safari_word: str
    vehicle_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    trouble: str
    cause: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    problem: str
    solution: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    ruler: str
    seed: Optional[int] = None


SETTINGS = {
    "savanna": Setting(
        id="savanna",
        place="the golden savanna",
        mood="warm and wide",
        safari_word="safari",
        vehicle_word="vehicle",
        tags={"safari", "vehicle"},
    ),
    "jungle": Setting(
        id="jungle",
        place="the green jungle path",
        mood="lush and leafy",
        safari_word="safari",
        vehicle_word="vehicle",
        tags={"safari", "vehicle"},
    ),
    "desert": Setting(
        id="desert",
        place="the bright desert trail",
        mood="sunlit and windy",
        safari_word="safari",
        vehicle_word="vehicle",
        tags={"safari", "vehicle"},
    ),
}

PROBLEMS = {
    "flat_tire": Problem(
        id="flat_tire",
        label="a flat tire",
        trouble="the wheel sagged into the sand",
        cause="a sharp thorn had poked the tire",
        risk="the safari could not go on",
        tags={"vehicle", "repair"},
    ),
    "stuck_in_mud": Problem(
        id="stuck_in_mud",
        label="stuck in mud",
        trouble="the vehicle sank and would not roll",
        cause="the path had turned muddy after the rain",
        risk="the animals would be missed",
        tags={"vehicle", "pull"},
    ),
    "broken_belt": Problem(
        id="broken_belt",
        label="a broken belt",
        trouble="the engine coughed and stopped",
        cause="a belt inside the vehicle had snapped",
        risk="the journey had become very still",
        tags={"vehicle", "fix"},
    ),
}

SOLUTIONS = {
    "spare_wheel": Solution(
        id="spare_wheel",
        sense=3,
        power=3,
        text="found the spare wheel under the seat, swapped it in, and tightened the lugs with a silver wrench",
        fail="found the spare wheel, but the tire was too damaged and the wheel still sank",
        qa_text="found the spare wheel under the seat and swapped it in with a silver wrench",
        tags={"repair", "wheel"},
    ),
    "tow_rope": Solution(
        id="tow_rope",
        sense=3,
        power=3,
        text="looped a tow rope around the vehicle and pulled it free with the help of two patient oxen",
        fail="looped a tow rope around the vehicle, but the mud held it fast",
        qa_text="looped a tow rope around the vehicle and pulled it free with help from two oxen",
        tags={"pull", "rope"},
    ),
    "repair_belt": Solution(
        id="repair_belt",
        sense=3,
        power=4,
        text="opened the side panel, mended the snapped belt with a clean new strap, and got the engine humming again",
        fail="opened the side panel, but the snapped belt was too torn to mend quickly",
        qa_text="opened the side panel and mended the snapped belt with a clean new strap",
        tags={"fix", "engine"},
    ),
    "brush_path": Solution(
        id="brush_path",
        sense=2,
        power=2,
        text="used sturdy branches to brush the mud away from the wheels until the vehicle could roll again",
        fail="brushed the mud away, but the vehicle still could not move by itself",
        qa_text="used sturdy branches to brush the mud away from the wheels",
        tags={"pull", "clear"},
    ),
    "low_magic": Solution(
        id="low_magic",
        sense=1,
        power=1,
        text="wished very hard and tapped the hood three times",
        fail="wished very hard and tapped the hood three times, but nothing changed",
        qa_text="wished very hard and tapped the hood three times",
        tags={"magic"},
    ),
}

HEROES = [("Amina", "girl"), ("Niko", "boy"), ("Leah", "girl"), ("Tomas", "boy"), ("Mira", "girl")]
HELPERS = [("Moss", "boy"), ("Suri", "girl"), ("Oren", "boy"), ("Lina", "girl")]
RULERS = ["queen", "king", "wise woman", "wise man", "kind ruler"]


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
        import copy as _copy
        c = World()
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def hazard(problem: Problem, solution: Solution) -> bool:
    return problem.id in {"flat_tire", "stuck_in_mud", "broken_belt"} and solution.sense >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for p in PROBLEMS:
            for sol in SOLUTIONS:
                if hazard(PROBLEMS[p], SOLUTIONS[sol]):
                    out.append((s, p, sol))
    return out


def sensible_solutions() -> list[Solution]:
    return [s for s in SOLUTIONS.values() if s.sense >= 2]


def problem_severity(problem: Problem, delay: int) -> int:
    return 2 + delay if problem.id == "flat_tire" else 3 + delay if problem.id == "stuck_in_mud" else 3 + delay


def can_solve(solution: Solution, problem: Problem, delay: int) -> bool:
    return solution.power >= problem_severity(problem, delay)


def _r_stuck(world: World) -> list[str]:
    out = []
    v = world.get("vehicle")
    p = world.get("problem")
    if v.meters["trouble"] >= THRESHOLD and "stuck" not in world.fired:
        world.fired.add(("stuck",))
        v.memes["worry"] += 1
        p.memes["worry"] += 1
        out.append("__problem__")
    return out


CAUSAL_RULES = [_r_stuck]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule(world):
                changed = True


def predict(world: World, problem: Problem) -> dict:
    sim = world.copy()
    sim.get("vehicle").meters["trouble"] = 1
    propagate(sim)
    return {"worry": sim.get("vehicle").memes["worry"]}


def build_story(world: World, setting: Setting, problem: Problem, solution: Solution) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    ruler = world.get("ruler")
    vehicle = world.get("vehicle")

    world.say(
        f"Once in {setting.place}, {hero.id} and {helper.id} climbed into a little {setting.vehicle_word} for a {setting.safari_word}. "
        f"The day was {setting.mood}, and the path seemed ready for wonder."
    )
    world.say(
        f"They waved to {ruler.label_word if ruler.label else ruler.type} at the gate and rode toward the lions and giraffes."
    )

    world.para()
    world.say(
        f"But soon {problem.trouble}. {problem.cause}, and {problem.risk}."
    )
    world.say(
        f'"Oh no," said {helper.id}. "{hero.id}, we need to solve this."'
    )

    world.para()
    if can_solve(solution, problem, 0):
        world.say(
            f"Then {helper.id} {solution.text}."
        )
        vehicle.meters["trouble"] = 0
        vehicle.memes["joy"] += 1
        hero.memes["joy"] += 1
        helper.memes["joy"] += 1
        world.say(
            f"The {setting.vehicle_word} gave a happy rumble, and the safari rolled on under the bright sky."
        )
        world.para()
        world.say(
            f"At last they saw tall giraffes nibbling leaves and a lion blinking in the grass. "
            f"{hero.id} smiled, because the journey had changed from trouble to triumph."
        )
    else:
        world.say(f"{helper.id} tried to help, but {solution.fail}.")
        world.say(
            f"Luckily, {ruler.label_word if ruler.label else ruler.type} called for a stronger fix and the adventure ended safely, if a little slowly."
        )

    world.facts.update(
        hero=hero,
        helper=helper,
        ruler=ruler,
        setting=setting,
        problem=problem,
        solution=solution,
        vehicle=vehicle,
        solved=vehicle.meters["trouble"] == 0,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story that includes the words "vehicle" and "safari" and shows a problem being solved.',
        f"Tell a child-friendly fairy tale where {f['hero'].id} goes on a safari in a vehicle, something goes wrong, and {f['helper'].id} fixes it.",
        f"Write a short problem-solving adventure about a vehicle on a safari, with a calm helper and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    problem = f["problem"]
    solution = f["solution"]
    setting = f["setting"]
    answer1 = (
        f"The story is about {hero.id} and {helper.id} going on a safari in {setting.place}. "
        f"When the vehicle had trouble, they worked together to fix it."
    )
    answer2 = (
        f"{problem.label.capitalize()} caused the trouble. It made the vehicle stop, so the safari could not continue until someone solved the problem."
    )
    answer3 = (
        f"{helper.id} solved it by {solution.qa_text}. That worked because the fix matched the kind of trouble the vehicle had."
    )
    return [
        QAItem(question="Who is the story about?", answer=answer1),
        QAItem(question="What went wrong on the safari?", answer=answer2),
        QAItem(question="How was the problem solved?", answer=answer3),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vehicle?",
            answer="A vehicle is something people ride in or drive to move from one place to another.",
        ),
        QAItem(
            question="What is a safari?",
            answer="A safari is a journey to look for wild animals in a place like grassland, jungle, or desert.",
        ),
        QAItem(
            question="Why do helpers need the right tool?",
            answer="The right tool solves the actual problem instead of making a guess, so the fix works faster and safer.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for sid, sol in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        lines.append(asp.fact("sense", sid, sol.sense))
        lines.append(asp.fact("power", sid, sol.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, Sol) :- setting(S), problem(P), solution(Sol), sense(Sol, N), sense_min(M), N >= M.
solvable(S, P, Sol) :- valid(S, P, Sol), power(Sol, Pow), trouble(P, T), needed(P, Need), Pow >= Need.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP gate differs from Python gate.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        if not sample.story:
            raise RuntimeError("empty story")
    except Exception as e:
        print(f"MISMATCH: normal generation failed: {e}")
        rc = 1
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
    except Exception as e:
        print(f"MISMATCH: emit smoke test failed: {e}")
        rc = 1
    if rc == 0:
        print("OK: verify passed.")
    return rc


@dataclass
class StorySampleBundle:
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale safari vehicle problem-solving storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--ruler", choices=RULERS)
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
    if args.solution and SOLUTIONS[args.solution].sense < 2:
        raise StoryError("That solution is too silly for a real problem-solving tale.")
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.problem is None or c[1] == args.problem)
        and (args.solution is None or c[2] == args.solution)
    ]
    if not combos:
        raise StoryError("No valid story fits those choices.")
    setting, problem, solution = rng.choice(sorted(combos))
    hero_name, hero_gender = rng.choice(HEROES)
    helper_name, helper_gender = rng.choice(HELPERS)
    if helper_name == hero_name:
        helper_name, helper_gender = "Suri", "girl"
    ruler = args.ruler or rng.choice(RULERS)
    return StoryParams(
        setting=setting,
        problem=problem,
        solution=solution,
        hero=args.hero or hero_name,
        hero_gender=args.hero_gender or hero_gender,
        helper=args.helper or helper_name,
        helper_gender=args.helper_gender or helper_gender,
        ruler=ruler,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.solution not in SOLUTIONS:
        raise StoryError("Unknown story parameters.")
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    solution = SOLUTIONS[params.solution]

    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    ruler = world.add(Entity(id=params.ruler, kind="character", type="queen" if params.ruler == "queen" else "king", label=params.ruler))
    vehicle = world.add(Entity(id="vehicle", kind="thing", type="vehicle", label="vehicle"))

    vehicle.meters["trouble"] = 1.0
    build_story(world, setting, problem, solution)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(setting="savanna", problem="flat_tire", solution="spare_wheel", hero="Amina", hero_gender="girl", helper="Moss", helper_gender="boy", ruler="queen"),
    StoryParams(setting="jungle", problem="stuck_in_mud", solution="tow_rope", hero="Niko", hero_gender="boy", helper="Suri", helper_gender="girl", ruler="king"),
    StoryParams(setting="desert", problem="broken_belt", solution="repair_belt", hero="Leah", hero_gender="girl", helper="Oren", helper_gender="boy", ruler="wise woman"),
]


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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combinations")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
                p.seed = base_seed + i
                s = generate(p)
                if s.story in seen:
                    continue
                seen.add(s.story)
                samples.append(s)
            except StoryError as e:
                print(e)
                return

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
