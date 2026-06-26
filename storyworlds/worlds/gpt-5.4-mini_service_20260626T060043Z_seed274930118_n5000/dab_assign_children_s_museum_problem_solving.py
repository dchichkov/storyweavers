#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/dab_assign_children_s_museum_problem_solving.py
============================================================================================================================

A small story world for a gentle children's-museum ghost story about a problem
that gets solved by careful noticing, assigning jobs, and a brave dab with the
right cloth.

Premise:
- A child hears a soft "tap-tap" in a children's museum after the lights dim.
- A little ghost has made a mess near an exhibit and needs help.
- The child and a museum guide must assign simple jobs to solve the problem.
- The ending shows the museum calm again, with the ghost happier and the room
  clean.

The story engine models:
- physical meters: mess, tidy, shine, damp, sticker, soot
- emotional memes: fear, curiosity, calm, trust, pride, relief

The prose is intentionally close to a ghost story, but stays child-facing and
warm: strange shadows, whispery clues, a helpful ghost, and a tidy ending.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    assigned_job: str = ""

    def __post_init__(self) -> None:
        for key in ["mess", "tidy", "shine", "damp", "sticker", "soot"]:
            self.meters.setdefault(key, 0.0)
        for key in ["fear", "curiosity", "calm", "trust", "pride", "relief"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "child", "kid"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Location:
    name: str
    theme: str
    supports: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    title: str
    clue: str
    mess_kind: str
    fix_kind: str
    needs: set[str]
    assignable_jobs: list[str]
    solve_steps: list[str]
    ghost_mood: str


@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


@dataclass
class World:
    location: Location
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    current_problem: Optional[Problem] = None

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
        clone = World(self.location)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.current_problem = self.current_problem
        return clone


def render_name(entity: Entity) -> str:
    return entity.label or entity.id


def problem_by_id(pid: str) -> Problem:
    return PROBLEMS[pid]


def location_by_id(lid: str) -> Location:
    return LOCATIONS[lid]


LOCATIONS = {
    "story_lab": Location(
        name="the children's museum story lab",
        theme="shadows, tiny stage lights, and paper puppets",
        supports={"stain", "shadow", "lost_item"},
    ),
    "dinosaur_room": Location(
        name="the children's museum dinosaur room",
        theme="big bones, echoing footsteps, and a sleeping cave wall",
        supports={"stain", "echo"},
    ),
    "water_room": Location(
        name="the children's museum water room",
        theme="glassy tables, splashy games, and shiny tiles",
        supports={"spill", "stain"},
    ),
}

PROBLEMS = {
    "shadow_spill": Problem(
        id="shadow_spill",
        title="a spill that looked like a shadow",
        clue="a dark puddle under the moon paper",
        mess_kind="stain",
        fix_kind="dab",
        needs={"cloth", "spotlight", "assign"},
        assignable_jobs=["hold_light", "fetch_cloth", "watch_floor"],
        solve_steps=[
            "notice the spill",
            "assign jobs",
            "dab the stain",
            "dry the floor",
        ],
        ghost_mood="worried",
    ),
    "sticky_stars": Problem(
        id="sticky_stars",
        title="sticky star stickers on the floor",
        clue="little stars stuck in a glitter trail",
        mess_kind="sticker",
        fix_kind="peel",
        needs={"patience", "basket", "assign"},
        assignable_jobs=["count_stars", "lift_edge", "carry_basket"],
        solve_steps=[
            "notice the trail",
            "assign jobs",
            "peel each sticker",
            "set the floor straight",
        ],
        ghost_mood="embarrassed",
    ),
    "soot_smudge": Problem(
        id="soot_smudge",
        title="a soot smudge by the puppet stage",
        clue="a gray blur on the curtain",
        mess_kind="soot",
        fix_kind="dab",
        needs={"cloth", "water", "assign"},
        assignable_jobs=["bring_water", "hold_cloth", "mind_stage"],
        solve_steps=[
            "notice the smudge",
            "assign jobs",
            "dab the soot",
            "make the curtain bright",
        ],
        ghost_mood="shy",
    ),
}

GIRL_NAMES = ["Maya", "Nina", "Lila", "Tess", "Ivy", "June", "Ada"]
BOY_NAMES = ["Finn", "Theo", "Leo", "Owen", "Noah", "Milo", "Eli"]
TRAITS = ["curious", "brave", "quiet", "careful", "gentle", "thoughtful"]
GUIDES = ["museum guide", "kind helper", "night guide", "gallery helper"]


def introduce(world: World, child: Entity) -> None:
    world.say(
        f"{child.label} was a little {child.type} with a {next((t for t in child.memes if False), '')}"
    )


def _make_intro(world: World, child: Entity, guide: Entity, problem: Problem) -> None:
    world.say(
        f"{child.label} loved the children's museum, especially when the rooms got quiet "
        f"and every shadow seemed to listen."
    )
    world.say(
        f"On this evening, {child.pronoun('possessive')} {guide.label} had a soft voice and a flashlight, "
        f"because they were closing up the {world.location.name}."
    )
    world.say(
        f"Then they saw {problem.clue}. It looked almost like a ghost had tapped a dark finger on the floor."
    )
    child.memes["curiosity"] += 1
    child.memes["fear"] += 1
    guide.memes["calm"] += 1


def _predict_problem(world: World, child: Entity, problem: Problem) -> bool:
    sim = world.copy()
    target = sim.facts["stain_target"]
    target.meters[problem.mess_kind] += 1
    return target.meters[problem.mess_kind] >= THRESHOLD


def _assign_jobs(world: World, child: Entity, guide: Entity, ghost: Entity, problem: Problem) -> None:
    world.say(
        f'{guide.label} whispered, "No need to run. Let us assign jobs and solve this together."'
    )
    child.assigned_job = problem.assignable_jobs[0]
    guide.assigned_job = problem.assignable_jobs[1]
    ghost.assigned_job = problem.assignable_jobs[2] if len(problem.assignable_jobs) > 2 else "wait"
    world.say(
        f"{child.label} would {child.assigned_job.replace('_', ' ')}, {guide.label} would {guide.assigned_job.replace('_', ' ')}, "
        f"and the ghost would {ghost.assigned_job.replace('_', ' ')}."
    )
    child.memes["trust"] += 1
    guide.memes["pride"] += 1
    ghost.memes["relief"] += 1


def _dab_fix(world: World, child: Entity, guide: Entity, ghost: Entity, problem: Problem) -> None:
    target = world.facts["stain_target"]
    if problem.fix_kind != "dab":
        return
    target.meters[problem.mess_kind] = max(0.0, target.meters[problem.mess_kind] - 1)
    target.meters["tidy"] += 1
    world.say(
        f"{child.label} took the soft cloth and dabbed the mark. Not rubbed it, just dabbed it, "
        f"like patting a sleepy kitten."
    )
    world.say(
        f"The dark patch faded little by little, and the floor stopped looking haunted."
    )


def _peel_fix(world: World, child: Entity, guide: Entity, ghost: Entity, problem: Problem) -> None:
    target = world.facts["stain_target"]
    if problem.fix_kind != "peel":
        return
    target.meters[problem.mess_kind] = 0.0
    target.meters["tidy"] += 1
    world.say(
        f"{child.label} lifted one sticker edge at a time, and the glitter trail came free with a tiny whisper."
    )


def _shine_fix(world: World, child: Entity, guide: Entity, ghost: Entity, problem: Problem) -> None:
    target = world.facts["stain_target"]
    target.meters["shine"] += 1
    target.meters["tidy"] += 1
    world.say(
        f"{guide.label} held the light low while {child.label} worked, and the curtain brightened again."
    )


def _resolution(world: World, child: Entity, guide: Entity, ghost: Entity, problem: Problem) -> None:
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    ghost.memes["calm"] += 1
    ghost.memes["relief"] += 1
    world.say(
        f"When the room was clean, the ghost floated up with a shy smile. "
        f'"Thank you," it breathed, as if the museum air itself were saying it.'
    )
    world.say(
        f"{child.label} looked back at the tidy floor and felt proud, because the problem was solved without a fuss."
    )


def tell(world: World, child: Entity, guide: Entity, ghost: Entity, problem: Problem) -> World:
    world.current_problem = problem
    world.facts["child"] = child
    world.facts["guide"] = guide
    world.facts["ghost"] = ghost
    world.facts["problem"] = problem
    _make_intro(world, child, guide, problem)
    world.para()
    world.say(
        f"{child.label} leaned closer and saw that the dark shape was not danger at all. "
        f"It was a spill left by a bumped ink cup near the moon exhibit."
    )
    _assign_jobs(world, child, guide, ghost, problem)
    world.para()
    if problem.fix_kind == "dab":
        _dab_fix(world, child, guide, ghost, problem)
    elif problem.fix_kind == "peel":
        _peel_fix(world, child, guide, ghost, problem)
    else:
        _shine_fix(world, child, guide, ghost, problem)
    _resolution(world, child, guide, ghost, problem)
    return world


def valid_story_combos() -> list[tuple[str, str]]:
    combos = []
    for place in LOCATIONS:
        for prob in PROBLEMS:
            combos.append((place, prob))
    return combos


def generation_prompts(world: World) -> list[str]:
    p = world.facts["problem"]
    child = world.facts["child"]
    guide = world.facts["guide"]
    return [
        f"Write a gentle ghost story set in {world.location.name} where {child.label} and {guide.label} solve {p.title}.",
        f"Tell a children's museum story about a quiet problem, a careful assignment of jobs, and a small helpful ghost.",
        f"Write a short story that uses the words 'dab' and 'assign' and ends with a clean museum room.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    guide = world.facts["guide"]
    ghost = world.facts["ghost"]
    problem = world.facts["problem"]
    target = world.facts["stain_target"]
    return [
        QAItem(
            question=f"What problem did {child.label} notice in the museum?",
            answer=f"{child.label} noticed {problem.clue}, which turned out to be {problem.title}.",
        ),
        QAItem(
            question=f"What did {guide.label} ask everyone to do to solve the problem?",
            answer=f"{guide.label} asked them to assign jobs so each helper had a clear task.",
        ),
        QAItem(
            question=f"What did {child.label} do to fix the mess?",
            answer=f"{child.label} used a soft cloth to dab the mark until the floor was tidy.",
        ),
        QAItem(
            question=f"How did the ghost feel when the problem was solved?",
            answer=f"The ghost started out {problem.ghost_mood} and ended up relieved and calm.",
        ),
        QAItem(
            question=f"What changed in the museum at the end?",
            answer=f"The stain was gone, the room looked bright again, and the museum felt peaceful.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "dab": [
        QAItem(
            question="What does it mean to dab something clean?",
            answer="To dab means to press gently with a cloth or tissue, usually to soak up a spill without rubbing it around.",
        )
    ],
    "assign": [
        QAItem(
            question="What does it mean to assign a job?",
            answer="To assign a job means to give each person a task so everyone knows what to do.",
        )
    ],
    "museum": [
        QAItem(
            question="What is a museum?",
            answer="A museum is a place where people can see interesting things, learn new facts, and look carefully at displays.",
        )
    ],
    "ghost": [
        QAItem(
            question="Are all ghosts scary in stories?",
            answer="No. In many children's stories, a ghost can be shy, lonely, or helpful instead of scary.",
        )
    ],
    "children's museum": [
        QAItem(
            question="What is special about a children's museum?",
            answer="A children's museum is made for kids to explore, play, and learn with their hands and eyes.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["problem"].solve_steps)
    tags.add("museum")
    tags.add("ghost")
    tags.add("children's museum")
    tags.add("dab")
    tags.add("assign")
    out: list[QAItem] = []
    for key in ["dab", "assign", "museum", "ghost", "children's museum"]:
        out.extend(WORLD_KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(
            f"{ent.id}: type={ent.type} label={ent.label!r} meters={meters} memes={memes} assigned={ent.assigned_job!r}"
        )
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lid, loc in LOCATIONS.items():
        lines.append(asp.fact("location", lid))
        for s in sorted(loc.supports):
            lines.append(asp.fact("supports", lid, s))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("mess_kind", pid, p.mess_kind))
        lines.append(asp.fact("fix_kind", pid, p.fix_kind))
        for need in sorted(p.needs):
            lines.append(asp.fact("needs", pid, need))
        for job in p.assignable_jobs:
            lines.append(asp.fact("assignable_job", pid, job))
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(L,P) :- location(L), problem(P).
has_assign(P) :- needs(P, assign).
good_problem(P) :- problem(P), has_assign(P).
shown_valid(L,P) :- valid_combo(L,P), good_problem(P).
#show shown_valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show shown_valid/2."))
    return sorted(set(asp.atoms(model, "shown_valid")))


def asp_verify() -> int:
    python_set = set((l, p) for l, p in valid_story_combos() if PROBLEMS[p].id in PROBLEMS)
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Children's museum ghost story with problem solving.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--guide", choices=GUIDES)
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
    place = args.place or rng.choice(list(LOCATIONS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = args.guide or rng.choice(GUIDES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, name=name, gender=gender, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    loc = location_by_id(params.place)
    prob = problem_by_id(params.problem)
    world = World(loc)
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    guide = world.add(Entity(id="guide", kind="character", type="adult", label=params.guide))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the little ghost"))
    target = world.add(Entity(id="target", kind="thing", type="floor", label="the floor"))
    world.facts["stain_target"] = target
    world.facts["child"] = child
    world.facts["guide"] = guide
    world.facts["ghost"] = ghost
    world.facts["problem"] = prob
    world.facts["location"] = loc
    world.facts["trait"] = params.trait
    world = tell(world, child, guide, ghost, prob)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="story_lab", problem="shadow_spill", name="Maya", gender="girl", guide="night guide", trait="careful"),
    StoryParams(place="dinosaur_room", problem="soot_smudge", name="Finn", gender="boy", guide="museum guide", trait="curious"),
    StoryParams(place="water_room", problem="sticky_stars", name="Ivy", gender="girl", guide="kind helper", trait="thoughtful"),
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
        print(asp_program("#show shown_valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for item in combos:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(100, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
