#!/usr/bin/env python3
"""A gentle nursery-rhyme story about a comma, a bangle, magic, and kindness."""

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


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class RhymeCase:
    key: str
    place: str
    trouble: str
    clue: str
    kindness: str
    magic: str
    ending: str
    lesson: str
    color: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    helper: str = "Milo"
    place: str = "Moonlit Meadow"
    case: str = "moon_gate"
    rhyme_mode: int = 0
    dialogue_mode: int = 0
    magic_mode: int = 0


@dataclass
class World:
    case: RhymeCase
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


CASES = {
    "moon_gate": RhymeCase(
        "moon_gate",
        "Moonlit Meadow",
        "the little silver gate would not open for the night parade",
        "a comma-shaped sparkle rested beneath the latch",
        "Luna asked a tired firefly to rest while she carried the lantern",
        "the bangle hummed, and its warm light drew a gentle curve around the latch",
        "the gate swung wide, and every small creature entered beneath the stars",
        "A kind pause can make room for magic.",
        "silver",
    ),
    "raindrop_bridge": RhymeCase(
        "raindrop_bridge",
        "Raindrop Lane",
        "a puddle covered the tiny bridge where the ducklings needed to cross",
        "the bangle shone beside a comma-shaped leaf",
        "Luna shared her red umbrella with the smallest duckling",
        "the comma sparkle rose and became a stepping-stone of moonlight",
        "the ducklings crossed in a row while the puddle twinkled below",
        "Kindness can turn a pause into a path.",
        "blue",
    ),
    "sleepy_clock": RhymeCase(
        "sleepy_clock",
        "Whispering Village",
        "the village clock had stopped before bedtime",
        "one bright comma gleamed on the silent bell",
        "Luna listened while the lonely clock-keeper told his worry",
        "the bangle chimed a soft, patient note that woke the clock's friendly spring",
        "the clock rang once, then twice, and everyone rested peacefully",
        "Listening kindly can wake a quiet hope.",
        "golden",
    ),
    "garden_ribbon": RhymeCase(
        "garden_ribbon",
        "Clover Garden",
        "the ribbon bridge had tangled around the old oak tree",
        "a comma-shaped loop glittered in the grass",
        "Luna untied the ribbon slowly instead of pulling it hard",
        "the bangle cast a little wind that lifted each knot like a feather",
        "the bridge fluttered free, and the garden wore a shining bow",
        "Gentle hands help hidden magic bloom.",
        "green",
    ),
}

HEROES = ("Luna", "Nell", "Pip", "Mara")
HELPERS = ("Milo", "Tess", "Robin", "Ari")

OPENINGS = (
    "By moonbeam bright, in a hush-hush night,",
    "In a meadow mild, where dreamers smiled,",
    "When silver stars began to sing,",
    "At twilight's door, on a dewy floor,",
    "One little pause, with a magical cause,",
    "Beneath a cloud in a sleepy crowd,",
)

DIALOGUES = (
    '"I will help," said {hero}. "A pause is small, but care can grow it tall."',
    '"Do not hurry," said {helper}. "Kind hands may find the hidden way."',
    '"Shall we listen first?" asked {hero}. "Then we can choose what to do."',
    '"Your worry matters," said {hero}. "We can face it together."',
    '"A little kindness," said {helper}, "may wake a little wonder."',
)

MAGIC_LINES = (
    "The bangle gave a tinkly ring, and the comma began to glow.",
    "A tiny silver shimmer curled like a comma in the air.",
    "The bangle warmed with a friendly hum, as if the moon had whispered, \"Try kindness.\"",
    "Magic tiptoed out of the bangle in a bright, comma-shaped curl.",
)

