#!/usr/bin/env python3
"""
A child-friendly space adventure about a flat robot, a curious brain, and teamwork.

Seed tale:
Luna and her helper Brainy orbit a quiet moon when their little rover loses its
way near a harmless nuclear-powered beacon. Curiosity helps them ask questions,
and teamwork helps them repair the beacon without taking unsafe risks.
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


PLACES = {
    "moon": "the silver moon",
    "station": "the little orbiting station",
    "asteroid": "a round-edged asteroid",
}

PLACE_DETAILS = {
    "moon": ("a field of pale dust", "a ridge shaped like a sleeping whale"),
    "station": ("the station's bright repair bay", "a window full of stars"),
    "asteroid": ("a patch of glittering space rock", "a slow-turning crater"),
}

NAMES = ["Luna", "Mira", "Nia", "Zara"]
HELPERS = ["Brainy", "Pip", "Orbit", "Nova"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    place: str
    name: str
    helper: str
    seed: Optional[int] = None


@dataclass
class Mission:
    signal: str
    object_name: str
    repair: str
    danger: str


MISSIONS = [
    Mission(
        signal="a blinking blue signal",
        object_name="the guidance beacon",
        repair="fit its loose star-map panel back into place",
        danger="a cracked power cover",
    ),
    Mission(
        signal="three soft beeps",
        object_name="the landing beacon",
        repair=" reconnect its silver antenna",
        danger="a warm nuclear power box",
    ),
    Mission(
        signal="a tiny red-and-gold flash",
        object_name="the moon beacon",
        repair="clear dust from its light sensor",
        danger="a humming power cable",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A space adventure about brain, flat, nuclear, curiosity, and teamwork."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
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
    return StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
    )


def tell(params: StoryParams, rng: random.Random) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.name not in NAMES:
        raise StoryError(f"Unknown explorer: {params.name}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")

    world = World(PLACES[params.place])
    hero = world.add(Entity(params.name, "character", params.name))
    helper = world.add(Entity("helper", "character", params.helper))
    rover = world.add(Entity("rover", "machine", "the flat rover", owner=params.name))
    beacon = world.add(Entity("beacon", "machine", "the nuclear-powered beacon"))
    brain = world.add(Entity("brain", "tool", "the thinking brain-board"))

    mission = rng.choice(MISSIONS)
    detail, landmark = PLACE_DETAILS[params.place]
    question = rng.choice(
        [
            "Why is the signal blinking?",
            "What part is asking for help?",
            "How can we fix it without touching the power box?",
        ]
    )
    discovery = rng.choice(
        [
            "The beacon was not broken all over; only its map panel had slipped loose.",
            "The beeps came from the sensor, which was covered by moon dust.",
            "The flash repeated whenever the antenna pointed away from the stars.",
        ]
    )

    hero.memes["curiosity"] = 1
    helper.memes["teamwork"] = 1
    brain.memes["reasoning"] = 1
    rover.meters["height"] = 0.4
    beacon.meters["power"] = 8.0
    beacon.memes["helpful"] = 1

    world.say(
        f"On {world.place}, {hero.label} piloted {rover.label} across {detail}. "
        f"The rover was flat enough to slide beneath low rocks, but its little screen suddenly went dark."
    )
    world.say(
        f"Nearby, {mission.signal} came from {mission.object_name}. "
        f"It used a safe nuclear power cell, yet its warning light was winking."
    )
    world.say(
        f"{hero.label} held up {brain.label}, a small board that could sort clues. "
        f"With curiosity bright in {hero.pronoun('possessive')} mind, {hero.label} asked, \"{question}\""
    )
    world.say(
        f"{helper.label} checked the rover's star chart and answered, \"Let's not guess. "
        "You watch the signal, and I will compare the chart with the beacon.\""
    )

    world.para()
    world.say(
        f"The two explorers worked as a team. {hero.label} counted the flashes while "
        f"{helper.label} turned the safe outside dial. The brain-board connected the pattern to the chart."
    )
    world.say(discovery)
    world.say(
        f"Then {hero.label} noticed {mission.danger}. \"We must not open that,\" "
        f"{hero.label} said. \"The nuclear power is useful, but it needs respect.\""
    )
    world.say(
        f"Together, they used a long insulated grabber to {mission.repair}. "
        f"The beacon glowed steadily, and the flat rover's screen woke with a cheerful map."
    )

    world.para()
    world.say(
        f"A path of golden arrows appeared across {landmark}. "
        f"{helper.label} laughed, \"Curiosity found the question!\""
    )
    world.say(
        f"{hero.label} replied, \"And teamwork found the answer.\" "
        f"Side by side, they followed the new path home while {mission.object_name} sent a calm light into space."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        rover=rover,
        beacon=beacon,
        brain=brain,
        mission=mission,
        question=question,
        discovery=discovery,
        landmark=landmark,
        detail=detail,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a space adventure about {f['hero'].label} using curiosity and teamwork to repair {f['mission'].object_name}.",
        "Tell a child-friendly story involving a brain, a flat rover, and a safe nuclear-powered beacon.",
        "Write a space adventure where asking a careful question prevents danger and teamwork solves the problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    helper = f["helper"].label
    mission = f["mission"]
    return [
        QAItem(
            question=f"What problem did {hero} and {helper} find in space?",
            answer=(
                f"They found that {mission.object_name} was sending {mission.signal}. "
                f"The beacon used a nuclear power cell, but its outside signal part needed repair."
            ),
        ),
        QAItem(
            question=f"How did curiosity help {hero}?",
            answer=(
                f"Curiosity led {hero} to ask {f['question'].lower()} instead of guessing. "
                f"The brain-board and the repeating signal helped the explorers discover that "
                f"{f['discovery'].lower()}"
            ),
        ),
        QAItem(
            question=f"How did teamwork keep the repair safe?",
            answer=(
                f"{hero} watched the signal while {helper} compared the star chart and turned "
                f"the safe outside dial. They used an insulated grabber and stayed away from "
                f"{mission.danger}, so they repaired the beacon without opening its nuclear power box."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn more by noticing things and asking questions.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people share jobs and help one another reach a goal.",
        ),
        QAItem(
            question="What does nuclear mean in this story?",
            answer=(
                "Nuclear describes the kind of power cell inside the beacon. The explorers treat "
                "that power carefully and repair only the safe outside parts."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
feature(curiosity).
feature(teamwork).
object(brain).
object(flat).
object(nuclear).
safe_repair :- feature(curiosity), feature(teamwork), object(brain), object(flat), object(nuclear).
valid_place(P) :- place(P), safe_repair.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("place", place) for place in PLACES)


def asp_program(show: str = "#show valid_place/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    found = set(asp.atoms(model, "valid_place"))
    expected = {(place,) for place in PLACES}
    if found != expected:
        print("MISMATCH between ASP and Python.")
        print("ASP:", sorted(found))
        print("PY:", sorted(expected))
        return 1
    for seed in range(5):
        params = StoryParams("moon", "Luna", "Brainy", seed)
        sample = generate(params)
        if not sample.story or "teamwork" not in sample.story.lower():
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP parity matches Python ({len(found)} places), and stories pass.")
    return 0


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    world = tell(params, rng)
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
        print("\n-- trace --")
        for entity in sample.world.entities.values():
            print(
                f"{entity.id}: kind={entity.kind} label={entity.label} "
                f"meters={entity.meters} memes={entity.memes}"
            )
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp or args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in PLACES:
            params = StoryParams(place, NAMES[0], HELPERS[0], base_seed)
            samples.append(generate(params))
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
