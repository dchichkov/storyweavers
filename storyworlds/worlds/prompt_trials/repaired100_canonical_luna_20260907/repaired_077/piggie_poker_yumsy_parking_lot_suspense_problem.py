#!/usr/bin/env python3
"""
A folk-tale story world about Piggie, Poker, and Yumsy solving a parking-lot
problem before a small surprise becomes a big one.
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
    helper_name: str
    witness_name: str
    setting: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Entity
    helper: Entity
    witness: Entity
    setting: str
    problem: str = ""
    clue: str = ""
    solution: str = ""
    danger: str = ""
    conflict: bool = False
    suspense: bool = False
    repaired: bool = False
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


NAMES = ["Luna", "Milo", "Pip", "Nora", "Tavi", "Suri", "Bram", "Cleo"]
SETTING = "the parking lot"


TRIALS = [
    {
        "problem": "a red wagon had rolled between two parked cars and blocked the narrow path to the sidewalk",
        "danger": "a driver might not see the wagon while backing out",
        "clue": "a trail of yellow chalk dust led from the wagon to the painted play square",
        "wrong": "pushed the wagon deeper between the cars",
        "solution": "asked the lot keeper to pause the nearby cars, then pulled the wagon by its handle into the safe play square",
        "ending": "the wagon rested in the bright square, where every driver could see it",
        "lesson": "A small obstacle becomes smaller when someone stops, looks, and asks for help.",
    },
    {
        "problem": "a blue scarf fluttered beneath a delivery van while a little bell rang somewhere in the shadows",
        "danger": "reaching beneath the van could put a small paw or hand near moving wheels",
        "clue": "the bell rang whenever the wind pushed the scarf against a loose shopping basket",
        "wrong": "crawled toward the dark space under the van",
        "solution": "stood well back, called the attendant, and used a long broom to draw the scarf and basket into the open",
        "ending": "the scarf was folded on a bench, and the bell was quiet in the warm afternoon",
        "lesson": "Courage is not crawling into danger; courage is choosing a safe helper.",
    },
    {
        "problem": "a cardboard box trembled beside the cart return, and a tiny scratching sound came from inside",
        "danger": "the box could hold a frightened animal, but lifting it without care might make the animal bolt into traffic",
        "clue": "two neat paw marks appeared beside a torn corner of the box",
        "wrong": "grabbed the box and ran toward the quietest row",
        "solution": "kept everyone still, called the animal rescue helper, and guided the small kitten into a carrier with a soft blanket",
        "ending": "the kitten blinked from its carrier while the cart return stood clear",
        "lesson": "When a mystery may contain a living creature, patience protects more than haste.",
    },
    {
        "problem": "a silver coin rolled beneath a car just as the car's lights blinked",
        "danger": "the driver might start moving before anyone knew a child was near the wheels",
        "clue": "the coin had stopped beside a white parking line, where it could be reached from a safe distance",
        "wrong": "ducked beneath the car to snatch it",
        "solution": "stepped away, waved to the driver, and asked the driver to check the car before moving",
        "ending": "the coin came out with a broom, shining safely in an open palm",
        "lesson": "A treasure is never worth risking a body; a clear warning can save the day.",
    },
    {
        "problem": "a string of paper stars had fallen across the entrance lane before the evening market",
        "danger": "tires could catch the string and scatter the stars under moving cars",
        "clue": "the loose end was tied to a market sign that had tipped in the wind",
        "wrong": "tugged the string without watching the lane",
        "solution": "stood behind the safety cone, signaled the attendant, and gathered the stars after the lane was stopped",
        "ending": "the stars hung above the market gate, sparkling instead of tangling around tires",
        "lesson": "Good problem solving makes room for both a careful plan and a watchful friend.",
    },
]


OPENINGS = [
    "In the old parking lot behind the market,",
    "One breezy afternoon in the parking lot,",
    "At the hour when shadows stretched beneath the cars,",
    "Before the evening stalls opened,",
    "On a day when the parking lot seemed quiet as a pond,",
]

REACTIONS = [
    "{helper} whispered, \"Do not rush. What do we truly know?\"",
    "{helper} raised a paw. \"Stop first, then we can solve it together.\"",
    "\"I have a guess,\" said {helper}, \"but a guess is not a clue.\"",
    "{helper} looked toward the attendant. \"This needs a safe plan, not a brave-looking one.\"",
]

CODAS = [
    "From then on, the three friends called the rule their parking-lot wisdom: stop, see, and seek a helper.",
    "The market folk repeated the tale, for even a small friend can notice the first important clue.",
    "And whenever a shadow made the lot seem mysterious, they remembered to brighten it with questions.",
    "By sunset, the lot was peaceful again, but the lesson stayed bright as a painted line.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Piggie, Poker, and Yumsy parking-lot folk tale.")
    parser.add_argument("--hero-name", choices=NAMES)
    parser.add_argument("--helper-name", choices=NAMES)
    parser.add_argument("--witness-name", choices=NAMES)
    parser.add_argument("--setting", choices=[SETTING])
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
    hero = args.hero_name or "Piggie"
    helper = args.helper_name or "Poker"
    witness = args.witness_name or "Yumsy"
    if len({hero, helper, witness}) != 3:
        raise StoryError("Piggie, Poker, and Yumsy must have different names in this tale.")
    return StoryParams(
        hero_name=hero,
        helper_name=helper,
        witness_name=witness,
        setting=args.setting or SETTING,
    )


def _reasonableness_gate(params: StoryParams) -> None:
    if params.setting != SETTING:
        raise StoryError("This folk tale belongs in the parking lot.")
    if len({params.hero_name, params.helper_name, params.witness_name}) != 3:
        raise StoryError("The three friends need different names so their choices are clear.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    trial = rng.choice(TRIALS)
    opening = rng.choice(OPENINGS)
    reaction = rng.choice(REACTIONS).format(helper=params.helper_name)
    coda = rng.choice(CODAS)

    hero = Entity(
        name=params.hero_name,
        kind="piggie",
        meters={"distance_to_problem": 2.0, "safe_distance": 1.0},
        memes={"curiosity": 1.0, "care": 1.0},
    )
    helper = Entity(
        name=params.helper_name,
        kind="poker",
        meters={"distance_to_helper": 3.0},
        memes={"patience": 1.0, "planning": 1.0},
    )
    witness = Entity(
        name=params.witness_name,
        kind="yumsy",
        meters={"distance_to_clue": 1.0},
        memes={"alertness": 1.0, "kindness": 1.0},
    )
    world = World(hero=hero, helper=helper, witness=witness, setting=params.setting)
    world.problem = trial["problem"]
    world.danger = trial["danger"]
    world.clue = trial["clue"]
    world.solution = trial["solution"]
    world.conflict = True
    world.suspense = True
    world.facts.update(
        problem=trial["problem"],
        danger=trial["danger"],
        clue=trial["clue"],
        solution=trial["solution"],
    )

    lines = [
        f"{opening} Piggie, Poker, and Yumsy were keeping watch over the quiet spaces between the cars.",
        f"Then {trial['problem']}.",
        f"The friends felt suspense gather like a dark cloud, because {trial['danger']}.",
        f"Piggie wanted to act at once and {trial['wrong']}.",
        reaction,
        f"Yumsy pointed to the ground. \"Look there,\" Yumsy said. \"{trial['clue'].capitalize()}.\"",
        f"Poker studied the lane, the shadows, and the safe place to stand. \"We can solve this without stepping into danger,\" Poker said.",
        f"Piggie listened, stepped back, and answered, \"Then let us make the safe choice together.\"",
        f"With the conflict clear, the friends {trial['solution']}.",
        f"The danger passed, and {trial['ending']}.",
        trial["lesson"],
        coda,
    ]
    world.repaired = True
    world.facts["ending"] = trial["ending"]
    world.facts["lesson"] = trial["lesson"]
    world.facts["story"] = " ".join(lines)

    prompts = [
        f"Write a folk tale about Piggie, Poker, and Yumsy solving a suspenseful problem in {params.setting}.",
        f"Show conflict when {trial['problem']}, then use a clue and a safe helper to solve it.",
        "Make the ending prove that careful problem solving changed the parking lot.",
    ]

    story_qa = [
        QAItem(
            question="What problem did Piggie, Poker, and Yumsy discover?",
            answer=f"They discovered that {trial['problem']}.",
        ),
        QAItem(
            question="Why was the problem dangerous?",
            answer=f"It was dangerous because {trial['danger']}.",
        ),
        QAItem(
            question="What clue helped the friends understand the situation?",
            answer=f"The clue was that {trial['clue']}.",
        ),
        QAItem(
            question="How did the friends solve the problem safely?",
            answer=f"They solved it when they {trial['solution']}.",
        ),
        QAItem(
            question="What did the friends learn?",
            answer=trial["lesson"],
        ),
    ]

    world_qa = [
        QAItem(
            question="Why should people stay alert in a parking lot?",
            answer="People should stay alert because cars can move unexpectedly and drivers may not see small people or objects.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing the facts, considering danger, making a plan, and taking a safe step toward a fix.",
        ),
        QAItem(
            question="What should a child do near a vehicle problem?",
            answer="A child should stay away from wheels and moving cars, tell a responsible adult, and follow the adult's safety directions.",
        ),
        QAItem(
            question="What makes suspense in a story?",
            answer="Suspense grows when a character faces an uncertain danger and readers want to know what will happen next.",
        ),
        QAItem(
            question="Why is asking for help a strong choice?",
            answer="Asking for help brings another careful person to the problem and can prevent a rushed or dangerous action.",
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        world = sample.world
        print("\n--- trace ---")
        for entity in (world.hero, world.helper, world.witness):
            print(
                f"{entity.name}: kind={entity.kind}, meters={entity.meters}, "
                f"memes={entity.memes}"
            )
        print(
            f"setting={world.setting}, suspense={world.suspense}, "
            f"conflict={world.conflict}, repaired={world.repaired}"
        )
        print(f"problem={world.problem}")
        print(f"clue={world.clue}")
        print(f"solution={world.solution}")
    if qa:
        print("\n== prompts ==")
        for number, prompt in enumerate(sample.prompts, 1):
            print(f"{number}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
required_place(parking_lot).
required_kind(piggie).
required_kind(poker).
required_kind(yumsy).

valid_setting(S) :- required_place(S).
valid_cast(H, P, Y) :- required_kind(H), required_kind(P), required_kind(Y), H != P, H != Y, P != Y.
safe_turn :- valid_setting(parking_lot), valid_cast(piggie,poker,yumsy).
solved :- safe_turn.

#show valid_setting/1.
#show valid_cast/3.
#show safe_turn/0.
#show solved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "parking_lot"),
            asp.fact("character_kind", "piggie"),
            asp.fact("character_kind", "poker"),
            asp.fact("character_kind", "yumsy"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_gate() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_turn/0."))
    return set(asp.atoms(model, "safe_turn"))


def asp_verify() -> int:
    expected = {()}
    actual = asp_gate()
    if actual != expected:
        print(f"MISMATCH between Python and ASP gate: expected {expected}, got {actual}")
        return 1
    print("OK: ASP and Python agree that the Piggie, Poker, and Yumsy setting is valid.")
    for index in range(5):
        params = StoryParams(
            hero_name="Piggie",
            helper_name="Poker",
            witness_name="Yumsy",
            setting=SETTING,
            seed=index,
        )
        sample = generate(params)
        if not sample.story or not sample.story.endswith("."):
            print("MISMATCH: generated story is incomplete.")
            return 1
        if "Piggie" not in sample.story or "Poker" not in sample.story or "Yumsy" not in sample.story:
            print("MISMATCH: generated story lost a required character.")
            return 1
    print("OK: generated stories pass the narrative exercise.")
    return 0


def generation_params(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        return [
            StoryParams(
                hero_name="Piggie",
                helper_name="Poker",
                witness_name="Yumsy",
                setting=SETTING,
                seed=index,
            )
            for index in range(len(TRIALS))
        ]
    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [
        resolve_params(args, random.Random(base + index))
        for index in range(max(0, args.n))
    ]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_setting/1.\n#show valid_cast/3.\n#show safe_turn/0.\n#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_setting/1.\n#show valid_cast/3.\n#show safe_turn/0.\n#show solved/0."))
        for atom in model:
            print(atom)
        return

    samples: list[StorySample] = []
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
