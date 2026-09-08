#!/usr/bin/env python3
"""
A small pirate tale about a historic shutter, friendship, and solving a problem together.
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


NAMES = ["Luna", "Pip", "Maris", "Cora", "Finn", "Tavi", "Nell", "Rook"]
PLACES = [
    "the old harbor tower",
    "the moonlit pirate port",
    "the weathered lighthouse",
    "the captain's island home",
    "the quiet cove",
]

PROBLEMS = [
    {
        "title": "the historic shutter",
        "setup": "a historic wooden shutter hung crookedly above the harbor tower",
        "risk": "a strong sea wind could tear it loose and send it crashing onto the dock",
        "clue": "one bronze hinge still held while a rope had wrapped around the lower latch",
        "first": "grabbed the shutter and pulled with all their might",
        "dialogue": [
            '"Hold fast!" cried {hero}. "I can pull it free."',
            '"Wait," said {friend}. "If we pull together without a plan, the hinge may split."',
        ],
        "plan": "they tied a spare sail rope around the frame, braced a plank beneath it, and loosened the tangled rope one loop at a time",
        "ending": "the shutter rested safely against the tower, ready for careful repair",
    },
    {
        "title": "the salt-worn window",
        "setup": "a salt-worn historic shutter had slammed across the lighthouse window",
        "risk": "the keeper could not see the reef lights, and a passing boat might mistake the dark window for a warning",
        "clue": "the shutter moved slightly whenever the tide pulled a loose chain below the sill",
        "first": "climbed the slippery stones and tried to force the shutter open",
        "dialogue": [
            '"I will reach it first!" said {hero}.',
            '"And I will watch your footing," answered {friend}. "A clever rescue needs two pairs of eyes."',
        ],
        "plan": "one friend held the lantern and called safe steps while the other used a boat hook to lift the loose chain",
        "ending": "the window opened, and the lighthouse beam swept safely across the reef",
    },
    {
        "title": "the painted pirate shutter",
        "setup": "a bright historic shutter painted with a tiny pirate star had fallen across the captain's doorway",
        "risk": "the crew could not reach the medicine chest inside before the next tide",
        "clue": "the shutter's lower edge rested on a smooth barrel that could roll if freed",
        "first": "tried to lift the heavy wood alone",
        "dialogue": [
            '"I am captain enough for this," said {hero}.',
            '"You are a brave captain," replied {friend}, "but even captains need a useful plan."',
        ],
        "plan": "they wedged a board beneath the shutter, rolled the barrel aside, and lifted on the count of three",
        "ending": "the doorway stood clear, and the painted star shone above the grateful crew",
    },
    {
        "title": "the museum shutter mystery",
        "setup": "a historic shutter had closed over a small room of maps in the pirate museum",
        "risk": "rain blowing through a cracked roof could soak the oldest chart",
        "clue": "fresh wet footprints led from the shutter to a bucket, not to the locked map room",
        "first": "accused a shy cabin boy of hiding the key",
        "dialogue": [
            '"Someone has stolen the key!" declared {hero}.',
            '"Let us follow what we know," said {friend}. "Footprints can tell us more than guesses."',
        ],
        "plan": "they traced the footprints, found the key beside the rain bucket, and used a cloth to protect the chart",
        "ending": "the old map dried beneath a clean cloth while the shutter was marked for repair",
    },
    {
        "title": "the storm-battered shutter",
        "setup": "a storm-battered historic shutter banged against the cove inn",
        "risk": "each bang shook loose another nail from the wall",
        "clue": "the rhythm stopped whenever a coil of anchor line was pressed against the frame",
        "first": "chased the banging shutter from side to side",
        "dialogue": [
            '"The shutter is dancing!" laughed {hero}, though the wall trembled.',
            '"Then let us give it a steadier partner," said {friend}.',
        ],
        "plan": "they padded the frame with sailcloth, secured it with anchor line, and hammered in a safe temporary peg",
        "ending": "the storm still roared, but the shutter rested quietly against its padded frame",
    },
]

OPENINGS = [
    "At dawn, when gulls circled the harbor",
    "One evening beneath a round pirate moon",
    "After a night of hard rain",
    "While the tide crept toward the docks",
    "On a calm morning at the edge of the sea",
]

LESSONS = [
    "Luna learned that friendship was not merely sailing side by side; it was listening when a friend saw a safer way.",
    "The crew discovered that a problem became smaller when brave friends shared the looking, thinking, and doing.",
    "They learned that a clever plan could be stronger than a hurried pull, especially when old wood and wild weather were involved.",
    "The sea taught them that asking for help was not weakness. It was good seamanship.",
    "Their friendship grew like a strong rope: one strand helped, but many strands held fast.",
]


@dataclass
class Character:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Shutter:
    material: str
    age: str
    state: str = "unsafe"
    location: str = "harbor"


@dataclass
class World:
    hero: Character
    friend: Character
    shutter: Shutter
    place: str
    problem: str = ""
    clue: str = ""
    plan: str = ""
    solved: bool = False
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    hero_name: str
    friend_name: str
    place: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Historic shutter pirate tale about friendship and problem solving."
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
    choices = [name for name in NAMES if name != hero]
    friend = args.friend_name or rng.choice(choices)
    place = args.place or rng.choice(PLACES)
    return StoryParams(hero_name=hero, friend_name=friend, place=place)


def _reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name == params.friend_name:
        raise StoryError("The pirate friends need different names.")
    if params.place not in PLACES:
        raise StoryError("That place is not part of this small pirate world.")
    if params.hero_name not in NAMES or params.friend_name not in NAMES:
        raise StoryError("Every pirate name must come from the ship's roster.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    problem = rng.choice(PROBLEMS)
    opening = rng.choice(OPENINGS)
    lesson = rng.choice(LESSONS)

    hero = Character(
        name=params.hero_name,
        kind="young pirate",
        meters={"courage": 0.7, "patience": 0.4},
        memes={"friendship": 0.8, "problem_solving": 0.6},
    )
    friend = Character(
        name=params.friend_name,
        kind="young pirate",
        meters={"courage": 0.6, "patience": 0.8},
        memes={"friendship": 0.9, "problem_solving": 0.9},
    )
    shutter = Shutter(material="oak", age="historic")
    world = World(hero=hero, friend=friend, shutter=shutter, place=params.place)
    world.problem = problem["risk"]
    world.clue = problem["clue"]
    world.plan = problem["plan"]

    dialogue = [
        line.format(hero=params.hero_name, friend=params.friend_name)
        for line in problem["dialogue"]
    ]

    lines = [
        f"{opening}, {params.hero_name} and {params.friend_name} sailed into {params.place}.",
        f"There they saw {problem['setup']}.",
        f"The danger was plain: {problem['risk']}.",
        f"{params.hero_name} hurried forward and {problem['first']}.",
        dialogue[0],
        dialogue[1],
        f"Together they looked closely instead of blaming the sea or one another. The clue was that {problem['clue']}.",
        f"That clue changed their plan. {problem['plan'].capitalize()}.",
        f"At last, the historic shutter was safe: {problem['ending']}.",
        lesson,
        f"{params.hero_name} grinned at {params.friend_name}. \"Best crew in the harbor,\" they said.",
        f"\"Best crew because we think together,\" {params.friend_name} replied.",
        f"Above them, the repaired-looking frame caught the last gold light, and the two friends sailed on beneath it.",
    ]

    world.solved = True
    world.shutter.state = "secured"
    world.facts.update(
        {
            "title": problem["title"],
            "risk": problem["risk"],
            "clue": problem["clue"],
            "plan": problem["plan"],
            "ending": problem["ending"],
            "lesson": lesson,
        }
    )
    world.facts["story"] = " ".join(lines)

    prompts = [
        f"Write a pirate tale about {params.hero_name} and {params.friend_name} solving a problem with a historic shutter.",
        f"Tell a child-friendly friendship story set at {params.place}, where careful observation leads to a safe plan.",
        "Show that problem solving works better when pirate friends listen to each other.",
    ]

    story_qa = [
        QAItem(
            question=f"What problem did {params.hero_name} and {params.friend_name} discover?",
            answer=f"They discovered that {problem['setup']}, and {problem['risk']}.",
        ),
        QAItem(
            question="What clue helped the friends understand the problem?",
            answer=f"The important clue was that {problem['clue']}.",
        ),
        QAItem(
            question="How did the friends solve the problem?",
            answer=f"They solved it when {problem['plan']}.",
        ),
        QAItem(
            question="How did friendship help the pirates?",
            answer=(
                f"Their friendship helped because {params.hero_name} listened to "
                f"{params.friend_name}, and they shared the looking, planning, and work."
            ),
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The danger was removed, and {problem['ending']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a wooden or metal panel that covers a window or opening for protection.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic means important or connected to the past.",
        ),
        QAItem(
            question="Why should people inspect a loose shutter before pulling it?",
            answer=(
                "They should inspect it because a loose hinge, rope, or piece of wood could break "
                "or fall and hurt someone."
            ),
        ),
        QAItem(
            question="What is problem solving?",
            answer=(
                "Problem solving means noticing the problem, looking for useful clues, making a safe plan, "
                "and checking whether the plan worked."
            ),
        ),
        QAItem(
            question="How can friends work well together?",
            answer=(
                "Friends can listen to one another, share observations, divide safe tasks, and change their plan "
                "when new evidence appears."
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
            f"place={world.place}, shutter_age={world.shutter.age}, "
            f"shutter_state={world.shutter.state}, solved={world.solved}"
        )
        print(f"risk={world.problem}")
        print(f"clue={world.clue}")
        print(f"plan={world.plan}")
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
historic_shutter :- shutter_age(historic).
friendship :- pirate(H), pirate(F), H != F.
problem_solving :- friendship, clue_available, safe_plan.
safe_plan :- plan_method(inspect).
safe_plan :- plan_method(brace).
safe_plan :- plan_method(tie).
safe_plan :- plan_method(lift).
solved :- historic_shutter, problem_solving.

#show valid_place/1.
#show solved/0.
"""


