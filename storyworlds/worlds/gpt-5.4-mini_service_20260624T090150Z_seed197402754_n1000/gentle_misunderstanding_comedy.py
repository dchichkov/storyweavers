#!/usr/bin/env python3
"""
A tiny storyworld about a gentle misunderstanding with comedic timing.

Premise:
- A child tries to help with a simple task.
- A harmless misunderstanding makes the task look much bigger than it is.
- A kind adult clears it up, and the joke lands in a happy ending.

The world is intentionally small:
- one child
- one grown-up helper
- one object that is mistaken for something else
- one place
- one resolution that changes emotional state and physical state
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    vibe: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    mistaken_for: str
    real_use: str
    trigger: str
    reveal: str
    prop_hint: str
    joke_style: str = "comic timing"


@dataclass
class StoryParams:
    place: str
    misunderstanding: str
    child_name: str
    child_type: str
    grownup_type: str
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

    def trace(self) -> str:
        out = ["--- world model state ---"]
        for e in self.entities.values():
            out.append(
                f"  {e.id:10} kind={e.kind:8} type={e.type:8} "
                f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
                f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
            )
        out.append(f"  place={self.place.id}")
        out.append(f"  facts={self.facts}")
        return "\n".join(out)


PLACES = {
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        vibe="bright and tidy",
        affordances={"snack", "helping", "cleaning"},
    ),
    "garden": Place(
        id="garden",
        label="the garden",
        vibe="soft and sunny",
        affordances={"watering", "helping", "playing"},
    ),
    "hall": Place(
        id="hall",
        label="the hallway",
        vibe="echoey and narrow",
        affordances={"waiting", "helping"},
    ),
}

MISUNDERSTANDINGS = {
    "box": Misunderstanding(
        id="box",
        mistaken_for="a hat box",
        real_use="a box of napkins",
        trigger="The lid was round and shiny, so it looked fancy.",
        reveal="It was only full of napkins for the lunch table.",
        prop_hint="round lid",
    ),
    "jar": Misunderstanding(
        id="jar",
        mistaken_for="a treasure jar",
        real_use="a jar of jam",
        trigger="The red sparkle made it look very important.",
        reveal="It was just jam for toast.",
        prop_hint="red sparkle",
    ),
    "basket": Misunderstanding(
        id="basket",
        mistaken_for="a pet basket",
        real_use="a basket of rolls",
        trigger="The blanket over it made it look secret and serious.",
        reveal="It was warm bread for dinner.",
        prop_hint="blanket cover",
    ),
    "bag": Misunderstanding(
        id="bag",
        mistaken_for="a drum bag",
        real_use="a bag of beans",
        trigger="It made a little rattly sound when it moved.",
        reveal="It was beans for soup, not a toy.",
        prop_hint="rattly sound",
    ),
}

CHILD_NAMES = ["Milo", "Nina", "Toby", "Pia", "Lulu", "Arlo"]
CHILD_TYPES = ["boy", "girl"]
GROWNUP_TYPES = ["mother", "father", "aunt", "uncle"]


ASP_RULES = r"""
place(kitchen). place(garden). place(hall).

misunderstanding(box).
misunderstanding(jar).
misunderstanding(basket).
misunderstanding(bag).

looks_like(box, hat_box).
looks_like(jar, treasure_jar).
looks_like(basket, pet_basket).
looks_like(bag, drum_bag).

valid_story(P, M) :- place(P), misunderstanding(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
    for m in MISUNDERSTANDINGS.values():
        lines.append(asp.fact("misunderstanding", m.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str]]:
    return [(p, m) for p in PLACES for m in MISUNDERSTANDINGS]


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle misunderstanding comedy storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=CHILD_TYPES)
    ap.add_argument("--parent", choices=GROWNUP_TYPES)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.misunderstanding:
        combos = [c for c in combos if c[1] == args.misunderstanding]
    if not combos:
        raise StoryError("No valid combination matches the given options.")

    place, misunderstanding = rng.choice(sorted(combos))
    child_type = args.gender or rng.choice(CHILD_TYPES)
    child_name = args.name or rng.choice(CHILD_NAMES)
    grownup_type = args.parent or rng.choice(GROWNUP_TYPES)
    return StoryParams(
        place=place,
        misunderstanding=misunderstanding,
        child_name=child_name,
        child_type=child_type,
        grownup_type=grownup_type,
    )


