#!/usr/bin/env python3
"""
A small space-adventure storyworld about a crew using tips, division, and sync
to solve a repeating problem aboard a ship.
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


@dataclass
class CrewMember:
    id: str
    role: str
    name: str
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class ShipSystem:
    id: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    ship: str
    system: str
    problem: str
    tip: str
    division: str
    sync: str
    captain: str
    engineer: str
    navigator: str
    seed: Optional[int] = None


SHIPS = {
    "comet": "the starship Comet Kite",
    "lantern": "the starship Lantern Drift",
    "orbit": "the starship Orbit Pearl",
}

SYSTEMS = {
    "scanner": "the sensor scanner",
    "router": "the signal router",
    "dome": "the glass dome",
}

PROBLEMS = {
    "static": "static noise kept slipping into every signal",
    "drift": "the map kept drifting a little out of sync",
    "echo": "the ship's announcements echoed and repeated themselves",
}

TIPS = {
    "tap": "tap the panel twice before each try",
    "pause": "pause one breath between each step",
    "pair": "pair up and check each switch together",
}

DIVISIONS = {
    "half": "divide the work in half",
    "roles": "divide the jobs by role",
    "timing": "divide the timing into short turns",
}

SYNCS = {
    "beat": "sync their steps to a steady beat",
    "count": "sync the countdown to the clock",
    "blink": "sync the lights to a blinking rhythm",
}

CREW_NAMES = ["Nova", "Milo", "Iris", "Taj", "Luna", "Zed", "Pia", "Kito"]
ROLES = ["captain", "engineer", "navigator", "pilot", "mechanic", "commander"]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, object] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def setup_world(params: StoryParams) -> World:
    world = World(params)
    ship = ShipSystem(id="ship", label=SHIPS[params.ship], meters={"stress": 0.0, "order": 0.0}, memes={"hope": 0.0})
    system = ShipSystem(id="system", label=SYSTEMS[params.system], meters={"glitch": 1.0, "stability": 0.0}, memes={"confusion": 1.0})
    world.add(ship)
    world.add(system)

    captain = CrewMember(id="captain", role="captain", name=params.captain, meters={"focus": 1.0}, memes={"worry": 0.0, "joy": 0.0})
    engineer = CrewMember(id="engineer", role="engineer", name=params.engineer, meters={"focus": 1.0}, memes={"worry": 0.0, "joy": 0.0})
    navigator = CrewMember(id="navigator", role="navigator", name=params.navigator, meters={"focus": 1.0}, memes={"worry": 0.0, "joy": 0.0})

    world.add(captain)
    world.add(engineer)
    world.add(navigator)
    return world


def propagate(world: World) -> None:
    params = world.params
    ship: ShipSystem = world.entities["ship"]  # type: ignore[assignment]
    system: ShipSystem = world.entities["system"]  # type: ignore[assignment]
    captain: CrewMember = world.entities["captain"]  # type: ignore[assignment]
    engineer: CrewMember = world.entities["engineer"]  # type: ignore[assignment]
    navigator: CrewMember = world.entities["navigator"]  # type: ignore[assignment]

    if system.meters["glitch"] > 0:
        ship.meters["stress"] += 1

    if captain.memes["worry"] > 0 and engineer.memes["worry"] > 0:
        ship.memes["hope"] += 1

    if engineer.meters.get("repair", 0) >= 1 and navigator.meters.get("trace", 0) >= 1:
        system.meters["stability"] = 1
        system.meters["glitch"] = 0


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    ship: ShipSystem = world.entities["ship"]  # type: ignore[assignment]
    system: ShipSystem = world.entities["system"]  # type: ignore[assignment]
    captain: CrewMember = world.entities["captain"]  # type: ignore[assignment]
    engineer: CrewMember = world.entities["engineer"]  # type: ignore[assignment]
    navigator: CrewMember = world.entities["navigator"]  # type: ignore[assignment]

    world.say(f"On {ship.label}, the crew could hear a problem humming inside {system.label}.")
    world.say(f"{captain.name} noticed that {PROBLEMS[params.problem]}.")
    world.say(f"{captain.name} showed the others a small tip: {TIPS[params.tip]}.")
    world.say(f"{engineer.name} and {navigator.name} nodded, because the tip sounded smart.")

    world.para()
    world.say(f"Then they made a plan to {DIVISIONS[params.division]} so nobody would get tangled up.")
    captain.memes["worry"] += 1
    engineer.memes["worry"] += 1
    navigator.memes["worry"] += 1

    if params.division == "half":
        engineer.meters["repair"] = 1
        navigator.meters["trace"] = 1
        world.say(f"{engineer.name} fixed the first half while {navigator.name} watched the signals.")
    elif params.division == "roles":
        engineer.meters["repair"] = 1
        navigator.meters["trace"] = 1
        world.say(f"{engineer.name} handled the wires, and {navigator.name} tracked the blinking map.")
    else:
        engineer.meters["repair"] = 1
        navigator.meters["trace"] = 1
        world.say(f"They worked in short turns, which kept the ship calm and steady.")

    world.say(f"To stay in sync, they chose to {SYNCS[params.sync]}.")
    world.say(f"Again and again, they checked the same steps, because repetition helped them keep the rhythm.")

    propagate(world)

    world.para()
    if system.meters["stability"] >= 1:
        captain.memes["joy"] += 1
        engineer.memes["joy"] += 1
        navigator.memes["joy"] += 1
        world.say(f"At last, the glitch faded away, and {system.label} came back in sync.")
        world.say(f"{ship.label} felt lighter, as if it had taken a deep breath in space.")
        world.say(f"{captain.name} smiled at the crew, because the repeating problem was solved together.")
    else:
        world.say(f"The problem was still there, so they kept working with careful, repeated steps.")

    world.facts = {
        "ship": ship,
        "system": system,
        "captain": captain,
        "engineer": engineer,
        "navigator": navigator,
        "params": params,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short space adventure for a child about a crew solving a repeating problem on {SHIPS[p.ship]}.',
        f'Tell a gentle story where the crew uses a tip, a division of jobs, and sync to fix {SYSTEMS[p.system]}.',
        f'Write a simple spaceship story that includes repetition and problem solving, with the word "{p.tip}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    ship: ShipSystem = world.facts["ship"]
    system: ShipSystem = world.facts["system"]
    captain: CrewMember = world.facts["captain"]
    engineer: CrewMember = world.facts["engineer"]
    navigator: CrewMember = world.facts["navigator"]
    return [
        QAItem(
            question=f"What problem did the crew notice on {ship.label}?",
            answer=f"They noticed that {PROBLEMS[p.problem]}. That made {system.label} act out of sync.",
        ),
        QAItem(
            question=f"What tip did {captain.name} show the others?",
            answer=f"{captain.name} showed them this tip: {TIPS[p.tip]}. It helped them start in a careful way.",
        ),
        QAItem(
            question=f"How did the crew divide the work to solve the problem?",
            answer=f"They chose to {DIVISIONS[p.division]}, so {engineer.name} and {navigator.name} could work without getting in each other's way.",
        ),
        QAItem(
            question=f"How did the crew keep everything in sync?",
            answer=f"They tried to {SYNCS[p.sync]}, and they repeated the same steps again and again until the ship felt steady.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"{system.label} came back in sync, the glitch faded, and the crew felt proud because they solved the problem together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tip in a story like this?",
            answer="A tip is a small helpful idea that shows a better way to do something.",
        ),
        QAItem(
            question="What does it mean to divide work?",
            answer="To divide work means to split jobs into smaller parts so people can help in an organized way.",
        ),
        QAItem(
            question="What does sync mean?",
            answer="To sync means to move or work at the same time in a steady, matching rhythm.",
        ),
    ]


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
    for ent in world.entities.values():
        if isinstance(ent, CrewMember):
            lines.append(
                f"  {ent.id:9} ({ent.role:9}) meters={ent.meters} memes={ent.memes}"
            )
        else:
            lines.append(
                f"  {ent.id:9} ({ent.label}) meters={ent.meters} memes={ent.memes}"
            )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld about tips, division, sync, repetition, and problem solving.")
    ap.add_argument("--ship", choices=SHIPS.keys())
    ap.add_argument("--system", choices=SYSTEMS.keys())
    ap.add_argument("--problem", choices=PROBLEMS.keys())
    ap.add_argument("--tip", choices=TIPS.keys())
    ap.add_argument("--division", choices=DIVISIONS.keys())
    ap.add_argument("--sync", choices=SYNCS.keys())
    ap.add_argument("--captain")
    ap.add_argument("--engineer")
    ap.add_argument("--navigator")
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


def valid_combos() -> list[tuple[str, str, str, str, str, str]]:
    combos = []
    for ship in SHIPS:
        for system in SYSTEMS:
            for problem in PROBLEMS:
                for tip in TIPS:
                    for division in DIVISIONS:
                        for sync in SYNCS:
                            combos.append((ship, system, problem, tip, division, sync))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations exist.")
    ship, system, problem, tip, division, sync = rng.choice(combos)
    if args.ship:
        ship = args.ship
    if args.system:
        system = args.system
    if args.problem:
        problem = args.problem
    if args.tip:
        tip = args.tip
    if args.division:
        division = args.division
    if args.sync:
        sync = args.sync

    captain = args.captain or rng.choice(CREW_NAMES)
    engineer = args.engineer or rng.choice([n for n in CREW_NAMES if n != captain])
    navigator = args.navigator or rng.choice([n for n in CREW_NAMES if n not in {captain, engineer}])

    if len({captain, engineer, navigator}) < 3:
        raise StoryError("Captain, engineer, and navigator must be different names.")

    return StoryParams(
        ship=ship, system=system, problem=problem, tip=tip,
        division=division, sync=sync,
        captain=captain, engineer=engineer, navigator=navigator,
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
ship(S) :- ship_fact(S).
system(X) :- system_fact(X).
problem(P) :- problem_fact(P).
tip(T) :- tip_fact(T).
division(D) :- division_fact(D).
sync(S) :- sync_fact(S).

compatible(SH, SY, PR, TI, DI, SYN) :- ship(SH), system(SY), problem(PR), tip(TI), division(DI), sync(SYN).
#show compatible/6.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for k in SHIPS:
        lines.append(asp.fact("ship_fact", k))
    for k in SYSTEMS:
        lines.append(asp.fact("system_fact", k))
    for k in PROBLEMS:
        lines.append(asp.fact("problem_fact", k))
    for k in TIPS:
        lines.append(asp.fact("tip_fact", k))
    for k in DIVISIONS:
        lines.append(asp.fact("division_fact", k))
    for k in SYNCS:
        lines.append(asp.fact("sync_fact", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/6."))
    return sorted(set(asp.atoms(model, "compatible")))


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


CURATED = [
    StoryParams("comet", "scanner", "static", "tap", "half", "beat", "Nova", "Milo", "Iris"),
    StoryParams("lantern", "router", "drift", "pause", "roles", "count", "Pia", "Taj", "Luna"),
    StoryParams("orbit", "dome", "echo", "pair", "timing", "blink", "Zed", "Kito", "Nova"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
