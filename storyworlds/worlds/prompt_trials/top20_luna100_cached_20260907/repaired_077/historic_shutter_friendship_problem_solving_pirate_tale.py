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


@dataclass
class Character:
    name: str
    kind: str
    memes: dict[str, float] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    captain_name: str
    friend_name: str
    harbor: str
    weather: str
    seed: Optional[int] = None


@dataclass
class World:
    captain: Character
    friend: Character
    harbor: str
    weather: str
    shutter_state: str = "closed"
    friendship: float = 0.0
    problem_solved: bool = False
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


NAMES = ["Luna", "Mara", "Pip", "Tess", "Nico", "Rook", "Sable", "Finn"]
HARBORS = [
    "Moonhook Harbor",
    "Old Lantern Cove",
    "Pebblehook Bay",
    "Whispering Gull Harbor",
    "Red Sail Quay",
]
WEATHERS = ["a salty breeze", "a warm dawn", "a restless wind", "a silver fog"]


INCIDENTS = [
    {
        "title": "the stuck historic shutter",
        "problem": "the historic shutter on the old lighthouse would not open",
        "risk": "forcing the weathered wood could break the shutter and damage the lighthouse",
        "clue": "a strand of seaweed was wedged beneath its lower hinge",
        "first_try": "pulled hard on the iron handle",
        "helper": "the friend held a lantern low so the captain could see the hinge",
        "plan": "clear the seaweed, support the shutter with a rope, and lift together",
        "repair": "they loosened the seaweed, tied a rope around the shutter, and counted three careful pulls",
        "ending": "the historic shutter swung open and painted a bright square of sunlight across the lighthouse floor",
    },
    {
        "title": "the storm-latched shutter",
        "problem": "a historic shutter had slammed shut before the crew could read the lighthouse map behind it",
        "risk": "a sharp nail hidden in the old frame could tear a sleeve or hand",
        "clue": "fresh scratches showed that the latch had twisted sideways rather than locked",
        "first_try": "jabbed at the latch with a little sword",
        "helper": "the friend brought a wooden spoon from the galley to push the latch safely",
        "plan": "cover the sharp edge, turn the latch with the spoon, and keep hands behind the frame",
        "repair": "they wrapped the edge in a spare cloth and eased the crooked latch around",
        "ending": "the shutter opened without a scratch, revealing the map and a cheerful patch of blue sea",
    },
    {
        "title": "the painted shutter clue",
        "problem": "the bright paint on a historic shutter hid the mark that told ships where to anchor",
        "risk": "scraping at the old paint could erase a clue sailors had used for generations",
        "clue": "the mark appeared where rain had washed a narrow clean line",
        "first_try": "started scraping with a metal hook",
        "helper": "the friend fetched a soft brush and a bowl of warm water",
        "plan": "wash gently, compare the mark with the harbor chart, and stop if the paint lifted",
        "repair": "they brushed away dust and matched the revealed crescent to the chart",
        "ending": "the old crescent shone on the shutter while the crew anchored in the safe blue cove",
    },
    {
        "title": "the gull in the shutter",
        "problem": "a young gull had tangled one wing in the rope beside a historic shutter",
        "risk": "pulling the rope could frighten the bird or hurt its wing",
        "clue": "the rope slackened whenever the shutter was held still",
        "first_try": "reached quickly for the tangled rope",
        "helper": "the friend stood quietly with a blanket and called for the harbor keeper",
        "plan": "hold the shutter steady, cover the gull gently, and ask the keeper to free it",
        "repair": "they kept the wood still while the keeper carefully unwound the rope",
        "ending": "the gull fluttered over the historic shutter, and the loose rope was coiled safely on the deck",
    },
    {
        "title": "the hidden friendship flag",
        "problem": "the crew could not raise the friendship flag because it was trapped behind a historic shutter",
        "risk": "climbing the slippery outer wall could send someone tumbling into the harbor",
        "clue": "the flag cord hung inside the lighthouse, just beyond the shutter",
        "first_try": "began climbing the wet wall",
        "helper": "the friend noticed an old indoor staircase marked on the lighthouse plan",
        "plan": "use the stairs, open the shutter from inside, and keep both feet on dry boards",
        "repair": "they followed the plan upstairs and pulled the cord from the safe landing",
        "ending": "the friendship flag waved above the historic shutter while two crews cheered together",
    },
    {
        "title": "the missing shutter peg",
        "problem": "the peg that held a historic shutter open had vanished before a visiting crew arrived",
        "risk": "a loose shutter could swing in the wind and strike someone",
        "clue": "round dents in the dust led from the window to a barrel of spare ship parts",
        "first_try": "blamed the visiting pirates",
        "helper": "the friend searched the dust trail instead of arguing",
        "plan": "follow the marks, find a safe replacement peg, and explain the mistake honestly",
        "repair": "they found the peg under the barrel, returned it, and apologized to the visitors",
        "ending": "the shutter rested firmly on its peg as the visiting crew shared biscuits on the quay",
    },
]