def introduce(world: World, child: Entity, grownup: Entity, item: Entity, mystery: Misunderstanding) -> None:
    world.say(
        f"{child.name()} was a gentle little {child.type} who liked helping in {world.place.label}."
    )
    world.say(
        f"One day, {child.name()} saw {item.phrase} and thought it might be {mystery.mistaken_for}."
    )


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MISUNDERSTANDINGS[params.misunderstanding]
    world = World(place)

    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.child_type,
        label=params.child_name,
        memes={"curiosity": 1.0, "gentle": 1.0},
    ))
    grownup = world.add(Entity(
        id="grownup",
        kind="character",
        type=params.grownup_type,
        label=f"the {params.grownup_type}",
        memes={"warmth": 1.0, "humor": 1.0},
    ))
    if mystery.id == "box":
        item = world.add(Entity(id="item", type="box", label="box", phrase="a small shiny box"))
    elif mystery.id == "jar":
        item = world.add(Entity(id="item", type="jar", label="jar", phrase="a clear jar with red sparkles"))
    elif mystery.id == "basket":
        item = world.add(Entity(id="item", type="basket", label="basket", phrase="a basket with a blanket over it"))
    else:
        item = world.add(Entity(id="item", type="bag", label="bag", phrase="a soft bag that gave a tiny rattle"))

    item.props["real_use"] = mystery.real_use
    item.props["mistaken_for"] = mystery.mistaken_for
    item.props["reveal"] = mystery.reveal
    item.caretaker = grownup.id

    world.facts.update(
        child=child,
        grownup=grownup,
        item=item,
        mystery=mystery,
        place=place,
    )

    introduce(world, child, grownup, item, mystery)

    world.para()
    world.say(
        f"{child.name()} leaned in and said, \"Oh! Is that {mystery.mistaken_for}?\""
    )
    world.say(mystery.trigger)
    world.say(
        f"The {params.grownup_type} blinked, then laughed a little. \"Nope, {child.name()}, it is not that.\""
    )

    world.para()
    world.say(
        f"{child.name()} looked properly surprised and tried to help anyway."
    )
    world.say(
        f"{child.name()} carefully lifted it, and the room went extra quiet for one silly second."
    )
    world.say(
        f"Then the {params.grownup_type} smiled and explained that it was {mystery.real_use}."
    )
    world.say(mystery.reveal)

    world.para()
    world.say(
        f"{child.name()} laughed so hard that even the {params.grownup_type} had to laugh too."
    )
    world.say(
        f"Together they set {item.label if item.label else 'it'} on the table, and the dinner job got easier."
    )
    world.say(
        f"By the end, the mistaken {mystery.mistaken_for} had become a happy joke, and {child.name()} was still gentle, just much less puzzled."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    item = f["item"]
    mystery = f["mystery"]
    return [
        f'Write a short gentle comedy story about {child.name()} who mistakes {item.phrase} for {mystery.mistaken_for}.',
        f"Tell a child-friendly story where a {child.type} and {grownup.type} share a harmless misunderstanding and then laugh together.",
        f'Write a simple funny story that ends with the surprise that {item.phrase} is really {mystery.real_use}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    item = f["item"]
    mystery = f["mystery"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.name()}, a gentle little {child.type}, and {grownup.name()}, {grownup.type}."
        ),
        QAItem(
            question=f"What did {child.name()} think {item.phrase} was at first?",
            answer=f"{child.name()} thought it was {mystery.mistaken_for} because it looked important and a little funny."
        ),
        QAItem(
            question=f"What was {item.phrase} really for?",
            answer=f"It was really {mystery.real_use}, and that is what made the misunderstanding silly."
        ),
        QAItem(
            question=f"Where did the misunderstanding happen?",
            answer=f"It happened in {place.label}, where {child.name()} and the {grownup.type} were helping together."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with both of them laughing, because the mistake was harmless and the grown-up explained it kindly."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks one thing is true, but they are mistaken."
        ),
        QAItem(
            question="Why can funny mistakes make a comedy story?",
            answer="Funny mistakes can make comedy because the reader knows the truth, and the surprise makes the moment amusing."
        ),
        QAItem(
            question="What does gentle mean?",
            answer="Gentle means kind, soft, and not rough or hurtful."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return world.trace()


CURATED = [
    StoryParams(place="kitchen", misunderstanding="box", child_name="Milo", child_type="boy", grownup_type="mother"),
    StoryParams(place="garden", misunderstanding="jar", child_name="Nina", child_type="girl", grownup_type="father"),
    StoryParams(place="hall", misunderstanding="basket", child_name="Toby", child_type="boy", grownup_type="aunt"),
    StoryParams(place="kitchen", misunderstanding="bag", child_name="Pia", child_type="girl", grownup_type="uncle"),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def asp_verify_story() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify_story())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible (place, misunderstanding) combos:\n")
        for p, m in combos:
            print(f"  {p:8} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.misunderstanding} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
