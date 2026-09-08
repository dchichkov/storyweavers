#!/usr/bin/env python3
"""
A child-facing mystery storyworld about a kabob, a gleam, and a shared clue.

The simulation tracks a small picnic mystery. Repeated clues build suspense,
and sharing information lets the children solve the mystery together.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "storyworlds" / "results.py").is_file()
)
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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


@dataclass
class StoryParams:
    name: str
    friend: str
    place: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class MysteryCase:
    key: str
    object_name: str
    gleam: str
    first_clue: str
    second_clue: str
    hiding_place: str
    owner: str
    explanation: str
    ending_image: str


PLACES = {
    "pine picnic": "the pine picnic table",
    "old orchard": "the old orchard bench",
    "river meadow": "the river meadow",
    "lantern garden": "the lantern garden",
}

NAMES = ["Luna", "Mara", "Niko", "Tavi", "Iris", "Owen", "Pia", "Sol"]
FRIENDS = ["Milo", "Nell", "Ari", "Bea", "Kito", "Rina", "Theo", "Uma"]

CASES = [
    MysteryCase(
        "silver_skewer",
        "a missing silver skewer",
        "a thin gleam under the picnic cloth",
        "a bright speck appeared beside the empty plate",
        "the same gleam flashed near the basket handle",
        "inside the basket's loose lining",
        "the picnic caretaker",
        "The skewer had slipped through a tear in the basket lining when the caretaker carried it away.",
        "The silver skewer rested beside the basket, shining like a tiny moon.",
    ),
    MysteryCase(
        "red_pepper",
        "a red pepper from the kabob",
        "a red gleam beneath the bench",
        "one red shine winked by the table leg",
        "another red shine blinked beside the napkins",
        "under a folded picnic blanket",
        "the wind",
        "The wind had rolled the pepper from the kabob beneath the blanket.",
        "The rescued pepper glowed on the plate while the blanket lay still.",
    ),
    MysteryCase(
        "golden_bead",
        "a golden bead from a bracelet",
        "a warm gleam beside the kabob sticks",
        "the bead flashed once near the plate",
        "it flashed again beside the path",
        "between two flat stones",
        "the younger child",
        "The bead had fallen while the younger child reached for a kabob and bounced along the path.",
        "The golden bead sat safely in a shared palm.",
    ),
    MysteryCase(
        "blue_ribbon",
        "a blue ribbon tied to the picnic basket",
        "a blue gleam in the grass",
        "a blue thread shimmered beside the blanket",
        "the same shimmer appeared near the tree",
        "caught on a low branch",
        "the breeze",
        "The breeze had lifted the ribbon from the basket and carried it to the branch.",
        "The blue ribbon fluttered above the picnic, no longer mysterious.",
    ),
]

OPENINGS = [
    "At noon, Luna and her friend spread lunch beneath the trees.",
    "On a bright picnic day, Luna and her friend unpacked their food.",
    "Near the quiet meadow, Luna and her friend shared a warm lunch.",
    "When the afternoon shadows reached the blanket, Luna and her friend opened the basket.",
]

PAUSES = [
    "The children stopped eating and listened.",
    "They held their breath beside the quiet table.",
    "For a moment, even the leaves seemed to wait.",
    "The picnic grew still as they watched the grass.",
]

ASP_RULES = r"""
present(kabob).
present(gleam).
clue(first).
clue(second).
repeated_clue :- clue(first), clue(second).
shared_information :- repeated_clue.
solved_mystery :- shared_information.
#show repeated_clue/0.
#show shared_information/0.
#show solved_mystery/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("present", "kabob"),
        asp.fact("present", "gleam"),
        asp.fact("clue", "first"),
        asp.fact("clue", "second"),
    ])


