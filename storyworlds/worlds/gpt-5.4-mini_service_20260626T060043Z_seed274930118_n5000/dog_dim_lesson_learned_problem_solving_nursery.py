#!/usr/bin/env python3
"""
storyworlds/worlds/dog_dim_lesson_learned_problem_solving_nursery.py
====================================================================

A tiny nursery-rhyme storyworld about a dog-sized problem, a lesson learned,
and a child-friendly problem-solving turn.

Premise:
- A small dog notices a mismatch between what it wants and what the world can do.
- The helper character first tries the wrong plan, then learns a better one.
- The ending proves the lesson through a changed state: the problem is solved,
  the friendship is calmer, and the right tool/place/method is used.

The prose leans rhythmic and simple, with repeating phrasing suitable for a
nursery style. The world model tracks both physical meters and emotional memes,
and the story is driven by those state changes rather than a frozen template.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    affordances: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    verb: str
    gerund: str
    trouble: str
    fix_hint: str
    location: str
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    solves: set[str]
    helps_place: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.problem_zone: set[str] = set()

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.problem_zone = set(self.problem_zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _apply_noise(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters.get("trouble", 0.0) < THRESHOLD:
            continue
        sig = ("noise", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] = e.memes.get("worry", 0.0) + 1
        out.append(f"The little day got fussy for {e.label}.")
    return out


def _apply_fix(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("plan", 0.0) < THRESHOLD:
            continue
        if actor.meters.get("problem_solved", 0.0) >= THRESHOLD:
            continue
        if not world.facts.get("tool_used"):
            continue
        sig = ("fix", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["problem_solved"] = 1.0
        actor.memes["calm"] = actor.memes.get("calm", 0.0) + 1
        actor.memes["lesson"] = actor.memes.get("lesson", 0.0) + 1
        out.append("__fix__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    while True:
        changed = False
        for rule in (_apply_noise, _apply_fix):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__fix__")
        if not changed:
            break
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def nursery_tone(name: str) -> str:
    return f"{name} in a little rhyme, with a problem for the time"


def start_line(hero: Entity, dog: Entity, place: Place) -> str:
    return f"{hero.label} and a dog-dim dog named {dog.label} were twirling near {place.label}."


def lesson_line(hero: Entity) -> str:
    return f"{hero.pronoun().capitalize()} learned that a small pause can make a big, bright plan."


def predict_solution(world: World, hero: Entity, problem: Problem, tool: Tool) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters["plan"] = 1.0
    sim.get(hero.id).meters["trouble"] = 0.0
    sim.facts["tool_used"] = tool.id in problem.tags or problem.id in tool.solves
    propagate(sim, narrate=False)
    return sim.get(hero.id).meters.get("problem_solved", 0.0) >= THRESHOLD


def tell(place: Place, problem: Problem, tool: Tool, hero_name: str, dog_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="child",
        label=hero_name,
        meters={"plan": 0.0, "trouble": 0.0, "problem_solved": 0.0},
        memes={"curious": 1.0},
    ))
    dog = world.add(Entity(
        id=dog_name,
        kind="character",
        type="dog",
        label=dog_name,
        plural=False,
        meters={"trouble": 0.0},
        memes={"happy": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="mother",
        label="the helper",
        meters={"patience": 1.0},
        memes={"warm": 1.0},
    ))
    prop = world.add(Entity(
        id="tool",
        type="thing",
        label=tool.label,
        phrase=tool.phrase,
        owner=hero.id,
        plural=tool.plural,
    ))

    world.say(start_line(hero, dog, place))
    world.say(f"{hero.label} liked the {problem.label} and liked to try {problem.gerund}.")
    world.say(f"But the {problem.label} would make a tiny tangle, and that was the trouble.")

    world.para()
    world.say(f"One day, {hero.label} tried to {problem.verb}, but it did not go just so.")
    hero.meters["trouble"] += 1
    dog.meters["trouble"] += 1
    propagate(world)

    world.say(
        f"{helper.label} said, \"A lesson learned is a helper found; let's use the {tool.label}.\""
    )
    hero.meters["plan"] += 1
    world.facts["tool_used"] = bool(tool.solves & {problem.id}) or problem.id in tool.solves

    world.para()
    if predict_solution(world, hero, problem, tool):
        hero.meters["problem_solved"] += 1
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
        dog.memes["joy"] = dog.memes.get("joy", 0.0) + 1
        world.say(f"{hero.label} took a breath and used the {tool.label}.")
        world.say(
            f"Then the little problem was solved, and {hero.label} and {dog.label} were calm again."
        )
        world.say(
            f"{lesson_line(hero)} {hero.label} smiled, and the {tool.label} stayed ready for next time."
        )
    else:
        raise StoryError("The chosen tool does not really solve this problem in the world model.")

    world.facts.update(
        hero=hero,
        dog=dog,
        helper=helper,
        tool=prop,
        problem=problem,
        place=place,
    )
    return world


PLACES = {
    "yard": Place(id="yard", label="the yard", indoors=False, affordances={"roll", "fetch", "dig"}),
    "room": Place(id="room", label="the playroom", indoors=True, affordances={"stack", "sort", "share"}),
    "path": Place(id="path", label="the garden path", indoors=False, affordances={"roll", "carry", "share"}),
}

PROBLEMS = {
    "stuck_ball": Problem(
        id="stuck_ball",
        label="a stuck ball",
        verb="reach the ball",
        gerund="reaching for the ball",
        trouble="the ball rolled under a box",
        fix_hint="move the box first",
        location="under the box",
        mess="stuck",
        tags={"ball", "box", "move"},
    ),
    "too_tall_step": Problem(
        id="too_tall_step",
        label="a tall step",
        verb="climb the step",
        gerund="climbing the step",
        trouble="the step was a bit too high for a little jump",
        fix_hint="use a stool",
        location="by the step",
        mess="high",
        tags={"step", "stool", "lift"},
    ),
    "snagged_string": Problem(
        id="snagged_string",
        label="a snagged string",
        verb="pull the string",
        gerund="pulling the string",
        trouble="the string had tied itself into a knot",
        fix_hint="pick the knot loose",
        location="on the floor",
        mess="snagged",
        tags={"string", "knot", "pick"},
    ),
}

TOOLS = {
    "box_nudge": Tool(
        id="box_nudge",
        label="a little box nudge",
        phrase="a tiny nudge for the box",
        solves={"stuck_ball"},
    ),
    "stool": Tool(
        id="stool",
        label="a stool",
        phrase="a sturdy little stool",
        solves={"too_tall_step"},
    ),
    "pinch_pick": Tool(
        id="pinch_pick",
        label="two pinchy fingers",
        phrase="two careful fingers for the knot",
        solves={"snagged_string"},
    ),
}

NAMES = ["Mina", "Luca", "Nia", "Eli", "Pip", "Tara", "Owen", "June"]
DOG_NAMES = ["Bax", "Momo", "Pudding", "Ruff", "Bibi"]


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    name: str
    dog_name: str
    seed: Optional[int] = None


def reasonableness_gate(place: Place, problem: Problem, tool: Tool) -> bool:
    return problem.id in tool.solves


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid in PLACES:
        for pr in PROBLEMS:
            for tid in TOOLS:
                if reasonableness_gate(PLACES[pid], PROBLEMS[pr], TOOLS[tid]):
                    out.append((pid, pr, tid))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story about {f["hero"].label}, a dog-dim dog, and a problem that gets solved.',
        f"Tell a gentle story where {f['hero'].label} learns to use {f['tool'].label} to help {f['dog'].label}.",
        f"Write a story with a lesson learned and a problem-solving turn at {f['place'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    dog = f["dog"]
    tool = f["tool"]
    problem = f["problem"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who had the little problem at {place.label}?",
            answer=f"{hero.label} had the little problem, and {dog.label} was there too.",
        ),
        QAItem(
            question=f"What helped {hero.label} solve {problem.label}?",
            answer=f"{tool.label} helped solve {problem.label}. That was the careful problem-solving choice.",
        ),
        QAItem(
            question=f"What lesson did {hero.label} learn?",
            answer=f"{hero.label} learned that pausing first and choosing the right helper can solve a problem kindly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find a good way to make the trouble stop or get easier.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a helpful thing you understand after trying, noticing, and choosing better next time.",
        ),
        QAItem(
            question="Why do people use tools?",
            answer="People use tools to help them do hard jobs more safely or more easily.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(place.affordances):
            lines.append(asp.fact("affords", pid, a))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for t in sorted(problem.tags):
            lines.append(asp.fact("tag", pid, t))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(tool.solves):
            lines.append(asp.fact("solves", tid, p))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place,Problem,Tool) :- place(Place), problem(Problem), tool(Tool), solves(Tool,Problem).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about dog-dim lessons and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--dog-name", choices=DOG_NAMES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, tool = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        problem=problem,
        tool=tool,
        name=args.name or rng.choice(NAMES),
        dog_name=args.dog_name or rng.choice(DOG_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    world = tell(place, problem, tool, params.name, params.dog_name)
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
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem, tool) combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for pid, pr, tid in valid_combos():
            params = StoryParams(place=pid, problem=pr, tool=tid, name="Mina", dog_name="Bax")
            samples.append(generate(params))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
