#!/usr/bin/env python3
"""
A small detective-story world about Hope, a snail, and Bahbah the sheep.
Hope follows a trail of clues, while a quiet inner monologue helps turn a
missing garden bell into a solvable mystery.
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

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryState:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    place: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None
    case: int = 0
    opening: int = 0
    clue_order: int = 0
    ending: int = 0


SETTINGS = {
    "garden": Setting("the moonlit garden", {"snail", "bell", "flowers"}),
    "yard": Setting("the quiet yard", {"snail", "bell", "grass"}),
    "orchard": Setting("the little orchard", {"snail", "bell", "trees"}),
}

HERO_NAMES = ["Hope", "Luna", "Mara", "Pip", "Nell"]
FRIEND_NAMES = ["Bahbah", "Bibi", "Moss", "Tilly", "Clover"]

CASES = [
    {
        "sign": "a thin silver trail crossing the stepping stones",
        "wrong": "someone had dragged a tiny spoon away from the flower bed",
        "first_clue": "the trail curved around every dry patch and ended beside a damp leaf",
        "second_clue": "a soft bell mark was pressed into the mud near the leaf",
        "truth": "a snail had carried a fallen bell ribbon through the dew",
        "action": "Hope lifted the ribbon from the grass and tied it back onto the garden bell",
        "lesson": "small clues can lead to a kind answer when a detective takes time",
        "ending": "The snail rested beneath the leaf while the bell chimed gently above it.",
    },
    {
        "sign": "three round drops shining beside the empty birdbath",
        "wrong": "a secret thief had washed muddy coins in the basin",
        "first_clue": "each drop lay beside a pale shell scrape",
        "second_clue": "the scrape continued toward a tipped watering cup",
        "truth": "a snail had passed the cup after rain nudged it onto its side",
        "action": "Bahbah set the cup upright, and Hope placed a smooth stone beside it as a marker",
        "lesson": "a strange pattern becomes clearer when every part of it is checked",
        "ending": "Moonlight touched the stone marker, and the snail's trail curved safely around the cup.",
    },
    {
        "sign": "a tiny muddy footprint beneath the garden gate",
        "wrong": "a miniature detective had escaped with the missing bell",
        "first_clue": "the mark had a shining edge instead of a toe shape",
        "second_clue": "a snail shell glimmered under the gate hinge",
        "truth": "a snail had squeezed under the gate while carrying a loose bell clapper",
        "action": "Hope called the gardener, who repaired the clapper and widened the safe gap",
        "lesson": "a careful question is better than a hurried accusation",
        "ending": "The repaired bell rang once, and the snail continued beneath the gate without being blamed.",
    },
    {
        "sign": "a line of blue petals leading toward the compost box",
        "wrong": "a flower thief had left a coded message",
        "first_clue": "the petals were damp only along one narrow path",
        "second_clue": "a snail shell had brushed blue dust onto the lower petals",
        "truth": "a snail had crossed the flowers after hiding under a blue blossom",
        "action": "Bahbah returned the petals to the soil while Hope moved the compost box away from the path",
        "lesson": "evidence should guide a detective toward care, not blame",
        "ending": "The blue flowers stood again, and the snail glided through a clear, gentle lane.",
    },
]

OPENINGS = [
    "At dusk, Hope opened a small notebook in {place}.",
    "The first star appeared over {place} when Hope began a new case.",
    "Rain had just stopped in {place}, leaving every stone bright.",
    "Hope was checking the garden gate when the mystery began.",
]

CLUE_LINES = [
    "Hope crouched low, studying the marks without touching them.",
    "The detective in Hope wanted to leap to an answer, but the wiser part waited.",
    "Hope took one breath, then another, and compared the clues.",
    "The trail looked mysterious, yet it also looked gentle and slow.",
]

ASP_RULES = r"""
#show valid/2.
setting(garden). setting(yard). setting(orchard).
affords(garden,snail). affords(garden,bell). affords(garden,flowers).
affords(yard,snail). affords(yard,bell). affords(yard,grass).
affords(orchard,snail). affords(orchard,bell). affords(orchard,trees).
valid(P,A) :- setting(P), affords(P,A).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for name, setting in SETTINGS.items():
        lines.append(asp.fact("setting", name))
        for item in sorted(setting.affords):
            lines.append(asp.fact("affords", name, item))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple[str, str]]:
    return sorted((place, item) for place, setting in SETTINGS.items() for item in setting.affords)


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(python_valid())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} combinations).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


