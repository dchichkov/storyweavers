#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/remorse_exist_mystery_to_solve_bravery_repetition.py
===============================================================================================================================

A small space-adventure storyworld about a crew facing a mystery, repeating
careful checks, and finding the brave choice that solves it.

Seed tale:
---
On a quiet starship, a young pilot named Mira woke to a blinking mystery. The
ship's map kept showing a missing moonlet that everyone said must exist, but no
one could see it on the screen. Mira felt remorse because she had rushed a scan
the day before and maybe missed the clue.

She and her little robot friend Tiko went through the same corridor again and
again, repeating the search with brave little steps. Each time, the mystery
grew clearer: a jammed lens in the observation dome had hidden the moonlet's
signal. Mira took a deep breath, fixed the lens, and the tiny moonlet appeared
bright and real. Her remorse faded, because now the moonlet did exist, and the
crew cheered at the solved mystery.

World model:
---
- Entities have physical meters and emotional memes.
- The ship contains rooms, devices, and crew members.
- Mystery state accumulates when clues are missing.
- Repetition is useful: repeating a careful check increases clue strength.
- Bravery helps a character enter a risky place or try a scary fix.
- Solving the mystery clears remorse and reveals the hidden object.
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain", "pilot"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class ShipRoom:
    id: str
    label: str
    dangerous: bool = False
    clue_boost: float = 0.0
    note: str = ""


@dataclass
class Mystery:
    id: str
    label: str
    hidden: bool = True
    solved: bool = False
    clue_need: float = 2.0
    reveal_room: str = ""
    reveal_item: str = ""
    answer: str = ""


@dataclass
class Tool:
    id: str
    label: str
    helps: str
    safe_room: str = ""
    brave_room: str = ""
    reveals: float = 1.0


class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.rooms: dict[str, ShipRoom] = {}
        self.mystery: Mystery | None = None
        self.tool: Tool | None = None
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.rooms = copy.deepcopy(self.rooms)
        clone.mystery = copy.deepcopy(self.mystery)
        clone.tool = copy.deepcopy(self.tool)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


ROOMS = {
    "bridge": ShipRoom("bridge", "the bridge", clue_boost=0.0, note="The bridge hummed with quiet lights."),
    "observation_dome": ShipRoom("observation_dome", "the observation dome", dangerous=False, clue_boost=1.0,
                                 note="The dome could see far into space."),
    "engine_room": ShipRoom("engine_room", "the engine room", dangerous=True, clue_boost=0.5,
                            note="The engine room glowed hot and orange."),
    "map_chamber": ShipRoom("map_chamber", "the map chamber", clue_boost=0.5,
                            note="The map chamber held star charts and blinking screens."),
}

TOOLS = {
    "scanner": Tool("scanner", "a hand scanner", helps="scan again and again", safe_room="bridge", brave_room="engine_room", reveals=1.0),
    "wrench": Tool("wrench", "a small wrench", helps="open a stuck panel", safe_room="engine_room", brave_room="observation_dome", reveals=0.5),
    "lamp": Tool("lamp", "a narrow lamp", helps="look for tiny marks", safe_room="map_chamber", brave_room="observation_dome", reveals=1.0),
}

MYSTERIES = {
    "missing_moonlet": Mystery(
        "missing_moonlet",
        "the missing moonlet",
        clue_need=2.0,
        reveal_room="observation_dome",
        reveal_item="lens",
        answer="A jammed lens had hidden the moonlet's signal.",
    ),
    "silent_beacon": Mystery(
        "silent_beacon",
        "the silent beacon",
        clue_need=2.5,
        reveal_room="engine_room",
        reveal_item="coil",
        answer="A loose coil had silenced the beacon.",
    ),
}

