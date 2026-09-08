#!/usr/bin/env python3
"""
A tiny cautionary ghost-story world about a giddy scrounge and a perceptive
friend who learn that spooky sounds are warnings, not invitations.
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


@dataclass(frozen=True)
class Place:
    id: str
    name: str
    detail: str
    safe_spot: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class ObjectChoice:
    id: str
    label: str
    found_in: str
    sound: str
    danger: str
    lesson: str


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.history.append(text)

    def render(self) -> str:
        return "\n\n".join(self.history)


@dataclass
class StoryParams:
    place: str
    object_choice: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    adult: str
    seed: Optional[int] = None


PLACES = {
    "attic": Place(
        "attic",
        "the old attic",
        "Dusty trunks crouched beneath the rafters, and moonlight made silver squares on the floor.",
        "the bright hallway",
        ("dust", "rafters", "moonlight"),
    ),
    "boathouse": Place(
        "boathouse",
        "the creaky boathouse",
        "Ropes hung from the walls, and the dark water bumped softly under the boards.",
        "the sunny dock",
        ("ropes", "water", "boards"),
    ),
    "garden_shed": Place(
        "garden_shed",
        "the little garden shed",
        "Rain tapped the roof while old pots and tools leaned together in the shadows.",
        "the kitchen porch",
        ("rain", "tools", "shadows"),
    ),
}

OBJECTS = {
    "bell": ObjectChoice(
        "bell",
        "a cracked brass bell",
        "under a wool blanket",
        "CLINK... CLINK...",
        "it wakes a lonely ghost who guards the dark room",
        "some old things make warning sounds for a reason",
    ),
    "music_box": ObjectChoice(
        "music_box",
        "a tiny music box",
        "inside a wooden chest",
        "TINK-TINK-TINK...",
        "its tune calls a ghost toward anyone who winds it",
        "a strange sound should be checked with a grown-up",
    ),
    "key": ObjectChoice(
        "key",
        "a long black key",
        "behind a loose board",
        "SCRAPE... SCRAPE...",
        "it opens a ghostly door that should stay closed",
        "curiosity is safer when a grown-up helps",
    ),
}

NAMES = {
    "girl": ["Luna", "Mia", "Zoe", "Nora", "Ivy"],
    "boy": ["Theo", "Sam", "Leo", "Ben", "Finn"],
}

ADULTS = ["Mom", "Dad", "Aunt May"]

KNOWLEDGE = {
    "warning": QAItem(
        "What should a child do when an old object makes a strange sound?",
        "A child should step back, leave the object alone, and tell a grown-up.",
    ),
    "ghost": QAItem(
        "Why is it wise to leave a spooky place when a warning appears?",
        "Leaving gives everyone time to get safe and lets a grown-up investigate.",
    ),
    "sound": QAItem(
        "Can a sound be a warning?",
        "Yes. A sudden or unusual sound can tell us to pause and look for help.",
    ),
}


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    obj = OBJECTS[params.object_choice]
    world = World()
    child = world.add(Entity(params.child, "character", params.child))
    helper = world.add(Entity(params.helper, "character", params.helper))
    adult = world.add(Entity("adult", "character", params.adult))
    room = world.add(Entity("place", "place", place.name))
    thing = world.add(Entity("object", "object", obj.label))
    ghost = world.add(Entity("ghost", "spirit", "the pale ghost"))

    child.memes.update({"giddy": 1.0, "curiosity": 1.0})
    helper.memes.update({"perception": 2.0, "caution": 0.0})
    room.meters.update({"darkness": 1.0, "risk": 0.0})
    thing.meters.update({"mystery": 1.0})
    ghost.memes.update({"lonely": 1.0})

    world.facts.update(
        place=place,
        object=obj,
        child=child,
        helper=helper,
        adult=adult,
        room=room,
        thing=thing,
        ghost=ghost,
    )

    world.say(
        f"{params.child} felt giddy when {params.helper} peeked into {place.name}. "
        f"{place.detail}"
    )
    world.say(
        f'"Let\'s scrounge for treasure!" said {params.child}. '
        f'"We can look quickly," answered {params.helper}, holding a little lantern.'
    )
    world.say(
        f"{params.child} poked around and found {obj.label} {obj.found_in}. "
        f"The dust puffed up like tiny gray ghosts."
    )
    world.say(f'"Listen!" whispered {params.child}. {obj.sound} went the object.')
    world.say(
        f'{params.helper} was perceptive. "{params.child}, that sound feels like '
        f"a warning. We should not touch it again."'
    )
    helper.memes["perception"] += 1.0
    helper.memes["caution"] += 1.0

    world.say(
        f'"Nonsense!" {params.child} said, reaching toward {obj.label}. '
        f'"Wait," said {params.helper}. "Let\'s call {params.adult}."'
    )
    child.memes["giddy"] += 1.0
    room.meters["risk"] += 1.0

    world.say(f"Then the sound came again, louder: {obj.sound}")
    world.say(
        "A cold breath curled around their ankles, and a pale shape appeared "
        "between the trunks."
    )
    ghost.memes["lonely"] -= 1.0
    world.say(
        f'"Please leave my keepsake alone," sighed the ghost. '
        f'"It makes that sound when danger is near."'
    )
    world.say(
        f'{params.helper} took {params.child}\'s hand. "{params.child}, I knew '
        f"the sound was telling us to stop. Let\'s go."'
    )
    world.say(
        f"{params.adult} arrived with a lantern and led them to {place.safe_spot}. "
        f"The ghost faded as the door closed."
    )
    room.meters["risk"] = 0.0
    child.memes["relief"] = 1.0
    helper.memes["relief"] = 1.0
    world.say(
        f"{params.adult} smiled gently. 'Being curious is fine, but a warning is "
        f"not an invitation. We listen, step away, and get help.'"
    )
    world.say(
        f"{params.child} nodded. The next time {params.child} heard "
        f"{obj.sound.lower()}, the giddy scrounger did not reach closer. "
        f"{params.child} reached for {params.adult} instead."
    )
    world.facts["outcome"] = "safe"
    return world


def prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = f["place"]  # type: ignore[assignment]
    obj: ObjectChoice = f["object"]  # type: ignore[assignment]
    child: Entity = f["child"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    return [
        f"Write a cautionary ghost story in {place.name} where {child.label} feels giddy "
        f"while scrounging for {obj.label}.",
        f"Include the sound effect '{obj.sound}' and make {helper.label} perceptive "
        "enough to recognize it as a warning.",
        "End with the children choosing safety and calling a grown-up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    place: Place = f["place"]  # type: ignore[assignment]
    obj: ObjectChoice = f["object"]  # type: ignore[assignment]
    child: Entity = f["child"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    adult: Entity = f["adult"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Where did {child.label} and {helper.label} go?",
            f"They went into {place.name}, where {place.detail[0].lower() + place.detail[1:]}",
        ),
        QAItem(
            f"What did {child.label} find while scrounging?",
            f"{child.label} found {obj.label} {obj.found_in}.",
        ),
        QAItem(
            "What sound did the object make?",
            f"It made the warning sound '{obj.sound}'.",
        ),
        QAItem(
            f"Why did {helper.label} want to stop?",
            f"{helper.label} was perceptive and understood that the strange sound was a warning.",
        ),
        QAItem(
            "Who helped the children get safe?",
            f"{adult.label} came with a lantern and led them to safety.",
        ),
        QAItem(
            "What did the children learn?",
            f"They learned that {obj.lesson}, so they should step away and ask a grown-up for help.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [KNOWLEDGE["warning"], KNOWLEDGE["sound"], KNOWLEDGE["ghost"]]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"{entity.id}: kind={entity.kind}, label={entity.label}, "
            f"meters={meters}, memes={memes}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A cautionary ghost-story world.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object", dest="object_choice", choices=OBJECTS)
    parser.add_argument("--child")
    parser.add_argument("--helper")
    parser.add_argument("--adult", choices=ADULTS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child or rng.choice(NAMES["girl"])
    helper_pool = [name for names in NAMES.values() for name in names if name != child]
    helper = args.helper or rng.choice(helper_pool)
    if helper in NAMES["girl"]:
        helper_gender = "girl"
    else:
        helper_gender = "boy"
    child_gender = "girl" if child in NAMES["girl"] else "boy"
    if child == helper:
        raise StoryError("The child and helper must have different names.")
    return StoryParams(
        place=args.place or rng.choice(sorted(PLACES)),
        object_choice=args.object_choice or rng.choice(sorted(OBJECTS)),
        child=child,
        child_gender=child_gender,
        helper=helper,
        helper_gender=helper_gender,
        adult=args.adult or rng.choice(ADULTS),
    )


ASP_RULES = r"""
hazardous_object(O) :- object(O), ghostly(O).
safe_choice :- called_adult.
safe_outcome :- safe_choice.
"""


def asp_facts() -> str:
    return "\n".join(
        [
            "object(bell).",
            "object(music_box).",
            "object(key).",
            "ghostly(bell).",
            "ghostly(music_box).",
            "ghostly(key).",
            "called_adult.",
        ]
    )


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def run_asp() -> None:
    try:
        import asp
    except ImportError as exc:
        raise StoryError("ASP mode requires clingo and the shared asp helper.") from exc
    model = asp.one_model(asp_program() + "\n#show hazardous_object/1.\n#show safe_outcome/1.")
    print("ASP model:")
    for symbol in sorted(str(item) for item in model):
        print(f"  {symbol}")


def verify() -> int:
    if not all(OBJECTS and PLACES for _ in [0]):
        return 1
    rng = random.Random(17)
    for _ in range(20):
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if not sample.story or "warning" not in sample.story:
            print("verification failed")
            return 1
    print("OK: generated stories contain a complete cautionary arc.")
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.asp:
        run_asp()
        return
    if args.verify:
        raise SystemExit(verify())

    rng = random.Random(args.seed)
    samples: list[StorySample] = []
    count = len(PLACES) * len(OBJECTS) if args.all else max(1, args.n)

    if args.all:
        for place in sorted(PLACES):
            for object_choice in sorted(OBJECTS):
                params = resolve_params(
                    argparse.Namespace(
                        place=place,
                        object_choice=object_choice,
                        child=None,
                        helper=None,
                        adult=None,
                    ),
                    rng,
                )
                samples.append(generate(params))
    else:
        for _ in range(count):
            params = resolve_params(args, rng)
            params.seed = args.seed
            samples.append(generate(params))

    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### story {index + 1}\n")
        emit(sample, trace=args.trace, qa=args.qa)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
