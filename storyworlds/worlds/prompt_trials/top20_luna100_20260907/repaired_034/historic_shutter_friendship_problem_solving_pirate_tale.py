#!/usr/bin/env python3
"""
A small pirate-tale storyworld about a historic shutter, friendship, and problem solving.
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
sys.path.insert(0, os.path.dirname(_storyworlds_dir))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    hero: str = "Luna"
    friend: str = "Tess"
    ship: str = "the Starfish"
    island: str = "Whistle Key"
    arc: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    hero: Entity
    friend: Entity
    ship: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


HERO_NAMES = ["Luna", "Mara", "Pip", "Juno", "Nell", "Cora"]
FRIEND_NAMES = ["Tess", "Bram", "Kit", "Ollie", "Faye", "Rook"]
SHIPS = ["the Starfish", "the Blue Parrot", "the Merry Gull", "the Copper Crab"]
ISLANDS = ["Whistle Key", "Old Lantern Isle", "Coral Crown", "Button Bay"]

ARCS = [
    {
        "premise": "The historic lighthouse on the island had guided sailors for more than a hundred years",
        "problem": "its wooden shutter slammed shut during a sudden sea wind",
        "stake": "The evening boats could miss the safe channel between the rocks",
        "clue": "a loose brass pin rattled inside the shutter frame",
        "plan": "They lowered a rope, braced the frame with a spare oar, and worked together to lift the shutter",
        "twist": "the shutter was not broken; a tiny gull had built a nest behind it",
        "resolution": "They moved the nest to a warm crate, then fastened the shutter so it could open gently",
        "lesson": "good friends solve a problem without making a smaller neighbor pay for it",
        "ending": "the old lighthouse blinked across the water while the rescued gull chick peeped from its new nest",
        "question": "Why did the friends need to open the historic shutter?",
        "answer": "They needed to open it so the lighthouse could guide evening boats through the safe channel.",
    },
    {
        "premise": "A historic harbor fort kept a painted map beside its oldest window",
        "problem": "the heavy shutter covered the map just as the tide began to rise",
        "stake": "The crew could not read the route home before the sandbar disappeared",
        "clue": "the shutter hinges had been polished smooth by generations of careful hands",
        "plan": "They shared a lantern, pushed from both sides, and poured oil along the hinges",
        "twist": "a hidden spring released a second map showing a shorter route through calm water",
        "resolution": "They copied both routes and left the old map open for the next sailors",
        "lesson": "patient teamwork can uncover help that haste hides",
        "ending": "two maps fluttered in the fort window as the crew sailed home on the quiet tide",
        "question": "What did the hidden map reveal?",
        "answer": "It revealed a shorter route through calm water.",
    },
    {
        "premise": "The island museum guarded a historic captain's room with a bright red shutter",
        "problem": "the shutter blocked the moonlight needed to find a lost compass",
        "stake": "Without the compass, the ship could not steer away from the reef",
        "clue": "a silver line showed where moonlight had slipped beneath the shutter",
        "plan": "They followed the silver line, lifted the shutter together, and searched beneath the window",
        "twist": "the compass was tucked inside an old message tube, not under the bed",
        "resolution": "They opened the tube with a hairpin and used the compass to mark the reef on the chart",
        "lesson": "friends ask new questions when the first guess does not fit",
        "ending": "the compass needle steadied while the museum shutter gleamed in the moonlight",
        "question": "Where was the lost compass?",
        "answer": "The compass was inside an old message tube.",
    },
    {
        "premise": "A historic seaside school kept its lesson bell behind a green shutter",
        "problem": "salt had crusted the latch, so the bell could not be reached",
        "stake": "The children on the shore would not know when the storm drill began",
        "clue": "warm tea softened the salt on one side of the latch",
        "plan": "They passed cups along a line and warmed the latch while one friend held the lantern",
        "twist": "the bell rope had tied itself into a sailor's knot",
        "resolution": "They followed the rope's loops slowly and loosened the knot without cutting it",
        "lesson": "careful hands and shared attention can rescue what force would ruin",
        "ending": "the bell rang over the schoolyard, and every child practiced the safe route home",
        "question": "How did the friends loosen the latch?",
        "answer": "They warmed the salt-crusted latch with shared cups of tea.",
    },
    {
        "premise": "The oldest house on the island had a historic shutter carved with a moon",
        "problem": "a treasure clue was hidden behind it, but the shutter would not budge",
        "stake": "The crew might search the wrong cave before nightfall",
        "clue": "the carved moon pointed toward a small stone shaped like a shell",
        "plan": "They studied the carving, moved the shell-shaped stone, and used its wooden handle as a lever",
        "twist": "the clue led not to gold but to a shelf of bread for hungry travelers",
        "resolution": "They shared the bread and wrote the true message in the house log",
        "lesson": "a real treasure is often the help waiting for someone else",
        "ending": "crumbs dotted the old doorstep while the moon-carved shutter stood wide open",
        "question": "What treasure did the clue lead to?",
        "answer": "It led to bread left for hungry travelers.",
    },
]

OPENINGS = [
    "The sea shone like a blue coin beneath the morning sun",
    "A salty breeze tugged at every flag on the little ship",
    "Gulls cried above the deck as waves slapped a cheerful rhythm",
    "The tide rolled past the harbor with a deep, friendly hush",
    "Clouds sailed overhead while the crew polished the brass rail",
]

DIALOGUE = [
    ("“I can climb first,” said {hero}.", "“And I can hold the rope,” said {friend}."),
    ("“The shutter is stuck,” said {hero}.", "“Then we will study it together,” said {friend}."),
    ("“I found a clue!” cried {hero}.", "“Tell me what you see,” said {friend}."),
    ("“We must hurry,” said {hero}.", "“We must hurry carefully,” replied {friend}."),
]

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A pirate tale about a historic shutter, friendship, and problem solving."
    )
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--friend", choices=FRIEND_NAMES)
    parser.add_argument("--ship", choices=SHIPS)
    parser.add_argument("--island", choices=ISLANDS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    choices = [name for name in FRIEND_NAMES if name != hero]
    friend = args.friend or rng.choice(choices)
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    return StoryParams(
        hero=hero,
        friend=friend,
        ship=args.ship or rng.choice(SHIPS),
        island=args.island or rng.choice(ISLANDS),
        arc=rng.randrange(len(ARCS)),
        seed=args.seed,
    )


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        hero=Entity(params.hero, "hero"),
        friend=Entity(params.friend, "friend"),
        ship=Entity(params.ship, "ship"),
    )


def simulate(world: World) -> None:
    params = world.params
    arc = ARCS[params.arc]
    rng = random.Random(params.seed)
    hero = world.hero
    friend = world.friend

    hero.memes["curiosity"] = 1.0
    hero.memes["courage"] = 1.0
    friend.memes["patience"] = 1.0
    friend.memes["friendship"] = 1.0
    world.facts.update(
        {
            "island": params.island,
            "ship": params.ship,
            "problem": arc["problem"],
            "stake": arc["stake"],
            "clue": arc["clue"],
            "solution": arc["resolution"],
            "historic": True,
        }
    )

    world.say(
        f"{rng.choice(OPENINGS)}. {hero.name} and {friend.name} sailed "
        f"{params.ship} toward {params.island}, where {arc['premise'].lower()}."
    )
    world.say(f"They had come to check the old beacon before the night tide.")
    world.para()

    world.say(f"Then {arc['problem']}. {arc['stake']}.")
    first, second = rng.choice(DIALOGUE)
    world.say(first.format(hero=hero.name, friend=friend.name))
    world.say(second.format(hero=hero.name, friend=friend.name))
    world.say(
        f"The friends did not blame one another. They searched for a useful detail, "
        f"and noticed that {arc['clue']}."
    )
    hero.memes["problem_solving"] = 1.0
    friend.memes["problem_solving"] = 1.0
    world.para()

    world.say(f"Together, they made a careful plan: {arc['plan']}.")
    world.say(f"At first, the plan seemed finished. But then they discovered that {arc['twist']}.")
    world.say(
        f"{hero.name} asked, “What should we do now?” "
        f"{friend.name} answered, “We can protect the little creature and still save the light.”"
    )
    world.say(f"So they worked side by side. {arc['resolution']}.")
    world.facts["twist"] = arc["twist"]
    world.facts["resolved"] = True
    world.facts["friendship"] = True
    world.para()

    world.say(
        f"{hero.name} smiled. “Your idea helped us see the way.” "
        f"{friend.name} replied, “Your courage helped us begin.”"
    )
    world.say(f"{arc['lesson'].capitalize()}.")
    world.say(f"At sunset, {arc['ending']}.")
    world.facts["ending_image"] = arc["ending"]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]
    prompts = [
        f"Write a child-friendly pirate tale about {params.hero} and {params.friend} solving a problem with a historic shutter.",
        f"Tell a friendship story aboard {params.ship} near {params.island}, with a surprising shutter mystery.",
        f"Create a pirate adventure in which careful problem solving protects both a historic place and a small creature.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} and {params.friend} face?",
            answer=f"They faced the problem that {arc['problem']}, which mattered because {arc['stake'].lower()}.",
        ),
        QAItem(
            question="What clue helped them make a plan?",
            answer=f"They noticed that {arc['clue']}, and that clue helped them choose a careful solution.",
        ),
        QAItem(
            question="What surprising twist did they discover?",
            answer=f"They discovered that {arc['twist']}.",
        ),
        QAItem(
            question="How did friendship help solve the problem?",
            answer=f"They listened to each other, shared the work, and used both courage and patience to {arc['resolution'].lower()}.",
        ),
        QAItem(
            question="What lesson did the pirate friends learn?",
            answer=f"They learned that {arc['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a movable cover for a window or opening.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic describes something important from the past.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing a difficulty, studying clues, and choosing a useful way to fix it.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring bond in which people trust, help, and listen to one another.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.hero, world.friend, world.ship]:
        lines.append(
            f"  {entity.name:14} ({entity.kind:8}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/1.
valid(story) :-
    domain(pirate_tale),
    feature(friendship),
    feature(problem_solving),
    object(historic_shutter).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("domain", "pirate_tale"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "problem_solving"),
            asp.fact("object", "historic_shutter"),
        ]
    )


def asp_program(show: str = "#show valid/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    if asp.atoms(model, "valid") != [("story",)]:
        print("MISMATCH: ASP twin failed.")
        return 1

    for params in CURATED:
        sample = generate(params)
        if not sample.story or "shutter" not in sample.story.lower():
            print("MISMATCH: generated story check failed.")
            return 1
        if len(sample.story_qa) < 3:
            print("MISMATCH: QA check failed.")
            return 1

    print("OK: ASP twin and generated stories are consistent.")
    return 0


CURATED = [
    StoryParams(hero="Luna", friend="Tess", ship="the Starfish", island="Whistle Key", arc=0, seed=101),
    StoryParams(hero="Mara", friend="Bram", ship="the Blue Parrot", island="Old Lantern Isle", arc=1, seed=202),
    StoryParams(hero="Pip", friend="Kit", ship="the Merry Gull", island="Coral Crown", arc=4, seed=303),
]


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

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        print(asp.atoms(model, "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(args.n, 1) * 20):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

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
