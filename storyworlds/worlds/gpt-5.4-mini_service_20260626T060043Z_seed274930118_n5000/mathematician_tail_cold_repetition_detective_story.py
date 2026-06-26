#!/usr/bin/env python3
"""
A small detective-story world about a mathematician, a cold case, and a tail-shaped clue.

The premise is a classical mystery: a careful mathematician notices that something
about a chilly room keeps happening again and again. A repeated pattern in the clues
leads to a hidden culprit and a neat resolution.
"""

from __future__ import annotations

import argparse
import copy
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
    carries: list[str] = field(default_factory=list)
    found_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "girl", "mother", "mom"}
        male = {"man", "boy", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Location:
    name: str
    cold: bool = False
    has_repetition: bool = False
    places: list[str] = field(default_factory=list)


@dataclass
class Clue:
    label: str
    repeated: bool = False
    origin: str = ""


@dataclass
class StoryParams:
    location: str
    clue: str
    name: str
    gender: str
    assistant: str
    seed: Optional[int] = None


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.clues: dict[str, Clue] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        clone = World(self.location)
        clone.entities = copy.deepcopy(self.entities)
        clone.clues = copy.deepcopy(self.clues)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

LOCATIONS = {
    "library": Location(
        name="the library",
        cold=True,
        has_repetition=True,
        places=["desk", "hallway", "stack of books"],
    ),
    "station": Location(
        name="the station",
        cold=True,
        has_repetition=True,
        places=["bench", "ticket window", "platform"],
    ),
    "observatory": Location(
        name="the observatory",
        cold=False,
        has_repetition=True,
        places=["dome", "stair", "chart table"],
    ),
}

CLUES = {
    "tail": Clue(
        label="a long tail of yarn",
        repeated=True,
        origin="across the room",
    ),
    "cold": Clue(
        label="a cold draft from under the door",
        repeated=True,
        origin="the same crack in the floor",
    ),
    "repetition": Clue(
        label="the same tiny pattern again and again",
        repeated=True,
        origin="everywhere in the room",
    ),
}

ASSISTANTS = {
    "mouse": "small mouse",
    "cat": "sleepy cat",
    "boy": "young helper",
    "girl": "young helper",
}

GENDERS = ["girl", "boy"]
NAMES = {
    "girl": ["Mina", "Ivy", "Nora", "Lena", "Zoe"],
    "boy": ["Theo", "Finn", "Eli", "Noah", "Max"],
}


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    loc = LOCATIONS[params.location]
    world = World(loc)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="woman" if params.gender == "girl" else "man",
        label="mathematician",
    ))
    helper = world.add(Entity(
        id="assistant",
        kind="character",
        type="cat" if params.assistant == "cat" else "mouse",
        label=ASSISTANTS[params.assistant],
    ))
    clue = world.clues.setdefault(params.clue, CLUES[params.clue])

    world.facts.update(hero=hero, helper=helper, clue=clue, location=loc)
    return world


def suspicious_pattern(world: World) -> bool:
    return world.location.has_repetition or world.location.cold


def add_clue(world: World, clue_key: str) -> None:
    clue = world.clues[clue_key]
    clue.repeated = True


