#!/usr/bin/env python3
"""
Standalone story world: a small animal problem-solving tale about a carpet and a worried mind.
The world is built to feel like a gentle Animal Story: a pet notices a problem, thinks hard,
tries a fix, and ends with a clear change in the room and in how everyone feels.
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
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "animal" | "thing"
    species: str = ""
    name: str = ""
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "it"

    def cap_name(self) -> str:
        return self.name or self.label or self.id


@dataclass
class Room:
    name: str
    features: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    mess: str
    clue: str
    fix: str
    risk: str
    solved_by: str
    asks_help: bool = True


@dataclass
class StoryParams:
    room: str
    problem: str
    hero: str
    helper: str
    seed: Optional[int] = None


@dataclass
class World:
    room: Room
    hero: Entity
    helper: Entity
    problem: Problem
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    carpet_mess: float = 0.0
    psych_worry: float = 0.0
    solved: bool = False
    story_bits: list[str] = field(default_factory=list)
    fired: set[str] = field(default_factory=set)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.story_bits.append(text)

    def para(self) -> None:
        if self.story_bits and self.story_bits[-1] != "":
            self.story_bits.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for bit in self.story_bits:
            if bit == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(bit)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

ROOMS = {
    "den": Room("the den", {"carpet"}),
    "living_room": Room("the living room", {"carpet", "lamp"}),
    "playroom": Room("the playroom", {"carpet", "toys"}),
}

ANIMALS = {
    "pup": {"species": "puppy", "name": "Pip"},
    "cat": {"species": "kitten", "name": "Mina"},
    "bunny": {"species": "bunny", "name": "Toby"},
    "bear": {"species": "bear cub", "name": "Momo"},
    "fox": {"species": "fox kit", "name": "Luna"},
}

HELPERS = {
    "mouse": {"species": "mouse", "name": "Nib"},
    "bird": {"species": "bird", "name": "Bea"},
    "squirrel": {"species": "squirrel", "name": "Tuck"},
}

PROBLEMS = {
    "stain": Problem(
        id="stain",
        label="a muddy stain on the carpet",
        mess="mud",
        clue="brown paw prints",
        fix="wipe the spot with warm water and a cloth",
        risk="the carpet will look dirty",
        solved_by="careful cleaning",
    ),
    "snag": Problem(
        id="snag",
        label="a loose thread in the carpet",
        mess="snag",
        clue="a tiny loop near the edge",
        fix="trim the thread and tuck it flat",
        risk="the thread might pull more carpet loose",
        solved_by="gentle fixing",
    ),
    "smell": Problem(
        id="smell",
        label="a funny smell coming from the carpet",
        mess="smell",
        clue="a damp spot hidden under a cushion",
        fix="move the cushion and air the room",
        risk="the room will stay unpleasant",
        solved_by="smart searching",
    ),
}

ROOM_ORDER = ["den", "living_room", "playroom"]
PROBLEM_ORDER = ["stain", "snag", "smell"]


# ---------------------------------------------------------------------------
# Reasoning / simulation
# ---------------------------------------------------------------------------

def validate_combo(room: Room, problem: Problem) -> bool:
    return "carpet" in room.features


def select_story_parts(params: StoryParams, rng: random.Random) -> tuple[Room, Problem, Entity, Entity]:
    if params.room not in ROOMS:
        raise StoryError(f"unknown room: {params.room}")
    if params.problem not in PROBLEMS:
        raise StoryError(f"unknown problem: {params.problem}")
    if params.hero not in ANIMALS:
        raise StoryError(f"unknown hero animal: {params.hero}")
    if params.helper not in HELPERS:
        raise StoryError(f"unknown helper animal: {params.helper}")

    room = ROOMS[params.room]
    problem = PROBLEMS[params.problem]
    if not validate_combo(room, problem):
        raise StoryError("this story needs a carpeted room")

    hero_cfg = ANIMALS[params.hero]
    helper_cfg = HELPERS[params.helper]
    hero = Entity(id="hero", kind="animal", species=hero_cfg["species"], name=hero_cfg["name"])
    helper = Entity(id="helper", kind="animal", species=helper_cfg["species"], name=helper_cfg["name"])
    return room, problem, hero, helper


def simulate(world: World) -> None:
    hero = world.hero
    helper = world.helper
    problem = world.problem

    world.say(f"{hero.cap_name()} was a small {hero.species} who loved to explore the room.")
    world.say(f"One afternoon, {hero.cap_name()} spotted {problem.label} near the carpet.")
    world.say(f"{helper.cap_name()} came closer and looked at the clue: {problem.clue}.")
    world.para()

    hero.memes["worry"] = 1.0
    world.psych_worry = 1.0
    world.carpet_mess = 1.0
    world.say(
        f"{hero.cap_name()} felt a little psych worried, because {problem.risk}."
    )
    world.say(
        f"{helper.cap_name()} did not panic. Instead, {helper.cap_name()} said, "
        f"\"Let's solve it step by step.\""
    )
    world.para()

    world.say(f"First, they found the problem by following the clue to the carpet.")
    world.say(f"Then they used {problem.fix} as their plan.")
    world.say(f"{hero.cap_name()} held the cloth while {helper.cap_name()} lifted the edge.")
    world.carpet_mess = 0.0
    world.psych_worry = 0.0
    world.solved = True
    world.say(
        f"At last, the carpet was neat again, and the room felt calm and safe."
    )
    world.say(
        f"{hero.cap_name()} sat beside {helper.cap_name()} and smiled at the tidy carpet."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        problem=problem,
        room=world.room,
        solved=world.solved,
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------

def generate_story(world: World) -> str:
    simulate(world)
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].cap_name()
    helper = f["helper"].cap_name()
    problem = f["problem"].label
    room = f["room"].name
    return [
        f"Write a short animal story about {hero} and {helper} solving {problem} in {room}.",
        f"Tell a gentle problem-solving tale where a carpet causes a small worry and two animals fix it together.",
        f"Write a child-friendly story with a carpet, a psych worry, and a clever fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].cap_name()
    helper = f["helper"].cap_name()
    problem = f["problem"]
    return [
        QAItem(
            question=f"What problem did {hero} find near the carpet?",
            answer=f"{hero} found {problem.label}.",
        ),
        QAItem(
            question=f"Why did {hero} feel psych worried?",
            answer=f"{hero} felt psych worried because {problem.risk}.",
        ),
        QAItem(
            question=f"How did {hero} and {helper} solve the problem?",
            answer=f"They solved it by {problem.fix}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a carpet?",
            answer="A carpet is a soft covering on the floor that makes a room feel cozy.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to figure out what is wrong and fix it.",
        ),
        QAItem(
            question="What does worried mean?",
            answer="Worried means feeling uneasy because something might go wrong.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
room_has_carpet(R) :- carpet_room(R).
problem_possible(P) :- problem(P).
valid_story(R,P,H,L) :- room_has_carpet(R), problem_possible(P), hero(H), helper(L).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        if "carpet" in room.features:
            lines.append(asp.fact("carpet_room", rid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for hid in ANIMALS:
        lines.append(asp.fact("hero", hid))
    for lid in HELPERS:
        lines.append(asp.fact("helper", lid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {
        (rid, pid, hid, lid)
        for rid, room in ROOMS.items()
        if "carpet" in room.features
        for pid in PROBLEMS
        for hid in ANIMALS
        for lid in HELPERS
    }
    clingo_set = set(asp_valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if clingo_set - python_set:
        print(" only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print(" only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Q&A / trace / CLI
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    hero = world.hero
    helper = world.helper
    lines = ["--- world model state ---"]
    lines.append(f"room={world.room.name} features={sorted(world.room.features)}")
    lines.append(f"hero={hero.cap_name()} species={hero.species} memes={hero.memes} meters={hero.meters}")
    lines.append(f"helper={helper.cap_name()} species={helper.species} memes={helper.memes} meters={helper.meters}")
    lines.append(f"problem={world.problem.id} solved={world.solved} carpet_mess={world.carpet_mess} psych_worry={world.psych_worry}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: carpet, psych, and problem solving.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero", choices=ANIMALS)
    ap.add_argument("--helper", choices=HELPERS)
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for rid, room in ROOMS.items():
        if "carpet" not in room.features:
            continue
        for pid in PROBLEMS:
            for hid in ANIMALS:
                for lid in HELPERS:
                    combos.append((rid, pid, hid, lid))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos
              if (args.room is None or c[0] == args.room)
              and (args.problem is None or c[1] == args.problem)
              and (args.hero is None or c[2] == args.hero)
              and (args.helper is None or c[3] == args.helper)]
    if not combos:
        raise StoryError("no valid story matches the chosen options")
    room, problem, hero, helper = rng.choice(sorted(combos))
    return StoryParams(room=room, problem=problem, hero=hero, helper=helper, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    room, problem, hero, helper = select_story_parts(params, rng)
    world = World(room=room, hero=hero, helper=helper, problem=problem)
    story = generate_story(world)
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print(" ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for rid, pid, hid, lid in valid_combos():
            params = StoryParams(room=rid, problem=pid, hero=hid, helper=lid, seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            p = sample.params
            header = f"### {p.hero} + {p.helper} in {p.room} ({p.problem})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
