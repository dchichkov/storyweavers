#!/usr/bin/env python3
"""
A cautionary nursery-rhyme storyworld about an illusion, a smith, and a roam.
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


METERS = {"light": "light", "distance": "distance", "danger": "danger", "trust": "trust"}
MEMES = {"curiosity": "curiosity", "worry": "worry", "shame": "shame", "relief": "relief"}


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
class World:
    place: str
    hero: Entity
    smith: Entity
    lantern: Entity
    facts: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {k: 0.0 for k in METERS})
    memes: dict[str, float] = field(default_factory=lambda: {k: 0.0 for k in MEMES})


@dataclass
class StoryParams:
    hero_name: str
    smith_name: str
    place: str
    seed: Optional[int] = None


HERO_NAMES = ["Luna", "Milo", "Nell", "Pip", "Tess", "Robin"]
SMITH_NAMES = ["Old Bram", "Mara Smith", "Master Flint", "Aunt Anvil"]
PLACES = ["a blue village", "the moonlit lane", "a little hill town", "the edge of the wood"]

TALES = [
    {
        "id": "silver_gate",
        "object": "a silver gate",
        "illusion": "a shining road that seemed to lead home",
        "danger": "the bright road was only moonlight on wet stones",
        "roam": "roamed past the mill and down the bramble lane",
        "turn": "asked the smith to test the road with a ringing hammer",
        "proof": "the hammer rang on true stone, while the shining path faded in the puddle",
        "ending": "Luna walked home by the real road, with the smith beside her and the lantern held low",
    },
    {
        "id": "golden_bird",
        "object": "a golden bird",
        "illusion": "a gold bird fluttering above the roof",
        "danger": "the bird was a bright leaf spinning toward the thorn hedge",
        "roam": "roamed beyond the baker's bell and under the crooked trees",
        "turn": "called to the smith before chasing the glittering shape",
        "proof": "the smith's bell woke the hedge, and the false bird fell silent as a leaf",
        "ending": "the child returned with a real feather, not a scraped knee, tucked beside the lantern",
    },
    {
        "id": "copper_crown",
        "object": "a copper crown",
        "illusion": "a crown gleaming at the far end of the common",
        "danger": "the crown was a fox's eyes shining between the reeds",
        "roam": "roamed across the common and toward the whispering marsh",
        "turn": "stopped at the smith's warning and watched before taking another step",
        "proof": "the fox slipped away, and the smith's copper crown shone safely on the workbench",
        "ending": "the child came home before dusk, wiser than a boast and safer than a rush",
    },
]

DIALOGUES = [
    ('"A crown!" cried {hero}.', '"Not so fast," said {smith}. "An illusion can glitter and still be a lie."'),
    ('"That road is calling me," said {hero}.', '"Roads do not call," replied {smith}. "Tell me what your eyes truly know."'),
    ('"{smith}, I must roam and catch it!" said {hero}.', '"First ask, then act," said {smith}. "A bright mistake can lead to a dark place."'),
]

ASP_RULES = r"""
needs_careful_check(P) :- has_illusion(P), has_smith(P), has_roam(P).
valid_story(P) :- needs_careful_check(P), cautionary(P), misunderstanding(P).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A cautionary nursery rhyme about illusion, smith, and roam.")
    parser.add_argument("--name", choices=HERO_NAMES)
    parser.add_argument("--smith", choices=SMITH_NAMES)
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
        smith_name=args.smith or rng.choice(SMITH_NAMES),
        place=args.place or rng.choice(PLACES),
        seed=rng.randrange(2**31),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name not in HERO_NAMES:
        raise StoryError("The child must have a name from the village roll.")
    if params.smith_name not in SMITH_NAMES:
        raise StoryError("The smith must be a known keeper of careful tools.")
    if params.place not in PLACES:
        raise StoryError("The rhyme needs a known little place.")


def make_world(params: StoryParams) -> World:
    return World(
        place=params.place,
        hero=Entity("hero", "child", params.hero_name),
        smith=Entity("smith", "smith", params.smith_name),
        lantern=Entity("lantern", "tool", "a brass lantern"),
    )


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("has_illusion", "tale"),
        asp.fact("has_smith", "tale"),
        asp.fact("has_roam", "tale"),
        asp.fact("cautionary", "tale"),
        asp.fact("misunderstanding", "tale"),
    ])


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import asp
    return bool(asp.atoms(asp.one_model(asp_program()), "valid_story"))