ASP_RULES = r"""
item(comma).
item(bangle).
feature(magic).
feature(kindness).
kind_action(C) :- feature(kindness), action(C).
magic_help(C) :- feature(magic), action(C).
good_turn(C) :- kind_action(C), magic_help(C).
solved(C) :- good_turn(C), case_fact(C).
"""


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("item", "comma"),
        asp.fact("item", "bangle"),
        asp.fact("feature", "magic"),
        asp.fact("feature", "kindness"),
    ]
    facts.extend(asp.fact("case_fact", key) for key in CASES)
    facts.extend(asp.fact("action", key) for key in CASES)
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A nursery-rhyme story about a comma, a bangle, magic, and kindness."
    )
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--place")
    parser.add_argument("--case", choices=sorted(CASES))
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
    case_key = args.case or rng.choice(list(CASES))
    case = CASES[case_key]
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(HEROES),
        helper=args.helper or rng.choice(HELPERS),
        place=args.place or case.place,
        case=case_key,
        rhyme_mode=rng.randrange(len(OPENINGS)),
        dialogue_mode=rng.randrange(len(DIALOGUES)),
        magic_mode=rng.randrange(len(MAGIC_LINES)),
    )


def tell(params: StoryParams) -> World:
    if params.case not in CASES:
        raise StoryError(f"Unknown rhyme case: {params.case}")
    if not params.hero.strip() or not params.helper.strip():
        raise StoryError("Hero and helper names must not be empty.")

    case = CASES[params.case]
    world = World(case)
    hero = world.add(
        Entity(
            params.hero,
            "child",
            params.hero,
            meters={"distance": 0.0, "patience": 1.0},
            memes={"kindness": 2.0, "courage": 1.0},
        )
    )
    helper = world.add(
        Entity(
            params.helper,
            "friend",
            params.helper,
            meters={"distance": 0.0},
            memes={"kindness": 1.0, "trust": 1.0},
        )
    )
    comma = world.add(
        Entity(
            "comma",
            "symbol",
            "the comma",
            meters={"brightness": 0.4},
            memes={"magic": 1.0},
        )
    )
    bangle = world.add(
        Entity(
            "bangle",
            "jewel",
            "the bangle",
            meters={"warmth": 0.3},
            memes={"magic": 1.0},
        )
    )

    world.say(f"{OPENINGS[params.rhyme_mode]} {params.hero} came skipping along.")
    world.say(
        f"In {params.place}, {case.trouble}; the night felt still, and the small stars hummed a song."
    )
    world.say(f"Near the trouble, {params.hero} saw that {case.clue}.")
    world.para()

    world.say(DIALOGUES[params.dialogue_mode].format(hero=params.hero, helper=params.helper))
    world.say(f"{params.helper} nodded. Together they chose to {case.kindness}.")
    world.say(f"{params.hero} did not tug or shout; {params.hero} waited, watched, and helped.")
    world.say(MAGIC_LINES[params.magic_mode])
    world.say(f"{case.magic}.")
    world.say(
        f"The comma made a little pause, the bangle made a little light, and kindness made the right choice bright."
    )
    world.para()

    world.say(f"Then {case.ending}.")
    world.say(f"{params.hero} smiled at {params.helper}. \"We made room for wonder.\"")
    world.say(f"{params.helper} replied, \"And wonder grew because you were kind.\"")
    world.say(f"{case.lesson} So they sang this rhyme:")
    world.say(
        f"\"Comma for a pause, bangle for a gleam, "
        f"kindness wakes the magic in a dream!\""
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        comma=comma,
        bangle=bangle,
        case=case,
        solved=True,
        magic=True,
        kindness=True,
    )
    world.trace.extend(
        [
            f"case:{case.key}",
            f"place:{params.place}",
            "symbol:comma",
            "jewel:bangle",
            "feature:magic",
            "feature:kindness",
            f"kind_action:{case.kindness}",
            f"magic_result:{case.magic}",
            "state:solved",
        ]
    )
    return world


