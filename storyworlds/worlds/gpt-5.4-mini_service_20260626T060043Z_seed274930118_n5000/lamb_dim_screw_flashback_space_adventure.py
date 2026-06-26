#!/usr/bin/env python3
"""
A small story world about a space adventure with a dim lamp, a loose screw,
and a helpful flashback to an earlier repair.

The world stays tiny and classical:
- one ship
- one crew member
- one important light
- one loose screw
- a remembered past fix that becomes the solution
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "pilot"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    label: str
    detail: str


@dataclass
class Problem:
    label: str
    cause: str
    effect: str
    fix: str
    flashback_hint: str


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    rank: str
    ship: str
    device: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "orbit": Place(
        label="orbit",
        detail="The ship floated in quiet orbit above a blue moon.",
    ),
    "asteroid": Place(
        label="asteroid field",
        detail="Tiny rocks drifted past the windows like slow silver rain.",
    ),
    "distant": Place(
        label="distant station",
        detail="A bright station blinked far away, like a tiny star with doors.",
    ),
}

PROBLEMS = {
    "dim_lamp": Problem(
        label="dim lamp",
        cause="a loose screw kept the lamp from shining right",
        effect="the cabin light went dim and sleepy",
        fix="tighten the screw with a tiny wrench",
        flashback_hint="they had already done this once before in a small training room",
    ),
}

HERO_NAMES = ["Nova", "Luna", "Milo", "Iris", "Zed", "Aria"]
HERO_TYPES = ["girl", "boy"]
RANKS = ["captain", "pilot", "mechanic", "engineer"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(place: str, problem: str, device: str) -> bool:
    return place in PLACES and problem == "dim_lamp" and device == "screw"


def explain_rejection(place: str, problem: str, device: str) -> str:
    if problem != "dim_lamp":
        return "(No story: this world only tells the dim lamp and loose screw space tale.)"
    if device != "screw":
        return "(No story: the fix must be a screw, because the lamp is dim from a loose screw.)"
    if place not in PLACES:
        return "(No story: that setting is not part of this tiny shipboard adventure.)"
    return "(No story: the requested setup does not make a reasonable space-adventure problem.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def _setup(world: World) -> None:
    ship = world.add(Entity(
        id="ship",
        kind="thing",
        type="ship",
        label=world.facts["ship"],
        phrase=f"the ship {world.facts['ship']}",
    ))
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=world.facts["hero_type"],
        label=world.facts["hero_name"],
    ))
    lamp = world.add(Entity(
        id="lamp",
        kind="thing",
        type="lamp",
        label="lamp",
        phrase="the cabin lamp",
        caretaker=hero.id,
    ))
    screw = world.add(Entity(
        id="screw",
        kind="thing",
        type="screw",
        label="screw",
        phrase="a tiny screw",
        caretaker=hero.id,
    ))

    ship.meters["distance"] = 1.0
    lamp.meters["light"] = 0.2
    screw.meters["looseness"] = 1.0
    hero.memes["care"] = 1.0


def _tell_flashback(world: World) -> None:
    hero = world.get("hero")
    world.say(
        f"Long before this trip, {hero.label} had learned something important "
        f"in a small training room on the ship."
    )
    world.say(
        f"{hero.pronoun().capitalize()} remembered how the lamp had flickered "
        f"when the screw was loose, and how a careful twist had made it bright again."
    )


def _problem(world: World) -> None:
    hero = world.get("hero")
    lamp = world.get("lamp")
    screw = world.get("screw")
    problem = PROBLEMS["dim_lamp"]

    lamp.meters["light"] = 0.1
    screw.meters["looseness"] = 1.0
    hero.memes["worry"] = 1.0

    world.say(
        f"On this trip, the {problem.label} gave the cabin a sleepy glow."
    )
    world.say(
        f"It happened because {problem.cause}, and soon {problem.effect}."
    )
    world.say(
        f"{hero.label} frowned, because the ship needed a bright lamp to read the map and keep watch."
    )


def _flashback_turn(world: World) -> None:
    hero = world.get("hero")
    world.say(
        f"Then {hero.label} had a flashback."
    )
    _tell_flashback(world)
    hero.memes["remembered"] = 1.0


def _fix(world: World) -> None:
    hero = world.get("hero")
    lamp = world.get("lamp")
    screw = world.get("screw")
    problem = PROBLEMS["dim_lamp"]

    screw.meters["looseness"] = 0.0
    lamp.meters["light"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["pride"] = 1.0

    world.say(
        f"{hero.label} fetched a tiny wrench and carefully chose the right screw."
    )
    world.say(
        f"With one steady turn, {problem.fix}, and the lamp glowed bright again."
    )
    world.say(
        f"The whole cabin woke up in warm light, and the ship could keep sailing through the dark."
    )


def _ending(world: World) -> None:
    hero = world.get("hero")
    world.say(
        f"At the end, {hero.label} smiled at the bright cabin and kept the wrench near the map table, just in case."
    )
    world.say(
        f"The ship drifted on, and the little light stayed strong."
    )


def tell(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    world.facts.update(
        place=params.place,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        rank=params.rank,
        ship=params.ship,
        device=params.device,
    )
    _setup(world)
    world.say(world.place.detail)
    world.say(
        f"On the ship {params.ship}, {params.hero_name} was the {params.rank} of the crew."
    )
    world.say(
        f"{params.hero_name} liked quiet space shifts, stars outside the window, and solving small ship problems."
    )
    world.para()
    _problem(world)
    world.para()
    _flashback_turn(world)
    world.para()
    _fix(world)
    world.para()
    _ending(world)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(orbit).
place(asteroid).
place(distant).

problem(dim_lamp).
device(screw).

valid(Place,Problem,Device) :- place(Place), problem(Problem), device(Device),
                               Place = orbit, Problem = dim_lamp, Device = screw.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    lines.append(asp.fact("problem", "dim_lamp"))
    lines.append(asp.fact("device", "screw"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {("orbit", "dim_lamp", "screw")}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid() ({len(cl)} combo).")
        return 0
    print("MISMATCH between clingo and python valid combos:")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short space-adventure story for a small child with a dim lamp and a remembered fix.',
        f"Tell a story where {f['hero_name']}, the {f['rank']}, notices a dim lamp on the ship {f['ship']} and remembers how to fix it.",
        "Write a simple space story that includes a flashback and ends with the cabin light shining again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero_name"]
    rank = f["rank"]
    ship = f["ship"]
    return [
        QAItem(
            question=f"Who was the story about on the ship {ship}?",
            answer=f"It was about {hero}, who served as the {rank} on the ship {ship}.",
        ),
        QAItem(
            question="What went wrong in the cabin?",
            answer="The cabin lamp went dim because a screw was loose.",
        ),
        QAItem(
            question="How did the problem get fixed?",
            answer="The hero remembered an earlier repair, then used a tiny wrench to tighten the screw.",
        ),
        QAItem(
            question="What made the hero think of the solution?",
            answer="A flashback reminded the hero of the earlier time when the lamp had flickered for the same reason.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a screw?",
            answer="A screw is a small metal piece with a twisty groove that helps hold things together when you turn it.",
        ),
        QAItem(
            question="What does dim mean?",
            answer="Dim means not very bright, so a dim light can make a room feel sleepy or shadowy.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that shows something that happened earlier, before the present moment.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with a dim lamp, a screw, and a flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--name")
    ap.add_argument("--rank", choices=RANKS)
    ap.add_argument("--gender", choices=HERO_TYPES)
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    if not valid_combo(place, "dim_lamp", "screw"):
        raise StoryError(explain_rejection(place, "dim_lamp", "screw"))
    hero_type = args.gender or rng.choice(HERO_TYPES)
    hero_name = args.name or rng.choice(HERO_NAMES)
    rank = args.rank or rng.choice(RANKS)
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        rank=rank,
        ship="Lamb-Dim",
        device="screw",
    )


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


CURATED = [
    StoryParams(place="orbit", hero_name="Nova", hero_type="girl", rank="engineer", ship="Lamb-Dim", device="screw"),
    StoryParams(place="asteroid", hero_name="Milo", hero_type="boy", rank="pilot", ship="Lamb-Dim", device="screw"),
    StoryParams(place="distant", hero_name="Iris", hero_type="girl", rank="captain", ship="Lamb-Dim", device="screw"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print("  ", t)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
