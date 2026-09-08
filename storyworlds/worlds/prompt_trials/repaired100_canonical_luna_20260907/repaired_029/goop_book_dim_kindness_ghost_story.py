#!/usr/bin/env python3
"""
A small ghost story about Luna, a dim book, stubborn goop, and kindness.
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

_worlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_worlds_dir, "results.py")):
    _worlds_dir = os.path.dirname(_worlds_dir)
sys.path.insert(0, _worlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def add_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.events.append(text)

    def render(self) -> str:
        return "\n\n".join(self.events)


@dataclass(frozen=True)
class Setting:
    id: str
    name: str
    detail: str


@dataclass(frozen=True)
class Problem:
    id: str
    phrase: str
    danger: str
    clue: str
    kindness: str


@dataclass(frozen=True)
class Tool:
    id: str
    phrase: str
    action: str


SETTINGS = {
    "attic_library": Setting(
        "attic_library",
        "the old attic library",
        "Dusty shelves leaned beneath the roof, and moonlight slipped through a round window.",
    ),
    "rainy_archive": Setting(
        "rainy_archive",
        "the rainy archive",
        "Rain tapped the long windows while quiet cabinets held forgotten stories.",
    ),
    "lantern_room": Setting(
        "lantern_room",
        "the lantern room",
        "Paper lanterns hung from the rafters, though none had been lit for years.",
    ),
}

PROBLEMS = {
    "stubborn_goop": Problem(
        "stubborn_goop",
        "a puddle of green goop had sealed the book-dim shut",
        "Pulling the cover could tear the ghost's only picture of home.",
        "The goop loosened whenever someone spoke gently about being lonely.",
        "listening before trying to fix the mess",
    ),
    "cold_goop": Problem(
        "cold_goop",
        "cold blue goop had glued the book-dim to a stone table",
        "Scraping too hard could crack the table and scatter the book's dim light.",
        "A warm handprint appeared wherever someone offered patient help.",
        "giving time instead of forcing an answer",
    ),
    "whisper_goop": Problem(
        "whisper_goop",
        "whispering gray goop covered the book-dim's silver letters",
        "Wiping quickly could erase the ghost's name from every page.",
        "The letters brightened when a true kind memory was shared.",
        "remembering another person's feelings",
    ),
}

TOOLS = {
    "soft_cloth": Tool(
        "soft_cloth",
        "a soft cotton cloth",
        "dabbed the goop from the edges in tiny circles",
    ),
    "warm_mitten": Tool(
        "warm_mitten",
        "a wool mitten warmed by Luna's hand",
        "held it against the goop until the sticky surface softened",
    ),
    "feather_brush": Tool(
        "feather_brush",
        "a quiet feather brush",
        "brushed the goop away from the silver letters one careful stroke at a time",
    ),
}

NAMES = ["Luna", "Mara", "Nell", "Iris", "Toby"]
GHOST_NAMES = ["Echo", "Wisp", "Moth", "Pale", "Whisper"]
MOODS = ["brave", "curious", "gentle", "patient", "thoughtful"]


@dataclass(frozen=True)
class StoryParams:
    setting: str
    problem: str
    tool: str
    name: str
    ghost: str
    mood: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (setting, problem, tool)
        for setting in SETTINGS
        for problem in PROBLEMS
        for tool in TOOLS
    ]


def _choose(mapping: dict, value: str):
    if value not in mapping:
        raise StoryError(f"Unknown choice {value!r}; choose one of {sorted(mapping)}.")
    return mapping[value]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    tool = args.tool or rng.choice(list(TOOLS))
    _choose(SETTINGS, setting)
    _choose(PROBLEMS, problem)
    _choose(TOOLS, tool)
    return StoryParams(
        setting=setting,
        problem=problem,
        tool=tool,
        name=args.name or rng.choice(NAMES),
        ghost=args.ghost or rng.choice(GHOST_NAMES),
        mood=args.mood or rng.choice(MOODS),
        seed=args.seed,
    )


def tell(params: StoryParams) -> World:
    setting = _choose(SETTINGS, params.setting)
    problem = _choose(PROBLEMS, params.problem)
    tool = _choose(TOOLS, params.tool)

    world = World()
    luna = world.add(Entity(params.name, "character", params.name, location=setting.id))
    ghost = world.add(Entity(params.ghost, "ghost", f"the ghost {params.ghost}", location=setting.id))
    book = world.add(Entity("book_dim", "book", "the book-dim", location=setting.id))
    goop = world.add(Entity("goop", "obstacle", "the goop", location=setting.id))

    luna.add_meme("kindness", 0.0)
    ghost.add_meme("loneliness", 1.0)
    book.add_meter("dim", 1.0)
    goop.add_meter("stuck", 1.0)

    world.say(
        f"{params.name} was a {params.mood} child who liked places where old stories slept."
    )
    world.say(f"One rainy evening, {params.name} entered {setting.name}. {setting.detail}")
    world.say(
        f"On a low table lay {book.label}, a strange book whose pages gave off only a dim gray glow."
    )
    world.say(
        f"Green {problem.phrase.split('green ', 1)[-1].split('cold ', 1)[-1].split('whispering ', 1)[-1]} "
        f"had spread over it, and a small ghost trembled beside the table."
    )
    world.say(f'"Please do not leave," whispered {params.ghost}. "The book remembers my home."')
    world.say(f'"I will stay," said {params.name}. "But tell me what happened."')
    world.say(
        f"The ghost explained that the goop had sealed the book-dim after nobody listened to its story. "
        f"{problem.danger}"
    )
    world.say(
        f"{params.name} did not grab the cover. Instead, {params.name} practiced {problem.kindness}."
    )
    luna.add_meme("kindness", 1.0)
    luna.add_meter("observed", 1.0)

    world.say(
        f'"What do you miss most?" asked {params.name}. '
        f'"A warm window and someone who says my name," answered {params.ghost}.'
    )
    world.say(
        f"That answer revealed the clue: {problem.clue}"
    )
    world.say(
        f'"Then we can begin slowly," said {params.name}. '
        f'"Slowly is still moving."'
    )
    world.say(
        f"{params.name} used {tool.phrase} and {tool.action}. "
        f"The goop curled away without a sound."
    )
    goop.add_meter("stuck", -1.0)
    book.add_meter("dim", -1.0)
    ghost.add_meme("loneliness", -1.0)
    book.add_meter("open", 1.0)

    world.say(
        f"When the last sticky patch lifted, the book-dim opened to a picture of a bright window."
    )
    world.say(
        f"{params.ghost} touched the page, and the ghostly room filled with a soft amber light."
    )
    world.say(
        f'"You heard me," said {params.ghost}. "That was the kindness I needed."'
    )
    world.say(
        f'"Everyone deserves a listener," {params.name} replied.'
    )
    world.say(
        f"The book was no longer dim. Its warm pages showed the way home, and {params.ghost} smiled before fading into the light."
    )
    world.say(
        f"After that night, {params.name} left a chair beside the table, because kindness can keep even a quiet ghost from feeling alone."
    )

    world.facts.update(
        setting=setting,
        problem=problem,
        tool=tool,
        hero=luna,
        ghost=ghost,
        book=book,
        goop=goop,
        clue=problem.clue,
        resolution="the book-dim opened and the ghost found a warm path home",
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    facts = world.facts
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a gentle ghost story in {facts['setting'].name} about {params.name}, goop, and a book-dim.",
            f"Show how {params.name} uses kindness to help {params.ghost} without forcing the stuck book.",
            "End with an image proving that listening changed the haunted room.",
        ],
        story_qa=[
            QAItem(
                f"What had happened to the book-dim?",
                f"{facts['problem'].phrase.capitalize()} had sealed the book-dim shut."
            ),
            QAItem(
                f"Why did {params.ghost} need help?",
                f"{params.ghost} was lonely and wanted someone to listen to the story of home."
            ),
            QAItem(
                f"What clue helped {params.name} choose a safe solution?",
                f"{params.name} noticed that {facts['clue']}."
            ),
            QAItem(
                f"How did {params.name} help?",
                f"{params.name} listened kindly, then used {facts['tool'].phrase} to {facts['tool'].action}."
            ),
            QAItem(
                "What changed at the end?",
                f"The book-dim opened, its pages grew warm, and the ghost found a path home."
            ),
        ],
        world_qa=[
            QAItem(
                "What is a ghost story?",
                "A ghost story is a tale about a spirit or mysterious presence, often with a feeling of wonder or suspense."
            ),
            QAItem(
                "What is kindness?",
                "Kindness means noticing another person's needs and responding with care."
            ),
            QAItem(
                "Why can listening help someone who feels lonely?",
                "Listening shows that the person's feelings matter and that they do not have to carry them alone."
            ),
        ],
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.kind:9}) "
            f"meters={entity.meters} memes={entity.memes} location={entity.location}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S, P, T) :- setting(S), problem(P), tool(T).
opened(book_dim) :- compatible(_, _, _), kind(book_dim, book).
kind(book_dim, book).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for setting in SETTINGS:
        lines.append(asp.fact("setting", setting))
    for problem in PROBLEMS:
        lines.append(asp.fact("problem", problem))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool))
    return "\n".join(lines)


def asp_program(show: str = "#show compatible/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    expected = set(valid_combos())
    actual = set(asp_valid_combos())
    if expected != actual:
        print("ASP/Python mismatch.")
        print("Only Python:", sorted(expected - actual))
        print("Only ASP:", sorted(actual - expected))
        return 1
    for params in [
        StoryParams("attic_library", "stubborn_goop", "soft_cloth", "Luna", "Echo", "gentle", 1),
        StoryParams("rainy_archive", "cold_goop", "warm_mitten", "Mara", "Wisp", "patient", 2),
    ]:
        sample = generate(params)
        if "goop" not in sample.story or "book-dim" not in sample.story:
            print("Generated story omitted required domain words.")
            return 1
        if not sample.story_qa:
            print("Generated story omitted QA.")
            return 1
    print(f"OK: ASP matches Python ({len(actual)} combinations); generated stories passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle ghost story about goop, a book-dim, and kindness."
    )
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--problem", choices=sorted(PROBLEMS))
    parser.add_argument("--tool", choices=sorted(TOOLS))
    parser.add_argument("--name")
    parser.add_argument("--ghost")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    if args.all:
        params_list = [
            StoryParams("attic_library", "stubborn_goop", "soft_cloth", "Luna", "Echo", "gentle", args.seed),
            StoryParams("rainy_archive", "cold_goop", "warm_mitten", "Mara", "Wisp", "patient", args.seed),
            StoryParams("lantern_room", "whisper_goop", "feather_brush", "Nell", "Moth", "thoughtful", args.seed),
        ]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        params_list = []
        for index in range(max(0, args.n)):
            rng = random.Random(base + index)
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = base + index
            params_list.append(resolve_params(local_args, rng))

    samples = [generate(params) for params in params_list]

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], ensure_ascii=False, indent=2))
        return

    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {index + 1}")
        print(sample.story)
        if args.trace:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
