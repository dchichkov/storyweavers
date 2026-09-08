#!/usr/bin/env python3
"""
A nursery-rhyme storyworld about muscle, patter, and gay color.

The little rhyme begins with a boast, turns when a bright parade goes awry,
and resolves through a spoken reconciliation in which strength becomes useful
only when joined with kindness.
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


METERS = {"strength": "physical muscle", "noise": "patter and clatter", "color": "gay brightness"}
MEMES = {"pride": "boasting pride", "hurt": "hurt feelings", "trust": "shared trust"}


@dataclass
class Creature:
    id: str
    label: str
    kind: str
    meters: dict[str, float] = field(default_factory=lambda: {k: 0.0 for k in METERS})
    memes: dict[str, float] = field(default_factory=lambda: {k: 0.0 for k in MEMES})


@dataclass
class Garden:
    place: str
    creatures: dict[str, Creature] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {k: 0.0 for k in METERS})
    memes: dict[str, float] = field(default_factory=lambda: {k: 0.0 for k in MEMES})


@dataclass
class StoryParams:
    hero_name: str
    friend_name: str
    place: str
    seed: Optional[int] = None


HERO_NAMES = ["Milo", "Lulu", "Pip", "Nina", "Bram", "Tess"]
FRIEND_NAMES = ["Dot", "Merry", "Clover", "Poppy", "Wren", "Sunny"]
PLACES = ["the tulip lane", "the moonlit garden", "the buttercup hill", "the little village green"]


@dataclass(frozen=True)
class VerseArc:
    id: str
    object_name: str
    object_plural: str
    boast: str
    omen: str
    trouble: str
    repair: str
    ending: str


ARCS = [
    VerseArc(
        "ribbon_cart",
        "ribbon cart",
        "ribbons",
        "my muscle can pull the grandest cart",
        "a loose wheel gave a tiny squeak",
        "the cart bumped the brook and spilled its gay ribbons",
        "held the axle steady while Dot tied the wheel with a soft green bow",
        "gay ribbons danced again, and every child received a bright one",
    ),
    VerseArc(
        "drum_bridge",
        "little drum",
        "drums",
        "my muscle can beat the boldest drum",
        "the bridge boards trembled under the patter",
        "the drum rolled away and startled the ducklings",
        "used careful strength to stop the drum while Poppy guided the ducklings home",
        "the ducklings quacked in time as the drum made a gentle beat",
    ),
    VerseArc(
        "flower_basket",
        "flower basket",
        "flowers",
        "my muscle can lift the biggest basket",
        "one handle frayed beneath a spray of gay flowers",
        "the basket tipped and scattered blossoms over the path",
        "lifted from below while Clover gathered each blossom into a new basket",
        "gay flowers crowned the gate without one petal lost",
    ),
    VerseArc(
        "kite_pole",
        "kite pole",
        "kites",
        "my muscle can raise the tallest kite",
        "a sharp wind tugged twice at the old pole",
        "the pole leaned toward the nursery roof",
        "lowered it slowly while Wren loosened the tangled kite string",
        "gay kites floated safely above the green",
    ),
    VerseArc(
        "lantern_train",
        "lantern train",
        "lanterns",
        "my muscle can carry the longest train",
        "the patter of rain began on the tin awning",
        "the front lantern went dark and the line lost its way",
        "carried the lanterns under the awning while Sunny relit the first one",
        "gay lanterns glowed like stars along the dry path",
    ),
    VerseArc(
        "painted_gate",
        "paint pot",
        "paint pots",
        "my muscle can swing the widest paint pot",
        "a blue drop trembled at the rim",
        "the pot splashed across the gate and covered the small gold sun",
        "held the pot still while Merry painted a new sun beside the blue splash",
        "the gate shone gay with blue sky and two golden suns",
    ),
]


ASP_RULES = r"""
needs_repair :- parade, loose_part.
can_reconcile :- needs_repair, helper, apology, helpful_strength.
valid_story :- can_reconcile.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("parade"),
        asp.fact("loose_part"),
        asp.fact("helper"),
        asp.fact("apology"),
        asp.fact("helpful_strength"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import asp
    return bool(asp.atoms(asp.one_model(asp_program("#show valid_story/0.")), "valid_story"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A nursery rhyme about muscle, patter, and gay color.")
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
    return StoryParams(
        hero_name=args.name or rng.choice(HERO_NAMES),
        friend_name=args.friend or rng.choice(FRIEND_NAMES),
        place=args.place or rng.choice(PLACES),
        seed=rng.randrange(2**31),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name not in HERO_NAMES:
        raise StoryError("The rhyme needs a known little hero.")
    if params.friend_name not in FRIEND_NAMES:
        raise StoryError("The friend must be a known helper.")
    if params.place not in PLACES:
        raise StoryError("The parade needs a known place.")
    if params.hero_name == params.friend_name:
        raise StoryError("The hero and friend must be different characters.")


def make_world(params: StoryParams) -> Garden:
    world = Garden(params.place)
    world.creatures["hero"] = Creature("hero", params.hero_name, "child")
    world.creatures["friend"] = Creature("friend", params.friend_name, "child")
    world.facts.update({
        "hero_name": params.hero_name,
        "friend_name": params.friend_name,
        "place": params.place,
        "parade": True,
        "loose_part": True,
        "helper": True,
        "apology": False,
        "helpful_strength": False,
        "reconciled": False,
    })
    return world


def opening(world: Garden, arc: VerseArc) -> str:
    hero = world.facts["hero_name"]
    world.meters["strength"] = 1
    world.memes["pride"] = 1
    return (
        f"In {world.place}, {hero} marched with a muscle so strong, "
        f"and sang this bright little song: “{arc.boast}!”"
    )


def foreshadow(world: Garden, arc: VerseArc) -> str:
    world.meters["noise"] = 1
    world.memes["worry"] = world.memes.get("worry", 0) + 1
    return f"But listen close—beneath the gay flags came a warning: {arc.omen}."


def dialogue(world: Garden, arc: VerseArc) -> str:
    hero = world.facts["hero_name"]
    friend = world.facts["friend_name"]
    world.memes["hurt"] = 1
    return (
        f'“Do not pull so hard,” said {friend}. “The parade belongs to all of us.” '
        f'“I only wished to help,” said {hero}. “Then use your muscle gently,” said {friend}.'
    )


def turn(world: Garden, arc: VerseArc) -> str:
    hero = world.facts["hero_name"]
    friend = world.facts["friend_name"]
    world.facts["apology"] = True
    world.facts["helpful_strength"] = True
    world.meters["strength"] = 0
    world.meters["noise"] = 0
    world.memes["pride"] = 0
    world.memes["trust"] = 1
    return (
        f"{arc.trouble.capitalize()}. {hero} stopped, took a breath, and said, "
        f'“I am sorry, {friend}. Will you help me mend it?” '
        f"{friend} nodded. Together they {arc.repair}."
    )


def ending(world: Garden, arc: VerseArc) -> str:
    hero = world.facts["hero_name"]
    friend = world.facts["friend_name"]
    world.facts["reconciled"] = True
    return (
        f"{arc.ending.capitalize()}. {hero} and {friend} smiled side by side, "
        f"for a strong hand is happiest when it helps a friend."
    )


def tell_story(params: StoryParams) -> Garden:
    world = make_world(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    arc = rng.choice(ARCS)
    world.facts["arc"] = arc
    parts = [
        opening(world, arc),
        foreshadow(world, arc),
        dialogue(world, arc),
        turn(world, arc),
        ending(world, arc),
    ]
    world.facts["story"] = "\n\n".join(parts)
    world.facts["arc_id"] = arc.id
    return world


def prompts(world: Garden) -> list[str]:
    return [
        'Write a nursery rhyme using the words "muscle", "patter", and "gay".',
        f"Tell a rhyme about {world.facts['hero_name']} and {world.facts['friend_name']} in {world.place}.",
        "Use reconciliation to turn a boast into a helpful friendship.",
    ]


def story_qa(world: Garden) -> list[QAItem]:
    arc: VerseArc = world.facts["arc"]
    hero = world.facts["hero_name"]
    friend = world.facts["friend_name"]
    return [
        QAItem(
            f"What did {hero} boast about at the start of the rhyme?",
            f"{hero} boasted that {arc.boast}.",
        ),
        QAItem(
            f"What warning came before the trouble in {world.place}?",
            f"The warning was that {arc.omen}.",
        ),
        QAItem(
            f"How did {hero} and {friend} reconcile after the trouble?",
            f"{hero} apologized and asked {friend} to help. Together they {arc.repair}.",
        ),
        QAItem(
            "What showed that the friendship was repaired?",
            f"{arc.ending.capitalize()} Then the two friends smiled side by side.",
        ),
    ]


def world_qa(world: Garden) -> list[QAItem]:
    return [
        QAItem("What is muscle?", "Muscle is the soft body tissue that helps a person move and lift."),
        QAItem("What does patter mean?", "Patter is a light, quick tapping sound, like rain on a roof."),
        QAItem("What does gay mean in this rhyme?", "Here, gay means bright, cheerful, and full of lively color."),
        QAItem("What is reconciliation?", "Reconciliation is making peace again after people have been hurt or disagreed."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story Q&A ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World Q&A ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: Garden) -> str:
    return "\n".join([
        "--- trace ---",
        f"place={world.place}",
        f"facts={world.facts}",
        f"meters={world.meters}",
        f"memes={world.memes}",
    ])


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.facts["story"],
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


def asp_verify() -> int:
    import asp
    if asp_valid() is not True:
        print("MISMATCH between ASP and Python gate.")
        return 1
    sample = generate(StoryParams("Milo", "Dot", PLACES[0], 4))
    if not all(word in sample.story for word in ("muscle", "patter", "gay")):
        return 1
    if not sample.world.facts["reconciled"]:
        return 1
    print("OK: ASP and Python gates agree.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP gate: valid_story/0 is", "true" if asp_valid() else "false")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("Milo", "Dot", PLACES[0], 11),
            StoryParams("Lulu", "Clover", PLACES[1], 22),
            StoryParams("Bram", "Wren", PLACES[2], 33),
        ]
    else:
        params_list = [
            resolve_params(args, random.Random(base_seed + i))
            for i in range(max(1, args.n))
        ]

    samples = [generate(params) for params in params_list]
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
