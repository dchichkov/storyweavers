#!/usr/bin/env python3
"""
A small detective storyworld about a mammoth, a triangle, and a puzzling
laundry-room mystery.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""
    owner: Optional[str] = None

    def __post_init__(self) -> None:
        for key in ("wet", "clean", "missing", "care", "worry", "curiosity", "trust"):
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)


@dataclass
class Setting:
    place: str = "the laundry room"
    affords: set[str] = field(default_factory=lambda: {"wash", "sort", "dry"})


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    name: str
    animal: str
    helper: str
    seed: Optional[int] = None
    case: str = "sock_switch"
    telling: int = 0


CASES = {
    "sock_switch": {
        "clue": "a tiny blue thread caught on the triangle's lowest corner",
        "surface": "the mammoth's clean red sock had vanished from the folding table",
        "wrong": "the basket of dirty clothes must have swallowed it",
        "twist": "the triangle was not a lost toy at all; it was a laundry-room sign that had been moved to hide the sock",
        "method": "followed the blue thread from the triangle to the warm dryer",
        "resolution": "found the sock tucked behind the dryer where a loose sign had pushed it",
        "ending": "The triangle went back on the shelf, and the red sock swung from the line like a little flag.",
    },
    "soap_shadow": {
        "clue": "three clean points in the soap dust beside the drain",
        "surface": "a yellow towel had disappeared after the morning wash",
        "wrong": "someone had carried it away with the empty soap box",
        "twist": "the triangle-shaped mark was made by the towel's folded corner, not by a footprint",
        "method": "compared the dust mark with the towel's stitched corner",
        "resolution": "lifted the towel from beneath the rolling laundry cart",
        "ending": "The soap dust was swept away, and the yellow towel dried beside the mammoth's scarf.",
    },
    "button_case": {
        "clue": "a silver button resting inside the triangle's hollow center",
        "surface": "the mammoth's striped scarf was missing one bright button",
        "wrong": "the washing machine had shaken the button into its secret belly",
        "twist": "the triangle had been used as a tray while someone repaired the scarf",
        "method": "matched the button's stripes with the scarf's empty stitch marks",
        "resolution": "asked the helper about the sewing basket and found the scarf waiting for repair",
        "ending": "The button was sewn on, and the triangle became the family's official tiny repair tray.",
    },
    "raincoat": {
        "clue": "a damp yellow fleck on the triangle's polished edge",
        "surface": "the mammoth's raincoat was missing from the drying rack",
        "wrong": "the coat had slipped into the washer with the blankets",
        "twist": "the triangle was a tag from the coat's pocket, placed on the shelf by mistake",
        "method": "tracked the yellow flecks toward the back door",
        "resolution": "found the raincoat hanging outside where it could drip without soaking the room",
        "ending": "The coat dried in the sun, while the triangle tag rested safely beside the clean baskets.",
    },
}

NAMES = ["Luna", "Milo", "Nia", "Toby", "Pippa"]
HELPERS = ["Grandma", "Dad", "Aunt May", "Uncle Ben"]
ANIMALS = ["mammoth", "rabbit", "otter", "badger"]

OPENINGS = [
    "{name} the {animal} loved solving small mysteries.",
    "In the laundry room, {name} the {animal} noticed details everyone else missed.",
    "{name} the {animal} kept a detective notebook beside the clean towels.",
    "The laundry room was full of swishes, drips, and clues, and {name} listened to all of them.",
]

DIALOGUE = [
    '"A mystery needs evidence, not a guess," said {helper}.',
    '"Tell me what you saw before you tell me what you think," said {helper}.',
    '"Could the triangle be part of the answer?" asked {name}.',
    '"Then let us follow the clue carefully," said {helper}.',
]


def validate(params: StoryParams) -> None:
    if params.case not in CASES:
        raise StoryError(f"Unknown laundry-room case: {params.case}")
    if not params.name.strip():
        raise StoryError("A detective needs a name.")
    if params.animal != "mammoth":
        raise StoryError("This canonical case requires a mammoth detective.")
    if params.helper.strip() == params.name.strip():
        raise StoryError("The helper must be a different character from the detective.")


def build_world(params: StoryParams) -> World:
    validate(params)
    case = CASES[params.case]
    world = World(Setting())
    hero = world.add(Entity("hero", "character", params.name, params.animal, location="laundry room"))
    helper = world.add(Entity("helper", "character", params.helper, "person", location="laundry room"))
    triangle = world.add(Entity("triangle", "object", "triangle", "triangle", location="shelf"))
    missing = world.add(Entity("missing_item", "object", "missing laundry item", "laundry", location="unknown"))
    hero.memes["curiosity"] = 1.0
    hero.memes["trust"] = 1.0
    triangle.meters["clean"] = 1.0
    world.facts.update(
        hero=hero,
        helper=helper,
        triangle=triangle,
        missing=missing,
        case_id=params.case,
        clue=case["clue"],
        surface=case["surface"],
        wrong=case["wrong"],
        twist=case["twist"],
        method=case["method"],
        resolution=case["resolution"],
        ending=case["ending"],
        twist_revealed=False,
        solved=False,
    )
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    case = CASES[params.case]
    rng = random.Random((params.seed or 0) ^ 0x753A)
    hero = world.facts["hero"]
    helper = world.facts["helper"]

    opening = OPENINGS[params.telling % len(OPENINGS)].format(
        name=params.name, animal=params.animal
    )
    world.say(opening)
    world.say(
        f"One morning in the laundry room, {case['surface']}. "
        f"Near the clean towels, a bright triangle sat at an odd angle."
    )
    world.say(f"{params.name} picked up a notebook, but {helper.label} shook their head.")
    world.say(rng.choice(DIALOGUE).format(name=params.name, helper=helper.label))

    world.para()
    world.say(
        f"The first guess was that {case['wrong']}. "
        f"{params.name} nearly followed that guess to the hamper."
    )
    world.say(
        f"Then {params.name} noticed {case['clue']}. "
        "That small detail did not fit the first explanation."
    )
    world.say(
        f'"A triangle may be a shape, but it can also point somewhere," {params.name} said.'
    )
    world.say(
        f'"Good detectives ask what changed," {helper.label} replied. '
        '"Look at the room as if you have never seen it before."'
    )

    hero.memes["curiosity"] += 1.0
    hero.memes["worry"] = 1.0
    world.para()
    world.say(
        f"Together they examined the shelf, the washer, and the warm dryer. "
        f"The clue led them as they {case['method']}."
    )
    world.say(
        f"At last, the twist appeared: {case['twist']}."
    )
    world.facts["twist_revealed"] = True
    hero.memes["worry"] = 0.0
    hero.memes["trust"] += 1.0
    world.say(
        f"{params.name} did not blame the basket. Instead, the detective {case['resolution']}."
    )
    world.facts["solved"] = True
    world.facts["missing"].location = "found"
    world.facts["missing"].meters["clean"] = 1.0

    world.para()
    world.say(
        f"The mystery was solved because {params.name} checked the clue before choosing a culprit."
    )
    world.say(case["ending"])
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a detective story about {hero.label}, a mammoth, solving a laundry-room mystery involving a triangle.",
        f"Include this clue: {f['clue']}. Make the twist reveal why the triangle mattered.",
        f"End with this concrete image: {f['ending']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        QAItem(
            "Who solved the laundry-room mystery?",
            f"{hero.label}, a young mammoth, solved the mystery by observing clues instead of blaming the laundry basket.",
        ),
        QAItem(
            "What problem did the detective find?",
            f"The problem was that {f['surface']}.",
        ),
        QAItem(
            "What clue changed the investigation?",
            f"The clue was {f['clue']}. It did not fit the first guess, so {hero.label} looked more closely.",
        ),
        QAItem(
            "What was the twist?",
            f"The twist was that {f['twist']}.",
        ),
        QAItem(
            "How was the mystery solved?",
            f"{hero.label} and {helper.label} {f['method']}, and then {f['resolution']}.",
        ),
        QAItem(
            "What lesson did the detective learn?",
            f"The detective learned to check evidence before deciding who or what caused a problem.",
        ),
        QAItem(
            "What final image proves the mystery was over?",
            f"The final image is: {f['ending']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a triangle?",
            "A triangle is a flat shape with three straight sides and three corners.",
        ),
        QAItem(
            "What is a mammoth?",
            "A mammoth was a large, hairy relative of the elephant that lived long ago.",
        ),
        QAItem(
            "What happens in a laundry room?",
            "People wash, dry, fold, and sort clothes in a laundry room.",
        ),
        QAItem(
            "What is a detective clue?",
            "A detective clue is a detail that helps someone understand what happened.",
        ),
        QAItem(
            "What is a twist in a story?",
            "A twist is a surprising change in what the reader thinks is happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: type={entity.type}, location={entity.location}, "
            f"meters={meters}, memes={memes}"
        )
    lines.append(f"  twist_revealed={world.facts.get('twist_revealed')}")
    lines.append(f"  solved={world.facts.get('solved')}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "laundry_room"),
            asp.fact("object", "triangle"),
            asp.fact("character", "mammoth"),
            asp.fact("has_clue", "triangle"),
            asp.fact("has_twist", "laundry_room"),
            asp.fact("evidence_required", "mystery"),
        ]
    )


ASP_RULES = r"""
valid_world :- setting(laundry_room), object(triangle), character(mammoth).
detective_case :- valid_world, has_clue(triangle), has_twist(laundry_room).
reasonable :- detective_case, evidence_required(mystery).
#show valid_world/0.
#show detective_case/0.
#show reasonable/0.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set(asp.atoms(model, "reasonable"))
    if atoms == {()}:
        print("OK: ASP gate agrees with Python reasonableness.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    print("ASP atoms:", sorted(atoms))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detective Story world: triangle, mammoth, laundry room, twist."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--animal", choices=ANIMALS, default="mammoth")
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--case", choices=sorted(CASES))
    parser.add_argument("--telling", type=int, choices=range(len(OPENINGS)))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    if helper == name:
        helper = "Grandma"
    return StoryParams(
        name=name,
        animal="mammoth",
        helper=helper,
        seed=args.seed,
        case=args.case or rng.choice(list(CASES)),
        telling=args.telling if args.telling is not None else rng.randrange(len(OPENINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, name in enumerate(NAMES):
            params = StoryParams(
                name=name,
                animal="mammoth",
                helper=HELPERS[index % len(HELPERS)],
                seed=base_seed + index,
                case=list(CASES)[index % len(CASES)],
                telling=index % len(OPENINGS),
            )
            samples.append(generate(params))
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.asp:
        print(asp_program())
        return

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