OPENINGS = [
    "At dawn,",
    "When the tide curled around the harbor stones,",
    "On a bright morning beneath the ship's flag,",
    "Just before the crew checked the lighthouse bell,",
    "As the first gulls cried above the masts,",
]

REACTIONS = [
    "\"I pulled too fast,\" admitted {friend}. \"Let us look before we try again.\"",
    "{friend} rubbed a worried thumb over the map. \"A good crew solves problems together,\" they said.",
    "\"Wait,\" said {friend}. \"The shutter is old, so our plan must be gentle.\"",
    "{friend} took a breath. \"I do not know the answer yet, but I can help find it.\"",
]

LESSONS = [
    "The captain learned that friendship was not merely sharing a voyage; it was listening when a careful friend saw a safer way.",
    "They discovered that a hard problem often became smaller when two friends paused, inspected the clues, and made a plan.",
    "The crew remembered that old things deserved patience, and friends deserved a voice in every important choice.",
    "No pirate needed to solve every trouble alone when a trusted friend could bring a fresh idea.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Historic shutter pirate friendship story world.")
    parser.add_argument("--captain-name", choices=NAMES)
    parser.add_argument("--friend-name", choices=NAMES)
    parser.add_argument("--harbor", choices=HARBORS)
    parser.add_argument("--weather", choices=WEATHERS)
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
    captain = args.captain_name or rng.choice(NAMES)
    friend_choices = [name for name in NAMES if name != captain]
    friend = args.friend_name or rng.choice(friend_choices)
    return StoryParams(
        captain_name=captain,
        friend_name=friend,
        harbor=args.harbor or rng.choice(HARBORS),
        weather=args.weather or rng.choice(WEATHERS),
    )


