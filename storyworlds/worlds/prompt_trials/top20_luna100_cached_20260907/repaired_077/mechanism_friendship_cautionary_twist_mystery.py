#!/usr/bin/env python3
"""
A small mystery story world about a friendship, a helpful mechanism, and a
cautionary twist.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STORYWORLDS_DIR))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    friend_name: str
    place: str
    mechanism: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Entity
    friend: Entity
    place: str
    mechanism: Entity
    clue: str
    danger: str
    mechanism_state: str = "idle"
    mystery_solved: bool = False
    friendship_strength: float = 0.0
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


NAMES = ["Luna", "Mira", "Tavi", "Nori", "Pip", "Suri", "Milo", "Rae"]
PLACES = [
    "the old greenhouse",
    "the little harbor",
    "the village library",
    "the clockmaker's courtyard",
    "the hilltop observatory",
]
MECHANISMS = [
    "a brass pulley",
    "a wind-up signal box",
    "a tiny water wheel",
    "a bell-and-string device",
    "a hinged mirror trap",
]

CASES = [
    {
        "title": "the lantern that blinked twice",
        "object": "a blue lantern blinked twice in the greenhouse window",
        "first_guess": "the blinking lantern was a secret warning from someone outside",
        "clue": "a loose vine brushed the pulley each time the evening draft moved",
        "risk": "climbing onto the unstable potting bench could cause a fall",
        "turn": "the pulley lifted a shade and made the lantern's switch bounce",
        "repair": "secured the vine, stepped away from the bench, and asked the keeper to inspect the wiring",
        "ending": "the lantern shone steadily while the pulley rested safely behind its guard",
    },
    {
        "title": "the bell beneath the dock",
        "object": "a bell rang once beneath the quiet harbor dock",
        "first_guess": "someone trapped below the dock was calling for help",
        "clue": "the tide tugged a rope through the bell-and-string device",
        "risk": "leaning over the wet edge could send someone into the cold water",
        "turn": "the rope tightened, swung the bell, and released it with one clear note",
        "repair": "called the harbor keeper, kept both friends on dry boards, and marked the rope for repair",
        "ending": "the repaired bell stayed quiet as the tide slid under the dock",
    },
    {
        "title": "the vanished library card",
        "object": "a red library card disappeared from a locked reading desk",
        "first_guess": "a visitor had secretly taken the card",
        "clue": "a book cart's small wheel pressed the desk drawer open whenever it rolled past",
        "risk": "accusing a visitor without checking could hurt an innocent person's feelings",
        "turn": "the wheel nudged the drawer, and the card slipped behind a stack of maps",
        "repair": "apologized for the hasty guess, found the card, and asked the librarian to fix the wheel",
        "ending": "the card returned to its pocket while the cart stood still beside the desk",
    },
    {
        "title": "the silent courtyard clock",
        "object": "the courtyard clock stopped just before the morning bell",
        "first_guess": "the clock had been deliberately stopped to hide a secret meeting",
        "clue": "a pebble had wedged inside the clock's exposed gear cover",
        "risk": "putting fingers near moving gears could cause a painful pinch",
        "turn": "the jammed gear held the hands still while the pendulum kept trying to swing",
        "repair": "kept hands away from the gears and asked the clockmaker to remove the pebble",
        "ending": "the clock chimed again, and its hands moved without a mysterious pause",
    },
    {
        "title": "the star in the wrong window",
        "object": "a bright star appeared in the observatory's side window after sunset",
        "first_guess": "a missing star map had been projected by a hidden visitor",
        "clue": "the hinged mirror trap reflected the observatory lamp toward the glass",
        "risk": "opening the dark roof hatch alone could lead to a dangerous fall",
        "turn": "the mirror swung with the breeze and sent the lamp's reflection across the room",
        "repair": "closed the hatch, held the mirror still with a safe latch, and told the astronomer",
        "ending": "the false star faded while the real stars filled the sky above the dome",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mystery story world about friendship, caution, and a surprising mechanism."
    )
    parser.add_argument("--hero-name", choices=NAMES)
    parser.add_argument("--friend-name", choices=NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--mechanism", choices=MECHANISMS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero_name or rng.choice(NAMES)
    choices = [name for name in NAMES if name != hero]
    friend = args.friend_name or rng.choice(choices)
    return StoryParams(
        hero_name=hero,
        friend_name=friend,
        place=args.place or rng.choice(PLACES),
        mechanism=args.mechanism or rng.choice(MECHANISMS),
    )


def _reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name == params.friend_name:
        raise StoryError("The two friends need different names.")
    if params.place not in PLACES:
        raise StoryError("That place is not part of this mystery world.")
    if params.mechanism not in MECHANISMS:
        raise StoryError("That mechanism is not available in this story world.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    case = rng.choice(CASES)

    hero = Entity(
        params.hero_name,
        "child_detective",
        meters={"distance_to_danger": 1.0, "attention": 0.8},
        memes={"curiosity": 0.9, "caution": 0.8, "friendship": 0.7},
    )
    friend = Entity(
        params.friend_name,
        "friend",
        meters={"distance_to_danger": 1.0, "attention": 0.7},
        memes={"loyalty": 0.9, "courage": 0.7},
    )
    mechanism = Entity(
        params.mechanism,
        "mechanism",
        meters={"distance_to_people": 1.0, "motion": 0.0},
        memes={"useful": 0.9, "mysterious": 0.8},
    )
    world = World(
        hero=hero,
        friend=friend,
        place=params.place,
        mechanism=mechanism,
        clue=case["clue"],
        danger=case["risk"],
    )

    opening = rng.choice(
        [
            "At dusk, the two friends were checking a quiet corner when",
            "The mystery began during an ordinary afternoon, when",
            "Just as the last visitors were leaving,",
            "Luna and her friend were following a harmless trail of clues when",
        ]
    )
    friendship_exchange = rng.choice(
        [
            f'"We should look together," said {hero.name}. "{friend.name}, stay where I can see you."',
            f'"I have an idea," said {friend.name}. "{hero.name}, promise we will check it before we act."',
            f'"A mystery is not worth getting hurt over," said {hero.name}. {friend.name} nodded. "Then we solve it carefully."',
        ]
    )
    reflection = rng.choice(
        [
            "The friends compared what they had seen instead of blaming anyone.",
            "They made a small list of facts and left guesses at the bottom.",
            "Their friendship made the next step easier: neither friend had to pretend to know more than they did.",
        ]
    )
    lesson = rng.choice(
        [
            "The strange machine had not been sending a secret message at all; it had been obeying a simple force.",
            "The cautionary part of the mystery was clear: a clever clue never makes an unsafe action safe.",
            "Their best discovery was not only the answer, but the habit of checking before accusing or touching.",
        ]
    )

    lines = [
        f"{opening} {case['object']}.",
        f"{hero.name} thought {case['first_guess']}.",
        friendship_exchange,
        f"They noticed the {params.mechanism} nearby, but neither friend touched it.",
        f"{friendship_exchange}",
        reflection,
        f"Then the mechanism moved: {case['turn']}.",
        f"The real clue was this: {case['clue']}.",
        f"The first guess fell apart. The danger was real, though: {case['risk']}.",
        f"{friend.name} whispered, \"So the mystery has an ordinary answer, but we still need to be careful.\"",
        f"{hero.name} replied, \"Exactly. We can solve it without stepping into trouble.\"",
        f"Together, they {case['repair']}.",
        lesson,
        f"By the end, {case['ending']}.",
        f"The friends left side by side, pleased that their careful questions had protected both the truth and each other.",
    ]

    world.mechanism_state = "understood and made safe"
    world.mystery_solved = True
    world.friendship_strength = 1.0
    world.facts.update(
        {
            "case": case["title"],
            "first_guess": case["first_guess"],
            "clue": case["clue"],
            "risk": case["risk"],
            "turn": case["turn"],
            "repair": case["repair"],
            "ending": case["ending"],
        }
    )
    story = " ".join(lines)
    world.facts["story"] = story

    prompts = [
        f"Write a mystery called {case['title']} about two friends and {params.mechanism}.",
        f"Tell a cautionary friendship story set in {params.place}, where a mechanism causes a surprising false alarm.",
        "Include a twist in which the strange event has a simple mechanical cause, and let the friends solve it safely.",
    ]

    story_qa = [
        QAItem(
            question=f"What did {params.hero_name} first think was happening?",
            answer=f"{params.hero_name} first thought {case['first_guess']}.",
        ),
        QAItem(
            question=f"What clue solved the mystery?",
            answer=f"The clue was that {case['clue']}.",
        ),
        QAItem(
            question="What was the cautionary danger?",
            answer=f"The danger was that {case['risk']}.",
        ),
        QAItem(
            question=f"How did the friends repair the problem?",
            answer=f"They {case['repair']}.",
        ),
        QAItem(
            question="What changed because of their friendship?",
            answer=(
                f"The friends listened to each other, checked the evidence together, and chose a safe solution "
                f"instead of letting fear or blame control them."
            ),
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a mechanism?",
            answer=(
                "A mechanism is a group of connected parts that transfers movement or force to do something useful, "
                "such as lifting, ringing, turning, or opening."
            ),
        ),
        QAItem(
            question="Why should people check clues before accusing someone?",
            answer=(
                "Checking clues helps people separate facts from guesses and prevents an innocent person from being blamed."
            ),
        ),
        QAItem(
            question="What does a cautionary story teach?",
            answer=(
                "A cautionary story shows a danger or mistake and teaches a safer choice for the future."
            ),
        ),
        QAItem(
            question="What makes a friendship helpful during a mystery?",
            answer=(
                "Helpful friends listen, share observations, ask honest questions, and remind one another to stay safe."
            ),
        ),
        QAItem(
            question="What is a twist in a mystery?",
            answer=(
                "A twist is a surprising change in understanding that reveals the event was different from the first guess."
            ),
        ),
    ]

    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        world = sample.world
        print()
        print("--- trace ---")
        print(
            f"hero={world.hero.name}, kind={world.hero.kind}, "
            f"meters={world.hero.meters}, memes={world.hero.memes}"
        )
        print(
            f"friend={world.friend.name}, kind={world.friend.kind}, "
            f"meters={world.friend.meters}, memes={world.friend.memes}"
        )
        print(
            f"place={world.place}, mechanism={world.mechanism.name}, "
            f"state={world.mechanism_state}, solved={world.mystery_solved}, "
            f"friendship={world.friendship_strength}"
        )
    if qa:
        print()
        print("== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_mechanism(M) :- mechanism(M).
compatible(P,M) :- place(P), mechanism(M).
safe_friendship(H,F) :- hero(H), friend(F), H != F.
mystery_ready(P,M) :- compatible(P,M), safe_friendship(H,F).
#show valid_place/1.
#show valid_mechanism/1.
#show compatible/2.
#show safe_friendship/2.
"""


