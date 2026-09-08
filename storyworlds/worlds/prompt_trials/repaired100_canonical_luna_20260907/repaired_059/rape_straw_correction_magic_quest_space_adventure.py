#!/usr/bin/env python3
"""
A child-safe space adventure about a straw-colored comet, a mistaken word,
and a magical quest to correct the ship's star map.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    name: str
    companion: str
    prize: str
    setting: str = "Moonlit Orbit"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


NAMES = ["Luna", "Mira", "Nova", "Ari", "Sol", "Pip"]
COMPANIONS = ["comet fox", "moon mouse", "starling", "robot owl"]
PRIZES = ["moon crystal", "silver star", "glowing pebble"]

SCENARIOS = [
    {
        "key": "straw_comet",
        "premise": "a straw-colored comet curled past the little ship",
        "problem": "the navigation spell labeled the comet with a hurtful mistaken word",
        "clue": "the comet's golden dust formed the same shape as the correction rune in the old quest book",
        "memory": "a teacher had said that a wrong label should be corrected kindly, not repeated as a joke",
        "dialogue": "'The spell made a mistake,' Luna said. 'We can fix the map without blaming anyone.'",
        "action": "Luna placed a clean straw ribbon beside the crystal compass while the companion read the correction rune",
        "result": "the map changed the label to Straw Comet and opened a safe route toward the moon crystal",
        "ending": "The repaired comet glowed like a warm lantern ahead of the ship",
        "lesson": "a careful correction can turn a confusing mistake into a safe new path",
    },
    {
        "key": "spell_console",
        "premise": "a floating straw bundle drifted beside the Quest ship",
        "problem": "a broken magic console displayed the seed word as if it were the name of a dangerous monster",
        "clue": "the harmless bundle bobbed whenever the ship's gentle music played",
        "memory": "Luna remembered that names should describe what something is, rather than frightening travelers",
        "dialogue": "'It is straw, not a monster,' Luna said. 'Let us correct the console and check the facts.'",
        "action": "The crew paused the engine, compared the picture with the bundle, and entered a calm correction spell",
        "result": "the console showed a straw marker and guided the ship around the drifting debris",
        "ending": "The bundle spun behind them, tied neatly like a tiny golden flag",
        "lesson": "checking evidence before trusting a dramatic message helps explorers stay brave and wise",
    },
    {
        "key": "quest_ribbon",
        "premise": "the Quest beacon wore a long ribbon woven from space-dry straw",
        "problem": "the beacon's magic had copied an incorrect warning onto every nearby star chart",
        "clue": "only the charts touched by the straw ribbon carried the strange warning",
        "memory": "Luna remembered correcting a classroom map by comparing it with the real window and the real road",
        "dialogue": "'The ribbon touched the charts,' Luna said. 'We need a correction, not a chase.'",
        "action": "The crew removed the ribbon, checked the beacon against three clear stars, and recast the map spell",
        "result": "the charts became trustworthy again and pointed to the prize without sending the ship into a storm",
        "ending": "The straw ribbon rested in a box while the true stars shone in their proper places",
        "lesson": "a patient comparison can repair magic that has copied a mistake",
    },
    {
        "key": "moon_garden",
        "premise": "a moon garden grew straw-colored reeds around a quiet portal",
        "problem": "the portal's quest inscription used a wrong word and would not open",
        "clue": "the reeds leaned toward the missing correction rune",
        "memory": "Luna recalled that even a tiny missing mark could change a whole sentence",
        "dialogue": "'Words matter,' Luna told the companion. 'Let us read the inscription carefully.'",
        "action": "They brushed moon dust from the stone, found the missing rune under a straw leaf, and spoke the corrected inscription",
        "result": "the portal opened onto a safe garden path where the prize waited beneath a silver tree",
        "ending": "The reeds rustled like applause as the portal folded into a bright little doorway",
        "lesson": "careful words can unlock a path that rushing leaves closed",
    },
]

ASP_RULES = r"""
#show valid/1.
#show story_ok/1.

valid(P) :- params(P), setting(P, moonlit_orbit), feature(P, magic), feature(P, quest).
story_ok(P) :- valid(P), correction(P), safe(P), resolved(P).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Space Adventure storyworld about magic, a quest, straw, and correction."
    )
    parser.add_argument("--name")
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--prize", choices=PRIZES)
    parser.add_argument("--setting", default="Moonlit Orbit")
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
    if args.setting.lower() != "moonlit orbit":
        raise StoryError("This quest takes place in the Moonlit Orbit.")
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        prize=args.prize or rng.choice(PRIZES),
        setting="Moonlit Orbit",
    )


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("params", "p1"),
        asp.fact("setting", "p1", "moonlit_orbit"),
        asp.fact("feature", "p1", "magic"),
        asp.fact("feature", "p1", "quest"),
        asp.fact("correction", "p1"),
        asp.fact("safe", "p1"),
        asp.fact("resolved", "p1"),
    ]
    return "\n".join(lines)


