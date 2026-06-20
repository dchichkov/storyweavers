#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hobo_geology_ist_elevator_problem_solving_tall.py
==================================================================================

A standalone storyworld sketch for a tall-tale elevator problem-solving story.
It rebuilds a small classical domain: a hobo and a geology-ist get stuck in an
elevator, notice the true cause, solve the trouble with brains and a few humble
tools, and end with the elevator rising again.

The story keeps the seed words and frame:
- words: hobo, geology-ist
- setting: elevator
- feature: problem solving
- style: tall tale

This script is stdlib-only and follows the shared Storyweavers result contract.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "hobo"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Location:
    id: str
    label: str
    height: str
    mood: str
    trap: str
    floor: int
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Problem:
    id: str
    label: str
    cause: str
    clue: str
    risk: str
    spread: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    lift = world.get("elevator")
    if lift.meters["stuck"] < THRESHOLD:
        return out
    sig = ("fear", lift.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for eid in ("hobo", "geologist"):
        world.get(eid).memes["worry"] += 1
    lift.meters["danger"] += 1
    out.append("__fear__")
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonability_gate(problem: Problem, tool: Tool) -> bool:
    return problem.id in {"stuck", "jammed", "overloaded"} and tool.sense >= SENSE_MIN


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sense >= SENSE_MIN]


def best_tool() -> Tool:
    return max(TOOLS.values(), key=lambda t: t.sense)


def predict(world: World, problem: Problem) -> dict:
    sim = world.copy()
    _trigger_problem(sim, sim.get("elevator"), problem, narrate=False)
    return {"stuck": sim.get("elevator").meters["stuck"] >= THRESHOLD}


def _trigger_problem(world: World, elevator: Entity, problem: Problem, narrate: bool = True) -> None:
    elevator.meters["stuck"] += 1
    elevator.meters["trouble"] += problem.spread
    propagate(world, narrate=narrate)


def open_story(world: World, hobo: Entity, geologist: Entity, place: Location) -> None:
    hobo.memes["pride"] += 1
    geologist.memes["wonder"] += 1
    world.say(
        f"In a little tower with a big heart and a mighty hum, {hobo.id} the hobo "
        f"and {geologist.id} the geology-ist stepped into the elevator. "
        f"{place.mood.capitalize()} hung in the air, and the cab rose like a tin can on a string."
    )
    world.say(
        f"{hobo.id} carried a patched sack, and {geologist.id} carried a pocket full of rock bits. "
        f"They talked as tall-tale travelers do, with eyes wide and voices ready for adventure."
    )


def trouble(world: World, place: Location, problem: Problem) -> None:
    world.say(
        f"But halfway between floors, the elevator gave a mighty shiver and stopped still as a fence post."
    )
    world.say(
        f"{place.trap.capitalize()} had done its mischief: {problem.cause}. "
        f"{problem.clue.capitalize()}, and the whole cab wore a worried hush."
    )


def study_problem(world: World, geologist: Entity, problem: Problem) -> None:
    geologist.memes["focus"] += 1
    world.say(
        f"{geologist.id} knelt and studied the seam by the door. "
        f'"That looks like {problem.clue}," {geologist.pronoun()} said. '
        f'"In my trade, a tiny stone can cause a giant fuss."'
    )


def invent_plan(world: World, hobo: Entity, geologist: Entity, problem: Problem, tool: Tool) -> None:
    hobo.memes["hope"] += 1
    geologist.memes["hope"] += 1
    world.say(
        f'{hobo.id} tipped {hobo.pronoun("possessive")} hat and said, '
        f'"Well, then we need a small idea with a long reach."'
    )
    world.say(
        f"{geologist.id} agreed, and together they chose {tool.phrase}. "
        f"{tool.use.capitalize()}, and the plan sounded smart enough to wake the moon."
    )


def solve(world: World, hobo: Entity, geologist: Entity, problem: Problem, tool: Tool, place: Location) -> None:
    elevator = world.get("elevator")
    elevator.meters["stuck"] = 0.0
    elevator.meters["trouble"] = 0.0
    world.say(
        f"With {tool.phrase}, they {tool.use}. "
        f"The jam gave way, the cable sighed, and the elevator climbed free as a kite in a spring wind."
    )
    world.say(
        f"{place.label.capitalize()} brightened as the cab began to move again, one floor, then another, "
        f"as steady as a wagon on a road."
    )
    hobo.memes["joy"] += 1
    geologist.memes["joy"] += 1


def ending(world: World, hobo: Entity, geologist: Entity, place: Location) -> None:
    world.say(
        f"At the top floor, the doors opened with a cheerful ding. "
        f"{hobo.id} grinned, {geologist.id} laughed, and the elevator stood tall and proper again."
    )
    world.say(
        f"They stepped out into {place.height}, carrying their story like a lantern: "
        f"when a small problem blocks a big machine, a steady head and a handy tool can set things right."
    )


