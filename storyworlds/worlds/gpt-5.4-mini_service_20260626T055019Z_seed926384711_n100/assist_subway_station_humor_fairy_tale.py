#!/usr/bin/env python3
"""
A small story world for a fairy-tale subway station, with humor and assistance.

Premise:
- A shy little helper arrives at a subway station where a lost traveler, a stubborn
  suitcase, and a clock that insists on being late all need assistance.
- The turn comes when the helper tries the wrong kind of help first, making the
  station even more silly and crowded.
- The resolution arrives when the helper uses a simple, practical kind of
  assistance that gets everyone where they need to go.

This world is intentionally tiny: one domain, one kind of tension, one clean fix.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    kind: str
    label: str
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        feminine = {"girl", "woman", "mother", "queen", "princess"}
        masculine = {"boy", "man", "father", "king", "prince"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Station:
    name: str = "the subway station"
    platforms: list[str] = field(default_factory=lambda: ["Platform One", "Platform Two"])
    has_elevator: bool = True
    has_bench: bool = True
    has_map: bool = True


@dataclass
class Task:
    id: str
    verb: str
    attempt_verb: str
    needed: str
    funny_mishelp: str
    proper_help: str
    clue: str


@dataclass
class StoryParams:
    station: str = "subway_station"
    task: str = "find_ticket"
    helper_name: str = "Mira"
    helper_type: str = "girl"
    traveler_name: str = "Bram"
    traveler_type: str = "boy"
    seed: Optional[int] = None


class World:
    def __init__(self, station: Station) -> None:
        self.station = station
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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
        other = World(self.station)
        other.entities = dataclasses.replace(self.entities) if False else {}
        import copy
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.facts = dict(self.facts)
        return other


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

STATION = Station()

TASKS = {
    "find_ticket": Task(
        id="find_ticket",
        verb="find the lost ticket",
        attempt_verb="peek behind the ticket gate",
        needed="a careful eye and a calm plan",
        funny_mishelp="offered the ticket gate a cookie and asked it to remember",
        proper_help="look under the bench and ask the map clerk",
        clue="the ticket had fallen beside the bench",
    ),
    "carry_parcel": Task(
        id="carry_parcel",
        verb="carry a heavy parcel",
        attempt_verb="lift the parcel with a heroic grunt",
        needed="strong arms and a rolling cart",
        funny_mishelp="tied a ribbon around the parcel and called it lighter",
        proper_help="borrow the rolling cart from the station keeper",
        clue="the parcel was too heavy to lift alone",
    ),
    "guide_train": Task(
        id="guide_train",
        verb="guide a lost train rider",
        attempt_verb="wave in every direction at once",
        needed="clear signs and a kind voice",
        funny_mishelp="drew arrows on the floor with a banana peel",
        proper_help="walk to the map and point to the right platform",
        clue="the rider only needed the right platform number",
    ),
    "share_bench": Task(
        id="share_bench",
        verb="make room on the bench",
        attempt_verb="squeeze in by sitting on one tiny corner",
        needed="patience and a polite request",
        funny_mishelp="pretended to be a conductor and announced a bench parade",
        proper_help="ask the sleepy travelers to scoot over kindly",
        clue="one bench had enough room if everyone moved a little",
    ),
}

HELPERS = {
    "girl": ["Mira", "Lina", "Tess", "Nora"],
    "boy": ["Bram", "Finn", "Leo", "Pip"],
}

TRAVELERS = {
    "girl": ["Queen Dot", "Lila", "Mona"],
    "boy": ["Sir Tock", "Bram", "Gus"],
}


# ---------------------------------------------------------------------------
# Reasonableness gate and ASP twin
# ---------------------------------------------------------------------------

def task_is_reasonable(task: Task) -> bool:
    return task.id in TASKS


ASP_RULES = r"""
station(subway_station).
helper_kind(girl;boy).
traveler_kind(girl;boy).

task(find_ticket).
task(carry_parcel).
task(guide_train).
task(share_bench).

reasonable(T) :- task(T).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("station", "subway_station")]
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_tasks() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/1."))
    return sorted({args[0] for args in asp.atoms(model, "reasonable")})


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def _choose_name(pool: list[str], rng: random.Random) -> str:
    return rng.choice(pool)


