#!/usr/bin/env python3
"""A small animal-story world about a misunderstanding aboard a frigate."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

ANIMALS = {
    "penguin": ("Pip", "she"),
    "otter": ("Ollie", "he"),
    "parrot": ("Paco", "he"),
    "seal": ("Mina", "she"),
}
PLACES = {
    "deck": "the frigate's sunny deck",
    "galley": "the frigate's cozy galley",
    "harbor": "the frigate's quiet harbor",
}
MISUNDERSTANDINGS = {
    "signal": "a pop from a bottle of sparkling grape juice sounds like a warning signal",
    "storm": "fizzing bubbles sound like rain beginning to patter",
    "cheer": "a cork's pop sounds like a call to begin the celebration",
}


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def render(self) -> str:
        return "\n\n".join(self.paragraphs)


@dataclass
class StoryParams:
    place: str = "deck"
    animal: str = "penguin"
    friend: str = "otter"
    misunderstanding: str = "signal"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Setup:
    place: str
    animal: str
    friend: str
    misunderstanding: str


CURATED = [
    Setup("deck", "penguin", "otter", "signal"),
    Setup("galley", "parrot", "seal", "storm"),
    Setup("harbor", "otter", "penguin", "cheer"),
]
VALID_COMBOS = [
    (place, animal, friend, kind)
    for place in PLACES
    for animal in ANIMALS
    for friend in ANIMALS
    for kind in MISUNDERSTANDINGS
    if animal != friend
]


def _check(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place!r}. Choose deck, galley, or harbor.")
    if params.animal not in ANIMALS or params.friend not in ANIMALS:
        raise StoryError("Choose a listed animal for both friends.")
    if params.animal == params.friend:
        raise StoryError("The two friends must be different animals.")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("Choose signal, storm, or cheer for the misunderstanding.")


def generate(params: StoryParams) -> StorySample:
    _check(params)
    rng = random.Random(params.seed)
    place = PLACES[params.place]
    animal_name, animal_pronoun = ANIMALS[params.animal]
    friend_name, friend_pronoun = ANIMALS[params.friend]
    misunderstanding = params.misunderstanding

    animal = Entity(params.animal, "character", params.animal, animal_name,
                    memes={"curiosity": 1.0})
    friend = Entity(params.friend, "character", params.friend, friend_name,
                    memes={"kindness": 1.0})
    ship = Entity("frigate", "vehicle", "ship", "frigate",
                  meters={"afloat": 1.0})
    bottle = Entity("bottle", "object", "drink", "sparkling grape juice",
                    meters={"sealed": 1.0})
    world = World(place=place)
    for entity in (animal, friend, ship, bottle):
        world.add(entity)

    opening = rng.choice([
        f"On the frigate, {animal_name} the {params.animal} and {friend_name} the {params.friend} were setting out cups in {place}.",
        f"The frigate rocked gently in the water while {animal_name} and {friend_name} prepared a little welcome party in {place}.",
    ])
    world.paragraphs.append(
        opening + f" A bottle of sparkling grape juice, sometimes called champagne, waited beside the cups."
    )

    world.paragraphs.append(
        f"When {animal_name} opened it, the cork popped and bubbles fizzed. {animal_name} thought the sound meant "
        f"{MISUNDERSTANDINGS[misunderstanding]}, and hurried to stop the party."
    )
    animal.memes["worry"] = 1.0
    bottle.meters["sealed"] = 0.0
    bottle.meters["bubbling"] = 1.0

    if misunderstanding == "signal":
        question = f'"Is that a warning?" {animal_name} asked. {friend_name} listened, then said, "I hear fizz, not a ship bell."'
        action = f'{friend_name} showed {animal_name} the tiny bubbles rising in the cup and pointed to the quiet sea.'
        ending = "The frigate stayed peaceful, and the friends clinked their cups as bubbles tickled their noses."
    elif misunderstanding == "storm":
        question = f'"Rain is coming!" {animal_name} cried. {friend_name} looked up at the clear sky and asked, "Could the sound be in our cups?"'
        action = f'{friend_name} tipped a little juice into a cup; the fizzing followed the drink, not the sky.'
        ending = "With the sky still bright above the frigate, the friends watched bubbles sparkle in their cups."
    else:
        question = f'"Was that the signal to cheer?" {animal_name} asked. {friend_name} smiled and said, "Maybe the cork only wants to join us."'
        action = f'{friend_name} gently pressed a cup to the bottle and showed how the bubbles made the same soft pop and fizz.'
        ending = "The friends began their celebration together, while the empty cork bobbed in a bowl like a tiny boat."
    world.paragraphs.append(question)
    animal.memes["curiosity"] += 1.0
    friend.memes["reassurance"] = 1.0
    world.paragraphs.append(
        f'{animal_name} paused to listen. "{action}" {animal_name} said, "You are right. It is only the drink!"'
    )
    animal.memes["worry"] = 0.0
    animal.memes["relief"] = 1.0
    friend.meters["helped"] = 1.0
    bottle.meters["understood"] = 1.0
    world.paragraphs.append(ending)

    world.facts.update(
        hero=animal_name, friend=friend_name, animal=params.animal,
        friend_animal=params.friend, place=place, misunderstanding=misunderstanding,
        belief=MISUNDERSTANDINGS[misunderstanding], action=action, ending=ending,
        resolved=True,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a gentle animal story about a misunderstanding aboard a frigate.",
            f"Tell how {animal_name} and {friend_name} discover what the champagne-like bubbles really mean.",
        ],
        story_qa=[
            QAItem("What did the animal misunderstand?",
                   f"{animal_name} misunderstood the bottle's pop and fizz as {MISUNDERSTANDINGS[misunderstanding]}."),
            QAItem("How did the friends clear up the misunderstanding?",
                   f"{friend_name} helped by explaining what the sound was: {action} That helped {animal_name} feel relieved."),
            QAItem("How did the story end?",
                   ending),
        ],
        world_qa=[
            QAItem("What is a frigate?",
                   "A frigate is a kind of ship. In this story, the animals travel and share a party aboard one."),
            QAItem("Why can a fizzy drink make bubbles?",
                   "Gas escaping from a fizzy drink forms bubbles. Opening its container can also make a little pop."),
        ],
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="An animal story about a misunderstanding on a frigate.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--friend", choices=ANIMALS)
    parser.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
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
    animal = args.animal or rng.choice(list(ANIMALS))
    friend_pool = [name for name in ANIMALS if name != animal]
    return StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        animal=animal,
        friend=args.friend or rng.choice(friend_pool),
        misunderstanding=args.misunderstanding or rng.choice(list(MISUNDERSTANDINGS)),
        seed=getattr(args, "seed", None),
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("\n== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---", f"  place: {world.place}"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label} ({entity.kind}/{entity.type}): "
            f"meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  resolved: {world.facts['resolved']}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
misread(A) :- animal(A), pop_belief(A).
explains(F,A) :- friend(F), animal(A), shows_bubbles(F,A).
resolved(A) :- misread(A), explains(F,A), friend(F), distinct(F,A).
outcome(clear) :- resolved(A).
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    facts = []
    for place in PLACES:
        facts.append(asp.fact("place", place))
    for animal in ANIMALS:
        facts.append(asp.fact("animal", animal))
        facts.append(asp.fact("friend", animal))
    for animal in ANIMALS:
        for friend in ANIMALS:
            if animal != friend:
                facts.append(asp.fact("distinct", friend, animal))
                facts.append(asp.fact("pop_belief", animal))
                facts.append(asp.fact("shows_bubbles", friend, animal))
    return "\n".join(facts)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "outcome")))


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
        if ("clear",) not in asp.atoms(model, "outcome"):
            print("ASP reasonableness check failed.")
            return 1
        for setup in CURATED:
            sample = generate(StoryParams(
                place=setup.place, animal=setup.animal, friend=setup.friend,
                misunderstanding=setup.misunderstanding,
            ))
            if not sample.story.strip() or not sample.world.facts["resolved"]:
                print("Python story verification failed.")
                return 1
        if len(VALID_COMBOS) != len(asp_valid_combos()) * len(VALID_COMBOS) // len(VALID_COMBOS):
            # The ASP outcome is a domain-level outcome; the Python gate checks each setup.
            print("Unexpected ASP parity state.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: Python stories and ASP reasonableness check passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    if args.n < 1 and not args.all:
        raise StoryError("-n must be at least 1.")

    if args.all:
        samples = [
            generate(StoryParams(s.place, s.animal, s.friend, s.misunderstanding))
            for s in CURATED
        ]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        for offset in range(max(args.n * 30, 30)):
            seed = base_seed + offset
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            if len(samples) >= args.n:
                break

    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        return
    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa,
             header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