def asp_facts() -> str:
    import asp

    facts = []
    facts.extend(asp.fact("place", value) for value in PLACES)
    facts.extend(asp.fact("mechanism", value) for value in MECHANISMS)
    facts.append(asp.fact("hero", "hero"))
    facts.append(asp.fact("friend", "friend"))
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_place/1."))
    return sorted(set(asp.atoms(model, "valid_place")))


def asp_valid_mechanisms() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_mechanism/1."))
    return sorted(set(asp.atoms(model, "valid_mechanism")))


def asp_verify() -> int:
    py_places = {(place,) for place in PLACES}
    py_mechanisms = {(mechanism,) for mechanism in MECHANISMS}
    cl_places = set(asp_valid_places())
    cl_mechanisms = set(asp_valid_mechanisms())
    if py_places != cl_places or py_mechanisms != cl_mechanisms:
        print("MISMATCH between Python registries and ASP registries.")
        if py_places != cl_places:
            print("  places only in Python:", sorted(py_places - cl_places))
            print("  places only in ASP:", sorted(cl_places - py_places))
        if py_mechanisms != cl_mechanisms:
            print("  mechanisms only in Python:", sorted(py_mechanisms - cl_mechanisms))
            print("  mechanisms only in ASP:", sorted(cl_mechanisms - py_mechanisms))
        return 1

    for index, params in enumerate(
        [
            StoryParams(
                hero_name=NAMES[index % len(NAMES)],
                friend_name=NAMES[(index + 1) % len(NAMES)],
                place=PLACES[index % len(PLACES)],
                mechanism=MECHANISMS[index % len(MECHANISMS)],
                seed=index,
            )
            for index in range(5)
        ]
    ):
        sample = generate(params)
        if not sample.story or not sample.story_qa or not sample.world_qa:
            print("Generated story verification failed.")
            return 1
    print(
        f"OK: ASP matches Python registries "
        f"({len(py_places)} places, {len(py_mechanisms)} mechanisms), "
        "and generated stories passed."
    )
    return 0


def generation_params(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        result = []
        for index, place in enumerate(PLACES):
            result.append(
                StoryParams(
                    hero_name=NAMES[index % len(NAMES)],
                    friend_name=NAMES[(index + 1) % len(NAMES)],
                    place=place,
                    mechanism=MECHANISMS[index % len(MECHANISMS)],
                )
            )
        return result

    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [
        resolve_params(args, random.Random(base + index))
        for index in range(max(0, args.n))
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_place/1.\n#show valid_mechanism/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        places = [item[0] for item in asp_valid_places()]
        mechanisms = [item[0] for item in asp_valid_mechanisms()]
        print("places:", ", ".join(places))
        print("mechanisms:", ", ".join(mechanisms))
        return

    samples = []
    for index, params in enumerate(generation_params(args)):
        params.seed = (args.seed if args.seed is not None else 0) + index
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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
