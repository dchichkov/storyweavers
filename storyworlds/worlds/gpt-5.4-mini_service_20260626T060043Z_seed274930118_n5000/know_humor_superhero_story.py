#!/usr/bin/env python3
"""
A small storyworld for a humorous superhero tale.

Premise:
A child hero tries to stop a silly city problem, learns to know the true cause,
and wins with a funny but sensible plan.

The world is intentionally small:
- one hero
- one sidekick
- one villain
- one tricky city problem
- one funny rescue
- one ending that proves the change

The script follows the Storyweavers contract:
- StoryParams and registries
- build_parser / resolve_params / generate / emit / main
- lazy ASP import for verification helpers
- world-state driven prose and Q&A
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad", "hero", "villain"}
        female = {"girl", "woman", "mother", "mom"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def display(self) -> str:
        return self.label or self.id


@dataclass
class CityProblem:
    id: str
    label: str
    verb: str
    gerund: str
    mess: str
    cause: str
    fix_hint: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    trick: str
    neutralizes: set[str]
    helps_with: set[str]


@dataclass
class StoryParams:
    problem: str
    gear: str
    hero_name: str
    sidekick_name: str
    villain_name: str
    hero_gender: str
    hero_trait: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


PROBLEMS = {
    "laughing-lamps": CityProblem(
        id="laughing-lamps",
        label="the laughing streetlamps",
        verb="fix the laughing streetlamps",
        gerund="fixing the laughing streetlamps",
        mess="giggles",
        cause="a squeaky tune in the wires",
        fix_hint="a quiet rubber cap",
        keyword="know",
        tags={"humor", "city", "lights"},
    ),
    "sticky-steps": CityProblem(
        id="sticky-steps",
        label="the sticky steps",
        verb="unstick the sticky steps",
        gerund="unsticking the sticky steps",
        mess="stuck shoes",
        cause="a spilled syrup bottle",
        fix_hint="a dusting of chalk",
        keyword="know",
        tags={"humor", "city", "stairs"},
    ),
    "bouncy-bus": CityProblem(
        id="bouncy-bus",
        label="the bouncy bus stop",
        verb="calm the bouncy bus stop",
        gerund="calming the bouncy bus stop",
        mess="bounces",
        cause="a spring under the bench",
        fix_hint="a steadying sandbag",
        keyword="know",
        tags={"humor", "city", "travel"},
    ),
}

GEAR = {
    "cap": Gear(
        id="cap",
        label="a quiet rubber cap",
        trick="cover the squeaky wire",
        neutralizes={"giggles"},
        helps_with={"laughing-lamps"},
    ),
    "chalk": Gear(
        id="chalk",
        label="a dusting of chalk",
        trick="dry the syrupy steps",
        neutralizes={"stuck shoes"},
        helps_with={"sticky-steps"},
    ),
    "sandbag": Gear(
        id="sandbag",
        label="a steadying sandbag",
        trick="hold the bench down",
        neutralizes={"bounces"},
        helps_with={"bouncy-bus"},
    ),
}

HERO_NAMES = ["Nova", "Milo", "Ada", "Zane", "Iris", "Bea", "Finn", "Luna"]
SIDEKICK_NAMES = ["Pip", "Tess", "Rex", "Dot", "Jules", "Mika"]
VILLAIN_NAMES = ["Captain Chuckle", "Dr. Snort", "The Wiggle King", "Lady Guffaw"]
TRAITS = ["brave", "curious", "cheerful", "clever", "silly", "swift"]


def reasonableness_gate(problem: CityProblem, gear: Gear) -> bool:
    return problem.id in gear.helps_with


def explain_rejection(problem: CityProblem, gear: Gear) -> str:
    return (
        f"(No story: {gear.label} does not fit {problem.label}. "
        f"The fix must match the problem, so this superhero tale would not make sense.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Humorous superhero storyworld.")
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--gear", choices=sorted(GEAR))
    ap.add_argument("--hero-name")
    ap.add_argument("--sidekick-name")
    ap.add_argument("--villain-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    problem_id = args.problem or rng.choice(sorted(PROBLEMS))
    gear_id = args.gear or rng.choice(sorted(GEAR))
    problem = PROBLEMS[problem_id]
    gear = GEAR[gear_id]

    if args.problem and args.gear and not reasonableness_gate(problem, gear):
        raise StoryError(explain_rejection(problem, gear))

    if args.problem is None or args.gear is None:
        candidates = [
            (p, g)
            for p in PROBLEMS.values()
            for g in GEAR.values()
            if reasonableness_gate(p, g)
        ]
        if args.problem:
            candidates = [(p, g) for (p, g) in candidates if p.id == problem_id]
        if args.gear:
            candidates = [(p, g) for (p, g) in candidates if g.id == gear_id]
        if not candidates:
            raise StoryError("(No valid problem/gear combination matches the given options.)")
        problem, gear = rng.choice(candidates)

    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick_name or rng.choice(SIDEKICK_NAMES)
    villain_name = args.villain_name or rng.choice(VILLAIN_NAMES)
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        problem=problem.id,
        gear=gear.id,
        hero_name=hero_name,
        sidekick_name=sidekick_name,
        villain_name=villain_name,
        hero_gender=gender,
        hero_trait=trait,
    )


def build_world(params: StoryParams) -> World:
    world = World()
    problem = PROBLEMS[params.problem]
    gear = GEAR[params.gear]

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="girl" if params.hero_gender == "girl" else "boy",
        traits=["superhero", params.hero_trait],
    ))
    sidekick = world.add(Entity(
        id=params.sidekick_name,
        kind="character",
        type="friend",
        traits=["helpful", "quick"],
    ))
    villain = world.add(Entity(
        id=params.villain_name,
        kind="character",
        type="villain",
        traits=["sneaky", "silly"],
    ))
    tool = world.add(Entity(
        id=gear.id,
        kind="thing",
        type="gear",
        label=gear.label,
        owner=hero.id,
    ))

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        villain=villain,
        problem=problem,
        gear=gear,
        tool=tool,
    )

    hero.memes["confidence"] = 1.0
    villain.memes["trouble"] = 1.0
    sidekick.memes["help"] = 1.0

    world.say(
        f"{hero.id} was a little {params.hero_trait} superhero who loved to know "
        f"how things worked in the city."
    )
    world.say(
        f"With {sidekick.id} beside {hero.pronoun('object')}, {hero.id} watched "
        f"for trouble and kept a bright red cape ready."
    )

    world.para()
    world.say(
        f"One day, {problem.label} caused a funny problem near the main square. "
        f"People had to hop, laugh, and wait."
    )
    world.say(
        f"{villain.id} grinned and said, \"I only meant to make a tiny joke!\" "
        f"But the joke had become a real mess."
    )

    world.para()
    world.say(
        f"{hero.id} wanted to {problem.verb}, but first {hero.id} tried to know "
        f"the true cause of the trouble."
    )
    world.say(
        f"{sidekick.id} found the clue: {problem.cause}. That made {hero.id} smile, "
        f"because the answer was not scary after all."
    )

    world.para()
    world.say(
        f"Then {hero.id} used {gear.label} to {gear.trick}. It worked at once."
    )
    world.say(
        f"The city stopped wobbling, {problem.mess} went away, and {villain.id} "
        f"had to admit the joke was over."
    )

    world.para()
    world.say(
        f"At the end, {hero.id}, {sidekick.id}, and even {villain.id} laughed "
        f"together. {hero.id} knew the fix, and the square looked steady and safe again."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    return [
        f"Write a short superhero story for a young child that includes the word \"know\".",
        f"Tell a humorous superhero story about {hero.id} who wants to {problem.verb} and learns the real cause first.",
        f"Write a bright, funny story where a superhero uses a small tool to solve {problem.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    villain = f["villain"]
    problem = f["problem"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who is the superhero in the story?",
            answer=f"The superhero is {hero.id}, who is {hero.pronoun('subject')} and brave.",
        ),
        QAItem(
            question=f"What problem did {hero.id} want to fix?",
            answer=f"{hero.id} wanted to {problem.verb}, because {problem.label} was causing trouble in the city.",
        ),
        QAItem(
            question=f"How did {hero.id} know what was really causing the trouble?",
            answer=(
                f"{sidekick.id} found the clue: {problem.cause}. "
                f"That helped {hero.id} know the real cause before fixing it."
            ),
        ),
        QAItem(
            question=f"What helped {hero.id} solve the problem at the end?",
            answer=f"{gear.label} helped {hero.id} {gear.trick}, so the city became steady again.",
        ),
        QAItem(
            question=f"Who was the silly villain?",
            answer=f"The silly villain was {villain.id}, who made a joke that turned into a mess.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    gear = f["gear"]
    problem = f["problem"]
    return [
        QAItem(
            question="What does a superhero do?",
            answer="A superhero helps people, stops trouble, and tries to make the city safe again.",
        ),
        QAItem(
            question="What does it mean to know something?",
            answer="To know something means to understand it or be sure about it.",
        ),
        QAItem(
            question="Why can jokes be funny but still cause problems?",
            answer="A joke can be funny, but if it changes the world in the wrong way, people may need help to fix it.",
        ),
        QAItem(
            question=f"What is {gear.label} for in this story?",
            answer=f"{gear.label} is the special tool that helps with {problem.label}.",
        ),
    ]


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
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
problem(problem_id).
gear(gear_id).

compatible(P, G) :- problem(P), gear(G), helps(G, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for tag in sorted(p.tags):
            lines.append(asp.fact("tag", pid, tag))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for prob in sorted(g.helps_with):
            lines.append(asp.fact("helps", gid, prob))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = {(p.id, g.id) for p in PROBLEMS.values() for g in GEAR.values() if reasonableness_gate(p, g)}
    clingo_set = set(asp_valid_combos())
    if py == clingo_set:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("python-only:", sorted(py - clingo_set))
    print("clingo-only:", sorted(clingo_set - py))
    return 1


CURATED = [
    StoryParams(
        problem="laughing-lamps",
        gear="cap",
        hero_name="Nova",
        sidekick_name="Pip",
        villain_name="Captain Chuckle",
        hero_gender="girl",
        hero_trait="clever",
    ),
    StoryParams(
        problem="sticky-steps",
        gear="chalk",
        hero_name="Milo",
        sidekick_name="Dot",
        villain_name="Dr. Snort",
        hero_gender="boy",
        hero_trait="brave",
    ),
    StoryParams(
        problem="bouncy-bus",
        gear="sandbag",
        hero_name="Iris",
        sidekick_name="Tess",
        villain_name="The Wiggle King",
        hero_gender="girl",
        hero_trait="cheerful",
    ),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible problem/gear combos:")
        for p, g in combos:
            print(f"  {p:16} -> {g}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples: list[StorySample] = []
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
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.problem} with {p.gear}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
