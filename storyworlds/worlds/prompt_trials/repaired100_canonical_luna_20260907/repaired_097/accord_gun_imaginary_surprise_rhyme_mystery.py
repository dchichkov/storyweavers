#!/usr/bin/env python3
"""
Standalone storyworld: an imaginary accord, a harmless toy gun, and a rhyme
mystery with a surprising turn.

The world models a child-friendly mystery in which a spoken accord changes the
characters' choices, an imaginary "gun" is revealed to be a toy prop, and a
rhyme helps the group find the safe answer.
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
class StoryParams:
    seed: Optional[int] = None
    place: str = "moonlit museum"
    protagonist: str = "Luna"
    protagonist_type: str = "girl"
    companion: str = "Milo"
    companion_type: str = "boy"
    curator: str = "Ms. Vale"
    incident_id: int = 0
    telling_mode: int = 0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Room:
    place: str
    detail: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, room: Room):
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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


INCIDENTS = [
    {
        "title": "the silent pop",
        "premise": "A little red flag had vanished from the Moon Room, and a cardboard gun stood beneath the empty display hook.",
        "clue": "a three-line rhyme scratched on a card beside the hook",
        "rhyme": "When the moon is bright, look left, not right; where soft stars sleep, the flag takes flight.",
        "cause": "the curator had moved the flag into the planetarium basket while repairing its display stand",
        "action": "read the rhyme aloud, checked the basket without touching the toy gun, and asked the curator to confirm the move",
        "resolution": "The curator found the flag in the basket and explained that the cardboard gun was only an imaginary space-pirate prop.",
        "ending": "The red flag waved beside the star basket while the toy gun rested harmlessly under its sign.",
    },
    {
        "title": "the backwards bang",
        "premise": "A soft bang echoed in the costume gallery, yet the painted toy gun on the wall had not moved.",
        "clue": "a rhyme taped beneath the costume chest",
        "rhyme": "If a bang has no smoke and a clue has a rhyme, seek the loose lid before you lose time.",
        "cause": "a loose wooden lid had dropped when a draft crossed the room",
        "action": "followed the rhyme to the chest and called the curator before opening anything",
        "resolution": "The curator secured the lid and reminded everyone that the toy gun could make no real shot.",
        "ending": "The chest stayed shut, the gallery grew quiet, and the painted gun watched over a peaceful row of hats.",
    },
    {
        "title": "the vanishing star",
        "premise": "A silver star disappeared from a model rocket just after someone declared an imaginary accord.",
        "clue": "the accord's words, repeated in a rhyme on the floor",
        "rhyme": "No grabbing, no guessing, let truth lead the way; check hands and shelves before you say.",
        "cause": "Milo had placed the star in his pocket only to keep it from falling through a cracked model shelf",
        "action": "asked Milo kindly, checked the shelf with the curator, and kept the toy gun safely on its stand",
        "resolution": "Milo returned the star, and the group repaired the shelf before restoring the model.",
        "ending": "The silver star gleamed again, held by a new blue bracket.",
    },
]


OPENINGS = [
    "The mystery began with a surprise no one had planned.",
    "A quiet room can hide a loud question.",
    "The first clue looked ordinary until Luna noticed its rhyme.",
    "Every good mystery begins when one small detail refuses to fit.",
]


LESSONS = [
    "An accord is strongest when everyone keeps it, especially when a surprise makes guessing tempting.",
    "A rhyme can point the way, but careful questions must still test what it means.",
    "Imaginary danger should not become real blame; people deserve calm facts and kind words.",
    "A strange sound is a question, not proof that someone has done wrong.",
]


def reason_gate(params: StoryParams) -> None:
    if not params.place.strip():
        raise StoryError("place must not be empty")
    if not params.protagonist.strip() or not params.companion.strip():
        raise StoryError("the mystery needs two named investigators")
    if params.protagonist == params.companion:
        raise StoryError("the investigators must have different names")
    if params.incident_id < 0:
        raise StoryError("incident_id must be non-negative")


def build_world(params: StoryParams) -> World:
    room = Room(
        place=params.place,
        detail="Blue lamps made the exhibits glow, and every visitor walked on the marked path.",
        meters={"quiet": 1.0},
        memes={"curiosity": 0.0},
    )
    world = World(room)
    hero = world.add(Entity(
        "hero", "character", params.protagonist_type, params.protagonist,
        memes={"curiosity": 1.0, "worry": 0.0, "trust": 0.0},
    ))
    companion = world.add(Entity(
        "companion", "character", params.companion_type, params.companion,
        memes={"curiosity": 1.0, "worry": 0.0, "trust": 0.0},
    ))
    curator = world.add(Entity(
        "curator", "character", "woman", params.curator,
        memes={"patience": 1.0, "trust": 0.0},
    ))
    toy_gun = world.add(Entity(
        "toy_gun", "thing", "prop", "cardboard space-pirate gun",
        location="costume gallery",
        meters={"real_danger": 0.0, "imaginary": 1.0, "moved": 0.0},
    ))
    accord = world.add(Entity(
        "accord", "thing", "promise", "imaginary accord",
        meters={"kept": 0.0},
    ))
    rhyme = world.add(Entity(
        "rhyme", "thing", "clue", "three-line rhyme",
        location="display hook",
        meters={"read": 0.0, "useful": 1.0},
    ))
    world.facts.update(
        hero=hero,
        companion=companion,
        curator=curator,
        toy_gun=toy_gun,
        accord=accord,
        rhyme=rhyme,
    )
    return world


def tell(params: StoryParams) -> World:
    reason_gate(params)
    world = build_world(params)
    incident = INCIDENTS[params.incident_id % len(INCIDENTS)]
    lesson = LESSONS[(params.incident_id + params.telling_mode) % len(LESSONS)]
    opening = OPENINGS[params.telling_mode % len(OPENINGS)]

    hero = world.facts["hero"]
    companion = world.facts["companion"]
    curator = world.facts["curator"]
    toy_gun = world.facts["toy_gun"]
    accord = world.facts["accord"]
    rhyme = world.facts["rhyme"]

    world.facts.update(
        incident_title=incident["title"],
        premise=incident["premise"],
        clue=incident["clue"],
        rhyme_text=incident["rhyme"],
        cause=incident["cause"],
        action=incident["action"],
        resolution=incident["resolution"],
        ending=incident["ending"],
        lesson=lesson,
        solved=True,
    )

    world.say(
        f"Once upon a time, {hero.label} and {companion.label} visited {world.room.place}. "
        f"{world.room.detail} Before entering, they made an imaginary accord: they would ask before touching, "
        "follow clues before guessing, and leave every prop where an adult could check it."
    )
    accord.meters["kept"] = 1.0
    world.say(f"{opening} {incident['premise']}")
    world.say(
        f"The cardboard gun looked dramatic, but it was only an imaginary prop with no real firing power. "
        f"{hero.label} felt a flutter of worry. 'Let us solve the mystery by our accord,' {hero.label} said."
    )

    world.para()
    world.say(
        f"{companion.label} pointed to {incident['clue']}. 'The rhyme may tell us where to look,' "
        f"{companion.label} said. The card read, '{incident['rhyme']}'"
    )
    rhyme.meters["read"] = 1.0
    hero.memes["curiosity"] += 1.0
    companion.memes["trust"] += 1.0
    world.say(
        f"'I first thought the toy gun caused the trouble,' {companion.label} admitted. "
        f"'But a prop is not proof,' {hero.label} replied. 'We should ask {curator.label}.'"
    )
    world.say(
        f"Together they {incident['action']}. The evidence showed that {incident['cause']}."
    )

    world.para()
    toy_gun.meters["moved"] = 0.0
    hero.memes["worry"] = 0.0
    curator.memes["trust"] += 1.0
    world.say(incident["resolution"])
    world.say(
        f"{curator.label} smiled. 'Your accord helped,' {curator.label} said. "
        f"'You used the rhyme as a guide, but you still checked the facts.'"
    )
    world.say(
        f"{hero.label} and {companion.label} nodded. The lesson was clear: {lesson}"
    )
    world.say(incident["ending"])
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly mystery about {f['incident_title']} in which an imaginary accord keeps the search safe.",
        f"Use this rhyme as a clue: {f['rhyme_text']}",
        "Include a surprising but gentle reveal showing that the gun is only a harmless toy prop.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    curator = f["curator"]
    return [
        QAItem(
            f"What mystery did {hero.label} and {companion.label} investigate?",
            f"They investigated {f['premise'].lower()} They used the accord to investigate without grabbing or blaming.",
        ),
        QAItem(
            f"What clue helped solve {f['incident_title']}?",
            f"They found {f['clue']}. The rhyme said, '{f['rhyme_text']}'",
        ),
        QAItem(
            f"What surprising fact did the investigators learn about the gun?",
            f"They learned that the cardboard gun was an imaginary costume prop, not a real weapon, so it could not have caused real harm.",
        ),
        QAItem(
            f"What was the real cause of {f['incident_title']}?",
            f"The real cause was that {f['cause']}. The curator confirmed the explanation.",
        ),
        QAItem(
            f"How did the accord change what {hero.label} and {companion.label} did?",
            f"The accord led them to ask before touching, follow the rhyme, and check the facts with {curator.label} instead of making an accusation.",
        ),
        QAItem(
            f"What lesson did the mystery teach?",
            f"It taught that {f['lesson']}",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        "What is an accord?",
        "An accord is an agreement or promise between people about what they will do.",
    ),
    QAItem(
        "What is a rhyme?",
        "A rhyme is a set of words or lines with matching sounds, often used to make a clue easy to remember.",
    ),
    QAItem(
        "What does imaginary mean?",
        "Imaginary means existing in pretend play or in the mind rather than being physically real.",
    ),
    QAItem(
        "Why should a child ask before touching a museum prop?",
        "A child should ask first because an adult can explain whether the prop is safe, fragile, or part of an exhibit.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if entity.location:
            bits.append(f"location={entity.location}")
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {entity.id:10} ({entity.type:8}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_accord :- accord(accord), kept(accord).
imaginary_prop(gun) :- prop(gun), imaginary(gun), real_danger(gun,0).
rhyme_ready :- clue(rhyme), read(rhyme), useful(rhyme).
coherent :- safe_accord, imaginary_prop(gun), rhyme_ready, mystery_solved.
#show coherent/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("accord", "accord"),
        asp.fact("kept", "accord"),
        asp.fact("prop", "gun"),
        asp.fact("imaginary", "gun"),
        asp.fact("real_danger", "gun", 0),
        asp.fact("clue", "rhyme"),
        asp.fact("read", "rhyme"),
        asp.fact("useful", "rhyme"),
        asp.fact("mystery_solved"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show coherent/0."))
    asp_ok = any(symbol.name == "coherent" for symbol in model)
    py_ok = True
    if asp_ok != py_ok:
        print("MISMATCH between ASP and Python reasonableness gate.")
        return 1
    sample = generate(StoryParams())
    if not sample.story or "rhyme" not in sample.story.lower():
        print("MISMATCH: generated story check failed.")
        return 1
    print("OK: ASP and Python reasonableness gate agree.")
    print("OK: generated story check passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Imaginary accord, toy gun, and rhyme mystery storyworld."
    )
    parser.add_argument("--place", default="moonlit museum")
    parser.add_argument("--protagonist")
    parser.add_argument("--protagonist-type", choices=["girl", "boy", "woman", "man"], default="girl")
    parser.add_argument("--companion")
    parser.add_argument("--companion-type", choices=["girl", "boy", "woman", "man"], default="boy")
    parser.add_argument("--curator", default="Ms. Vale")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, sample_seed: int) -> StoryParams:
    protagonist = args.protagonist or rng.choice(["Luna", "Iris", "Nia", "Mara"])
    companion = args.companion or rng.choice(["Milo", "Theo", "Pip", "Ari"])
    if protagonist == companion:
        raise StoryError("protagonist and companion must have different names")
    return StoryParams(
        seed=args.seed,
        place=args.place,
        protagonist=protagonist,
        protagonist_type=args.protagonist_type,
        companion=companion,
        companion_type=args.companion_type,
        curator=args.curator,
        incident_id=sample_seed % len(INCIDENTS),
        telling_mode=(sample_seed // len(INCIDENTS)) % len(OPENINGS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show coherent/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print("ASP model:", asp.one_model(asp_program("#show coherent/0.")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(seed=base_seed, protagonist="Luna", companion="Milo", incident_id=0),
            StoryParams(seed=base_seed + 1, protagonist="Iris", companion="Theo", incident_id=1),
            StoryParams(seed=base_seed + 2, protagonist="Nia", companion="Pip", incident_id=2),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        for offset in range(max(args.n, 1) * 20):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            try:
                params = resolve_params(args, random.Random(seed), seed)
                params.seed = seed
                sample = generate(params)
            except StoryError:
                continue
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
