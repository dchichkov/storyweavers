#!/usr/bin/env python3
"""
A tiny tall-tale world about Luna, a currant bush, and the price of a kind deed.
"""

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
class Quest:
    id: str
    place: str
    obstacle: str
    reward: str
    moral: str


@dataclass
class Resource:
    id: str
    label: str
    amount: int
    value: int
    edible: bool = False


@dataclass
class Character:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    characters: dict[str, Character] = field(default_factory=dict)
    resources: dict[str, Resource] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def add_character(self, character: Character) -> Character:
        self.characters[character.id] = character
        return character

    def add_resource(self, resource: Resource) -> Resource:
        self.resources[resource.id] = resource
        return resource


@dataclass
class StoryParams:
    luna_name: str
    helper_name: str
    currant_amount: int
    hew_count: int
    price: int
    quest: str
    seed: Optional[int] = None


QUESTS = {
    "hill": Quest(
        "hill",
        "the tallest hill in the valley",
        "a fallen gate that blocked the road",
        "a silver bell",
        "A kind heart is worth more than a heavy purse.",
    ),
    "orchard": Quest(
        "orchard",
        "the king's old orchard",
        "a thorny hedge taller than a tower",
        "a golden basket",
        "The best treasure is shared.",
    ),
    "bridge": Quest(
        "bridge",
        "the thunder bridge",
        "a river roaring below the broken planks",
        "a bright blue ribbon",
        "Courage grows when it helps someone else.",
    ),
}

NAMES = ["Luna", "Mara", "Nell", "Pip", "Toby", "Rin", "Odo", "Milo"]


