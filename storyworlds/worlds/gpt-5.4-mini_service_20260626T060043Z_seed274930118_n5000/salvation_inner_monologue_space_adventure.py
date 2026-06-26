#!/usr/bin/env python3
"""
storyworlds/worlds/salvation_inner_monologue_space_adventure.py
===============================================================

A small space-adventure story world about a stranded traveler, a risky choice,
and a rescue that begins inside the hero's head.

Premise:
- A pilot or scout is separated from the ship.
- A mission-critical beacon, fuel cell, or map is missing or damaged.
- The hero must choose between panic and a careful rescue plan.

Narrative instrument:
- Inner monologue is used as a stateful emotional engine.
- The story should show thought, fear, reasoning, and relief as world state
  changes, not as static decoration.

The world is built around:
- physical meters: oxygen, drift, battery, signal, damage, distance
- emotional memes: fear, hope, resolve, relief, gratitude

This file follows the Storyweavers world contract:
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- imports results eagerly and asp lazily
- includes Python reasonableness gates and inline ASP_RULES twin
- supports --verify, --asp, --show-asp, --json, --qa, --trace, -n, --all, --seed
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        male = {"man", "boy", "father", "pilot", "captain", "scout", "astronaut", "engineer"}
        female = {"woman", "girl", "mother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str
    setting: str = "deep space"
    hazards: set[str] = field(default_factory=set)
    supports: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    kind: str
    at_risk: str
    cause: str
    inner_voice: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RescueTool:
    id: str
    label: str
    covers: set[str]
    fixes: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PROBLEMS = {
    "drift": Problem(
        id="drift",
        label="the slow drift away from the ship",
        kind="drift",
        at_risk="distance",
        cause="a broken tether",
        inner_voice="If I keep drifting, nobody will find me.",
        tags={"space", "rescue", "distance"},
    ),
    "oxygen": Problem(
        id="oxygen",
        label="the fading oxygen reading",
        kind="oxygen",
        at_risk="oxygen",
        cause="a cracked tank seal",
        inner_voice="I need to breathe carefully and not waste a puff.",
        tags={"space", "rescue", "oxygen"},
    ),
    "signal": Problem(
        id="signal",
        label="the dim rescue signal",
        kind="signal",
        at_risk="signal",
        cause="dust on the beacon lens",
        inner_voice="If the beacon stays dark, the rescue ship will miss me.",
        tags={"space", "rescue", "signal"},
    ),
    "battery": Problem(
        id="battery",
        label="the weak map battery",
        kind="battery",
        at_risk="battery",
        cause="a long, cold night",
        inner_voice="The map will fail before I can reach home.",
        tags={"space", "navigation", "battery"},
    ),
}

TOOLS = [
    RescueTool(
        id="tether",
        label="a spare tether",
        covers={"distance"},
        fixes={"drift"},
        prep="clip on a spare tether first",
        tail="clipped on the spare tether",
    ),
    RescueTool(
        id="seal_patch",
        label="a seal patch",
        covers={"oxygen"},
        fixes={"oxygen"},
        prep="press a seal patch over the crack",
        tail="pressed the seal patch over the crack",
    ),
    RescueTool(
        id="lens_wipe",
        label="a lens wipe",
        covers={"signal"},
        fixes={"signal"},
        prep="wipe the beacon lens clean",
        tail="wiped the beacon lens clean",
    ),
    RescueTool(
        id="cell_pack",
        label="a backup cell pack",
        covers={"battery"},
        fixes={"battery"},
        prep="snap in a backup cell pack",
        tail="snapped in a backup cell pack",
        plural=False,
    ),
]

LOCATIONS = {
    "airlock": Ship(name="Orion Ark", supports={"drift", "oxygen"}),
    "moon_base": Ship(name="Moon Ladder", supports={"signal", "battery"}),
    "asteroid_dock": Ship(name="Star Harbor", supports={"drift", "signal", "battery"}),
}

HEROES = [
    ("Ari", "scout", ["brave", "quiet"]),
    ("Mina", "astronaut", ["careful", "curious"]),
    ("Jules", "pilot", ["determined", "small"]),
    ("Rin", "engineer", ["clever", "steady"]),
]

COMPANIONS = [
    ("beep", "robot", "a little helper robot"),
    ("sora", "robot", "a round rescue bot"),
    ("nav", "tool", "the ship's navigation voice"),
]


@dataclass
class StoryParams:
    place: str
    problem: str
    hero_name: str
    hero_type: str
    companion: str
    trait: str
    seed: Optional[int] = None


def world_objective(problem: Problem, tool: Optional[RescueTool]) -> bool:
    return tool is not None and problem.id in tool.fixes


def select_tool(problem: Problem) -> Optional[RescueTool]:
    for tool in TOOLS:
        if problem.id in tool.fixes and problem.at_risk in tool.covers:
            return tool
    return None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, ship in LOCATIONS.items():
        for pid, prob in PROBLEMS.items():
            if prob.at_risk in ship.supports and select_tool(prob):
                out.append((place, pid))
    return out


def explain_rejection(prob: Problem) -> str:
    return (
        f"(No story: this problem has no honest rescue tool that covers {prob.at_risk}. "
        f"The rescue has to change the world state, not just the wording.)"
    )


class WorldTrace:
    pass


def inner_voice(problem: Problem, hero: Entity) -> str:
    return problem.inner_voice.replace("I", hero.pronoun("subject").capitalize())


def build_scene(world: World, hero: Entity, companion: Entity, problem: Problem, tool: Optional[RescueTool]) -> None:
    world.say(
        f"{hero.id} floated beside {world.ship.name} with {hero.pronoun('possessive')} "
        f"{companion.label} humming softly in the dark."
    )
    world.say(
        f"The trouble was {problem.label}; {problem.cause} had made the situation feel too small for big fear."
    )
    hero.memes["fear"] += 1
    hero.memes["hope"] += 0.25
    world.say(
        f"Inside {hero.id}'s head, a quiet thought kept repeating: \"{inner_voice(problem, hero)}\""
    )
    world.para()
    world.say(
        f"{hero.id} checked the damaged gear. The reading for {problem.at_risk} was low, and the silence felt heavy."
    )
    if tool:
        hero.memes["resolve"] += 1
        world.say(
            f"Then {hero.id} found {tool.label}. {hero.pronoun('subject').capitalize()} took a slow breath and chose a careful rescue instead of panic."
        )
        world.say(
            f"{hero.id} decided to {tool.prep}, because that would protect the part of the mission that mattered most."
        )
        world.say(
            f"{hero.pronoun('subject').capitalize()} could almost hear the future getting brighter."
        )
        world.para()
        world.say(
            f"{hero.id} {tool.tail}, and the world changed right away: the danger eased, the signal steadied, and the dark felt less lonely."
        )
        hero.memes["fear"] = 0
        hero.memes["hope"] += 1
        hero.memes["relief"] += 1
        hero.memes["gratitude"] += 1
    else:
        world.say(
            f"{hero.id} searched, but there was no tool that could truly fix the problem."
        )


def tell(place: Ship, problem: Problem, hero_name: str, hero_type: str, companion_id: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=[trait, "alone"],
        meters={"oxygen": 1.0, "distance": 1.0, "signal": 0.0, "battery": 0.5},
        memes={"fear": 0.0, "hope": 0.5, "resolve": 0.0, "relief": 0.0, "gratitude": 0.0},
    ))
    companion = world.add(Entity(
        id=companion_id,
        kind="character" if companion_id != "nav" else "thing",
        type="robot" if companion_id != "nav" else "tool",
        label={"beep": "beep-beep", "sora": "Sora", "nav": "the navigation voice"}[companion_id],
    ))
    tool = select_tool(problem)
    if tool:
        world.add(Entity(
            id=tool.id,
            type="tool",
            label=tool.label,
            plural=tool.plural,
            owner=hero.id,
        ))
    world.facts.update(hero=hero, companion=companion, problem=problem, tool=tool, ship=place)
    build_scene(world, hero, companion, problem, tool)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    problem: Problem = f["problem"]
    return [
        f'Write a short space-adventure story for a small child about "{problem.id}" and a rescue that begins with an inner monologue.',
        f"Tell a gentle story where {hero.id} thinks carefully under stress, notices {problem.label}, and finds a way to save the mission.",
        f"Write a child-facing rescue story in space with a brave choice, a quiet thought, and a happy ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    problem: Problem = f["problem"]
    tool: Optional[RescueTool] = f["tool"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.type} who was trying to stay calm in space.",
        ),
        QAItem(
            question=f"What problem made the adventure scary?",
            answer=f"The scary problem was {problem.label}. It mattered because {problem.cause}.",
        ),
        QAItem(
            question=f"What was the quiet thought in {hero.id}'s head?",
            answer=f"{problem.inner_voice}",
        ),
    ]
    if tool:
        qa.append(
            QAItem(
                question=f"How did {hero.id} solve the problem?",
                answer=f"{hero.id} used {tool.label} and followed a careful plan, so the rescue became safe enough to finish.",
            )
        )
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel at the end?",
                answer=f"{hero.id} felt relief and gratitude after the rescue worked.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rescue beacon for?",
            answer="A rescue beacon is a signal that helps others find someone who needs help.",
        ),
        QAItem(
            question="Why do astronauts keep track of oxygen?",
            answer="Astronauts keep track of oxygen because they need air to breathe safely.",
        ),
        QAItem(
            question="What does a tether do in space?",
            answer="A tether can help keep a person from drifting too far away from a ship or station.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


@dataclass
class ASPFacts:
    pass


ASP_RULES = r"""
problem_valid(P) :- problem(P), tool(T), fixes(T,P), covers(T,R), at_risk(P,R).
story_valid(Place,P) :- ship_place(Place), problem_valid(P), supports(Place,R), at_risk(P,R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, ship in LOCATIONS.items():
        lines.append(asp.fact("ship_place", place))
        for s in sorted(ship.supports):
            lines.append(asp.fact("supports", place, s))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("at_risk", pid, prob.at_risk))
        for t in sorted(prob.tags):
            lines.append(asp.fact("tag", pid, t))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for c in sorted(tool.covers):
            lines.append(asp.fact("covers", tool.id, c))
        for f in sorted(tool.fixes):
            lines.append(asp.fact("fixes", tool.id, f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_valid/2."))
    return sorted(set(asp.atoms(model, "story_valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asv = set(asp_valid_combos())
    if py == asv:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    print("only python:", sorted(py - asv))
    print("only clingo:", sorted(asv - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with inner monologue and rescue.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["scout", "astronaut", "pilot", "engineer"])
    ap.add_argument("--companion", choices=[c[0] for c in COMPANIONS])
    ap.add_argument("--trait")
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
    if args.place and args.problem:
        if (args.place, args.problem) not in combos:
            raise StoryError(explain_rejection(PROBLEMS[args.problem]))
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.problem is None or c[1] == args.problem)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, prob = rng.choice(sorted(filtered))
    hero_name, hero_type, traits = rng.choice(HEROES)
    companion = args.companion or rng.choice([c[0] for c in COMPANIONS])
    trait = args.trait or rng.choice(traits)
    return StoryParams(
        place=place,
        problem=prob,
        hero_name=args.name or hero_name,
        hero_type=args.hero_type or hero_type,
        companion=companion,
        trait=trait,
    )


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, ship in LOCATIONS.items():
        for pid, prob in PROBLEMS.items():
            if prob.at_risk in ship.supports and select_tool(prob) is not None:
                combos.append((place, pid))
    return combos


def generate(params: StoryParams) -> StorySample:
    world = tell(LOCATIONS[params.place], PROBLEMS[params.problem], params.hero_name, params.hero_type, params.companion, params.trait)
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


CURATED = [
    StoryParams(place="airlock", problem="drift", hero_name="Ari", hero_type="scout", companion="beep", trait="brave"),
    StoryParams(place="moon_base", problem="signal", hero_name="Mina", hero_type="astronaut", companion="sora", trait="careful"),
    StoryParams(place="asteroid_dock", problem="battery", hero_name="Jules", hero_type="pilot", companion="nav", trait="determined"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_valid/2."))
        combos = sorted(set(asp.atoms(model, "story_valid")))
        print(f"{len(combos)} compatible story combos:")
        for place, prob in combos:
            print(f"  {place:12} {prob}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.hero_name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
