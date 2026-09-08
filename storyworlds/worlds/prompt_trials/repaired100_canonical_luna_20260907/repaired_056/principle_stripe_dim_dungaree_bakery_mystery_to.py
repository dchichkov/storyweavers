#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = {
    "bakery": {
        "setting": "the little bakery",
        "oven": True,
        "counter": True,
        "flour": True,
    }
}

CHARACTERS = ("Luna", "Milo", "Pip", "Nora", "Theo", "Mina")
MOODS = ("curious", "careful", "cheerful", "patient")
SOUNDS = ("tap-tap", "ding-ding", "whuff", "scritch", "clink")
SEEDS = ("principle", "stripe-dim", "dungaree")

CASES = (
    {
        "title": "The Stripe-Dim Dungaree Mystery",
        "opening": "At dawn, the bakery smelled of cinnamon, warm bread, and a puzzle in the air.",
        "clue": "a stripe-dim blue apron lay beside a trail of flour near the cooling rack",
        "mistake": "thought the flour trail led to a missing pair of dungarees",
        "discovery": "the dim stripe was a pale reflection from the oven window, not a torn mark",
        "method": "followed the flour prints one careful step at a time",
        "turn": "the prints stopped beneath a basket marked with a tiny dungaree-shaped patch",
        "solution": "the baker's lost recipe card had slipped beneath the basket when the patch was sewn on",
        "action": "lifted the basket and rescued the recipe card without disturbing the cooling buns",
        "result": "the baker could bake the honey buns exactly as planned",
        "lesson": "a good principle is to check the light and the evidence before making a guess",
        "ending": "The buns rose like golden hills, and the stripe-dim apron danced beside the dungarees.",
    },
    {
        "title": "The Dungaree Pocket Clue",
        "opening": "Before breakfast, a muffin tray vanished from the bakery counter.",
        "clue": "blue threads and a dusting of flour glittered beneath the wooden table",
        "mistake": "suspected that a stripe-dim dungaree pocket had swallowed the whole tray",
        "discovery": "the threads came from an old cloth, while the flour showed wheels, not footsteps",
        "method": "held a paper ruler beside the marks and measured their tiny turns",
        "turn": "the trail curved toward the delivery cart's shadow",
        "solution": "the tray had rolled into the cart when a wheel bumped the counter",
        "action": "blocked the wheel, pulled the cart gently back, and found every muffin safe",
        "result": "the muffins reached the breakfast table in a neat warm row",
        "lesson": "the principle of careful measuring can turn a wild guess into a clear answer",
        "ending": "Ding-ding went the cart, and the muffins grinned beneath their sugar snow.",
    },
    {
        "title": "The Quiet Oven Riddle",
        "opening": "The bakery oven went quiet just when the berry pies needed one more minute.",
        "clue": "a stripe-dim line crossed the oven door, and a dungaree button rested beside the timer",
        "mistake": "believed someone in dungarees had hidden the oven's baking principle",
        "discovery": "the line was flour on the glass, and the button had fallen from a work coat",
        "method": "asked who had touched the timer and compared the answer with the warm trays",
        "turn": "Luna heard a faint click behind the flour bin",
        "solution": "a wooden spoon had nudged the safety switch when it slid from the bin",
        "action": "called the baker, who reset the switch and checked the pies",
        "result": "the pies finished safely, with no one touching the hot oven alone",
        "lesson": "a wise principle is to ask for help near heat and to test clues calmly",
        "ending": "The timer chimed bright, and berry pies wore red smiles beneath the oven light.",
    },
)

OPENINGS = (
    "A mystery may be small as a crumb, yet it can lead to a very big answer.",
    "In a bakery where sweet smells flew, one puzzling clue appeared from blue.",
    "When morning bells began to ring, a curious case hid under everything.",
    "A floury trail crossed the floor, and Luna wondered what it was for.",
)

DIALOGUE = (
    ("“I see a clue!”", "“Then let us check it twice.”"),
    ("“Could dungarees be part of this case?”", "“Perhaps, but evidence must decide.”"),
    ("“The stripe looks dim and strange.”", "“Light can trick our eyes, so let us change our view.”"),
    ("“Should we rush to solve it now?”", "“We can be quick, kind, and careful somehow.”"),
)

