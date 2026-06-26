#!/usr/bin/env python3
"""
storyworlds/worlds/transit_problem_solving_teamwork_space_adventure.py
======================================================================

A small, standalone story world about a transit run through space:
a crew tries to reach a destination, faces a problem in the middle,
and solves it together with teamwork.

The premise is inspired by a child-friendly space adventure:
a ship is on transit between stops, a route problem appears, and the crew
uses tools, calm thinking, and cooperation to get moving again.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "captain"}
        male = {"boy", "man", "pilot", "engineer"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class TransitRoute:
    start: str
    end: str
    vessel: str
    transit_kind: str
    speed: str
    hazard: str
    route_problem: str
    fix_tool: str
    teamwork_role: str
    route_tag: str


@dataclass
class CrewRole:
    id: str
    label: str
    type: str
    traits: list[str]


class World:
    def __init__(self, route: TransitRoute) -> None:
        self.route = route
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.route)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


ROUTES = {
    "orbital_line": TransitRoute(
        start="orbital station",
        end="moon dock",
        vessel="the transit shuttle",
        transit_kind="space transit",
        speed="smooth",
        hazard="a drifting cargo ring",
        route_problem="the map display froze",
        fix_tool="a spare cable",
        teamwork_role="navigator",
        route_tag="transit",
    ),
    "asteroid_link": TransitRoute(
        start="asteroid stop",
        end="research dome",
        vessel="the transit pod",
        transit_kind="moon transit",
        speed="careful",
        hazard="a pebble cloud",
        route_problem="the steering latch stuck",
        fix_tool="a small wrench",
        teamwork_role="pilot",
        route_tag="transit",
    ),
    "solar_run": TransitRoute(
        start="sunport",
        end="harbor ring",
        vessel="the bright commuter craft",
        transit_kind="space transit",
        speed="swift",
        hazard="a spark storm",
        route_problem="the power dial blinked out",
        fix_tool="a backup battery",
        teamwork_role="engineer",
        route_tag="transit",
    ),
}

CREW = {
    "captain": CrewRole("captain", "captain", "captain", ["calm", "brave"]),
    "pilot": CrewRole("pilot", "pilot", "pilot", ["careful", "quick"]),
    "engineer": CrewRole("engineer", "engineer", "engineer", ["clever", "steady"]),
    "navigator": CrewRole("navigator", "navigator", "crew", ["sharp", "patient"]),
}

NAMES = ["Nova", "Milo", "Luna", "Zed", "Pia", "Rio", "Tess", "Ollie"]
TEAM_TRAITS = ["calm", "curious", "brave", "steady", "kind", "clever"]


def intro(world: World, crew: list[Entity]) -> None:
    names = ", ".join(c.id for c in crew[:-1]) + f", and {crew[-1].id}"
    world.say(
        f"{names} were aboard {world.route.vessel}, ready for {world.route.transit_kind} "
        f"from {world.route.start} to {world.route.end}."
    )
    world.say(
        f"They liked long windows, star maps, and the soft hum that made the ship feel "
        f"like a little moving home."
    )


def board(world: World, crew: list[Entity]) -> None:
    world.say(
        f"Before departure, each friend checked a job: one watched the route, one watched the controls, "
        f"and one watched for trouble."
    )
    for c in crew:
        c.memes["teamwork"] = c.memes.get("teamwork", 0.0) + 1


def depart(world: World) -> None:
    world.say(
        f"The shuttle drifted out from {world.route.start} and began its {world.route.route_tag} run."
    )
    world.say(f"Outside the glass, stars slid by like tiny silver dots.")


def encounter_problem(world: World, hero: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"Then {world.route.route_problem}."
    )
    world.say(
        f"The ship slowed near {world.route.hazard}, and the cheerful trip turned into a puzzle."
    )


def think(world: World, hero: Entity) -> None:
    hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1
    world.say(
        f"{hero.id} took a breath and said, \"Let's solve this together.\""
    )
    world.say(
        f"The crew looked at the problem, then at one another, and started checking clues instead of panicking."
    )


def repair(world: World, crew: list[Entity]) -> None:
    tool = world.route.fix_tool
    problem = world.route.route_problem
    helper = crew[1]
    world.say(
        f"{crew[0].id} held the light, {helper.id} worked the {tool}, and {crew[2].id} kept the ship steady."
    )
    world.say(
        f"With three sets of hands and one clear plan, they fixed the trouble that had made the trip stop."
    )
    for c in crew:
        c.memes["teamwork"] = c.memes.get("teamwork", 0.0) + 1
        c.memes["joy"] = c.memes.get("joy", 0.0) + 1
    world.facts["problem"] = problem
    world.facts["tool"] = tool


def finish(world: World, crew: list[Entity]) -> None:
    world.say(
        f"At last, {world.route.vessel} moved on again and reached {world.route.end} on time."
    )
    world.say(
        f"The friends smiled at the bright dock lights, glad their teamwork had turned a broken transit into a safe arrival."
    )


def build_world(route: TransitRoute, crew_names: list[str], crew_roles: list[str]) -> World:
    world = World(route)
    crew: list[Entity] = []
    for name, role_key, trait in zip(crew_names, crew_roles, TEAM_TRAITS):
        role = CREW[role_key]
        crew.append(world.add(Entity(
            id=name,
            kind="character",
            type=role.type,
            label=role.label,
            traits=[trait, role.traits[0]],
        )))
    world.facts["crew"] = crew
    world.facts["route"] = route
    intro(world, crew)
    world.para()
    board(world, crew)
    depart(world)
    encounter_problem(world, crew[0])
    world.para()
    think(world, crew[0])
    repair(world, crew)
    finish(world, crew)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    route: TransitRoute = f["route"]
    crew: list[Entity] = f["crew"]
    return [
        f'Write a short space-adventure story for a child about a {route.transit_kind} journey that uses the word "transit".',
        f"Tell a gentle story where {crew[0].id} and friends solve a ship problem together while traveling from {route.start} to {route.end}.",
        f"Write a story about teamwork on {route.vessel} when {route.route_problem} during a transit ride.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    route: TransitRoute = f["route"]
    crew: list[Entity] = f["crew"]
    hero = crew[0]
    helper = crew[1]
    return [
        QAItem(
            question=f"Where were the friends traveling at the start?",
            answer=f"They were on {route.vessel}, traveling from {route.start} to {route.end} in space.",
        ),
        QAItem(
            question=f"What went wrong during the transit?",
            answer=f"{route.route_problem.capitalize()}, so the ship had to stop and the crew had to think of a fix.",
        ),
        QAItem(
            question=f"How did the crew solve the problem?",
            answer=f"They worked together, used {route.fix_tool}, and kept the ship steady until it could move again.",
        ),
        QAItem(
            question=f"How did {hero.id} feel when the problem appeared?",
            answer=f"{hero.id} felt worried for a moment, but then became focused and helped the team solve it.",
        ),
        QAItem(
            question=f"Who helped most with the repair?",
            answer=f"{helper.id} helped by working with {route.fix_tool} while the others held the light and steadied the ship.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "transit": [
        QAItem(
            question="What does transit mean?",
            answer="Transit means traveling from one place to another, often by a vehicle like a ship, train, or shuttle.",
        ),
        QAItem(
            question="Why do travelers use routes?",
            answer="Travelers use routes so they can follow a planned path and reach the correct destination safely.",
        ),
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people share jobs, help one another, and work toward the same goal.",
        ),
    ],
    "space": [
        QAItem(
            question="What is space like?",
            answer="Space is huge and dark, with stars, planets, and long distances between places.",
        ),
    ],
    "problem solving": [
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing what is wrong, thinking about choices, and trying a good fix.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE["transit"] + WORLD_KNOWLEDGE["teamwork"] + WORLD_KNOWLEDGE["space"] + WORLD_KNOWLEDGE["problem solving"]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  route problem: {world.route.route_problem}")
    lines.append(f"  fix tool: {world.route.fix_tool}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    route: str
    crew0: str
    crew1: str
    crew2: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(route="orbital_line", crew0="Nova", crew1="Milo", crew2="Luna"),
    StoryParams(route="asteroid_link", crew0="Pia", crew1="Rio", crew2="Tess"),
    StoryParams(route="solar_run", crew0="Zed", crew1="Ollie", crew2="Maya"),
]


ASP_RULES = r"""
route_problem(Route) :- route(Route), needs_fix(Route).
teamwork(Route) :- route_problem(Route), crew(Agent1), crew(Agent2), crew(Agent3).

