#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50/dentist_problem_solving_kindness_misunderstanding_ghost_story.py
=============================================================================================================

A small ghost-story storyworld about a dentist, a misunderstanding, and a
kindly problem-solving turn.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "hurt": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "kindness": 0.0, "misunderstanding": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "dentist"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    eerie: str


@dataclass
class Problem:
    id: str
    trouble: str
    clue: str
    fix: str
    outcome: str
    ghost_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    action: str
    helps: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


SETTINGS = {
    "clinic": Place("clinic", "the quiet dentist clinic", "moonlight shone on the polished floor"),
    "house": Place("house", "the old little house by the road", "shadows leaned against the window"),
    "school": Place("school", "the school nurse room", "the hallway was still and whispery"),
}

PROBLEMS = {
    "missing_tooth": Problem(
        "missing_tooth",
        trouble="a child thought a tooth had vanished",
        clue="the tooth was tucked in a napkin",
        fix="the dentist checked the napkin and explained what happened",
        outcome="the child felt relieved",
        ghost_hint="the white napkin looked like a tiny ghost in the lamp light",
        tags={"misunderstanding", "dentist"},
    ),
    "night_noise": Problem(
        "night_noise",
        trouble="a strange tapping sounded like a ghost",
        clue="it was a loose spoon in a cup",
        fix="the dentist listened carefully and found the spoon",
        outcome="everyone laughed softly",
        ghost_hint="the spoon tapped like a tiny ghost finger",
        tags={"misunderstanding", "kindness"},
    ),
    "cold_brush": Problem(
        "cold_brush",
        trouble="a child flinched at the cold brush",
        clue="the brush just needed a warm rinse",
        fix="the dentist warmed it and spoke gently",
        outcome="the child could sit still",
        ghost_hint="the brush felt like a chilly ghost feather",
        tags={"kindness", "problem_solving"},
    ),
}

COMFORTS = {
    "lamp": Comfort("lamp", "a little lamp", "turned it on for soft light", {"dentist"}),
    "blanket": Comfort("blanket", "a warm blanket", "wrapped it around the child", {"kindness"}),
    "mirror": Comfort("mirror", "a round mirror", "held it up so the child could see", {"problem_solving"}),
}

NAMES = ["Mina", "Eli", "Nora", "Sam", "Lena", "Toby", "Iris", "Finn"]
DENTIST_NAMES = ["Dr. Hale", "Dr. Mira", "Dr. Pine"]
CHILD_TYPES = ["girl", "boy"]


def story_seed_words() -> list[str]:
    return ["dentist", "problem solving", "kindness", "misunderstanding", "ghost"]


def reasonableness_gate(problem: Problem, setting: Place) -> bool:
    return "dentist" in problem.tags and setting.id in SETTINGS


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid in SETTINGS:
        for pid, prob in PROBLEMS.items():
            if reasonableness_gate(prob, SETTINGS[sid]):
                out.append((sid, pid))
    return out


def introduce(world: World, dentist: Entity, child: Entity, problem: Problem) -> None:
    world.say(
        f"At {world.place.label}, {dentist.id} was a gentle dentist who noticed worries before they grew too big."
    )
    world.say(
        f"One evening, {child.id} came in because {problem.trouble}; {problem.ghost_hint}."
    )


def misunderstanding_beat(world: World, child: Entity, problem: Problem) -> None:
    child.memes["misunderstanding"] += 1
    child.memes["fear"] += 1
    world.say(
        f"{child.id} whispered that a ghost must be near, because the room sounded so strange."
    )
    world.say(
        f"But the noise was only a small mistake hiding in plain sight."
    )


def kind_response(world: World, dentist: Entity, child: Entity, comfort: Comfort) -> None:
    child.memes["kindness"] += 1
    world.say(
        f"{dentist.id} stayed calm and kind. {dentist.id} {comfort.action}, so {child.id} would feel safe."
    )


