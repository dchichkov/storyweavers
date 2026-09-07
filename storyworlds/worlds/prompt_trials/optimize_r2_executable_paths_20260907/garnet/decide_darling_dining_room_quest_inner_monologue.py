#!/usr/bin/env python3
"""
A heartwarming dining-room quest about deciding what to do with a darling gift.
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
while not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    parent = os.path.dirname(_storyworlds_dir)
    if parent == _storyworlds_dir:
        break
    _storyworlds_dir = parent
sys.path.insert(0, _storyworlds_dir)

from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Item
    darling: Item
    helper: Item
    room: str
    path: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    darling_name: str
    room: str
    path: str
    seed: Optional[int] = None


NAMES = ["Mara", "Theo", "Lina", "Owen", "Pia", "Sam"]
DARLINGS = ["Darling", "Sweetheart", "Little Star", "Honey"]
ROOMS = ["the dining room", "the sunny dining room", "the quiet dining room"]
PATHS = ["candle", "napkin", "both", "wait"]

PATH_REGISTRY = {
    "candle": {
        "problem": "the birthday candle had vanished before the cake could be carried in",
        "clue": "a warm waxy smell beneath the sideboard",
        "actions": ["look beneath the sideboard", "follow the wax spot", "light the rescued candle"],
        "change": "the candle was found in a fallen napkin ring and returned to the cake",
        "ending": "the cake glowed with one small flame as everyone leaned close to make a wish",
    },
    "napkin": {
        "problem": "the tablecloth was sliding toward a bowl of berry punch",
        "clue": "the darling embroidered napkin had a firm wooden ring",
        "actions": ["ask for the napkin ring", "place it over the tablecloth corner", "steady the punch bowl"],
        "change": "the napkin ring held the cloth safely in place",
        "ending": "the punch stayed still while the darling napkin rested neatly beside each plate",
    },
    "both": {
        "problem": "the missing candle and sliding tablecloth threatened the family supper together",
        "clue": "one trail led under the sideboard and another led to the loose cloth",
        "actions": ["search under the sideboard", "use the napkin ring as a weight", "carry the candle to the cake"],
        "change": "the ring steadied the cloth and the candle returned to the cake",
        "ending": "the table shone calmly, with the cake lit and every berry safely in its bowl",
    },
    "wait": {
        "problem": "the family was rushing to begin, but the darling gift had not yet been found",
        "clue": "a quiet pause would let the room reveal its smallest sounds",
        "actions": ["ask everyone to pause", "listen for a tiny clink", "open the drawer beneath the sideboard"],
        "change": "waiting revealed the gift inside the drawer before anyone overturned the room",
        "ending": "the darling gift appeared just in time, warm in careful hands at the welcoming table",
    },
}


ASP_RULES = r"""
#show quest/1.
#show decided/1.
#show safe/1.

