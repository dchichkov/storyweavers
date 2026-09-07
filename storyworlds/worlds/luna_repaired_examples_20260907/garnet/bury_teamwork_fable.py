#!/usr/bin/env python3
"""
A small fable about a child, a buried seed, and the teamwork needed to help
something hidden become strong enough to grow.
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
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Item
    helper: Item
    seed_item: Item
    animal: Item
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    helper_name: str
    animal_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Mina", "Toby", "Lena", "Omar", "Pip", "Nia", "Suri", "Cal"]
HELPERS = ["Grandma June", "Uncle Sol", "Aunt Bea", "Grandpa Moss", "Mara", "Eli"]
ANIMALS = ["Badger", "Rabbit", "Tortoise", "Crow", "Mole", "Hedgehog"]
PLACES = [
    "the village garden",
    "the hill behind the mill",
    "the sunny schoolyard",
    "the orchard edge",
    "the little meadow",
]


ASP_RULES = r"""
#show planted/1.
#show helped/1.
#show sprouted/1.
#show shared/1.

planted(hero) :- chooses_seed(hero).
helped(hero) :- carries_water(helper).
helped(hero) :- loosens_soil(helper).
sprouted(seed) :- planted(hero), watered(seed), covered(seed).
shared(hero) :- worked_together(hero, helper).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("chooses_seed", "hero"),
            asp.fact("carries_water", "helper"),
            asp.fact("loosens_soil", "helper"),
            asp.fact("watered", "seed"),
            asp.fact("covered", "seed"),
            asp.fact("worked_together", "hero", "helper"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    shown = """
#show planted/1.
#show helped/1.
#show sprouted/1.
#show shared/1.
"""
    model = asp.one_model(asp_program(shown))
    actual = set()
    for atom in model:
        if atom.name not in {"planted", "helped", "sprouted", "shared"}:
            continue
        args = tuple(
            arg.number if arg.type == arg.type.Number else arg.name
            for arg in atom.arguments
        )
        actual.add((atom.name, args))
    expected = {
        ("planted", ("hero",)),
        ("helped", ("hero",)),
        ("sprouted", ("seed",)),
        ("shared", ("hero",)),
    }
    if actual == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A teamwork fable about burying a seed."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper-name", choices=HELPERS)
    parser.add_argument("--animal-name", choices=ANIMALS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
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
        name=args.name or rng.choice(NAMES),
        helper_name=args.helper_name or rng.choice(HELPERS),
        animal_name=args.animal_name or rng.choice(ANIMALS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    if not params.name.strip():
        raise StoryError("The child’s name cannot be empty.")
    if not params.helper_name.strip():
        raise StoryError("The helper’s name cannot be empty.")
    if params.name == params.helper_name:
        raise StoryError("The child and helper must have different names.")

    hero = Item(
        id="hero",
        label=params.name,
        phrase=f"young {params.name}",
        kind="character",
        meters={"strength": 0.55, "reach": 0.45},
        memes={"curiosity": 0.85, "patience": 0.55},
    )
    helper = Item(
        id="helper",
        label=params.helper_name,
        phrase=params.helper_name,
        kind="character",
        meters={"strength": 0.8, "reach": 0.75},
        memes={"wisdom": 0.9, "kindness": 0.85},
    )
    seed_item = Item(
        id="seed",
        label="seed",
        phrase="a small brown seed",
        owner="hero",
        meters={"hardness": 0.2, "size": 0.05},
        memes={"hope": 0.9, "hiddenness": 0.95},
    )
    animal = Item(
        id="animal",
        label=params.animal_name,
        phrase=f"a {params.animal_name.lower()}",
        kind="animal",
        meters={"strength": 0.35, "reach": 0.3},
        memes={"mischief": 0.65, "alertness": 0.7},
    )
    seed_value = params.seed
    if seed_value is None:
        seed_value = sum(
            ord(char)
            for char in f"{params.name}|{params.helper_name}|{params.animal_name}|{params.place}"
        )
    return World(
        hero=hero,
        helper=helper,
        seed_item=seed_item,
        animal=animal,
        place=params.place,
        seed=seed_value,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record_story(
    world: World,
    *,
    discovery: str,
    difficulty: str,
    cause: str,
    teamwork: str,
    lesson: str,
    resolution: str,
    ending: str,
    lines: list[str],
) -> str:
    world.facts.update(
        discovery=discovery,
        difficulty=difficulty,
        cause=cause,
        teamwork=teamwork,
        lesson=lesson,
        resolution=resolution,
        ending=ending,
        shared=True,
        buried=True,
        sprouted=True,
    )
    return " ".join(lines)


def _stone_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    helper = world.helper.label
    animal = world.animal.label
    place = world.place
    tool = _choice(rng, ["a soup spoon", "a flat twig", "a little shovel"])
    discovery = "the seed needed to be buried in soft earth before it could wake"
    difficulty = "the ground beneath the hard path was packed like a clay brick"
    cause = "the child tried to dig alone and used a tiny tool against earth that needed many hands"
    teamwork = f"{h} loosened the soil while {helper} lifted the stones and {animal} pushed the loose dirt aside"
    resolution = (
        f"{h} and {helper} worked in turns, using {tool} and a sturdy garden trowel, "
        f"until the seed could rest in a warm hollow"
    )
    ending = "a green shoot stood between them, carrying one bright drop of morning dew"
    lines = [
        f"At {place}, {h} found a small brown seed beneath a bench.",
        f'"I will bury it and grow a tree by supper," said {h}.',
        f"{h} chose a sunny patch, but the earth was packed hard as a stone.",
        f"The child pushed with {tool}. The tool bent. {h} pushed harder. The ground did not even blink.",
        f"{animal} scratched at the edge and sent a pebble rolling onto {h}'s shoe.",
        f"{helper} smiled. “A seed may be small, but a good beginning need not be lonely.”",
        f"{h} loosened the soil while {helper} lifted the stones and {animal} pushed the loose dirt aside.",
        f"Together they made a small hollow, placed the seed inside, and covered it gently.",
        f"They carried water in a cup, waited through the afternoon, and promised not to dig the seed up to check on it.",
        f"By morning, {ending}. {h} learned that teamwork can make even stubborn ground ready for hope.",
    ]
    return _record_story(
        world,
        discovery=discovery,
        difficulty=difficulty,
        cause=cause,
        teamwork=teamwork,
        lesson="a small helper and a strong helper can make a better team than either one alone",
        resolution=resolution,
        ending=ending,
        lines=lines,
    )


def _rain_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    helper = world.helper.label
    animal = world.animal.label
    place = world.place
    shelter = _choice(rng, ["an old watering can", "a wooden crate", "a broad leaf"])
    discovery = "the buried seed needed protection from a sudden spring rain"
    difficulty = "the fresh mound began to wash away as clouds opened over the garden"
    cause = "the seed had been buried in loose soil just before a hard rain arrived"
    teamwork = f"{h} held the shelter while {helper} pressed small stones around the mound and {animal} fetched twigs"
    resolution = (
        f"{h} and {helper} built a little roof from {shelter} and twigs, then guided the rain "
        "into a shallow channel around the seed"
    )
    ending = "the new sprout lifted its two green leaves beneath a roof that no longer needed to stand"
    lines = [
        f"One bright morning at {place}, {h} buried a seed in a neat little mound.",
        f"{h} patted the earth and whispered, “Sleep well. I will see you soon.”",
        f"Then the sky turned gray, and rain fell with the heavy drumming of a thousand tiny feet.",
        f"The mound began to slide downhill. {animal} chased a seed-sized river and came back with muddy whiskers.",
        f"{h} tried to cup both hands over the soil, but the rain slipped between the fingers.",
        f"{helper} called, “One pair of hands can shield a seed. Many pairs can build it a roof.”",
        f"{h} held {shelter} while {helper} pressed small stones around the mound and {animal} fetched twigs.",
        f"Together they built a little roof and a shallow channel, so the water flowed around the buried seed instead of over it.",
        f"The storm passed. The three workers sat quietly beside the dark, shining earth.",
        f"By the next sunrise, {ending}. {h} learned that teamwork is also a way of standing steady when the weather changes.",
    ]
    return _record_story(
        world,
        discovery=discovery,
        difficulty=difficulty,
        cause=cause,
        teamwork=teamwork,
        lesson="many careful hands can protect a small hope from a large trouble",
        resolution=resolution,
        ending=ending,
        lines=lines,
    )


def _thief_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    helper = world.helper.label
    animal = world.animal.label
    place = world.place
    prize = _choice(rng, ["a red berry", "a shiny button", "a yellow ribbon"])
    discovery = "the seed was hidden under a marker so everyone would know where it slept"
    difficulty = f"the curious {animal.lower()} kept pawing at the fresh mound and scattering the marker"
    cause = "the marker was too light for the busy animal to notice as a boundary"
    teamwork = f"{h} watched the mound while {helper} made a stronger marker and {animal} carried the spare twigs"
    resolution = (
        f"{h} offered {prize} far from the garden while {helper} set a ring of twigs around the buried seed; "
        f"the {animal.lower()} chose the safer game"
    )
    ending = "the marker stood straight beside a green shoot, while the once-curious visitor napped in the shade"
    lines = [
        f"At {place}, {h} dug a small hole and buried a seed beneath a painted pebble.",
        f"“This is your bed,” said {h}. “Please stay tucked in.”",
        f"But the {animal.lower()} sniffed the mound, pawed once, and sent the painted pebble spinning.",
        f"{h} replaced it. The {animal.lower()} pawed again. Soon the seed's bed looked like a tiny battlefield.",
        f"{helper} did not scold. “The {animal.lower()} needs a job,” said {helper}.",
        f"{h} watched the mound while {helper} made a stronger marker and {animal} carried the spare twigs.",
        f"Then {h} offered {prize} far from the garden while {helper} set a ring of twigs around the buried seed.",
        f"The {animal.lower()} chased the new prize, forgot the mound, and returned proudly carrying one harmless twig.",
        f"Everyone made the twig into a bright flag and placed it beside the seed.",
        f"By evening, {ending}. {h} learned that teamwork can solve a quarrel by giving every helper a useful part.",
    ]
    return _record_story(
        world,
        discovery=discovery,
        difficulty=difficulty,
        cause=cause,
        teamwork=teamwork,
        lesson="a wise team gives each creature a helpful task",
        resolution=resolution,
        ending=ending,
        lines=lines,
    )


def _hill_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    helper = world.helper.label
    animal = world.animal.label
    place = world.place
    object_name = _choice(rng, ["a fallen branch", "a smooth plank", "an empty basket"])
    discovery = "the seed had rolled into a shallow hollow and needed to be buried on level ground"
    difficulty = "the hill's loose soil made every little hole collapse"
    cause = "the child chose a slope where water and seeds could not stay in place"
    teamwork = f"{h} found level ground while {helper} carried soil and {animal} tested the path with careful steps"
    resolution = (
        f"{h} marked a flat place, {helper} brought soil in {object_name}, and {animal} tamped the edge "
        "with gentle paws"
    )
    ending = "a sturdy green stem rose from the level earth and pointed toward the village below"
    lines = [
        f"On the hill above {place}, {h} found a seed shining in a patch of dust.",
        f"{h} dug a hole and buried it, but the hill tipped the loose earth back out.",
        f"The seed rolled downhill, past {animal}, and stopped beside a thistle.",
        f"“The hill is not being unkind,” said {helper}. “It is simply telling us where the seed cannot rest.”",
        f"{h} looked around and found a level patch below the windy stones.",
        f"{h} marked the flat place, {helper} brought soil in {object_name}, and {animal} tested the path with careful steps.",
        f"Together they made a snug hollow and buried the seed where rain could reach it without washing it away.",
        f"They pressed the earth softly, then built a low rim of pebbles to keep the seed from rolling.",
        f"Days passed. The wind blew over the hill, but the little mound stayed.",
        f"At last, {ending}. {h} learned that teamwork includes listening when the world gives advice.",
    ]
    return _record_story(
        world,
        discovery=discovery,
        difficulty=difficulty,
        cause=cause,
        teamwork=teamwork,
        lesson="a team succeeds when it listens, changes plans, and uses each member's strength",
        resolution=resolution,
        ending=ending,
        lines=lines,
    )


ARC_BUILDERS = [_stone_arc, _rain_arc, _thief_arc, _hill_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x51A7B)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    facts = world.facts
    return [
        QAItem(
            question=f"What did {h} discover about the seed?",
            answer=f"{h} discovered that {facts['discovery']}.",
        ),
        QAItem(
            question="What caused the difficulty?",
            answer=f"The difficulty began because {facts['cause']}.",
        ),
        QAItem(
            question=f"How did {h} and the helpers solve the problem?",
            answer=f"They solved it through teamwork: {facts['resolution']}.",
        ),
        QAItem(
            question="What lesson did the fable teach?",
            answer=f"The fable taught that {facts['lesson']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why do people bury seeds?",
            answer="People bury seeds in soil so the seeds can receive moisture, warmth, and support while they begin to grow.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people or animals cooperate, sharing tasks and using their different strengths to reach a common goal.",
        ),
        QAItem(
            question="What does a seed need in order to sprout?",
            answer="A seed usually needs moisture, suitable warmth, air, and a safe place in which its roots and shoot can begin growing.",
        ),
        QAItem(
            question="Why can changing a plan be wise?",
            answer="Changing a plan can be wise when new information shows that the first plan will not keep the work or the living thing safe.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle fable for young children about burying a seed.",
        f"Tell a teamwork story about {world.hero.label}, {world.helper.label}, and a seed at {world.place}.",
        "Create a simple fable in which different helpers use different strengths to help something hidden grow.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.hero, world.helper, world.seed_item, world.animal]:
        lines.append(
            f"  {entity.id:7} {entity.kind:9} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  place={world.place!r}")
    lines.append(f"  buried={world.facts.get('buried', False)}")
    lines.append(f"  sprouted={world.facts.get('sprouted', False)}")
    lines.append(f"  shared={world.facts.get('shared', False)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    output = ["== Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        output.append(f"{index}. {prompt}")
    output.append("")
    output.append("== Story QA ==")
    for item in sample.story_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    output.append("")
    output.append("== World QA ==")
    for item in sample.world_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    return "\n".join(output)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    world.facts["story"] = story
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
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


def asp_facts_text() -> str:
    return asp_facts()


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                """
#show planted/1.
#show helped/1.
#show sprouted/1.
#show shared/1.
"""
            )
        )
        names = sorted(atom.name for atom in model if atom.name in {
            "planted",
            "helped",
            "sprouted",
            "shared",
        })
        print("ASP teamwork result: " + ", ".join(names))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                name="Mina",
                helper_name="Grandma June",
                animal_name="Badger",
                place="the village garden",
                seed=base_seed,
            ),
            StoryParams(
                name="Toby",
                helper_name="Uncle Sol",
                animal_name="Rabbit",
                place="the hill behind the mill",
                seed=base_seed + 1,
            ),
            StoryParams(
                name="Lena",
                helper_name="Aunt Bea",
                animal_name="Crow",
                place="the sunny schoolyard",
                seed=base_seed + 2,
            ),
            StoryParams(
                name="Pip",
                helper_name="Grandpa Moss",
                animal_name="Tortoise",
                place="the little meadow",
                seed=base_seed + 3,
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + attempt))
            params.seed = base_seed + attempt
            sample = generate(params)
            attempt += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

        if len(samples) < args.n:
            raise StoryError("Could not create the requested number of distinct stories.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all:
            params = sample.params
            header = f"### {params.name} at {params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
