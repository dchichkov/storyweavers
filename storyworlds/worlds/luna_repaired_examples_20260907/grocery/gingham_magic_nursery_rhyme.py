#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about a gingham cloth, a little magic, and a
kind repair in a moonlit kitchen.
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
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
class StoryParams:
    child: str
    helper: str
    charm: str
    mishap: str
    lesson: str
    ending: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Charm:
    name: str
    phrase: str
    power: str
    sign: str


@dataclass(frozen=True)
class Mishap:
    trouble: str
    danger: str
    repair: str
    result: str


@dataclass(frozen=True)
class Lesson:
    temptation: str
    choice: str
    wisdom: str


@dataclass(frozen=True)
class Ending:
    image: str
    line: str


CHARMS = {
    "silver_thimble": Charm(
        "silver thimble",
        "a silver thimble",
        "mend what kindness touches",
        "a tiny star winked on its rim",
    ),
    "blue_button": Charm(
        "blue button",
        "a blue button",
        "make lost things remember home",
        "it hummed a bright little note",
    ),
    "moon_thread": Charm(
        "moon thread",
        "a spool of moon-white thread",
        "weave courage into a careful hand",
        "the thread shone like a puddle of moonlight",
    ),
    "red_ribbon": Charm(
        "red ribbon",
        "a red ribbon",
        "tie a promise so it will not slip away",
        "the ribbon curled into a heart",
    ),
}


MISHAPS = {
    "torn_cloth": Mishap(
        "a sharp teacup handle caught the gingham and tore a long red check",
        "the tear widened whenever the cloth tried to dance",
        "hold the edges together, speak honestly, and stitch slowly with the magic charm",
        "the gingham became whole again, with one shining stitch to remember the trouble",
    ),
    "wandering_squares": Mishap(
        "the gingham squares began to wander off the cloth and march across the floor",
        "the little squares might cover the doorway and leave nobody a clear path",
        "call each square by its color and guide it home one at a time",
        "every square returned to its proper place in a neat red-and-white pattern",
    ),
    "spilled_stars": Mishap(
        "a jar of sugar fell, and bright sugar stars scattered over the gingham",
        "the enchanted stars made the table sparkle so strongly that everyone forgot the supper",
        "cover the stars with a bowl, then share the sparkle instead of chasing it",
        "the stars settled into a gentle border around the cloth",
    ),
    "sleepy_pattern": Mishap(
        "the gingham pattern grew sleepy and forgot which checks belonged beside one another",
        "the cloth sagged like a blanket and slid toward the warm stove",
        "lay it flat, count the checks aloud, and keep watch together",
        "the pattern woke and held firm beneath the cooling pie",
    ),
    "runaway_corner": Mishap(
        "one corner of the gingham fluttered free and flew through the open window",
        "the cloth could snag on the apple tree and tumble into the dark garden",
        "ask the moon breeze for help and knot the corner to a wooden spoon",
        "the corner floated back and rested safely on the table",
    ),
}


LESSONS = {
    "truth": Lesson(
        "hide the first little mistake",
        "tell the truth before the trouble can grow",
        "An honest word is a small lamp in a dark room.",
    ),
    "patience": Lesson(
        "pull hard and finish in a hurry",
        "work slowly enough for every stitch and square to stay safe",
        "Patient hands can mend what hurried hands may tear.",
    ),
    "sharing": Lesson(
        "keep the magic for one special person",
        "let every willing helper hold a safe part of the work",
        "A shared wonder grows brighter without growing smaller.",
    ),
    "listening": Lesson(
        "sing over the quiet warning",
        "listen to the cloth, the breeze, and the helper",
        "A quiet voice may know the safest way home.",
    ),
}


ENDINGS = {
    "moon_table": Ending(
        "The repaired gingham spread beneath the moon, bright as a checkerboard pond",
        "And the kitchen sang, 'Kind hands mend what magic cannot do alone.'",
    ),
    "morning_pie": Ending(
        "By morning, the gingham held a warm pie and one shining stitch",
        "The little house woke to the sweetest rhyme: help first, hurry never.",
    ),
    "window_song": Ending(
        "The gingham rested by the window while the stars sang through its squares",
        "Even the nightingale learned the tune of careful hearts.",
    ),
    "shared_feast": Ending(
        "At last, everyone sat around the gingham cloth and shared the moonlit supper",
        "The magic tasted best when every plate had a place.",
    ),
    "garden_breeze": Ending(
        "The gingham waved softly above the garden, safe from the restless breeze",
        "Its red checks danced, but its faithful corner stayed home.",
    ),
}