def build_world(params: StoryParams) -> StoryState:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    case = CASES[params.case % len(CASES)]
    world = StoryState(SETTINGS[params.place])

    hope = world.add(Entity(
        params.hero_name, "character", "child",
        memes={"hope": 0.8, "curiosity": 0.9, "patience": 0.7},
    ))
    bahbah = world.add(Entity(
        params.friend_name, "character", "sheep",
        memes={"friendship": 0.9, "courage": 0.7},
    ))
    snail = world.add(Entity(
        "snail", "animal", "snail", label="a small snail",
        memes={"calm": 0.9},
        meters={"speed": 0.1},
    ))
    bell = world.add(Entity(
        "bell", "thing", "bell", label="the garden bell",
        owner="gardener",
        meters={"distance": 3.0},
    ))

    place = world.setting.place
    world.say(OPENINGS[params.opening % len(OPENINGS)].format(place=place))
    world.say(f'"The bell is missing its little ribbon," Bahbah said. "Look: {case["sign"]}."')
    world.say(
        f'Hope whispered, "A detective must not guess too soon." '
        f'Inside, Hope thought, *I feel hope because every mystery has a next clue.*'
    )

    world.para()
    world.say(CLUE_LINES[params.clue_order % len(CLUE_LINES)])
    world.say(f"First, {case['first_clue']}.")
    world.say(
        f'"Could the snail have taken it?" Bahbah asked. '
        f'"We will ask what the trail shows," Hope replied.'
    )
    world.say(f"Then they noticed that {case['second_clue']}.")
    world.say(
        f'Hope thought, *The trail is slow, the mark is light, and nobody is in danger. '
        f'I can be careful and still be brave.*'
    )
    world.say(f"The clues pointed to one gentle answer: {case['truth']}.")

    world.para()
    world.say(
        f'"We found the answer without chasing anyone," Hope said. '
        f'"And without frightening the snail," Bahbah replied.'
    )
    world.say(case["action"] + ".")
    world.say(
        f'Hope closed the notebook. "Today I learned that {case["lesson"]}." '
        f'Bahbah nodded, and the snail slipped beneath a safe leaf.'
    )
    world.say(case["ending"])

    world.facts.update(
        hope=hope,
        bahbah=bahbah,
        snail=snail,
        bell=bell,
        case=case,
        place=place,
    )
    return world


def generation_prompts(world: StoryState) -> list[str]:
    case = world.facts["case"]
    return [
        f"Write a detective story in {world.facts['place']} about Hope, a snail, and Bahbah.",
        f"Show Hope solving a mystery involving {case['sign']} through patient clues.",
        "Include inner monologue, dialogue, hope, and a kind resolution.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    case = f["case"]
    return [
        QAItem(
            "Who investigated the mystery?",
            f"{f['hope'].id} investigated the mystery with help from {f['bahbah'].id}. {f['hope'].id} stayed hopeful and checked each clue.",
        ),
        QAItem(
            "What first sign did Hope and Bahbah notice?",
            f"They noticed {case['sign']}. The sign began a careful investigation rather than proving that anyone was guilty.",
        ),
        QAItem(
            "What clues solved the case?",
            f"They found that {case['first_clue']} They also saw that {case['second_clue']} Those details showed that {case['truth']}.",
        ),
        QAItem(
            "How did Hope and Bahbah repair the problem?",
            case["action"] + ".",
        ),
        QAItem(
            "What did Hope learn?",
            f"Hope learned that {case['lesson']}. The lesson helped Hope use hope and patience together.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            "What is a snail?",
            "A snail is a small animal with a soft body that often carries a hard shell and moves slowly.",
        ),
        QAItem(
            "Why do detectives examine clues?",
            "Detectives examine clues because details can help them discover what happened instead of relying on guesses.",
        ),
        QAItem(
            "What is hope?",
            "Hope is the feeling that a good possibility remains, even when a problem has not been solved yet.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.type:8}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.name or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    if hero == friend:
        friend = rng.choice([x for x in FRIEND_NAMES if x != hero])
    return StoryParams(
        place=place,
        hero_name=hero,
        friend_name=friend,
        seed=args.seed,
        case=rng.randrange(len(CASES)),
        opening=rng.randrange(len(OPENINGS)),
        clue_order=rng.randrange(len(CLUE_LINES)),
        ending=rng.randrange(3),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detective storyworld about Hope, a snail, and Bahbah."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--name")
    parser.add_argument("--friend")
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for place, item in asp_valid():
            print(f"{place:10} {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(
                place=place,
                hero_name="Hope",
                friend_name="Bahbah",
                case=list(SETTINGS).index(place) % len(CASES),
                opening=list(SETTINGS).index(place) % len(OPENINGS),
                clue_order=list(SETTINGS).index(place) % len(CLUE_LINES),
                ending=0,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for i in range(max(1, args.n * 30)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
