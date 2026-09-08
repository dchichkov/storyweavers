#!/usr/bin/env python3
"""
A tiny mystery storyworld about mozzarella, a missing picnic moon, and a happy
ending discovered through careful clues.
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


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass
class Setting:
    id: str
    label: str
    affordances: set[str]


@dataclass
class Mystery:
    id: str
    missing_item: str
    material: str
    clue: str
    hiding_place: str
    solution: str


@dataclass(frozen=True)
class StoryParams:
    setting: str
    mystery: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, str] = {}
        self.events: list[str] = []
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.events.append(text)

    def render(self) -> str:
        return "\n\n".join(self.events)


SETTINGS = {
    "meadow": Setting("meadow", "the sunny meadow", {"picnic", "search"}),
    "kitchen": Setting("kitchen", "the little kitchen", {"picnic", "search"}),
    "orchard": Setting("orchard", "the old orchard", {"picnic", "search"}),
}

MYSTERIES = {
    "mozzarella_moon": Mystery(
        id="mozzarella_moon",
        missing_item="the round mozzarella moon",
        material="fresh mozzarella",
        clue="a white thread of mozzarella stretched toward the picnic basket",
        hiding_place="under a folded red napkin",
        solution="the cheese moon had rolled away when the basket was bumped",
    )
}

NAMES = ["Luna", "Milo", "Nora", "Tess", "Pip"]
HELPERS = ["Mara", "Ollie", "Bea", "Theo", "Mimi"]
TRAITS = ["curious", "careful", "cheerful", "patient", "brave"]

CURATED = [
    StoryParams("meadow", "mozzarella_moon", "Luna", "Mara", "curious", 11),
    StoryParams("kitchen", "mozzarella_moon", "Milo", "Bea", "careful", 12),
    StoryParams("orchard", "mozzarella_moon", "Nora", "Theo", "patient", 13),
]


def _lookup(mapping: dict, key: str):
    if key not in mapping:
        raise StoryError(f"Unknown choice {key!r}. Choose one of: {', '.join(mapping)}.")
    return mapping[key]


def build_world(params: StoryParams, rng: random.Random) -> World:
    setting = _lookup(SETTINGS, params.setting)
    mystery = _lookup(MYSTERIES, params.mystery)
    if "search" not in setting.affordances:
        raise StoryError(f"{setting.label} is not suitable for a search.")
    world = World(setting)
    hero = world.add(Entity(params.name, "character", params.name, location=setting.id))
    helper = world.add(Entity(params.helper, "character", params.helper, location=setting.id))
    object_entity = world.add(
        Entity(
            "mozzarella",
            "food",
            "the mozzarella moon",
            meters={"round": 1.0, "missing": 1.0},
            location="unknown",
        )
    )
    world.facts.update(
        hero=params.name,
        helper=params.helper,
        mystery=mystery.id,
        clue=mystery.clue,
        hiding_place=mystery.hiding_place,
    )

    world.say(
        f"{hero.label} was a {params.trait} child who loved solving small mysteries."
    )
    world.say(
        f"At {setting.label}, {hero.label} and {helper.label} prepared a picnic with "
        "bright tomatoes, basil leaves, and a round piece of mozzarella shaped like a moon."
    )
    world.say(
        f"When they turned back, {mystery.missing_item} was gone. "
        f"The basket sat open, and one corner of the cloth was crooked."
    )
    hero.memes["curiosity"] = 1.0
    hero.memes["worry"] = 1.0
    world.say(
        f'"The mozzarella cannot simply vanish," said {hero.label}. '
        f'"Then let us look for what it left behind," replied {helper.label}.'
    )
    world.say(
        f"{hero.label} knelt beside the picnic cloth and noticed that {mystery.clue}."
    )
    hero.meters["observed"] = 1.0
    hero.memes["problem_solving"] = 1.0
    world.say(
        f'"A trail means the moon moved," {hero.label} said. '
        f'"And the crooked cloth tells us which way it went," {helper.label} answered.'
    )
    world.say(
        f"They followed the tiny trail around the basket. It ended {mystery.hiding_place}."
    )
    object_entity.location = "under_napkin"
    object_entity.meters["missing"] = 0.0
    object_entity.meters["found"] = 1.0
    world.fired.add("mozzarella_found")
    world.say(
        f"{hero.label} lifted the napkin gently, and there it was: {mystery.solution}."
    )
    world.say(
        f"{helper.label} laughed with relief. \"The mystery is solved, and the mozzarella is safe!\""
    )
    hero.memes["joy"] = 1.0
    world.say(
        f"They placed the mozzarella moon back on the picnic plate, where it shone beside "
        "the red tomatoes and green basil."
    )
    world.say(
        f"Everyone shared the picnic, and {hero.label} learned that careful clues can lead "
        "a worried heart to a happy ending."
    )
    return world


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else params.name)
    world = build_world(params, rng)
    mystery = MYSTERIES[params.mystery]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a child-friendly mystery about {params.name} finding missing mozzarella.",
            f"Show how a clue helps {params.name} solve the mystery at {SETTINGS[params.setting].label}.",
            "End with a warm, happy picnic after the missing cheese is found.",
        ],
        story_qa=[
            QAItem(
                f"What disappeared from the picnic?",
                f"The round mozzarella moon disappeared from the picnic.",
            ),
            QAItem(
                f"What clue did {params.name} notice?",
                f"{params.name} noticed that {mystery.clue}.",
            ),
            QAItem(
                f"How was the mozzarella found?",
                f"They followed the mozzarella trail, which ended {mystery.hiding_place}.",
            ),
            QAItem(
                "How did the story end?",
                "The mozzarella was returned to the plate, and everyone shared a happy picnic.",
            ),
        ],
        world_qa=[
            QAItem(
                "What is mozzarella?",
                "Mozzarella is a soft, mild cheese often used on pizza, salads, and sandwiches.",
            ),
            QAItem(
                "Why are clues useful in a mystery?",
                "Clues provide information that helps people figure out what happened.",
            ),
            QAItem(
                "What makes an ending happy?",
                "A happy ending resolves the trouble and leaves the characters safe, relieved, or joyful.",
            ),
        ],
        world=world,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---", f"  setting: {world.setting.label}"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.label}: location={entity.location}, meters={meters}, memes={memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid_setting(S) :- setting(S), affords(S, search).
valid_mystery(M) :- mystery(M), has_material(M, mozzarella).
compatible(S, M) :- valid_setting(S), valid_mystery(M).
#show compatible/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for affordance in sorted(setting.affordances):
            lines.append(asp.fact("affords", sid, affordance))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        if mystery.material == "fresh mozzarella":
            lines.append(asp.fact("has_material", mid, "mozzarella"))
    return "\n".join(lines)


def asp_program(show: str | None = None) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show or ''}\n"


def asp_valid_pairs() -> set[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "compatible"))


def python_valid_pairs() -> set[tuple[str, str]]:
    return {
        (setting_id, mystery_id)
        for setting_id, setting in SETTINGS.items()
        if "search" in setting.affordances
        for mystery_id, mystery in MYSTERIES.items()
        if mystery.material == "fresh mozzarella"
    }


def asp_verify() -> int:
    expected = python_valid_pairs()
    actual = asp_valid_pairs()
    if expected != actual:
        print("ASP/Python mismatch.")
        print("Only in ASP:", sorted(actual - expected))
        print("Only in Python:", sorted(expected - actual))
        return 1
    for params in CURATED:
        sample = generate(params)
        if "mozzarella" not in sample.story.lower() or "happy" not in sample.story.lower():
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP matches Python ({len(actual)} compatible pairs); stories verified.")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or "mozzarella_moon"
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice([x for x in HELPERS if x != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, mystery, name, helper, trait, args.seed)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A mozzarella mystery with a happy ending.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--mystery", choices=MYSTERIES)
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--trait", choices=TRAITS)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        for pair in sorted(asp_valid_pairs()):
            print(pair)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        for index in range(max(0, args.n)):
            seed = base_seed + index
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = seed
            params = resolve_params(local_args, random.Random(seed))
            samples.append(generate(params))

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
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
