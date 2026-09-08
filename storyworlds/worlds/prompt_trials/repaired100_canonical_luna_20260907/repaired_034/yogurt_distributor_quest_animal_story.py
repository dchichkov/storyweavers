#!/usr/bin/env python3
"""
A small animal quest about a yogurt distributor, a missing cart, and a kind solution.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
while not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    parent = os.path.dirname(_storyworlds_dir)
    if parent == _storyworlds_dir:
        break
    _storyworlds_dir = parent
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    hero: str = "Luna"
    companion: str = "Pip"
    animal: str = "rabbit"
    setting: str = "the meadow"
    yogurt: str = "berry yogurt"
    arc: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    hero: Entity
    companion: Entity
    distributor: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HEROES = ["Luna", "Milo", "Clover", "Nori", "Bramble", "Tess"]
COMPANIONS = ["Pip", "Biscuit", "Moss", "Daisy", "Otis", "Wren"]
ANIMALS = ["rabbit", "fox", "badger", "squirrel", "hedgehog", "otter"]
SETTINGS = ["the meadow", "the orchard", "the riverside", "the woodland path"]
YOGURTS = ["berry yogurt", "honey yogurt", "apple yogurt", "vanilla yogurt"]

ARCS = [
    {
        "premise": "Luna was a careful yogurt distributor who carried cool cups to the animals each morning",
        "problem": "the little delivery cart rolled away before the breakfast bell",
        "stake": "the hungry young animals might miss their meal",
        "clue": "purple berry drops dotted the path beside the cart tracks",
        "action": "Luna and Pip followed the drops, using a long scarf to mark each turn",
        "twist": "the cart had stopped beside a fawn who had been trying to return a spilled cup",
        "sharing": "Luna gave the fawn a clean spoon, and the animals helped carry every cup to the picnic blanket",
        "lesson": "a quest becomes kinder when rescuers notice who needs help along the way",
        "ending": "the empty yogurt cart rested under an oak while every animal licked a bright berry mustache",
        "question": "Why did Luna follow the berry drops?",
        "answer": "Luna followed the berry drops because they marked the path taken by the rolling yogurt cart.",
    },
    {
        "premise": "Luna prepared honey yogurt for a woodland morning picnic",
        "problem": "the distributor's sign blew loose and pointed travelers toward a muddy ditch",
        "stake": "the animals could wander past the safe picnic place",
        "clue": "the sign's honey-colored ribbon was caught on a low branch",
        "action": "Luna and Pip gathered straight sticks and made a new arrow beside the trail",
        "twist": "a shy mole had moved the old sign while searching for its lost button",
        "sharing": "the animals found the button together and let the mole choose the picnic's first flavor",
        "lesson": "a mistake can hide a small need that deserves care",
        "ending": "the new sign stood firm, pointing toward yogurt cups and a sunny patch of grass",
        "question": "What had pulled the distributor's sign from its post?",
        "answer": "A honey-colored ribbon on the sign had caught on a low branch and pulled it loose.",
    },
    {
        "premise": "Luna brought apple yogurt to the riverside animals",
        "problem": "the cooler latch froze shut in the chilly morning air",
        "stake": "the yogurt would stay trapped when everyone was ready to eat",
        "clue": "warm breath made a little cloud above each animal's nose",
        "action": "Luna asked everyone to breathe gently around the latch while Pip wrapped it in a soft nest of moss",
        "twist": "the latch opened when the animals stopped pulling and shared their warmth",
        "sharing": "they divided the apple cups fairly, saving one for the smallest vole",
        "lesson": "many small helpful breaths can open a stubborn problem",
        "ending": "the cooler clicked shut again after breakfast, and the vole carried an apple-colored smile home",
        "question": "How did the animals open the frozen cooler?",
        "answer": "They shared their gentle warmth around the latch and wrapped it in soft moss.",
    },
    {
        "premise": "Luna was the woodland yogurt distributor for the annual animal parade",
        "problem": "a flock of geese blocked the bridge where the delivery path crossed the stream",
        "stake": "the parade could begin without its cool refreshments",
        "clue": "the geese were guarding a nest hidden beneath the bridge rail",
        "action": "Luna and Pip made a quiet detour and carried the yogurt in a basket over the hill",
        "twist": "the geese were not being troublesome; they were protecting three tiny eggs",
        "sharing": "the animals left a fresh patch of grass near the nest and delivered yogurt to the geese afterward",
        "lesson": "a patient quest looks for the reason behind an obstacle",
        "ending": "the parade crossed the bridge later while the geese watched from their safe nest",
        "question": "Why did the geese block the bridge?",
        "answer": "The geese blocked the bridge because they were protecting a nest with three tiny eggs.",
    },
    {
        "premise": "Luna carried vanilla yogurt to a circle of young animals near the old oak",
        "problem": "one cup slipped beneath a pile of autumn leaves",
        "stake": "a tiny hedgehog feared it would have no breakfast",
        "clue": "a pale vanilla smell rose whenever the breeze lifted a leaf",
        "action": "Luna and Pip made a careful leaf line and searched without stepping on the hidden cup",
        "twist": "the cup was beside a hedgehog nest, keeping the babies warm with its sunny lid",
        "sharing": "they moved the cup gently and poured it into smaller bowls for the whole family",
        "lesson": "careful searching can protect more than the thing we first hope to find",
        "ending": "the leaves settled over the nest, while clean bowls shone beside the old oak",
        "question": "What clue helped Luna find the hidden cup?",
        "answer": "A pale vanilla smell rose when the breeze lifted the leaves, showing where the cup was hidden.",
    },
]

OPENINGS = [
    "Dew sparkled on the grass as morning birds began to sing",
    "The sun peeked over the trees and warmed the sleepy trail",
    "A soft breeze tickled the clover beside the path",
    "The meadow woke beneath a sky as blue as a robin's wing",
    "Tiny paws and bright eyes gathered for the first meal of the day",
]

DIALOGUE = [
    ("Pip asked, \"Should we hurry after it?\"", "\"We should hurry carefully,\" Luna replied. \"First, we need to see who might be waiting along the path.\""),
    ("Pip called, \"I see something!\"", "\"Tell me what you see,\" said Luna. \"A good clue can make our quest safer.\""),
    ("Pip whispered, \"What if we cannot fix this?\"", "\"Then we will ask the animals nearby,\" Luna said. \"No quest has to be carried by one pair of paws.\""),
    ("Pip said, \"The trail looks muddy.\"", "\"We can take the high ground,\" Luna answered. \"A slower path may still lead everyone to breakfast.\""),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="An animal story about a yogurt distributor on a helpful quest.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--yogurt", choices=YOGURTS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HEROES)
    companion = args.companion or rng.choice([x for x in COMPANIONS if x != hero])
    if hero == companion:
        raise StoryError("The hero and companion must be different animals.")
    return StoryParams(
        hero=hero,
        companion=companion,
        animal=args.animal or rng.choice(ANIMALS),
        setting=args.setting or rng.choice(SETTINGS),
        yogurt=args.yogurt or rng.choice(YOGURTS),
        arc=rng.randrange(len(ARCS)),
        seed=args.seed,
    )


def build_world(params: StoryParams) -> World:
    hero = Entity(params.hero, "hero")
    companion = Entity(params.companion, "companion")
    distributor = Entity("yogurt distributor", "distributor")
    return World(params, hero, companion, distributor)


def simulate(world: World) -> None:
    p = world.params
    arc = ARCS[p.arc]
    rng = random.Random(p.seed)
    h, c = world.hero, world.companion

    h.memes["kindness"] = 1.0
    h.memes["curiosity"] = 1.0
    h.meters["energy"] = 1.0
    c.memes["helpfulness"] = 1.0
    world.facts.update({
        "setting": p.setting,
        "yogurt": p.yogurt,
        "role": "distributor",
        "problem": arc["problem"],
        "clue": arc["clue"],
        "resolved": False,
    })

    world.say(f"{rng.choice(OPENINGS)}. In {p.setting}, {h.name} the {p.animal} worked as a yogurt distributor.")
    world.say(f"Each morning, {h.name} carried {p.yogurt} to the animal families, and {c.name} helped count the cups.")
    world.para()

    world.say(f"{arc['premise']}. Then {arc['problem']}. {arc['stake']}.")
    world.say(f"{h.name} held the empty delivery handle and looked down the path.")
    first, second = rng.choice(DIALOGUE)
    world.say(f"{first} {second}")
    world.facts["risk"] = arc["stake"]
    world.para()

    world.say(f"On their quest, {h.name} and {c.name} noticed that {arc['clue']}.")
    world.say(f"{arc['action']}.")
    world.say(f"Then came the surprise: {arc['twist']}.")
    h.memes["understanding"] = 1.0
    c.memes["trust"] = 1.0
    world.facts["twist"] = arc["twist"]
    world.facts["solution"] = arc["action"]
    world.para()

    world.say(f"{arc['sharing']}.")
    world.say(f"{h.name} learned that {arc['lesson']}.")
    world.say(f"At last, {arc['ending']}.")
    world.facts["resolved"] = True
    world.facts["shared"] = True


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]
    prompts = [
        f"Write an animal story about {params.hero}, a yogurt distributor, going on a kind quest in {params.setting}.",
        f"Tell a child-friendly quest where {params.hero} and {params.companion} solve this problem: {arc['problem']}.",
        f"Create an animal tale in which a surprising clue changes how {params.hero} helps others.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} face as a yogurt distributor?",
            answer=f"{params.hero} faced this problem: {arc['problem']}.",
        ),
        QAItem(
            question=f"What clue helped {params.hero} and {params.companion} on their quest?",
            answer=f"They noticed that {arc['clue']}.",
        ),
        QAItem(
            question=f"What surprising thing did {params.hero} discover?",
            answer=f"{params.hero} discovered that {arc['twist']}.",
        ),
        QAItem(
            question=f"How was the yogurt delivery completed?",
            answer=f"The delivery was completed when {arc['sharing']}.",
        ),
        QAItem(
            question=f"What lesson did {params.hero} learn?",
            answer=f"{params.hero} learned that {arc['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does a distributor do?",
            answer="A distributor carries goods from one place to the people or animals who need them.",
        ),
        QAItem(
            question="What is yogurt?",
            answer="Yogurt is a soft, creamy food made from milk with helpful cultures.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey with a purpose, such as finding something, solving a problem, or helping someone.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.hero, world.companion, world.distributor]:
        lines.append(
            f"  {entity.name:20} ({entity.kind:11}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/1.
valid(story) :- domain(yogurt), role(distributor), feature(quest), feature(animal_story).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("domain", "yogurt"),
        asp.fact("role", "distributor"),
        asp.fact("feature", "quest"),
        asp.fact("feature", "animal_story"),
    ])


def asp_program(show: str = "#show valid/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    if asp.atoms(model, "valid") != [("story",)]:
        print("MISMATCH: ASP twin failed.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or "yogurt" not in sample.story or "quest" not in " ".join(sample.prompts).lower():
            print("MISMATCH: generated story check failed.")
            return 1
    print("OK: ASP twin and generated stories are consistent.")
    return 0


CURATED = [
    StoryParams(hero="Luna", companion="Pip", animal="rabbit", setting="the meadow", yogurt="berry yogurt", arc=0, seed=101),
    StoryParams(hero="Milo", companion="Daisy", animal="fox", setting="the orchard", yogurt="honey yogurt", arc=1, seed=202),
    StoryParams(hero="Clover", companion="Moss", animal="hedgehog", setting="the woodland path", yogurt="vanilla yogurt", arc=4, seed=303),
]


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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        print(asp.atoms(asp.one_model(asp_program()), "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for i in range(max(args.n, 1) * 30):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
