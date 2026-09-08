#!/usr/bin/env python3
"""
A standalone story world about a bakery mystery, friendship, humor, and a lesson learned.
"""

from __future__ import annotations

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


FRIENDS = ["Luna", "Milo", "Nia", "Theo", "Poppy", "Sam"]
BAKERS = ["Mr. Rowan", "Aunt Bea", "Ms. Crumb", "Chef Rosa"]
BAKERIES = ["Moonrise Bakery", "Honeybell Bakery", "The Warm Whisk", "Blue Door Bakery"]
PASTRIES = ["cinnamon rolls", "berry buns", "chocolate twists", "lemon tarts"]
CLUES = [
    "a trail of flour near the back door",
    "three blueberry spots on the floor",
    "a warm oven mitt beneath the counter",
    "a tiny paper star stuck to a basket",
]
TOOLS = ["a magnifying glass", "a recipe card", "a red ribbon", "a small flashlight"]
JOKES = [
    "The flour cloud made Milo sneeze so loudly that a cupcake trembled.",
    "Luna wore a paper chef hat that slid over one eye.",
    "A rolling pin rolled away as if it had solved the mystery first.",
    "Theo whispered to a loaf, and the loaf answered only with a crunchy crust.",
]
LESSONS = [
    "good friends ask before they guess",
    "a careful search is better than a hurried accusation",
    "mistakes become easier to fix when friends tell the truth",
    "listening closely can uncover a kinder answer",
]

INCIDENTS = [
    {
        "id": "vanished_star",
        "mystery": "the golden star cookie for the bakery window had vanished",
        "truth": "the cookie had been placed in a cooling tray behind a stack of empty boxes",
        "turn": "a warm buttery smell led from the display case toward the storage shelf",
        "resolution": "they found the cookie safe in the cooling tray",
        "ending": "the golden cookie shone in the window beside a handwritten friendship sign",
    },
    {
        "id": "missing_recipe",
        "mystery": "the recipe card for the famous berry buns had disappeared",
        "truth": "the card was tucked inside the flour ledger after a gust from the open door",
        "turn": "a blueberry fingerprint marked the ledger's corner",
        "resolution": "they discovered the recipe folded neatly inside the ledger",
        "ending": "the recipe card rested under a clean paperweight while berry buns cooled nearby",
    },
    {
        "id": "crooked_bread",
        "mystery": "the champion loaf had come out with a mysterious crooked smile",
        "truth": "a spoon had slipped against the dough before baking",
        "turn": "a shiny spoon mark curved across the loaf pan",
        "resolution": "they learned that the spoon had nudged the dough when nobody was looking",
        "ending": "customers laughed kindly at the loaf's smile before sharing every slice",
    },
]

@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Mystery:
    object: str
    clue: str
    truth: str
    resolution: str
    solved: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    friend: Person
    baker: Person
    bakery: str
    pastry: str
    tool: str
    incident: dict
    mystery: Mystery
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def say(self, line: str) -> None:
        self.lines.append(line)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    friend: str
    baker: str
    bakery: str
    pastry: str
    tool: str
    incident: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A bakery mystery about friendship, humor, and a lesson learned."
    )
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--baker", choices=BAKERS)
    parser.add_argument("--bakery", choices=BAKERIES)
    parser.add_argument("--pastry", choices=PASTRIES)
    parser.add_argument("--tool", choices=TOOLS)
    parser.add_argument("--incident", choices=[x["id"] for x in INCIDENTS])
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


def valid_combo(params: StoryParams) -> bool:
    return (
        params.friend in FRIENDS
        and params.baker in BAKERS
        and params.bakery in BAKERIES
        and params.pastry in PASTRIES
        and params.tool in TOOLS
        and params.incident in {x["id"] for x in INCIDENTS}
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        friend=args.friend or rng.choice(FRIENDS),
        baker=args.baker or rng.choice(BAKERS),
        bakery=args.bakery or rng.choice(BAKERIES),
        pastry=args.pastry or rng.choice(PASTRIES),
        tool=args.tool or rng.choice(TOOLS),
        incident=args.incident or rng.choice([x["id"] for x in INCIDENTS]),
        seed=args.seed,
    )
    if not valid_combo(params):
        raise StoryError("The requested bakery mystery choices do not form a valid story.")
    return params


def make_world(params: StoryParams) -> World:
    incident = next(item for item in INCIDENTS if item["id"] == params.incident)
    friend = Person(
        params.friend,
        "young bakery helper",
        meters={"curiosity": 1.0, "care": 1.0},
        memes={"worry": 0.2, "friendship": 0.5, "humor": 0.0},
    )
    baker = Person(
        params.baker,
        "baker",
        meters={"patience": 1.0},
        memes={"trust": 1.0},
    )
    mystery = Mystery(
        object=incident["mystery"],
        clue=incident["clue"],
        truth=incident["truth"],
        resolution=incident["resolution"],
        meters={"mystery": 1.0},
        memes={"confusion": 1.0},
    )
    return World(
        friend=friend,
        baker=baker,
        bakery=params.bakery,
        pastry=params.pastry,
        tool=params.tool,
        incident=incident,
        mystery=mystery,
        facts={"lesson": random.Random(params.seed).choice(LESSONS) if params.seed is not None else LESSONS[0]},
    )


