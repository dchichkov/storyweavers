#!/usr/bin/env python3
"""
A small mystery story world about a curious mechanism, loyal friendship,
and a cautionary twist.
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
class Character:
    name: str
    kind: str
    memes: dict[str, float] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    friend_name: str
    place: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Character
    friend: Character
    place: str
    mechanism: str
    state: str = "locked"
    clue: str = ""
    danger: str = ""
    trust: float = 0.0
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


NAMES = ["Luna", "Mira", "Pip", "Nori", "Tavi", "Suki", "Milo", "Rae"]
PLACES = [
    "the old clock tower",
    "the school greenhouse",
    "the quiet library",
    "the harbor shed",
    "the moonlit museum",
]

MECHANISMS = [
    {
        "name": "the brass moon box",
        "setup": "a small brass box with a turning wheel sat beneath a dusty window",
        "clue": "three fresh scratches formed a neat arrow toward the wheel",
        "danger": "the wheel was connected to a heavy display door, so forcing it could make the door swing loose",
        "twist": "the box was not a treasure chest at all; it was a warning device for the old door",
        "solution": "read the faded instruction plate, turn the wheel only halfway, and tell the caretaker",
        "ending": "the warning bell gave one gentle ring while the heavy door stayed safely latched",
    },
    {
        "name": "the whispering gear",
        "setup": "a silver gear clicked inside a wooden cabinet whenever someone passed",
        "clue": "the clicking stopped when a loose blue ribbon was lifted from the cabinet hinge",
        "danger": "pulling the gear could snap the hinge and spill the cabinet's glass jars",
        "twist": "the mysterious whisper was only the ribbon brushing the turning gear",
        "solution": "held the cabinet still, removed the ribbon with permission, and called the museum guide",
        "ending": "the gear rested quietly behind its glass while the blue ribbon hung on a proper hook",
    },
    {
        "name": "the three-key trap",
        "setup": "three painted keys lay beside a locked drawer marked with a star",
        "clue": "only one key had clean dust around its handle, as if it had recently been used",
        "danger": "the wrong key could release a spring-loaded drawer toward anyone standing close",
        "twist": "the drawer held no prize; it held the caretaker's emergency instructions",
        "solution": "stepped back, chose no key, and asked an adult to inspect the lock",
        "ending": "the drawer opened safely, revealing a map of exits instead of a secret jewel",
    },
    {
        "name": "the tide-turning crank",
        "setup": "an iron crank beside the harbor shed pointed toward a painted red mark",
        "clue": "a damp rope ran from the crank to a little gate by the water",
        "danger": "turning it could change the gate and let water rush across the slippery floor",
        "twist": "the supposed hidden passage was really a flood-control mechanism",
        "solution": "left the crank untouched, moved away from the water, and fetched the harbor keeper",
        "ending": "the keeper secured the gate as the tide whispered harmlessly beneath the boards",
    },
    {
        "name": "the greenhouse bell",
        "setup": "a tiny bell rang inside the greenhouse after every warm gust",
        "clue": "its cord was tied to a vent that opened whenever the sun heated the roof",
        "danger": "climbing to reach the bell could break the glass roof or damage young plants",
        "twist": "the bell was an old temperature warning, not a call from someone trapped inside",
        "solution": "checked the vent from the ground and asked the gardener to repair the cord",
        "ending": "the bell rang once at sunset, and the seedlings stayed safe beneath the closed glass",
    },
    {
        "name": "the library compass",
        "setup": "a brass compass spun beside a shelf of mystery books",
        "clue": "a hidden magnet was tucked beneath the shelf's wooden trim",
        "danger": "pulling at the trim could loosen the shelf and send heavy books tumbling",
        "twist": "the compass pointed to the magnet, not to a secret tunnel",
        "solution": "marked the spot without prying and asked the librarian to examine the shelf",
        "ending": "the librarian removed the magnet, and the compass settled on north beside the books",
    },
]

OPENINGS = [
    "The mystery began when",
    "On a quiet afternoon,",
    "Just before closing time,",
    "While the clouds gathered outside,",
    "At the end of an ordinary visit,",
    "When the last sunbeam crossed the floor,",
]

REACTIONS = [
    "{friend} leaned closer. \"We should not touch it until we know what it does.\"",
    "\"A mystery is not a reason to rush,\" {friend} said, stepping back.",
    "{friend} swallowed. \"Let us look for a clue before we make a guess.\"",
    "\"If it can move, it can surprise us,\" {friend} warned. \"We need help.\"",
    "{friend} pointed to the floor. \"The safest answer may be the one we do not force.\"",
]

CODAS = [
    "Afterward, they wrote the clue in the caretaker's notebook.",
    "They promised to tell the next visitor what they had learned.",
    "The two friends left together, pleased that caution had solved the mystery.",
    "Before going home, they checked that the path around the mechanism was clear.",
    "The strange sound faded, but their careful question stayed with them.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mystery story world about friendship and a cautionary mechanism."
    )
    parser.add_argument("--hero-name", choices=NAMES)
    parser.add_argument("--friend-name", choices=NAMES)
    parser.add_argument("--place", choices=PLACES)
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
    friend = args.friend_name or rng.choice([name for name in NAMES if name != hero])
    place = args.place or rng.choice(PLACES)
    return StoryParams(hero_name=hero, friend_name=friend, place=place)


def _reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name == params.friend_name:
        raise StoryError("The two friends need different names.")
    if params.place not in PLACES:
        raise StoryError("That place is not part of this mystery world.")
    if not params.hero_name or not params.friend_name:
        raise StoryError("Both friends need names.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    case = rng.choice(MECHANISMS)
    opening = rng.choice(OPENINGS)
    reaction = rng.choice(REACTIONS).format(friend=params.friend_name)
    coda = rng.choice(CODAS)

    hero = Character(
        name=params.hero_name,
        kind="child detective",
        memes={"curious": 1.0, "careful": 1.0},
        meters={"distance_from_mechanism": 2.0},
    )
    friend = Character(
        name=params.friend_name,
        kind="friend",
        memes={"loyal": 1.0, "cautious": 1.0},
        meters={"distance_from_mechanism": 2.0},
    )
    world = World(
        hero=hero,
        friend=friend,
        place=params.place,
        mechanism=case["name"],
        clue=case["clue"],
        danger=case["danger"],
        trust=1.0,
    )

    lines = [
        f"{hero.name} and {friend.name} liked solving small mysteries together at {params.place}.",
        f"{opening} {case['setup']}.",
        f"The mechanism made a soft, secret sound, and {hero.name} wondered whether it hid something important.",
        reaction,
        f"Instead of touching the mechanism, the friends searched from a safe distance.",
        f"They noticed the clue: {case['clue']}.",
        f"That clue changed the mystery. {case['twist']}.",
        f"They also understood the caution: {case['danger']}.",
        f"{hero.name} looked at {friend.name}. \"You were right to stop me,\" they said.",
        f"{friend.name} smiled. \"And you were right to look closely. We solve things better together.\"",
        f"Together, they {case['solution']}.",
        coda,
        f"In the end, {case['ending']}.",
    ]

    world.state = "understood and safely reported"
    world.facts.update(
        {
            "mechanism": case["name"],
            "clue": case["clue"],
            "danger": case["danger"],
            "twist": case["twist"],
            "solution": case["solution"],
            "ending": case["ending"],
            "story": " ".join(lines),
        }
    )

    prompts = [
        f"Write a mystery about {case['name']} and two friends at {params.place}.",
        "Include a mechanism, a cautionary warning, a twist, and a friendship-based solution.",
        f"Show how {params.hero_name} and {params.friend_name} solve the mystery without forcing the mechanism.",
    ]

    story_qa = [
        QAItem(
            question=f"What mechanism did {params.hero_name} and {params.friend_name} discover?",
            answer=f"They discovered {case['name']}.",
        ),
        QAItem(
            question="What clue helped the friends understand the mystery?",
            answer=f"The important clue was that {case['clue']}.",
        ),
        QAItem(
            question="What caution did the friends learn?",
            answer=f"They learned that {case['danger']}.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {case['twist']}.",
        ),
        QAItem(
            question="How did friendship help solve the mystery?",
            answer=(
                f"{params.friend_name} urged caution, {params.hero_name} listened, and together they "
                f"{case['solution']}."
            ),
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a mechanism?",
            answer=(
                "A mechanism is a group of parts that work together to make something move, open, signal, or change."
            ),
        ),
        QAItem(
            question="Why should someone avoid forcing an unfamiliar mechanism?",
            answer=(
                "Forcing an unfamiliar mechanism can make it move suddenly, break nearby objects, or hurt someone. "
                "It is safer to observe it and ask a responsible adult for help."
            ),
        ),
        QAItem(
            question="What makes a good mystery clue?",
            answer=(
                "A good mystery clue is a real detail that helps explain what happened, such as a mark, sound, position, "
                "or change in the scene."
            ),
        ),
        QAItem(
            question="How can friends solve a problem together?",
            answer=(
                "Friends can share observations, listen to one another, stay calm, and choose an action that keeps "
                "everyone safe."
            ),
        ),
        QAItem(
            question="What is a twist in a story?",
            answer=(
                "A twist is a surprising change in understanding that makes earlier clues fit together in a new way."
            ),
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
        world = sample.world
        print("\n--- trace ---")
        print(
            f"hero={world.hero.name}, kind={world.hero.kind}, "
            f"memes={world.hero.memes}, meters={world.hero.meters}"
        )
        print(
            f"friend={world.friend.name}, kind={world.friend.kind}, "
            f"memes={world.friend.memes}, meters={world.friend.meters}"
        )
        print(
            f"place={world.place}, mechanism={world.mechanism}, "
            f"state={world.state}, trust={world.trust}"
        )
        print(f"clue={world.clue}")
        print(f"danger={world.danger}")

    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")

        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")

        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_mechanism(M) :- mechanism(M).
safe_mechanism(M) :- mechanism(M), caution(M).
friendship_solution :- friendship.
mystery_ready :- valid_place(P), valid_mechanism(M), safe_mechanism(M), friendship_solution.

#show valid_place/1.
#show valid_mechanism/1.
#show safe_mechanism/1.
#show friendship_solution/0.
#show mystery_ready/0.
"""


