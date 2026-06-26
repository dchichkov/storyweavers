#!/usr/bin/env python3
"""
A standalone story world for a tiny pirate tale about a maze, a cautionary
mistake, and a lesson learned.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pirate", "captain"}
        if self.type in female and self.type not in {"pirate", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male or self.type in {"pirate", "captain"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Maze:
    name: str
    corridors: list[str]
    trap_corridor: str
    treasure_room: str
    start: str
    exit: str
    lantern_safe: bool = True
    map_safe: bool = True


@dataclass
class StoryParams:
    maze: str
    hero_name: str
    hero_type: str
    captain_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, maze: Maze) -> None:
        self.maze = maze
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace: list[str] = []
        self.facts: dict = {}

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
        w = World(self.maze)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        return w


def _r_lost(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.memes.get("confused", 0) < THRESHOLD:
        return out
    sig = ("lost",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["distance_from_exit"] = 3
    out.append("The maze turned twisty, and the pirate could not tell one turn from the next.")
    return out


def _r_trap(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.meters.get("distance_from_exit", 0) < THRESHOLD:
        return out
    if hero.memes.get("careful", 0) >= THRESHOLD:
        return out
    sig = ("trap",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["scraped"] = 1
    hero.memes["shaken"] = 1
    out.append("A hidden plank creaked, and the pirate got a nasty scrape.")
    return out


def _r_learned(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.memes.get("shaken", 0) < THRESHOLD:
        return out
    if hero.memes.get("learned", 0) >= THRESHOLD:
        return out
    sig = ("learned",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["learned"] = 1
    out.append("The pirate learned that a maze is no place to rush without a map and a lantern.")
    return out


def _r_find_exit(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.memes.get("learned", 0) < THRESHOLD:
        return out
    sig = ("exit",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["distance_from_exit"] = 0
    hero.memes["relief"] = 1
    out.append("With the lantern held high and the map opened wide, the pirate found the safe way out.")
    return out


RULES = [_r_lost, _r_trap, _r_learned, _r_find_exit]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


MAZES = {
    "sea_maze": Maze(
        name="the sea-cave maze",
        corridors=["shell hall", "anchor bend", "kraken corner", "tide tunnel"],
        trap_corridor="kraken corner",
        treasure_room="gold room",
        start="shell hall",
        exit="tide tunnel",
    ),
    "vine_maze": Maze(
        name="the jungle maze",
        corridors=["leaf lane", "vine turn", "stone fork", "sun gap"],
        trap_corridor="stone fork",
        treasure_room="parrot room",
        start="leaf lane",
        exit="sun gap",
    ),
}

NAMES = ["Milo", "Nia", "Jules", "Pip", "Rory", "Tess"]
TYPES = ["boy", "girl"]
CAPTAINS = ["Blackfin", "Redbeard", "Silverhook", "Captain Mire"]


def tell(params: StoryParams) -> World:
    maze = MAZES[params.maze]
    world = World(maze)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    captain = world.add(Entity(id="captain", kind="character", type="pirate", label=params.captain_name))
    map_item = world.add(Entity(id="map", type="thing", label="map", phrase="a folded map", owner=hero.id))
    lantern = world.add(Entity(id="lantern", type="thing", label="lantern", phrase="a bright lantern", owner=hero.id))
    world.facts.update(hero=hero, captain=captain, map=map_item, lantern=lantern, maze=maze)

    world.say(
        f"{hero.label} was a little {hero.type} pirate who loved adventures on the whispering sea."
    )
    world.say(
        f"{captain.label} gave {hero.label} a folded map and a bright lantern before the crew went into {maze.name}."
    )
    world.say(
        f"{hero.label} wanted to dash ahead and prove {hero.pronoun('object')} was brave."
    )
    world.para()

    hero.memes["confused"] = 1
    world.say(
        f"At first, {hero.label} ignored the map and turned down the wrong corridor."
    )
    propagate(world, narrate=True)
    world.say(
        f"The stones echoed like giggles, and soon {hero.label} could not see the exit."
    )
    world.para()

    hero.memes["careful"] = 1
    world.say(
        f"{captain.label} held up the lantern and said, 'Slow down now, matey. A maze teaches a careful pirate best.'"
    )
    hero.memes["shaken"] = 1
    propagate(world, narrate=True)
    world.say(
        f"{hero.label} opened the map, kept the lantern high, and followed the safe turns."
    )
    propagate(world, narrate=True)
    world.say(
        f"In the end, {hero.label} stepped out of {maze.name} with a wiser heart, and {hero.pronoun('possessive')} boots were still dry."
    )

    world.facts["resolved"] = hero.memes.get("relief", 0) >= THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short pirate tale for children about a maze, a mistake, and a lesson learned.",
        f"Tell a cautionary story where {f['hero'].label} ignores a map in {f['maze'].name} and then learns to be careful.",
        "Write a gentle pirate adventure that ends with a wiser child choosing the safe path out of a maze.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    captain: Entity = f["captain"]
    maze: Maze = f["maze"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.label}, a little {hero.type} pirate, and {captain.label}, who helps guide the way."
        ),
        QAItem(
            question=f"What went wrong when {hero.label} first went into {maze.name}?",
            answer=f"{hero.label} ignored the map, took the wrong corridor, and got lost in {maze.name}."
        ),
        QAItem(
            question=f"What lesson did {hero.label} learn in the end?",
            answer=f"{hero.label} learned to slow down, listen to the captain, and follow the map and lantern in a maze."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.label} finding the safe way out of {maze.name} and leaving wiser than before."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a maze?",
            answer="A maze is a place with many turns and paths, so you have to choose carefully to find the exit."
        ),
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives light so you can see where you are going in the dark."
        ),
        QAItem(
            question="Why is it smart to use a map?",
            answer="A map shows the way, so it helps you avoid getting lost."
        ),
        QAItem(
            question="Why should someone be careful in a maze?",
            answer="A maze can have hidden turns and traps, so moving carefully helps keep you safe."
        ),
    ]


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("character", "hero"),
        asp.fact("character", "captain"),
        asp.fact("tool", "map"),
        asp.fact("tool", "lantern"),
    ]
    for maze_id, maze in MAZES.items():
        lines.append(asp.fact("maze", maze_id))
        lines.append(asp.fact("has_exit", maze_id, maze.exit))
        lines.append(asp.fact("trap", maze_id, maze.trap_corridor))
    return "\n".join(lines)


ASP_RULES = r"""
lost(H) :- ignores_map(H), enters_maze(H).
shaken(H) :- lost(H), meets_trap(H).
learns_care(H) :- shaken(H).
finds_exit(H) :- learns_care(H), uses_map(H), uses_lantern(H).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show lost/1. #show learns_care/1. #show finds_exit/1."))
    atoms = {str(a) for a in model}
    expected = set()
    if atoms == expected:
        print("OK: ASP twin loaded.")
        return 0
    print("ASP check completed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld: maze, caution, lesson learned.")
    ap.add_argument("--maze", choices=MAZES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=TYPES)
    ap.add_argument("--captain", choices=CAPTAINS)
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
    maze = args.maze or rng.choice(list(MAZES))
    gender = args.gender or rng.choice(TYPES)
    name = args.name or rng.choice(NAMES)
    captain = args.captain or rng.choice(CAPTAINS)
    return StoryParams(maze=maze, hero_name=name, hero_type=gender, captain_name=captain)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
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
    StoryParams(maze="sea_maze", hero_name="Milo", hero_type="boy", captain_name="Captain Mire"),
    StoryParams(maze="vine_maze", hero_name="Nia", hero_type="girl", captain_name="Silverhook"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show lost/1. #show learns_care/1. #show finds_exit/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show lost/1. #show learns_care/1. #show finds_exit/1."))
        return

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
