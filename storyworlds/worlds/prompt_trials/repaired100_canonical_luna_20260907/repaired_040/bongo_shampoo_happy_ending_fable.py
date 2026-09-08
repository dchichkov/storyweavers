#!/usr/bin/env python3
"""
bongo_shampoo_happy_ending_fable.py
===================================

A small fable world about a bongo drum, a bottle of shampoo, and the
difference between making a loud promise and keeping a gentle one.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Fable:
    id: str
    lesson: str
    problem: str
    repair: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "orchard": Setting(
        id="orchard",
        place="the sunny orchard",
        affords={"wash", "music"},
    ),
}

FABLES = {
    "bongo_shampoo": Fable(
        id="bongo_shampoo",
        lesson="A loud promise is small beside a quiet kindness kept.",
        problem="the bongo had been left dusty after the village wash, and its deep voice had gone dull",
        repair="washed the bongo with a little shampoo, dried it in the warm shade, and invited the worried donkey to help tune it",
        ending="the clean bongo sounded bright beneath the apple trees, while every friend danced in a happy circle",
    ),
}

ANIMAL_NAMES = ["Luna", "Milo", "Pippa", "Nora", "Bram"]
ANIMAL_TYPES = ["rabbit", "fox", "badger", "squirrel", "mouse"]
TRAITS = ["patient", "cheerful", "curious", "gentle", "brave"]

OPENINGS = [
    "In the sunny orchard, {hero} the {species} found a bongo beside the wash basin.",
    "One bright morning, {hero}, a {trait} {species}, carried a little bongo beneath the apple trees.",
    "The orchard was waking when {hero} the {species} heard a sad thump from an old bongo.",
    "At the edge of the orchard, {hero} discovered a bottle of shampoo and a dusty bongo waiting nearby.",
]

DIALOGUE = [
    '"I can make it loud again!" {hero} cried. "But first, let us learn what it needs."',
    '"Do not splash too fast," said {helper}. "The bongo is wood, and wood likes gentle care."',
    '"I was hoping for a grand song," {helper} admitted. "Could we make the first kind choice together?"',
    '"A clean drum may sing," said {hero}, "but a cared-for friend makes the happiest music."',
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (place, "bongo_shampoo", "orchard")
        for place, setting in SETTINGS.items()
        if "wash" in setting.affords and "music" in setting.affords
    ]


ASP_RULES = r"""
place(orchard).
affords(orchard,wash).
affords(orchard,music).
fable(bongo_shampoo).
valid(Place,Fable,Instrument) :-
    place(Place),
    affords(Place,wash),
    affords(Place,music),
    fable(Fable),
    Instrument=bongo.
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for place, setting in SETTINGS.items():
        for affordance in sorted(setting.affords):
            lines.append(asp.fact("affords", place, affordance))
    for fable in FABLES:
        lines.append(asp.fact("fable", fable))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and clingo:")
    print("  only in Python:", sorted(py - clingo))
    print("  only in clingo:", sorted(clingo - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A fable about a bongo, shampoo, and a happy ending."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--fable", choices=FABLES)
    parser.add_argument("--name")
    parser.add_argument("--species", choices=ANIMAL_TYPES)
    parser.add_argument("--helper", choices=["donkey", "goat", "sparrow"])
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


@dataclass
class StoryParams:
    place: str
    fable: str
    name: str
    species: str
    helper: str
    trait: str
    seed: Optional[int] = None
    telling: int = 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if args.place is None or combo[0] == args.place
    ]
    if args.fable is not None:
        combos = [combo for combo in combos if combo[1] == args.fable]
    if not combos:
        raise StoryError("No valid orchard fable matches the requested options.")
    place, fable, _ = rng.choice(combos)
    return StoryParams(
        place=place,
        fable=fable,
        name=args.name or rng.choice(ANIMAL_NAMES),
        species=args.species or rng.choice(ANIMAL_TYPES),
        helper=args.helper or rng.choice(["donkey", "goat", "sparrow"]),
        trait=args.trait or rng.choice(TRAITS),
        telling=rng.randrange(1_000_000),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.fable not in FABLES:
        raise StoryError(f"Unknown fable: {params.fable}")

    setting = SETTINGS[params.place]
    fable = FABLES[params.fable]
    world = World(setting)
    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.species,
            label=params.name,
            memes={"eagerness": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper.capitalize(),
            kind="character",
            type=params.helper,
            label=params.helper,
            memes={"worry": 1.0},
        )
    )
    bongo = world.add(
        Entity(
            id="bongo",
            type="instrument",
            label="bongo",
            meters={"dust": 1.0, "voice": 0.0},
        )
    )
    shampoo = world.add(
        Entity(
            id="shampoo",
            type="soap",
            label="shampoo",
            meters={"cleaning": 1.0},
        )
    )

    rng = random.Random(params.telling)
    opening = rng.choice(OPENINGS).format(
        hero=params.name,
        species=params.species,
        trait=params.trait,
    )
    dialogue = rng.choice(DIALOGUE).format(
        hero=params.name,
        helper=helper.id,
    )
    turn = rng.choice(
        [
            "Then {hero} noticed that the drum was not asking for a louder hand; it was asking for a careful one.",
            "The dull sound changed {hero}'s plan from showing off to helping.",
            "For the first time, {hero} understood that music begins with listening.",
        ]
    ).format(hero=params.name)
    apology = rng.choice(
        [
            f'"I hurried past your worry," {params.name} said. "I am sorry."',
            f'"I wanted everyone to cheer for me," {params.name} admitted. "I should have helped first."',
            f'{params.name} bowed. "My bright idea became a careless one. Please let me repair it."',
        ]
    )

    world.say(opening)
    world.say(
        f"The {bongo.label} was dusty, and {fable.problem}; "
        f"even its deepest note sounded like a sleepy pebble."
    )
    world.para()
    world.say(
        f"{params.name} reached for the {shampoo.label}, hoping to make a grand show "
        f"before the orchard friends arrived."
    )
    world.say(dialogue)
    world.say(
        f"{helper.id} held the bongo steady while {params.name} used a small drop of shampoo "
        f"and a soft leaf to clean it."
    )
    world.say(turn)
    world.say(apology)
    world.para()
    world.say(
        f"Together, {params.name} and {helper.id} rinsed the bongo, dried it in the shade, "
        f"and tapped its skin very gently."
    )
    world.say(
        f"The bongo's voice grew warm and round. {helper.id} smiled, and {params.name} "
        f"let the helper make the first beat."
    )
    world.say(
        f"That was the happy ending: {fable.ending}. "
        f"The orchard learned that {fable.lesson}"
    )

    bongo.meters["dust"] = 0.0
    bongo.meters["voice"] = 1.0
    bongo.memes["cared_for"] = 1.0
    shampoo.meters["used"] = 1.0
    hero.memes["humility"] = 1.0
    hero.memes["kindness"] = 1.0
    helper.memes["trust"] = 1.0

    world.facts = {
        "hero": hero,
        "helper": helper,
        "bongo": bongo,
        "shampoo": shampoo,
        "fable": fable,
        "lesson": fable.lesson,
        "problem": fable.problem,
        "repair": fable.repair,
        "ending": fable.ending,
        "repaired": True,
    }

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    return [
        "Write a child-friendly fable with a happy ending.",
        f"Tell a fable in which {hero.id} learns to care for a bongo instead of showing off.",
        "Include bongo and shampoo, with a clear turn from carelessness to kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"]
    helper = facts["helper"]
    return [
        QAItem(
            question=f"What was wrong with the bongo?",
            answer=f"The bongo was dusty and its voice had gone dull, so {hero.id} could not make a cheerful song.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} help the bongo?",
            answer=f"They used a little shampoo and a soft leaf, then rinsed and dried the bongo gently in the shade.",
        ),
        QAItem(
            question=f"What changed {hero.id}'s plan?",
            answer=f"The dull bongo showed {hero.id} that careful listening and helping mattered more than making a loud show.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily: {facts['ending']}.",
        ),
        QAItem(
            question="What is the fable's lesson?",
            answer=f"The lesson is that {facts['lesson']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bongo?",
            answer="A bongo is a small hand drum that makes music when someone taps its stretched skin.",
        ),
        QAItem(
            question="What is shampoo?",
            answer="Shampoo is a gentle liquid used for washing hair or, in this fable, carefully cleaning a dusty object.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that teaches a lesson, often by giving animals or objects human-like choices.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is a closing that shows the main trouble has been safely resolved.",
        ),
        QAItem(
            question="Why should a wooden instrument be dried after washing?",
            answer="It should be dried so extra water does not damage the wood or change the instrument's sound.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
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
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"{entity.id}: {entity.type} meters={meters} memes={memes}"
        )
    lines.append(f"facts: repaired={world.facts.get('repaired')}")
    return "\n".join(lines)


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        place="orchard",
        fable="bongo_shampoo",
        name="Luna",
        species="rabbit",
        helper="donkey",
        trait="patient",
        telling=101,
    ),
    StoryParams(
        place="orchard",
        fable="bongo_shampoo",
        name="Milo",
        species="fox",
        helper="goat",
        trait="curious",
        telling=202,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(args.n, 0)):
            seed = base_seed + index
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as error:
                print(error)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No stories requested.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
