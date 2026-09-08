#!/usr/bin/env python3
"""
A small mythic storyworld about Luna, a pup, and a Hawaiian surprise revealed
by a sonogram.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = STORYWORLDS_ROOT.parent
sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(STORYWORLDS_ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class StoryParams:
    hero: str
    pup: str
    guide: str
    island: str
    surprise: str
    seed: Optional[int] = None
    variant: int = 0
    telling_mode: int = 0


HERO_NAMES = ["Luna", "Maya", "Nia", "Kai", "Leilani"]
PUP_NAMES = ["Piko", "Momo", "Koa", "Tiki", "Nalu"]
GUIDE_NAMES = ["Aunty Hoku", "Uncle Keoni", "Grandma Lehua", "Kumu Ikaika"]
ISLANDS = ["Hawaiian shore", "Kona village", "Maui valley", "Kauai garden"]
SURPRISES = [
    "a tiny heartbeat beneath the pup's blanket",
    "a hidden nest of moon-bright eggs",
    "a lost sea turtle waiting in a warm tide pool",
    "a new litter of puppies curled beneath the canoe shed",
]

OPENINGS = [
    "Long ago on a Hawaiian island, {hero} listened to the waves with {pup}, a small pup who followed every bright shell.",
    "In the old Hawaiian village of {island}, {hero} and {pup} walked beneath palms that whispered like grandmothers.",
    "One golden morning, {hero} carried {pup} through the Hawaiian village while the ocean shone like a blue bowl.",
    "The elders of {island} said that surprises arrived quietly, so {hero} watched carefully while {pup} padded beside her.",
]

DIALOGUE = [
    '"Why is the pup so restless?" {hero} asked. "Perhaps the sea is calling," said {guide}.',
    '"I hear a secret," said {hero}. "{pup} hears it too," replied {guide}.',
    '"Should we hurry?" asked {hero}. "No," said {guide}. "A mystery opens when we are gentle."',
    '"What can the picture mean?" asked {hero}. "Look with your heart as well as your eyes," said {guide}.',
]

TURN_LINES = [
    "The strange sound was not a warning; it was a promise.",
    "At last, the hidden pattern became clear.",
    "The quiet clue had been pointing toward joy all along.",
    "The surprise was greater because nobody had forced it to appear.",
]

LESSONS = [
    "A patient heart can hear a blessing before the eyes can see it.",
    "Gentleness helps hidden wonders come safely into the light.",
    "A surprise becomes brighter when it is welcomed with care.",
    "The smallest clue may carry the largest promise.",
]


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, str] = {}
        self.fired: set[str] = set()

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mythic Hawaiian sonogram surprise storyworld.")
    parser.add_argument("--hero")
    parser.add_argument("--pup")
    parser.add_argument("--guide")
    parser.add_argument("--island")
    parser.add_argument("--surprise")
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
    hero = args.hero or rng.choice(HERO_NAMES)
    pup = args.pup or rng.choice([name for name in PUP_NAMES if name != hero])
    return StoryParams(
        hero=hero,
        pup=pup,
        guide=args.guide or rng.choice(GUIDE_NAMES),
        island=args.island or rng.choice(ISLANDS),
        surprise=args.surprise or rng.choice(SURPRISES),
        seed=args.seed,
        variant=rng.randrange(1_000_000_000),
        telling_mode=rng.randrange(len(OPENINGS)),
    )


def generate_world(params: StoryParams) -> World:
    if not params.hero.strip():
        raise StoryError("hero must not be empty")
    if not params.pup.strip():
        raise StoryError("pup must not be empty")
    world = World(params.island)
    world.add(Entity("hero", "character", params.hero, memes={"curiosity": 0.4}))
    world.add(Entity("pup", "animal", params.pup, meters={"warmth": 0.7}, memes={"trust": 0.8}))
    world.add(Entity("guide", "character", params.guide, memes={"wisdom": 0.9}))
    world.add(Entity("sonogram", "instrument", "sonogram", meters={"clarity": 0.0}))
    world.add(Entity("surprise", "wonder", params.surprise, memes={"joy": 0.0}))
    return world


def tell(world: World, params: StoryParams) -> World:
    rng = random.Random((params.seed or 0) ^ params.variant ^ 0xA17A)
    hero = world.entities["hero"]
    pup = world.entities["pup"]
    guide = world.entities["guide"]
    sonogram = world.entities["sonogram"]
    surprise = world.entities["surprise"]

    opening = OPENINGS[params.telling_mode % len(OPENINGS)].format(
        hero=hero.label, pup=pup.label, island=params.island
    )
    world.say(opening)
    world.say(
        f"That day, {pup.label} kept pressing one paw against a smooth stone, "
        "then looking toward the old healer's hut."
    )
    world.say(
        f"{guide.label} welcomed them and used a sonogram, a gentle machine that "
        "turns hidden movement into a picture."
    )

    world.para()
    world.say(
        f"The first sonogram showed a small pulsing shape beside {pup.label}'s warm blanket. "
        "Nobody could yet tell what it was."
    )
    world.say(rng.choice(DIALOGUE).format(hero=hero.label, pup=pup.label, guide=guide.label))
    world.say(
        f"{hero.label} wanted to lift the blanket at once, but {guide.label} raised a calm hand. "
        "The pup needed quiet, water, and time."
    )
    world.say(
        f"They placed a flower lei near {pup.label}, sang a soft Hawaiian welcome, "
        "and watched the sonogram again."
    )

    world.para()
    world.say(
        f"This time the picture showed the truth: {params.surprise}. "
        "The hidden visitor was alive and safe."
    )
    world.say(rng.choice(TURN_LINES))
    world.say(
        f"{pup.label} wagged so hard that the woven mat trembled. "
        f"{hero.label} laughed, while {guide.label} explained that careful listening had protected the surprise."
    )
    world.say(
        f'"We found it without frightening it," said {hero.label}. '
        f'"That is how a true blessing should be met," said {guide.label}.'
    )

    world.para()
    world.say(
        f"Together they carried fresh water, shaded the resting place, and waited beside {pup.label} "
        "until the sun leaned westward."
    )
    world.say(
        f"When evening came, the Hawaiian sky turned coral. "
        f"{params.surprise.capitalize()} remained safe, and {pup.label} curled proudly beside it."
    )
    world.say(f"{rng.choice(LESSONS)}")
    world.say(
        f"From that day on, the people of {params.island} called the gentle sonogram "
        "the Listening Shell, because it had helped them hear a miracle before they could touch it."
    )

    sonogram.meters["clarity"] = 1.0
    surprise.memes["joy"] = 1.0
    hero.memes["patience"] = 1.0
    guide.memes["wisdom"] = 1.0
    pup.meters["safe"] = 1.0
    world.fired.update({"clue_understood", "surprise_revealed", "wonder_protected"})
    world.facts = {
        "hero": params.hero,
        "pup": params.pup,
        "guide": params.guide,
        "island": params.island,
        "surprise": params.surprise,
        "method": "a sonogram",
        "lesson": rng.choice(LESSONS),
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly Hawaiian myth about {f['hero']} and the pup {f['pup']}.",
        f"Include a sonogram that reveals this surprise: {f['surprise']}.",
        f"Make patience and gentle listening important in {f['island']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem("Who listened for the hidden surprise?", f"{f['hero']} listened with the pup {f['pup']} and {f['guide']}."),
        QAItem("What tool revealed the hidden clue?", f"A sonogram revealed the hidden clue by turning movement into a picture."),
        QAItem("What was the surprise?", f"The surprise was {f['surprise']}."),
        QAItem("Why did the characters wait instead of lifting the blanket quickly?", "They waited so the pup and the hidden visitor would stay calm and safe."),
        QAItem("What lesson did the myth teach?", f"It taught that {f['lesson']}"),
        QAItem("Where did the story happen?", f"It happened in the Hawaiian setting of {f['island']}."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a sonogram?", "A sonogram is a picture made from sound waves that helps people see movement inside or beneath something."),
        QAItem("Why can patience help during a surprise?", "Patience gives people time to understand what is happening and protect everyone involved."),
        QAItem("What is a pup?", "A pup is a young dog."),
        QAItem("What does Hawaiian describe?", "Hawaiian describes things connected with Hawaiʻi, its people, lands, languages, and traditions."),
    ]


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("instrument", "sonogram"),
        asp.fact("animal", "pup"),
        asp.fact("culture", "hawaiian"),
        asp.fact("virtue", "patience"),
        asp.fact("outcome", "surprise"),
    ])


ASP_RULES = r"""
safe_revelation(sonogram, patience, surprise).
myth_instrument(sonogram).
myth_animal(pup).
myth_setting(hawaiian).
good_ending(X) :- safe_revelation(sonogram, patience, X).
#show safe_revelation/3.
#show myth_instrument/1.
#show myth_animal/1.
#show myth_setting/1.
#show good_ending/1.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    required = {
        ("safe_revelation", ("sonogram", "patience", "surprise")),
        ("myth_instrument", ("sonogram",)),
        ("myth_animal", ("pup",)),
        ("myth_setting", ("hawaiian",)),
        ("good_ending", ("surprise",)),
    }
    actual = set()
    for name in ["safe_revelation", "myth_instrument", "myth_animal", "myth_setting", "good_ending"]:
        for args in asp.atoms(model, name):
            actual.add((name, args))
    if actual != required:
        print("MISMATCH between ASP and Python facts.")
        print("ASP:", sorted(actual))
        print("Expected:", sorted(required))
        return 1
    sample = generate(StoryParams("Luna", "Piko", "Aunty Hoku", "Hawaiian shore", SURPRISES[0], seed=7))
    if "sonogram" not in sample.story.lower() or "pup" not in sample.story.lower():
        print("Generated story exercise failed.")
        return 1
    print("OK: ASP parity and generated story exercise passed.")
    return 0


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== Generation prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("== Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("== World questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def generate(params: StoryParams) -> StorySample:
    world = tell(generate_world(params), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("Luna", "Piko", "Aunty Hoku", "Hawaiian shore", SURPRISES[0], seed=11, variant=11),
    StoryParams("Maya", "Koa", "Grandma Lehua", "Maui valley", SURPRISES[2], seed=29, variant=29, telling_mode=2),
]


def format_json(samples: list[StorySample]) -> str:
    if len(samples) == 1:
        return samples[0].to_json()
    return json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(max(0, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        print(format_json(samples))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
