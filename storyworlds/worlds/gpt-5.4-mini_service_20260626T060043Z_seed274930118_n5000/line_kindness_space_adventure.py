#!/usr/bin/env python3
"""
storyworlds/worlds/line_kindness_space_adventure.py
====================================================

A small story world about a space adventure where kindness helps a crew solve
a problem involving a line.

Seed tale, imagined from the prompt:
---
On a tiny starship, Mina loved the bright light line that guided the crew
through the dark corridor. One day the line flickered, and the ship's little
robot became worried because the next room was full of floating parts. Mina
wanted to rush ahead, but the captain asked her to slow down and help.

Mina listened. She found the broken wire, shared tools, and spoke kindly to the
robot. Together they fixed the line, and the path across the ship glowed again.
The crew followed the shining line safely, and Mina smiled because being kind
had saved the day.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    dark: bool = False
    zero_g: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: str
    keyword: str = "line"
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    covers: set[str]
    helps: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.problem_zone: str = ""

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
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.problem_zone = self.problem_zone
        clone.paragraphs = [[]]
        return clone


PROBLEMS = {
    "tangled_line": Problem(
        id="tangled_line",
        verb="follow the glowing line",
        gerund="following the glowing line",
        rush="dash down the corridor",
        mess="tangled",
        zone="corridor",
        keyword="line",
        tags={"line", "space", "guide"},
    ),
    "dim_line": Problem(
        id="dim_line",
        verb="guide the ship with the light line",
        gerund="guiding with the light line",
        rush="run to the control panel",
        mess="dim",
        zone="bridge",
        keyword="line",
        tags={"line", "light", "ship"},
    ),
    "broken_line": Problem(
        id="broken_line",
        verb="fix the broken line",
        gerund="fixing the broken line",
        rush="grab the toolkit",
        mess="broken",
        zone="engine_room",
        keyword="line",
        tags={"line", "repair", "tool"},
    ),
}

FIXES = [
    Fix(
        id="gloves",
        label="soft repair gloves",
        covers={"hands"},
        helps={"broken"},
        prep="put on soft repair gloves first",
        tail="put on the soft repair gloves",
    ),
    Fix(
        id="lamp",
        label="a bright lamp",
        covers={"corridor", "bridge"},
        helps={"dim"},
        prep="carry a bright lamp",
        tail="carried the bright lamp",
    ),
    Fix(
        id="spool",
        label="a spare tether spool",
        covers={"corridor", "engine_room"},
        helps={"tangled", "broken"},
        prep="bring a spare tether spool",
        tail="brought the spare tether spool",
    ),
]

SETTINGS = {
    "corridor": Place(name="the silver corridor", dark=True, zero_g=True, affords={"tangled_line"}),
    "bridge": Place(name="the bridge", dark=True, zero_g=True, affords={"dim_line"}),
    "engine_room": Place(name="the engine room", dark=False, zero_g=True, affords={"broken_line"}),
}

HERO_NAMES = ["Mina", "Tari", "Niko", "Luna", "Pax", "Arin"]
CREW_NAMES = ["Captain Sol", "Robo-7", "Pilot Joss", "Engineer Vera"]
TRAITS = ["brave", "curious", "gentle", "quick", "helpful"]


@dataclass
class StoryParams:
    place: str
    problem: str
    hero: str
    crew: str
    trait: str
    seed: Optional[int] = None


def problem_needs_fix(problem: Problem) -> bool:
    return bool(problem.keyword == "line")


def select_fix(problem: Problem) -> Optional[Fix]:
    for fx in FIXES:
        if problem.mess in fx.helps:
            return fx
    return None


def predict(world: World, hero: Entity, problem: Problem) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(hero.id), problem, narrate=False)
    line_ok = sim.facts.get("line_fixed", False)
    return {"fixed": line_ok, "kindness": sim.facts.get("kindness", 0)}


def _do_action(world: World, hero: Entity, problem: Problem, narrate: bool = True) -> None:
    hero.meters[problem.mess] = hero.meters.get(problem.mess, 0.0) + 1
    hero.memes["need"] = hero.memes.get("need", 0.0) + 1
    if narrate:
        world.say(f"{hero.id} wanted to {problem.verb}, but the line was not ready yet.")


def set_problem_zone(world: World, problem: Problem) -> None:
    world.problem_zone = problem.zone


def introduce(world: World, hero: Entity, crew: Entity) -> None:
    world.say(f"{hero.id} was a {hero.memes.get('trait_word', 'little')} space explorer who liked to look for safe paths.")
    world.say(f"{hero.pronoun().capitalize()} traveled with {crew.label} on a small starship full of blinking panels.")


def setup(world: World, hero: Entity, crew: Entity, problem: Problem) -> None:
    hero.memes["kindness"] = 0.0
    hero.memes["joy"] = 0.0
    world.say(
        f"One night, the crew saw a {problem.keyword} that ran through {world.place.name} "
        f"like a tiny silver path."
    )
    world.say(f"It helped everyone move safely, but now it had trouble {problem.gerund}.")


def worry(world: World, crew: Entity, problem: Problem) -> None:
    crew.memes["worry"] = crew.memes.get("worry", 0.0) + 1
    world.say(f"{crew.label} frowned because the ship needed the line to work before the next turn through space.")


def ask_kindly(world: World, hero: Entity, crew: Entity, problem: Problem) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    world.facts["kindness"] = hero.memes["kindness"]
    world.say(
        f"{hero.id} took a slow breath and said, "
        f'"Don\'t worry. I can help, and we can do it together."'
    )
    world.say(f"That kind voice made {crew.label} relax and point toward the broken spot.")


def offer_fix(world: World, hero: Entity, problem: Problem) -> Optional[Fix]:
    fx = select_fix(problem)
    if fx is None:
        return None
    if fx.id == "lamp":
        world.say(f"{hero.id} held up {fx.label} so the whole path glowed.")
    elif fx.id == "gloves":
        world.say(f"{hero.id} used {fx.label} to safely touch the damaged strands.")
    else:
        world.say(f"{hero.id} fetched {fx.label}, because a line in space needs the right tool.")
    return fx


def resolve(world: World, hero: Entity, crew: Entity, problem: Problem, fx: Fix) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    crew.memes["worry"] = 0.0
    world.facts["line_fixed"] = True
    world.say(
        f"Together they {fx.tail} and mended the {problem.keyword}. "
        f"At once, the path shone clear again."
    )
    world.say(
        f"{hero.id} smiled as the crew followed the bright line through {world.place.name}, "
        f"and the little starship drifted on with a calm, kind glow."
    )


def tell(place: Place, problem: Problem, hero_name: str, crew_name: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl"))
    crew = world.add(Entity(id=crew_name, kind="character", type="captain", label=crew_name))
    hero.memes["trait_word"] = trait

    set_problem_zone(world, problem)
    introduce(world, hero, crew)
    world.para()
    setup(world, hero, crew, problem)
    worry(world, crew, problem)
    ask_kindly(world, hero, crew, problem)
    world.para()
    fx = offer_fix(world, hero, problem)
    if fx is None:
        raise StoryError("No kind fix exists for this space-line problem.")
    resolve(world, hero, crew, problem, fx)

    world.facts.update(hero=hero, crew=crew, problem=problem, fix=fx, place=place)
    return world


def build_story(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PROBLEMS[params.problem], params.hero, params.crew, params.trait)
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
    problem = f["problem"]
    return [
        f'Write a short space adventure story for a young child that includes the word "{problem.keyword}".',
        f"Tell a gentle story where {hero.id} helps a crew member with a {problem.keyword} using kindness.",
        f"Write a simple story about a starship problem, a kind helper, and a bright ending with a line."
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    crew = f["crew"]
    problem = f["problem"]
    fx = f["fix"]
    return [
        QAItem(
            question=f"What did {hero.id} help fix in the story?",
            answer=f"{hero.id} helped fix the {problem.keyword}. It had trouble {problem.gerund}, so the crew needed help."
        ),
        QAItem(
            question=f"How did {hero.id} act when {crew.label} worried?",
            answer=f"{hero.id} acted kindly. {hero.id} spoke softly, offered help, and showed the crew a safer way to solve the problem."
        ),
        QAItem(
            question=f"What tool or item helped them finish the job?",
            answer=f"{fx.label} helped them finish the job, because it was the right thing for this kind of space problem."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a line used for on a starship?",
            answer="A line can mark a safe path, hold things together, or guide people through a dark place in space."
        ),
        QAItem(
            question="Why is kindness useful on a spaceship?",
            answer="Kindness helps the crew stay calm, listen to one another, and solve problems together."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {' '.join(bits) if bits else 'quiet'}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if place.dark:
            lines.append(asp.fact("dark", pid))
        if place.zero_g:
            lines.append(asp.fact("zero_g", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("mess", pid, p.mess))
        lines.append(asp.fact("zone", pid, p.zone))
        lines.append(asp.fact("keyword", pid, p.keyword))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for c in sorted(fx.covers):
            lines.append(asp.fact("covers", fx.id, c))
        for h in sorted(fx.helps):
            lines.append(asp.fact("helps", fx.id, h))
    return "\n".join(lines)


ASP_RULES = r"""
reachable(P) :- place(P).
needs_kindness(Problem) :- problem(Problem), keyword(Problem, line).
good_fix(Problem, Fix) :- problem(Problem), fix(Fix), mess(Problem, M), helps(Fix, M).
can_resolve(Problem) :- good_fix(Problem, _).
valid_story(Place, Problem) :- affords(Place, Problem), can_resolve(Problem), place(Place).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, p in SETTINGS.items():
        for prob in p.affords:
            if select_fix(PROBLEMS[prob]) is not None:
                combos.append((place, prob))
    return sorted(combos)


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo matches python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with kindness and a guiding line.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--crew", choices=CREW_NAMES)
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
    combos = valid_combos()
    if args.place or args.problem:
        combos = [
            (pl, pr) for pl, pr in combos
            if (args.place is None or pl == args.place)
            and (args.problem is None or pr == args.problem)
        ]
    if not combos:
        raise StoryError("No valid space-line story matches those options.")
    place, problem = rng.choice(combos)
    hero = args.name or rng.choice(HERO_NAMES)
    crew = args.crew or rng.choice(CREW_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, hero=hero, crew=crew, trait=trait)


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="corridor", problem="tangled_line", hero="Mina", crew="Captain Sol", trait="gentle"),
    StoryParams(place="bridge", problem="dim_line", hero="Luna", crew="Pilot Joss", trait="curious"),
    StoryParams(place="engine_room", problem="broken_line", hero="Niko", crew="Engineer Vera", trait="helpful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
