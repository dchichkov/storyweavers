#!/usr/bin/env python3
"""
storyworlds/worlds/violet_repetition_animal_story.py
====================================================

A small animal-story world built from the seed word "violet" and the feature
"Repetition".

The domain premise:
- A young animal wants something lovely and violet.
- A small problem makes the animal repeat a useful action or phrase.
- A helper or simple plan turns repetition from frustration into practice.
- The ending proves the change with a concrete image.

This world keeps the story style close to a gentle Animal Story: a small animal,
a simple want, a tiny obstacle, a repeated attempt, and a warm resolution.
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
    kind: str = "thing"  # "animal" | "thing"
    species: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caregiver: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.species in {"rabbit", "mouse", "squirrel", "fox", "bear", "duck"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    weather: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Place:
    name: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Want:
    id: str
    verb: str
    repeated_verb: str
    object_label: str
    object_phrase: str
    object_color: str
    trouble: str
    obstacle: str
    helper: str
    result_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    want: str
    animal: str
    name: str
    caregiver: str
    seed: Optional[int] = None


PLACES = {
    "garden": Place(
        name="the garden",
        detail="The garden was small and bright, with soft grass and a little stone path.",
        affords={"flower", "string", "paint"},
    ),
    "barn": Place(
        name="the barn",
        detail="The barn smelled like hay, and old rafters made tiny shadows overhead.",
        affords={"rope", "ribbon", "paint"},
    ),
    "pond": Place(
        name="the pond",
        detail="The pond was still and silver, with reeds leaning over the water.",
        affords={"ribbon", "shell"},
    ),
    "meadow": Place(
        name="the meadow",
        detail="The meadow was wide and sunny, with clover and warm wind in the grass.",
        affords={"flower", "string", "shell"},
    ),
}

WANTS = {
    "violet_flower": Want(
        id="violet_flower",
        verb="pick the violet flower",
        repeated_verb="pick the violet flower again",
        object_label="flower",
        object_phrase="a small violet flower",
        object_color="violet",
        trouble="the stem kept bending",
        obstacle="the flower was tucked between thorns",
        helper="a careful twist",
        result_image="a neat violet flower sat in the little basket",
        tags={"violet", "flower", "repeat"},
    ),
    "violet_ribbon": Want(
        id="violet_ribbon",
        verb="loop the violet ribbon",
        repeated_verb="loop the violet ribbon again",
        object_label="ribbon",
        object_phrase="a bright violet ribbon",
        object_color="violet",
        trouble="the knot kept slipping",
        obstacle="the ribbon slid off the wooden peg",
        helper="a slow, steady loop",
        result_image="a tidy violet ribbon stayed tied around the box",
        tags={"violet", "ribbon", "repeat"},
    ),
    "violet_string": Want(
        id="violet_string",
        verb="tie the violet string",
        repeated_verb="tie the violet string again",
        object_label="string",
        object_phrase="a thin violet string",
        object_color="violet",
        trouble="the ends kept coming loose",
        obstacle="the string was too slick for a quick knot",
        helper="a double knot",
        result_image="the violet string stayed snug and still",
        tags={"violet", "string", "repeat"},
    ),
}

ANIMALS = {
    "rabbit": {"kind": "animal", "species": "rabbit", "sound": "hop"},
    "mouse": {"kind": "animal", "species": "mouse", "sound": "squeak"},
    "squirrel": {"kind": "animal", "species": "squirrel", "sound": "chatter"},
    "duck": {"kind": "animal", "species": "duck", "sound": "waddle"},
}

NAMES = {
    "rabbit": ["Pip", "Mina", "Toby", "Luna"],
    "mouse": ["Nim", "Cora", "Pico", "Melly"],
    "squirrel": ["Suri", "Tansy", "Milo", "Fenn"],
    "duck": ["Dottie", "Pebble", "Nell", "Wren"],
}

CAREGIVERS = ["mother", "father", "grandmother", "grandfather", "aunt", "uncle"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def _safe_name(animal: str, name: Optional[str], rng: random.Random) -> str:
    if name:
        return name
    return rng.choice(NAMES[animal])


def _introduce(world: World, child: Entity, want: Want) -> None:
    world.say(
        f"{child.id} was a little {child.species} who loved anything {want.object_color}."
    )
    world.say(
        f"Every day, {child.id} liked to say, '{want.object_color}, {want.object_color}, {want.object_color}.'"
    )


def _setup(world: World, child: Entity, caregiver: Entity, want: Want, thing: Entity) -> None:
    world.say(
        f"One day, {child.id} and {child.pronoun('possessive')} {caregiver.label} went to {world.setting}."
    )
    world.say(world.facts["place_detail"])
    world.say(
        f"There {child.id} saw {thing.phrase} and wanted to {want.verb}."
    )


def _trouble(world: World, child: Entity, want: Want) -> None:
    child.memes["want"] = child.memes.get("want", 0.0) + 1.0
    child.memes["frustration"] = child.memes.get("frustration", 0.0) + 1.0
    world.say(
        f"But {want.obstacle}, and {want.trouble}."
    )
    world.say(
        f"{child.id} tried to {want.repeated_verb}."
    )
    world.say(
        f"'{want.object_color}, {want.object_color}, {want.object_color},' {child.id} said, trying again."
    )


def _resolve(world: World, child: Entity, caregiver: Entity, want: Want, thing: Entity) -> None:
    child.memes["patience"] = child.memes.get("patience", 0.0) + 1.0
    child.memes["frustration"] = 0.0
    thing.meters["held"] = 1.0
    world.say(
        f"{caregiver.label} smiled and showed {child.id} {want.helper}."
    )
    world.say(
        f"After that, {child.id} could {want.verb} without rushing."
    )
    world.say(
        f"At the end, {want.result_image}."
    )


def build_world(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    place = PLACES[params.place]
    want = WANTS[params.want]
    animal = ANIMALS[params.animal]

    world = World(setting=place.name, weather="soft morning")
    child = world.add(
        Entity(
            id=params.name,
            **animal,
            meters={"meters": 0.0},
            memes={"joy": 0.0},
        )
    )
    caregiver = world.add(
        Entity(
            id="Caregiver",
            kind="animal",
            species=params.caregiver,
            label=params.caregiver,
            memes={"care": 1.0},
        )
    )
    thing = world.add(
        Entity(
            id="violet_thing",
            kind="thing",
            species="thing",
            label=want.object_label,
            phrase=want.object_phrase,
            owner=child.id,
        )
    )

    world.facts.update(
        place=place,
        want=want,
        child=child,
        caregiver=caregiver,
        thing=thing,
        place_detail=place.detail,
    )

    _introduce(world, child, want)
    world.para()
    _setup(world, child, caregiver, want, thing)
    world.para()
    _trouble(world, child, want)
    _resolve(world, child, caregiver, want, thing)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    want: Want = f["want"]
    child: Entity = f["child"]
    caregiver: Entity = f["caregiver"]
    return [
        f"Write a gentle animal story for a young child that repeats the word '{want.object_color}' three times.",
        f"Tell a short story about a little {child.species} named {child.id} who wants to {want.verb} with help from a {caregiver.label}.",
        f"Write an animal story where repetition helps a small problem become easy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    want: Want = f["want"]
    child: Entity = f["child"]
    caregiver: Entity = f["caregiver"]
    place: Place = f["place"]

    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about a little {child.species} named {child.id}. {child.id} loves {want.object_color} things and keeps repeating that word.",
        ),
        QAItem(
            question=f"What did {child.id} want to do at {place.name}?",
            answer=f"{child.id} wanted to {want.verb} at {place.name}. The flower, ribbon, or string was lovely, but it needed patience.",
        ),
        QAItem(
            question=f"How did the caregiver help {child.id}?",
            answer=f"The {caregiver.label} helped by showing {want.helper}. That let {child.id} try again without rushing.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {child.id} was calmer and the {want.object_label} stayed neatly in place. The repeated tries turned into a successful finish.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    want: Want = f["want"]
    qs = [
        QAItem(
            question="What is violet?",
            answer="Violet is a color that sits between blue and purple. It can make flowers, ribbons, and clothes look soft and pretty.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing or saying the same thing again and again. Sometimes repetition helps you remember, practice, or finish a hard job.",
        ),
    ]
    if "flower" in want.tags:
        qs.append(
            QAItem(
                question="Why do flowers sometimes need careful touching?",
                answer="Some flowers have thin stems or thorns, so careful touching keeps them from bending or breaking.",
            )
        )
    if "ribbon" in want.tags:
        qs.append(
            QAItem(
                question="Why do ribbons slip sometimes?",
                answer="Ribbons can slip because they are smooth and light, so a slow knot or loop can hold them better.",
            )
        )
    return qs


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
want(W) :- desire(W).

repeat_theme(W) :- tags(W, repeat).
violet_theme(W) :- tags(W, violet).

compatible(P, W) :- place(P), want(W), affords(P, flower), violet_theme(W).
compatible(P, W) :- place(P), want(W), affords(P, ribbon), violet_theme(W).
compatible(P, W) :- place(P), want(W), affords(P, string), violet_theme(W).

showable(P, W) :- compatible(P, W), repeat_theme(W).

#show compatible/2.
#show showable/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        for thing in sorted(p.affords):
            lines.append(asp.fact("affords", pid, thing))
    for wid, w in WANTS.items():
        lines.append(asp.fact("desire", wid))
        for tag in sorted(w.tags):
            lines.append(asp.fact("tags", wid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Validation / parameter resolution
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for want_id, want in WANTS.items():
            if "violet" not in want.tags:
                continue
            if any(tag in place.affords for tag in {"flower", "ribbon", "string"}):
                out.append((place_id, want_id))
    return out


def explain_invalid(place: str, want: str) -> str:
    p = PLACES[place]
    w = WANTS[want]
    return (
        f"(No story: {p.name} does not support a satisfying violet repetition story for "
        f"{w.object_label}. Choose a place with flowers, ribbon, or string.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with violet repetition.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--want", choices=WANTS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--name")
    ap.add_argument("--caregiver", choices=CAREGIVERS)
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
    if args.place and args.want and (args.place, args.want) not in combos:
        raise StoryError(explain_invalid(args.place, args.want))

    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.want is None or c[1] == args.want)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")

    place, want = rng.choice(sorted(filtered))
    animal = args.animal or rng.choice(list(ANIMALS))
    caregiver = args.caregiver or rng.choice(CAREGIVERS)
    name = args.name or rng.choice(NAMES[animal])
    return StoryParams(place=place, want=want, animal=animal, name=name, caregiver=caregiver)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        lines.append(f"  {e.id}: {e.species} {' '.join(bits)}")
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
    StoryParams(place="garden", want="violet_flower", animal="rabbit", name="Pip", caregiver="mother"),
    StoryParams(place="barn", want="violet_ribbon", animal="mouse", name="Mina", caregiver="father"),
    StoryParams(place="meadow", want="violet_string", animal="squirrel", name="Suri", caregiver="aunt"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2.\n#show showable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, w in combos:
            print(f"  {p:8} {w}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.want} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
