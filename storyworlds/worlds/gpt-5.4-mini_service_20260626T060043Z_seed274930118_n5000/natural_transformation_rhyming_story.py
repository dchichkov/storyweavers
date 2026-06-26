#!/usr/bin/env python3
"""
A small storyworld about a natural transformation with a rhyming, child-facing
storybook feel.

Seed idea:
A child finds a plain little thing in nature, gently helps it transform into a
new form, and learns that change can be beautiful when it happens with care.
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
    transformed_from: Optional[str] = None
    transformed_into: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    parent_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "garden": "the garden",
    "meadow": "the meadow",
    "forest": "the forest",
    "pond": "the pond",
    "orchard": "the orchard",
}

CHILD_NAMES = ["Mia", "Noah", "Lily", "Ben", "Ava", "Theo", "Nora", "Leo"]
PARENT_TYPES = ["mother", "father"]
CHILD_TYPES = ["girl", "boy"]

NATURE_THINGS = {
    "caterpillar": {
        "label": "caterpillar",
        "phrase": "a tiny green caterpillar",
        "from": "caterpillar",
        "to": "butterfly",
        "turn": "wrap in a silken bed",
        "result_phrase": "a bright butterfly",
    },
    "tadpole": {
        "label": "tadpole",
        "phrase": "a little tadpole",
        "from": "tadpole",
        "to": "frog",
        "turn": "grow legs with a little leap",
        "result_phrase": "a hopping frog",
    },
    "seed": {
        "label": "seed",
        "phrase": "a small brown seed",
        "from": "seed",
        "to": "flower",
        "turn": "wake in warm rain",
        "result_phrase": "a blooming flower",
    },
    "acorn": {
        "label": "acorn",
        "phrase": "a round little acorn",
        "from": "acorn",
        "to": "oak tree",
        "turn": "push out roots and reach for light",
        "result_phrase": "a young oak tree",
    },
}

TRANSFORM_ORDER = ["seed", "tadpole", "caterpillar", "acorn"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in PLACES for t in NATURE_THINGS]


def choose_nature_thing(place: str, rng: random.Random) -> str:
    if place == "pond":
        return "tadpole"
    if place == "garden":
        return rng.choice(["seed", "caterpillar"])
    if place == "orchard":
        return rng.choice(["seed", "acorn"])
    return rng.choice(list(NATURE_THINGS))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Natural transformation in a rhyming little story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--thing", choices=NATURE_THINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=CHILD_TYPES)
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    place = args.place or rng.choice(list(PLACES))
    thing = args.thing or choose_nature_thing(place, rng)
    name = args.name or rng.choice(CHILD_NAMES)
    gender = args.gender or rng.choice(CHILD_TYPES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    if args.gender == "girl" and name in {"Noah", "Ben", "Theo", "Leo"}:
        pass
    if thing not in NATURE_THINGS:
        raise StoryError("Unknown transformation thing.")
    return StoryParams(place=place, child_name=name, child_type=gender, parent_type=parent)


def story_rhyme(kind: str, step: str) -> str:
    if kind == "seed":
        return f"With a tap and a cheer, the little seed woke here."
    if kind == "tadpole":
        return f"With a swish and a hop, the tadpole would not stop."
    if kind == "caterpillar":
        return f"With a soft little spin, the caterpillar tucked in."
    return f"With a hush and a glow, the acorn was ready to grow."


def make_world(params: StoryParams) -> World:
    rng = random.Random(params.seed or 0)
    world = World(place=PLACES[params.place])
    thing_key = choose_nature_thing(params.place, rng)
    if params.place == "pond":
        thing_key = "tadpole"
    thing = NATURE_THINGS[thing_key]

    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, label=params.parent_type))
    nature = world.add(Entity(id="nature", type=thing["from"], label=thing["label"], phrase=thing["phrase"]))

    child.memes["wonder"] = 1.0
    nature.meters["plain"] = 1.0
    nature.meters["ready"] = 1.0

    world.say(f"{child.label} went to {world.place}, where the air felt clear and bright.")
    world.say(f"There {nature.phrase} sat still in the grass, all simple, all light.")
    world.say(f"{child.label} smiled and said, 'What can you become if we help you along?'")
    world.say(
        f"{parent.label.capitalize()} said, 'Wait and watch, and nature will sing its own song.'"
    )

    world.para()
    world.say(
        f"{child.label} gave the little thing room, and room is a gift that helps living things bloom."
    )
    world.say(
        f"{story_rhyme(thing_key, thing['turn'])} {thing['turn'].capitalize()}, and then came the tune."
    )

    world.para()
    nature.transformed_from = thing["from"]
    nature.transformed_into = thing["to"]
    nature.type = thing["to"]
    nature.label = thing["result_phrase"]
    nature.phrase = thing["result_phrase"]
    nature.meters["plain"] = 0.0
    nature.meters["changed"] = 1.0
    nature.memes["joy"] = 1.0

    world.say(
        f"Soon the small {thing['from']} was no longer the same; it had changed by a natural game."
    )
    world.say(
        f"Where once there was one tiny start, now {nature.phrase} shone like a bright little heart."
    )
    world.say(
        f"{child.label} clapped, and {parent.label} laughed low: 'A gentle change can be lovely to know.'"
    )

    world.facts.update(
        child=child,
        parent=parent,
        nature=nature,
        thing_key=thing_key,
        thing=thing,
        place=params.place,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    thing = f["thing"]
    place = PLACES[f["place"]]
    return [
        f'Write a short rhyming story for a young child about a natural transformation at {place}.',
        f"Tell a gentle story where {child.label} watches {thing['phrase']} change into {thing['result_phrase']}.",
        f'Write a simple story with the word "natural" and a calm transformation in {place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    nature: Entity = f["nature"]
    thing = f["thing"]
    place = PLACES[f["place"]]
    return [
        QAItem(
            question=f"Where did {child.label} see the little {thing['label']} change?",
            answer=f"{child.label} saw it in {place}, where the whole moment felt calm and natural.",
        ),
        QAItem(
            question=f"What did the {thing['label']} turn into?",
            answer=f"It changed into {nature.phrase}. That was the natural transformation in the story.",
        ),
        QAItem(
            question=f"Who said the change could be lovely to know?",
            answer=f"{parent.label.capitalize()} said that a gentle change could be lovely to know.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does natural mean in a story like this?",
            answer="Natural means something happens in the world by itself, like a plant or animal growing and changing over time.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another form.",
        ),
        QAItem(
            question="Why is it nice to watch a living thing change slowly?",
            answer="It can be nice because slow change lets you notice each small step, like growing, budding, or hatching.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
thing(seed). thing(tadpole). thing(caterpillar). thing(acorn).
place(garden). place(meadow). place(forest). place(pond). place(orchard).

transforms(seed, flower).
transforms(tadpole, frog).
transforms(caterpillar, butterfly).
transforms(acorn, oak_tree).

natural_story(P, T) :- place(P), thing(T), transforms(T, _).
#show natural_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in NATURE_THINGS:
        lines.append(asp.fact("thing", t))
    for t, info in NATURE_THINGS.items():
        lines.append(asp.fact("transforms", t, info["to"].replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show natural_story/2."))
    asp_pairs = set(asp.atoms(model, "natural_story"))
    py_pairs = set((p, t) for p, t in valid_combos())
    if asp_pairs == py_pairs:
        print(f"OK: ASP matches Python ({len(py_pairs)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in ASP:", sorted(asp_pairs - py_pairs))
    print("only in Python:", sorted(py_pairs - asp_pairs))
    return 1


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show natural_story/2."))
    return sorted(set(asp.atoms(model, "natural_story")))


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

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
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.transformed_from:
            bits.append(f"from={e.transformed_from}")
        if e.transformed_into:
            bits.append(f"into={e.transformed_into}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: " + ", ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_curated() -> list[StoryParams]:
    return [
        StoryParams(place="garden", child_name="Mia", child_type="girl", parent_type="mother", seed=1),
        StoryParams(place="pond", child_name="Noah", child_type="boy", parent_type="father", seed=2),
        StoryParams(place="orchard", child_name="Lily", child_type="girl", parent_type="mother", seed=3),
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


def resolve_valid_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    thing = args.thing or choose_nature_thing(place, rng)
    name = args.name or rng.choice(CHILD_NAMES)
    gender = args.gender or rng.choice(CHILD_TYPES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(place=place, child_name=name, child_type=gender, parent_type=parent, seed=args.seed)


def valid_combos_count() -> int:
    return len(valid_combos())


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show natural_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show natural_story/2."))
        combos = sorted(set(asp.atoms(model, "natural_story")))
        print(f"{len(combos)} natural transformation combos:\n")
        for p, t in combos:
            print(f"  {p:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in build_curated()]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_valid_params(args, random.Random(seed))
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
            header = f"### {p.child_name}: natural transformation in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