ASP_RULES = r"""
kind(bakery).
feature(mystery_to_solve).
style(rhyming_story).
seed_word(principle).
seed_word(stripe_dim).
seed_word(dungaree).
has_oven(bakery).
has_counter(bakery).
has_flour(bakery).
valid_setting(bakery) :- kind(bakery), has_oven(bakery), has_counter(bakery), has_flour(bakery).
story_ready(bakery) :- valid_setting(bakery), feature(mystery_to_solve), style(rhyming_story).
#show valid_setting/1.
#show story_ready/1.
"""


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: Optional[str] = None
    carried_by: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    mood: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A rhyming bakery mystery about principle, stripe-dim, and dungaree.")
    parser.add_argument("--place", choices=PLACES, default=None)
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


def asp_facts() -> str:
    import asp
    return "\n".join(
        (
            asp.fact("kind", "bakery"),
            asp.fact("has_oven", "bakery"),
            asp.fact("has_counter", "bakery"),
            asp.fact("has_flour", "bakery"),
            asp.fact("feature", "mystery_to_solve"),
            asp.fact("style", "rhyming_story"),
            asp.fact("seed_word", "principle"),
            asp.fact("seed_word", "stripe_dim"),
            asp.fact("seed_word", "dungaree"),
        )
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ready/1."))
    ready = asp.atoms(model, "story_ready")
    if ready == [("bakery",)]:
        print("OK: ASP bakery mystery gate matches Python reasoning.")
        return 0
    print("MISMATCH: ASP did not approve the bakery story domain.")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "bakery"
    if place not in PLACES:
        raise StoryError(f"Unknown place: {place}")
    hero = rng.choice(CHARACTERS)
    helper = rng.choice([name for name in CHARACTERS if name != hero])
    mood = rng.choice(MOODS)
    return StoryParams(place=place, hero=hero, helper=helper, mood=mood, seed=args.seed)


def _story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.place, params.hero, params.helper, params.mood))
    return int.from_bytes(hashlib.blake2b(text.encode(), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("This mystery must take place in the bakery.")
    if params.hero == params.helper:
        raise StoryError("The hero and helper must be different characters.")

    seed = _story_seed(params)
    rng = random.Random(seed)
    case = CASES[seed % len(CASES)]
    opening = OPENINGS[(seed // len(CASES)) % len(OPENINGS)]
    dialogue = DIALOGUE[(seed // (len(CASES) * len(OPENINGS))) % len(DIALOGUE)]
    sound = SOUNDS[seed % len(SOUNDS)]

    world = World(place="the little bakery")
    hero = Entity(
        id=params.hero,
        kind="character",
        label="young mystery solver",
        type="detective",
        meters={"alertness": 1.0, "care": 0.8},
        memes={"curiosity": 1.0},
        location=params.place,
    )
    helper = Entity(
        id=params.helper,
        kind="character",
        label="bakery helper",
        type="helper",
        meters={"alertness": 0.8, "care": 0.9},
        memes={"patience": 1.0},
        location=params.place,
    )
    apron = Entity(
        id="apron",
        kind="object",
        label="stripe-dim apron",
        type="dungaree_cloth",
        meters={"warmth": 0.4},
        memes={"clue": 1.0},
        location=params.place,
    )
    oven = Entity(
        id="oven",
        kind="object",
        label="warm bakery oven",
        type="oven",
        meters={"heat": 0.8},
        memes={"safety": 1.0},
        location=params.place,
    )
    world.entities = {item.id: item for item in (hero, helper, apron, oven)}

    world.say(opening)
    world.say(
        f"{params.hero}, a {params.mood} solver, visited {world.place} with {params.helper}; "
        f"the morning smelled of buns, and the mystery began with a soft {sound}."
    )
    world.say(case["opening"])
    world.para()

    world.say(f"They found {case['clue']}.")
    world.say(f"{params.helper} said, {dialogue[0]} {params.hero} replied, {dialogue[1]}")
    world.say(f"At first, {params.helper} {case['mistake']}.")
    world.say(f"But their first guess did not fit, so they {case['method']}.")

    world.para()
    world.say("Their principle was simple: look, listen, and keep every clue in view.")
    world.say(f"Then they noticed that {case['turn']}.")
    world.say(f"The new clue showed that {case['discovery']}.")
    world.say(
        f"“Now I know!” cried {params.hero}. “The mystery is not solved by guessing; "
        f"it is solved by checking what is true.”"
    )
    world.say(f"Together they {case['action']}.")

    world.para()
    world.say(f"Because they worked carefully, {case['result']}.")
    world.say(f"The lesson was clear: {case['lesson'].capitalize()}.")
    world.say(case["ending"])

    hero.meters["alertness"] = 1.4
    hero.memes["careful_reasoning"] = 1.0
    helper.meters["alertness"] = 1.2
    helper.memes["careful_reasoning"] = 1.0
    apron.memes["meaning_checked"] = 1.0
    oven.memes["handled_safely"] = 1.0

    world.trace = [
        f"clue:{case['clue']}",
        f"first_guess:{case['mistake']}",
        f"method:{case['method']}",
        f"turn:{case['turn']}",
        f"discovery:{case['discovery']}",
        f"resolution:{case['result']}",
    ]
    world.facts = {
        "setting": "bakery",
        "hero": params.hero,
        "helper": params.helper,
        "case": case["title"],
        "seed_words": list(SEEDS),
        "clue": case["clue"],
        "mistake": case["mistake"],
        "discovery": case["discovery"],
        "resolution": case["result"],
        "lesson": case["lesson"],
    }

    prompts = [
        f"Write a rhyming bakery mystery for {params.hero} and {params.helper} using principle, stripe-dim, and dungaree.",
        f"Tell how two children solve the mystery in {case['title']} by checking evidence instead of guessing.",
        "Write a child-friendly story with bakery sounds, spoken dialogue, a turning clue, and a clear lesson.",
    ]

    story_qa = [
        QAItem(
            question=f"What mystery did {params.hero} and {params.helper} investigate?",
            answer=f"They investigated {case['title']}, a bakery mystery involving a stripe-dim clue and dungaree.",
        ),
        QAItem(
            question="What was the first mistaken idea?",
            answer=f"The first mistaken idea was that someone {case['mistake']}.",
        ),
        QAItem(
            question="What clue changed their minds?",
            answer=f"They noticed that {case['turn']}, which helped them understand that {case['discovery']}.",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"They {case['action']}, and this meant that {case['result']}.",
        ),
        QAItem(
            question="What principle did they learn?",
            answer=f"They learned that {case['lesson']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a bakery?",
            answer="A bakery is a place where people mix, shape, and bake bread, buns, cakes, and other foods.",
        ),
        QAItem(
            question="What are dungarees?",
            answer="Dungarees are sturdy clothes, often made from denim, worn for work or play.",
        ),
        QAItem(
            question="What does stripe-dim mean in this story?",
            answer="Stripe-dim describes a stripe that looks faint or less bright, especially when light makes it hard to see.",
        ),
        QAItem(
            question="Why is a principle useful when solving a mystery?",
            answer="A principle gives a solver a helpful rule, such as checking evidence before deciding what happened.",
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
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            details = []
            if entity.label:
                details.append(f"label={entity.label}")
            if entity.location:
                details.append(f"location={entity.location}")
            if entity.meters:
                details.append(f"meters={entity.meters}")
            if entity.memes:
                details.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.kind} {' '.join(details)}")
        for item in sample.world.trace:
            print(f"  event: {item}")
    if qa:
        print("\n== prompts ==")
        for number, prompt in enumerate(sample.prompts, 1):
            print(f"{number}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


CURATED = [
    StoryParams(place="bakery", hero="Luna", helper="Milo", mood="curious"),
    StoryParams(place="bakery", hero="Nora", helper="Pip", mood="careful"),
    StoryParams(place="bakery", hero="Theo", helper="Mina", mood="patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ready/1."))
        return

    if args.verify:
        if asp_verify() != 0:
            raise SystemExit(1)
        for params in CURATED:
            sample = generate(params)
            if not sample.story or not sample.story_qa:
                raise SystemExit("Generated story verification failed.")
        print("OK: generated stories and QA passed.")
        return

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_setting/1.\n#show story_ready/1."))
        print(asp.atoms(model, "valid_setting"))
        print(asp.atoms(model, "story_ready"))
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        count = max(1, args.n)
        base = args.seed if args.seed is not None else random.randrange(2**31)
        seen: set[str] = set()
        for index in range(count):
            rng = random.Random(base + index)
            params = resolve_params(args, rng)
            params.seed = base + index
            sample = generate(params)
            if sample.story in seen:
                params.seed += 1000003
                sample = generate(params)
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
