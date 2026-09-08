#!/usr/bin/env python3
"""
Standalone storyworld: a child-friendly comedy about a sprinkle, a rhyme,
and a tiny mistake that becomes a shared joke.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = {
    "bakery": {"surface": "counter", "mess": 0.4},
    "school kitchen": {"surface": "table", "mess": 0.3},
    "town picnic": {"surface": "blanket", "mess": 0.2},
    "birthday room": {"surface": "cake table", "mess": 0.5},
}

HEROES = ["Luna", "Milo", "Nia", "Toby", "Ari", "Zoe"]
HELPERS = ["Pip", "Rae", "Finn", "Sana", "Bo", "Mina"]
FOODS = ["cupcakes", "pancakes", "muffins", "cookies", "fruit tarts"]

RHYME_PAIRS = [
    ("sprinkle", "twinkle"),
    ("cake", "bake"),
    ("sweet", "treat"),
    ("pan", "plan"),
    ("crumb", "drum"),
]


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    food: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Bit:
    problem: str
    first_attempt: str
    clue: str
    fix: str
    ending: str


BITS = [
    Bit(
        problem="a windy sneeze sent a cloud of rainbow sprinkles sailing across the counter",
        first_attempt="Luna tried to catch them with a mixing bowl, but caught her own hat instead",
        clue="the sprinkles were landing in a neat trail beside the fan",
        fix="turned the fan toward an empty tray and used a paper plate as a little shield",
        ending="one blue sprinkle remained on Luna's nose like a tiny clown button",
    ),
    Bit(
        problem="the sprinkle jar tipped over and decorated the table, the floor, and one surprised spoon",
        first_attempt="Luna chased the rolling jar, slipped on a napkin, and bowed to the spoon",
        clue="the jar had stopped beside a wobbly stack of recipe cards",
        fix="moved the cards away, set the jar in a wide bowl, and swept the loose sprinkles into a cup",
        ending="the spoon wore three sprinkles like a very fancy necklace",
    ),
    Bit(
        problem="a spoonful of sprinkles bounced into the batter and made the bowl look polka-dotted",
        first_attempt="Luna stirred faster, which made the batter leap up and land on the recipe",
        clue="the recipe said to add decorations only after the cakes cooled",
        fix="covered the batter, cleaned the recipe, and saved the sprinkles for the tops",
        ending="the finished cakes wore bright dots like tiny party hats",
    ),
    Bit(
        problem="the dessert sign fell face-down into a box of sprinkles",
        first_attempt="Luna lifted it quickly and gave the whole sign a glittery orange beard",
        clue="the clean back of the sign still showed the missing word",
        fix="brushed the sign gently, rewrote the word, and placed it in a stand",
        ending="the sign announced CUPCAKES while its orange beard sparkled proudly",
    ),
]


OPENINGS = [
    "At the town bakery, Luna believed every dessert needed a little drama.",
    "The school kitchen was quiet until Luna opened the sprinkle cupboard.",
    "At the birthday table, Luna prepared a treat that was meant to look ordinary.",
    "The picnic began with sandwiches, sunshine, and one very ambitious jar of sprinkles.",
]


def build_world(params: StoryParams) -> World:
    seed = params.seed
    if seed is None:
        seed = sum((i + 1) * ord(c) for i, c in enumerate("|".join(vars(params).values() if False else [params.place, params.hero, params.helper, params.food])))
    rng = random.Random(seed ^ 0x51A7)
    bit = rng.choice(BITS)
    rhyme = rng.choice(RHYME_PAIRS)
    opening = rng.choice(OPENINGS)

    world = World(params.place)
    hero = world.add(Entity("hero", "person", params.hero, memes={"confidence": 0.5, "relief": 0.0}))
    helper = world.add(Entity("helper", "person", params.helper, memes={"patience": 0.8, "amusement": 0.2}))
    sprinkles = world.add(Entity("sprinkles", "food", "rainbow sprinkles", meters={"looseness": 0.7, "mess": 0.0}))
    food = world.add(Entity("food", "dessert", params.food, meters={"readiness": 0.2}))
    world.facts.update(bit=bit, rhyme=rhyme, hero=hero, helper=helper, sprinkles=sprinkles, food=food)

    world.say(opening)
    world.say(
        f"{hero.label} and {helper.label} were making {params.food} when {hero.label} announced, "
        f'"A sprinkle should twinkle!"'
    )
    world.say(
        f'{helper.label} tapped the bowl. "Then make it rhyme, not just shine." '
        f'{hero.label} grinned. "I can do both. I am a poet with an apron."'
    )
    world.para()

    world.say(f"The plan wobbled when {bit.problem}.")
    sprinkles.meters["mess"] = 1.0
    hero.memes["confidence"] = 0.1
    world.say(
        f'{hero.label} declared, "{bit.first_attempt.capitalize()}." '
        f'{helper.label} laughed so hard that a measuring cup began to wobble.'
    )
    world.say(
        f'"Please do not rhyme with disaster," said {helper.label}. '
        f'"Disaster, faster, platter!" replied {hero.label}, which did not help at all.'
    )
    world.para()

    world.say(f"Then {helper.label} noticed that {bit.clue}.")
    world.say(
        f'{hero.label} stopped posing like a poet and studied the room. '
        f'"The sprinkle trail is showing us the answer," {hero.label} said.'
    )
    world.say(
        f'"A clue can be sweet and neat," said {helper.label}. '
        f'"And a fix can be quick," said {hero.label}, "if we do not panic in public."'
    )
    hero.memes["confidence"] = 0.8
    world.para()

    world.say(f"Together they {bit.fix}.")
    sprinkles.meters["mess"] = 0.1
    food.meters["readiness"] = 1.0
    hero.memes["relief"] = 1.0
    helper.memes["amusement"] = 1.0
    world.say(
        f'{hero.label} tested the rhyme again: "{rhyme[0].capitalize()} with {rhyme[1]}!" '
        f'{helper.label} nodded. "That one actually works."'
    )
    world.say(
        f"They shared the finished {params.food}, and {hero.label} admitted, "
        f'"A good sprinkle needs a good plan."'
    )
    world.say(f"The kitchen grew quiet at last, except for one ridiculous little sound: {bit.ending}.")
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    bit = world.facts["bit"]
    rhyme = world.facts["rhyme"]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a funny child-friendly story containing the word sprinkle.",
            f"Tell a comedy about {hero.label} and {helper.label} solving a sprinkle problem with a rhyme.",
            f"Include the rhyme pair {rhyme[0]} and {rhyme[1]}, then end with a visible silly image.",
        ],
        story_qa=[
            QAItem(
                question=f"What went wrong while {hero.label} and {helper.label} were making {params.food}?",
                answer=f"Their sprinkle problem was that {bit.problem}.",
            ),
            QAItem(
                question=f"How did {hero.label} discover what to do?",
                answer=f"{hero.label} noticed that {bit.clue}, so the sprinkle trail helped reveal the cause.",
            ),
            QAItem(
                question=f"How did the two friends fix the mess?",
                answer=f"Together they {bit.fix}. This reduced the mess and let them finish the {params.food}.",
            ),
            QAItem(
                question="What rhyme did the story use?",
                answer=f"The story used the rhyme pair {rhyme[0]} and {rhyme[1]}.",
            ),
        ],
        world_qa=[
            QAItem(
                question="What is a sprinkle?",
                answer="A sprinkle is a tiny piece of colorful food decoration placed on desserts.",
            ),
            QAItem(
                question="What is a rhyme?",
                answer="A rhyme is a pattern in which words have matching or similar ending sounds.",
            ),
            QAItem(
                question="Why can a small plan help with a mess?",
                answer="A small plan helps people notice the cause, choose a safe action, and avoid making the mess bigger.",
            ),
        ],
        world=world,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice([x for x in HELPERS if x != hero])
    food = args.food or rng.choice(FOODS)
    if hero == helper:
        raise StoryError("hero and helper must be different characters")
    return StoryParams(place, hero, helper, food, args.seed)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    sections = [
        ("== (1) Generation prompts ==", sample.prompts),
        ("== (2) Story questions ==", sample.story_qa),
        ("== (3) World knowledge ==", sample.world_qa),
    ]
    lines: list[str] = []
    for title, items in sections:
        lines.append(title)
        for i, item in enumerate(items, 1):
            if isinstance(item, QAItem):
                lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
            else:
                lines.append(f"{i}. {item}")
        lines.append("")
    return "\n".join(lines).rstrip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A sprinkle-and-rhyme comedy storyworld.")
    parser.add_argument("--place", choices=list(PLACES))
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--food", choices=FOODS)
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


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_food(F) :- food(F).
valid_story(P,F) :- valid_place(P), valid_food(F).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    facts = [asp.fact("place", place) for place in PLACES]
    facts.extend(asp.fact("food", food) for food in FOODS)
    return "\n".join(facts)


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> set[tuple[str, str]]:
    return {(place, food) for place in PLACES for food in FOODS}


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
        actual = set(asp.atoms(model, "valid_story"))
    except ImportError:
        print("ASP verification requires clingo.")
        return 1
    expected = valid_combos()
    if actual != expected:
        print("ASP/Python mismatch.")
        print("Only in ASP:", sorted(actual - expected))
        print("Only in Python:", sorted(expected - actual))
        return 1
    for index, (place, food) in enumerate(sorted(expected)[:5]):
        sample = generate(StoryParams(place, HEROES[index % len(HEROES)], HELPERS[index % len(HELPERS)], food, index))
        if "sprinkle" not in sample.story.lower() or "rhyme" not in sample.story.lower():
            print("Generated story validation failed.")
            return 1
    print(f"OK: ASP/Python parity and generated stories verified ({len(expected)} combinations).")
    return 0


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print("Compatible place and food combinations:")
        for place, food in sorted(valid_combos()):
            print(f"  {place} / {food}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, place in enumerate(PLACES):
            params = StoryParams(
                place=place,
                hero=HEROES[index % len(HEROES)],
                helper=HELPERS[index % len(HELPERS)],
                food=FOODS[index % len(FOODS)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
