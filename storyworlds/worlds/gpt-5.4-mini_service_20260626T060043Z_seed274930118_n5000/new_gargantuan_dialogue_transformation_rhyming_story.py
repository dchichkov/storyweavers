#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/new_gargantuan_dialogue_transformation_rhyming_story.py
=============================================================================================

A small standalone storyworld built from the seed prompt:
- style: Rhyming Story
- instruments: Dialogue, Transformation
- seed words: new, gargantuan

Domain premise:
A child brings home a new gargantuan paper dragon. It is far too large for the
playroom, so a worried parent and a delighted child talk it through, then use a
careful folding transformation to turn the giant thing into a cozy parade banner.

The simulated world tracks:
- physical size and fold state
- emotional pride, worry, and joy
- whether the dragon fits the room
- whether the transformation has happened

The prose is authored from state changes, not from a frozen template.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    fits_large: bool = False
    fits_medium: bool = True
    fits_small: bool = True


@dataclass
class DragonSpec:
    name: str
    phrase: str
    initial_size: str  # gargantuan
    final_form: str    # banner, kite, or lantern
    final_size: str    # neat, small, roomy
    transformation: str
    rhyme_word: str
    place_ok: set[str]


@dataclass
class StoryParams:
    place: str
    dragon: str
    name: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _m(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _v(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + delta


def _e(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + delta


def _is_large(dragon: Entity) -> bool:
    return _m(dragon, "size") >= 1.0 and dragon.attrs.get("form") == "gargantuan"


def _fits(world: World, dragon: Entity) -> bool:
    return _m(dragon, "size") < 1.0 or world.place.fits_large


def setup(world: World, child: Entity, parent: Entity, dragon: Entity) -> None:
    world.say(
        f"{child.id} found a new gargantuan paper dragon, bright as a dawn-lit day. "
        f"{child.pronoun().capitalize()} grinned and gave a squeal, " 
        f'"It is new," {child.pronoun()} said, "and huge in a shiny way!"'
    )
    _e(child, "delight", 1)
    _e(child, "pride", 1)
    _v(dragon, "size", 2)


def arrive(world: World, child: Entity, parent: Entity, dragon: Entity) -> None:
    world.say(
        f"Then {child.id} marched to {world.place.name} to show the prize with cheer, "
        f"but {parent.id} blinked and said, " 
        f'"That dragon is gargantuan, my dear."'
    )
    _e(parent, "worry", 1)
    if not _fits(world, dragon):
        _e(parent, "concern", 1)
        _v(dragon, "blocked", 1)


def dialogue_turn(world: World, child: Entity, parent: Entity, dragon: Entity) -> None:
    world.say(
        f'"It is my new dragon," {child.id} cried, "its wings are wide and free!" '
        f'"Aye," {parent.id} said, "but it does not fit the room for me."'
    )
    _e(child, "want", 1)
    _e(child, "stubborn", 1)
    _e(parent, "patience", 1)


def predict_fix(world: World, dragon: Entity) -> bool:
    sim = world.copy()
    d = sim.get(dragon.id)
    return _m(d, "size") >= 1.0 and sim.place.fits_large is False


def transform(world: World, child: Entity, parent: Entity, dragon: Entity, spec: DragonSpec) -> bool:
    if not predict_fix(world, dragon):
        return False
    world.say(
        f'"Then let us fold it slow," said {parent.id}, "and sing a tiny tune; '
        f"we'll turn this gargantuan dragon into {spec.final_form} by noon.""
    )
    _e(parent, "helpfulness", 1)
    _e(child, "hope", 1)
    dragon.attrs["form"] = spec.final_form
    dragon.attrs["shape"] = spec.final_size
    dragon.meters["size"] = 0.4
    dragon.meters["folds"] = dragon.meters.get("folds", 0.0) + 1
    _e(dragon, "changed", 1)
    return True


def finish(world: World, child: Entity, parent: Entity, dragon: Entity, spec: DragonSpec) -> None:
    _e(child, "joy", 1)
    _e(parent, "relief", 1)
    world.say(
        f"{child.id} clapped and laughed, " 
        f'"Oh, what a splendid sight! My dragon is now {spec.final_form}, '
        f"small and neat and light."'
    )
    world.say(
        f"So they hung {dragon.pronoun('object')} by the window, where it swayed like a gentle spark; "
        f"the new little banner glowed at dusk, and the room felt warm and bright and smart."
    )


PLACES = {
    "playroom": Place(name="the playroom", fits_large=False),
    "hall": Place(name="the hall", fits_large=False),
    "yard": Place(name="the yard", fits_large=False),
    "attic": Place(name="the attic", fits_large=True),
}

DRAGONS = {
    "banner": DragonSpec(
        name="paper dragon",
        phrase="a paper dragon",
        initial_size="gargantuan",
        final_form="a parade banner",
        final_size="neat",
        transformation="folding",
        rhyme_word="glow",
        place_ok={"playroom", "hall", "yard", "attic"},
    ),
    "kite": DragonSpec(
        name="paper dragon",
        phrase="a paper dragon",
        initial_size="gargantuan",
        final_form="a kite",
        final_size="small",
        transformation="rolling",
        rhyme_word="breeze",
        place_ok={"yard", "attic"},
    ),
    "lantern": DragonSpec(
        name="paper dragon",
        phrase="a paper dragon",
        initial_size="gargantuan",
        final_form="a lantern",
        final_size="small",
        transformation="tucking",
        rhyme_word="gleam",
        place_ok={"playroom", "hall", "attic"},
    ),
}

CHILDREN = ["Mia", "Leo", "Nora", "Ben", "Ava", "Finn", "Lily", "Sam"]
PARENTS = ["mom", "dad", "mother", "father"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, p in PLACES.items():
        for dragon, spec in DRAGONS.items():
            if place in spec.place_ok:
                out.append((place, dragon))
    return out


def explain_rejection(place: str, dragon: str) -> str:
    spec = DRAGONS[dragon]
    return (
        f"(No story: {spec.phrase} as a gargantuan thing is not a good fit for {PLACES[place].name}. "
        f"Pick a place where the dragon can be transformed safely.)"
    )


def build_story(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    spec = DRAGONS[params.dragon]

    child = world.add(Entity(id=params.name, kind="character", type="child"))
    parent = world.add(Entity(id=params.parent, kind="character", type=params.parent))
    dragon = world.add(Entity(
        id="dragon",
        kind="thing",
        type="dragon",
        label="dragon",
        phrase=spec.phrase,
        owner=child.id,
        meters={"size": 0.0},
        attrs={"form": "gargantuan", "shape": spec.initial_size},
    ))

    setup(world, child, parent, dragon)
    world.para()
    arrive(world, child, parent, dragon)
    dialogue_turn(world, child, parent, dragon)
    world.para()
    if transform(world, child, parent, dragon, spec):
        finish(world, child, parent, dragon, spec)

    world.facts.update(
        child=child,
        parent=parent,
        dragon=dragon,
        spec=spec,
        place=params.place,
        resolved=dragon.attrs.get("form") == spec.final_form,
    )

    prompts = [
        f'Write a short rhyming story with the words "new" and "gargantuan" about a child and a parent talking kindly.',
        f"Tell a gentle story where {params.name} has a new gargantuan paper dragon and it changes form by careful teamwork.",
        f'Create a child-friendly rhyming tale with dialogue, where something huge becomes something useful and neat.',
    ]

    story_qa = [
        QAItem(
            question=f"What did {params.name} find?",
            answer=f"{params.name} found a new gargantuan paper dragon.",
        ),
        QAItem(
            question=f"Why did {params.parent} worry?",
            answer=f"{params.parent.capitalize()} worried because the dragon was gargantuan and did not fit neatly in {world.place.name}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{params.name} and {params.parent} folded the dragon into {spec.final_form}, and it looked small, neat, and bright at the end.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What does gargantuan mean?",
            answer="Gargantuan means very, very large.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another form.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is when characters speak to each other in a story.",
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


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld about a new gargantuan thing and a gentle transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--dragon", choices=DRAGONS)
    ap.add_argument("--name", choices=CHILDREN)
    ap.add_argument("--parent", choices=PARENTS)
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
    if args.place and args.dragon and args.place not in DRAGONS[args.dragon].place_ok:
        raise StoryError(explain_rejection(args.place, args.dragon))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.dragon is None or c[1] == args.dragon)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, dragon = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHILDREN)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(place=place, dragon=dragon, name=name, parent=parent)


ASP_RULES = r"""
place(playroom).
place(hall).
place(yard).
place(attic).

dragon(banner).
dragon(kite).
dragon(lantern).

fits_large(attic).

place_ok(playroom,banner).
place_ok(hall,banner).
place_ok(yard,banner).
place_ok(attic,banner).

place_ok(yard,kite).
place_ok(attic,kite).

place_ok(playroom,lantern).
place_ok(hall,lantern).
place_ok(attic,lantern).

valid(P,D) :- place_ok(P,D), place(P), dragon(D).
"""


def asp_facts() -> str:
    lines = []
    for p in PLACES:
        lines.append(f"place({p}).")
    for d in DRAGONS:
        lines.append(f"dragon({d}).")
    for p, d in valid_combos():
        lines.append(f"place_ok({p},{d}).")
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _lazy_asp():
    import asp
    return asp


def asp_valid_combos() -> list[tuple]:
    asp = _lazy_asp()
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


def generate_many(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(50, args.n * 50):
        seed = base_seed + i
        i += 1
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


CURATED = [
    StoryParams(place="playroom", dragon="banner", name="Mia", parent="mom"),
    StoryParams(place="yard", dragon="kite", name="Leo", parent="dad"),
    StoryParams(place="hall", dragon="lantern", name="Nora", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid place/dragon combos:\n")
        for p, d in combos:
            print(f"  {p:9} {d}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = generate_many(args)

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