quest(H) :- seeks_gift(H).
decided(H) :- chooses_path(H).
safe(H) :- completes_quest(H).
"""


def asp_facts(path: str = "candle") -> str:
    import asp

    if path not in PATH_REGISTRY:
        raise StoryError(f"unknown quest path: {path}")
    return "\n".join(
        [
            asp.fact("seeks_gift", "hero"),
            asp.fact("chooses_path", "hero"),
            asp.fact("completes_quest", "hero"),
            asp.fact("path", "hero", path),
        ]
    )


def asp_program(path: str = "candle", show: str = "") -> str:
    return f"{asp_facts(path)}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    expected = {
        ("quest", ("hero",)),
        ("decided", ("hero",)),
        ("safe", ("hero",)),
    }
    for path in PATHS:
        model = asp.one_model(
            asp_program(
                path,
                "#show quest/1.\n#show decided/1.\n#show safe/1.",
            )
        )
        actual = set()
        for atom in model:
            if atom.name in {"quest", "decided", "safe"}:
                actual.add(
                    (
                        atom.name,
                        tuple(
                            x.number
                            if x.type == x.type.Number
                            else x.string
                            if x.type == x.type.String
                            else x.name
                            for x in atom.arguments
                        ),
                    )
                )
        if actual != expected:
            print(f"MISMATCH for path {path}: ASP={sorted(actual)} PY={sorted(expected)}")
            return 1
    for path in PATHS:
        params = StoryParams("Mara", "Darling", "the dining room", path, 17)
        sample = generate(params)
        if not sample.story or "Darling" not in sample.story:
            print(f"MISMATCH: ungrounded story for path {path}")
            return 1
        if "{" in sample.story or "}" in sample.story:
            print(f"MISMATCH: unresolved template for path {path}")
            return 1
        if sample.story.count('"') < 4 or not all(
            any(f'{verb} {speaker}' in sample.story for verb in ("said", "asked", "answered"))
            for speaker in ("Mara", "Grandma")
        ):
            print(f"MISMATCH: missing spoken exchange for path {path}")
            return 1
    print("OK: Python and ASP quest parity verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming dining-room decision quest."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--darling-name", choices=DARLINGS)
    parser.add_argument("--room", choices=ROOMS)
    parser.add_argument("--path", choices=PATHS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    path = args.path or rng.choice(PATHS)
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        darling_name=args.darling_name or rng.choice(DARLINGS),
        room=args.room or rng.choice(ROOMS),
        path=path,
    )


def build_world(params: StoryParams) -> World:
    if params.path not in PATH_REGISTRY:
        raise StoryError(f"unsupported dining-room quest path: {params.path}")
    hero = Item(
        "hero",
        params.name,
        f"{params.name}, a thoughtful child",
        "character",
        memes={"courage": 1.0, "care": 1.0},
    )
    darling = Item(
        "darling",
        params.darling_name,
        f"the darling {params.darling_name.lower()} gift",
        "gift",
        owner=params.name,
        meters={"warmth": 1.0},
        memes={"love": 1.0},
    )
    helper = Item(
        "helper",
        "Grandma",
        "Grandma",
        "character",
        memes={"patience": 1.0, "trust": 1.0},
    )
    return World(
        hero=hero,
        darling=darling,
        helper=helper,
        room=params.room,
        path=params.path,
        seed=params.seed if params.seed is not None else 1,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _candle_story(world: World, rng: random.Random) -> str:
    h, d, room = world.hero.label, world.darling.label, world.room
    scent = _choice(rng, ["a warm honey smell", "a faint vanilla smell", "a little beeswax scent"])
    question = _choice(
        rng,
        [
            "Should I search first, or should I tell everyone to wait?",
            "Could the candle be hiding somewhere close?",
            "What would a careful helper do now?",
        ],
    )
    world.facts.update(
        problem=PATH_REGISTRY["candle"]["problem"],
        clue=PATH_REGISTRY["candle"]["clue"],
        method="Mara followed the warm waxy smell beneath the sideboard and found the candle in a fallen napkin ring",
        resolution=f"{h} returned the candle to the cake and lit it beside {d}",
        ending="the cake glowed with one small flame as everyone leaned close to make a wish",
    )
    return " ".join(
        [
            f"In {room}, {h} carried a cake toward the waiting table, but the birthday candle was gone.",
            f"A suspenseful little silence filled the room. {h} noticed {scent} beneath the sideboard and thought, \"{question}\"",
            f'"Do you want help deciding, darling?" asked Grandma. "I do," said {h}, "but I want to look gently."',
            f"{h} knelt, followed the waxy trail, and found the candle tucked inside a fallen napkin ring.",
            f'"There you are, {d}," whispered {h}. Grandma smiled. "You decided with care, and care helped you notice the clue."',
            f"{h} returned the candle to the cake and lit it. The family waited until the tiny flame stood steady.",
            f"At last, {world.facts['ending']}.",
        ]
    )


def _napkin_story(world: World, rng: random.Random) -> str:
    h, d, room = world.hero.label, world.darling.label, world.room
    sound = _choice(rng, ["a soft scrape", "a tiny skitter", "a whisper of cloth"])
    question = _choice(
        rng,
        [
            "Should I grab the bowl or find something to hold the cloth?",
            "What can keep everyone safe without making a fuss?",
            "Could the darling ring help?",
        ],
    )
    world.facts.update(
        problem=PATH_REGISTRY["napkin"]["problem"],
        clue=PATH_REGISTRY["napkin"]["clue"],
        method=f"{h} used the firm wooden ring from {d} to hold the tablecloth corner",
        resolution=f"{h} placed the ring over the cloth and steadied the punch bowl",
        ending="the punch stayed still while the darling napkin rested neatly beside each plate",
    )
    return " ".join(
        [
            f"The dining room was ready for supper when {h} heard {sound}. The tablecloth was sliding toward a bowl of berry punch.",
            f"{h} watched the red punch tremble and thought, \"{question}\" The suspense felt as wiggly as the cloth.",
            f'"Darling, may I borrow your ring?" asked Grandma. "Yes," said {h}. "It can help everyone."',
            f"{h} took the wooden ring from {d}, placed it over the cloth corner, and gently steadied the bowl.",
            f"The cloth stopped. The punch settled. Grandma touched {h}'s shoulder and said, \"Your decision made room for calm.\"",
            f"{h} folded the napkin and returned the ring. {world.facts['ending']}.",
        ]
    )


def _both_story(world: World, rng: random.Random) -> str:
    h, d, room = world.hero.label, world.darling.label, world.room
    question = _choice(
        rng,
        [
            "Which danger should I handle first, and what can help with both?",
            "Can one careful plan protect the whole table?",
            "Should I hurry, or should I notice what belongs where?",
        ],
    )
    world.facts.update(
        problem=PATH_REGISTRY["both"]["problem"],
        clue=PATH_REGISTRY["both"]["clue"],
        method=f"{h} used {d}'s napkin ring as a weight, then followed the wax trail to the candle",
        resolution=f"{h} steadied the cloth with the ring and returned the candle to the cake",
        ending="the table shone calmly, with the cake lit and every berry safely in its bowl",
    )
    return " ".join(
        [
            f"In {room}, two troubles arrived at once: the candle was missing, and the tablecloth crept toward the punch.",
            f"{h} saw the cloth twitch and the empty cake waiting. In a worried inner monologue, {h} thought, \"{question}\"",
            f'"Tell me what you see," said Grandma. "A trail under the sideboard and a loose corner," said {h}.',
            f"{h} placed {d}'s napkin ring over the loose corner first, then searched beneath the sideboard.",
            f"The ring held the cloth. A wax spot led to the missing candle, hiding in a fallen napkin ring nearby.",
            f'"I decided not to rush," said {h}. Grandma answered, "That gave you time to solve both problems."',
            f"{h} carried the candle to the cake and checked every plate. {world.facts['ending']}.",
        ]
    )


def _wait_story(world: World, rng: random.Random) -> str:
    h, d, room = world.hero.label, world.darling.label, world.room
    sound = _choice(rng, ["a delicate clink", "a shy wooden tap", "a tiny ring against a drawer"])
    world.facts.update(
        problem=PATH_REGISTRY["wait"]["problem"],
        clue=PATH_REGISTRY["wait"]["clue"],
        method=f"{h} asked everyone to pause, heard {sound}, and opened the drawer beneath the sideboard",
        resolution=f"{h} found {d} in the drawer because waiting made its small sound audible",
        ending="the darling gift appeared just in time, warm in careful hands at the welcoming table",
    )
    return " ".join(
        [
            f"The family stood around the dining room, ready to begin, but {d} was nowhere to be seen.",
            f"Everyone began reaching beneath chairs. The suspense grew until {h} thought, \"If we all hurry, we may miss the answer.\"",
            f'"Please pause," said {h}. "Can we trust the quiet?" asked Grandma. "Yes," said {h}.',
            f"The room became still. Then {h} heard {sound} beneath the sideboard.",
            f"{h} opened the drawer and found {d} tucked safely inside. The gift had not been lost; it had simply been waiting too.",
            f'"You decided to listen before searching," said Grandma. {h} held {d} close and smiled.',
            f"{world.facts['ending']}.",
        ]
    )


BUILDERS = {
    "candle": _candle_story,
    "napkin": _napkin_story,
    "both": _both_story,
    "wait": _wait_story,
}


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0xD4A11)
    return BUILDERS[world.path](world, rng)


def story_qa(world: World) -> list[QAItem]:
    h, d = world.hero.label, world.darling.label
    return [
        QAItem(
            question=f"What problem did {h} face in the dining room?",
            answer=f"{h} faced {world.facts['problem']}.",
        ),
        QAItem(
            question=f"What clue helped {h} decide what to do?",
            answer=f"The important clue was {world.facts['clue']}.",
        ),
        QAItem(
            question=f"How did {h} complete the quest involving {d}?",
            answer=f"{world.facts['resolution']}.",
        ),
        QAItem(
            question="How did the suspense change before the ending?",
            answer=f"The suspense eased because {world.facts['method']}, which made the dining room safe and welcoming.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why is it useful to decide before acting?",
            answer="Deciding after noticing the facts can prevent a rushed mistake and help someone choose a safer action.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next while a problem remains unresolved.",
        ),
        QAItem(
            question="Why can a napkin ring help on a table?",
            answer="A firm napkin ring can add a little weight and keep a cloth corner from sliding.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a heartwarming quest in {world.room} about deciding what to do with a darling gift.",
        "Use inner monologue and gentle suspense while a child solves a small dining-room problem.",
        "End with a warm family image that proves the careful decision mattered.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.hero, world.darling, world.helper]:
        lines.append(
            f"  {entity.id:8} {entity.kind:9} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  room={world.room!r} path={world.path!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    sections = ["== Generation prompts =="]
    sections.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    sections.append("")
    sections.append("== Story QA ==")
    for item in sample.story_qa:
        sections.extend([f"Q: {item.question}", f"A: {item.answer}"])
    sections.append("")
    sections.append("== World QA ==")
    for item in sample.world_qa:
        sections.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(sections)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    world.facts["story"] = story
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts_text(path: str = "candle") -> str:
    return asp_facts(path)


def asp_valid(path: str = "candle") -> bool:
    return path in PATH_REGISTRY


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                args.path or "candle",
                "#show quest/1.\n#show decided/1.\n#show safe/1.",
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        path = args.path or "candle"
        model = asp.one_model(
            asp_program(path, "#show quest/1.\n#show decided/1.\n#show safe/1.")
        )
        print(" ".join(str(atom) for atom in model))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Mara", "Darling", "the dining room", "candle", base_seed),
            StoryParams("Theo", "Sweetheart", "the sunny dining room", "napkin", base_seed + 1),
            StoryParams("Lina", "Little Star", "the quiet dining room", "both", base_seed + 2),
            StoryParams("Owen", "Honey", "the dining room", "wait", base_seed + 3),
        ]
        samples = [generate(params) for params in curated]
    else:
        for index in range(args.n):
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
        header = ""
        if args.all:
            header = f"### {sample.params.name} in {sample.params.room}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