def asp_program(show: str = "#show solved_mystery/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {symbol.name for symbol in model}
    expected = {"repeated_clue", "shared_information", "solved_mystery"}
    if expected <= names:
        print("OK: ASP mystery twin agrees that repeated shared clues solve the case.")
        return 0
    print("MISMATCH: ASP mystery twin did not derive the expected solution.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a small mystery about a kabob and a gleam."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice([x for x in FRIENDS if x != name])
    place = args.place or rng.choice(list(PLACES))
    return StoryParams(name=name, friend=friend, place=place)


def tell(params: StoryParams) -> World:
    seed = params.seed if params.seed is not None else sum(
        ord(char) for char in f"{params.name}|{params.friend}|{params.place}"
    )
    cursor = seed
    case = CASES[cursor % len(CASES)]
    cursor //= len(CASES)
    opening = OPENINGS[cursor % len(OPENINGS)]
    cursor //= len(OPENINGS)
    pause = PAUSES[cursor % len(PAUSES)]

    world = World(place=PLACES[params.place])
    luna = world.add(Entity("hero", "child", params.name, memes={"curiosity": 1}))
    friend = world.add(Entity("friend", "child", params.friend, memes={"helpfulness": 1}))
    kabob = world.add(Entity("kabob", "food", "kabob"))
    gleam = world.add(Entity("gleam", "clue", case.gleam))
    world.add(Entity("basket", "container", "picnic basket"))
    world.facts.update(
        hero=luna,
        friend=friend,
        kabob=kabob,
        gleam=gleam,
        case=case,
        opening=opening,
        pause=pause,
        repeated=0,
        shared=False,
        solved=False,
    )

    world.say(f"{opening} The kabob smelled of peppers and warm bread.")
    world.say(
        f"Then {params.name} noticed {case.first_clue}. "
        f"It was a tiny {case.gleam} that vanished when {params.name} blinked."
    )

    world.para()
    world.say(f"{pause} \"Did you see that?\" asked {params.name}.")
    world.say(
        f"\"I saw a {case.object_name} missing from our things,\" said {params.friend}. "
        f"\"Tell me exactly where the gleam was.\""
    )
    world.say(
        f"{params.name} pointed beside the plate, and the two children shared the clue instead of keeping it secret."
    )
    world.facts["shared"] = True
    friend.memes["trust"] = 1

    world.para()
    world.say(
        f"They followed the mystery slowly. Then {case.second_clue}. "
        f"The gleam had repeated itself."
    )
    world.facts["repeated"] = 2
    world.say(
        f"\"The shine moved from the plate toward the basket,\" said {params.friend}. "
        f"\"Let's search the places that connect those two spots.\""
    )
    world.say(
        f"Together they checked the basket, the blanket, and the ground beneath the kabob."
    )
    world.say(f"At last, they found {case.object_name} {case.hiding_place}.")
    world.facts["solved"] = True
    luna.meters["mystery_solved"] = 1
    friend.meters["mystery_solved"] = 1

    world.para()
    world.say(case.explanation)
    world.say(
        f"{params.name} smiled. \"The first gleam was easy to miss, but the second one helped us understand it.\""
    )
    world.say(
        f"{params.friend} nodded. \"Sharing a clue makes a small mystery less scary.\""
    )
    world.say(case.ending_image)
    return world


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    hero = world.facts["hero"]
    return [
        f"Write a child-facing mystery about {hero.label}, a kabob, and {case.gleam}.",
        f"Show suspense growing when {case.first_clue}, then use repetition and sharing to solve the mystery.",
        f"End with the missing object found {case.hiding_place}, and explain why the gleam appeared twice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: MysteryCase = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    return [
        QAItem(
            "Who noticed the first gleam?",
            f"{hero.label} noticed the first gleam while the children were sharing a kabob picnic.",
        ),
        QAItem(
            "What made the mystery suspenseful?",
            f"The suspense grew because {case.first_clue}, and then the same gleam appeared again near the basket.",
        ),
        QAItem(
            f"How did {hero.label} and {friend.label} solve the mystery?",
            f"They shared what each of them had seen, followed the repeated gleam, and searched the connected places until they found {case.object_name} {case.hiding_place}.",
        ),
        QAItem(
            "What did the children learn?",
            "They learned that sharing clues and noticing repeated details can make a mystery easier to solve.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a kabob?",
            "A kabob is food, such as vegetables or meat, arranged on a skewer for cooking or serving.",
        ),
        QAItem(
            "What is a gleam?",
            "A gleam is a small, bright flash of reflected light.",
        ),
        QAItem(
            "Why can repetition help solve a mystery?",
            "When a clue appears more than once, it may show a pattern or point toward the same important place.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} label={entity.label!r} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(
        f"place={world.place!r} repeated_clues={world.facts['repeated']} "
        f"shared={world.facts['shared']} solved={world.facts['solved']}"
    )
    return "\n".join(lines)


CURATED = [
    StoryParams("Luna", "Milo", "pine picnic", 101),
    StoryParams("Mara", "Nell", "old orchard", 202),
    StoryParams("Niko", "Bea", "river meadow", 303),
]


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

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        shown = [str(symbol) for symbol in model]
        print("ASP model:", ", ".join(shown) if shown else "(empty)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.n < 1:
        raise StoryError("-n must be at least 1")

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1
            if index > max(100, args.n * 100):
                raise StoryError("Could not produce enough distinct mystery variants.")

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
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