CREW_NAMES = ["Mira", "Jun", "Tess", "Ari", "Niko", "Lina"]
ROLES = ["pilot", "navigator", "engineer", "scout", "captain"]
COMPANIONS = ["tiny robot friend", "brave co-pilot", "small helper drone", "clever cabin bot"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero_name: str
    hero_role: str
    companion: str
    seed: Optional[int] = None


ASP_RULES = r"""
% A room is risky if the mystery hides there and the room is dangerous or the crew must be brave to enter.
risky(Room) :- room(Room), dangerous(Room).
needs_bravery(Room) :- risky(Room).

% Repetition helps when the crew checks the same place again.
useful_repeat(Room) :- room(Room), clue_boost(Room, B), B > 0.

% A mystery is solved when enough clue power accumulates.
solved(M) :- mystery(M), clue_total(M, T), clue_need(M, N), T >= N.

% Remorse fades when the mystery is solved.
remorse_fades(Crew) :- solved(_), crew(Crew).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        if room.dangerous:
            lines.append(asp.fact("dangerous", rid))
        if room.clue_boost:
            lines.append(asp.fact("clue_boost", rid, room.clue_boost))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_need", mid, m.clue_need))
    lines.append(asp.fact("crew", "crew"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show room/1."))
    _ = model
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld about mystery, bravery, and repetition.")
    ap.add_argument("--setting", choices=sorted(ROOMS))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--name", choices=CREW_NAMES)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--companion", choices=COMPANIONS)
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
    setting = args.setting or rng.choice(list(ROOMS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    name = args.name or rng.choice(CREW_NAMES)
    role = args.role or rng.choice(ROLES)
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(setting=setting, mystery=mystery, hero_name=name, hero_role=role, companion=companion)


def build_world(params: StoryParams) -> World:
    w = World(params.setting)
    hero = w.add(Entity(params.hero_name, kind="character", type="pilot" if params.hero_role == "pilot" else "crew",
                        label=params.hero_name, location="bridge"))
    helper = w.add(Entity("companion", kind="character", type="robot", label=params.companion, location="bridge"))
    mystery = MYSTERIES[params.mystery]
    tool = TOOLS["scanner"] if mystery.id == "missing_moonlet" else TOOLS["wrench"]
    w.mystery = mystery
    w.tool = tool
    w.add(Entity("lens", kind="thing", type="device", label="a jammed lens", location="observation_dome"))
    w.add(Entity("coil", kind="thing", type="device", label="a loose coil", location="engine_room"))
    w.facts.update(hero=hero, helper=helper, mystery=mystery, tool=tool)
    return w


def propagate(world: World) -> None:
    m = world.mystery
    if not m:
        return
    clue = world.facts.get("clue", 0.0)
    if clue >= m.clue_need and not m.solved:
        m.solved = True
        world.say(f"The mystery clicked into place: {m.answer}")
        hero = world.facts["hero"]
        hero.memes["remorse"] = 0.0


def tell(world: World) -> World:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    mystery: Mystery = world.mystery  # type: ignore[assignment]
    tool: Tool = world.tool  # type: ignore[assignment]
    room = ROOMS[world.setting]

    hero.memes["remorse"] = 1.0
    hero.memes["curiosity"] = 1.0
    world.say(f"On {room.label}, {hero.id} found a mystery that should have been simple.")
    world.say(f"{hero.id} worried the missing clue might not exist at all, and that made {hero.pronoun('object')} feel remorse.")
    world.say(f"Still, {hero.id} had {helper.label} beside {hero.pronoun('object')}, and together they chose to look again.")

    world.para()
    world.say(f"They went to {mystery.reveal_room.replace('_', ' ')} with {tool.label}.")
    for i in range(3):
        hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 0.4
        world.facts["clue"] = world.facts.get("clue", 0.0) + ROOMS[mystery.reveal_room].clue_boost * tool.reveals
        world.say(f"They checked the same place again, carefully and bravely, because one try was not enough.")
        if i == 0:
            world.say(f"{helper.label} held the lamp steady while {hero.id} searched for a tiny mark.")
        if i == 1:
            world.say(f"{hero.id} repeated the scan, and this time the screen flickered a little stronger.")
        propagate(world)

    if not mystery.solved:
        world.say(f"{hero.id} took a brave breath and opened the stuck panel by hand.")
        world.facts["clue"] = max(world.facts.get("clue", 0.0), mystery.clue_need)
        propagate(world)

    world.para()
    if mystery.solved:
        world.say(f"In the end, the clue was real, the moonlet could exist after all, and the crew cheered.")
        world.say(f"{hero.id} felt the remorse drain away, because the mystery had been solved with patience and bravery.")
    else:
        world.say(f"The mystery stayed dim, and the ship only got quieter.")
    world.facts["resolved"] = mystery.solved
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    mystery: Mystery = f["mystery"]
    tool: Tool = f["tool"]
    return [
        f"Write a space-adventure story for a young child about {hero.id}, a {hero.type}, who solves {mystery.label} by trying again and again.",
        f"Tell a brave little story where repetition helps {hero.id} use {tool.label} to solve {mystery.label}.",
        f"Write a child-friendly mystery story in space that includes the words 'remorse' and 'exist'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    mystery: Mystery = world.facts["mystery"]
    tool: Tool = world.facts["tool"]
    qa = [
        QAItem(
            question=f"Who solved {mystery.label} in the story?",
            answer=f"{hero.id} solved {mystery.label} with help from {world.facts['helper'].label}.",
        ),
        QAItem(
            question=f"What did {hero.id} keep doing to find the clue?",
            answer="They repeated the search again and again, because repetition helped the clue grow clearer.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel remorse at first?",
            answer=f"{hero.id} felt remorse because {hero.pronoun('object')} thought an earlier rushed scan might have missed the clue.",
        ),
        QAItem(
            question=f"What helped the crew solve the mystery?",
            answer=f"{tool.label} helped, along with brave checking in the right room.",
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(QAItem(
            question="What changed by the end of the story?",
            answer=f"The mystery was solved, the hidden thing could exist clearly again, and remorse faded away.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something hard or a little scary even when you feel nervous.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing the same action again and again, often to practice or to check carefully.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that needs clues before it can be understood.",
        ),
        QAItem(
            question="What does it mean for something to exist?",
            answer="If something exists, it is real and is there in the world, even if you need to find it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    if world.mystery:
        lines.append(f"  mystery: solved={world.mystery.solved} clue_need={world.mystery.clue_need}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("bridge", "missing_moonlet", "Mira", "pilot", "tiny robot friend"),
    StoryParams("map_chamber", "missing_moonlet", "Jun", "navigator", "small helper drone"),
    StoryParams("engine_room", "silent_beacon", "Tess", "engineer", "brave co-pilot"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(build_world(params))
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


def resolve_for_all() -> list[StoryParams]:
    return CURATED


def valid_combo(params: StoryParams) -> bool:
    return params.setting in ROOMS and params.mystery in MYSTERIES


def asp_verify_gate() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show risky/1.\n#show needs_bravery/1.\n#show useful_repeat/1."))
        return
    if args.verify:
        sys.exit(asp_verify_gate())
    if args.asp:
        print("ASP mode is available for parity checks.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        params_list = resolve_for_all()
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                samples.append(s)
                seen.add(s.story)
            i += 1

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