def tell(place: Location, problem: Problem, tool: Tool,
         hobo_name: str = "Hank", geologist_name: str = "Gus") -> World:
    world = World()
    hobo = world.add(Entity(id=hobo_name, kind="character", type="hobo", role="hobo"))
    geologist = world.add(Entity(id=geologist_name, kind="character", type="man", role="geology-ist"))
    elevator = world.add(Entity(id="elevator", type="elevator", label="the elevator"))
    world.add(Entity(id="shaft", type="shaft", label="the shaft"))
    world.facts.update(place=place, problem=problem, tool=tool, hobo=hobo, geologist=geologist)

    open_story(world, hobo, geologist, place)
    world.para()
    trouble(world, place, problem)
    study_problem(world, geologist, problem)
    world.para()
    invent_plan(world, hobo, geologist, problem, tool)
    _trigger_problem(world, elevator, problem)
    world.para()
    solve(world, hobo, geologist, problem, tool, place)
    ending(world, hobo, geologist, place)
    world.facts.update(outcome="solved", stuck=False, repaired=True)
    return world


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    hobo_name: str
    geologist_name: str
    seed: Optional[int] = None


PLACES = {
    "elevator": Location("elevator", "the elevator", "high above the lobby", "warm and echoey", "a sly little jam", 7),
}

PROBLEMS = {
    "stuck": Problem("stuck", "stuck elevator", "the elevator stopped between floors", "a pebble was wedged in the door track", "people might worry", 1, {"stone", "problem", "elevator"}),
    "jammed": Problem("jammed", "jammed door", "the door would not close right", "a chip of shale had caught in the guide", "the cab could not move", 1, {"stone", "problem", "elevator"}),
    "overloaded": Problem("overloaded", "heavy elevator", "the cab was carrying too much weight", "the weight light blinked red like a firefly", "the lift would not start", 1, {"weight", "problem", "elevator"}),
}

TOOLS = {
    "rock_tap": Tool("rock_tap", "a rock-tapper", "a little chisel", "carefully tapped the pebble loose", 3, 3, {"stone"}),
    "spoon": Tool("spoon", "a bent spoon", "a bent spoon", "pried the shard free", 2, 2, {"metal"}),
    "balance": Tool("balance", "a balance trick", "a quick balance trick", "shifted the bags to ease the load", 2, 2, {"weight"}),
    "card": Tool("card", "a stiff card", "a stiff card", "slid under the edge and lifted the grit away", 2, 2, {"stone"}),
}

HOBO_NAMES = ["Hank", "Silas", "Jeb", "Milo", "Rufus"]
GEO_NAMES = ["Gus", "Ivy", "Ada", "Nell", "Bert"]
TRAITS = ["spry", "kindly", "clever", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for pid, prob in PROBLEMS.items():
            for tid, tool in TOOLS.items():
                if reasonability_gate(prob, tool):
                    combos.append((place, pid, tid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: hobo, geology-ist, elevator, problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.tool and not reasonability_gate(PROBLEMS[args.problem], TOOLS[args.tool]):
        raise StoryError("That tool does not make a sensible fix for that elevator problem.")
    combos = [c for c in valid_combos() if (args.place is None or c[0] == args.place) and (args.problem is None or c[1] == args.problem) and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, tool = rng.choice(sorted(combos))
    return StoryParams(place, problem, tool, rng.choice(HOBO_NAMES), rng.choice(GEO_NAMES))


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], PROBLEMS[params.problem], TOOLS[params.tool], params.hobo_name, params.geologist_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale about a hobo and a geology-ist in an elevator that gets {f["problem"].id if hasattr(f["problem"], "id") else "stuck"}.',
        f"Tell a problem-solving story where {f['hobo'].id} and {f['geologist'].id} work together to fix the elevator with a small tool.",
        'Write a child-friendly tall tale that includes the words "hobo" and "geology-ist" and ends with the elevator moving again.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("Who is the story about?",
         f"It is about {f['hobo'].id} the hobo and {f['geologist'].id} the geology-ist. They rode the elevator and faced a problem together."),
        ("What went wrong in the elevator?",
         f"The elevator got stuck between floors because {f['problem'].clue}. That made the cab stop and turned the ride into a big, echoing puzzle."),
        ("How did they fix it?",
         f"They used {f['tool'].phrase} and worked together until the trouble cleared. The hobo helped with steady hands, and the geology-ist spotted the right place to act."),
        ("How did the story end?",
         f"The elevator moved again and reached the top floor safely. The ending shows that a small problem can be solved when people think hard and help one another."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a geology-ist?",
         "A geology-ist is a person who studies rocks, stones, and the ground. They pay close attention to tiny chips and hard surfaces."),
        ("What does an elevator do?",
         "An elevator carries people up and down between floors in a building. It helps them travel without climbing the stairs."),
        ("Why is it smart to stay calm when a machine stops working?",
         "Staying calm helps people notice the real problem and choose a safe fix. Panic makes it harder to think clearly."),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("elevator", "stuck", "rock_tap", "Hank", "Gus"),
    StoryParams("elevator", "jammed", "card", "Silas", "Ivy"),
    StoryParams("elevator", "overloaded", "balance", "Rufus", "Ada"),
]


def explain_response(tool_id: str) -> str:
    t = TOOLS[tool_id]
    return f"(Refusing tool '{tool_id}': it is too weak or too odd for this elevator puzzle.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("spread", pid, p.spread))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, t.sense))
        lines.append(asp.fact("power", tid, t.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Pr, T) :- place(P), problem(Pr), tool(T), sense(T, S), sense_min(M), S >= M, problem(Pr).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in the gate.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (place, problem, tool) combos:")
        for combo in asp_valid_combos():
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