def generate_story(world: World) -> None:
    friend = world.friend.name
    baker = world.baker.name
    incident = world.incident
    lesson = world.facts["lesson"]

    world.say(
        f"At {world.bakery}, the morning ovens hummed while {friend} helped prepare "
        f"{world.pastry}."
    )
    world.say(f"Then {friend} noticed a mystery: {incident['mystery']}.")
    world.say(f'"I know who did it!" {friend} cried.')
    world.say(
        f'"Do you?" asked {baker}. "A mystery needs clues, not guesses." '
        f"{friend} looked again and found {incident['clue']}."
    )
    world.friend.memes["worry"] += 0.4
    world.say(
        f"{friend} used {world.tool} and followed the clue past the mixing bowl. "
        f"{JOKES[sum(ord(c) for c in friend) % len(JOKES)]}"
    )
    world.say(
        f'"Let us search together,' said {friend}. "Friends should help, not blame." '
        f'"That is a much better recipe," said {baker}."
    )
    world.friend.memes["friendship"] += 1.0
    world.friend.memes["humor"] += 1.0
    world.say(f"The clue led them to the truth: {incident['truth']}.")
    world.mystery.solved = True
    world.mystery.memes["confusion"] = 0.0
    world.say(
        f"They {incident['resolution']}. {friend} apologized for guessing too quickly, "
        f"and {baker} thanked the friend for telling the truth."
    )
    world.say(
        f"By lunchtime, {friend} had learned that {lesson}. "
        f"Everyone shared the {world.pastry}, and even the mystery seemed to smile."
    )
    world.say(f"At closing time, {incident['ending']}.")


def story_qa(world: World) -> list[QAItem]:
    friend = world.friend.name
    baker = world.baker.name
    incident = world.incident
    return [
        QAItem(
            question=f"What mystery did {friend} notice?",
            answer=f"{friend} noticed that {incident['mystery']}.",
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=f"The clue was {incident['clue']}. It guided the friends toward the answer.",
        ),
        QAItem(
            question=f"How did {friend} and {baker} solve the mystery?",
            answer=f"They searched together and learned that {incident['truth']}.",
        ),
        QAItem(
            question="What lesson did the friend learn?",
            answer=f"The friend learned that {world.facts['lesson']}.",
        ),
        QAItem(
            question="How did humor help the bakery?",
            answer="The funny moment made everyone less worried, so the friends could keep searching kindly.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should friends look for clues before blaming someone?",
            answer="Clues help friends learn what really happened and avoid unfair accusations.",
        ),
        QAItem(
            question="What is a bakery?",
            answer="A bakery is a place where people make and sell bread, cakes, cookies, and other baked foods.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, helping them, and treating them with trust.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is an idea someone understands after an experience changes what they do.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly bakery mystery in which friendship, humor, and a lesson learned change the investigation.",
        f"Tell how {world.friend.name} solves a mystery at {world.bakery} by following the clue {world.incident['clue']}.",
        f"Write a gentle mystery where {world.friend.name} and {world.baker.name} search for {world.incident['mystery']} without blaming anyone.",
    ]


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"friend={world.friend.name} meters={world.friend.meters} memes={world.friend.memes}",
            f"baker={world.baker.name} role={world.baker.role}",
            f"bakery={world.bakery} pastry={world.pastry} tool={world.tool}",
            f"mystery={world.mystery.object} clue={world.mystery.clue}",
            f"solved={world.mystery.solved} truth={world.mystery.truth}",
        ]
    )


def format_qa(sample: StorySample) -> str:
    sections = ["== prompts =="]
    sections.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    sections.append("")
    sections.append("== story QA ==")
    for item in sample.story_qa:
        sections.extend([f"Q: {item.question}", f"A: {item.answer}"])
    sections.append("")
    sections.append("== world QA ==")
    for item in sample.world_qa:
        sections.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(sections)


def asp_facts() -> str:
    import asp

    lines = ["domain(rbi).", "setting(bakery)."]
    for friend in FRIENDS:
        lines.append(asp.fact("friend", friend))
    for baker in BAKERS:
        lines.append(asp.fact("baker", baker))
    for bakery in BAKERIES:
        lines.append(asp.fact("bakery", bakery))
    for incident in INCIDENTS:
        lines.append(asp.fact("mystery", incident["id"]))
    return "\n".join(lines)


ASP_RULES = r"""
valid(F,B,K,I) :-
    friend(F),
    baker(B),
    bakery(K),
    mystery(I),
    domain(rbi),
    setting(bakery).
#show valid/4.
"""


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    python = {
        (friend, baker, bakery, incident["id"])
        for friend in FRIENDS
        for baker in BAKERS
        for bakery in BAKERIES
        for incident in INCIDENTS
    }
    model = asp.one_model(asp_program())
    clingo_set = set(asp.atoms(model, "valid"))
    if python != clingo_set:
        print("MISMATCH")
        print("only in Python:", sorted(python - clingo_set))
        print("only in ASP:", sorted(clingo_set - python))
        return 1
    for params in curated_params():
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP/Python parity verified for {len(python)} combinations and generated stories.")
    return 0


def curated_params() -> list[StoryParams]:
    return [
        StoryParams("Luna", "Mr. Rowan", "Moonrise Bakery", "cinnamon rolls", "a magnifying glass", "vanished_star"),
        StoryParams("Milo", "Aunt Bea", "Honeybell Bakery", "berry buns", "a recipe card", "missing_recipe"),
        StoryParams("Nia", "Chef Rosa", "Blue Door Bakery", "lemon tarts", "a red ribbon", "crooked_bread"),
    ]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    generate_story(world)
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

    if args.show_asp or args.asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in curated_params()]
    else:
        samples = []
        for index in range(max(1, args.n)):
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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