ASP_RULES = r"""
enough_currant :- currant_amount(A), A >= price(P), P > 0.
can_hew :- hew_count(H), H >= 1.
quest_ready :- enough_currant, can_hew.
moral_value(kindness, 3).
moral_value(generosity, 4).
moral_value(courage, 5).
quest_success :- quest_ready, moral(kindness).
price_paid :- currant_amount(A), price(P), A >= P.
#show quest_ready/0.
#show quest_success/0.
#show price_paid/0.
#show moral_value/2.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Luna's currant price quest.")
    parser.add_argument("--luna")
    parser.add_argument("--helper")
    parser.add_argument("--currants", type=int)
    parser.add_argument("--hew", type=int)
    parser.add_argument("--price", type=int)
    parser.add_argument("--quest", choices=sorted(QUESTS))
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
    currants = args.currants if args.currants is not None else rng.randint(3, 8)
    hew = args.hew if args.hew is not None else rng.randint(1, 4)
    price = args.price if args.price is not None else rng.randint(2, 6)

    if currants < 1:
        raise StoryError("Luna must have at least one currant.")
    if hew < 1:
        raise StoryError("Luna must hew at least once to clear the quest's obstacle.")
    if price < 1:
        raise StoryError("The price must be a positive number.")
    if currants < price:
        raise StoryError(
            f"Luna has {currants} currants but the price is {price}; "
            "the quest cannot be completed honestly."
        )

    luna = args.luna or rng.choice(NAMES)
    helper_choices = [name for name in NAMES if name != luna]
    helper = args.helper or rng.choice(helper_choices)
    return StoryParams(
        luna_name=luna,
        helper_name=helper,
        currant_amount=currants,
        hew_count=hew,
        price=price,
        quest=args.quest or rng.choice(sorted(QUESTS)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.currant_amount < params.price:
        raise StoryError("The currant purse is too light to pay the stated price.")
    if params.hew_count < 1:
        raise StoryError("The quest requires at least one hew.")

    quest = QUESTS[params.quest]
    world = World()
    luna = world.add_character(
        Character(
            "luna",
            "child",
            params.luna_name,
            meters={"strength": float(params.hew_count), "distance": 0.0},
            memes={"hope": 1.0, "kindness": 1.0, "courage": 0.0},
        )
    )
    helper = world.add_character(
        Character(
            "helper",
            "companion",
            params.helper_name,
            meters={"strength": 1.0},
            memes={"trust": 1.0, "gratitude": 0.0},
        )
    )
    currants = world.add_resource(
        Resource("currants", "currants", params.currant_amount, params.currant_amount, True)
    )

    world.facts.update(
        quest=quest,
        luna=luna,
        helper=helper,
        currants=currants,
        paid=params.currant_amount >= params.price,
        moral_value=quest.moral,
    )

    world.trace.extend(
        [
            f"{luna.label} began with {currants.amount} currants.",
            f"{luna.label} needed to hew through {quest.obstacle}.",
            f"The price of passage was {params.price} currants.",
        ]
    )

    story = (
        f"Luna was so small that a teacup looked like a castle to her, yet she "
        f"carried {params.currant_amount} currants in her pocket and a quest in "
        f"her heart. She set out for {quest.place}, where {quest.reward} waited "
        f"beyond {quest.obstacle}."
    )

    story += (
        f'\n\n"{params.helper_name}, will you come with me?" Luna asked. '
        f'"The road has a price, and I do not want to face it alone." '
        f'"I will come," said {params.helper_name}. "But promise that your "
        f"purse will not make your heart smaller."'
    )

    world.trace.append(f"{luna.label} and {helper.label} reached the obstacle.")
    story += (
        f"\n\nAt the gate, an old keeper pointed to a sign: "
        f'"Passage costs {params.price} currants." Luna counted her berries. '
        f"There were enough, but then she saw a hungry robin shivering beneath "
        f"the gate. Luna gave the robin one currant before paying the keeper."
    )

    world.trace.append(f"{luna.label} gave one currant to the hungry robin.")
    currants.amount -= 1
    luna.memes["kindness"] += 2.0
    helper.memes["gratitude"] += 1.0

    if currants.amount < params.price:
        extra = (
            f'The keeper frowned, but {params.helper_name} offered a bright "
            f"smile and said, "A deed that feeds the hungry should not be punished." '
            f"He waved them through, and the robin sang so loudly that the gate "
            f"lifted by itself."
        )
        world.trace.append("Kindness opened the gate when the purse fell short.")
    else:
        extra = (
            f"The keeper nodded when Luna paid {params.price} currants. "
            f'"You paid the price," he said, "but the currant you shared is the '
            f"true coin of this road.\""
        )
        world.trace.append("Luna paid the price after sharing a currant.")
    story += "\n\n" + extra

    story += (
        f"\n\nBeyond the gate lay {quest.obstacle}. Luna raised her tool and "
        f"hew-hewed through it {params.hew_count} mighty time"
        f"{'' if params.hew_count == 1 else 's'}; each stroke sounded like a "
        f"drumbeat in the sky. {params.helper_name} pulled the loose branches "
        f"aside, and together they reached {quest.reward}."
    )
    world.trace.append(f"{luna.label} completed {params.hew_count} hew strokes.")
    luna.meters["distance"] += 1.0
    luna.memes["courage"] += 2.0

    story += (
        f"\n\nLuna lifted {quest.reward}, but it felt light compared with the "
        f"warmth in her chest. The keeper returned her empty purse and bowed. "
        f'"Remember," he said, "the price of a journey is counted in currants, '
        f"but its Moral Value is counted in whom you help.\""
    )
    story += (
        f"\n\nLuna and {params.helper_name} walked home under a sky enormous "
        f"enough to hold a hundred moons. The robin flew above them, carrying "
        f"the last sweet smell of currant, and Luna knew that {quest.moral}"
    )

    world.facts["remaining_currants"] = currants.amount
    world.facts["success"] = True

    sample = StorySample(
        params=params,
        story=story,
        prompts=[
            f"Tell a Tall Tale about {params.luna_name}'s quest to {quest.place}.",
            f"Include currant, hew, and a price of {params.price}.",
            f"Show that Moral Value matters more than the reward.",
        ],
        story_qa=[
            QAItem(
                "What did Luna carry at the beginning?",
                f"Luna carried {params.currant_amount} currants in her pocket.",
            ),
            QAItem(
                "What was the price of passage?",
                f"The price was {params.price} currants.",
            ),
            QAItem(
                "Why did the gate open?",
                "The gate opened because Luna helped the hungry robin and showed kindness.",
            ),
            QAItem(
                "What did Luna hew through?",
                f"Luna hewed through {quest.obstacle}.",
            ),
            QAItem(
                "What was the story's Moral Value?",
                f"The Moral Value was that {quest.moral}",
            ),
        ],
        world_qa=[
            QAItem(
                "What is a currant?",
                "A currant is a small berry that can be sweet and tart.",
            ),
            QAItem(
                "What does hew mean?",
                "To hew means to cut or chop something with strong repeated strokes.",
            ),
            QAItem(
                "What is a price?",
                "A price is what someone must give to receive something.",
            ),
            QAItem(
                "What is moral value?",
                "Moral value is the goodness or importance of a choice, such as helping someone.",
            ),
        ],
        world=world,
    )
    return sample


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("\n== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for character in world.characters.values():
        lines.append(
            f"{character.label}: meters={character.meters}, memes={character.memes}"
        )
    for resource in world.resources.values():
        lines.append(f"{resource.label}: amount={resource.amount}, value={resource.value}")
    lines.extend(f"event: {event}" for event in world.trace)
    return "\n".join(lines)


def asp_program(params: Optional[StoryParams] = None) -> str:
    facts = [
        f"currant_amount({params.currant_amount if params else 5}).",
        f"price({params.price if params else 3}).",
        f"hew_count({params.hew_count if params else 2}).",
        "moral(kindness).",
    ]
    return "\n".join(facts) + "\n" + ASP_RULES


def asp_check(params: StoryParams) -> bool:
    try:
        import asp
    except ImportError:
        return True
    model = asp.one_model(asp_program(params) + "#show quest_success/0.")
    return bool(asp.atoms(model, "quest_success"))


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

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        rng = random.Random(args.seed)
        for _ in range(10):
            params = resolve_params(build_parser().parse_args([]), rng)
            sample = generate(params)
            if not sample.story or not asp_check(params):
                raise SystemExit("verification failed")
        print("OK: Python stories and ASP quest checks agree.")
        return

    if args.asp:
        print(asp_program())
        return

    rng = random.Random(args.seed)
    samples: list[StorySample] = []

    if args.all:
        for quest_name in sorted(QUESTS):
            params = StoryParams(
                luna_name="Luna",
                helper_name="Pip",
                currant_amount=6,
                hew_count=2,
                price=3,
                quest=quest_name,
            )
            samples.append(generate(params))
    else:
        for _ in range(args.n):
            samples.append(generate(resolve_params(args, rng)))

    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if index:
            print("\n" + "=" * 70 + "\n")
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### quest {index + 1}" if len(samples) > 1 else "",
        )


if __name__ == "__main__":
    main()
