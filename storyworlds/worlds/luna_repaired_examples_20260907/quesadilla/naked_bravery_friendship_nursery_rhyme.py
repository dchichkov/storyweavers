#!/usr/bin/env python3
"""
A gentle nursery-rhyme world about a naked little acorn, bravery, and friendship.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    facts: dict[str, str] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SCENARIOS = (
    {
        "place": "under the old oak tree",
        "friend": "a bluebird",
        "friend_name": "Bluebird Pip",
        "challenge": "a brisk wind had carried away the acorn's leafy cap",
        "clue": "a silver thread of spider silk",
        "help": "held the acorn steady with one bright wing",
        "ending": "The oak tree hummed while two friends danced beneath the moon.",
    },
    {
        "place": "beside the quiet brook",
        "friend": "a small green frog",
        "friend_name": "Frog Finn",
        "challenge": "the brook had rolled the acorn onto a bare stone",
        "clue": "three ripples that curled toward the reeds",
        "help": "called a soft, steady rhythm that helped the acorn hop home",
        "ending": "The brook sang low, and friendship warmed the little bank.",
    },
    {
        "place": "in a meadow of clover",
        "friend": "a gentle rabbit",
        "friend_name": "Rabbit Rue",
        "challenge": "a playful gust had left the acorn naked beside a puddle",
        "clue": "a trail of clover petals",
        "help": "made a leafy shelter from four clover stems",
        "ending": "The clover bells rang softly as the friends curled up together.",
    },
    {
        "place": "near the lantern-lit hill",
        "friend": "a warm-hearted hedgehog",
        "friend_name": "Hedgehog Hush",
        "challenge": "the acorn's cap had tumbled down the hill",
        "clue": "a tiny golden leaf",
        "help": "shared a snug scarf of dried grass",
        "ending": "The lantern winked above them, and brave hearts rested side by side.",
    },
)

CHILD_NAMES = ("Nell", "Toby", "Mara", "Pip")
ENDING_IMAGES = (
    "By dawn, the acorn's new cap was snug, and the first sunbeam found the friends smiling.",
    "When the stars blinked out, the naked acorn no longer felt alone.",
    "A dew drop shone like a pearl on the cap, while brave friendship kept watch.",
)


@dataclass
class StoryParams:
    seed: int | None = None
    child_name: str = "Nell"
    scenario: dict = field(default_factory=lambda: SCENARIOS[0])
    ending_image: str = ENDING_IMAGES[0]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A nursery rhyme about nakedness, bravery, and friendship.")
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
    return StoryParams(
        seed=args.seed,
        child_name=rng.choice(CHILD_NAMES),
        scenario=rng.choice(SCENARIOS),
        ending_image=rng.choice(ENDING_IMAGES),
    )


def tell(params: StoryParams) -> World:
    scenario = params.scenario
    world = World(place=scenario["place"])
    child = world.add(Entity(
        "child",
        "character",
        params.child_name,
        meters={"distance": 0.0},
        memes={"bravery": 0.0, "friendship": 0.0, "worry": 1.0},
    ))
    acorn = world.add(Entity(
        "acorn",
        "thing",
        "the naked acorn",
        meters={"safety": 0.0},
        memes={"hope": 0.0},
    ))
    friend = world.add(Entity(
        "friend",
        "animal",
        scenario["friend_name"],
        meters={"distance": 1.0},
        memes={"friendship": 0.0},
    ))
    world.facts.update(scenario)
    world.say(
        f"{params.child_name} found a naked acorn {scenario['place']}, "
        f"shivering beneath the wide sky."
    )
    world.say(
        f"Its little cap was gone; {scenario['challenge'].capitalize()}."
    )
    world.para()
    world.say(
        f'"Do not hide," whispered {params.child_name}. "A brave heart may tremble, '
        f"but it can still take a step."'
    )
    child.memes["bravery"] += 1
    child.meters["distance"] += 1
    world.say(
        f"Then {scenario['friend_name']} came near, following {scenario['clue']}."
    )
    friend.memes["friendship"] += 1
    child.memes["friendship"] += 1
    acorn.memes["hope"] += 1
    world.fired.add("bravery")
    world.para()
    world.say(
        f"{scenario['friend_name']} did not laugh at the naked acorn. "
        f"Instead, the friend {scenario['help']}."
    )
    acorn.meters["safety"] = 1.0
    child.memes["worry"] = 0.0
    world.fired.add("friendship")
    world.say(
        f"Together they found the lost cap, and {params.child_name} set it gently "
        f"on the acorn's round little head."
    )
    world.fired.add("safe")
    world.say(
        f"{scenario['ending']} {params.ending_image}"
    )
    return world


ASP_RULES = r"""
naked(acorn).
needs_courage(acorn).
has_friend(friend).
brave(child) :- needs_courage(acorn), chooses_step(child).
friendship_grows(child,friend) :- brave(child), has_friend(friend).
safe(acorn) :- friendship_grows(child,friend).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("naked", "acorn"),
        asp.fact("needs_courage", "acorn"),
        asp.fact("has_friend", "friend"),
        asp.fact("chooses_step", "child"),
    ])


def asp_program(show: str = "#show brave/1.\n#show friendship_grows/2.\n#show safe/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    brave = set(asp.atoms(model, "brave"))
    friendship = set(asp.atoms(model, "friendship_grows"))
    safe = set(asp.atoms(model, "safe"))
    if brave == {("child",)} and friendship == {("child", "friend")} and safe == {("acorn",)}:
        print("OK: ASP and Python agree on bravery, friendship, and safety.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle nursery rhyme about a naked acorn learning bravery.",
        f"Tell how {world.facts['friend_name']} helps the acorn through friendship.",
        f"Make the ending warm and rhythmic in {world.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="Why was the acorn naked?",
            answer=f"The acorn was naked because {f['challenge']}. Its leafy cap had been lost.",
        ),
        QAItem(
            question="Who helped the acorn?",
            answer=f"{f['friend_name']} helped the acorn by offering friendship and making a safe shelter.",
        ),
        QAItem(
            question="How did the child show bravery?",
            answer="The child felt worried but took a careful step toward the acorn and refused to hide it.",
        ),
        QAItem(
            question="What changed by the end?",
            answer="The lost cap was placed back on the acorn, and the child, friend, and acorn felt safe together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing a helpful or right thing even when you feel afraid or uncertain.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is caring for someone, staying near, and helping them feel less alone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


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
        raise SystemExit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(sorted(set(asp.atoms(model, "brave"))))
        print(sorted(set(asp.atoms(model, "friendship_grows"))))
        print(sorted(set(asp.atoms(model, "safe"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = len(SCENARIOS) if args.all else max(1, args.n)
    samples: list[StorySample] = []

    for index in range(count):
        seed = base_seed + index
        rng = random.Random(seed)
        params = resolve_params(argparse.Namespace(seed=seed), rng)
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
