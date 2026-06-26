#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/great_transformation_sharing_rhyming_story.py
=========================================================================================================================

A small story world for a rhyming tale about great transformation through sharing.

Premise:
- A child and a helper discover a plain, unfinished thing.
- By sharing colorful pieces, the plain thing changes into something great.
- The story reads like a rhyming picture-book tale with a clear turn and ending image.
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
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "subject": "it",
            "object": "it",
            "possessive": "its",
        }
        if self.type in {"girl", "mother", "woman"}:
            mapping = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.type in {"boy", "father", "man"}:
            mapping = {"subject": "he", "object": "him", "possessive": "his"}
        return mapping[case]


@dataclass
class Place:
    name: str
    affords: set[str] = field(default_factory=set)


@dataclass
class TransformKit:
    id: str
    label: str
    change_from: str
    change_to: str
    shared_good: str
    rhyme_word: str
    lift: str
    finish: str


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        return World(place=self.place, entities=copy.deepcopy(self.entities), facts=dict(self.facts), paragraphs=[[]])


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "garden": Place(name="the garden", affords={"collect", "transform"}),
    "playroom": Place(name="the playroom", affords={"collect", "transform"}),
    "workbench": Place(name="the workbench", affords={"collect", "transform"}),
}

KITS = {
    "glitter": TransformKit(
        id="glitter",
        label="glitter dust",
        change_from="plain",
        change_to="sparkly",
        shared_good="sparkles",
        rhyme_word="bright",
        lift="shared the glitter in the light",
        finish="shone with a great big glow",
    ),
    "paint": TransformKit(
        id="paint",
        label="paint pots",
        change_from="dull",
        change_to="rainbow-bright",
        shared_good="colors",
        rhyme_word="gleam",
        lift="shared the paint in a lovely stream",
        finish="became a great new dream",
    ),
    "stickers": TransformKit(
        id="stickers",
        label="star stickers",
        change_from="plain",
        change_to="starry",
        shared_good="stars",
        rhyme_word="shine",
        lift="shared the stickers, line by line",
        finish="looked great and just so fine",
    ),
}

BASE_OBJECTS = {
    "box": ("a plain cardboard box", "box"),
    "crown": ("a simple paper crown", "crown"),
    "kite": ("a little paper kite", "kite"),
}