def resolve_task(name: str) -> Task:
    if name not in TASKS:
        raise StoryError(f"Unknown task: {name}")
    return TASKS[name]


def choose_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    task = args.task or rng.choice(sorted(TASKS))
    if task not in TASKS:
        raise StoryError(f"Unknown task: {task}")
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    traveler_type = args.traveler_type or rng.choice(["girl", "boy"])
    helper_name = args.helper_name or _choose_name(HELPERS[helper_type], rng)
    traveler_name = args.traveler_name or _choose_name(TRAVELERS[traveler_type], rng)
    return StoryParams(
        station="subway_station",
        task=task,
        helper_name=helper_name,
        helper_type=helper_type,
        traveler_name=traveler_name,
        traveler_type=traveler_type,
    )


def build_world(params: StoryParams) -> World:
    task = resolve_task(params.task)
    world = World(STATION)
    helper = world.add(Entity(id="helper", kind="character", label=params.helper_name, type=params.helper_type))
    traveler = world.add(Entity(id="traveler", kind="character", label=params.traveler_name, type=params.traveler_type))
    stationkeeper = world.add(Entity(id="keeper", kind="character", label="the station keeper", type="woman"))
    ticket = world.add(Entity(id="ticket", kind="thing", label="a small paper ticket"))
    parcel = world.add(Entity(id="parcel", kind="thing", label="a very heavy parcel"))
    bench = world.add(Entity(id="bench", kind="thing", label="the long wooden bench"))
    map_ = world.add(Entity(id="map", kind="thing", label="the wall map"))

    helper.memes["kind"] = 1
    helper.memes["curious"] = 1
    traveler.memes["worry"] = 1

    world.facts.update(task=task, helper=helper, traveler=traveler, stationkeeper=stationkeeper,
                       ticket=ticket, parcel=parcel, bench=bench, map=map_)
    return world


