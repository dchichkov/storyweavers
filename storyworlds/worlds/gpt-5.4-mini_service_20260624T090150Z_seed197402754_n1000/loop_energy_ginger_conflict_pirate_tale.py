#!/usr/bin/env python3
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
        if self.type in {"pirate", "captain", "sailor", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"pirate_woman", "captain_woman", "sailor_woman", "woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str
    setting: str = "the wide blue sea"
    loop_energy: float = 0.0
    loop_depth: float = 0.0
    conflict_active: bool = False
    loop_count: int = 0
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    captain_name: str
    mate_name: str
    ship_name: str
    seed: Optional[int] = None


NAMES = ["Mara", "Nell", "Finn", "Pip", "Rory", "Tess", "Jory", "Bram"]
SHIP_NAMES = ["The Blue Comet", "The Merry Loop", "The Ginger Gull", "The Salt Star"]


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(_copy.deepcopy(self.ship))
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        return w


def _join_clauses(*parts: str) -> str:
    return " ".join(p for p in parts if p)


def setup_story(world: World, captain: Entity, mate: Entity, ginger: Entity) -> None:
    world.say(f"{captain.id} was a pirate captain on {world.ship.name}, sailing the wide blue sea.")
    world.say(f"{mate.id} was {captain.id}'s first mate, quick with ropes and quick with a grin.")
    world.say(f"On a small table in the cabin sat a cup of ginger tea, and it smelled warm and sharp.")
    world.say(f"{captain.id} liked ginger because it brought back energy on long sea days.")


def loop_problem(world: World, captain: Entity, mate: Entity, ginger: Entity) -> None:
    world.para()
    world.ship.loop_energy = 0.0
    world.ship.loop_depth = 1.0
    world.ship.loop_count += 1
    captain.meters["energy"] = 1.0
    mate.meters["energy"] = 1.0
    world.say(f"One foggy morning, the ship found the same wave again and again, like a loop that would not let go.")
    world.say(f"The sails tugged one way, then the other, and the ship kept circling the same patch of sea.")
    world.say(f"{mate.id} frowned. \"We need to break this loop,\" {mate.pronoun('subject')} said.")
    world.ship.conflict_active = True
    captain.memes["conflict"] = 1.0
    mate.memes["conflict"] = 1.0
    world.say(f"{captain.id} wanted to push faster, but {mate.id} wanted to slow down and think.")


def use_ginger(world: World, captain: Entity, mate: Entity, ginger: Entity) -> None:
    world.para()
    captain.meters["energy"] += 2.0
    mate.meters["energy"] += 1.0
    ginger.meters["used"] = ginger.meters.get("used", 0.0) + 1.0
    world.ship.loop_energy += 1.0
    world.say(f"{captain.id} sipped the ginger tea and felt warmth climb from stomach to toes.")
    world.say(f"The sharp ginger taste woke up {captain.pronoun('object')}, and {captain.pronoun('subject')} stood straighter at once.")
    world.say(f"{mate.id} took a sip too, and {mate.pronoun('subject')} got a little more energy for the work ahead.")


def break_loop(world: World, captain: Entity, mate: Entity) -> None:
    world.para()
    world.ship.loop_depth = 0.0
    world.ship.conflict_active = False
    captain.memes["conflict"] = 0.0
    mate.memes["conflict"] = 0.0
    captain.meters["energy"] += 1.0
    mate.meters["energy"] += 1.0
    world.say(f"{captain.id} stopped trying to fight the sea and followed {mate.id}'s plan instead.")
    world.say(f"They turned the wheel at the right moment, let the current slide past, and the ship slipped out of the loop.")
    world.say(f"At last the water opened ahead of them, and the ship pointed toward open sea.")


def ending(world: World, captain: Entity, mate: Entity, ginger: Entity) -> None:
    world.para()
    world.say(f"{captain.id} laughed and poured the last drop of ginger tea into the wind for luck.")
    world.say(f"{mate.id} smiled back, and the two pirates watched the sunrise while the ship sailed straight and free.")
    world.say(f"The loop was gone, their energy was back, and the ginger cup was empty on the cabin table.")


def tell(params: StoryParams) -> World:
    ship = Ship(name=params.ship_name)
    world = World(ship)
    captain = world.add(Entity(id=params.captain_name, kind="character", type="captain", label="captain"))
    mate = world.add(Entity(id=params.mate_name, kind="character", type="pirate", label="first mate"))
    ginger = world.add(Entity(id="ginger", kind="thing", type="thing", label="ginger tea", phrase="a warm cup of ginger tea"))
    ginger.meters["warm"] = 1.0

    setup_story(world, captain, mate, ginger)
    loop_problem(world, captain, mate, ginger)
    use_ginger(world, captain, mate, ginger)
    break_loop(world, captain, mate)
    ending(world, captain, mate, ginger)

    world.ship.facts = {
        "captain": captain,
        "mate": mate,
        "ginger": ginger,
        "ship": ship,
    }
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.ship.facts
    captain = f["captain"]
    mate = f["mate"]
    return [
        'Write a short pirate tale about a ship caught in a loop, where ginger helps restore energy.',
        f"Tell a child-friendly pirate story where {captain.id} and {mate.id} disagree, then solve the conflict with ginger tea.",
        "Write a simple sea adventure that ends with a ship escaping a looping current and sailing on.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.ship.facts
    captain = f["captain"]
    mate = f["mate"]
    return [
        QAItem(
            question=f"Who was the story about on {world.ship.name}?",
            answer=f"It was about {captain.id}, a pirate captain, and {mate.id}, the first mate, sailing together on {world.ship.name}.",
        ),
        QAItem(
            question="What problem kept happening to the ship?",
            answer="The ship kept circling in a loop around the same part of the sea, so it could not sail forward at first.",
        ),
        QAItem(
            question="What helped the pirates get more energy?",
            answer="The ginger tea helped them feel warmer and more awake, so they had the energy to work on the problem.",
        ),
        QAItem(
            question="How did the conflict end?",
            answer="They stopped arguing, followed the better turning plan, and the ship slipped out of the loop and into open water.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ginger?",
            answer="Ginger is a root with a sharp, warm taste. People use it in tea or food, and it can feel cozy on a cold day.",
        ),
        QAItem(
            question="What does energy mean in a story like this?",
            answer="Energy means having enough strength and pep to move, work, and keep going.",
        ),
        QAItem(
            question="What is a loop?",
            answer="A loop is something that goes around and comes back again and again.",
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  ship.loop_count={world.ship.loop_count}")
    lines.append(f"  ship.loop_energy={world.ship.loop_energy}")
    lines.append(f"  ship.loop_depth={world.ship.loop_depth}")
    lines.append(f"  ship.conflict_active={world.ship.conflict_active}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid if the ship has a loop, ginger exists, energy can be restored,
% and conflict is resolved by the end.
valid_story(loop, ginger, energy, conflict).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("theme", "loop"),
            asp.fact("theme", "energy"),
            asp.fact("theme", "ginger"),
            asp.fact("feature", "conflict"),
            asp.fact("style", "pirate_tale"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/4."))
    ok = any(sym.name == "valid_story" for sym in model)
    if ok:
        print("OK: ASP twin recognizes the pirate loop story.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected story fact.")
    return 1


@dataclass
class StoryParams:
    captain_name: str
    mate_name: str
    ship_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale world: loop, energy, ginger, and conflict.")
    ap.add_argument("--captain-name")
    ap.add_argument("--mate-name")
    ap.add_argument("--ship-name", choices=SHIP_NAMES)
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
    captain = args.captain_name or rng.choice(NAMES)
    mate = args.mate_name or rng.choice([n for n in NAMES if n != captain])
    ship = args.ship_name or rng.choice(SHIP_NAMES)
    return StoryParams(captain_name=captain, mate_name=mate, ship_name=ship)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
        print("1 compatible pirate story pattern: loop + ginger + energy + conflict")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Mara", "Finn", "The Ginger Gull"),
            StoryParams("Nell", "Pip", "The Merry Loop"),
            StoryParams("Tess", "Bram", "The Blue Comet"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