def asp_facts() -> str:
    import asp

    facts = [asp.fact("place", place) for place in PLACES]
    facts.extend(asp.fact("mechanism", item["name"]) for item in MECHANISMS)
    facts.extend(asp.fact("caution", item["name"]) for item in MECHANISMS)
    facts.append(asp.fact("friendship"))
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


def asp_safe_mechanisms() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show safe_mechanism/1."))
    return sorted(set(asp.atoms(model, "safe_mechanism")))


def asp_verify() -> int:
    py_places = {(place,) for place in PLACES}
    py_mechanisms = {(item["name"],) for item in MECHANISMS}
    py_safe = py_mechanisms
    cl_places = set(asp_valid_places())
    cl_mechanisms = set(asp_valid_mechanisms())
    cl_safe = set(asp_safe_mechanisms())

    problems = []
    if py_places != cl_places:
        problems.append(("places", py_places, cl_places))
    if py_mechanisms != cl_mechanisms:
        problems.append(("mechanisms", py_mechanisms, cl_mechanisms))
    if py_safe != cl_safe:
        problems.append(("safe mechanisms", py_safe, cl_safe))

    if problems:
        print("MISMATCH between Python and ASP:")
        for label, py_value, cl_value in problems:
            print(f"  {label}: python={sorted(py_value)} asp={sorted(cl_value)}")
        return 1

    for index in range(12):
        params = StoryParams(
            hero_name=NAMES[index % len(NAMES)],
            friend_name=NAMES[(index + 1) % len(NAMES)],
            place=PLACES[index % len(PLACES)],
            seed=index,
        )
        sample = generate(params)
        if not sample.story or len(sample.story_qa) < 3:
            print("Generated-story verification failed.")
            return 1

    print(
        "OK: ASP/Python parity holds for "
        f"{len(py_places)} places and {len(py_mechanisms)} mechanisms; "
        "generated stories passed."
    )
    return 0


def generation_params(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        return [
            StoryParams(
                hero_name=NAMES[index % len(NAMES)],
                friend_name=NAMES[(index + 1) % len(NAMES)],
                place=place,
                seed=index,
            )
            for index, place in enumerate(PLACES)
        ]

    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [
        resolve_params(args, random.Random(base + index))
        for index in range(args.n)
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(
            "#show valid_place/1.\n"
            "#show valid_mechanism/1.\n"
            "#show safe_mechanism/1.\n"
            "#show friendship_solution/0.\n"
            "#show mystery_ready/0."
        ))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("places:")
        for place in asp_valid_places():
            print(f"- {place[0]}")
        print("mechanisms:")
        for mechanism in asp_valid_mechanisms():
            print(f"- {mechanism[0]}")
        return

    samples = []
    for index, params in enumerate(generation_params(args)):
        if params.seed is None:
            params.seed = (args.seed if args.seed is not None else 0) + index
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps(
                [sample.to_dict() for sample in samples],
                indent=2,
                ensure_ascii=False,
            ))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
