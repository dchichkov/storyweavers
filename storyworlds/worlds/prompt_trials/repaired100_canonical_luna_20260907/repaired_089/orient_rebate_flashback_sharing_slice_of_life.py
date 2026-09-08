#!/usr/bin/env python3
"""
Storyworld: orient_rebate_flashback_sharing_slice_of_life

A small slice-of-life world about orienting a shared rebate fairly, remembering
an earlier promise, and letting a quiet conversation repair a household plan.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Person:
    id: str
    name: str
    role: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"confusion": 0.0, "fairness": 0.0, "warmth": 0.0}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"worry": 0.0, "trust": 0.0, "relief": 0.0}
    )


@dataclass
class HouseholdItem:
    id: str
    label: str
    owner: str
    purpose: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"usefulness": 0.0, "shared_value": 0.0}
    )


@dataclass
class StoryParams:
    child_name: str
    neighbor_name: str
    home: str
    purchase: str
    rebate_amount: int
    shared_need: str
    flashback_detail: str
    sharing_place: str
    telling_mode: str = "ordinary"
    seed: Optional[int] = None


CHILD_NAMES = ["Luna", "Mara", "Theo", "Niko", "Ivy", "Pia"]
NEIGHBOR_NAMES = ["Ari", "Jo", "Sam", "Bea", "Mina", "Owen"]

HOMES = [
    "a small apartment above the bakery",
    "a yellow house beside the bus stop",
    "a quiet row house near the library",
    "a cottage at the end of Maple Lane",
    "a second-floor flat overlooking the community garden",
]

PURCHASES = [
    "a new kettle",
    "a repair kit for the washing machine",
    "a box of warm winter bulbs",
    "a sturdy folding table",
    "a set of bicycle lights",
    "a packet of water-saving shower parts",
]

SHARED_NEEDS = [
    "fresh paint for the shared hallway",
    "a new shelf for the lending cupboard",
    "bus tickets for the neighborhood food run",
    "soil for the community garden",
    "a repair fund for the old courtyard bench",
    "snacks for the evening reading circle",
]

FLASHBACKS = [
    "last spring, when the neighbor lent a ladder without asking for anything back",
    "the rainy afternoon when both families carried groceries upstairs together",
    "the winter morning when the household shared its spare heater during a power cut",
    "the day the children made one long chalk road across the courtyard",
    "the summer evening when everyone took turns watering the thirsty garden",
]

SHARING_PLACES = [
    "the kitchen table",
    "the courtyard bench",
    "the library steps",
    "the garden gate",
    "the hallway by the noticeboard",
]

TELLING_MODES = ["ordinary", "flashback-first", "dialogue-first", "evening", "errand"]

REBATE_OPTIONS = [8, 10, 12, 15, 18, 20]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.people: dict[str, Person] = {}
        self.items: dict[str, HouseholdItem] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        paragraphs: list[str] = []
        current: list[str] = []
        for line in self.lines:
            if line == "":
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            paragraphs.append(" ".join(current))
        return "\n\n".join(paragraphs)


def build_world(params: StoryParams) -> World:
    if params.rebate_amount <= 0:
        raise StoryError("rebate_amount must be positive")
    if params.child_name == params.neighbor_name:
        raise StoryError("child_name and neighbor_name must be different")
    if not params.purchase or not params.shared_need:
        raise StoryError("purchase and shared_need must be provided")

    world = World(params)
    child = Person("child", params.child_name, "young household member")
    neighbor = Person("neighbor", params.neighbor_name, "neighbor and friend")
    adult = Person("adult", "Aunt May", "careful household adult")
    item = HouseholdItem("purchase", params.purchase, "household", "a useful household purchase")
    fund = HouseholdItem("shared_fund", params.shared_need, "neighbors", "a small shared need")

    world.people.update(child=child, neighbor=neighbor, adult=adult)
    world.items.update(purchase=item, shared_fund=fund)

    openings = {
        "ordinary": (
            f"On an ordinary afternoon at {params.home}, {params.child_name} found a receipt "
            f"for {params.purchase} beside the kettle."
        ),
        "flashback-first": (
            f"{params.child_name} remembered {params.flashback_detail}. "
            f"That memory returned while a receipt for {params.purchase} rested on the table at {params.home}."
        ),
        "dialogue-first": (
            f'"Is this money meant for one person?" {params.child_name} asked at {params.sharing_place}. '
            f"The question began with a receipt for {params.purchase}."
        ),
        "evening": (
            f"That evening at {params.home}, the light turned gold on a receipt for {params.purchase}. "
            f"{params.child_name} picked it up before clearing the table."
        ),
        "errand": (
            f"After an errand, {params.child_name} returned to {params.home} with a receipt for "
            f"{params.purchase} and a question about the money printed below it."
        ),
    }

    world.say(openings[params.telling_mode])
    world.say(
        f"At the bottom of the receipt, a store rebate promised {params.rebate_amount} dollars back. "
        f"{params.child_name} knew the purchase had helped the household, but the money did not yet have a clear home."
    )
    world.say(
        f"{params.child_name} first thought, 'It could buy a little treat for me,' "
        f"then noticed the note about {params.shared_need} written on the family calendar."
    )
    world.para()

    child.meters["confusion"] += 1
    child.memes["worry"] += 1
    world.say(
        f"{params.child_name} carried the receipt to {params.neighbor_name} at {params.sharing_place}, "
        f"where they were sorting crayons into a shared box."
    )
    world.say(
        f'"The rebate came from our purchase," {params.child_name} said, "but the purchase helped us both. '
        f'How can I tell what would be fair?"'
    )
    world.say(
        f'"Let us orient ourselves before we divide anything," {params.neighbor_name} replied. '
        f'"We can name who paid, who used the item, and what promise is still waiting."'
    )
    world.say(
        f"The calm question made the small problem feel less like a contest and more like something they could examine together."
    )
    world.para()

    world.say(
        f"Then {params.child_name} had a flashback: {params.flashback_detail}. "
        f"In that memory, nobody kept a careful score; each person noticed what the others needed."
    )
    world.say(
        f'"I remember how you helped then," {params.child_name} said. '
        f'"Maybe sharing this rebate can help the promise on our calendar."'
    )
    world.say(
        f"{params.neighbor_name} read the receipt closely. The rebate was linked to {params.purchase}, "
        f"so they decided not to pretend it belonged to only one person."
    )
    child.meters["confusion"] -= 1
    child.meters["fairness"] += 1
    neighbor.meters["fairness"] += 1
    neighbor.memes["trust"] += 1
    world.para()

    world.say(
        f"Together, they oriented the money toward {params.shared_need}: "
        f"some would cover the shared need, and the rest would remain with the household for the item that earned the rebate."
    )
    world.say(
        f"{params.neighbor_name} offered to write the plan on the noticeboard, while {params.child_name} "
        f"placed the receipt in an envelope so nobody would have to remember the numbers alone."
    )
    world.say(
        f'"This is not exactly equal in coins," {params.child_name} said. '
        f'"But it is fair because the plan follows what the money came from and what we promised to share."'
    )
    world.say(
        f'"That is a good way to orient a choice," said Aunt May when she joined them. '
        f'"Use clear facts, remember kindness, and make the next step visible."'
    )
    world.para()

    item.meters["shared_value"] += 1
    fund.meters["usefulness"] += 1
    child.meters["warmth"] += 1
    neighbor.meters["warmth"] += 1
    child.memes["relief"] += 1
    neighbor.memes["relief"] += 1

    world.say(
        f"The plan worked. The shared part of the {params.rebate_amount}-dollar rebate went toward "
        f"{params.shared_need}, and the household kept the remainder for {params.purchase}."
    )
    world.say(
        f"At {params.sharing_place}, {params.child_name} and {params.neighbor_name} added their names beneath the plan. "
        f"The receipt no longer looked like a loose prize; it looked like a bridge between an old kindness and a new promise."
    )
    world.say(
        f"{params.child_name} learned that sharing does not always mean splitting a thing into identical pieces. "
        f"It can mean orienting people toward the need, the history, and the trust held by everyone involved."
    )
    world.say(
        f'"Next time a rebate appears," {params.child_name} said, "I will ask what it is connected to before I decide what it means."'
    )
    world.say(
        f'{params.neighbor_name} smiled. "And I will help you look. That is part of sharing too."'
    )
    world.say(
        f"By the next morning, the noticeboard showed the plan clearly, and a fresh line beside it named the first small improvement made for {params.shared_need}."
    )

    world.facts.update(
        child=child,
        neighbor=neighbor,
        adult=adult,
        purchase=item,
        shared_fund=fund,
        rebate=params.rebate_amount,
        flashback=params.flashback_detail,
        sharing_place=params.sharing_place,
        shared_need=params.shared_need,
        purchase_label=params.purchase,
        resolution=(
            f"the shared part of the {params.rebate_amount}-dollar rebate went toward "
            f"{params.shared_need}, while the household kept the remainder for {params.purchase}"
        ),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Person = f["child"]
    neighbor: Person = f["neighbor"]
    return [
        f"Write a slice-of-life story about {child.name} and {neighbor.name} learning how to share a rebate fairly.",
        f"Tell a gentle story in which {child.name} uses a flashback about {f['flashback']} to orient a decision about {f['purchase_label']}.",
        f"Write a warm household story where a {f['rebate']}-dollar rebate becomes connected to {f['shared_need']} through an honest conversation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Person = f["child"]
    neighbor: Person = f["neighbor"]
    return [
        QAItem(
            question=f"Why was {child.name} unsure what to do with the rebate?",
            answer=(
                f"{child.name} was unsure because the rebate came from {f['purchase_label']}, "
                f"which helped the household, while the calendar named {f['shared_need']} as a shared need."
            ),
        ),
        QAItem(
            question=f"How did {neighbor.name} help {child.name} orient the decision?",
            answer=(
                f"{neighbor.name} helped by asking them to name who paid, who used the purchase, "
                f"and what promise was still waiting. Those facts gave the rebate a fair direction."
            ),
        ),
        QAItem(
            question="What did the flashback remind the children?",
            answer=(
                f"The flashback reminded them of {f['flashback']}. "
                f"It showed that kindness and shared needs mattered more than keeping a strict score."
            ),
        ),
        QAItem(
            question="How was the rebate shared?",
            answer=f"The shared part of the rebate went toward {f['shared_need']}, while the household kept the remainder for {f['purchase_label']}.",
        ),
        QAItem(
            question="What final image shows that the plan became real?",
            answer=(
                f"The noticeboard showed the plan clearly, with a fresh line naming the first small improvement "
                f"made for {f['shared_need']}. The written plan proved that the conversation had become action."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does orient mean?",
            answer="To orient means to help someone understand where they are, what matters, or which direction to take.",
        ),
        QAItem(
            question="What is a rebate?",
            answer="A rebate is money returned after a purchase, often because a store or maker offers part of the price back.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means allowing others to use, receive, or benefit from something in a thoughtful and fair way.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a moment when a story returns to something that happened earlier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for person in world.people.values():
        lines.append(
            f"{person.id}: name={person.name} role={person.role} "
            f"meters={dict(person.meters)} memes={dict(person.memes)}"
        )
    for item in world.items.values():
        lines.append(
            f"{item.id}: label={item.label} owner={item.owner} purpose={item.purpose} "
            f"meters={dict(item.meters)}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
oriented_rebate_story(S) :-
    story(S),
    rebate_exists(S),
    facts_checked(S),
    shared_plan(S),
    respectful_exchange(S).

rebate_exists(S) :- story(S), rebate(S).
facts_checked(S) :- story(S), payment_context(S), need_named(S).
shared_plan(S) :- story(S), sharing_choice(S).
respectful_exchange(S) :- story(S), dialogue(S).
"""