def generation_prompts(world: World) -> list[str]:
    case: RhymeCase = world.facts["case"]
    hero: Entity = world.facts["hero"]
    return [
        f"Write a child-friendly nursery rhyme about {hero.label}, a comma, and a bangle.",
        f"Include a magical kindness choice at {case.place}, where {case.trouble}.",
        f"Show that {case.magic} and end with the lesson: {case.lesson}",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: RhymeCase = world.facts["case"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    return [
        QAItem(
            question=f"What trouble did {hero.label} find?",
            answer=f"At {case.place}, {case.trouble}.",
        ),
        QAItem(
            question="What did the comma-shaped clue show?",
            answer=f"It showed that {case.clue}.",
        ),
        QAItem(
            question=f"How did {hero.label} show kindness?",
            answer=f"{hero.label} chose to {case.kindness}.",
        ),
        QAItem(
            question="How did the bangle help?",
            answer=f"The bangle helped because {case.magic}.",
        ),
        QAItem(
            question=f"What did {hero.label} and {helper.label} learn?",
            answer=case.lesson,
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a comma used for?",
            answer="A comma can mark a short pause in a sentence.",
        ),
        QAItem(
            question="What made the magic helpful rather than frightening?",
            answer="The magic was guided by kindness, patience, and a wish to help.",
        ),
        QAItem(
            question="Why did waiting matter in the story?",
            answer="Waiting helped the characters notice the clue and choose a gentle action instead of making the trouble worse.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.extend(f"  {entry}" for entry in world.trace)
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id} ({entity.kind}) meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts={sorted(world.facts)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(("", "== World questions =="))
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


CURATED = [
    StoryParams(case="moon_gate", hero="Luna", helper="Milo", rhyme_mode=0, dialogue_mode=0, magic_mode=0),
    StoryParams(case="raindrop_bridge", hero="Nell", helper="Tess", rhyme_mode=2, dialogue_mode=1, magic_mode=1),
    StoryParams(case="sleepy_clock", hero="Pip", helper="Robin", rhyme_mode=4, dialogue_mode=2, magic_mode=2),
    StoryParams(case="garden_ribbon", hero="Mara", helper="Ari", rhyme_mode=3, dialogue_mode=3, magic_mode=3),
]


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1

    show = (
        "#show item/1.\n"
        "#show feature/1.\n"
        "#show solved/1.\n"
        "#show good_turn/1.\n"
    )
    model = asp.one_model(asp_program(show))
    if not model:
        print("ASP produced no model.")
        return 1
    items = set(asp.atoms(model, "item"))
    features = set(asp.atoms(model, "feature"))
    solved = set(asp.atoms(model, "solved"))
    if ("comma",) not in items or ("bangle",) not in items:
        print("ASP parity failed for items.")
        return 1
    if ("magic",) not in features or ("kindness",) not in features:
        print("ASP parity failed for features.")
        return 1
    if len(solved) != len(CASES):
        print("ASP parity failed for solved cases.")
        return 1

    for params in CURATED:
        sample = generate(params)
        if "comma" not in sample.story.lower() or "bangle" not in sample.story.lower():
            print("Story parity failed: required words missing.")
            return 1
        if "magic" not in sample.story.lower() and "magical" not in sample.story.lower():
            print("Story parity failed: magic missing.")
            return 1
        if "kind" not in sample.story.lower():
            print("Story parity failed: kindness missing.")
            return 1

    print("OK: ASP/Python parity and generated stories verified.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
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


def main() -> None:
    args = build_parser().parse_args()
    show = (
        "#show item/1.\n"
        "#show feature/1.\n"
        "#show solved/1.\n"
        "#show good_turn/1.\n"
    )

    if args.show_asp:
        print(asp_program(show))
        return

    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise SystemExit(f"ASP unavailable: {exc}")
        model = asp.one_model(asp_program(show))
        print(json.dumps([str(atom) for atom in model], indent=2))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for offset in range(max(0, args.n)):
            seed = base_seed + offset
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