needs_fix(R) :- route(R), blocked(R).
can_continue(R) :- teamwork(R), repair_tool(R, Tool), tool_available(Tool).
valid_story(R) :- route(R), can_continue(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, route in ROUTES.items():
        lines.append(asp.fact("route", key))
        lines.append(asp.fact("start", key, route.start))
        lines.append(asp.fact("end", key, route.end))
        lines.append(asp.fact("vessel", key, route.vessel))
        lines.append(asp.fact("blocked", key))
        lines.append(asp.fact("repair_tool", key, route.fix_tool))
    for role in CREW:
        lines.append(asp.fact("crew", role))
        lines.append(asp.fact("tool_available", "backup"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    route = args.route or rng.choice(sorted(ROUTES))
    crew_names = [args.crew0, args.crew1, args.crew2]
    defaults = [rng.choice(NAMES), rng.choice(NAMES), rng.choice(NAMES)]
    crew_names = [n or d for n, d in zip(crew_names, defaults)]
    return StoryParams(route=route, crew0=crew_names[0], crew1=crew_names[1], crew2=crew_names[2])


def generate(params: StoryParams) -> StorySample:
    route = ROUTES[params.route]
    world = build_world(route, [params.crew0, params.crew1, params.crew2], ["captain", "engineer", "navigator"])
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure transit story world with teamwork and problem solving.")
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--crew0")
    ap.add_argument("--crew1")
    ap.add_argument("--crew2")
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


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
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