def tell_story(world: World) -> None:
    task: Task = world.facts["task"]
    helper: Entity = world.facts["helper"]
    traveler: Entity = world.facts["traveler"]
    stationkeeper: Entity = world.facts["stationkeeper"]

    world.say(
        f"At the subway station, {helper.label} was a little helper with a bright scarf and a brave heart."
        f" {helper.label} liked to assist anyone who looked lost, because fairy-tale stations can be noisy places."
    )
    world.say(
        f"One shiny morning, {traveler.label} came in with a sigh and a wobble, because {task.clue}."
        f" {traveler.label} needed {task.needed}, and the station bell kept ding-dinging like a giggling spoon."
    )

    world.para()
    world.say(
        f"{helper.label} wanted to {task.verb}, so {helper.pronoun()} tried to {task.attempt_verb}."
        f" That was a funny sort of help, and it only made the people look in three different directions at once."
    )

    world.para()
    world.say(
        f"The station keeper smiled and said, \"Kind helper, the better way is to {task.proper_help}.\""
        f" Then {helper.label} remembered that real assistance is simple when it listens first."
    )
    world.say(
        f"{helper.label} did exactly that. Soon the station felt less wobbly, less tangled, and much more merry."
        f" {traveler.label} laughed, the keeper nodded, and even the clock seemed to stop being late for one tiny moment."
    )

    world.para()
    if task.id == "find_ticket":
        world.say(
            f"Together they found the ticket under the bench, where it had been hiding like a shy crumb."
            f" {traveler.label} tucked it safely away and thanked {helper.label} with a little bow."
        )
    elif task.id == "carry_parcel":
        world.say(
            f"Together they rolled the parcel onto the cart, and the parcel stopped pretending to be a mountain."
            f" {traveler.label} could push it with ease, and {helper.label} felt proud of the useful rescue."
        )
    elif task.id == "guide_train":
        world.say(
            f"Together they walked to the map and pointed to the right platform, and the lost rider's face turned sunny."
            f" The right train was waiting exactly where the map had promised."
        )
    elif task.id == "share_bench":
        world.say(
            f"Together they asked the sleepy travelers to scoot over, and the bench made enough room for everyone."
            f" The whole station rested in peace, which felt almost like a spell."
        )

    world.say(
        f"By evening, {helper.label} had learned that the best assistance at a subway station is not grand or noisy."
        f" It is gentle, clever, and just a little funny."
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    task: Task = world.facts["task"]
    helper: Entity = world.facts["helper"]
    traveler: Entity = world.facts["traveler"]
    return [
        'Write a short fairy tale about a helpful child at a subway station who learns that assistance works best when it is practical.',
        f"Tell a humorous story where {helper.label} tries to assist {traveler.label} with {task.verb} at the subway station.",
        f"Write a child-friendly fairy tale in a subway station that includes the word 'assist' and ends with a kind solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    task: Task = world.facts["task"]
    helper: Entity = world.facts["helper"]
    traveler: Entity = world.facts["traveler"]
    return [
        QAItem(
            question=f"Who tried to assist {traveler.label} at the subway station?",
            answer=f"{helper.label} tried to assist {traveler.label}, and {helper.label} did it with a bright scarf, a kind heart, and a funny mistake before finding the right way.",
        ),
        QAItem(
            question=f"What was the first silly way {helper.label} tried to help?",
            answer=f"At first, {helper.label} {task.funny_mishelp}. That made the station feel extra silly, but it did not solve the problem.",
        ),
        QAItem(
            question=f"How did {helper.label} solve the problem in the end?",
            answer=f"{helper.label} listened to the station keeper and used the proper help: {task.proper_help}. That was the kind of assistance that truly worked.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {traveler.label} was relieved, the station was calmer, and {helper.label} learned that helpfulness can be simple, gentle, and wise.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a subway station?",
            answer="A subway station is a place where people wait for underground trains, follow signs, and move from one platform to another.",
        ),
        QAItem(
            question="What does it mean to assist someone?",
            answer="To assist someone means to help them in a useful, kind way.",
        ),
        QAItem(
            question="Why can humor help in a story?",
            answer="Humor can help because a funny mistake can make a problem feel lighter while the characters still work toward a real solution.",
        ),
        QAItem(
            question="Why do fairy tales often feel special?",
            answer="Fairy tales often feel special because ordinary places and problems can seem magical, brave, and a little larger than life.",
        ),
    ]


# ---------------------------------------------------------------------------
# Formatting and CLI
# ---------------------------------------------------------------------------

def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for p in sample.prompts:
        parts.append(f"- {p}")
    parts.append("")
    parts.append("== story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: {e.kind} {e.label} type={e.type}")
    return "\n".join(lines)


def asp_verify() -> int:
    py = set(TASKS)
    asp_set = set(asp_valid_tasks())
    if py == asp_set:
        print(f"OK: ASP matches Python registry ({len(py)} tasks).")
        return 0
    print("Mismatch between ASP and Python task registries.")
    print("only in python:", sorted(py - asp_set))
    print("only in asp:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous fairy-tale story world set in a subway station.")
    ap.add_argument("--station", default="subway_station", choices=["subway_station"])
    ap.add_argument("--task", choices=sorted(TASKS))
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--traveler-name")
    ap.add_argument("--traveler-type", choices=["girl", "boy"])
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
    if args.task and args.task not in TASKS:
        raise StoryError(f"Unknown task: {args.task}")
    return choose_params(args, rng)


CURATED = [
    StoryParams(task="find_ticket", helper_name="Mira", helper_type="girl", traveler_name="Sir Tock", traveler_type="boy"),
    StoryParams(task="carry_parcel", helper_name="Pip", helper_type="boy", traveler_name="Mona", traveler_type="girl"),
    StoryParams(task="guide_train", helper_name="Lina", helper_type="girl", traveler_name="Gus", traveler_type="boy"),
    StoryParams(task="share_bench", helper_name="Finn", helper_type="boy", traveler_name="Queen Dot", traveler_type="girl"),
]


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
        print(asp_program("#show reasonable/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("reasonable tasks:", ", ".join(asp_valid_tasks()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.helper_name} and {p.traveler_name} at the subway station ({p.task})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