NAMES = ["Nell", "Mabel", "Toby", "Pip", "Rose", "Kit"]
HELPERS = ["Grandma", "the moon mouse", "the baker", "the robin"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gingham magic nursery-rhyme storyworld.")
    parser.add_argument("--child")
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--charm", choices=CHARMS)
    parser.add_argument("--mishap", choices=MISHAPS)
    parser.add_argument("--lesson", choices=LESSONS)
    parser.add_argument("--ending", choices=ENDINGS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child or rng.choice(NAMES)
    if child not in NAMES:
        raise StoryError("The child must be one of the story's little names.")
    return StoryParams(
        child=child,
        helper=args.helper or rng.choice(HELPERS),
        charm=args.charm or rng.choice(tuple(CHARMS)),
        mishap=args.mishap or rng.choice(tuple(MISHAPS)),
        lesson=args.lesson or rng.choice(tuple(LESSONS)),
        ending=args.ending or rng.choice(tuple(ENDINGS)),
    )


def tell(params: StoryParams) -> World:
    charm = CHARMS[params.charm]
    mishap = MISHAPS[params.mishap]
    lesson = LESSONS[params.lesson]
    ending = ENDINGS[params.ending]

    world = World()
    child = world.add(Entity("child", "character", params.child, "kitchen"))
    helper = world.add(Entity("helper", "helper", params.helper, "kitchen"))
    cloth = world.add(Entity("gingham", "cloth", "gingham cloth", "table"))
    charm_entity = world.add(Entity("charm", "magic", charm.name, "drawer"))

    world.facts.update(
        child=child,
        helper=helper,
        cloth=cloth,
        charm=charm_entity,
        charm_data=charm,
        mishap_data=mishap,
        lesson_data=lesson,
        ending_data=ending,
    )

    world.say(
        f"Once there was {child.label}, who lived in a little kitchen with "
        f"{params.helper} and a red-and-white gingham cloth."
    )
    world.say(
        f"Each dawn the cloth danced beneath the pie, and each night it folded "
        f"itself with a soft little clap."
    )
    world.say(
        f"But one moonlit evening, {mishap.trouble}."
    )

    world.para()
    cloth.meters["flutter"] = 1.0
    cloth.memes["worry"] = 1.0
    world.say(f"{child.label} reached for it, but {mishap.danger}.")
    world.say(
        f"{child.label} wanted to {lesson.temptation}, yet {params.helper} "
        f"whispered, 'Listen before you leap.'"
    )

    world.para()
    child.memes["honesty"] = 1.0
    child.memes["care"] = 1.0
    world.say(
        f"So {child.label} chose to {lesson.choice}. "
        f"{child.label} fetched {charm.phrase} from the old kitchen drawer."
    )
    world.say(f"{charm.sign.capitalize()}.")
    world.say(
        f"Together, {child.label} and {params.helper} decided to {mishap.repair}."
    )
    world.say(
        f"The charm helped, but the careful work belonged to every patient hand."
    )
    world.say(f"At last, {mishap.result}.")

    cloth.meters["flutter"] = 0.0
    cloth.memes["worry"] = 0.0
    cloth.memes["trust"] = 1.0
    world.facts["resolved"] = True

    world.para()
    world.say(f"{lesson.wisdom}")
    world.say(f"{ending.image}.")
    world.say(ending.line)
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"].label
    mishap = world.facts["mishap_data"]
    return [
        f"Write a nursery rhyme about {child}, a gingham cloth, and gentle magic.",
        f"Tell how {child} repairs this trouble: {mishap.trouble}.",
        "Show why careful kindness matters even when magic is available.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"].label
    helper = world.facts["helper"].label
    charm = world.facts["charm_data"]
    mishap = world.facts["mishap_data"]
    lesson = world.facts["lesson_data"]
    return [
        QAItem(
            f"What trouble happened to {child}'s gingham cloth?",
            f"{mishap.trouble.capitalize()}. It was dangerous because {mishap.danger.lower()}",
        ),
        QAItem(
            f"Who helped {child} repair the gingham?",
            f"{helper} helped {child}, and they worked carefully together instead of relying on magic alone.",
        ),
        QAItem(
            "What magic helped with the repair?",
            f"The {charm.name} helped by letting them {charm.power}.",
        ),
        QAItem(
            "What lesson did the rhyme teach?",
            lesson.wisdom,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is gingham?",
            "Gingham is a woven cloth with an even checked pattern, often made with two colors.",
        ),
        QAItem(
            "Why should a torn cloth be repaired carefully?",
            "A torn cloth should be repaired carefully so the tear does not grow and the cloth can be used safely again.",
        ),
        QAItem(
            "What is magic in this story?",
            "Magic is a playful wonder that helps the characters, while kindness and careful work solve the real problem.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:8} ({entity.kind:9}) location={entity.location} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  resolved={world.facts.get('resolved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(kitchen).
material(gingham).
feature(magic).
style(nursery_rhyme).
valid(kitchen,gingham,magic,nursery_rhyme).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "kitchen"),
            asp.fact("material", "gingham"),
            asp.fact("feature", "magic"),
            asp.fact("style", "nursery_rhyme"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [("kitchen", "gingham", "magic", "nursery_rhyme")]


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py != clingo:
        print("MISMATCH between Python and ASP valid combinations.")
        print("Only in Python:", sorted(py - clingo))
        print("Only in ASP:", sorted(clingo - py))
        return 1

    sample = generate(
        StoryParams(
            child="Nell",
            helper="Grandma",
            charm="silver_thimble",
            mishap="torn_cloth",
            lesson="patience",
            ending="moon_table",
        )
    )
    if "gingham" not in sample.story.lower() or "magic" not in sample.story.lower():
        print("Generated story exercise failed.")
        return 1

    print(f"OK: ASP and Python agree on {len(py)} valid combination.")
    print("OK: generated story exercise passed.")
    return 0


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


def show_qa_item(item: QAItem) -> str:
    return f"Q: {item.question}\nA: {item.answer}"


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
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"[Prompt {index}] {prompt}")
        for item in sample.story_qa + sample.world_qa:
            print()
            print(show_qa_item(item))


CURATED = [
    StoryParams(
        child="Nell",
        helper="Grandma",
        charm="silver_thimble",
        mishap="torn_cloth",
        lesson="truth",
        ending="moon_table",
    ),
    StoryParams(
        child="Pip",
        helper="the moon mouse",
        charm="blue_button",
        mishap="wandering_squares",
        lesson="listening",
        ending="window_song",
    ),
    StoryParams(
        child="Rose",
        helper="the robin",
        charm="moon_thread",
        mishap="runaway_corner",
        lesson="sharing",
        ending="garden_breeze",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 20):
            seed = base_seed + attempt
            attempt += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
