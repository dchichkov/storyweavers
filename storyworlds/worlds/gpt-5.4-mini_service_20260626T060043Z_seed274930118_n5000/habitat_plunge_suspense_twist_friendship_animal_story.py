#!/usr/bin/env python3
"""
A small storyworld about an animal in a habitat, a brave plunge, a suspenseful
twist, and a friendship ending.

The premise is a child-facing Animal Story style tale: a little animal wants to
plunge into a habitat pool, something surprising interrupts the plan, and a
friend helps turn worry into a happy ending.
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
class Creature:
    id: str
    species: str
    label: str
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        table = {
            "subject": "it",
            "object": "it",
            "possessive": "its",
        }
        return table[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Habitat:
    id: str
    name: str
    water: str
    shelter: str
    splashy: bool = True


@dataclass
class Venture:
    id: str
    verb: str
    gerund: str
    rush: str
    suspense: str
    twist: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Friend:
    id: str
    label: str
    species: str
    helpful: bool = True


@dataclass
class StoryParams:
    habitat: str
    venture: str
    creature: str
    friend: str
    seed: Optional[int] = None


HABITATS = {
    "pond": Habitat(
        id="pond",
        name="the pond",
        water="clear water",
        shelter="reeds",
        splashy=True,
    ),
    "riverbank": Habitat(
        id="riverbank",
        name="the riverbank",
        water="cool current",
        shelter="tall grass",
        splashy=True,
    ),
    "lagoon": Habitat(
        id="lagoon",
        name="the lagoon",
        water="still water",
        shelter="mangrove roots",
        splashy=True,
    ),
}

VENTURES = {
    "plunge": Venture(
        id="plunge",
        verb="plunge into the water",
        gerund="plunging into the water",
        rush="rush to the edge",
        suspense="the ripples kept getting bigger and bigger",
        twist="a tiny helper was already there",
        tags={"water", "plunge", "suspense", "twist"},
    ),
    "splash": Venture(
        id="splash",
        verb="splash around",
        gerund="splashing around",
        rush="dash to the shallow water",
        suspense="a shadow moved under the lilies",
        twist="the shadow was only a floating leaf",
        tags={"water", "suspense", "twist"},
    ),
}

CREATURES = {
    "otter": Creature(id="otter", species="otter", label="little otter"),
    "duck": Creature(id="duck", species="duck", label="small duck"),
    "turtle": Creature(id="turtle", species="turtle", label="young turtle"),
    "frog": Creature(id="frog", species="frog", label="tiny frog"),
}

FRIENDS = {
    "heron": Friend(id="heron", label="a patient heron", species="heron"),
    "fish": Friend(id="fish", label="a shiny fish", species="fish"),
    "crab": Friend(id="crab", label="a brave crab", species="crab"),
    "beetle": Friend(id="beetle", label="a busy beetle", species="beetle"),
}

CURATED = [
    StoryParams(habitat="pond", venture="plunge", creature="otter", friend="fish"),
    StoryParams(habitat="riverbank", venture="splash", creature="duck", friend="crab"),
    StoryParams(habitat="lagoon", venture="plunge", creature="frog", friend="heron"),
]


@dataclass
class World:
    habitat: Habitat
    venture: Venture
    creature: Creature
    friend: Friend
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def say(self, line: str) -> None:
        self.trace.append(line)

    def render(self) -> str:
        parts = []
        paragraph = []
        for line in self.trace:
            if line == "":
                if paragraph:
                    parts.append(" ".join(paragraph))
                    paragraph = []
            else:
                paragraph.append(line)
        if paragraph:
            parts.append(" ".join(paragraph))
        return "\n\n".join(parts)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal Story world: habitat, plunge, suspense, twist, friendship."
    )
    ap.add_argument("--habitat", choices=HABITATS)
    ap.add_argument("--venture", choices=VENTURES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hab_choices = list(HABITATS)
    ven_choices = list(VENTURES)
    cre_choices = list(CREATURES)
    fri_choices = list(FRIENDS)

    habitat = args.habitat or rng.choice(hab_choices)
    venture = args.venture or rng.choice(ven_choices)
    creature = args.creature or rng.choice(cre_choices)
    friend = args.friend or rng.choice(fri_choices)

    if args.creature and args.creature not in CREATURES:
        raise StoryError("Unknown creature.")
    if args.friend and args.friend not in FRIENDS:
        raise StoryError("Unknown friend.")

    return StoryParams(habitat=habitat, venture=venture, creature=creature, friend=friend)


def reasonableness_gate(params: StoryParams) -> None:
    if params.venture == "plunge" and params.habitat not in HABITATS:
        raise StoryError("The plunge needs a real habitat.")
    if params.creature not in CREATURES or params.friend not in FRIENDS:
        raise StoryError("Invalid story cast.")


def build_world(params: StoryParams) -> World:
    habitat = HABITATS[params.habitat]
    venture = VENTURES[params.venture]
    creature = CREATURES[params.creature]
    friend = FRIENDS[params.friend]
    world = World(habitat=habitat, venture=venture, creature=creature, friend=friend)

    creature.meters["curiosity"] = 1.0
    creature.memes["hope"] = 1.0
    world.meters["water"] = 0.0
    world.memes["suspense"] = 0.0

    world.say(f"At {habitat.name}, a {creature.label} watched the {habitat.water} near the {habitat.shelter}.")
    world.say(f"{creature.pronoun().capitalize()} loved {venture.gerund}, because the habitat looked soft and safe.")
    world.say("")
    world.say(f"One afternoon, {creature.label} {venture.rush} to make a big {venture.id}.")
    world.say(f"But then {venture.suspense}, and the little animal froze.")
    world.memes["suspense"] += 1.0

    # tension and twist
    if venture.id == "plunge":
        world.say(f"Just before the splash, {venture.twist}. It was {friend.label}, peeking from the reeds.")
        creature.memes["fear"] = 1.0
        world.memes["suspense"] += 1.0
        world.say(f"{friend.label.capitalize()} did not laugh. Instead, {friend.label} nudged a safe lily pad toward the water.")
        creature.memes["fear"] = 0.0
        creature.memes["joy"] = 1.0
        creature.memes["friendship"] = 1.0
        world.say(f"{creature.label} smiled, and together they made a careful plunge beside the lily pad.")
        world.say(f"The water sparkled, and the habitat felt friendly instead of frightening.")
    else:
        world.say(f"Then {venture.twist}. It was {friend.label}, carrying a tiny leaf boat.")
        creature.memes["fear"] = 1.0
        world.say(f"{friend.label.capitalize()} showed where the shallow water was calm, and the worry floated away.")
        creature.memes["joy"] = 1.0
        creature.memes["friendship"] = 1.0
        world.say(f"At the end, {creature.label} and {friend.label} splashed together and shared the quiet pond light.")

    world.facts = {
        "habitat": habitat,
        "venture": venture,
        "creature": creature,
        "friend": friend,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an Animal Story about a {f["creature"].species} in {f["habitat"].name} that includes the word "habitat".',
        f"Tell a gentle suspense story where {f['creature'].label} wants to {f['venture'].verb} but meets a surprise friend.",
        f'Write a short story with a twist, a plunge, and a friendship ending near {f["habitat"].name}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["creature"]
    h = world.facts["habitat"]
    v = world.facts["venture"]
    f = world.facts["friend"]
    return [
        QAItem(
            question=f"Where did {c.label} want to {v.verb}?",
            answer=f"{c.label.capitalize()} wanted to {v.verb} at {h.name}, right beside the {h.water}.",
        ),
        QAItem(
            question=f"What made the moment suspenseful for {c.label}?",
            answer=f"It was suspenseful because {v.suspense} and {c.label} had to stop and look around.",
        ),
        QAItem(
            question=f"Who turned the scary moment into a friendly one?",
            answer=f"{f.label.capitalize()} helped turn the moment into friendship by guiding {c.label} safely.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {f.label} was already there and helped instead of causing trouble.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a habitat?",
            answer="A habitat is the natural home where an animal lives, finds food, and stays safe.",
        ),
        QAItem(
            question="What does plunge mean?",
            answer="To plunge means to jump or go quickly down into water with a splash.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the worried, wondering feeling when something important might happen soon.",
        ),
        QAItem(
            question="What is a friendship?",
            answer="Friendship is when two living things are kind to each other and enjoy being together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- trace ---"]
    lines.append(f"habitat={world.habitat.name}")
    lines.append(f"venture={world.venture.id}")
    lines.append(f"creature={world.creature.label}")
    lines.append(f"friend={world.friend.label}")
    lines.append(f"meters={world.meters}")
    lines.append(f"memes={world.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/4.
valid(H,V,C,F) :- habitat(H), venture(V), creature(C), friend(F).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for hid in HABITATS:
        lines.append(asp.fact("habitat", hid))
    for vid in VENTURES:
        lines.append(asp.fact("venture", vid))
    for cid in CREATURES:
        lines.append(asp.fact("creature", cid))
    for fid in FRIENDS:
        lines.append(asp.fact("friend", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple]:
    return sorted((h, v, c, f) for h in HABITATS for v in VENTURES for c in CREATURES for f in FRIENDS)


def asp_verify() -> int:
    a = set(asp_valid())
    p = set(python_valid())
    if a == p:
        print(f"OK: clingo gate matches python_valid() ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    print("only in asp:", sorted(a - p))
    print("only in python:", sorted(p - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(python_valid())} compatible stories.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