def _reasonableness_gate(params: StoryParams) -> None:
    if params.captain_name == params.friend_name:
        raise StoryError("The captain and friend need different names.")
    if params.harbor not in HARBORS:
        raise StoryError("That harbor is not part of this pirate world.")
    if params.weather not in WEATHERS:
        raise StoryError("That weather does not belong in this story world.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    incident = rng.choice(INCIDENTS)
    opening = rng.choice(OPENINGS)
    reaction = rng.choice(REACTIONS).format(friend=params.friend_name)
    lesson = rng.choice(LESSONS)

    captain = Character(
        name=params.captain_name,
        kind="pirate captain",
        memes={"brave": 1.0, "curious": 1.0},
        meters={"patience": 0.4},
    )
    friend = Character(
        name=params.friend_name,
        kind="shipmate",
        memes={"loyal": 1.0, "observant": 1.0},
        meters={"confidence": 0.5},
    )
    world = World(
        captain=captain,
        friend=friend,
        harbor=params.harbor,
        weather=params.weather,
    )
    world.facts.update(
        problem=incident["problem"],
        risk=incident["risk"],
        clue=incident["clue"],
    )

    lines = [
        f"{opening} Captain {captain.name} sailed into {params.harbor}, where {params.weather} brushed the old lighthouse.",
        f"Behind the lighthouse stood {incident['problem']}.",
        f"The shutter was historic, with iron hinges darkened by many years of salt and rain.",
        f"Captain {captain.name} {incident['first_try']}, but the wood gave a loud groan.",
        f"The captain stopped. {incident['risk'].capitalize()}.",
        reaction,
        f"Then {friend.name} found an important clue: {incident['clue']}.",
        f"{friend.name} offered a plan: {incident['plan']}.",
        f"Together, the friends carried out the plan. {incident['repair']}.",
        f"The problem was solved because they shared the work instead of blaming one another.",
        lesson,
        incident["ending"].capitalize() + ".",
        f"That evening, Captain {captain.name} and {friend.name} marked the day in the ship's log as a victory for friendship and problem solving.",
    ]

    world.shutter_state = "open and secured"
    world.friendship = 1.0
    world.problem_solved = True
    world.facts.update(
        helper=incident["helper"],
        plan=incident["plan"],
        repair=incident["repair"],
        ending=incident["ending"],
    )
    world.facts["story"] = " ".join(lines)

    prompts = [
        f"Write a pirate tale about {incident['title']} in {params.harbor}.",
        f"Tell a story in which {params.captain_name} and {params.friend_name} solve a historic shutter problem through friendship.",
        "Show how careful observation and teamwork are safer than rushing.",
    ]

    story_qa = [
        QAItem(
            question="What problem did the friends face?",
            answer=f"They faced a problem because {incident['problem']}.",
        ),
        QAItem(
            question=f"What clue did {params.friend_name} notice?",
            answer=f"{params.friend_name} noticed that {incident['clue']}.",
        ),
        QAItem(
            question="How did the friends solve the problem?",
            answer=f"They solved it by deciding to {incident['plan']}. Then {incident['repair']}.",
        ),
        QAItem(
            question="Why was it unsafe to rush?",
            answer=f"It was unsafe to rush because {incident['risk']}.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer=f"The historic shutter was {world.shutter_state}, and {incident['ending']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a cover fitted over a window or opening. It can protect the opening from weather or darkness.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic means important because it belongs to the past or helps people remember the past.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring relationship in which people listen to, trust, and help one another.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means understanding a difficulty, noticing useful clues, making a safe plan, and trying the plan carefully.",
        ),
        QAItem(
            question="Why should people work together on a difficult task?",
            answer="Working together lets people share effort, notice different clues, and choose a safer answer than one person might find alone.",
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
        print(
            f"captain={world.captain.name}, kind={world.captain.kind}, "
            f"memes={world.captain.memes}, meters={world.captain.meters}"
        )
        print(
            f"friend={world.friend.name}, kind={world.friend.kind}, "
            f"memes={world.friend.memes}, meters={world.friend.meters}"
        )
        print(
            f"harbor={world.harbor}, weather={world.weather}, "
            f"shutter_state={world.shutter_state}, friendship={world.friendship}, "
            f"problem_solved={world.problem_solved}"
        )
        print(f"facts={world.facts}")
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
historic_shutter.
friendship_feature.
problem_solving_feature.
harbor(H) :- registered_harbor(H).
weather(W) :- registered_weather(W).
valid_world(H,W) :- harbor(H), weather(W), historic_shutter, friendship_feature, problem_solving_feature.
#show valid_world/2.
"""


def asp_facts() -> str:
    import asp
    facts = [asp.fact("registered_harbor", harbor) for harbor in HARBORS]
    facts.extend(asp.fact("registered_weather", weather) for weather in WEATHERS)
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_worlds() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_world/2."))
    return sorted(set(asp.atoms(model, "valid_world")))


def asp_verify() -> int:
    python_worlds = {(harbor, weather) for harbor in HARBORS for weather in WEATHERS}
    clingo_worlds = set(asp_valid_worlds())
    if python_worlds != clingo_worlds:
        print("MISMATCH between Python and ASP world registries.")
        print("Only in Python:", sorted(python_worlds - clingo_worlds))
        print("Only in ASP:", sorted(clingo_worlds - python_worlds))
        return 1

    for index, harbor in enumerate(HARBORS):
        params = StoryParams(
            captain_name=NAMES[index % len(NAMES)],
            friend_name=NAMES[(index + 1) % len(NAMES)],
            harbor=harbor,
            weather=WEATHERS[index % len(WEATHERS)],
            seed=index,
        )
        sample = generate(params)
        if not sample.world or not sample.world.problem_solved:
            print("Generated story failed its problem-solving check.")
            return 1

    print(f"OK: ASP matches Python ({len(python_worlds)} registered combinations), and generated stories solve their problems.")
    return 0


def generation_params(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        return [
            StoryParams(
                captain_name=NAMES[index % len(NAMES)],
                friend_name=NAMES[(index + 1) % len(NAMES)],
                harbor=harbor,
                weather=WEATHERS[index % len(WEATHERS)],
            )
            for index, harbor in enumerate(HARBORS)
        ]

    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [
        resolve_params(args, random.Random(base + index))
        for index in range(args.n)
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_world/2."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        for harbor, weather in asp_valid_worlds():
            print(f"{harbor} / {weather}")
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