def aspire() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import asp

    model = asp.one_model(aspire())
    valid = set(asp.atoms(model, "valid"))
    good = set(asp.atoms(model, "story_ok"))
    if ("p1",) in valid and ("p1",) in good:
        print("OK: ASP and Python accept the corrected space quest.")
        return 0
    print("Mismatch: ASP did not accept the corrected space quest.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.setting != "Moonlit Orbit":
        raise StoryError("The setting must be Moonlit Orbit.")

    world = World(params)
    hero = world.add(Entity(params.name, "explorer", params.name))
    companion = world.add(Entity("companion", "companion", f"the {params.companion}"))
    prize = world.add(Entity("prize", "object", params.prize))

    stable = params.seed
    if stable is None:
        stable = sum(ord(c) for c in f"{params.name}|{params.companion}|{params.prize}")
    scenario = SCENARIOS[stable % len(SCENARIOS)]
    values = {
        "name": params.name,
        "companion": params.companion,
        "prize": params.prize,
    }
    detail = {
        key: value.format(**values)
        for key, value in scenario.items()
        if key != "key"
    }

    hero.meters.update(bravery=1.0, curiosity=1.0)
    hero.memes.update(kindness=1.0, carefulness=1.0)
    companion.memes["trust"] = 1.0
    prize.meters["reachable"] = 1.0

    world.facts.update(
        setting="Moonlit Orbit",
        feature_magic=True,
        feature_quest=True,
        seed_words=["rape", "straw", "correction"],
        problem=detail["problem"],
        clue=detail["clue"],
        correction=True,
        safe=True,
        resolved=True,
    )

    world.say(
        f"On a quiet night in the Moonlit Orbit, {params.name} guided the Quest ship beside a "
        f"{params.companion}. During their magic quest, {detail['premise']}. "
        "The strange sight made the ship's star lamps blink twice."
    )
    world.say(
        f"Then the trouble appeared: {detail['problem']}. "
        f"{params.name} almost rushed to repeat the message, but the {params.companion} tapped the console and waited."
    )
    world.say(
        f"{params.name} remembered that {detail['memory']}. "
        f"Looking closer, the useful clue was that {detail['clue']}."
    )
    world.say(detail["dialogue"])
    world.say(
        f"{detail['action']}. The correction spell used a harmless straw-colored spark, "
        "and nobody entered the drifting debris or touched the ship's hot engine."
    )
    world.say(
        f"The corrected magic changed the quest: {detail['result']}. "
        f"{params.name} understood that {detail['lesson']}."
    )
    world.say(
        f"At last, {detail['ending']}. The ship sailed on toward the {params.prize}, "
        "while the old mistake faded into a tiny harmless dot behind them."
    )

    world.facts.update(hero=hero, companion=companion, prize=prize)

    story_qa = [
        QAItem(
            f"What problem did {params.name} discover?",
            f"{params.name} discovered that {detail['problem']}.",
        ),
        QAItem(
            "What clue helped solve the mystery?",
            f"The clue was that {detail['clue']}.",
        ),
        QAItem(
            "What did the correction do?",
            f"The correction {detail['result']}.",
        ),
        QAItem(
            "How did the crew stay safe?",
            f"They paused, checked the evidence, used magic carefully, and did not enter the debris or touch the hot engine.",
        ),
        QAItem(
            "What lesson did the quest teach?",
            f"It taught that {detail['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            "What is straw?",
            "Straw is the dry stalk left after some grain plants are harvested; it can be woven or used as soft plant material.",
        ),
        QAItem(
            "What is a correction?",
            "A correction is a careful change that fixes a mistake in words, directions, or information.",
        ),
        QAItem(
            "What is a quest?",
            "A quest is a journey with a goal, often involving clues, choices, and challenges.",
        ),
        QAItem(
            "Why should explorers check a magical message?",
            "They should check it because a spell or machine can make a mistake, and careful evidence helps them choose a safe action.",
        ),
    ]
    prompts = [
        f"Write a Space Adventure about {params.name} correcting a magical quest message.",
        f"Tell a child-safe story featuring {params.name}, a {params.companion}, straw, and a kind correction.",
        "Create a space quest where checking evidence changes the route and leads to a peaceful ending.",
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.name}: kind={entity.kind}, "
                f"meters={entity.meters}, memes={entity.memes}"
            )
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(aspire())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        print("ASP model:")
        for atom in asp.one_model(aspire()):
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "comet fox", "moon crystal", seed=101),
            StoryParams("Mira", "robot owl", "silver star", seed=202),
            StoryParams("Nova", "moon mouse", "glowing pebble", seed=303),
            StoryParams("Ari", "starling", "moon crystal", seed=404),
        ]
        samples = [generate(item) for item in curated]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {index + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
