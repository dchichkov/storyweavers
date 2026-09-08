#!/usr/bin/env python3
"""
A tall tale about Luna, a tattered bowl, and an antic little wind.

The bowl looks ordinary until its first loose thread points toward trouble.
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

_worlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_worlds_dir, "results.py")):
    _worlds_dir = os.path.dirname(_worlds_dir)
sys.path.insert(0, _worlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Tale:
    id: str
    place: str
    warning: str
    antic: str
    repair: str
    ending: str


TALES = {
    "bell_hill": Tale(
        "bell_hill",
        "Bell Hill",
        "the bowl's loose tatter pointed uphill before a single bell had rung",
        "an antic gust that hopped from stone to stone",
        "Luna stitched the bowl with horsehair and set it beneath the bell rope",
        "the repaired bowl caught the first golden raindrop, and every bell on the hill rang at once",
    ),
    "cloud_yard": Tale(
        "cloud_yard",
        "the Cloud Yard",
        "the tatter tugged toward the only cloud wearing a silver button",
        "an antic cloud that sneezed small thunderclaps",
        "Luna tied the tatter down with a braid of blue grass",
        "the bowl held the cloud's rain, and the yard floated three inches higher",
    ),
    "giant_garden": Tale(
        "giant_garden",
        "the Giant's Garden",
        "the tatter trembled whenever the tallest sunflower leaned too far",
        "an antic beetle big enough to wear a wheelbarrow as a hat",
        "Luna turned the bowl into a bright brace beneath the sunflower's stem",
        "the sunflower stood straight and cast a shadow over the whole county",
    ),
    "moon_dock": Tale(
        "moon_dock",
        "Moon Dock",
        "the tatter pointed at a boat that was tied to the moon instead of the shore",
        "an antic tide that climbed stairs backward",
        "Luna patched the bowl with a strip of sailcloth and used it to scoop the rising water",
        "the moonboat sailed safely home and left a trail of silver fish",
    ),
}

NAMES = ["Luna", "Mara", "Toby", "Nell", "Pip"]
TRAITS = ["bold", "patient", "curious", "nimble", "cheerful"]


@dataclass
class StoryParams:
    tale: str = "bell_hill"
    name: str = "Luna"
    trait: str = "curious"
    seed: Optional[int] = None


class World:
    def __init__(self, tale: Tale, params: StoryParams):
        self.tale = tale
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.facts: dict[str, str] = {}
        self.paragraphs: list[list[str]] = [[]]

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


def _meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def _meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def build_world(params: StoryParams, rng: random.Random) -> World:
    if params.tale not in TALES:
        raise StoryError(f"Unknown tale: {params.tale}")
    if not params.name.strip():
        raise StoryError("The hero's name cannot be empty.")
    if not params.trait.strip():
        raise StoryError("The hero needs a clear trait.")

    tale = TALES[params.tale]
    world = World(tale, params)
    luna = world.add(Entity(params.name, "character", params.name))
    bowl = world.add(Entity("bowl", "object", "a tattered bowl"))
    wind = world.add(Entity("antic_wind", "force", "the antic wind"))
    _meme(luna, "curiosity")
    _meter(bowl, "tattered")

    openings = [
        f"In {tale.place}, {params.name} was the most {params.trait} person for seven counties and a bit of the eighth.",
        f"People in {tale.place} said {params.name} was so {params.trait} that even the morning sun followed along to see what happened.",
        f"Once, in {tale.place}, {params.name} found a question hiding where sensible people usually found breakfast.",
    ]
    world.say(rng.choice(openings))
    world.say(
        f"That morning, {params.name} discovered a tattered bowl beside the road. "
        f"It had one crooked rim, two brave cracks, and a tatter that fluttered like a tiny flag."
    )
    world.para()

    world.say(
        f"At first the bowl seemed useless, but {tale.warning}. "
        f"{params.name} picked it up, and the bowl gave a faint wooden clack."
    )
    world.say(
        f'"A bowl should not point at trouble," said {params.name}. '
        f'"Perhaps this one has been practicing."'
    )
    world.say(
        f'"Perhaps it has," replied the antic wind, which was hiding in a thistle. '
        f'"But do not mend the wrong thing."'
    )
    _meme(luna, "worry")
    _meter(bowl, "foreshadowing", 1.0)

    world.para()
    world.say(
        f"The wind began an antic dance: {tale.antic}. "
        f"It spun the bowl in a circle, but the loose tatter kept pointing toward the same danger."
    )
    world.say(
        f"{params.name} watched instead of chasing the commotion. "
        f"The crooked rim showed where the bowl had been struck, and the tatter showed what needed protecting."
    )
    _meter(luna, "observed")
    _meme(luna, "problem_solving")

    world.say(
        f'"The tatter told us first," said {params.name}. '
        f'"Now the bowl can help us tell the rest."'
    )
    world.say(
        f'"That is a fine plan," said the wind. "A small clue can pull a very large story into place."'
    )
    world.say(f"{params.name} {tale.repair}.")
    _meter(bowl, "repaired")
    _meter(bowl, "protective")

    world.para()
    world.say(f"The danger passed because {tale.ending}.")
    _meme(luna, "joy")
    world.say(
        f"From then on, whenever anyone called the bowl useless, {params.name} pointed to its tatter. "
        "The smallest loose thread, after all, may be the first knot in a very tall tale."
    )

    world.facts.update(
        hero=params.name,
        place=tale.place,
        warning=tale.warning,
        antic=tale.antic,
        repair=tale.repair,
        ending=tale.ending,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else f"{params.tale}:{params.name}")
    world = build_world(params, rng)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a Tall Tale about {params.name} finding a tattered bowl in {world.tale.place}.",
            f"Use foreshadowing: show how {world.tale.warning} before the problem is understood.",
            f"Include an antic wind, spoken dialogue, and a repair that uses the bowl's tatter as a clue.",
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Where did {f['hero']} find the tattered bowl?",
            answer=f"{f['hero']} found the tattered bowl in {f['place']}."
        ),
        QAItem(
            question="What foreshadowed that trouble was coming?",
            answer=f"The bowl's loose tatter pointed toward trouble: {f['warning']}."
        ),
        QAItem(
            question="What made the middle of the story antic?",
            answer=f"The antic wind caused a wild disturbance: {f['antic']}."
        ),
        QAItem(
            question="How did the hero use the bowl?",
            answer=f"{f['hero']} repaired the bowl by {f['repair']}."
        ),
        QAItem(
            question="What proved that the repair worked?",
            answer=f"The repair worked because {f['ending']}."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bowl?",
            answer="A bowl is a round container with an open top, often used for holding food or other things."
        ),
        QAItem(
            question="What does tattered mean?",
            answer="Tattered means torn, worn, or full of loose threads and ragged edges."
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue placed early in a story that hints at something important later."
        ),
        QAItem(
            question="What is an antic action?",
            answer="An antic action is a playful, surprising, and often silly movement."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.label}: meters={meters} memes={memes}")
    lines.append(f"  foreshadowing clue fired: {'foreshadowing' in world.fired or world.entities['bowl'].meters.get('foreshadowing', 0) > 0}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
tale(bell_hill; cloud_yard; giant_garden; moon_dock).
has_bowl(tale).
foreshadowing(tale) :- has_bowl(tale).
valid(Tale) :- tale(Tale), foreshadowing(Tale).
#show valid/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("tale", key) for key in TALES)


def asp_program(show: str = "#show valid/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_tales() -> set[str]:
    import asp
    model = asp.one_model(asp_program())
    return {str(row[0]) for row in asp.atoms(model, "valid")}


def asp_verify() -> int:
    expected = set(TALES)
    actual = asp_valid_tales()
    if actual == expected:
        print(f"OK: ASP matches Python ({len(actual)} tales).")
        for key in sorted(expected):
            sample = generate(StoryParams(tale=key, seed=17))
            if not sample.story.strip():
                print(f"FAIL: empty story for {key}")
                return 1
        print("OK: generated stories are non-empty.")
        return 0
    print("Mismatch between ASP and Python.")
    print("Only ASP:", sorted(actual - expected))
    print("Only Python:", sorted(expected - actual))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A Tall Tale of a tattered bowl and an antic clue.")
    parser.add_argument("--tale", choices=TALES, default=None)
    parser.add_argument("--name", default=None)
    parser.add_argument("--trait", choices=TRAITS, default=None)
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
    tale = args.tale or rng.choice(list(TALES))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(tale=tale, name=name, trait=trait)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
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
        print("Valid tales:")
        for tale in sorted(asp_valid_tales()):
            print(f"  {tale}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, tale in enumerate(TALES):
            params = StoryParams(
                tale=tale,
                name=NAMES[index % len(NAMES)],
                trait=TRAITS[index % len(TRAITS)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        for index in range(max(0, args.n)):
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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
