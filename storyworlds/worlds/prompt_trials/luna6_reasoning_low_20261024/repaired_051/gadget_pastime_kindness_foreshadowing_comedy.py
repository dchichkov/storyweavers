#!/usr/bin/env python3
"""A comic little storyworld about a gadget, a pastime, and a kindness repaid."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_here = Path(__file__).resolve()
for _parent in _here.parents:
    if (_parent / "storyworlds" / "results.py").exists():
        sys.path.insert(0, str(_parent / "storyworlds"))
        break
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0, "order": 0.0, "working": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"worry": 0.0, "kindness": 0.0, "joy": 0.0, "trust": 0.0})


@dataclass
class StoryParams:
    hero: str
    friend: str
    neighbor: str
    gadget: str
    pastime: str
    scenario_index: int = 0
    variant: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace_log: list[str] = []
        self.completed = False

    def add(self, entity: Entity) -> Entity:
        if entity.id in self.entities:
            raise StoryError(f"Entity name {entity.id!r} is used more than once.")
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part for part in paragraph if part) for paragraph in self.paragraphs if paragraph)

    def log(self, text: str) -> None:
        self.trace_log.append(text)


SCENARIOS = [
    {
        "problem": "The gadget's tiny fan blew the paper napkin right onto the mayor's nose.",
        "clue": "A scrap of ribbon kept fluttering toward the fan's loose side flap.",
        "fix": "They tied the flap down with ribbon and aimed the fan at a pinwheel instead.",
        "kindness": "The mayor laughed, then helped them hold the pinwheel steady.",
        "image": "the pinwheel spun merrily while the mayor wore the napkin as a very small cape",
        "lesson": "a funny mistake is easier to fix when nobody is made fun of",
    },
    {
        "problem": "The gadget's alarm chirped every time a pigeon blinked, so the chess club thought a parade was coming.",
        "clue": "The friend noticed a feather resting across the gadget's little light sensor.",
        "fix": "They lifted the feather away and set the gadget to ring only when the game was finished.",
        "kindness": "They invited the pigeons to watch from a safe perch, where no blinking could interrupt the game.",
        "image": "the last chess piece stood proudly beside a pigeon wearing a feather like a hat",
        "lesson": "patience and a gentle invitation can turn a nuisance into company",
    },
    {
        "problem": "A spring-loaded snack sorter bounced carrots into the flowerpots and radishes into a shoe.",
        "clue": "The hero saw that the labels had been swapped when the gadget was turned upside down.",
        "fix": "They turned the labels around and tested the sorter with one carrot before filling the basket.",
        "kindness": "They shared the rescued vegetables with the gardener, who had been working through lunch.",
        "image": "a tidy snack basket sat beside one very surprised shoe and a row of happy flowers",
        "lesson": "checking a small detail can save a great deal of scrambling",
    },
    {
        "problem": "The gadget's singing timer played a grand trumpet fanfare whenever someone sat down to knit.",
        "clue": "The friend heard the fanfare begin exactly when a loose button bumped the timer.",
        "fix": "They fastened the button and chose a quiet bell for the knitting pastime.",
        "kindness": "They saved the trumpet fanfare for the neighbor's birthday, with the neighbor's permission.",
        "image": "a soft scarf warmed the neighbor while a birthday trumpet gave one cheerful toot",
        "lesson": "noticing what bothers someone is a kind way to choose what to do next",
    },
]

OPENINGS = [
    "On a bright Saturday morning",
    "Just as the town clock gave a polite little hiccup",
    "While the clouds looked like lumpy mashed potatoes",
    "Before the first kettle whistled",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A comic tale of a helpful gadget and a favorite pastime.")
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--neighbor")
    parser.add_argument("--gadget")
    parser.add_argument("--pastime")
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
    pastime = args.pastime or rng.choice(["birdwatching", "knitting", "chess", "gardening", "making paper boats"])
    if not pastime.strip():
        raise StoryError("Pastime must be a non-empty activity.")
    return StoryParams(
        hero=args.hero or rng.choice(["Mina", "Pip", "Ravi", "Lulu", "Tess"]),
        friend=args.friend or rng.choice(["Bo", "Nell", "Kit", "Omar", "June"]),
        neighbor=args.neighbor or rng.choice(["Mr. Wobble", "Auntie Fern", "Mayor Plum", "Old Badger"]),
        gadget=args.gadget or rng.choice(["the whirring helper", "the pocket-sized gadget", "the clever little machine"]),
        pastime=pastime,
        scenario_index=rng.randrange(len(SCENARIOS)),
        variant=rng.randrange(10_000),
    )


def tell(params: StoryParams) -> World:
    if not params.hero.strip() or not params.friend.strip() or not params.neighbor.strip():
        raise StoryError("Hero, friend, and neighbor names must not be empty.")
    if params.hero.strip().casefold() == params.friend.strip().casefold():
        raise StoryError("The hero and friend need different names.")
    if not params.gadget.strip() or not params.pastime.strip():
        raise StoryError("Gadget and pastime must not be empty.")
    if not 0 <= params.scenario_index < len(SCENARIOS):
        raise StoryError(f"Scenario index must be from 0 to {len(SCENARIOS) - 1}.")

    w = World()
    hero = w.add(Entity(params.hero, "child", params.hero))
    friend = w.add(Entity(params.friend, "child", params.friend))
    neighbor = w.add(Entity(params.neighbor, "neighbor", params.neighbor))
    gadget = w.add(Entity("gadget", "machine", params.gadget))
    scenario = SCENARIOS[params.scenario_index]
    w.facts.update(hero=hero, friend=friend, neighbor=neighbor, gadget=gadget, scenario=scenario)

    hero.memes["joy"] += 1
    friend.memes["trust"] += 1
    opening = OPENINGS[params.variant % len(OPENINGS)]
    w.say(
        f"{opening}, {hero.label} and {friend.label} brought {params.gadget} to the garden shed "
        f"to make {params.pastime} more fun."
    )
    w.say(
        f"{neighbor.label} had once lent them a bright ribbon when their kite got stuck, "
        f"so they promised to use the gadget to help the neighbor too."
    )
    w.para()

    hero.memes["worry"] += 1
    w.say(scenario["problem"])
    w.say(f'{hero.label} frowned. "{scenario["clue"]}"')
    w.say(f'"Then let us look before we poke," {friend.label} said. {scenario["clue"]}')
    w.para()

    gadget.meters["working"] = 1
    gadget.meters["order"] = 1
    friend.memes["kindness"] += 1
    hero.memes["kindness"] += 1
    w.say(scenario["fix"])
    w.say(
        f'"We can use this to make your afternoon easier, too," {hero.label} told {neighbor.label}. '
        f'{scenario["kindness"]}'
    )
    w.para()

    w.completed = True
    hero.memes["joy"] += 1
    neighbor.memes["trust"] += 1
    neighbor.memes["kindness"] += 1
    w.say(
        f"The gadget now behaved, and the friends returned to {params.pastime} with the neighbor beside them. "
        f"{scenario['lesson'].capitalize()}."
    )
    w.say(f"By sunset, {scenario['image']}.")
    w.log(f"scenario={params.scenario_index}")
    w.log("gadget_repaired=true")
    w.log("kindness_shared=true")
    return w


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        f"Write a funny, kind story about {p.gadget} and {p.pastime}.",
        f"Tell how {p.hero} and {p.friend} notice a clue, help {p.neighbor}, and make a gadget work.",
        "Include an early hint that becomes useful later, a brief spoken exchange, and a concrete comic ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    scenario: dict[str, str] = world.facts["scenario"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What went wrong with {p.gadget}?",
            answer=f"{scenario['problem']} The friends stopped to look for a clue instead of making the trouble worse.",
        ),
        QAItem(
            question=f"What clue helped {p.hero} and {p.friend}?",
            answer=f"{scenario['clue']} It pointed them toward a simple repair.",
        ),
        QAItem(
            question=f"How did the friends show kindness to {p.neighbor}?",
            answer=f"They used their repaired gadget to help {p.neighbor}: {scenario['kindness']}",
        ),
        QAItem(
            question=f"What pastime were the friends enjoying?",
            answer=f"They had brought the gadget to make {p.pastime} more fun, and returned to it after helping their neighbor.",
        ),
        QAItem(
            question="What showed that the problem was truly solved?",
            answer=f"{scenario['image']}. The gadget worked, and the neighbor was included in the happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gadget?",
            answer="A gadget is a small tool or device made to help with a task or make something easier.",
        ),
        QAItem(
            question="What is a pastime?",
            answer="A pastime is an activity someone enjoys doing in their free time, such as knitting, gardening, or playing chess.",
        ),
        QAItem(
            question="How can a small kindness help a friendship?",
            answer="A small kindness shows someone that they matter. Listening, sharing, or offering useful help can make people feel welcome and build trust.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(("", "== world qa =="))
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"{entity.label}: kind={entity.kind}, meters={meters}, memes={memes}")
    lines.extend(world.trace_log)
    return "\n".join(lines)


ASP_RULES = r"""
repaired :- clue_found, gentle_repair.
kindness_returned :- remembered_help, help_neighbor.
complete_story :- repaired, kindness_returned, pastime_resumes.
#show repaired/0.
#show kindness_returned/0.
#show complete_story/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        (
            asp.fact("clue_found"),
            asp.fact("gentle_repair"),
            asp.fact("remembered_help"),
            asp.fact("help_neighbor"),
            asp.fact("pastime_resumes"),
        )
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    actual = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {"repaired/0", "kindness_returned/0", "complete_story/0"}
    if actual != expected:
        print(f"MISMATCH: ASP produced {sorted(actual)}, expected {sorted(expected)}")
        return 1
    try:
        for index in range(len(SCENARIOS)):
            sample = generate(
                StoryParams("Mina", "Bo", "Mayor Plum", "the whirring helper", "chess", index, index)
            )
            if not sample.story or not sample.world or not sample.world.completed:
                raise AssertionError("Generated story did not reach its resolution.")
            if "said" not in sample.story or SCENARIOS[index]["image"] not in sample.story:
                raise AssertionError("Generated story is missing dialogue or its changed ending image.")
    except Exception as exc:
        print(f"MISMATCH: generated-story check failed: {exc}")
        return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    world.facts["params"] = params
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Mina", "Bo", "Mayor Plum", "the whirring helper", "birdwatching", 0, 1),
    StoryParams("Pip", "Nell", "Auntie Fern", "the pocket-sized gadget", "chess", 1, 2),
    StoryParams("Ravi", "June", "Mr. Wobble", "the clever little machine", "knitting", 2, 3),
    StoryParams("Tess", "Kit", "Old Badger", "the singing timer", "gardening", 3, 0),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1 and not args.all:
        raise StoryError("-n must be at least 1.")
    if args.show_asp:
        print(asp_program("#show repaired/0. #show kindness_returned/0. #show complete_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        print("ASP model:", " ".join(str(atom) for atom in asp.one_model(asp_program())))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 30, 30):
            rng = random.Random(base_seed + attempts)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempts
            attempts += 1
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
        if len(samples) < args.n:
            raise StoryError("Could not produce enough distinct stories; try a different seed or fewer samples.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return
    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except StoryError as exc:
        print(f"Story error: {exc}", file=sys.stderr)
        sys.exit(2)
