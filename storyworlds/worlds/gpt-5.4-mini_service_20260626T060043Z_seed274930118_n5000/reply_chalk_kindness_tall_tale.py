#!/usr/bin/env python3
"""
reply_chalk_kindness_tall_tale.py
=================================

A small storyworld about a big-hearted child, a piece of chalk, and a reply
that changes the shape of a day. The world keeps the action small and concrete
while leaning into a Tall Tale voice: one ordinary kindness grows so large it
seems to stretch clear across the block.

Seed image:
- A child finds chalk.
- Someone asks for help or makes a mistake.
- A kind reply turns the moment around.
- The ending proves the change with a vivid image.

This script is standalone and uses only the stdlib plus the shared Storyweavers
result containers. ASP support is provided as an inline twin for parity checks.
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    carrier: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    surfaces: set[str] = field(default_factory=set)
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    surface: str
    can_smudge: bool = False


@dataclass
class StoryParams:
    place: str
    object: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "sidewalk": Place(id="sidewalk", label="the sidewalk", outdoors=True if False else False, surfaces={"stone"}, affords={"draw", "build"}),
    "porch": Place(id="porch", label="the porch", surfaces={"wood"}, affords={"draw", "build"}),
    "schoolyard": Place(id="schoolyard", label="the schoolyard", surfaces={"pavement"}, affords={"draw", "build"}),
}

OBJECTS = {
    "chalk": ObjectCfg(
        id="chalk",
        label="chalk",
        phrase="a small box of bright sidewalk chalk",
        surface="stone",
        can_smudge=True,
    ),
    "bucket": ObjectCfg(
        id="bucket",
        label="bucket",
        phrase="a little bucket of chalk pieces",
        surface="wood",
        can_smudge=False,
    ),
}

GENDERS = {"girl", "boy"}
HELPERS = {
    "friend": "friend",
    "neighbor": "neighbor",
    "teacher": "teacher",
    "brother": "brother",
    "sister": "sister",
}
TRAITS = ["kind", "gentle", "cheerful", "brave", "bright", "patient"]


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def can_help_reply(reply: str) -> bool:
    return reply in {"share", "apologize", "invite", "encourage"}


def reply_text(reply: str) -> str:
    return {
        "share": "You can have half my chalk",
        "apologize": "I am sorry for the mess",
        "invite": "Come draw with me",
        "encourage": "It is all right; we can fix it together",
    }[reply]


def reply_effect(reply: str) -> tuple[float, float]:
    if reply == "share":
        return 1.5, 1.0
    if reply == "apologize":
        return 1.0, 1.2
    if reply == "invite":
        return 1.8, 0.8
    return 1.4, 1.0


def story_seed_to_tale(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    chalk = world.get("chalk")

    world.say(
        f"{hero.id} was a {hero.memes['trait_word']} child who walked as lightly as a raindrop "
        f"and noticed every little thing that wanted to be loved."
    )
    world.say(
        f"One day {hero.id} found {chalk.phrase} near {world.place.label}, and {hero.pronoun()} "
        f"treated it like a treasure dug out of a comet."
    )
    world.say(
        f"{hero.id} loved to draw big swirls and long roads, and the chalk sang against the ground "
        f"like a cricket with a thousand silver legs."
    )

    world.para()
    world.say(
        f"Then {helper.id} hurried over and asked for a reply, because a small worry had landed in "
        f"{helper.pronoun('possessive')} day: {helper.pronoun('possessive').capitalize()} hands were empty, "
        f"and the picture was growing unfinished."
    )
    world.say(
        f"{hero.id} looked at the last piece of chalk, looked at {helper.id}, and gave a {world.facts['reply_kind']} reply: "
        f"\"{reply_text(world.facts['reply_kind'])}.\""
    )

    kindness, calm = reply_effect(world.facts["reply_kind"])
    hero.memes["kindness"] += kindness
    helper.memes["joy"] += kindness
    helper.memes["calm"] += calm

    if world.facts["reply_kind"] == "share":
        chalk.meters["used"] += 0.5
    else:
        chalk.meters["used"] += 1.0

    world.say(
        f"That reply was so kind it seemed to shine brighter than a lantern on a moonless fencepost."
    )

    world.para()
    world.say(
        f"So {hero.id} broke the chalk in two with a careful thumb, and {helper.id} took the smaller half "
        f"as if it were a ribbon from a birthday cloud."
    )
    world.say(
        f"Together they drew a long picture across the {world.place.label.removeprefix('the ')}: a house, a hill, "
        f"a giant sunflower, and a dog tall enough to carry the whole afternoon on its back."
    )
    world.say(
        f"When the sun slid low, {helper.id} smiled so wide it nearly folded {helper.pronoun('possessive')} cheeks in half, "
        f"and {hero.id} went home with dusty fingers and a heart as roomy as the sky."
    )

    hero.memes["satisfaction"] += 1.5
    hero.meters["chalk_dust"] += 1.0
    world.facts["resolved"] = True
    world.facts["kindness"] = kindness


# ---------------------------------------------------------------------------
# Reasonable story generation constraints
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for obj_id, obj in OBJECTS.items():
            if obj.surface in place.surfaces and "draw" in place.affords:
                combos.append((place_id, obj_id))
    return combos


def explain_rejection(place: Place, obj: ObjectCfg) -> str:
    return (
        f"(No story: {obj.label} works best on {obj.surface}, but {place.label} does not fit that surface well "
        f"for this tale. Pick a place whose ground matches the chalk.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- location(P).
object(O) :- chalk(O).

compatible(P,O) :- location(P), chalk(O), surface(O,S), surface_of(P,S), draws(P).

helpful_reply(share).
helpful_reply(apologize).
helpful_reply(invite).
helpful_reply(encourage).

valid(P,O,R) :- compatible(P,O), helpful_reply(R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("location", pid))
        for s in sorted(place.surfaces):
            lines.append(asp.fact("surface_of", pid, s))
        if "draw" in place.affords:
            lines.append(asp.fact("draws", pid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("chalk", oid))
        lines.append(asp.fact("surface", oid, obj.surface))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((p, o, "share") for p, o in valid_combos()) | set((p, o, "apologize") for p, o in valid_combos()) | set((p, o, "invite") for p, o in valid_combos()) | set((p, o, "encourage") for p, o in valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(cl)} valid triples.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  only in ASP:", sorted(cl - py))
    print("  only in Python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a Tall Tale style story for a child who finds chalk at {world.place.label} and gives a kind reply.",
        f"Tell a short story where {f['hero_name']} shares chalk and a helpful reply changes the day.",
        f"Write a gentle tall tale with chalk, a reply, and kindness that ends with a big drawing."
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    chalk = f["chalk"]
    return [
        QAItem(
            question=f"Who found the chalk at {world.place.label}?",
            answer=f"{hero.id} found the chalk at {world.place.label} and treated it like a treasure.",
        ),
        QAItem(
            question=f"What kind of reply did {hero.id} give when {helper.id} needed help?",
            answer=f"{hero.id} gave a kind reply: \"{reply_text(f['reply_kind'])}.\"",
        ),
        QAItem(
            question=f"What happened after {hero.id} shared the chalk?",
            answer=f"{hero.id} and {helper.id} drew together, and the day turned cheerful and bright.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chalk used for?",
            answer="Chalk is used for drawing and writing on rough surfaces like sidewalks or blackboards.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means doing or saying something gentle and helpful so another person feels cared for.",
        ),
        QAItem(
            question="What is a reply?",
            answer="A reply is an answer you give when someone speaks to you or asks you something.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.object and args.object not in OBJECTS:
        raise StoryError("Unknown object.")
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.object:
        combos = [c for c in combos if c[1] == args.object]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj = rng.choice(sorted(combos))
    name = args.name or rng.choice(["Mina", "Leo", "June", "Toby", "Ivy", "Nico"])
    gender = args.gender or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice(list(HELPERS))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, object=obj, name=name, gender=gender, helper=helper, trait=trait)


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        memes={"trait_word": params.trait, "kindness": 0.0, "joy": 0.0, "satisfaction": 0.0},
        meters={"chalk_dust": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type="child" if params.helper in {"friend", "neighbor", "brother", "sister"} else "adult",
        memes={"joy": 0.0, "calm": 0.0},
    ))
    chalk = world.add(Entity(
        id="chalk",
        kind="thing",
        label="chalk",
        phrase=OBJECTS[params.object].phrase,
        owner=hero.id,
        carrier=hero.id,
        meters={"used": 0.0},
    ))

    world.facts.update(
        hero=hero,
        helper=helper,
        chalk=chalk,
        reply_kind="share",
        resolved=True,
    )
    story_seed_to_tale(world)
    return world


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about chalk, a reply, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=sorted(GENDERS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--trait", choices=TRAITS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, obj in sorted(valid_combos()):
            params = StoryParams(
                place=place,
                object=obj,
                name="Mina",
                gender="girl",
                helper="friend",
                trait="kind",
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
