#!/usr/bin/env python3
"""A gentle bedtime world about a little nose, sharing, and a promise that returns."""

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
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass(frozen=True)
class Bed:
    id: str
    phrase: str
    detail: str


@dataclass(frozen=True)
class Comfort:
    id: str
    phrase: str
    detail: str


@dataclass
class Event:
    kind: str
    actor: str
    target: str
    text: str
    cause: str
    result: str


@dataclass
class StoryParams:
    bed: str
    comfort: str
    name: str
    gender: str
    helper: str
    trait: str
    problem: str = "sharing"
    seed: Optional[int] = None


BEDS = {
    "moon_bed": Bed("moon_bed", "a little bed beneath a moon-shaped quilt",
                    "A silver moon shone through the curtains."),
    "window_bed": Bed("window_bed", "a small bed beside the window",
                       "The stars blinked above the quiet garden."),
    "cloud_bed": Bed("cloud_bed", "a cozy bed piled with cloud-soft blankets",
                      "The room smelled of clean blankets and lavender."),
}

COMFORTS = {
    "rabbit": Comfort("rabbit", "a floppy-eared rabbit", "one ear was bent from many hugs"),
    "bear": Comfort("bear", "a small brown bear", "his button eyes shone in the lamplight"),
    "fox": Comfort("fox", "a soft orange fox", "her tail was warm and wide"),
}

NAMES = {
    "girl": ["Luna", "Mia", "Nora", "Ivy", "Ava"],
    "boy": ["Milo", "Theo", "Noah", "Leo", "Sam"],
}
TRAITS = ["thoughtful", "sleepy", "curious", "gentle", "hopeful"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]

KNOWLEDGE = {
    "nose": [
        QAItem("What can a nose do?",
                "A nose helps us smell things and breathe air."),
    ],
    "sharing": [
        QAItem("Why can sharing make someone feel cared for?",
                "Sharing shows another person that their feelings and needs matter to you."),
    ],
    "bedtime": [
        QAItem("Why do children sleep at bedtime?",
                "Sleep gives the body and mind a peaceful time to rest and grow."),
    ],
    "foreshadowing": [
        QAItem("What is a clue in a story?",
                "A clue is a small detail that prepares us for something that happens later."),
    ],
}


class World:
    def __init__(self, bed: Bed, comfort: Comfort) -> None:
        self.bed = bed
        self.comfort = comfort
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.turn = 0

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, kind: str, text: str, cause: str, result: str,
               actor: str, target: str) -> None:
        self.history.append(Event(kind, actor, target, text, cause, result))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def build_world(params: StoryParams) -> World:
    if params.bed not in BEDS or params.comfort not in COMFORTS:
        raise StoryError("That bedtime setting is not available.")
    if params.gender not in NAMES:
        raise StoryError("The child must have a supported gender.")
    if params.name in {"parent", "comfort", "nose", "bed"}:
        raise StoryError("The child's name collides with a story object.")

    world = World(BEDS[params.bed], COMFORTS[params.comfort])
    child = world.add(Entity(
        params.name, "character", params.gender, params.name,
        memes={"love": 1.0, "sleepiness": 0.0, "generosity": 0.0},
    ))
    helper = world.add(Entity(
        "parent", "character", params.helper, "the " + params.helper,
        memes={"patience": 1.0},
    ))
    nose = world.add(Entity(
        "nose", "body", "nose", "little nose", owner=child.id,
        meters={"warmth": 1.0}, memes={"worry": 0.0},
    ))
    comfort = world.add(Entity(
        "comfort", "thing", params.comfort, world.comfort.phrase,
        owner=child.id, meters={"needed": 1.0, "shared": 0.0},
    ))
    world.add(Entity("bed", "place", "bed", world.bed.phrase))
    world.facts.update(child=child, helper=helper, nose=nose, comfort=comfort)
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    nose: Entity = world.facts["nose"]  # type: ignore[assignment]
    comfort: Entity = world.facts["comfort"]  # type: ignore[assignment]
    name = child.label
    possessive = "her" if params.gender == "girl" else "his"
    pronoun = "she" if params.gender == "girl" else "he"
    object_pronoun = "her" if params.gender == "girl" else "him"

    world.record(
        "settle",
        f"{name} climbed into {world.bed.phrase}. {world.bed.detail} "
        f"{possessive.capitalize()} {comfort.label} waited under the blanket, "
        f"and {possessive} little nose peeked out to smell the lavender night.",
        "The room was ready for sleep, but the child still wanted one quiet comfort.",
        f"{name} settled into bed with the {comfort.label} close by.",
        child.id,
        "bed",
    )

    world.para()
    nose.memes["worry"] += 1
    world.record(
        "foreshadow",
        f"Then {name} heard a tiny sniffle from the hallway. "
        f'"Someone may need a friend," said the {helper.type}. '
        f"{name} held the {comfort.label} close, while {possessive} nose "
        f"noticed the soft, worried sound before anyone else did.",
        "A small sound in the dark warned that another child might be lonely.",
        "The child understood that the favorite comfort could help someone else.",
        child.id,
        "nose",
    )

    world.para()
    comfort.meters["shared"] = 1.0
    child.memes["generosity"] += 1
    world.record(
        "share",
        f"{name} carried the {comfort.label} to the doorway. "
        f'"You may cuddle with it first," {pronoun} whispered. '
        f"The little {comfort.type} rested beside a waiting child, "
        f"and the sniffle became a small, thankful sigh.",
        f"The other child needed comfort, and {name} had a gentle friend to share.",
        f"The {comfort.label} helped the other child feel safe.",
        child.id,
        "comfort",
    )

    world.para()
    child.memes["sleepiness"] += 1
    world.record(
        "return",
        f"After a while, the {comfort.label} came back to {name}'s bed. "
        f"{name} tucked it beneath the blanket and touched {possessive} nose "
        f"with one sleepy finger. " 
        f'"Sharing did not make love smaller," {name} murmured. '
        f'"It made the whole hallway warmer."',
        "The comfort had been shared for a while, and it could return when the need was over.",
        f"{name} fell asleep knowing that kindness could travel out and come home again.",
        child.id,
        "comfort",
    )

    world.para()
    nose.meters["warmth"] += 1.0
    child.memes["sleepiness"] += 1
    world.record(
        "sleep",
        f"The {helper.type} kissed {name}'s forehead. Outside, the stars blinked "
        f"once, twice, and then softly disappeared behind a cloud. "
        f"{name}'s nose gave one last peaceful sniff, and the room grew still.",
        "The child had shared, listened, and returned to bed.",
        f"{name} slept peacefully with the {comfort.label} tucked close.",
        child.id,
        "bed",
    )
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    return [
        f"Write a gentle bedtime story about {child.label} sharing a favorite comfort "
        f"after noticing something with a little nose.",
        "Tell a sleepy story in which a small clue prepares the child for a kind act, "
        "and the shared comfort returns before morning.",
    ]


