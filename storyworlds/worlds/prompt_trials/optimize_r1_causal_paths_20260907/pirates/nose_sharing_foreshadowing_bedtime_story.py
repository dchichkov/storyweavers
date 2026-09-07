#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    child: str = "Mira"
    friend: str = "Pip"
    nose: str = "a red wooden nose"
    bedtime_object: str = "the moon pillow"
    problem: str = "lonely"
    solution: str = "share"
    voice: str = "gentle"
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.history.append(text)

    def render(self) -> str:
        return " ".join(self.history)


def _entity(world: World, eid: str, kind: str, label: str) -> Entity:
    return world.add(Entity(eid, kind, label))


def build_world(params: StoryParams, rng: random.Random) -> World:
    if params.solution not in {"share", "lend", "trade"}:
        raise StoryError("The solution must be share, lend, or trade.")
    world = World()
    child = _entity(world, "child", "character", params.child)
    friend = _entity(world, "friend", "character", params.friend)
    nose = _entity(world, "nose", "object", params.nose)
    pillow = _entity(world, "pillow", "object", params.bedtime_object)

    child.memes.update(warmth=1, kindness=0, curiosity=0)
    friend.memes["hope"] = 0
    nose.meters["held"] = 1
    pillow.meters["softness"] = 1

    openings = [
        f"At bedtime, {params.child} tucked {params.bedtime_object} beneath the quilt.",
        f"When the bedroom grew quiet, {params.child} arranged a small bedtime scene beside {params.bedtime_object}.",
        f"Under the sleepy yellow moon, {params.child} carried {params.nose} to bed.",
    ]
    world.say(rng.choice(openings))
    world.say(
        f"{params.child} loved {params.nose}, but tonight {params.friend} sat nearby "
        f"with drooping shoulders and a very quiet {params.friend}."
    )

    if params.problem == "lonely":
        friend.memes["loneliness"] = 2
        world.say(
            f'"I cannot settle down," said {params.friend}. "The dark feels too big."'
        )
    elif params.problem == "worried":
        friend.memes["worry"] = 2
        world.say(
            f'"I heard a creak," whispered {params.friend}. "What if the night is awake?"'
        )
    elif params.problem == "sad":
        friend.memes["sadness"] = 2
        world.say(
            f'"My good feeling went missing," said {params.friend}. "I cannot find it anywhere."'
        )
    else:
        raise StoryError("Unknown bedtime problem.")

    world.say(f"{params.child} remembered that {params.nose} had made {params.friend} giggle earlier.")
    world.say(
        f'"You can hold {params.nose} for a while," said {params.child}. '
        f'"A happy thing grows when it is shared."'
    )

    if params.solution == "share":
        nose.meters["held"] = 0
        friend.memes["hope"] += 2
        child.memes["kindness"] += 2
        world.say(
            f"{params.friend} held {params.nose} gently, and {params.child} kept one hand "
            f"on {params.friend}'s sleeve."
        )
        world.say(
            f'"It is still ours," {params.friend} said. "It feels warmer that way."'
        )
    elif params.solution == "lend":
        friend.memes["hope"] += 1
        child.memes["kindness"] += 1
        world.say(
            f"{params.child} placed {params.nose} beside {params.friend}'s pillow and "
            'said, "Keep it until morning."'
        )
        world.say(
            f'"I will take care of it," promised {params.friend}, hugging the little nose close.'
        )
    else:
        friend.memes["hope"] += 1
        child.memes["curiosity"] += 1
        world.say(
            f"{params.friend} offered a smooth pebble, and the two friends made a tiny "
            f"bedtime trade: {params.nose} for the night, then the pebble for tomorrow."
        )
        world.say(
            f'"Now we both have something to hold," {params.child} said.'
        )

    world.say(
        f"The room stayed quiet, but it no longer felt empty. The moon pillow rested "
        f"between them like a small silver boat."
    )
    world.say(
        f'Before sleep came, {params.friend} whispered, "Tomorrow, I will share the '
        'good things too."'
    )
    world.say(
        f"{params.child} smiled, and the two friends fell asleep while {params.nose} "
        f"kept watch in the soft moonlight."
    )

    world.facts.update(
        child=child,
        friend=friend,
        nose=nose,
        pillow=pillow,
        problem=params.problem,
        solution=params.solution,
    )
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle bedtime story about {f['child'].label} sharing {f['nose'].label} with {f['friend'].label}.",
        f"Tell a sleepy story in which sharing {f['nose'].label} changes how {f['friend'].label} feels before bed.",
        f"Write a story with a quiet foreshadowing detail about {f['nose'].label}, followed by a warm shared ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"].label
    friend = f["friend"].label
    nose = f["nose"].label
    solution = f["solution"]
    action = {
        "share": f"{child} let {friend} hold {nose}, so the comfort became something they enjoyed together.",
        "lend": f"{child} placed {nose} beside {friend}'s pillow and lent it until morning.",
        "trade": f"{child} and {friend} traded {nose} and a smooth pebble so each friend had something comforting.",
    }[solution]
    return [
        QAItem(
            f"Who was awake at bedtime?",
            f"{child} and {friend} were awake together in the quiet bedroom.",
        ),
        QAItem(
            f"Why did {friend} need comfort?",
            f"{friend} felt {f['problem']} in the dark and needed a kind friend nearby.",
        ),
        QAItem(
            f"What happened to {nose}?",
            action,
        ),
        QAItem(
            "How did sharing change the ending?",
            f"Sharing helped {friend} feel hopeful, and both friends fell asleep peacefully.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why can sharing help someone?",
            "Sharing can help someone feel included, cared for, and less alone.",
        ),
        QAItem(
            "What is foreshadowing?",
            "Foreshadowing is a small earlier clue that hints at something important later.",
        ),
        QAItem(
            "Why are bedtime stories often gentle?",
            "Gentle bedtime stories help children feel safe and ready to rest.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    world = build_world(params, rng)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
comforting(share).
comforting(lend).
comforting(trade).
valid_solution(S) :- comforting(S).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("solution", x) for x in ("share", "lend", "trade"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A bedtime storyworld about sharing a nose.")
    parser.add_argument("--child")
    parser.add_argument("--friend")
    parser.add_argument("--nose")
    parser.add_argument("--problem", choices=["lonely", "worried", "sad"])
    parser.add_argument("--solution", choices=["share", "lend", "trade"])
    parser.add_argument("--voice", choices=["gentle", "dreamy", "quiet"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child or rng.choice(["Mira", "Nell", "Toby", "Ari", "Lina"])
    friends = [x for x in ["Pip", "Moss", "Bram", "Una", "Sol"] if x != child]
    return StoryParams(
        child=child,
        friend=args.friend or rng.choice(friends),
        nose=args.nose or rng.choice(["a red wooden nose", "a round blue nose", "a tiny felt nose"]),
        bedtime_object="the moon pillow",
        problem=args.problem or rng.choice(["lonely", "worried", "sad"]),
        solution=args.solution or rng.choice(["share", "lend", "trade"]),
        voice=args.voice or rng.choice(["gentle", "dreamy", "quiet"]),
        seed=args.seed,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"{entity.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def verify() -> int:
    import asp
    actual = {str(args[0]) for args in asp.atoms(asp.one_model(asp_facts() + "\n" + ASP_RULES), "valid_solution")}
    if actual != {"share", "lend", "trade"}:
        return 1
    for solution in sorted(actual):
        for problem in ("lonely", "worried", "sad"):
            sample = generate(StoryParams(solution=solution, problem=problem, seed=777))
            assert sample.world.facts["friend"].memes["hope"] > 0
            assert sample.story_qa
    print("OK: causal bedtime solutions are defined.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_facts())
        print(ASP_RULES)
        return
    if args.verify:
        sys.exit(verify())
    if args.asp:
        print("valid solutions: share, lend, trade")
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(problem="lonely", solution="share", seed=base, child="Mira", friend="Pip"),
            StoryParams(problem="worried", solution="lend", seed=base + 1, child="Nell", friend="Moss"),
            StoryParams(problem="sad", solution="trade", seed=base + 2, child="Toby", friend="Una"),
        ]
    else:
        params_list = []
        for i in range(args.n):
            rng = random.Random(base + i)
            params = resolve_params(args, rng)
            params.seed = base + i
            params_list.append(params)

    samples = [generate(p) for p in params_list]
    if args.json:
        data = [s.to_dict() for s in samples]
        print(json.dumps(data[0] if len(data) == 1 else data, indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### bedtime story {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i + 1 < len(samples):
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