def solve_problem(world: World, dentist: Entity, child: Entity, problem: Problem, comfort: Comfort) -> None:
    child.memes["relief"] += 1
    child.memes["fear"] = 0.0
    world.say(
        f"Together they looked closely, and {problem.fix}."
    )
    world.say(
        f"In the soft light, the thing that seemed spooky turned out to be {problem.clue}."
    )
    world.say(
        f"After that, {problem.outcome}, and the room felt friendly again."
    )


def tell(setting: Place, problem: Problem, child_name: str, child_type: str, dentist_name: str) -> World:
    world = World(place=setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type))
    dentist = world.add(Entity(id=dentist_name, kind="character", type="dentist"))
    comfort = COMFORTS["lamp"] if setting.id != "school" else COMFORTS["mirror"]

    world.facts.update(setting=setting, problem=problem, child=child, dentist=dentist, comfort=comfort)

    introduce(world, dentist, child, problem)
    world.para()
    misunderstanding_beat(world, child, problem)
    kind_response(world, dentist, child, comfort)
    world.para()
    solve_problem(world, dentist, child, problem, comfort)
    world.say(
        f"By the end, {child.id} smiled at {dentist.id}, and the only ghost left was the one in the story."
    )
    return world


@dataclass
class StoryParams:
    setting: str
    problem: str
    child_name: str
    child_type: str
    dentist_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story dentist tale with kindness and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--dentist-name", choices=DENTIST_NAMES)
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
    combos = valid_combos()
    if args.setting and args.problem:
        if (args.setting, args.problem) not in combos:
            raise StoryError("No reasonable story matches those choices.")
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice([p for s, p in combos if s == setting])
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    child_name = args.child_name or rng.choice(NAMES)
    dentist_name = args.dentist_name or rng.choice(DENTIST_NAMES)
    return StoryParams(setting=setting, problem=problem, child_name=child_name, child_type=child_type, dentist_name=dentist_name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short ghost story for a child about a dentist who solves a scary-sounding problem kindly.",
        f"Tell a gentle story where {f['child'].id} thinks something spooky is happening at {f['setting'].label}.",
        "Make the ending reassuring, with the dentist explaining the misunderstanding and fixing the problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    dentist = f["dentist"]
    problem = f["problem"]
    return [
        QAItem(
            question=f"Why did {child.id} think there was a ghost?",
            answer=f"{child.id} thought there was a ghost because the sound in the room was strange, but it was only a misunderstanding.",
        ),
        QAItem(
            question=f"What did {dentist.id} do to help {child.id}?",
            answer=f"{dentist.id} stayed calm, was kind, and used problem solving to look closely and explain what was really happening.",
        ),
        QAItem(
            question=f"What fixed the spooky problem in the end?",
            answer=f"The real cause was found and {problem.fix}, so the scary feeling went away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a dentist do?",
            answer="A dentist helps take care of teeth and mouths, and checks for problems like pain or a tooth that needs help.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true, but they are not understanding the situation correctly.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, caring, and helpful to someone who feels worried or upset.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id} ({e.type}) meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
setting(clinic). setting(house). setting(school).
problem(missing_tooth). problem(night_noise). problem(cold_brush).

reasonably_valid(S,P) :- setting(S), problem(P), P != cold_brush.
reasonably_valid(S,P) :- setting(S), problem(P), P = cold_brush.
#show reasonably_valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonably_valid/2."))
    return sorted(set(asp.atoms(model, "reasonably_valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    if py - ac:
        print("only in python:", sorted(py - ac))
    if ac - py:
        print("only in clingo:", sorted(ac - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    world = tell(setting, problem, params.child_name, params.child_type, params.dentist_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("clinic", "missing_tooth", "Mina", "girl", "Dr. Hale"),
    StoryParams("house", "night_noise", "Eli", "boy", "Dr. Mira"),
    StoryParams("school", "cold_brush", "Nora", "girl", "Dr. Pine"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show reasonably_valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reasonably_valid/2."))
        print(sorted(set(asp.atoms(model, "reasonably_valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
