#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/kangaroo_tat_sensible_subway_station_problem_solving.py
===============================================================================================================================

A small folk-tale-style story world set in a subway station.

Seed tale sketch:
---
A sensible kangaroo waits in a subway station with a tat of an old paper map.
The map is hard to read, and the last train is near. The kangaroo remembers a
flashback from an elder who taught that when a path is unclear, one should stop,
think, and ask for the kindest sign. The kangaroo listens to an inner monologue,
follows the station symbols, and solves the problem by finding the right platform
before the train leaves.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "kangaroo":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str = "the subway station"
    affords: set[str] = field(default_factory=lambda: {"find_platform", "ask_for_help"})


@dataclass
class Problem:
    id: str
    title: str
    trouble: str
    clue: str
    resolution: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    method: str
    effect: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    seed: Optional[int] = None


STATION = Place()

PROBLEMS = {
    "tat_map": Problem(
        id="tat_map",
        title="a tat of a torn paper map",
        trouble="the little tat of paper had torn along the fold",
        clue="the platform number was still visible on one corner",
        resolution="the kangaroo followed the signs and asked the conductor",
        keyword="tat",
        tags={"tat", "map", "problem_solving", "flashback", "inner_monologue"},
    ),
}

AIDS = {
    "signs": Aid(
        id="signs",
        label="station signs",
        method="reading the arrows and platform numbers",
        effect="the path became clear",
        tags={"subway_station"},
    ),
    "conductor": Aid(
        id="conductor",
        label="the conductor",
        method="asking a kind question",
        effect="the right platform was named aloud",
        tags={"subway_station"},
    ),
}

KANGAROO_NAMES = ["Milo", "Pip", "Nori", "Kara", "Toby", "Luna"]
TRAITS = ["sensible", "patient", "careful", "quiet", "steady"]


class TaleWorld(World):
    pass


def build_story_world(params: StoryParams) -> TaleWorld:
    world = TaleWorld(STATION)
    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type="kangaroo",
            label=params.name,
            traits=["sensible", "curious"],
            meters={"worry": 0.0, "hope": 0.0, "distance": 0.0},
            memes={"calm": 1.0, "confidence": 0.0},
        )
    )
    map_piece = world.add(
        Entity(
            id="tat",
            kind="thing",
            type="paper",
            label="tat of paper map",
            phrase="a tat of a torn paper map",
            owner=hero.id,
            caretaker=hero.id,
            region="pouch",
            meters={"torn": 1.0},
            memes={"importance": 1.0},
        )
    )
    world.facts["hero"] = hero
    world.facts["tat"] = map_piece
    world.facts["problem"] = PROBLEMS[params.problem]
    world.facts["aids"] = [AIDS["signs"], AIDS["conductor"]]
    return world


def inner_monologue(world: TaleWorld, hero: Entity, problem: Problem) -> None:
    hero.memes["confidence"] += 0.5
    hero.meters["worry"] += 1.0
    world.say(
        f'{hero.id} looked down at the {problem.keyword} and thought, '
        f'"If I hurry too much, I may only make the trouble bigger. '
        f"I should be sensible and look twice."'
    )


def flashback(world: TaleWorld, hero: Entity) -> None:
    hero.meters["distance"] += 0.0
    world.say(
        f"Then {hero.id} remembered a flashback from an old jackaroo by the station stairs: "
        f'"When a path looks bent, stop, breathe, and let the signs speak first."'
    )


def problem_state(world: TaleWorld, hero: Entity, problem: Problem) -> None:
    world.say(
        f"At the subway station, {hero.id} found the {problem.title}. "
        f"{problem.trouble.capitalize()}, and the last train would not wait forever."
    )


def search_and_reason(world: TaleWorld, hero: Entity, problem: Problem) -> None:
    world.say(
        f'{hero.id} listened to {hero.pronoun("possessive")} inner monologue and nodded. '
        f'"The corner still shows the platform number," {hero.pronoun()} told {hero.pronoun("object")}self. '
        f'"So I do not need to know everything. I only need the next sensible step."'
    )
    hero.memes["confidence"] += 1.0
    hero.meters["worry"] -= 0.5