def narrate_setup(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    loc: Location = world.facts["location"]
    world.say(
        f"{hero.id} was a mathematician who loved neat numbers and neat clues."
    )
    world.say(
        f"One cold evening, {hero.id} and the {helper.label} went to {loc.name}."
    )
    world.say(
        f"At {loc.name}, {hero.id} noticed something odd: the same little sign kept appearing, "
        f"again and again, again and again."
    )


def narrate_turn(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    clue: Clue = world.facts["clue"]
    loc: Location = world.facts["location"]

    world.para()
    world.say(
        f"{hero.id} frowned. The room felt cold, and the clues did not match at first."
    )
    world.say(
        f"Then {helper.pronoun('subject')} pointed with a tiny paw at {clue.label}."
    )
    world.say(
        f"The clue came from {clue.origin}, and it showed up in {loc.name} more than once."
    )
    world.say(
        f"{hero.id} counted the repeats: one, two, three. A pattern was hiding in plain sight."
    )


def narrate_resolution(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    clue: Clue = world.facts["clue"]
    loc: Location = world.facts["location"]

    world.para()
    world.say(
        f"{hero.id} followed the repeated clue to its source and found the answer."
    )
    if clue.label == "a long tail of yarn":
        world.say(
            f"It was the {helper.label}'s tail, dragging yarn across the floor in the same path twice."
        )
    elif clue.label == "a cold draft from under the door":
        world.say(
            f"It was cold air slipping under the same door crack and making the pages flutter twice."
        )
    else:
        world.say(
            f"It was a simple repeated pattern that led {hero.id} straight to the hidden answer."
        )
    world.say(
        f"{hero.id} smiled, because the mystery was solved by careful counting and calm thinking."
    )
    world.say(
        f"Before long, {hero.id} and the {helper.label} left {loc.name}, and the cold case felt warm and clear."
    )


def generate_story(world: World) -> None:
    narrate_setup(world)
    narrate_turn(world)
    narrate_resolution(world)
    world.facts["solved"] = True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    clue: Clue = world.facts["clue"]
    loc: Location = world.facts["location"]
    return [
        f"Write a short detective story about a mathematician at {loc.name} who notices {clue.label}.",
        f"Tell a child-friendly mystery where {hero.id} solves a cold case by spotting repetition.",
        f"Write a story with a clever mathematician, a cold setting, and a clue that repeats again and again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    clue: Clue = world.facts["clue"]
    loc: Location = world.facts["location"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a mathematician who solves a mystery by noticing patterns.",
        ),
        QAItem(
            question=f"What made the case hard at {loc.name}?",
            answer=f"The case was hard because it felt cold, and the clue kept repeating again and again.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} solve the mystery?",
            answer=f"{hero.id} solved the mystery by following {clue.label}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} notice the clue?",
            answer=f"The {helper.label} helped by pointing to the clue and making the pattern easier to see.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the mystery solved, the clue explained, and {hero.id} leaving {loc.name} feeling proud.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    loc: Location = world.facts["location"]
    return [
        QAItem(
            question="What is a mathematician?",
            answer="A mathematician is a person who studies numbers, shapes, and patterns.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means something happens again and again in the same way.",
        ),
        QAItem(
            question="What does cold mean in a story?",
            answer="Cold means the air or room feels chilly, so people may shiver and want warmth.",
        ),
        QAItem(
            question=f"What kind of place is {loc.name}?",
            answer=f"{loc.name} is a place where the story's mystery can happen and clues can be found.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is reasonable when it has a mathematician, a cold location, and a clue that repeats.
reasonable_story(L, C) :- location(L), clue(C), cold(L), repeated(C).

% Detective stories should be solvable by pattern recognition.
solves(L, C) :- reasonable_story(L, C), pattern_story(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lid, loc in LOCATIONS.items():
        lines.append(asp.fact("location", lid))
        if loc.cold:
            lines.append(asp.fact("cold", lid))
        if loc.has_repetition:
            lines.append(asp.fact("repetition_space", lid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if clue.repeated:
            lines.append(asp.fact("repeated", cid))
        if cid in {"tail", "repetition"}:
            lines.append(asp.fact("pattern_story", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable_story/2."))
    return sorted(set(asp.atoms(model, "reasonable_story")))


def asp_verify() -> int:
    python_set = {
        (lid, cid)
        for lid, loc in LOCATIONS.items()
        for cid, clue in CLUES.items()
        if loc.cold and clue.repeated
    }
    clingo_set = set(asp_valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if clingo_set - python_set:
        print("  only in ASP:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in Python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness and generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for lid, loc in LOCATIONS.items():
        if not loc.cold:
            continue
        for cid, clue in CLUES.items():
            if clue.repeated:
                combos.append((lid, cid))
    return combos


def explain_rejection(location: Location, clue: Clue) -> str:
    if not location.cold:
        return "(No story: this detective tale needs a cold setting so the chill matters.)"
    if not clue.repeated:
        return "(No story: the mystery needs repetition so the mathematician can notice a pattern.)"
    return "(No story: the chosen setup is not a good detective mystery.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.location and args.clue:
        loc = LOCATIONS[args.location]
        clue = CLUES[args.clue]
        if not (loc.cold and clue.repeated):
            raise StoryError(explain_rejection(loc, clue))

    combos = [
        c for c in valid_combos()
        if (args.location is None or c[0] == args.location)
        and (args.clue is None or c[1] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    location, clue = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES[gender])
    assistant = args.assistant or rng.choice(list(ASSISTANTS))
    return StoryParams(
        location=location,
        clue=clue,
        name=name,
        gender=gender,
        assistant=assistant,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: mathematician, cold case, repetition.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--assistant", choices=list(ASSISTANTS))
    ap.add_argument("--name")
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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    for cid, clue in world.clues.items():
        lines.append(f"  clue {cid:10} repeated={clue.repeated} origin={clue.origin}")
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
        print(asp_program("#show reasonable_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reasonable_story/2."))
        combos = sorted(set(asp.atoms(model, "reasonable_story")))
        print(f"{len(combos)} reasonable combos:")
        for item in combos:
            print(f"  {item[0]} / {item[1]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for lid, cid in sorted(valid_combos()):
            params = StoryParams(
                location=lid,
                clue=cid,
                name=NAMES["girl"][0],
                gender="girl",
                assistant="cat",
            )
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