def story_qa(world: World) -> list[QAItem]:
    questions = {
        "foreshadow": "What did the child's nose notice?",
        "share": "Why did the child share the comfort?",
        "return": "What happened after the other child used it?",
        "sleep": "How did the story end?",
    }
    return [
        QAItem(questions[event.kind], f"{event.cause} {event.result}")
        for event in world.history if event.kind in questions
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        KNOWLEDGE[key][0]
        for key in ("nose", "sharing", "bedtime", "foreshadowing")
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} feelings={memes}")
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.text}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
heard_before_share(Child) :- has_nose(Child), needs_comfort(Other),
                              noticed(Child, Other).
kind_choice(Child) :- heard_before_share(Child), owns_comfort(Child),
                      shares(Child).
comfort_returns(Child) :- kind_choice(Child), shared_with(Child, Other).
resolved(Child) :- comfort_returns(Child), sleeps(Child).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("has_nose", "child"),
        asp.fact("needs_comfort", "other"),
        asp.fact("noticed", "child", "other"),
        asp.fact("owns_comfort", "child"),
        asp.fact("shares", "child"),
        asp.fact("shared_with", "child", "other"),
        asp.fact("sleeps", "child"),
    ])


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n#show resolved/1.\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    if ("child",) not in asp.atoms(model, "resolved"):
        print("MISMATCH: ASP did not find the bedtime resolution.")
        return 1
    sample = generate(StoryParams(
        bed="moon_bed", comfort="rabbit", name="Luna", gender="girl",
        helper="mother", trait="gentle", seed=1,
    ))
    if "nose" not in sample.story.lower() or "share" not in sample.story.lower():
        print("MISMATCH: generated story lost the required narrative instruments.")
        return 1
    print("OK: ASP and Python agree that noticing, sharing, returning, and sleeping resolve the story.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A bedtime storyworld about a nose and the warmth of sharing."
    )
    parser.add_argument("--bed", choices=sorted(BEDS))
    parser.add_argument("--comfort", choices=sorted(COMFORTS))
    parser.add_argument("--name")
    parser.add_argument("--gender", choices=sorted(NAMES))
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--problem", choices=["sharing"], default="sharing")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(sorted(NAMES))
    return StoryParams(
        bed=args.bed or rng.choice(sorted(BEDS)),
        comfort=args.comfort or rng.choice(sorted(COMFORTS)),
        name=args.name or rng.choice(NAMES[gender]),
        gender=gender,
        helper=args.helper or rng.choice(HELPERS),
        trait=args.trait or rng.choice(TRAITS),
        problem=args.problem,
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("moon_bed", "rabbit", "Luna", "girl", "mother", "gentle"),
    StoryParams("window_bed", "bear", "Milo", "boy", "father", "thoughtful"),
    StoryParams("cloud_bed", "fox", "Nora", "girl", "grandmother", "hopeful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise SystemExit("-n must be at least 1")
    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp:
        print(asp_program())
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("Resolved atoms:", asp.atoms(model, "resolved"))
        return

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples],
                             ensure_ascii=False, indent=2))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all or len(samples) > 1:
            header = f"### bedtime story {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