def solve_problem(world: TaleWorld, hero: Entity, problem: Problem, aid_signs: Aid, aid_conductor: Aid) -> None:
    world.say(
        f"{hero.id} followed the station signs, and then asked {aid_conductor.label} for help. "
        f"{aid_signs.method.capitalize()}, and {aid_conductor.effect}."
    )
    hero.meters["distance"] += 1.0
    hero.memes["hope"] += 1.0
    world.facts["solved"] = True
    world.facts["resolution"] = problem.resolution


def ending(world: TaleWorld, hero: Entity, problem: Problem) -> None:
    hero.memes["calm"] += 1.0
    world.say(
        f"In the end, {hero.id} reached the right platform with the tat of paper map tucked safe in {hero.pronoun('possessive')} pouch. "
        f"The train came at last, and the station felt kind and bright."
    )


def tell(params: StoryParams) -> TaleWorld:
    world = build_story_world(params)
    hero = world.facts["hero"]
    problem = world.facts["problem"]
    aid_signs = world.facts["aids"][0]
    aid_conductor = world.facts["aids"][1]

    problem_state(world, hero, problem)
    world.para()
    inner_monologue(world, hero, problem)
    flashback(world, hero)
    world.para()
    search_and_reason(world, hero, problem)
    solve_problem(world, hero, problem, aid_signs, aid_conductor)
    ending(world, hero, problem)
    return world


SETTINGS = {"subway_station": STATION}
PROBLEM_REGISTRY = PROBLEMS
AID_REGISTRY = AIDS


def valid_combos() -> list[tuple[str, str]]:
    return [("subway_station", "tat_map")]


def generation_prompts(world: TaleWorld) -> list[str]:
    hero = world.facts["hero"]
    prob = world.facts["problem"]
    return [
        'Write a short folk tale set in a subway station about a kangaroo and a tat of paper.',
        f"Tell a story where {hero.id}, a sensible kangaroo, faces {prob.title} and solves it calmly.",
        'Write a child-friendly story with problem solving, inner monologue, and a flashback at a subway station.',
    ]


def story_qa(world: TaleWorld) -> list[QAItem]:
    hero = world.facts["hero"]
    prob = world.facts["problem"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a sensible kangaroo at the subway station.",
        ),
        QAItem(
            question=f"What was the problem with the tat?",
            answer=f"The problem was that {prob.trouble}, so the map was hard to use.",
        ),
        QAItem(
            question="How did the kangaroo solve the problem?",
            answer="He stopped to think, remembered the old advice from a flashback, read the signs, and asked the conductor for help.",
        ),
        QAItem(
            question="What did the kangaroo say to himself in his inner monologue?",
            answer='He said he should not hurry blindly and that the next sensible step was to look for the platform number.',
        ),
    ]


def world_knowledge_qa(world: TaleWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a subway station?",
            answer="A subway station is a place where people wait for trains that travel underground.",
        ),
        QAItem(
            question="What does sensible mean?",
            answer="Sensible means thinking carefully and choosing a good, safe way to act.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a memory from earlier that the story shows again for a moment.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: TaleWorld) -> str:
    parts = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        parts.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(parts)


ASP_RULES = r"""
problem_valid(P) :- problem(P).
story_valid(Place, Problem) :- place(Place), problem(Problem), place_name(Place,"subway station"),
                               problem_keyword(Problem,"tat"), problem_tags(Problem,"problem_solving").
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "subway_station"), asp.fact("place_name", "subway_station", "subway station")]
    for pid, p in PROBLEM_REGISTRY.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_keyword", pid, p.keyword))
        for tag in sorted(p.tags):
            lines.append(asp.fact("problem_tags", pid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_valid/2."))
    return sorted(set(asp.atoms(model, "story_valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


CURATED = [StoryParams(place="subway_station", problem="tat_map", name="Milo")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world in a subway station.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--problem", choices=PROBLEM_REGISTRY.keys())
    ap.add_argument("--name")
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
    if args.place and args.place != "subway_station":
        raise StoryError("This world only takes place in a subway station.")
    if args.problem and args.problem not in PROBLEM_REGISTRY:
        raise StoryError("Unknown problem.")
    name = args.name or rng.choice(KANGAROO_NAMES)
    problem = args.problem or "tat_map"
    return StoryParams(place="subway_station", problem=problem, name=name)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 10):
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

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
