#!/usr/bin/env python3
"""
A small space-adventure world about a cryptic chemical mystery solved in rhyme.

Seed words: premise, chemical, cryptic
Features: Mystery to Solve, Rhyme, Happy Ending
Style: Space Adventure
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = [
    "the moonlit research station",
    "the comet observatory",
    "the silver space garden",
    "the little orbiting laboratory",
]
CHEMICALS = ["blue oxygen gel", "silver moonwater", "green aurora crystals", "golden star-salt"]
HERO_NAMES = ["Luna", "Mira", "Nova", "Tess", "Pia", "Zara"]
HELPER_NAMES = ["Orin", "Kip", "Sol", "Bex", "Rafi", "Nell"]
SPECIES = ["space fox", "moon rabbit", "tiny robot", "star mouse", "comet owl"]
MYSTERIES = [
    {
        "object": "the station's welcome beacon",
        "problem": "it blinked three times and then went dark",
        "clue": "a curled silver symbol beside the beaker matched the beacon's three blinking lights",
        "truth": "the chemical's safe mixing order was hidden in a tiny rhyme on the beacon",
        "riddle": "First the pale drop, then the shining grain; turn them twice and wake the rain.",
        "method": "read the cryptic rhyme, measured the chemical carefully, and mixed it in the proper order",
        "result": "the beacon glowed warm and bright",
        "ending": "The welcome beacon shone across the stars, guiding a friendly shuttle home.",
    },
    {
        "object": "the comet garden's water wheel",
        "problem": "it spun backward and sprayed silver drops into the air",
        "clue": "three star-shaped marks on the wheel formed the same pattern as the chemical labels",
        "truth": "the marks gave a cryptic instruction for balancing the chemical in the wheel",
        "riddle": "One for the root, two for the sky; turn the moon cup, let the water fly.",
        "method": "followed the rhyme, counted the star marks, and added the chemical one small spoon at a time",
        "result": "the wheel turned forward and watered every moonflower",
        "ending": "Moonflowers opened like little lamps while the happy garden sparkled below the orbiting stars.",
    },
    {
        "object": "the observatory's star map",
        "problem": "one bright route had vanished from its glass",
        "clue": "a cryptic line of dots appeared only when a safe chemical mist touched the map",
        "truth": "the missing route was covered by a harmless crystal film made from the chemical",
        "riddle": "Mist the glass and wait, do not race; the hidden path will find its place.",
        "method": "read the rhyme, used a gentle puff of the chemical, and waited without rubbing the glass",
        "result": "the lost route returned in a trail of blue stars",
        "ending": "The restored map led every traveler safely toward a new, glittering world.",
    },
    {
        "object": "the rocket's cheerful engine bell",
        "problem": "it made a low hum instead of its bright launch song",
        "clue": "a cryptic rhyme was etched beneath a harmless chemical sample tube",
        "truth": "the rhyme described the exact order for clearing a sticky crystal from the bell",
        "riddle": "Warm the ring, cool the chain; sing one note to wake the rain.",
        "method": "recited the rhyme, warmed the ring, cooled the chain, and used the chemical with care",
        "result": "the bell rang a clear musical note",
        "ending": "The rocket hummed a happy tune as it carried friends toward the sunrise.",
    },
]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    style: str = "Space Adventure"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(line) for line in self.lines if line)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_species: str
    helper_name: str
    helper_species: str
    chemical: str
    seed: Optional[int] = None


def tell(params: StoryParams) -> World:
    world = World(Setting(params.place))
    hero = world.add(Entity(params.hero_name, "character", params.hero_species))
    helper = world.add(Entity(params.helper_name, "character", params.helper_species))
    chemical = world.add(Entity("chemical", "material", params.chemical, owner=params.hero_name))
    beacon = world.add(Entity("mystery-object", "device", "mystery device"))

    seed_value: object = params.seed
    if seed_value is None:
        seed_value = "|".join(
            [
                params.place,
                params.hero_name,
                params.hero_species,
                params.helper_name,
                params.helper_species,
                params.chemical,
            ]
        )
    rng = random.Random(seed_value)
    mystery = rng.choice(MYSTERIES)
    opening = rng.choice(
        [
            "Luna's small spacecraft slipped past a river of stars and docked with a soft hiss.",
            "Far above a blue planet, the space station twinkled like a lantern in the dark.",
            "The crew had planned a peaceful science day, but the first alarm chimed before breakfast.",
            "A silver comet sailed past the window just as the station's instruments began to behave strangely.",
        ]
    )

    hero.meters.update(care=1.0, curiosity=1.0)
    helper.meters.update(care=1.0, alertness=1.0)
    hero.memes.update(worry=1.0, hope=1.0)
    helper.memes.update(puzzlement=1.0, friendship=1.0)

    world.say(opening)
    world.say(
        f"At {params.place}, {params.hero_name}, a brave {params.hero_species}, was studying {params.chemical} with {params.helper_name}, a clever {params.helper_species}."
    )
    world.say(
        f"Their premise for the day's experiment was simple: a careful chemical can help a space machine, but only when its clues are understood."
    )
    world.para()
    world.say(f"Suddenly, {mystery['object']} {mystery['problem']}.")
    world.say(
        f"{params.helper_name} pointed at the sample and said, \"Perhaps the {params.chemical} caused it.\""
    )
    world.say(
        f"{params.hero_name} shook their head. \"That is only a guess. Let us solve the cryptic clue before we touch anything.\""
    )
    world.say(f"Beside the device, they found this rhyme: \"{mystery['riddle']}\"")
    world.para()
    world.say(
        f"The first attempt failed because they hurried and used too much {params.chemical}. The device gave a tired beep."
    )
    world.say(f"Then {params.hero_name} noticed that {mystery['clue']}.")
    world.say(
        f"That clue revealed the truth: {mystery['truth']}. The mystery was not a danger; it was a puzzle asking for patience."
    )
    world.say(
        f"\"I know what to do now,\" said {params.hero_name}. \"We will follow every part of the rhyme.\""
    )
    world.say(
        f"\"And I will count each step aloud,\" replied {params.helper_name}. \"Two careful minds are better than one hurried guess.\""
    )
    world.para()
    world.say(
        f"Together they {mystery['method']}. They wore safety gloves, kept the sample sealed, and watched the instruments from behind the clear shield."
    )
    world.say(f"At once, {mystery['result']}.")
    world.say(
        f"{params.helper_name} laughed with relief. \"The cryptic message led us to the happy ending!\""
    )
    world.say(
        f"{params.hero_name} smiled. \"A mystery becomes smaller when friends share clues and care for one another.\""
    )
    world.say(mystery["ending"])
    world.say(
        f"Before bed, the crew wrote the rhyme in their science book so the next space explorers could solve the chemical mystery too."
    )

    hero.memes.update(worry=0.0, confidence=1.0, joy=1.0)
    helper.memes.update(puzzlement=0.0, confidence=1.0, joy=1.0)
    chemical.meters.update(measured=1.0, safe=1.0)
    beacon.meters.update(repaired=1.0, shining=1.0)

    world.facts.update(
        hero=hero,
        helper=helper,
        chemical=chemical,
        beacon=beacon,
        mystery=mystery,
        rhyme=mystery["riddle"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    mystery = world.facts["mystery"]
    return [
        "Write a child-friendly Space Adventure about a chemical mystery.",
        "Include a cryptic clue written as a rhyme and a happy ending.",
        f"Make the heroes solve why {mystery['object']} changed without blaming the chemical too quickly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    chemical = world.facts["chemical"]
    mystery = world.facts["mystery"]
    return [
        QAItem(
            question=f"What mystery did {hero.id} and {helper.id} need to solve?",
            answer=f"They needed to discover why {mystery['object']} {mystery['problem']}.",
        ),
        QAItem(
            question="What was the cryptic rhyme?",
            answer=f"The rhyme said, “{mystery['riddle']}” It gave the heroes the order for their careful work.",
        ),
        QAItem(
            question=f"How did the heroes use the chemical?",
            answer=f"They used {chemical.label} carefully and followed the rhyme instead of guessing. They measured it safely and used it in the proper order.",
        ),
        QAItem(
            question="What clue revealed the real answer?",
            answer=f"They noticed that {mystery['clue']}. This showed that {mystery['truth']}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{mystery['result'].capitalize()}. {mystery['ending']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chemical?",
            answer="A chemical is a kind of material with particular properties. Scientists handle chemicals carefully and follow safety rules.",
        ),
        QAItem(
            question="What does cryptic mean?",
            answer="Cryptic means mysterious or hard to understand at first, like a hidden message that needs clues.",
        ),
        QAItem(
            question="Why can a rhyme help solve a mystery?",
            answer="A rhyme can make instructions easier to remember, while its words may also point toward the order of useful steps.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending shows that the danger or problem has been resolved and that the characters are safe, relieved, or joyful.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id} ({entity.kind}: {entity.label}) {' '.join(details)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Space Adventure world about a chemical cryptic mystery solved in rhyme."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--chemical", choices=CHEMICALS)
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
    place = args.place or rng.choice(PLACES)
    chemical = args.chemical or rng.choice(CHEMICALS)
    hero_name = rng.choice(HERO_NAMES)
    helper_name = rng.choice([name for name in HELPER_NAMES if name != hero_name])
    hero_species = rng.choice(SPECIES)
    helper_species = rng.choice([species for species in SPECIES if species != hero_species])
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_species=hero_species,
        helper_name=helper_name,
        helper_species=helper_species,
        chemical=chemical,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def asp_facts() -> str:
    return "\n".join(
        [
            "setting(space).",
            "feature(mystery_to_solve).",
            "feature(rhyme).",
            "feature(happy_ending).",
            "theme(chemical).",
            "theme(cryptic).",
            "style(space_adventure).",
        ]
    )


ASP_RULES = r"""
valid_story(space, chemical, cryptic, mystery_to_solve, rhyme, happy_ending) :-
    setting(space),
    theme(chemical),
    theme(cryptic),
    feature(mystery_to_solve),
    feature(rhyme),
    feature(happy_ending),
    style(space_adventure).
#show valid_story/6.
"""


def asp_program(show: str = "#show valid_story/6.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    actual = set(asp.atoms(model, "valid_story"))
    expected = {
        (
            "space",
            "chemical",
            "cryptic",
            "mystery_to_solve",
            "rhyme",
            "happy_ending",
        )
    }
    if actual != expected:
        print("MISMATCH:", actual, expected)
        return 1

    params = StoryParams(
        place=PLACES[0],
        hero_name="Luna",
        hero_species="space fox",
        helper_name="Orin",
        helper_species="tiny robot",
        chemical=CHEMICALS[0],
        seed=7,
    )
    sample = generate(params)
    required = ["chemical", "cryptic", "rhyme", "mystery", "happy ending"]
    text = sample.story.lower()
    missing = [word for word in required if word not in text]
    if missing:
        print("MISSING STORY TERMS:", missing)
        return 1
    if not sample.story_qa or not sample.world_qa:
        print("MISSING QA")
        return 1
    print("OK: ASP facts and Python world agree; generated story checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = resolve_params(args, random.Random(base_seed))
        params.seed = base_seed
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        if not asp.atoms(model, "valid_story"):
            raise StoryError("ASP rejected the requested space-adventure story features.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### story {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