def tell_story(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = make_world(params)
    rng = random.Random(params.seed if params.seed is not None else params.hero_name)
    tale = rng.choice(TALES)
    dialogue = rng.choice(DIALOGUES)
    hero = params.hero_name
    smith = params.smith_name

    world.facts.update(tale)
    world.facts["dialogue"] = dialogue
    world.facts["resolved"] = False
    world.meters["light"] = 1
    world.meters["distance"] = 0
    world.meters["danger"] = 0
    world.meters["trust"] = 0
    world.memes["curiosity"] = 1

    opening = (
        f"In {params.place}, {hero} saw {tale['object']} gleam by moonlight. "
        f"With a tap-tap-tap and a bright little clink, {smith} worked at the forge."
    )
    misunderstanding = (
        f"{hero} made a misunderstanding: {hero} believed {tale['illusion']} "
        f"was real, and {tale['roam']}."
    )
    world.meters["distance"] = 1
    world.meters["danger"] = 1
    world.memes["worry"] = 1

    first, second = dialogue
    spoken = " ".join([
        first.format(hero=hero, smith=smith),
        second.format(hero=hero, smith=smith),
    ])

    turn = (
        f"{smith} held up the lantern, and {hero} {tale['turn']}. "
        f"Then {tale['proof']}. The shining thing had fooled eager eyes."
    )
    world.memes["trust"] = 1
    world.memes["shame"] = 1

    ending = (
        f"So {hero} did not chase every sparkle after that. {tale['ending']}. "
        f'"Look twice before you roam," said {smith}. "That is how a small mistake stays small."'
    )
    world.meters["distance"] = 0
    world.meters["danger"] = 0
    world.meters["trust"] = 1
    world.memes["relief"] = 1
    world.facts["resolved"] = True

    forms = [
        [opening, misunderstanding, spoken, turn, ending],
        [opening + " " + misunderstanding, spoken, turn, ending],
        [opening, spoken + " " + misunderstanding, turn, ending],
    ]
    world.facts["story"] = "\n\n".join(rng.choice(forms))
    return world


def prompts(world: World) -> list[str]:
    return [
        'Write a cautionary nursery rhyme using "illusion", "smith", and "roam".',
        f"Tell how {world.hero.label} misunderstood a glittering sight in {world.place}.",
        "Include dialogue with a careful smith and end with a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.hero.label
    smith = world.smith.label
    return [
        QAItem(
            question=f"What illusion did {hero} misunderstand in {world.place}?",
            answer=f"{hero} mistook {world.facts['illusion']} for something real, although it was actually {world.facts['danger']}.",
        ),
        QAItem(
            question=f"Why did {smith} tell {hero} not to roam too quickly?",
            answer=f"{smith} knew that {world.facts['danger']}, so rushing after it could have led {hero} into danger.",
        ),
        QAItem(
            question=f"How did {hero} and {smith} discover the truth?",
            answer=f"{hero} listened to {smith}, used the lantern, and {world.facts['proof']}.",
        ),
        QAItem(
            question=f"What lesson did {hero} learn?",
            answer=f"{hero} learned to look twice and ask a careful helper before roaming after a glittering illusion.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an illusion?",
            answer="An illusion is something that looks or seems real but is actually different.",
        ),
        QAItem(
            question="What does it mean to roam?",
            answer="To roam means to wander from place to place without following one short path.",
        ),
        QAItem(
            question="What does a smith do?",
            answer="A smith shapes metal with tools, heat, and careful hammering.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return "\n".join([
        "--- trace ---",
        f"place={world.place}",
        f"hero={world.hero.label}",
        f"smith={world.smith.label}",
        f"resolved={world.facts.get('resolved')}",
        f"meters={world.meters}",
        f"memes={world.memes}",
    ])


def generate(params: StoryParams) -> StorySample:
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
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    if not asp_valid():
        print("ASP gate rejected the canonical tale.")
        return 1
    sample = generate(StoryParams("Luna", "Old Bram", "the moonlit lane", 17))
    if "illusion" not in sample.story or "smith" not in sample.story or "roam" not in sample.story:
        return 1
    print("OK: ASP and Python gates agree.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP gate: valid_story/1 is", "true" if asp_valid() else "false")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("Luna", "Old Bram", "the moonlit lane", 11),
            StoryParams("Milo", "Mara Smith", "a blue village", 22),
            StoryParams("Nell", "Master Flint", "the edge of the wood", 33),
        ]
    else:
        params_list = []
        for i in range(max(1, args.n)):
            params_list.append(resolve_params(args, random.Random(base_seed + i)))

    samples = [generate(p) for p in params_list]
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
