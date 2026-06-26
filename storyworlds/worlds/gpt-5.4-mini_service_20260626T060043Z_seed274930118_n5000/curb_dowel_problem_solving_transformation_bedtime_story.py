#!/usr/bin/env python3
"""
Storyworld: curb + dowel, with problem solving and transformation.

A tiny bedtime-story domain about a child who wants to keep a small plaything
moving, meets a curb that blocks the way, and discovers how a dowel can turn a
stuck moment into a clever new shape.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "mother", "mom", "woman"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "father", "dad", "man"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    afford: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    blockage: str
    remedy: str
    result: str
    zone: str = "path"
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    transforms_to: str
    helps: set[str] = field(default_factory=set)


@dataclass
class Goal:
    label: str
    phrase: str
    type: str
    role: str = "toy"
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_bits: list[str] = []

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def _do_problem(world: World, actor: Entity, problem: Problem, narrate: bool = True) -> None:
    actor.meters["stuck"] = actor.meters.get("stuck", 0.0) + 1.0
    actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1.0
    if narrate:
        world.say(f"{actor.id} saw the {problem.blockage} and frowned.")


def _use_tool(world: World, actor: Entity, tool: Tool, problem: Problem, goal: Entity, narrate: bool = True) -> None:
    sig = ("use", tool.id, problem.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    actor.memes["hope"] = actor.memes.get("hope", 0.0) + 1.0
    actor.meters["skill"] = actor.meters.get("skill", 0.0) + 1.0
    if narrate:
        world.say(
            f"{actor.id} picked up {tool.label} and tried a new idea."
        )
        world.say(
            f"The {tool.label} became {tool.transforms_to}, and the hard {problem.blockage} "
            f"turned into a softer path."
        )
        world.say(
            f"That let {goal.id} move again."
        )


def propagate(world: World, narrate: bool = True) -> None:
    hero = next((e for e in world.entities.values() if e.kind == "character"), None)
    problem = world.facts.get("problem")
    tool = world.facts.get("tool")
    goal = world.facts.get("goal")
    if not hero or not problem or not tool or not goal:
        return
    if hero.meters.get("stuck", 0.0) >= THRESHOLD and tool.id not in world.fired:
        _use_tool(world, hero, tool, problem, goal, narrate=narrate)


def reason_gate(problem: Problem, goal: Goal, tool: Tool) -> Optional[str]:
    if problem.id != "curb" or tool.id != "dowel":
        return "This world only tells the curb-and-dowel story."
    if "roll" not in problem.tags:
        return "The problem is too unlike the story's little turning point."
    if "ramp" not in tool.helps:
        return "The dowel would not actually help transform the problem."
    if goal.type not in {"toy_car", "ball"}:
        return "The goal needs to be something small that can travel along the path."
    return None


SETTINGS = {
    "bedroom": Setting(place="the bedroom", indoor=True, afford={"curb"}),
    "hallway": Setting(place="the hallway", indoor=True, afford={"curb"}),
    "garden_path": Setting(place="the garden path", indoor=False, afford={"curb"}),
}

PROBLEMS = {
    "curb": Problem(
        id="curb",
        verb="go past the curb",
        gerund="rolling to the curb",
        blockage="curb",
        remedy="ramp",
        result="smooth path",
        zone="path",
        keyword="curb",
        tags={"roll", "block", "path"},
    ),
}

TOOLS = {
    "dowel": Tool(
        id="dowel",
        label="a smooth dowel",
        phrase="a smooth wooden dowel",
        use="lean it under the toy",
        transforms_to="a little ramp",
        helps={"ramp", "lever", "balance"},
    ),
}

GOALS = {
    "toy_car": Goal(
        label="toy car",
        phrase="a little red toy car",
        type="toy_car",
    ),
    "marble": Goal(
        label="marble",
        phrase="a shiny marble",
        type="marble",
    ),
}

NAMES = ["Mina", "Leo", "Iris", "Noah", "Ava", "Nina", "Owen", "Maya"]
TRAITS = ["gentle", "curious", "quiet", "patient", "bright", "careful"]


@dataclass
class StoryParams:
    place: str
    problem: str
    goal: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            if pid not in setting.afford:
                continue
            for gid, goal in GOALS.items():
                if goal.type in {"toy_car", "marble"}:
                    out.append((place, pid, gid))
    return out


def explain_rejection(problem: Problem, goal: Goal) -> str:
    return (
        f"(No story: this gentle world needs a small movable thing to face the curb, "
        f"and the tool must turn into a ramp. The pairing {problem.id} + {goal.label} "
        f"doesn't give that clear bedtime-turn.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: curb, dowel, problem solving, transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.problem and args.goal:
        p = PROBLEMS[args.problem]
        g = GOALS[args.goal]
        err = reason_gate(p, g, TOOLS["dowel"])
        if err:
            raise StoryError(err)

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.goal is None or c[2] == args.goal)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, goal = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, goal=goal, name=name, gender=gender, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type="parent", label="the parent"))
    problem = PROBLEMS[params.problem]
    tool = TOOLS["dowel"]
    goal = GOALS[params.goal]
    g = world.add(Entity(id=goal.label, kind="thing", type=goal.type, label=goal.label, phrase=goal.phrase,
                         owner=hero.id, caretaker=parent.id, role="goal"))
    hero.meters["care"] = 1.0
    hero.memes["love"] = 1.0

    world.say(f"{hero.id} was a {params.trait} little {params.gender} who loved quiet bedtime play.")
    world.say(f"{hero.pronoun().capitalize()} liked to roll {g.phrase} across {world.setting.place}.")

    world.para()
    world.say(f"But one evening, the {problem.blockage} blocked the way.")
    hero.meters["stuck"] = hero.meters.get("stuck", 0.0) + 1.0
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.say(f"{hero.id} stopped and looked at the curb, thinking hard.")

    world.para()
    world.say(f"Then {hero.id} found {tool.phrase}.")
    world.say(f"{hero.id} said, 'Maybe I can use this to make a {problem.remedy}.'")
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"Soon the dowel was not just a dowel anymore; it was a little ramp, and the curb felt less big."
    )
    world.say(
        f"{g.id} rolled over the new shape, and {hero.id} smiled the sleepy smile of someone who solved a problem."
    )
    world.say(
        f"The room grew calm again, with the toy waiting safely at the other side of the curb."
    )

    world.facts.update(hero=hero, parent=parent, problem=problem, tool=tool, goal=g)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a bedtime story for a preschool child about {hero.id} solving a small problem with a curb and a dowel.',
        f"Tell a gentle story where {hero.id} finds a way to turn a curb into a path using a dowel.",
        f'Write a calm, child-facing story that includes the words "curb" and "dowel" and ends with a transformation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, problem, tool, goal = f["hero"], f["problem"], f["tool"], f["goal"]
    return [
        QAItem(
            question=f"What problem did {hero.id} face in the story?",
            answer=f"{hero.id} faced a curb that blocked the way for {goal.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} use to solve the problem?",
            answer=f"{hero.id} used {tool.phrase} to make a little ramp.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The curb still stayed there, but it no longer stopped {goal.label}; the dowel had become a ramp and the path felt open again.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after solving the problem?",
            answer=f"{hero.id} felt calm and proud after figuring out a clever way forward.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a curb?",
            answer="A curb is the raised edge between a road or walkway and a sidewalk or path.",
        ),
        QAItem(
            question="What is a dowel?",
            answer="A dowel is a smooth, round stick made of wood or another material. People can use it in building or simple craft projects.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find a way around a difficulty so things can work again.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a new form or a new use.",
        ),
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.
valid(Place, Problem, Goal) :- setting(Place), problem(Problem), goal(Goal),
    afford(Place, Problem), problem_gate(Problem, Goal).
problem_gate(curb, toy_car).
problem_gate(curb, marble).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for p in sorted(setting.afford):
            lines.append(asp.fact("afford", pid, p))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    clingo_set = sorted(set(asp.atoms(model, "valid")))
    py_set = sorted(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(set(clingo_set) - set(py_set)))
    print("  only in python:", sorted(set(py_set) - set(clingo_set)))
    return 1


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(50, args.n * 50):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        sample = generate(params)
        i += 1
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program())
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        vals = sorted(set(asp.atoms(model, "valid")))
        for place, prob, goal in vals:
            print(place, prob, goal)
        return

    if args.all:
        samples = [generate(StoryParams(place=p, problem=pr, goal=g, name="Mina", gender="girl", trait="gentle"))
                   for p, pr, g in valid_combos()]
    else:
        samples = build_samples(args)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
