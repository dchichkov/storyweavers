#!/usr/bin/env python3
"""
A small rhyming storyworld about a supply, a claim, and the surprise that
sharing can make a happy ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


METERS = {"supply", "need", "joy", "fairness"}
MEMES = {"hope", "worry", "pride", "kindness", "trust"}


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in METERS:
            self.meters.setdefault(key, 0.0)
        for key in MEMES:
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryWorld:
    hero: Entity
    friend: Entity
    place: str
    supply_name: str
    claim: str
    facts: dict[str, object] = field(default_factory=dict)

    def copy(self) -> "StoryWorld":
        return StoryWorld(
            hero=Entity(self.hero.id, self.hero.kind, self.hero.label,
                        dict(self.hero.meters), dict(self.hero.memes)),
            friend=Entity(self.friend.id, self.friend.kind, self.friend.label,
                          dict(self.friend.meters), dict(self.friend.memes)),
            place=self.place,
            supply_name=self.supply_name,
            claim=self.claim,
            facts=dict(self.facts),
        )


@dataclass
class StoryParams:
    hero_name: str
    friend_name: str
    place: str
    seed: Optional[int] = None


HERO_NAMES = ["Luna", "Milo", "Pia", "Toby", "Nia", "Sol"]
FRIEND_NAMES = ["Bram", "Cleo", "Rafi", "Wren", "Ivy", "Ollie"]
PLACES = ["the hilltop fair", "the little moon market", "the village green"]
SUPPLIES = ["a basket of berry buns", "a box of apple tarts", "a bundle of honey cakes"]
CLAIMS = [
    "the whole supply was hers",
    "the first prize should belong to her",
    "the last sweet bun was meant for her",
]


@dataclass(frozen=True)
class Arc:
    ident: str
    omen: str
    need: str
    task: str
    complication: str
    twist: str
    sharing: str
    ending: str
    moral: str


ARCS = [
    Arc(
        "bell_rope",
        "The fair bell rang while the basket gave a wobbly swing.",
        "a hungry band of small birds had found the crumbs below",
        "carry the basket safely to the picnic table",
        "a gust blew one bright bun toward the pond",
        "the so-called hungry birds were tiny ducklings guarding a lost chick",
        "Luna broke each bun in two and fed the ducklings first",
        "the chick's grateful peep led the children to a missing silver bell",
        "A claim may feel big, but kindness makes room for everyone.",
    ),
    Arc(
        "moon_lantern",
        "A moon lantern flickered beside the unopened box.",
        "the night workers had no supper after mending the market stalls",
        "bring the box beneath the lantern's warm light",
        "the path grew dark when a cloud covered the moon",
        "the quiet stranger who offered a candle was the festival baker",
        "Luna shared the tarts and learned that the baker had baked them for all",
        "the market glowed as every helper held a golden lantern",
        "A fair supply is sweeter when no helper is forgotten.",
    ),
    Arc(
        "red_ribbon",
        "A red ribbon fluttered from the bundle like a tiny flag.",
        "a shy child had no treat for the ribbon parade",
        "guard the cakes while the parade crossed the green",
        "the ribbon caught on a thorn and pulled the bundle open",
        "the child was not a rival at all, but the judge's helper carrying the prize list",
        "Luna offered the finest cake and asked the child to choose first",
        "the helper placed a bright ribbon around Luna and her new friend together",
        "The best prize is a generous heart, not the loudest claim.",
    ),
]


ASP_RULES = r"""
needs_help(F) :- friend(F), hungry(F).
can_share(H, F) :- hero(H), friend(F), supply(S), needs_help(F), has_supply(H, S).
kind_choice(H, F) :- can_share(H, F), chooses_share(H, F).
happy_ending(H) :- kind_choice(H, _).
valid_story(H) :- hero(H), supply(S), has_supply(H, S), happy_ending(H).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A rhyming story about a supply, a claim, and sharing."
    )
    parser.add_argument("--name", choices=HERO_NAMES)
    parser.add_argument("--friend", choices=FRIEND_NAMES)
    parser.add_argument("--place", choices=PLACES)
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
    hero = args.name or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([name for name in FRIEND_NAMES if name != hero])
    return StoryParams(
        hero_name=hero,
        friend_name=friend,
        place=args.place or rng.choice(PLACES),
        seed=rng.randrange(2**31),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name not in HERO_NAMES:
        raise StoryError("The hero must be chosen from the known story friends.")
    if params.friend_name not in FRIEND_NAMES:
        raise StoryError("The friend must be chosen from the known story friends.")
    if params.hero_name == params.friend_name:
        raise StoryError("The hero and friend need different names.")
    if params.place not in PLACES:
        raise StoryError("The story needs a known gathering place.")


def make_world(params: StoryParams, arc: Arc, supply: str) -> StoryWorld:
    hero = Entity("hero", "child", params.hero_name)
    friend = Entity("friend", "child", params.friend_name)
    hero.meters["supply"] = 1
    hero.meters["fairness"] = 0
    friend.meters["need"] = 1
    hero.memes["pride"] = 1
    friend.memes["worry"] = 1
    return StoryWorld(
        hero=hero,
        friend=friend,
        place=params.place,
        supply_name=supply,
        claim=CLAIMS[0],
        facts={"arc": arc, "resolved": False},
    )


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("hero", "luna"),
        asp.fact("friend", "friend"),
        asp.fact("supply", "treats"),
        asp.fact("has_supply", "luna", "treats"),
        asp.fact("hungry", "friend"),
        asp.fact("chooses_share", "luna", "friend"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import asp

    model = asp.one_model(asp_program())
    return bool(asp.atoms(model, "valid_story"))


def compose_story(params: StoryParams) -> StoryWorld:
    rng = random.Random(params.seed if params.seed is not None else 0)
    arc = rng.choice(ARCS)
    supply = rng.choice(SUPPLIES)
    world = make_world(params, arc, supply)
    hero = params.hero_name
    friend = params.friend_name

    intro = (
        f"At {params.place}, {hero} held {supply}. "
        f'"This supply is mine," came the claim, with a proud little rhyme.'
    )
    omen = f"{arc.omen} It hinted that {arc.need}."
    dialogue = (
        f'"Is the supply all for you?" asked {friend}, feeling blue. '
        f'"I thought so," said {hero}. "But what should kind hearts do?" '
        f'"Let us {arc.task}," said {friend}.'
    )
    action = (
        f"{hero} stepped lightly, though the fair wind blew brightly. "
        f"First came trouble: {arc.complication} "
        f"Then came the twist: {arc.twist}. "
        f"{hero} paused, saw the truth, and changed the claim."
    )

    world.facts["claim_before"] = world.claim
    world.facts["dialogue"] = dialogue
    world.facts["twist"] = arc.twist
    world.facts["task"] = arc.task

    world.hero.meters["fairness"] = 1
    world.hero.memes["pride"] = 0
    world.hero.memes["kindness"] = 1
    world.hero.memes["trust"] = 1
    world.friend.meters["need"] = 0
    world.friend.memes["worry"] = 0
    world.friend.memes["hope"] = 1
    world.facts["resolved"] = True

    resolution = (
        f"So {hero} said, \"The supply can be shared today!\" "
        f"{arc.sharing}. {arc.ending}. "
        f"That happy ending sang in a bright, bouncing way: {arc.moral}"
    )
    world.facts["story"] = "\n\n".join([intro, omen, dialogue, action, resolution])
    return world


def prompts(world: StoryWorld) -> list[str]:
    return [
        'Write a rhyming story using the words "supply" and "claim".',
        f"Tell how {world.hero.label} learns whether a claim about {world.supply_name} is fair.",
        "Include a twist, a happy ending, and a moral value about sharing.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    arc: Arc = world.facts["arc"]
    hero = world.hero.label
    friend = world.friend.label
    return [
        QAItem(
            question=f"What supply did {hero} carry at {world.place}?",
            answer=f"{hero} carried {world.supply_name} at {world.place}, and first claimed that the whole supply was hers.",
        ),
        QAItem(
            question=f"What did {friend} ask {hero} about the claim?",
            answer=f"{friend} asked whether the supply was all for {hero}, then suggested that they {arc.task}.",
        ),
        QAItem(
            question="What twist changed the way the claim looked?",
            answer=f"The twist was that {arc.twist}. This showed that the problem needed kindness rather than a proud claim.",
        ),
        QAItem(
            question=f"How did {hero} create a happy ending for {friend}?",
            answer=f"{hero} shared the supply. {arc.sharing}, and {arc.ending}.",
        ),
    ]


def world_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a supply?",
            answer="A supply is something kept ready for use, such as food, water, or helpful materials.",
        ),
        QAItem(
            question="What is a claim?",
            answer="A claim is something a person says belongs to them or is true; a fair claim should consider other people's needs.",
        ),
        QAItem(
            question="Why is sharing a moral value?",
            answer="Sharing is a moral value because it treats other people kindly and helps everyone receive what they need.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: StoryWorld) -> str:
    return "\n".join(
        [
            "--- trace ---",
            f"place={world.place}",
            f"supply={world.supply_name}",
            f"claim={world.claim}",
            f"hero_meters={world.hero.meters}",
            f"hero_memes={world.hero.memes}",
            f"friend_meters={world.friend.meters}",
            f"friend_memes={world.friend.memes}",
            f"resolved={world.facts.get('resolved')}",
        ]
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = compose_story(params)
    return StorySample(
        params=params,
        story=world.facts["story"],
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_verify() -> int:
    if not asp_valid():
        print("ASP gate rejected the valid sharing story.")
        return 1
    sample = generate(
        StoryParams(
            hero_name="Luna",
            friend_name="Bram",
            place="the village green",
            seed=11,
        )
    )
    checks = [
        "supply" in sample.story,
        "claim" in sample.story,
        "twist" not in sample.story.lower(),
        sample.world is not None and sample.world.facts.get("resolved") is True,
        len(sample.story_qa) == 4,
    ]
    if not all(checks):
        print("Generated story verification failed.")
        return 1
    print("OK: ASP and Python gates agree; generated story checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        print("ASP gate: valid_story/1 is", "true" if asp_valid() else "false")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [
            StoryParams("Luna", "Bram", "the hilltop fair", base_seed),
            StoryParams("Milo", "Cleo", "the little moon market", base_seed + 1),
            StoryParams("Pia", "Wren", "the village green", base_seed + 2),
        ]
    else:
        params_list = []
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params_list.append(resolve_params(args, rng))

    samples = [generate(params) for params in params_list]

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
