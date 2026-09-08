#!/usr/bin/env python3
"""
A gentle bedtime storyworld about an ambitious little fox, a misunderstood
footstep, and the kindness that makes bravery feel safe.
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
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str = "the moonlit hill"
    steepness: float = 1.0
    bedtime_safe: bool = True


@dataclass
class StoryParams:
    place: str = "hill"
    hero: str = "Luna"
    helper: str = "Pip"
    elder: str = "Mira"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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


@dataclass
class Arc:
    beginning: str
    sound: str
    clue: str
    misunderstanding: str
    brave_act: str
    kindness: str
    ending: str


ARCS = [
    Arc(
        "Luna had been practicing moon-climbing, one careful step at a time",
        "a soft thump came from behind the sleeping stones",
        "a trail of silver pebbles curled toward the old lantern tree",
        "that a shadowy giant was waiting there",
        "walked forward with her small lantern held high",
        "Pip stayed beside her and counted each calm breath",
        "the moon painted a silver path all the way home",
    ),
    Arc(
        "Luna was carrying a basket of star-shaped biscuits to the hilltop",
        "a quick pat-pat-pat sounded under the wooden bridge",
        "one biscuit crumb led beneath the bridge rail",
        "that a hungry goblin had come to steal the bedtime treats",
        "knelt down and looked beneath the bridge instead of running away",
        "Pip shared the last biscuit with a shivering hedgehog",
        "the hedgehog curled into a warm nest of fallen leaves",
    ),
    Arc(
        "Luna had made an ambitious plan to touch the first evening star",
        "a long scrape whispered across the grass",
        "the grass bent in a neat line toward the sleepy pond",
        "that a giant creature was creeping toward the water",
        "followed the line slowly while keeping both feet on the safe path",
        "Mira brought a blanket and called the creature gently",
        "a lost fawn rested beneath the willow until its mother arrived",
    ),
    Arc(
        "Luna was polishing her tiny red boots before bed",
        "one boot gave a wobbling bump from inside the cupboard",
        "a loose blue ribbon hung from the cupboard latch",
        "that a stranger had hidden among the coats",
        "opened the cupboard one inch at a time and asked who was there",
        "Pip answered the frightened kitten with a soft song",
        "the kitten slept in a basket beside the quiet boots",
    ),
    Arc(
        "Luna was learning to cross the hill without waking the fireflies",
        "a fluttering sound rose from the tall lavender",
        "a single paper star trembled on a stem",
        "that the night wind was carrying away the bedtime wishes",
        "stepped into the lavender and caught the star before it tore",
        "Mira helped smooth its fold and write a new wish",
        "the paper star shone from Luna's bedside window",
    ),
]


def tell_story(params: StoryParams) -> World:
    if params.place != "hill":
        raise StoryError("This bedtime story takes place on the moonlit hill.")
    if len({params.hero, params.helper, params.elder}) != 3:
        raise StoryError("The hero, helper, and elder must have different names.")

    world = World(Place())
    hero = world.add(Entity(params.hero, "character", "fox", params.hero))
    helper = world.add(Entity(params.helper, "character", "mouse", params.helper))
    elder = world.add(Entity(params.elder, "character", "owl", params.elder))

    hero.meters.update(energy=0.8, balance=0.5)
    helper.meters.update(energy=0.7, balance=0.4)
    elder.meters.update(energy=0.9, balance=0.8)
    hero.memes.update(bravery=0.0, ambition=1.0, worry=0.5)
    helper.memes.update(kindness=1.0, worry=0.3)
    elder.memes.update(wisdom=1.0, kindness=1.0)

    arc = ARCS[(params.seed or 0) % len(ARCS)]
    world.facts["arc"] = arc
    world.facts["misunderstanding"] = True
    world.facts["bravery"] = False
    world.facts["kindness"] = False

    world.say(
        f"{hero.label} lived near {world.place.name}. Tonight, {arc.beginning}, "
        f"because she wanted to prove that even a little fox could do a very big thing."
    )
    world.say(
        f"The stars were blinking sleepily when {arc.sound}. "
        f"{hero.label} froze with one foot lifted, listening to the dark."
    )
    world.para()
    world.say(
        f"She saw {arc.clue}. Her ambitious heart hurried ahead of her careful eyes, "
        f"and she thought {arc.misunderstanding}."
    )
    world.say(
        f'"You do not have to solve the mystery alone," said {helper.label}. '
        f'"I will walk with you."'
    )
    world.say(
        f'"And I will listen before I decide," {hero.label} replied. '
        f'"That is a brave thing too."'
    )
    world.say(
        f"Together they {arc.brave_act}. Behind the shadow, they found the truth: "
        f"the night had made something small seem enormous."
    )
    world.facts["bravery"] = True
    hero.memes["bravery"] = 1.0
    hero.memes["worry"] = 0.0
    hero.meters["balance"] = 1.0

    world.para()
    world.say(
        f"{elder.label} arrived with a warm shawl. {helper.label} showed kindness when "
        f"{arc.kindness}. {hero.label} understood that bravery was not a loud roar; "
        f"it was a gentle step taken while someone kind stood nearby."
    )
    world.facts["kindness"] = True
    world.facts["misunderstanding"] = False
    helper.memes["kindness"] = 2.0

    world.say(
        f"At last, {arc.ending}. {hero.label} yawned, tucked her paws beneath her chin, "
        f"and watched the stars until the whole hill seemed to whisper, "
        f'"Good night, little adventurer."'
    )
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    arc: Arc = world.facts["arc"]
    return [
        "Write a gentle bedtime story about an ambitious young fox learning brave kindness.",
        f"Tell a moonlit story beginning when {arc.sound}, with a misunderstanding that is solved gently.",
        "Write a child-facing adventure where bravery means taking one careful step and listening.",
    ]


def story_qa(world: World) -> list[QAItem]:
    arc: Arc = world.facts["arc"]
    hero = world.entities[world.facts.get("hero_id", "")] if world.facts.get("hero_id") else None
    name = hero.label if hero else "Luna"
    return [
        QAItem(
            question=f"What ambitious thing was {name} trying to do?",
            answer=f"{name} was trying to complete a big nighttime goal: {arc.beginning}.",
        ),
        QAItem(
            question="What caused the misunderstanding?",
            answer=f"The misunderstanding began when {arc.sound} and the clue seemed frightening: {arc.clue}.",
        ),
        QAItem(
            question="How did bravery help solve the problem?",
            answer=f"Bravery helped when the children {arc.brave_act}. They looked closely instead of running away.",
        ),
        QAItem(
            question="How did kindness change the ending?",
            answer=f"Kindness brought comfort because {arc.kindness}. The frightened feeling became safe.",
        ),
        QAItem(
            question="What showed that the story was ready for bedtime?",
            answer=f"At the end, {arc.ending}. Then the little adventurer yawned and settled down beneath the stars.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing a careful, helpful thing even when you feel afraid.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is a mistaken idea about what happened or what someone meant.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is choosing to help, comfort, or care for someone.",
        ),
        QAItem(
            question="Why can bedtime stories feel peaceful?",
            answer="Bedtime stories often end with danger solved, caring friends nearby, and everyone ready to rest.",
        ),
    ]


ASP_RULES = r"""
safe_after_kindness :- brave_step, kindness_shown.
misunderstanding_resolved :- clue_checked, safe_after_kindness.
ready_for_bed :- misunderstanding_resolved.
#show ready_for_bed/0.
#show misunderstanding_resolved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("ambitious_goal"),
            asp.fact("brave_step"),
            asp.fact("clue_checked"),
            asp.fact("kindness_shown"),
        ]
    )


def asp_program(show: str = "#show ready_for_bed/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_outcome() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "ready_for_bed")))


def asp_verify() -> int:
    if asp_outcome() == [()]:
        print("OK: ASP and Python agree that the story is ready for bed.")
        return 0
    print("MISMATCH: ASP did not derive ready_for_bed.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    world.facts["hero_id"] = params.hero
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


NAMES = ["Luna", "Mina", "Nora", "Tessa", "Ivy"]
HELPERS = ["Pip", "Pipkin", "Milo", "Bram", "Ollie"]
ELDERS = ["Mira", "Oona", "Sage", "Nell", "Aster"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A gentle bedtime bravery storyworld.")
    parser.add_argument("--place", choices=["hill"])
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--elder", choices=ELDERS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([x for x in HELPERS if x != hero])
    elder = args.elder or rng.choice([x for x in ELDERS if x not in {hero, helper}])
    return StoryParams(
        place=args.place or "hill",
        hero=hero,
        helper=helper,
        elder=elder,
        seed=args.seed,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_outcome())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            place="hill",
            hero="Luna",
            helper="Pip",
            elder="Mira",
            seed=base_seed,
        )
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

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
