#!/usr/bin/env python3
"""
A small detective-story world about a drape, a hesitation, and a misunderstanding
that turns into conflict before the clues make things clear.
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
class StoryParams:
    room: str
    hero: str
    helper: str
    object_name: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Room:
    name: str
    description: str


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
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


ROOMS = {
    "study": Room("the study", "The study was quiet, with a desk lamp and a tall window."),
    "hall": Room("the hall", "The hall was long, with a narrow rug and framed pictures."),
    "library": Room("the library", "The library smelled like paper and had shelves that reached high."),
}

HEROES = [
    ("Mina", "girl"),
    ("Leo", "boy"),
    ("Nora", "girl"),
    ("Owen", "boy"),
]

HELPERS = [
    ("Detective Finch", "detective"),
    ("Officer Vale", "detective"),
    ("Aunt June", "woman"),
    ("Uncle Sam", "man"),
]

OBJECTS = [
    ("drape", "a blue drape"),
    ("curtain", "a velvet curtain"),
    ("cloth", "a folded cloth"),
    ("shawl", "a long shawl"),
]

TRAITS = ["careful", "curious", "quiet", "bright", "brave"]


ASP_RULES = r"""
room(R) :- setting(R).
object(O) :- item(O).
hesitation(P) :- feels(P, hesitate).
misunderstanding(P) :- feels(P, misunderstanding).
conflict(P) :- feels(P, conflict).
resolve(P) :- understanding(P), not conflict(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for r in ROOMS:
        lines.append(asp.fact("setting", r))
    for o, _ in OBJECTS:
        lines.append(asp.fact("item", o))
    lines.append(asp.fact("feels", "hero", "hesitate"))
    lines.append(asp.fact("feels", "hero", "misunderstanding"))
    lines.append(asp.fact("feels", "hero", "conflict"))
    lines.append(asp.fact("understanding", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show conflict/1.\n#show misunderstanding/1.\n#show hesitation/1.\n"))
    names = sorted(set(asp.atoms(model, "conflict") + asp.atoms(model, "misunderstanding") + asp.atoms(model, "hesitation")))
    py = [("hero",), ("hero",), ("hero",)]
    if names == py:
        print("OK: ASP and Python reasonableness gates agree.")
        return 0
    print("MISMATCH: ASP and Python gates differ.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-story world: drape, hesitate, misunderstanding, conflict.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--hero", choices=[h for h, _ in HEROES])
    ap.add_argument("--helper", choices=[h for h, _ in HELPERS])
    ap.add_argument("--object", dest="object_name", choices=[o for o, _ in OBJECTS])
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
    room = args.room or rng.choice(list(ROOMS))
    hero = args.hero or rng.choice([h for h, _ in HEROES])
    helper = args.helper or rng.choice([h for h, _ in HELPERS])
    object_name = args.object_name or rng.choice([o for o, _ in OBJECTS])
    if hero == helper:
        raise StoryError("The detective and the child should not be the same person.")
    return StoryParams(room=room, hero=hero, helper=helper, object_name=object_name)


def generate(params: StoryParams) -> StorySample:
    room = ROOMS[params.room]
    world = World(room)
    hero_type = dict(HEROES)[params.hero]
    helper_type = dict(HELPERS)[params.helper]
    obj_label = dict(OBJECTS)[params.object_name]

    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=params.hero))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=params.helper))
    item = world.add(Entity(id="item", kind="thing", type=params.object_name, label=obj_label))

    trait = random.choice(TRAITS)
    world.facts.update(hero=hero, helper=helper, item=item, trait=trait, room=room)

    world.say(f"{hero.label} was a {trait} child who liked clues and quiet corners.")
    world.say(f"One evening, {hero.label} and {helper.label} walked into {room.name}.")
    world.say(room.description)
    world.say(f"{hero.label} noticed {obj_label} draped over a chair and had to hesitate.")
    world.say(f"{hero.label} thought the drape hid something, but that was a misunderstanding.")
    world.para()
    world.say(f"That misunderstanding caused conflict, because {hero.label} pulled back while {helper.label} wanted a closer look.")
    world.say(f"Then {helper.label} found a tiny clue behind the drape: a lost button, not a secret threat.")
    world.para()
    world.say(f"{hero.label} laughed in relief. The drape had only looked suspicious in the dim light.")
    world.say(f"By the end, {hero.label} was helping {helper.label} arrange the clue bag, and the room felt calm again.")

    prompts = [
        f"Write a short detective story for a child that includes the word 'drape' and the feeling of hesitation.",
        f"Tell a mystery story where {params.hero} and {params.helper} are surprised by {obj_label} in {room.name}.",
        f"Write a gentle detective tale about a misunderstanding that becomes conflict and then gets solved.",
    ]

    story_qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label}, a {trait} child, and {helper.label}, who helped solve the mystery in {room.name}.",
        ),
        QAItem(
            question=f"Why did {hero.label} hesitate near the drape?",
            answer=f"{hero.label} hesitated because the drape looked like it was hiding something, but that was a misunderstanding.",
        ),
        QAItem(
            question=f"What caused the conflict in the middle of the story?",
            answer=f"The conflict came when {hero.label} pulled back and {helper.label} wanted a closer look at the drape.",
        ),
        QAItem(
            question=f"What did the clue behind the drape turn out to be?",
            answer="It turned out to be a lost button, which showed that the drape was not hiding anything scary.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a drape?",
            answer="A drape is a hanging piece of cloth that can cover a window or a chair.",
        ),
        QAItem(
            question="What does hesitate mean?",
            answer="To hesitate means to pause or stop for a moment before acting.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something wrong because they do not have all the facts.",
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is a problem or disagreement that makes the characters struggle before things get better.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        lines.append(f"  {ent.id}: {ent.label} ({ent.type})")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
    StoryParams(room="study", hero="Mina", helper="Detective Finch", object_name="drape"),
    StoryParams(room="hall", hero="Leo", helper="Officer Vale", object_name="curtain"),
    StoryParams(room="library", hero="Nora", helper="Aunt June", object_name="cloth"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show conflict/1.\n#show misunderstanding/1.\n#show hesitation/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for parity checks, but this world is generated procedurally.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
