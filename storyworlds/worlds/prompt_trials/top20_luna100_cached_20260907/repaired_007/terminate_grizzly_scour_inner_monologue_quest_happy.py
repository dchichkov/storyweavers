#!/usr/bin/env python3
"""
A tiny superhero storyworld about a grizzly, a careful scour, and a quest
that ends happily. Luna must decide whether to terminate a dangerous mess
before it reaches the village.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Quest:
    key: str
    threat: str
    tool: str
    action: str
    ending: str


QUESTS = (
    Quest(
        "berry_mist",
        "a cloud of sour berry mist",
        "her bright moon scoop",
        "scour the mist from the spring stones",
        "the spring ran clear, and the grizzly carried baskets of sweet berries home",
    ),
    Quest(
        "cave_spark",
        "a nest of crackling cave sparks",
        "her silver brush",
        "scour the sparks away from the dry grass",
        "the cave glowed safely, and the grizzly shared warm honey cakes with the village",
    ),
    Quest(
        "river_foam",
        "a ribbon of foamy river mud",
        "her rainbow shield",
        "scour the mud from the little river gate",
        "the gate opened, and the grizzly splashed happily through clean water",
    ),
    Quest(
        "star_dust",
        "a heap of prickly star dust",
        "her soft cloud cape",
        "scour the star dust from the moon bridge",
        "the bridge shone again, and the grizzly danced beneath the stars",
    ),
)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    bear_name: str
    hero_gender: str = "girl"
    seed: Optional[int] = None


PLACES = {
    "moon_valley": Place("moon_valley", "Moon Valley", {"valley", "magical"}),
    "pine_village": Place("pine_village", "Pine Village", {"village", "forest"}),
    "cloud_harbor": Place("cloud_harbor", "Cloud Harbor", {"harbor", "sky"}),
}

NAMES = ["Luna", "Mira", "Nova", "Pia", "Zara"]
BEAR_NAMES = ["Bruno", "Grizzle", "Honey", "Moss", "Thunder"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A superhero quest about Luna and a grizzly.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hero")
    parser.add_argument("--bear")
    parser.add_argument("--hero-gender", choices=["girl", "boy"], default="girl")
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
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(NAMES)
    bears = [name for name in BEAR_NAMES if name != hero]
    bear = args.bear or rng.choice(bears)
    return StoryParams(place, hero, bear, args.hero_gender, args.seed)


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if not params.hero_name.strip() or not params.bear_name.strip():
        raise StoryError("Hero and grizzly names must not be empty.")
    if params.hero_name.lower() == params.bear_name.lower():
        raise StoryError("The hero and grizzly need different names.")

    rng = random.Random(params.seed if params.seed is not None else 0)
    quest = QUESTS[rng.randrange(len(QUESTS))]
    world = World(PLACES[params.place])

    luna = world.add(Entity("hero", "character", params.hero_gender, params.hero_name))
    grizzly = world.add(Entity("grizzly", "character", "grizzly", params.bear_name))
    threat = world.add(Entity("threat", "thing", "danger", quest.threat))
    tool = world.add(Entity("tool", "thing", "gear", quest.tool))

    world.say(f"In {world.place.label}, {luna.label} wore a cape bright enough to guide a comet.")
    world.say(f"Her brave grizzly friend, {grizzly.label}, watched the valley gate.")
    world.para()
    world.say(f"Suddenly, {quest.threat} rolled toward the village.")
    world.say(f'"I must terminate this danger before it reaches anyone," thought {luna.label}.')
    world.say(f'"Are you sure we should go?" asked {grizzly.label}.')
    world.say(f'"Not alone," said {luna.label}. "You watch the path while I use {quest.tool}."')
    world.para()

    luna.meters["courage"] = 1
    luna.memes["worry"] = 1
    grizzly.meters["help"] = 1
    grizzly.memes["trust"] = 1
    world.say(f"The two friends began their quest. {grizzly.label} thumped beside the danger and kept it away from the homes.")
    world.say(f"{luna.label} used {quest.tool} to {quest.action}.")
    world.say(f'"The path is clear now!" called {grizzly.label}.')
    world.say(f'"Then one last sweep," replied {luna.label}. "A hero checks the corners."')
    world.para()

    threat.meters["danger"] = 0
    threat.meters["terminated"] = 1
    luna.memes["joy"] = 1
    grizzly.memes["joy"] = 1
    world.say(f"The danger faded at last. Their teamwork had terminated the threat safely.")
    world.say(f"{quest.ending.capitalize()}. {luna.label} and {grizzly.label} hugged beneath the happy moon.")

    world.facts.update(
        hero=luna,
        grizzly=grizzly,
        threat=threat,
        tool=tool,
        quest=quest,
        problem=quest.threat,
        action=quest.action,
        ending=quest.ending,
        terminated=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a child-friendly superhero story using the words "terminate," "grizzly," and "scour."',
        f"Tell a quest story in which {f['hero'].label} and {f['grizzly'].label} face {f['problem']} and solve it together.",
        "Include a short inner monologue, spoken dialogue, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            "What danger did the superhero friends face?",
            f"They faced {f['problem']}, which was moving toward the village."
        ),
        QAItem(
            "How did Luna and the grizzly solve the problem?",
            f"{f['grizzly'].label} guarded the path while {f['hero'].label} used {f['tool'].label} to {f['action']}."
        ),
        QAItem(
            "How did the story end happily?",
            f"The danger was terminated safely, and {f['ending']}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a grizzly?", "A grizzly is a large brown bear. Grizzlies are strong animals with powerful paws."),
        QAItem("What does terminate mean?", "Terminate means to bring something to an end."),
        QAItem("What does scour mean?", "Scour means to clean or search something carefully."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
dangerous(T) :- threat(T), danger(T, 1).
can_terminate :- dangerous(T), hero(H), grizzly(G), tool(X), helps(G), uses(H, X).
resolved :- can_terminate.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "luna"),
            asp.fact("grizzly", "grizzly"),
            asp.fact("threat", "cloud"),
            asp.fact("tool", "scoop"),
            asp.fact("danger", "cloud", 1),
            asp.fact("helps", "grizzly"),
            asp.fact("uses", "luna", "scoop"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program())
        if not asp.atoms(model, "resolved"):
            print("ASP parity failed: no resolved outcome.")
            return 1
        sample = generate(StoryParams("moon_valley", "Luna", "Bruno", seed=3))
        if not sample.story.strip() or "happy" not in sample.story.lower():
            print("Generation parity failed.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: smoke tests passed.")
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolved/0."))
    return asp.atoms(model, "resolved")


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(place, NAMES[i % len(NAMES)], BEAR_NAMES[i % len(BEAR_NAMES)], seed=base + i)
            for i, place in enumerate(PLACES)
        ]
    else:
        params_list = []
        for i in range(args.n):
            rng = random.Random(base + i)
            params = resolve_params(args, rng)
            params.seed = base + i
            params_list.append(params)

    samples = [generate(params) for params in params_list]
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
