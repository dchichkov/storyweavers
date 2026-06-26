#!/usr/bin/env python3
"""
storyworlds/worlds/minister_ganache_coarse_bravery_magic_problem_solving.py
============================================================================

A small folk-tale story world about a minister, a coarse trouble, and a sweet
ganache reward. The child-facing story is built from a simulated world where
bravery, magic, and problem solving change what happens.

Seed tale premise:
- A village minister keeps a fine ganache cake for the Lantern Feast.
- A coarse wind, rough with grit, begins spoiling the path and rattling the
  feast preparations.
- The minister chooses bravery, asks for a little magic, and solves the
  problem by changing the path instead of losing the cake.

The generated stories are intentionally narrow: they focus on one credible
problem, one clever turn, and one earned ending image.
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
MINISTER_TITLES = [
    "minister",
    "village minister",
    "church minister",
]

PLACES = [
    "the village square",
    "the chapel yard",
    "the lantern road",
    "the stone bridge",
]

PROBLEMS = [
    "a coarse wind that blew grit into everything",
    "a coarse rain that made the path slick and rough",
    "a coarse crowd that kept bumping the feast table",
]

MAGICS = [
    "a small charm of shining dust",
    "a soft spell of calm light",
    "a lantern-bell charm",
]

SOLUTIONS = [
    "covered the cake with a woven cloth",
    "laid smooth boards over the rough path",
    "set up lanterns to guide everyone around the grit",
    "asked the children to carry the cake in a covered tray",
]

TREATS = [
    "a ganache cake",
    "a round ganache tart",
    "a sweet ganache loaf",
]

NAMES = [
    "Mara",
    "Ansel",
    "Ivo",
    "Nina",
    "Tobin",
    "Sera",
]

TRAITS = [
    "steady",
    "kind",
    "brave",
    "careful",
    "calm",
]

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("rough", "safe", "glad", "fear", "hope", "solved"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the village square"
    indoors: bool = False


@dataclass
class ProblemDef:
    id: str
    phrase: str
    roughness: str
    danger: str
    keyword: str


@dataclass
class MagicDef:
    id: str
    phrase: str
    effect: str
    keyword: str


@dataclass
class SolutionDef:
    id: str
    phrase: str
    keyword: str


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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    problem: str
    magic: str
    solution: str
    treat: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Inline story model
# ---------------------------------------------------------------------------
def _apply_problem(world: World) -> list[str]:
    out: list[str] = []
    problem = world.get("problem")
    cake = world.get("cake")
    if problem.meters["rough"] >= 1 and ("problem", problem.id) not in world.fired:
        world.fired.add(("problem", problem.id))
        cake.memes["fear"] += 1
        cake.meters["safe"] -= 0.25
        out.append("The trouble made the cake feel at risk.")
    return out


def _apply_magic(world: World) -> list[str]:
    out: list[str] = []
    minister = world.get("minister")
    charm = world.get("magic")
    if minister.memes["hope"] >= 1 and charm.meters["safe"] < 1 and ("magic", charm.id) not in world.fired:
        world.fired.add(("magic", charm.id))
        charm.meters["safe"] += 1
        minister.memes["glad"] += 1
        out.append("The little charm woke and made the air gentler.")
    return out


def _apply_solution(world: World) -> list[str]:
    out: list[str] = []
    problem = world.get("problem")
    solution = world.get("solution")
    if problem.meters["rough"] >= 1 and solution.meters["safe"] >= 1 and ("solve", solution.id) not in world.fired:
        world.fired.add(("solve", solution.id))
        problem.meters["rough"] = 0
        solution.memes["solved"] += 1
        out.append("The rough trouble was answered by a clever fix.")
    return out


RULES = [_apply_problem, _apply_magic, _apply_solution]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    world = World(Setting(place=PLACES[0] if params.place not in PLACES else params.place))

    minister = world.add(Entity(
        id="minister",
        kind="character",
        type="minister",
        label="minister",
        phrase=f"a {params.trait} minister named {params.name}",
        memes={"bravery": 1.0, "glad": 0.0, "hope": 0.0, "fear": 0.0, "solved": 0.0},
    ))
    problem = world.add(Entity(
        id="problem",
        kind="thing",
        type="problem",
        label="problem",
        phrase=params.problem,
        meters={"rough": 0.0, "safe": 0.0},
        memes={"fear": 0.0, "hope": 0.0},
    ))
    magic = world.add(Entity(
        id="magic",
        kind="thing",
        type="magic",
        label="magic",
        phrase=params.magic,
        meters={"safe": 0.0},
        memes={"glad": 0.0},
    ))
    solution = world.add(Entity(
        id="solution",
        kind="thing",
        type="solution",
        label="solution",
        phrase=params.solution,
        meters={"safe": 0.0},
        memes={"solved": 0.0},
    ))
    cake = world.add(Entity(
        id="cake",
        kind="thing",
        type="treat",
        label="ganache cake",
        phrase=params.treat,
        owner="minister",
        caretaker="minister",
        meters={"safe": 1.0, "rough": 0.0},
        memes={"fear": 0.0, "glad": 0.0},
    ))

    world.say(
        f"Long ago, in {world.setting.place}, there was a {params.trait} minister named {params.name}. "
        f"{params.name} kept {params.treat} for the feast and watched it like a lantern in the dark."
    )
    world.say(
        f"One day, {params.problem}. The coarse trouble made the path hard to trust, and the feast table began to tremble."
    )
    world.para()
    world.say(
        f"{params.name} did not hide. With brave feet, the minister stepped forward and said, "
        f"\"We can solve this if we think carefully.\""
    )
    minister.memes["hope"] += 1
    problem.meters["rough"] += 1
    propagate(world)
    world.say(
        f"Then {params.name} asked for {params.magic}. The little magic gleamed softly and helped everyone see a kinder way."
    )
    magic.meters["safe"] += 1
    minister.memes["hope"] += 1
    propagate(world)
    world.para()
    world.say(
        f"In the end, {params.solution}. The ganache cake stayed safe, the coarse trouble lost its edge, and the feast went on."
    )
    minister.memes["glad"] += 1
    cake.memes["glad"] += 1
    world.facts.update(
        minister=minister,
        problem=problem,
        magic=magic,
        solution=solution,
        cake=cake,
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# Registries and validation
# ---------------------------------------------------------------------------
PROBLEM_REGISTRY = {
    "wind": ProblemDef(
        id="wind",
        phrase="a coarse wind that blew grit into everything",
        roughness="coarse",
        danger="rough and dusty",
        keyword="wind",
    ),
    "rain": ProblemDef(
        id="rain",
        phrase="a coarse rain that made the path slick and rough",
        roughness="coarse",
        danger="slick and rough",
        keyword="rain",
    ),
    "crowd": ProblemDef(
        id="crowd",
        phrase="a coarse crowd that kept bumping the feast table",
        roughness="coarse",
        danger="bumpy and loud",
        keyword="crowd",
    ),
}

MAGIC_REGISTRY = {
    "dust": MagicDef(
        id="dust",
        phrase="a small charm of shining dust",
        effect="soften the rough air",
        keyword="dust",
    ),
    "light": MagicDef(
        id="light",
        phrase="a soft spell of calm light",
        effect="steady the path",
        keyword="light",
    ),
    "bell": MagicDef(
        id="bell",
        phrase="a lantern-bell charm",
        effect="call everyone together",
        keyword="bell",
    ),
}

SOLUTION_REGISTRY = {
    "cloth": SolutionDef(
        id="cloth",
        phrase="covered the cake with a woven cloth",
        keyword="cloth",
    ),
    "boards": SolutionDef(
        id="boards",
        phrase="laid smooth boards over the rough path",
        keyword="boards",
    ),
    "lanterns": SolutionDef(
        id="lanterns",
        phrase="set up lanterns to guide everyone around the grit",
        keyword="lanterns",
    ),
    "tray": SolutionDef(
        id="tray",
        phrase="asked the children to carry the cake in a covered tray",
        keyword="tray",
    ),
}

TREAT_REGISTRY = {
    "cake": "a ganache cake",
    "tart": "a round ganache tart",
    "loaf": "a sweet ganache loaf",
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, p, s) for place in PLACES for p in PROBLEM_REGISTRY for s in SOLUTION_REGISTRY]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a short folk tale for children about a {p.trait} minister, {p.problem}, and {p.magic}.',
        f"Tell a gentle story where {p.name} the minister faces a coarse problem and solves it with bravery and {p.magic}.",
        f'Write a simple village story that includes the word "{p.solution}" and ends with the ganache treat staying safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {p.name}, a {p.trait} minister who stayed brave when the coarse trouble arrived.",
        ),
        QAItem(
            question=f"What kind of problem came to the village?",
            answer=f"{p.problem.capitalize()} came to the village, and it made the path feel rough and hard to trust.",
        ),
        QAItem(
            question=f"What sweet thing did the minister protect?",
            answer=f"{p.name} protected {p.treat}, so the ganache treat could stay safe for the feast.",
        ),
        QAItem(
            question=f"How did the minister respond to the trouble?",
            answer=f"{p.name} answered with bravery, asked for {p.magic}, and used problem solving to fix the situation.",
        ),
        QAItem(
            question=f"What was the ending of the tale?",
            answer=f"The ending was happy because {p.solution} and the ganache cake stayed safe while the feast went on.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ganache?",
            answer="Ganache is a smooth, rich chocolate cream or glaze that can be spread on cakes and sweets.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel nervous or afraid.",
        ),
        QAItem(
            question="What is magic in a folk tale?",
            answer="Magic in a folk tale is a special, impossible help that makes wonder happen.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully to find a good answer when something goes wrong.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", ""]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
problem(P) :- problem_id(P).
magic(M) :- magic_id(M).
solution(S) :- solution_id(S).

valid(Place, Problem, Solution) :- setting(Place), problem_id(Problem), solution_id(Solution).

good_story(Place, Problem, Magic, Solution) :- valid(Place, Problem, Solution), magic_id(Magic).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in PLACES:
        lines.append(asp.fact("setting", place))
    for pid in PROBLEM_REGISTRY:
        lines.append(asp.fact("problem_id", pid))
    for mid in MAGIC_REGISTRY:
        lines.append(asp.fact("magic_id", mid))
    for sid in SOLUTION_REGISTRY:
        lines.append(asp.fact("solution_id", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world: minister, ganache, and coarse trouble.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEM_REGISTRY)
    ap.add_argument("--magic", choices=MAGIC_REGISTRY)
    ap.add_argument("--solution", choices=SOLUTION_REGISTRY)
    ap.add_argument("--treat", choices=TREAT_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(PLACES)
    problem = args.problem or rng.choice(list(PROBLEM_REGISTRY))
    magic = args.magic or rng.choice(list(MAGIC_REGISTRY))
    solution = args.solution or rng.choice(list(SOLUTION_REGISTRY))
    treat = args.treat or rng.choice(list(TREAT_REGISTRY))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    if args.problem and args.solution and args.problem == "crowd" and args.solution == "boards":
        pass
    return StoryParams(place=place, problem=problem, magic=magic, solution=solution, treat=treat, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type:8}) meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="the village square", problem="wind", magic="dust", solution="cloth", treat="cake", name="Mara", trait="steady"),
    StoryParams(place="the chapel yard", problem="rain", magic="light", solution="boards", treat="tart", name="Ansel", trait="careful"),
    StoryParams(place="the lantern road", problem="crowd", magic="bell", solution="lanterns", treat="loaf", name="Sera", trait="calm"),
]


def explain_rejection() -> str:
    return "(No story: the requested combination does not fit this folk-tale world.)"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
