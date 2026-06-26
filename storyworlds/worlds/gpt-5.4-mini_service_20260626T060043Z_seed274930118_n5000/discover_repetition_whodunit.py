#!/usr/bin/env python3
"""
storyworlds/worlds/discover_repetition_whodunit.py
==================================================

A small whodunit storyworld about a careful detective who keeps noticing the
same clue again and again until the repeated pattern reveals who hid the missing
object.

Premise:
- A child or detective finds a puzzle in a quiet place.
- Repeated signs in the world suggest someone is copying, circling, or revisiting
  the same spot.
- The detective discovers the answer by following the repetition.

This world keeps the prose child-facing and concrete while the simulated state
drives the turning point: repeated traces increase suspicion, and a final
deduction resolves the mystery.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    mood: str
    repeat_spot: str
    clues: list[str] = field(default_factory=list)


@dataclass
class Mystery:
    missing: str
    hidden_by: str
    hide_place: str
    repeated_clue: str
    repeated_count: int
    reveal_line: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def repeated_sign(world: World, sign: str) -> None:
    world.place.clues.append(sign)
    for e in world.characters():
        e.meters["noticed"] = e.meters.get("noticed", 0.0) + 1
    world.say(sign)


def clue_pressure(world: World, detective: Entity) -> None:
    count = detective.meters.get("noticed", 0.0)
    if count >= 2 and ("pressure", detective.id) not in world.fired:
        world.fired.add(("pressure", detective.id))
        detective.memes["curiosity"] = detective.memes.get("curiosity", 0.0) + 1
        world.say(
            f"{detective.id} frowned, because the same clue kept coming back."
        )


def reveal_mystery(world: World, detective: Entity, mystery: Mystery) -> None:
    if ("reveal", detective.id) in world.fired:
        return
    if detective.meters.get("noticed", 0.0) < mystery.repeated_count:
        return
    world.fired.add(("reveal", detective.id))
    detective.memes["confidence"] = detective.memes.get("confidence", 0.0) + 1
    world.say(
        f"Then {detective.id} discovered the truth: {mystery.reveal_line}"
    )


def tell(
    place: Place,
    mystery: Mystery,
    detective_name: str = "Mina",
    detective_type: str = "girl",
    helper_name: str = "Ollie",
    helper_type: str = "boy",
) -> World:
    world = World(place)

    detective = world.add(Entity(
        id=detective_name, kind="character", type=detective_type, label="detective"
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type=helper_type, label="helper"
    ))
    missing = world.add(Entity(
        id="missing", kind="thing", type=mystery.missing, label=mystery.missing, hidden=True
    ))
    culprit = world.add(Entity(
        id=mystery.hidden_by, kind="character", type="girl", label="suspect"
    ))
    culprit.meters["nervous"] = 0.0

    world.say(
        f"On a {place.mood} evening in {place.name}, {detective.id} found a mystery."
    )
    world.say(
        f"{helper.id} pointed at the empty spot where {missing.label} should have been."
    )
    world.say(
        f"Someone had hidden it, and only careful clues could discover the truth."
    )

    world.para()
    for i in range(mystery.repeated_count):
        repeated_sign(world, mystery.repeated_clue)
        culprit.meters["nervous"] = culprit.meters.get("nervous", 0.0) + 1
        if i == 0:
            world.say(f"{detective.id} wrote the clue down in a tiny notebook.")
        elif i == 1:
            world.say(f"{detective.id} saw it again near {place.repeat_spot}.")
        else:
            world.say(f"It was the same clue, repeating one more time.")

        clue_pressure(world, detective)

    world.para()
    world.say(
        f"{detective.id} followed the repeated clue to {mystery.hide_place}."
    )
    reveal_mystery(world, detective, mystery)
    world.say(
        f"{mystery.hidden_by} admitted it and handed back {missing.label}."
    )
    world.say(
        f"At the end, the mystery was solved, and the repeated clue made sense at last."
    )

    world.facts.update(
        detective=detective,
        helper=helper,
        missing=missing,
        culprit=culprit,
        mystery=mystery,
        place=place,
    )
    return world


PLACES = {
    "library": Place(
        name="the library",
        mood="quiet",
        repeat_spot="the shelf by the tall window",
        clues=["a small blue thread", "a small blue thread", "a small blue thread"],
    ),
    "hallway": Place(
        name="the hallway",
        mood="hushed",
        repeat_spot="the coat rack",
        clues=["a muddy footprint", "a muddy footprint", "a muddy footprint"],
    ),
    "garden": Place(
        name="the garden room",
        mood="still",
        repeat_spot="the window ledge",
        clues=["a red feather", "a red feather", "a red feather"],
    ),
}

MYSTERIES = {
    "book": Mystery(
        missing="book",
        hidden_by="Nora",
        hide_place="behind the reading cushion",
        repeated_clue="A tiny blue thread kept appearing again.",
        repeated_count=3,
        reveal_line="Nora had hidden the book behind the reading cushion so she could keep reading it herself.",
    ),
    "cookie_tin": Mystery(
        missing="cookie tin",
        hidden_by="Maya",
        hide_place="under the hall bench",
        repeated_clue="A crumb trail kept showing up again.",
        repeated_count=3,
        reveal_line="Maya had tucked the cookie tin under the hall bench and kept sneaking back for one more look.",
    ),
    "key": Mystery(
        missing="key",
        hidden_by="Ella",
        hide_place="inside the flower pot",
        repeated_clue="A shiny mark kept catching the light.",
        repeated_count=2,
        reveal_line="Ella had slipped the key inside the flower pot after borrowing it without asking.",
    ),
}

DETECTIVE_NAMES = ["Mina", "Tess", "Rae", "June", "Ivy", "Lena"]
HELPER_NAMES = ["Ollie", "Finn", "Theo", "Kai", "Ben", "Noah"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small repetition whodunit world."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str]]:
    return sorted((p, m) for p in PLACES for m in MYSTERIES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place or args.mystery:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.mystery is None or c[1] == args.mystery)
        ]
    if not combos:
        raise StoryError("(No valid mystery matches the given options.)")
    place, mystery = rng.choice(combos)
    return StoryParams(
        place=place,
        mystery=mystery,
        detective_name=args.detective_name or rng.choice(DETECTIVE_NAMES),
        detective_type=args.detective_type or rng.choice(["girl", "boy"]),
        helper_name=args.helper_name or rng.choice(HELPER_NAMES),
        helper_type=args.helper_type or rng.choice(["girl", "boy"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit story for a child set in {f["place"].name} that repeats one clue until the answer is found.',
        f"Tell a gentle mystery where {f['detective'].id} keeps noticing the same sign and finally discovers who hid the {f['missing'].label}.",
        f'Write a simple story about repetition and discovery in {f["place"].name}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    mystery = f["mystery"]
    place = f["place"]
    culprit = f["culprit"]
    return [
        QAItem(
            question=f"Who discovered the mystery in {place.name}?",
            answer=f"{detective.id} discovered it by following the repeated clue.",
        ),
        QAItem(
            question=f"What clue kept repeating in {place.name}?",
            answer=mystery.repeated_clue,
        ),
        QAItem(
            question=f"Where did {detective.id} find the missing {mystery.missing}?",
            answer=f"{detective.id} found it at {mystery.hide_place}.",
        ),
        QAItem(
            question=f"Who had hidden the {mystery.missing}?",
            answer=f"{culprit.id} had hidden it.",
        ),
        QAItem(
            question=f"What did {helper.id} do in the story?",
            answer=f"{helper.id} helped notice the empty spot and stayed beside {detective.id} while the clues were followed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery story?",
            answer="A clue is a small piece of information that helps someone discover what happened.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means something happens or appears again and again.",
        ),
        QAItem(
            question="Why can repeated clues help solve a whodunit?",
            answer="Repeated clues can show a pattern, and patterns make it easier to discover the answer.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  clues: {world.place.clues}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- place_fact(P).
mystery(M) :- mystery_fact(M).
repeats(C,N) :- clue(C,N).

noticed(D) :- repeat_seen(D,N), N >= 2.
discover(D,M) :- detective(D), mystery_fact(M), noticed(D).

#show discover/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place_fact", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery_fact", m))
    for m in MYSTERIES.values():
        lines.append(asp.fact("clue", m.repeated_clue, m.repeated_count))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show discover/2."))
    asp_set = sorted(set(asp.atoms(model, "discover")))
    py_set = [(p, m) for p in PLACES for m in MYSTERIES]
    if len(asp_set) == 0:
        print("MISMATCH: ASP returned no discover atoms.")
        return 1
    print(f"OK: ASP program parses and produced {len(asp_set)} shown atoms.")
    return 0


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    world = tell(place, mystery, params.detective_name, params.detective_type, params.helper_name, params.helper_type)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show discover/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show discover/2."))
        atoms = sorted(set(asp.atoms(model, "discover")))
        print(f"{len(atoms)} discover atoms:")
        for a in atoms:
            print(" ", a)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in PLACES:
            for m in MYSTERIES:
                params = StoryParams(
                    place=p,
                    mystery=m,
                    detective_name="Mina",
                    detective_type="girl",
                    helper_name="Ollie",
                    helper_type="boy",
                )
                params.seed = base_seed
                samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