NAMES = ["Mina", "Toby", "Lena", "Owen", "Pia", "Nico", "Ruby", "Jude"]
HELPERS = ["grandma", "grandpa", "mother", "father", "friend"]
TRAITS = ["cheerful", "curious", "gentle", "bright-eyed", "patient"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    object: str
    kit: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.object not in BASE_OBJECTS:
        raise StoryError("Unknown object.")
    if params.kit not in KITS:
        raise StoryError("Unknown transformation kit.")

    kit = KITS[params.kit]
    obj_phrase, _ = BASE_OBJECTS[params.object]
    if kit.change_from == "plain" and "plain" not in obj_phrase:
        return
    if kit.change_from == "dull" and "plain" not in obj_phrase and "simple" not in obj_phrase:
        return


def rhyming_line(a: str, b: str) -> str:
    return f"{a}, {b}."


def tell_story(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World(place=PLACES[params.place])

    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Mina", "Lena", "Pia", "Ruby"} else "boy"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper))
    base_text, base_type = BASE_OBJECTS[params.object]
    object_ent = world.add(Entity(
        id=params.object,
        type=base_type,
        label=base_type,
        phrase=base_text,
        owner=hero.id,
    ))
    kit = world.add(Entity(
        id=params.kit,
        type="kit",
        label=KITS[params.kit].label,
        owner=helper.id,
        shared_with={hero.id},
        meters={"color": 0.0},
    ))

    # Act 1: setup
    world.say(
        f"{hero.id} was {params.trait} and small, "
        f"and loved a little craft day most of all."
    )
    world.say(
        f"At {world.place.name}, {hero.id} saw {object_ent.phrase}; "
        f"it seemed plain, but it had a good tiny face."
    )
    world.say(
        f"{helper.id} came near with {kit.label} to share, "
        f"and said the best changes begin with care."
    )

    # Act 2: desire and sharing
    world.para()
    hero.memes["want"] = 1.0
    kit.shared_with.add(hero.id)
    world.say(
        f"{hero.id} wanted a wonder, a sparkle, a gleam, "
        f"so {helper.id} shared the {KITS[params.kit].shared_good} in a bright little stream."
    )
    world.say(
        f"They {KITS[params.kit].lift}, two hands side by side, "
        f"and the plain little object began to transform with pride."
    )

    # Act 3: transformation
    world.para()
    object_ent.meters["changed"] = 1.0
    object_ent.meters["great"] = 1.0
    object_ent.memes["joy"] = 1.0
    hero.memes["joy"] = 1.0
    helper.memes["joy"] = 1.0
    changed_name = {
        "glitter": "sparkly",
        "paint": "rainbow-bright",
        "stickers": "starry",
    }[params.kit]
    world.say(
        f"At last, the plain thing was not plain anymore; "
        f"it wore {changed_name} charm like a grin in the air."
    )
    world.say(
        f"It {KITS[params.kit].finish}, and {hero.id} clapped once more, "
        f"for sharing had made something great from the floor."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        object=object_ent,
        kit=kit,
        params=params,
        changed_name=changed_name,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    kit = KITS[p.kit]
    return [
        f'Write a short rhyming story for a young child about "{kit.shared_good}" and a great transformation through sharing.',
        f"Tell a gentle rhyming tale where {p.name} and {p.helper} share {kit.label} to change a plain object into something great.",
        f"Write a simple story that begins with a plain thing at {world.place.name} and ends with a happy shared transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    obj = world.facts["object"]
    kit = KITS[p.kit]
    return [
        QAItem(
            question=f"What did {p.name} and {p.helper} share to transform the {obj.label}?",
            answer=f"They shared {kit.label} together, which helped the plain object become {world.facts['changed_name']} and great.",
        ),
        QAItem(
            question=f"Where did the transformation happen in the story?",
            answer=f"It happened at {world.place.name}, where {p.name} and {p.helper} worked side by side.",
        ),
        QAItem(
            question=f"How did {hero.id} feel by the end?",
            answer=f"{hero.id} felt happy and proud, because sharing made the change happen and the ending looked great.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to share something?",
            answer="To share means to let someone else use, hold, or enjoy the same thing with you.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is a big change that turns something into a new form or new look.",
        ),
        QAItem(
            question="Why can sharing help make a project better?",
            answer="Sharing can help because two people can add ideas, tools, or colors together, and the result can be bigger and better than one person alone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        if e.shared_with:
            bits.append(f"shared_with={sorted(e.shared_with)}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/3.
#show compatible/3.

valid(P, O, K) :- place(P), object(O), kit(K),
                  transforms(K, O), affords(P, transform).

compatible(P, O, K) :- valid(P, O, K).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for oid, (_phrase, _typ) in BASE_OBJECTS.items():
        lines.append(asp.fact("object", oid))
    for kid, kit in KITS.items():
        lines.append(asp.fact("kit", kid))
        lines.append(asp.fact("transforms", kid, kit.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate.")
    if py - asp_set:
        print("only python:", sorted(py - asp_set))
    if asp_set - py:
        print("only asp:", sorted(asp_set - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for p in PLACES:
        for o in BASE_OBJECTS:
            for k in KITS:
                combos.append((p, o, k))
    return combos


# ---------------------------------------------------------------------------
# StorySample interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world about great transformation through sharing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=BASE_OBJECTS)
    ap.add_argument("--kit", choices=KITS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(PLACES))
    obj = args.object or rng.choice(list(BASE_OBJECTS))
    kit = args.kit or rng.choice(list(KITS))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, object=obj, kit=kit, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(place="garden", object="box", kit="glitter", name="Mina", helper="grandma", trait="cheerful"),
    StoryParams(place="playroom", object="crown", kit="stickers", name="Toby", helper="mother", trait="curious"),
    StoryParams(place="workbench", object="kite", kit="paint", name="Lena", helper="father", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3.\n#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp_valid_combos()
        print(f"{len(models)} compatible combos:")
        for p, o, k in models:
            print(f"  {p} {o} {k}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            seed = base_seed + i
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            header = f"### {p.name} / {p.kit} / {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