def asp_facts(params: StoryParams) -> str:
    import asp

    if params.rebate_amount <= 0:
        raise StoryError("ASP facts require a positive rebate amount")
    return "\n".join(
        [
            asp.fact("story", "s1"),
            asp.fact("rebate", "s1"),
            asp.fact("payment_context", "s1"),
            asp.fact("need_named", "s1"),
            asp.fact("sharing_choice", "s1"),
            asp.fact("dialogue", "s1"),
        ]
    )


def asp_program() -> str:
    params = StoryParams(
        child_name="Luna",
        neighbor_name="Ari",
        home=HOMES[0],
        purchase=PURCHASES[0],
        rebate_amount=12,
        shared_need=SHARED_NEEDS[0],
        flashback_detail=FLASHBACKS[0],
        sharing_place=SHARING_PLACES[0],
    )
    return f"{asp_facts(params)}\n{ASP_RULES}\n#show oriented_rebate_story/1.\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "oriented_rebate_story"))
    if found != {("s1",)}:
        print("MISMATCH: ASP did not recognize the oriented rebate story.")
        return 1

    params = StoryParams(
        child_name="Luna",
        neighbor_name="Ari",
        home=HOMES[0],
        purchase=PURCHASES[0],
        rebate_amount=12,
        shared_need=SHARED_NEEDS[0],
        flashback_detail=FLASHBACKS[0],
        sharing_place=SHARING_PLACES[0],
        seed=7,
    )
    sample = generate(params)
    required = ["rebate", "orient", "sharing", "flashback"]
    lowered = sample.story.lower()
    missing = [word for word in required if word not in lowered]
    if missing:
        print("MISMATCH: generated story is missing " + ", ".join(missing))
        return 1
    if not sample.story_qa or not sample.world_qa:
        print("MISMATCH: generated story lacks QA.")
        return 1
    print("OK: ASP gate, Python world, prose, and QA agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Slice-of-life story world about orienting and sharing a rebate."
    )
    parser.add_argument("--child-name")
    parser.add_argument("--neighbor-name")
    parser.add_argument("--home")
    parser.add_argument("--purchase")
    parser.add_argument("--rebate-amount", type=int)
    parser.add_argument("--shared-need")
    parser.add_argument("--flashback-detail")
    parser.add_argument("--sharing-place")
    parser.add_argument("--telling-mode", choices=TELLING_MODES)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    neighbor_name = args.neighbor_name or rng.choice(
        [name for name in NEIGHBOR_NAMES if name != child_name]
    )
    rebate_amount = args.rebate_amount if args.rebate_amount is not None else rng.choice(REBATE_OPTIONS)
    if rebate_amount <= 0:
        raise StoryError("--rebate-amount must be positive")
    return StoryParams(
        child_name=child_name,
        neighbor_name=neighbor_name,
        home=args.home or rng.choice(HOMES),
        purchase=args.purchase or rng.choice(PURCHASES),
        rebate_amount=rebate_amount,
        shared_need=args.shared_need or rng.choice(SHARED_NEEDS),
        flashback_detail=args.flashback_detail or rng.choice(FLASHBACKS),
        sharing_place=args.sharing_place or rng.choice(SHARING_PLACES),
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        child_name="Luna",
        neighbor_name="Ari",
        home="a small apartment above the bakery",
        purchase="a new kettle",
        rebate_amount=12,
        shared_need="a new shelf for the lending cupboard",
        flashback_detail="the rainy afternoon when both families carried groceries upstairs together",
        sharing_place="the kitchen table",
        telling_mode="flashback-first",
    ),
    StoryParams(
        child_name="Mara",
        neighbor_name="Jo",
        home="a quiet row house near the library",
        purchase="a sturdy folding table",
        rebate_amount=18,
        shared_need="snacks for the evening reading circle",
        flashback_detail="the summer evening when everyone took turns watering the thirsty garden",
        sharing_place="the library steps",
        telling_mode="dialogue-first",
    ),
    StoryParams(
        child_name="Theo",
        neighbor_name="Bea",
        home="a cottage at the end of Maple Lane",
        purchase="a set of bicycle lights",
        rebate_amount=10,
        shared_need="bus tickets for the neighborhood food run",
        flashback_detail="the winter morning when the household shared its spare heater during a power cut",
        sharing_place="the garden gate",
        telling_mode="evening",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print(model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 20):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

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
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
