#!/usr/bin/env python3
"""
A small mystery storyworld about chlorophyll, careful choices, and the moral value
of protecting living things. A child detective must discover why the greenhouse
plants are losing their green color before a careless shortcut harms them.
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

    def __post_init__(self) -> None:
        self.meters.setdefault("health", 0.0)
        self.meters.setdefault("light", 0.0)
        self.meters.setdefault("water", 0.0)
        self.memes.setdefault("curiosity", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("trust", 0.0)


@dataclass(frozen=True)
class Setting:
    id: str
    place: str
    affordances: frozenset[str]


@dataclass(frozen=True)
class Clue:
    id: str
    object_name: str
    finding: str
    meaning: str


@dataclass(frozen=True)
class Case:
    id: str
    missing: str
    danger: str
    clue_ids: tuple[str, ...]
    truth: str
    safe_action: str
    result: str
    moral: str


SETTINGS = {
    "greenhouse": Setting(
        "greenhouse",
        "the old school greenhouse",
        frozenset({"sunlight", "plants", "rainwater", "shelves"}),
    ),
    "garden": Setting(
        "garden",
        "the community garden",
        frozenset({"sunlight", "plants", "rainwater", "beds"}),
    ),
    "conservatory": Setting(
        "conservatory",
        "the glass conservatory",
        frozenset({"sunlight", "plants", "rainwater", "benches"}),
    ),
}

CLUES = {
    "muddy_boot": Clue(
        "muddy_boot",
        "a muddy bootprint",
        "a single muddy bootprint crossed the clean tile",
        "someone had carried wet soil toward the west window",
    ),
    "dry_can": Clue(
        "dry_can",
        "an empty watering can",
        "the watering can was dry, although its spout smelled of pond water",
        "the plants had not received ordinary rainwater",
    ),
    "shutter_mark": Clue(
        "shutter_mark",
        "a fresh scrape on the shutter",
        "a pale scrape marked the inside of the west shutter",
        "the shutter had been pulled closed from inside",
    ),
    "green_drop": Clue(
        "green_drop",
        "a green drop on a shelf",
        "one sticky green drop glittered beside the fern shelf",
        "a leaf-cleaning mixture had been spilled",
    ),
    "shadow_ribbon": Clue(
        "shadow_ribbon",
        "a ribbon-shaped shadow",
        "a long shadow cut across the tomato leaves",
        "something had blocked their sunlight for hours",
    ),
    "broken_latch": Clue(
        "broken_latch",
        "a bent latch",
        "the west-window latch was bent but not broken",
        "the window had been forced when someone hurried away",
    ),
}

CASES = {
    "shutter": Case(
        "shutter",
        "the plants' green color was fading",
        "a rushed repair could break the window and chill every plant",
        ("shadow_ribbon", "shutter_mark", "broken_latch"),
        "The west shutter had been closed during the brightest part of the day.",
        "open the shutter gently, check the latch, and let the plants receive safe morning light",
        "The leaves brightened after the sunlight returned, and their chlorophyll could keep making food.",
        "Careful attention protects living things better than a hurried guess.",
    ),
    "mixture": Case(
        "mixture",
        "the leaves were turning dull after a strange green spill",
        "scrubbing the leaves with a harsh cleaner could damage their living cells",
        ("green_drop", "dry_can", "muddy_boot"),
        "Someone had poured pond water mixed with leaf cleaner into the watering can.",
        "rinse the can, use clean rainwater, and wash only the shelf under a teacher's care",
        "The new leaves recovered while the old leaves slowly stopped looking dull.",
        "Honesty and gentle repair are worth more than hiding a mistake.",
    ),
    "water": Case(
        "water",
        "the seedlings were pale and drooping",
        "flooding the beds could drown their roots while trying to help",
        ("dry_can", "muddy_boot", "shadow_ribbon"),
        "The watering can had been left outside, and the seedlings had received neither rainwater nor enough sunlight.",
        "measure clean rainwater, loosen the soil, and move the trays into gentle light",
        "The seedlings stood up without muddy puddles, and their new leaves grew green.",
        "Good care means giving exactly what is needed, not simply doing more.",
    ),
}

NAMES = ["Luna", "Mara", "Theo", "Iris", "Noah", "Pip"]
HELPERS = ["Ms. Vale", "Grandpa Sol", "Aunt Nia", "Mr. Rowan"]
TRAITS = ["patient", "bright", "careful", "curious", "kind"]


@dataclass
class StoryParams:
    setting: str
    case: str
    name: str
    helper: str
    trait: str
    opening: int = 0
    reveal: int = 0
    ending: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.clues_found: list[Clue] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def paragraph(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _lookup(mapping, key):
    if key not in mapping:
        raise StoryError(f"Unknown choice {key!r}. Choose from: {', '.join(mapping)}")
    return mapping[key]


def build_world(params: StoryParams) -> World:
    setting = _lookup(SETTINGS, params.setting)
    case = _lookup(CASES, params.case)
    world = World(setting)

    child = world.add(
        Entity(
            params.name,
            "detective",
            params.name,
            memes={"curiosity": 1.0, "worry": 0.0, "trust": 0.0},
        )
    )
    helper = world.add(
        Entity(
            "helper",
            "helper",
            params.helper,
            memes={"curiosity": 0.0, "worry": 0.0, "trust": 1.0},
        )
    )
    plants = world.add(
        Entity(
            "plants",
            "living_things",
            "the plants",
            meters={"health": 0.4, "light": 0.2, "water": 0.5},
            memes={},
        )
    )
    chlorophyll = world.add(
        Entity(
            "chlorophyll",
            "plant_process",
            "chlorophyll",
            meters={"health": 0.0, "light": 0.0, "water": 0.0},
            memes={},
        )
    )

    case_clues = [CLUES[cid] for cid in case.clue_ids]
    world.facts.update(
        child=child,
        helper=helper,
        plants=plants,
        chlorophyll=chlorophyll,
        case=case,
        clues=case_clues,
    )

    openings = [
        f"{params.name} was a {params.trait} young detective who noticed something wrong in {setting.place}. The leaves looked pale, as if the green had been whispered away.",
        f"At dawn, {params.name} unlocked {setting.place} and stopped at the first bench. Every plant seemed to be holding its breath.",
        f"The mystery began with a quiet color change. In {setting.place}, the leaves were losing their green, and {params.name} was the first to notice.",
        f"{params.name} came to {setting.place} to sketch leaves, but the sketchbook had to wait. The plants were too pale for an ordinary morning.",
    ]
    world.say(openings[params.opening % len(openings)])
    world.say(
        f"The green color came from chlorophyll, the part of a plant that helps it use sunlight to make food."
    )
    world.paragraph()

    world.say(f'"Something blocked the plants or fed them the wrong thing," {params.name} said.')
    world.say(f'"Then investigate before touching anything," {params.helper} replied. "A mystery deserves evidence, and living things deserve care."')
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1

    for index, clue in enumerate(case_clues):
        world.clues_found.append(clue)
        world.say(f"{params.name} examined {clue.object_name}. {clue.finding.capitalize()}.")
        if index == params.reveal % len(case_clues):
            world.say(f'"This clue means {clue.meaning}," {params.name} explained.')
        else:
            world.say(f"The clue suggested that {clue.meaning}.")

    world.paragraph()

    if params.reveal % 2 == 0:
        world.say(f'"I think I know what happened," said {params.name}. "But guessing is not enough."')
        world.say(f'"What will you do?" asked {params.helper}.')
    else:
        world.say(f'"Could we fix it quickly?" asked {params.name}.')
        world.say(f'"Quickly is not always safely," said {params.helper}. "Tell me what the clues prove."')

    world.say(f"{case.truth} {case.safe_action.capitalize()}.")
    child.memes["trust"] += 1
    plants.meters["light"] += 0.8
    plants.meters["water"] += 0.3
    plants.meters["health"] += 0.7
    chlorophyll.meters["light"] += 1.0

    if params.reveal % 3 == 0:
        world.say(f"{params.name} worked slowly, and {case.result}.")
    elif params.reveal % 3 == 1:
        world.say(f"Together they checked each step twice. Then {case.result}.")
    else:
        world.say(f"No one shouted or blamed anyone. After the careful repair, {case.result}.")

    world.paragraph()
    endings = [
        f"By afternoon, {case.moral} {params.name} wrote the solution in the casebook: protect what is alive, even when a shortcut looks tempting.",
        f"{params.helper} smiled as a new green leaf unfolded. {case.moral} The mystery was solved because {params.name} chose care over haste.",
        f"The greenhouse grew quiet again, except for the soft drip of rainwater. {case.moral} The green leaves were proof that a careful choice can help a whole living world.",
        f"{params.name} left one small sign by the shelf: “Look closely. Help gently.” {case.moral}",
    ]
    world.say(endings[params.ending % len(endings)])
    return world


ASP_RULES = r"""
healthy_action(A) :- action(A), protects(A).
safe_case(C) :- case(C), has_clue(C), healthy_action(A), solves(A,C).
valid_case(S,C) :- setting(S), case(C), affords(S,plants), safe_case(C).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for affordance in setting.affordances:
            lines.append(asp.fact("affords", sid, affordance))
    for cid, case in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("has_clue", cid))
    lines.extend(
        [
            asp.fact("action", "careful_repair"),
            asp.fact("protects", "careful_repair"),
            asp.fact("action", "harsh_shortcut"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str = "#show valid_case/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, cid) for sid in SETTINGS for cid in CASES]


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_case")))


def prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]
    return [
        f"Write a child-friendly mystery about chlorophyll fading when {case.missing}.",
        f"Tell a cautionary mystery in which a detective discovers why {case.missing} and chooses {case.safe_action}.",
        "Write a mystery showing the moral value of protecting living things instead of taking a careless shortcut.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    return [
        QAItem(
            "What mystery did the detective investigate?",
            f"{child.label} investigated why {case.missing}.",
        ),
        QAItem(
            "What did the clues reveal?",
            case.truth,
        ),
        QAItem(
            f"How did {child.label} and {helper.label} solve the problem?",
            f"They chose to {case.safe_action}.",
        ),
        QAItem(
            "What was the cautionary lesson?",
            case.moral,
        ),
        QAItem(
            "How did the ending prove that the solution worked?",
            case.result,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is chlorophyll?",
            "Chlorophyll is the green substance in many plants that helps them use sunlight to make food.",
        ),
        QAItem(
            "Why do plants need sunlight?",
            "Plants use sunlight as energy while making food, so too little light can make them weak or pale.",
        ),
        QAItem(
            "What is a moral value?",
            "A moral value is a principle about how to act well, such as honesty, patience, or care for living things.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    sections = ["== prompts =="]
    sections.extend(sample.prompts)
    sections.append("")
    sections.append("== story qa ==")
    for item in sample.story_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    sections.append("")
    sections.append("== world qa ==")
    for item in sample.world_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    return "\n".join(sections)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A chlorophyll cautionary mystery about moral value and careful care."
    )
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--case", choices=sorted(CASES))
    parser.add_argument("--name")
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    settings = [args.setting] if args.setting else list(SETTINGS)
    cases = [args.case] if args.case else list(CASES)
    if not settings or not cases:
        raise StoryError("At least one setting and one case are required.")
    return StoryParams(
        setting=rng.choice(settings),
        case=rng.choice(cases),
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        trait=args.trait or rng.choice(TRAITS),
        opening=rng.randrange(4),
        reveal=rng.randrange(6),
        ending=rng.randrange(4),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"{entity.id}: meters={meters} memes={memes}")
    lines.append("clues=" + ", ".join(clue.id for clue in world.clues_found))
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


def asp_verify() -> int:
    python_pairs = set(valid_combos())
    asp_pairs = set(asp_valid())
    if python_pairs != asp_pairs:
        print("Mismatch between ASP and Python:")
        print("Only Python:", sorted(python_pairs - asp_pairs))
        print("Only ASP:", sorted(asp_pairs - python_pairs))
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or "chlorophyll" not in sample.story:
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP and Python agree on {len(python_pairs)} valid combinations.")
    return 0


CURATED = [
    StoryParams(
        setting="greenhouse",
        case="shutter",
        name="Luna",
        helper="Ms. Vale",
        trait="careful",
        opening=0,
        reveal=1,
        ending=0,
    ),
    StoryParams(
        setting="garden",
        case="mixture",
        name="Theo",
        helper="Mr. Rowan",
        trait="curious",
        opening=1,
        reveal=2,
        ending=1,
    ),
    StoryParams(
        setting="conservatory",
        case="water",
        name="Iris",
        helper="Aunt Nia",
        trait="patient",
        opening=2,
        reveal=4,
        ending=2,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp or args.asp:
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        limit = max(50, args.n * 50)
        while len(samples) < args.n and attempt < limit:
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            attempt += 1

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
