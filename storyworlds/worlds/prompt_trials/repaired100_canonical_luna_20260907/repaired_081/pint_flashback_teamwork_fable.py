#!/usr/bin/env python3
"""
A small fable about a pint of moon milk, a flashback, and teamwork.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str = "Luna"
    helper_name: str = "Pip"
    village: str = "Thistle Hollow"
    animal: str = "fox"
    challenge: str = "spill"
    telling_mode: str = "flashback"
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


HERO_NAMES = ["Luna", "Mira", "Tess", "Nell", "Ravi"]
HELPER_NAMES = ["Pip", "Bram", "Ivy", "Otto", "Sela"]
VILLAGES = ["Thistle Hollow", "Mossy Glen", "Clover Brook", "Wrenfield"]
ANIMALS = ["fox", "badger", "rabbit", "hedgehog"]

CHALLENGES = {
    "spill": {
        "problem": "A pint of warm moon milk slipped from the stone table and began to run toward the fire.",
        "clue": "Luna noticed that the milk had stopped beside a ring of flour, where the floor dipped gently.",
        "fix": "The friends tilted a clean board toward the dip, placed a cup beneath the edge, and guided the milk back into the pint jar.",
        "result": "Not a drop was lost, and the fire stayed safely dry.",
        "lesson": "a small accident is easier to mend when everyone uses a different helpful skill",
        "ending": "The moon rose above the cottage, and the rescued pint shone like a tiny silver pond.",
    },
    "crack": {
        "problem": "A hairline crack appeared in the clay pint cup just as the evening drink was poured.",
        "clue": "Pip saw a dark line grow only when the warm milk touched the cold clay.",
        "fix": "Luna fetched a wooden cup, while Pip wrapped the clay cup in wool and used it to carry dry oats instead.",
        "result": "The milk stayed warm, and the cracked cup found a safer new purpose.",
        "lesson": "a thing can be useful again when friends notice what it can safely do",
        "ending": "The old cup held oats by the window, where a sparrow pecked beside it.",
    },
    "missing": {
        "problem": "The village pint jar vanished before the neighbors could share their bedtime drink.",
        "clue": "A trail of white drops led from the pantry to the sleepy fox's basket.",
        "fix": "The friends followed the trail, found the jar behind a blanket, and carried it together without waking the fox.",
        "result": "The milk returned to the table, and the fox kept sleeping peacefully.",
        "lesson": "careful looking can solve a mystery without blaming anyone",
        "ending": "At dawn, the fox blinked at the empty trail and curled up beside the clean jar.",
    },
    "froth": {
        "problem": "The pint of milk frothed so high that it hid the honey spoon and nearly overflowed.",
        "clue": "Luna remembered that the village churn made less froth when the milk was stirred slowly.",
        "fix": "Pip held the jar steady while Luna stirred in quiet circles and waited between each turn.",
        "result": "The froth settled, leaving just enough cream for every bowl.",
        "lesson": "patience and steady hands can make room for everyone",
        "ending": "The villagers shared the creamy pint, and no one hurried the last sweet spoonful.",
    },
}

ASP_RULES = r"""
entity(E) :- named(E).
teamwork :- helped(hero, helper), repaired(pint).
flashback_used :- remembered(hero), repaired(pint).
safe_pint :- repaired(pint), shared(pint).
fable_lesson :- learned(hero).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("named", "hero"),
            asp.fact("named", "helper"),
            asp.fact("named", "pint"),
            asp.fact("helped", "hero", "helper"),
            asp.fact("repaired", "pint"),
            asp.fact("remembered", "hero"),
            asp.fact("shared", "pint"),
            asp.fact("learned", "hero"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    shown = (
        "#show teamwork/0.\n"
        "#show flashback_used/0.\n"
        "#show safe_pint/0.\n"
        "#show fable_lesson/0."
    )
    model = asp.one_model(asp_program(shown))
    names = {symbol.name for symbol in model}
    wanted = {"teamwork", "flashback_used", "safe_pint", "fable_lesson"}
    if names == wanted:
        sample = generate(StoryParams(seed=17))
        if not sample.story or "pint" not in sample.story.lower():
            print("Generated story exercise failed.")
            return 1
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(names))
    print("PY :", sorted(wanted))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a fable about a pint, a flashback, and teamwork."
    )
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--village", choices=VILLAGES)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--challenge", choices=list(CHALLENGES))
    parser.add_argument("--telling-mode", choices=["flashback", "straight", "dialogue"])
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
    hero = args.name or rng.choice(HERO_NAMES)
    possible_helpers = [name for name in HELPER_NAMES if name != hero]
    helper = args.helper or rng.choice(possible_helpers)
    if hero == helper:
        raise StoryError("The hero and helper must be different characters.")
    return StoryParams(
        hero_name=hero,
        helper_name=helper,
        village=args.village or rng.choice(VILLAGES),
        animal=args.animal or rng.choice(ANIMALS),
        challenge=args.challenge or rng.choice(list(CHALLENGES)),
        telling_mode=args.telling_mode or rng.choice(["flashback", "straight", "dialogue"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.challenge not in CHALLENGES:
        raise StoryError(f"Unknown challenge: {params.challenge}.")
    if params.hero_name == params.helper_name:
        raise StoryError("The hero and helper must be different characters.")

    rng = random.Random(
        params.seed
        if params.seed is not None
        else f"{params.hero_name}:{params.helper_name}:{params.village}:{params.challenge}"
    )
    challenge = CHALLENGES[params.challenge]
    world = World()

    hero = world.add(
        Entity(
            "hero",
            "character",
            params.hero_name,
            meters={"energy": 1.0, "distance_to_pint": 2.0},
            memes={"worry": 0.0, "courage": 0.0, "kindness": 1.0},
        )
    )
    helper = world.add(
        Entity(
            "helper",
            "character",
            params.helper_name,
            meters={"energy": 1.0, "distance_to_pint": 2.0},
            memes={"worry": 0.0, "patience": 1.0, "team_spirit": 1.0},
        )
    )
    pint = world.add(
        Entity(
            "pint",
            "thing",
            "pint of moon milk",
            meters={"fullness": 1.0, "stability": 0.4, "warmth": 0.8},
            memes={"value": 1.0, "danger": 0.3},
        )
    )
    animal = world.add(
        Entity(
            "animal",
            "animal",
           	f"a sleepy {params.animal}",
            meters={"sleepiness": 0.9},
            memes={"trust": 0.7},
        )
    )

    if params.telling_mode == "flashback":
        world.say(
            f"Years later, whenever {params.hero_name} poured a pint of milk in {params.village}, "
            f"the old fable came back to mind."
        )
        world.say(
            f"Back then, {params.hero_name} and {params.helper_name} had been young enough to think "
            f"one little accident meant the evening was ruined."
        )
    elif params.telling_mode == "dialogue":
        world.say(
            f'“Do you remember the pint?” {params.helper_name} asked {params.hero_name} in {params.village}.'
        )
        world.say(
            f'“I remember the lesson,” {params.hero_name} replied, as the fable began again.'
        )
    else:
        world.say(
            f"In {params.village}, {params.hero_name} carried a pint of moon milk toward the cottage table."
        )
        world.say(
            f"The sleepy {params.animal} watched from a basket while the evening grew cool."
        )

    if params.telling_mode != "straight":
        world.say(
            f"The memory returned to the moment when {params.hero_name} carried the pint into the cottage."
        )
    world.say(
        f"The {params.animal} slept near the hearth, and the pint was meant to be shared with every neighbor."
    )
    world.say(challenge["problem"])

    pint.meters["stability"] = 0.1
    pint.memes["danger"] = 1.0
    hero.memes["worry"] = 1.0
    helper.memes["worry"] = 0.7

    world.say(
        f'“Oh no,” said {params.hero_name}. “I should fix this before anyone gets hurt.”'
    )
    world.say(
        f'“You do not have to fix it alone,” said {params.helper_name}. “Tell me what you see.”'
    )
    world.say(
        f"{params.hero_name} described the trouble, and {params.helper_name} looked closely instead of rushing."
    )
    world.say(challenge["clue"])

    hero.meters["distance_to_pint"] = 0.5
    helper.meters["distance_to_pint"] = 0.5
    world.say(
        f"{params.hero_name} watched the path of the milk while {params.helper_name} searched for a safe tool."
    )
    world.say(
        f"They each chose one job, because teamwork worked better than two pairs of hands grabbing at once."
    )
    world.say(challenge["fix"])

    pint.meters["stability"] = 1.0
    pint.meters["fullness"] = 0.9
    pint.memes["danger"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["courage"] = 1.0
    helper.memes["worry"] = 0.0
    helper.memes["team_spirit"] = 2.0

    world.say(challenge["result"])
    world.say(
        f'“We saved the pint because we listened to each other,” {params.hero_name} said.'
    )
    world.say(
        f'“And because we noticed the clue before choosing the cure,” {params.helper_name} answered.'
    )
    world.say(
        f"Then the friends shared the milk with the neighbors, leaving a small saucer for the sleepy {params.animal}."
    )
    world.say(
        f"{params.hero_name} understood the fable's lesson: {challenge['lesson']}."
    )
    world.say(challenge["ending"])

    world.facts.update(
        hero=hero,
        helper=helper,
        pint=pint,
        animal=animal,
        repaired=True,
        shared=True,
        teamwork=True,
        flashback=params.telling_mode == "flashback",
        lesson=challenge["lesson"],
        problem=challenge["problem"],
        clue=challenge["clue"],
        fix=challenge["fix"],
        result=challenge["result"],
    )

    prompts = [
        f"Tell a fable about {params.hero_name} and {params.helper_name} saving a pint in {params.village}.",
        f"Use a flashback to show how teamwork helped with this problem: {challenge['problem']}",
        f"Write a child-facing fable with a clear clue, repair, shared ending, and lesson about {challenge['lesson']}.",
    ]

    story_qa = [
        QAItem(
            question="What happened to the pint?",
            answer=challenge["problem"],
        ),
        QAItem(
            question=f"What clue did {params.hero_name} and {params.helper_name} notice?",
            answer=challenge["clue"],
        ),
        QAItem(
            question="How did teamwork solve the problem?",
            answer=challenge["fix"],
        ),
        QAItem(
            question="What proved that the repair worked?",
            answer=challenge["result"],
        ),
        QAItem(
            question=f"What lesson did {params.hero_name} learn?",
            answer=f"{params.hero_name} learned that {challenge['lesson']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a pint?",
            answer="A pint is a unit used for measuring liquid, equal to about two cups in many everyday measures.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people share jobs, listen to one another, and work together toward the same goal.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a part of a story that returns to an earlier event.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that often uses animals or simple events to teach a useful lesson.",
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for entity_id, entity in sample.world.entities.items():
            print(
                f"{entity_id}: {entity.label}; "
                f"meters={entity.meters}; memes={entity.memes}"
            )
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "#show teamwork/0.\n"
                "#show flashback_used/0.\n"
                "#show safe_pint/0.\n"
                "#show fable_lesson/0."
            )
        )
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "#show teamwork/0.\n"
                "#show flashback_used/0.\n"
                "#show safe_pint/0.\n"
                "#show fable_lesson/0."
            )
        )
        print("ASP model:")
        for symbol in sorted(model, key=str):
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, challenge in enumerate(CHALLENGES):
            params = StoryParams(
                hero_name=HERO_NAMES[index % len(HERO_NAMES)],
                helper_name=HELPER_NAMES[index % len(HELPER_NAMES)],
                village=VILLAGES[index % len(VILLAGES)],
                animal=ANIMALS[index % len(ANIMALS)],
                challenge=challenge,
                telling_mode=["flashback", "straight", "dialogue"][index % 3],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 20)
        while len(samples) < args.n and index < limit:
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
