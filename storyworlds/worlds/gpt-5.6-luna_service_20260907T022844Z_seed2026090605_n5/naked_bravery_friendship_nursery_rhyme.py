#!/usr/bin/env python3
"""A gentle nursery-rhyme world about courage, friendship, and getting dressed."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class Event:
    kind: str
    actor: str
    target: str
    text: str
    cause: str = ""
    result: str = ""


@dataclass
class Setting:
    id: str
    name: str
    detail: str
    rhyme: str


@dataclass
class Friend:
    id: str
    name: str
    animal: str
    phrase: str
    kindness: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def record(
        self,
        kind: str,
        text: str,
        *,
        actor: str,
        target: str,
        cause: str = "",
        result: str = "",
    ) -> None:
        self.history.append(Event(kind, actor, target, text, cause, result))

    def render(self) -> str:
        return "\n\n".join(event.text for event in self.history)


@dataclass
class StoryParams:
    setting: str
    friend: str
    name: str
    gender: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting(
        "garden",
        "the garden",
        "where daisies nodded beside a little gate",
        "with a skip and a hop by the garden gate",
    ),
    "meadow": Setting(
        "meadow",
        "the meadow",
        "where buttercups shone like buttons of gold",
        "through the meadow bright and bold",
    ),
    "playroom": Setting(
        "playroom",
        "the playroom",
        "where wooden blocks made a tower by the rug",
        "round the tower by the rug",
    ),
}

FRIENDS = {
    "bear": Friend(
        "bear",
        "Bramble",
        "small bear",
        "We can be brave together",
        "found a warm blue robe and held it open",
    ),
    "rabbit": Friend(
        "rabbit",
        "Pip",
        "quick rabbit",
        "A friend stays near",
        "carried a yellow sweater in both paws",
    ),
    "duck": Friend(
        "duck",
        "Dapple",
        "bright duck",
        "Courage grows when friends share it",
        "brought a soft green towel from the peg",
    ),
}

NAMES = {
    "girl": ["Luna", "Mina", "Ada", "Nell"],
    "boy": ["Leo", "Milo", "Theo", "Sam"],
}
TRAITS = ["shy", "thoughtful", "quiet", "curious"]


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("That setting is not available.")
    if params.friend not in FRIENDS:
        raise StoryError("That friend is not available.")
    if not params.name.strip():
        raise StoryError("The child needs a name.")
    if params.gender not in NAMES:
        raise StoryError("Gender must be girl or boy.")

    setting = SETTINGS[params.setting]
    friend = FRIENDS[params.friend]
    world = World(setting)

    child = world.add(Entity(
        params.name,
        "character",
        params.gender,
        params.name,
        memes={"bravery": 0.0, "friendship": 1.0, "worry": 1.0},
    ))
    companion = world.add(Entity(
        friend.id,
        "character",
        friend.animal,
        friend.name,
        memes={"bravery": 1.0, "friendship": 1.0},
    ))
    robe = world.add(Entity(
        "robe",
        "clothing",
        "robe",
        "a soft robe",
        owner=child.id,
        meters={"warmth": 1.0},
    ))
    world.facts.update(child=child, companion=companion, robe=robe, friend=friend)
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    child = world.facts["child"]
    friend = world.facts["friend"]
    companion = world.facts["companion"]
    robe = world.facts["robe"]
    setting = world.setting
    name = child.label
    pronoun = "she" if params.gender == "girl" else "he"
    possessive = "her" if params.gender == "girl" else "his"

    opening = (
        f"Little {name} stood naked in {setting.name}, "
        f"and {setting.detail}. "
        f'"I have no clothes," {pronoun} whispered, '
        f"though the morning breeze made {possessive} toes curl."
    )
    world.record(
        "notice",
        opening,
        actor=child.id,
        target=child.id,
        cause=f"{name} was naked and felt worried in the open air.",
        result=f"{name} wished for a safe way to get dressed.",
    )

    problem = (
        f"The breeze went whoosh, the tall grass went swish, "
        f"and {name} wished to hide. "
        f"But {companion.label} came near and said, "
        f'"A friend stays near, and courage can grow here."'
    )
    world.record(
        "comfort",
        problem,
        actor=companion.id,
        target=child.id,
        cause=f"{companion.label} noticed that {name} felt shy while naked.",
        result=f"{companion.label} stayed close instead of laughing or leaving.",
    )
    child.memes["worry"] = 0.5
    child.memes["friendship"] += 1.0

    help_text = (
        f"{companion.label} {friend.kindness}. "
        f"{name} took one breath, then two, and said, "
        f'"I can try." '
        f"Slowly, bravely, {pronoun} stepped into the robe."
    )
    world.record(
        "help",
        help_text,
        actor=companion.id,
        target=robe.id,
        cause=f"{companion.label} offered clothing and stayed beside {name}.",
        result=f"{name} chose to get dressed with a friend's help.",
    )
    child.memes["bravery"] += 1.0
    child.memes["worry"] = 0.0
    robe.meters["worn"] = 1.0

    ending = (
        f"Now {name} was warm and covered, and {pronoun} gave a brave little grin. "
        f"Together they sang, "
        f'"Naked at first, then dressed with care; '
        f"bravery blooms when friends are there!" '
        f"{setting.rhyme.capitalize()}."
    )
    world.record(
        "resolve",
        ending,
        actor=child.id,
        target=robe.id,
        cause=f"The robe covered {name}, while friendship made the difficult moment feel safe.",
        result=f"{name} felt brave, warm, and ready to play.",
    )
    return world


KNOWLEDGE = {
    "bravery": QAItem(
        "What is bravery?",
        "Bravery means trying something difficult or frightening while taking care of yourself and others.",
    ),
    "friendship": QAItem(
        "What makes a good friend?",
        "A good friend stays kind, listens, helps when needed, and does not laugh at someone who feels worried.",
    ),
    "clothing": QAItem(
        "Why do people wear clothes?",
        "People wear clothes to stay warm, protect their bodies, and feel comfortable and covered.",
    ),
}


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    friend = world.facts["friend"]
    return [
        f"Write a gentle nursery rhyme about {child.label} feeling naked and finding bravery with {friend.name}.",
        f"Tell a child-friendly story in {world.setting.name} showing how friendship helps someone get dressed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why did the child feel worried at the beginning?",
            world.history[0].cause + " " + world.history[0].result,
        ),
        QAItem(
            "How did the friend help?",
            world.history[1].cause + " " + world.history[1].result,
        ),
        QAItem(
            "What did the child do bravely?",
            world.history[2].cause + " " + world.history[2].result,
        ),
        QAItem(
            "How did the story end?",
            world.history[3].cause + " " + world.history[3].result,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [KNOWLEDGE["bravery"], KNOWLEDGE["friendship"], KNOWLEDGE["clothing"]]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: type={entity.type}, meters={meters}, memes={memes}"
        )
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.text}")
    return "\n".join(lines)


ASP_RULES = r"""
covered_by_robe(child).
friend_supports(friend).
brave_after_support(child) :- covered_by_robe(child), friend_supports(friend).
valid_story :- brave_after_support(child).
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("covered_by_robe", "child"),
        asp.fact("friend_supports", "friend"),
    ])


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    if not asp.atoms(model, "valid_story"):
        print("ASP verification failed.")
        return 1
    sample = generate(StoryParams("garden", "bear", "Luna", "girl", seed=1))
    if "bravery" not in sample.story.lower() and "brave" not in sample.story.lower():
        print("Story verification failed.")
        return 1
    print("OK: ASP gate and generated story verified.")
    return 0


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A nursery-rhyme storyworld about nakedness, bravery, and friendship."
    )
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--friend", choices=sorted(FRIENDS))
    parser.add_argument("--name")
    parser.add_argument("--gender", choices=sorted(NAMES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(sorted(NAMES))
    return StoryParams(
        setting=args.setting or rng.choice(sorted(SETTINGS)),
        friend=args.friend or rng.choice(sorted(FRIENDS)),
        name=args.name or rng.choice(NAMES[gender]),
        gender=gender,
    )


CURATED = [
    StoryParams("garden", "bear", "Luna", "girl"),
    StoryParams("meadow", "rabbit", "Milo", "boy"),
    StoryParams("playroom", "duck", "Ada", "girl"),
]


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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise SystemExit("-n must be at least 1")
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("ASP valid story:", bool(asp.atoms(model, "valid_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
