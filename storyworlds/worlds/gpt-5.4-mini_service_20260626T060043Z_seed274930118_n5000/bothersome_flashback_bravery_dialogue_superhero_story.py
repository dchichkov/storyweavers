#!/usr/bin/env python3
"""
A small superhero story world with a bothersome problem, a flashback, brave
dialogue, and a clear rescue-style ending.

The world is deliberately small and constraint-checked: a hero, a city, a
bothersome incident, a remembered moment of doubt, a brave choice, and a
helpful gadget or plan that makes the ending possible.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "heroine", "mother"}
        male = {"boy", "man", "hero", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class City:
    name: str
    place: str
    danger: str
    afford: str


@dataclass
class Problem:
    id: str
    verb: str
    noun: str
    bother: str
    intensity: str
    cause: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    use: str
    helps: set[str]


@dataclass
class World:
    city: City
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

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
        import copy
        clone = World(self.city)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

CITIES = {
    "skyport": City(name="Skyport City", place="the busy skybridge", danger="a wobbling drone", afford="patrol"),
    "harbor": City(name="Harbor City", place="the moonlit docks", danger="a runaway cargo cart", afford="patrol"),
    "downtown": City(name="Downtown", place="the glass square", danger="a broken scoreboard", afford="patrol"),
}

PROBLEMS = {
    "drone": Problem(
        id="drone",
        verb="stop the drone",
        noun="drone",
        bother="bothersome",
        intensity="buzzed too loudly",
        cause="a tangled control wire",
        tags={"tech", "noise"},
    ),
    "cart": Problem(
        id="cart",
        verb="catch the cart",
        noun="cart",
        bother="bothersome",
        intensity="rolled too fast",
        cause="a loose brake",
        tags={"motion", "crowd"},
    ),
    "scoreboard": Problem(
        id="scoreboard",
        verb="fix the scoreboard",
        noun="scoreboard",
        bother="bothersome",
        intensity="kept flashing wrong numbers",
        cause="a cracked power box",
        tags={"light", "crowd"},
    ),
}

AIDS = {
    "shield": Aid(
        id="shield",
        label="a bright shield",
        prep="raise",
        use="shield the crowd",
        helps={"motion", "crowd"},
    ),
    "gloves": Aid(
        id="gloves",
        label="power gloves",
        prep="wear",
        use="grab the problem carefully",
        helps={"tech", "motion"},
    ),
    "glider": Aid(
        id="glider",
        label="a quick glider pack",
        prep="strap on",
        use="reach the problem in a flash",
        helps={"noise", "light"},
    ),
}

HERO_NAMES = ["Nova", "Sky", "Aria", "Bolt", "Mira", "Jett"]
SIDEKICK_NAMES = ["Pip", "Leo", "Zia", "Rin", "Tess", "Max"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    city: str
    problem: str
    hero: str
    sidekick: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for city_id, city in CITIES.items():
        for pid, problem in PROBLEMS.items():
            if pid == "drone" and city_id != "skyport":
                continue
            if pid == "cart" and city_id != "harbor":
                continue
            if pid == "scoreboard" and city_id != "downtown":
                continue
            combos.append((city_id, pid))
    return combos


def choose_aid(problem: Problem) -> Optional[Aid]:
    for aid in AIDS.values():
        if problem.tags & aid.helps:
            return aid
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with a bothersome problem, flashback, bravery, and dialogue.")
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
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
    combos = [c for c in valid_combos()
              if (args.city is None or c[0] == args.city)
              and (args.problem is None or c[1] == args.problem)]
    if not combos:
        raise StoryError("No valid superhero story matches the given options.")
    city_id, problem_id = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice([n for n in SIDEKICK_NAMES if n != hero])
    return StoryParams(city=city_id, problem=problem_id, hero=hero, sidekick=sidekick)


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    city = CITIES[params.city]
    problem = PROBLEMS[params.problem]
    aid = choose_aid(problem)
    world = World(city)
    hero = world.add(Entity(id=params.hero, kind="character", type="hero", label=params.hero))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="sidekick", label=params.sidekick))
    threat = world.add(Entity(id=problem.id, type=problem.noun, label=problem.noun))
    tool = world.add(Entity(id=aid.id if aid else "tool", type="aid", label=aid.label if aid else "tool"))

    hero.memes["care"] = 1
    hero.memes["bravery"] = 1
    sidekick.memes["worry"] = 1
    threat.meters["trouble"] = 1

    world.say(f"{hero.id} was a superhero who watched over {city.name}.")
    world.say(f"{hero.id} and {sidekick.id} liked quiet mornings, when the city felt safe and shiny.")

    world.para()
    world.say(f"One day, a {problem.bother} {problem.noun} {problem.intensity} at {city.place}.")
    world.say(f"It was {problem.cause}, and that made the whole scene feel like a {problem.bother} surprise.")
    world.say(f"{sidekick.id} pointed and said, \"{hero.id}, we need help now!\"")

    world.para()
    world.say(f"That sight brought back a flashback for {hero.id}.")
    world.say(f"Long ago, {hero.id} had once frozen up when a similar problem started to spread.")
    world.say(f"But {hero.id} remembered taking one brave breath, then stepping forward anyway.")

    world.para()
    world.say(f"{hero.id} straightened {hero.pronoun('possessive')} cape and said, \"I can do this.\"")
    world.say(f"Then {hero.id} answered, \"Stay back, {sidekick.id}. I will fix it carefully.\"")
    if aid:
        world.say(f"{hero.id} decided to {aid.prep} {aid.label} so {hero.id} could {aid.use}.")
    else:
        world.say(f"{hero.id} looked for a simple way to help without making the trouble worse.")

    world.para()
    hero.meters["action"] = 1
    hero.memes["bravery"] += 1
    threat.meters["trouble"] = 0
    if aid:
        tool.worn_by = hero.id
        tool.protective = True
    world.say(f"With brave hands and clear eyes, {hero.id} handled the {problem.noun}.")
    if aid:
        world.say(f"{aid.label.capitalize()} helped {hero.id} keep everyone safe while the fix was made.")
    world.say(f"At last, the {problem.noun} was quiet, and the city stopped feeling {problem.bother}.")

    world.para()
    world.say(f"{sidekick.id} smiled and said, \"That was the bravest thing I have seen today!\"")
    world.say(f"{hero.id} smiled back, and together they looked over {city.name}, calm and bright again.")

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        threat=threat,
        aid=aid,
        city=city,
        problem=problem,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a young child that includes the word "bothersome" and a flashback.',
        f"Tell a brave rescue story where {f['hero'].id} and {f['sidekick'].id} face a {f['problem'].noun} in {f['city'].name}.",
        f"Write a simple dialogue-filled story about a superhero solving a {f['problem'].noun} problem with courage.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    problem = f["problem"]
    city = f["city"]
    aid = f["aid"]
    qs = [
        QAItem(
            question=f"Where did {hero.id} try to help with the {problem.noun}?",
            answer=f"{hero.id} helped at {city.place} in {city.name}, where the problem was causing trouble.",
        ),
        QAItem(
            question=f"What made the problem feel {problem.bother}?",
            answer=f"The {problem.noun} felt {problem.bother} because it {problem.intensity} and came from {problem.cause}.",
        ),
        QAItem(
            question=f"Who talked with {hero.id} during the rescue?",
            answer=f"{hero.id} talked with {sidekick.id}, and their dialogue helped the story move toward a solution.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=f"{hero.id} remembered a time of fear from before, then chose bravery instead of freezing again.",
        ),
    ]
    if aid:
        qs.append(QAItem(
            question=f"What helped {hero.id} solve the problem safely?",
            answer=f"{aid.label} helped {hero.id} handle the {problem.noun} carefully and keep the city safe.",
        ))
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is being scared or unsure but still doing the helpful thing anyway.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a story moment that shows something from earlier in the character's memory.",
        ),
        QAItem(
            question="Why do superheroes talk to each other during a rescue?",
            answer="Dialogue helps superheroes share plans, warn each other, and work together quickly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append("protective=True")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
city(C) :- city_fact(C).
problem(P) :- problem_fact(P).
valid(C, P) :- compatible(C, P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in CITIES:
        lines.append(asp.fact("city_fact", cid))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem_fact", pid))
        lines.append(asp.fact("problem_tag", pid, *sorted(problem.tags)))
    for cid, pid in valid_combos():
        lines.append(asp.fact("compatible", cid, pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(city="skyport", problem="drone", hero="Nova", sidekick="Pip"),
    StoryParams(city="harbor", problem="cart", hero="Sky", sidekick="Tess"),
    StoryParams(city="downtown", problem="scoreboard", hero="Aria", sidekick="Rin"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible superhero story combos:\n")
        for cid, pid in triples:
            print(f"  {cid:10} {pid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            except StoryError as e:
                print(e)
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
            header = f"### {p.hero} in {p.city} against {p.problem}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