def asp_facts() -> str:
    import asp

    facts = [asp.fact("place", place) for place in PLACES]
    facts.append(asp.fact("shutter_age", "historic"))
    facts.extend(
        [
            asp.fact("pirate", "hero"),
            asp.fact("pirate", "friend"),
            asp.fact("clue_available"),
            asp.fact("plan_method", "inspect"),
            asp.fact("plan_method", "brace"),
            asp.fact("plan_method", "tie"),
            asp.fact("plan_method", "lift"),
        ]
    )
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_place/1."))
    return sorted(set(asp.atoms(model, "valid_place")))


def asp_solved() -> bool:
    import asp

    model = asp.one_model(asp_program("#show solved/0."))
    return bool(asp.atoms(model, "solved"))


def asp_verify() -> int:
    python_places = {(place,) for place in PLACES}
    clingo_places = set(asp_valid_places())
    if python_places != clingo_places:
        print("MISMATCH between Python and ASP place registries.")
        print("  only in python:", sorted(python_places - clingo_places))
        print("  only in clingo:", sorted(clingo_places - python_places))
        return 1
    if not asp_solved():
        print("MISMATCH: ASP did not derive a solved historic-shutter story.")
        return 1

    for index, params in enumerate(
        [
            StoryParams(
                hero_name=NAMES[index % len(NAMES)],
                friend_name=NAMES[(index + 1) % len(NAMES)],
                place=PLACES[index % len(PLACES)],
                seed=index,
            )
            for index in range(8)
        ]
    ):
        sample = generate(params)
        if not sample.story or "historic shutter" not in sample.story:
            print(f"Generation check failed for sample {index + 1}.")
            return 1
        if not sample.world or not sample.world.solved:
            print(f"World resolution check failed for sample {index + 1}.")
            return 1

    print(
        f"OK: ASP matches {len(PLACES)} places, derives a solved story, "
        "and generated samples pass."
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
        for index in range(max(0, args.n))
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_place/1.\n#show solved/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        for place, in asp_valid_places():
            print(place)
        print(f"solved={asp_solved()}")
        return

    samples: list[StorySample] = []
    for index, params in enumerate(generation_params(args)):
        if args.seed is not None:
            params.seed = args.seed + index
        elif params.seed is None:
            params.seed = index
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
