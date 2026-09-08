#!/usr/bin/env python3
"""
A tiny mythic storyworld about a rogue crab, a moonlit claw, and puny bravery.
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
from collections import defaultdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Creature:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class StoryParams:
    hero: str
    companion: str
    beast: str
    place: str
    treasure: str
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Creature] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    history: list[str] = field(default_factory=list)

    def add(self, creature: Creature) -> Creature:
        self.entities[creature.id] = creature
        return creature

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HEROES = ["Luna", "Mira", "Nia", "Tala"]
COMPANIONS = ["Pip", "Oren", "Bram", "Suri"]
PLACES = [
    ("the hill of sleeping stones", "a star-pearl"),
    ("the shore beneath the silver moon", "the moon's lost bell"),
    ("the valley of blue reeds", "a golden seed"),
]
BEASTS = ["the rogue crab", "the rogue beetle", "the rogue lizard"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a mythic bravery tale.")
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--place")
    parser.add_argument("--beast", choices=BEASTS)
    parser.add_argument("--treasure")
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
    hero = args.hero or rng.choice(HEROES)
    companion = args.companion or rng.choice([x for x in COMPANIONS if x != hero])
    place, treasure = rng.choice(PLACES)
    return StoryParams(
        hero=hero,
        companion=companion,
        beast=args.beast or rng.choice(BEASTS),
        place=args.place or place,
        treasure=args.treasure or treasure,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero == params.companion:
        raise StoryError("The hero and companion must have different names.")

    world = World()
    hero = world.add(Creature("hero", "child", params.hero))
    companion = world.add(Creature("companion", "child", params.companion))
    beast = world.add(Creature("beast", "beast", params.beast))

    hero.memes["bravery"] = 1.0
    companion.memes["wisdom"] = 1.0
    beast.meters["strength"] = 3.0
    beast.meters["claw"] = 1.0

    world.say(
        f"In the first age, when the moon still listened to children, "
        f"{params.hero} climbed into {params.place} with {params.companion}."
    )
    world.say(
        f"They sought {params.treasure}, which the old stones said had fallen "
        f"from the sky."
    )
    world.para()
    world.say(
        f"From behind a black rock came {params.beast}, a rogue creature with "
        f"one bright claw and a hungry grin."
    )
    world.say(
        f'"Go away," said {params.companion}. "Its claw is bigger than your hand."'
    )
    world.say(
        f'"I know," said {params.hero}. Inside, {params.hero} thought, '
        f'"My bravery feels puny. Perhaps brave heroes feel no fear."'
    )
    world.para()
    world.say(
        f"The rogue beast snatched {params.treasure} and turned toward a crack "
        f"in the mountain."
    )
    world.say(
        f'{params.hero} took one small step. "Wait!" {params.hero} called. '
        f'"That treasure belongs to the sky."'
    )
    world.say(
        f'"Then come and claim it," growled the beast. Its claw scraped the stone.'
    )
    world.say(
        f'{params.companion} whispered, "Your bravery may be puny, but your voice '
        f'is not. I will stand beside you."'
    )
    world.para()
    hero.memes["bravery"] += 2.0
    companion.memes["bravery"] += 1.0
    world.say(
        f'{params.hero} lifted a little reed like a sword. The reed shook, and '
        f'{params.hero} shook with it, but neither fell.'
    )
    world.say(
        f'"We do not need to be stronger than your claw," said {params.hero}. '
        f'"We only need to be together."'
    )
    world.say(
        f'The words struck the rogue harder than a spear. Its claw lowered. '
        f'It had never heard such a small voice carry so far.'
    )
    world.say(
        f'The beast placed {params.treasure} on the stone. "Take it," it said. '
        f'"But remember: courage is not a giant. It is a small light that refuses '
        f'to go out."'
    )
    world.para()
    world.say(
        f'{params.hero} and {params.companion} carried {params.treasure} home '
        f'under the listening moon.'
    )
    world.say(
        f'And from that night onward, whenever fear whispered that their bravery '
        f'was puny, they answered together, "Small lights can guide whole worlds."'
    )

    world.facts.update(
        hero=hero,
        companion=companion,
        beast=beast,
        treasure=params.treasure,
        place=params.place,
    )

    prompts = [
        f"Write a myth about {params.hero} facing a rogue creature with a dangerous claw.",
        f"Show that puny bravery can grow when {params.hero} speaks with a friend.",
        "Use inner monologue to show that courage means acting while afraid.",
    ]
    story_qa = [
        QAItem(
            f"Who faced the rogue creature?",
            f"{params.hero} faced the rogue creature while {params.companion} stood beside {params.hero}.",
        ),
        QAItem(
            f"What made the creature frightening?",
            f"The creature had a strong, scraping claw and had stolen {params.treasure}.",
        ),
        QAItem(
            f"What did {params.hero} learn about bravery?",
            f"{params.hero} learned that bravery can feel puny and still be strong enough to speak and act.",
        ),
        QAItem(
            f"How did the story end?",
            f"The creature returned {params.treasure}, and the two friends carried it home beneath the moon.",
        ),
    ]
    world_qa = [
        QAItem(
            "What is bravery?",
            "Bravery is choosing a helpful or right action even when you feel afraid.",
        ),
        QAItem(
            "What is an inner monologue?",
            "An inner monologue is the private thought a character has inside their mind.",
        ),
        QAItem(
            "Why can a claw be dangerous?",
            "A claw can scratch or pinch, so it is wise to give a dangerous animal space.",
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


ASP_RULES = r"""
brave(hero) :- speaks(hero).
returns_treasure(beast) :- hears(beast, hero).
safe_ending :- brave(hero), returns_treasure(beast).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "luna"),
        asp.fact("quality", "bravery"),
        asp.fact("feature", "inner_monologue"),
        asp.fact("theme", "myth"),
    ])


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program() + "\n#show hero/1.")
    return 0 if asp.atoms(model, "hero") else 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.kind}, meters={dict(entity.meters)}, "
            f"memes={dict(entity.memes)}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("\n== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    for index in range(args.n):
        rng = random.Random(seed + index)
        params = resolve_params(args, rng)
        params.seed = seed + index
        samples.append(generate(params))

    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if index:
            print("\n" + "=" * 70 + "\n")
        emit(sample, trace=args.trace, qa=args.qa)


if __name__ == "__main__":
    main()
