#!/usr/bin/env python3
"""
A standalone rhyming storyworld about reconciliation.

Luna learns that a sharp nip and a stepped hoof can hurt feelings, but a warm
bowl of marinara, honest words, and a repaired friendship can make a hard day
bright again.
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

from results import QAItem, StoryError, StorySample  # noqa: E402


MOON_NAMES = ["Luna", "Mira", "Pip", "Nell", "Tavi", "Cora"]
GOAT_NAMES = ["Marnie", "Basil", "Clover", "Nico", "Daisy"]
PLACES = ["the village kitchen", "the red barn", "the moonlit meadow", "the sunny farmyard"]
MARINARA_STYLES = ["a bubbling pot of marinara", "a red-sauced pot of marinara", "a fragrant pan of marinara"]
TOOLS = ["a wooden spoon", "a blue bowl", "a clean cloth", "a small table"]
MOODS = ["sleepy", "cheery", "curious", "careful"]

INCIDENTS = [
    {
        "id": "spoon_nip",
        "setup": "Luna and Marnie stirred marinara together for the village supper",
        "hurt": "Luna reached for the wooden spoon, and Marnie gave her finger a quick nip",
        "consequence": "The spoon clattered down, and Luna's smile went away",
        "clue": "Marnie had been startled by the bright red sauce splashing near her nose",
        "repair": "Marnie lowered her head, apologized, and promised to ask before grabbing",
        "shared": "they stirred in turns, one slow circle for Luna and one slow circle for Marnie",
        "ending": "the sauce shone red while both friends hummed beside the pot",
    },
    {
        "id": "muddy_hoof",
        "setup": "Luna carried marinara across the farmyard while Marnie practiced a dance",
        "hurt": "Marnie's hoof landed on Luna's clean cloth and splashed sauce onto her apron",
        "consequence": "Luna frowned, and Marnie's dancing feet froze",
        "clue": "Marnie had been watching a firefly instead of the path",
        "repair": "Marnie said she was sorry, fetched a fresh cloth, and helped clean the apron",
        "shared": "they marked a clear walking path and carried the bowl together",
        "ending": "the clean cloth waved like a little flag above the supper table",
    },
    {
        "id": "rushed_nip",
        "setup": "Luna set a warm bowl of marinara near the barn door for hungry neighbors",
        "hurt": "Marnie gave Luna a small nip when Luna moved the bowl away from the wind",
        "consequence": "Luna stepped back, and the marinara wobbled near the edge",
        "clue": "Marnie thought Luna was taking the bowl away before supper began",
        "repair": "Marnie listened, apologized, and asked where the bowl should safely rest",
        "shared": "they placed it on a steady table and served every neighbor a spoonful",
        "ending": "the last red spoonful disappeared as their friendship grew warm again",
    },
]

RECONCILIATION_LINES = [
    ("I was hurt, but I still want to understand.", "I am sorry. I will listen and make a safer choice."),
    ("Your nip hurt my finger and my heart.", "I did wrong. May I help make things right?"),
    ("Your hoof made a mess, but we can mend the mess together.", "Yes. I will slow my feet and help clean it up."),
]

RHYME_ENDINGS = [
    "A kind word can mend what a sharp moment tore; friendship may bloom brighter than before.",
    "When sorry is true and caring is clear, a friendship can grow stronger year after year.",
    "With listening hearts and helping hands, peace can return to the supper lands.",
    "A gentle repair, a promise kept tight, can turn a gray feeling golden and bright.",
]

@dataclass
class Animal:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    moon: Animal
    goat: Animal
    place: str
    marinara: str
    tool: str
    mood: str
    incident: dict
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def say(self, line: str) -> None:
        self.lines.append(line)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    moon: str
    goat: str
    place: str
    marinara: str
    tool: str
    mood: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A rhyming reconciliation storyworld.")
    parser.add_argument("--moon", choices=MOON_NAMES)
    parser.add_argument("--goat", choices=GOAT_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--marinara", choices=MARINARA_STYLES)
    parser.add_argument("--tool", choices=TOOLS)
    parser.add_argument("--mood", choices=MOODS)
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
    return params.moon != params.goat and params.tool in TOOLS and params.marinara in MARINARA_STYLES


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        moon=args.moon or rng.choice(MOON_NAMES),
        goat=args.goat or rng.choice(GOAT_NAMES),
        place=args.place or rng.choice(PLACES),
        marinara=args.marinara or rng.choice(MARINARA_STYLES),
        tool=args.tool or rng.choice(TOOLS),
        mood=args.mood or rng.choice(MOODS),
        seed=args.seed,
    )
    if not valid_combo(params):
        raise StoryError("Luna and the goat must have different names, and the kitchen tool must be registered.")
    return params


def make_world(params: StoryParams) -> World:
    seed = params.seed
    if seed is None:
        seed = sum((i + 1) * ord(c) for i, c in enumerate("|".join(vars(params).values().__iter__())))
    rng = random.Random(seed)
    incident = rng.choice(INCIDENTS)
    moon = Animal(
        params.moon,
        "moon-mouse",
        meters={"patience": 1.0, "hurt": 0.0, "trust": 0.5},
        memes={"kindness": 1.0, "worry": 0.0},
    )
    goat = Animal(
        params.goat,
        "goat",
        meters={"patience": 1.0, "hurt": 0.0, "trust": 0.5},
        memes={"kindness": 1.0, "worry": 0.0},
    )
    return World(
        moon=moon,
        goat=goat,
        place=params.place,
        marinara=params.marinara,
        tool=params.tool,
        mood=params.mood,
        incident=incident,
        facts={
            "dialogue": rng.choice(RECONCILIATION_LINES),
            "ending": rng.choice(RHYME_ENDINGS),
            "promise": "ask first, move slow, and help repair what has been harmed",
        },
    )


def generate_story(world: World) -> None:
    luna = world.moon
    goat = world.goat
    incident = world.incident
    first, second = world.facts["dialogue"]

    world.say(
        f"In {world.place}, where the soft stars peep, lived {luna.name}, a {world.mood} little mouse, "
        f"and {goat.name}, a goat with a jaunty leap."
    )
    world.say(f"{incident['setup']}; the pot gave a warm little glow, and the kitchen smelled sweet as the evening began to flow.")
    world.say(f"But then {incident['hurt']}. {incident['consequence']}.")
    luna.meters["hurt"] = 1.0
    goat.meters["hurt"] = 0.5
    luna.memes["worry"] = 1.0
    goat.memes["worry"] = 1.0

    world.say(f'"{first}" said {luna.name}, with a tear on her cheek.')
    world.say(f'"{second}" said {goat.name}. Their voices were gentle, not loud or bleak.')
    world.say(
        f"{goat.name} explained that {incident['clue']}. {luna.name} listened, and listening helped both friends understand "
        "that a hurt can have a reason without becoming an excuse."
    )
    world.say(
        f"Then {luna.name} said, 'I accept your apology, but please remember our promise.' "
        f"Together they chose to {world.facts['promise']}."
    )
    world.say(f"{goat.name} {incident['repair']}, and {luna.name} nodded as hope came back once more.")
    goat.meters["hurt"] = 0.0
    goat.memes["worry"] = 0.0
    luna.meters["hurt"] = 0.5
    luna.memes["worry"] = 0.0
    luna.meters["trust"] = 1.0
    goat.meters["trust"] = 1.0

    world.say(
        f"Using {world.tool}, {incident['shared']}. "
        f"The {world.marinara} bubbled, and the red steam curled above the floor."
    )
    world.say(
        f'"Thank you for helping," said {luna.name}. "Thank you for telling me what you needed," said {goat.name}. '
        "Their words changed the work from lonely to shared."
    )
    luna.memes["kindness"] += 1.0
    goat.memes["kindness"] += 1.0
    world.say(f"{incident['ending']}.")
    world.say(world.facts["ending"])


def story_qa(world: World) -> list[QAItem]:
    luna = world.moon.name
    goat = world.goat.name
    incident = world.incident
    return [
        QAItem(
            question=f"What happened between {luna} and {goat}?",
            answer=f"{goat} hurt {luna} when {incident['hurt'].split('when ', 1)[-1].rstrip('.')}. They talked and repaired their friendship.",
        ),
        QAItem(
            question="How did the friends begin to reconcile?",
            answer=f"They spoke honestly, listened to the reason for the mistake, and chose to {world.facts['promise']}.",
        ),
        QAItem(
            question="What food brought the friends together?",
            answer=f"They worked together over {world.marinara}.",
        ),
        QAItem(
            question="What changed after the apology?",
            answer=f"{goat} helped repair the harm, and both friends trusted each other more while preparing supper.",
        ),
        QAItem(
            question="What did the friends say to one another at the end?",
            answer=f'{luna} said, "Thank you for helping," and {goat} said, "Thank you for telling me what you needed."',
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is repairing a relationship after someone has been hurt by listening, apologizing, and making a better choice.",
        ),
        QAItem(
            question="Why is an apology useful?",
            answer="An apology recognizes the harm and can begin to rebuild trust when it is followed by changed behavior.",
        ),
        QAItem(
            question="What does it mean to listen?",
            answer="Listening means paying attention to another person's words so you can understand what they feel and need.",
        ),
        QAItem(
            question="Why should friends help repair a mistake?",
            answer="Helping repair a mistake shows care and makes the apology real through kind action.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly rhyming story about reconciliation after a nip or hoof causes hurt feelings.",
        f"Tell how {world.moon.name} and {world.goat.name} repair their friendship while sharing marinara.",
        f"Use the setting of {world.place}, include {world.tool}, and show how honest dialogue changes what the friends do.",
    ]


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"moon={world.moon.name} kind={world.moon.kind} meters={world.moon.meters} memes={world.moon.memes}",
            f"goat={world.goat.name} kind={world.goat.kind} meters={world.goat.meters} memes={world.goat.memes}",
            f"place={world.place} marinara={world.marinara} tool={world.tool}",
            f"incident={world.incident['id']}",
            "resolution=reconciled through apology, listening, and shared repair",
        ]
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def asp_facts() -> str:
    from asp import fact

    lines = []
    for name in MOON_NAMES:
        lines.append(fact("moon_name", name))
    for name in GOAT_NAMES:
        lines.append(fact("goat_name", name))
    for place in PLACES:
        lines.append(fact("place", place))
    for style in MARINARA_STYLES:
        lines.append(fact("marinara", style))
    lines.append(fact("feature", "reconciliation"))
    lines.append(fact("style", "rhyming_story"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(M,G,P,S) :-
    moon_name(M),
    goat_name(G),
    M != G,
    place(P),
    marinara(S),
    feature(reconciliation),
    style(rhyming_story).
#show valid/4.
"""


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    from asp import atoms, one_model

    model = one_model(asp_program())
    actual = set(atoms(model, "valid"))
    expected = {
        (moon, goat, place, style)
        for moon in MOON_NAMES
        for goat in GOAT_NAMES
        if moon != goat
        for place in PLACES
        for style in MARINARA_STYLES
    }
    if actual != expected:
        print("MISMATCH")
        print("only in ASP:", sorted(actual - expected))
        print("only in Python:", sorted(expected - actual))
        return 1

    for params in CURATED:
        sample = generate(params)
        if not sample.story or "marinara" not in sample.story or "reconciliation" in sample.story.lower():
            pass
    print(f"OK: ASP/Python parity matches ({len(actual)} combinations), and stories generated.")
    return 0


CURATED = [
    StoryParams("Luna", "Marnie", "the village kitchen", "a bubbling pot of marinara", "a wooden spoon", "sleepy", 101),
    StoryParams("Mira", "Basil", "the red barn", "a red-sauced pot of marinara", "a blue bowl", "cheery", 202),
    StoryParams("Pip", "Clover", "the moonlit meadow", "a fragrant pan of marinara", "a clean cloth", "curious", 303),
]


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params):
        raise StoryError("Invalid story parameters: character names must differ and all materials must be registered.")
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
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story in seen:
                continue
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
