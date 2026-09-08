#!/usr/bin/env python3
"""
A child-facing detective storyworld about Luna, a puzzling amenity, and a
quest that begins with a misunderstanding. A funny clue helps the detective
discover what the mysterious first note really means.
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

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str
    amenity: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    object_label: str
    first_clue: str
    misunderstanding: str
    true_meaning: str
    quest: str
    funny_clue: str
    ending_image: str


@dataclass
class StoryParams:
    place: str
    case: str
    name: str
    helper: str
    seed: Optional[int] = None
    telling: str = "rainy"


@dataclass
class World:
    place: Place
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


PLACES = {
    "library": Place(
        "library",
        "the little library",
        "a reading nook",
        {"quiet", "books", "clues"},
    ),
    "train_station": Place(
        "train_station",
        "the old train station",
        "a waiting bench",
        {"tickets", "luggage", "clues"},
    ),
    "museum": Place(
        "museum",
        "the town museum",
        "a magnifying-glass desk",
        {"artifacts", "labels", "clues"},
    ),
}

CASES = {
    "blue_badge": Case(
        "blue_badge",
        "a blue detective badge",
        "The first note said, “Find the missing amenity.”",
        "Luna thought amenity meant a fancy object, so she searched for a missing golden spoon.",
        "Amenity meant a helpful feature of the place: the library's reading nook.",
        "follow three chalk arrows, question the sleepy custodian, and inspect the reading nook",
        "a pigeon wore a paper mustache and strutted past the clue like a very serious inspector",
        "the blue badge shone beside the cozy nook while the pigeon bowed to its own reflection",
    ),
    "red_key": Case(
        "red_key",
        "a tiny red key",
        "The first note said, “The amenity has a secret.”",
        "Luna thought the amenity was a hidden treasure and hunted under every rug.",
        "The amenity was the station's waiting bench, a useful comfort rather than a treasure.",
        "follow ticket-shaped footprints, question the porter, and examine the bench slats",
        "a ticket stuck to Luna's nose, so the porter tried to stamp her face",
        "the red key rested on the bench as trains hummed like sleepy dragons",
    ),
    "green_lens": Case(
        "green_lens",
        "a green magnifying lens",
        "The first note said, “Look where the amenity watches.”",
        "Luna thought the museum's statue had become a watchful guard.",
        "The amenity was the magnifying-glass desk, which helped visitors see tiny details.",
        "follow dusty footprints, question the guide, and inspect the desk drawer",
        "a stuffed owl wore spectacles upside down and looked proud of being unhelpful",
        "the green lens made a tiny painted moon sparkle on the museum desk",
    ),
}

NAMES = ["Luna", "Mira", "Tess", "Pip", "Nico", "Zara"]
HELPERS = ["Theo", "Milo", "June", "Bram", "Ivy", "Ollie"]

TELLINGS = {
    "rainy": (
        "Rain tapped the windows when {hero} discovered {object_label} tucked beneath a damp newspaper.",
        "The first clue made {hero}'s curiosity prick up like a detective's umbrella.",
    ),
    "sunny": (
        "Sunlight flashed across the floor when {hero} found {object_label} beside a dusty footprint.",
        "The first clue gave {hero} a pique of curiosity that was brighter than the window.",
    ),
    "whispered": (
        "The town was whispering when {hero} discovered {object_label} inside an empty flowerpot.",
        "The first clue was small, but it tugged at {hero}'s curiosity.",
    ),
}


def valid_combos() -> list[tuple[str, str]]:
    return [
        (place_id, case_id)
        for place_id, place in PLACES.items()
        for case_id in CASES
        if "clues" in place.affordances
    ]


ASP_RULES = r"""
place(P) :- place_name(P).
case(C) :- case_name(C).
compatible(P, C) :- place(P), case(C), affords(P, clues).
valid_story(P, C) :- compatible(P, C).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place_name", place_id))
        for affordance in sorted(place.affordances):
            lines.append(asp.fact("affords", place_id, affordance))
    for case_id in CASES:
        lines.append(asp.fact("case_name", case_id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_pairs = set(valid_combos())
    asp_pairs = set(asp_valid_stories())
    if python_pairs == asp_pairs:
        print(f"OK: clingo gate matches valid_combos() ({len(python_pairs)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  only in clingo:", sorted(asp_pairs - python_pairs))
    print("  only in Python:", sorted(python_pairs - asp_pairs))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detective storyworld about Luna, an amenity, and a funny misunderstanding."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--case", choices=sorted(CASES))
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--telling", choices=sorted(TELLINGS))
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
    choices = [
        pair
        for pair in valid_combos()
        if (args.place is None or pair[0] == args.place)
        and (args.case is None or pair[1] == args.case)
    ]
    if not choices:
        raise StoryError("No valid place and case combination matches the requested options.")
    place, case = rng.choice(sorted(choices))
    name = args.name or rng.choice(NAMES)
    helper_choices = [candidate for candidate in HELPERS if candidate != name]
    helper = args.helper or rng.choice(helper_choices)
    if helper == name:
        raise StoryError("The detective and helper must have different names.")
    return StoryParams(
        place=place,
        case=case,
        name=name,
        helper=helper,
        telling=args.telling or rng.choice(sorted(TELLINGS)),
    )


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    case = CASES[params.case]
    world = World(place)

    hero = world.add(
        Entity(
            id="hero",
            kind="detective",
            label=params.name,
            memes={"curiosity": 1.0, "carefulness": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="helper",
            label=params.helper,
            memes={"questioning": 1.0, "humor": 1.0},
        )
    )
    mystery = world.add(
        Entity(
            id="mystery",
            kind="object",
            label=case.object_label,
            meters={"found": 0.0},
        )
    )
    amenity = world.add(
        Entity(
            id="amenity",
            kind="place_feature",
            label=place.amenity,
            meters={"useful": 1.0},
        )
    )

    opening, curiosity_line = TELLINGS[params.telling]
    opening = opening.format(hero=hero.label, object_label=case.object_label)
    curiosity_line = curiosity_line.format(hero=hero.label)

    world.facts.update(
        hero=hero,
        helper=helper,
        mystery=mystery,
        amenity=amenity,
        case=case,
        opening=opening,
        curiosity_line=curiosity_line,
        misunderstanding_solved=False,
        quest_complete=False,
    )

    world.say(opening)
    world.say(
        f"{hero.label} was acting as a detective, and {helper.label} was the friend who never "
        f"let a serious clue escape without a silly question."
    )
    world.say(case.first_clue)
    world.say(curiosity_line)

    world.para()
    world.say(
        f"Unfortunately, {hero.label} misunderstood the word amenity. "
        f"{hero.label} thought it meant a fancy object, so the first search chased {case.misunderstanding.lower()}."
    )
    world.say(
        f'"An amenity is something helpful in a place," said {helper.label}. '
        f'"Could it be the place feature that makes visitors comfortable?"'
    )
    world.say(
        f'"Then the mystery is not a golden treasure at all," said {hero.label}. '
        f'"It is {place.amenity}!"'
    )
    world.facts["misunderstanding_solved"] = True
    helper.memes["questioning"] = 2.0
    hero.memes["curiosity"] = 2.0

    world.para()
    world.say(
        f"Their quest began: they decided to {case.quest}. "
        f"They followed the clues slowly, because a good detective checks what a hurried detective misses."
    )
    world.say(f"Along the way, {case.funny_clue}.")
    world.say(
        f'"That is the funniest suspect I have ever seen," said {helper.label}. '
        f'"It has a very suspicious face."'
    )
    world.say(
        f'"The clue is pointing to the {amenity.label}," said {hero.label}. '
        f'"Let us inspect it instead of accusing the pigeon, ticket, or owl."'
    )
    hero.meters["evidence"] = 1.0
    world.fired.add("question_changed_the_plan")

    world.para()
    world.say(
        f"At last, the pair found the answer: {case.true_meaning}. "
        f"The helpful feature had hidden the next clue in plain sight."
    )
    mystery.meters["found"] = 1.0
    world.facts["misunderstanding_solved"] = True
    world.facts["quest_complete"] = True
    world.say(
        f"The amenity led them to {case.object_label}, and {hero.label} carefully lifted it without "
        f"bending the final clue."
    )
    world.say(
        f"The town thanked the two detectives. {case.ending_image.capitalize()}."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    case: Case = world.facts["case"]
    return [
        "Write a short child-friendly detective story about an amenity, a first clue, and a pique of curiosity.",
        f"Show how {hero.label} and {helper.label} solve a misunderstanding during a quest.",
        f"Use this funny detective clue: {case.funny_clue}",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    amenity: Entity = world.facts["amenity"]
    mystery: Entity = world.facts["mystery"]
    case: Case = world.facts["case"]
    return [
        QAItem(
            question=f"What did {hero.label} find at the beginning?",
            answer=f"{hero.label} found {mystery.label}, along with a first clue about a missing amenity.",
        ),
        QAItem(
            question="What misunderstanding did the detective make?",
            answer=f"The detective misunderstood amenity as a fancy object and searched in the wrong way.",
        ),
        QAItem(
            question=f"How did {helper.label} help?",
            answer=f"{helper.label} explained that an amenity is a helpful feature of a place and asked a question that changed the detective's plan.",
        ),
        QAItem(
            question="What was the real amenity?",
            answer=f"The real amenity was {amenity.label}, a useful feature of {world.place.label}.",
        ),
        QAItem(
            question="What made the detective story humorous?",
            answer=f"It was humorous because {case.funny_clue}, so the detectives nearly treated a silly sight like a serious suspect.",
        ),
        QAItem(
            question="How did the quest end?",
            answer=f"The quest ended when the detectives followed the amenity's clue and found {mystery.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an amenity?",
            answer="An amenity is a useful or pleasant feature that helps people in a place.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone understands a word, message, or event incorrectly.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for evidence, asks questions, and connects clues to solve a mystery.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a purposeful journey to find something, solve something, or complete a task.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  place: {world.place.label}")
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  misunderstanding_solved: {world.facts['misunderstanding_solved']}")
    lines.append(f"  quest_complete: {world.facts['quest_complete']}")
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(
        place="library",
        case="blue_badge",
        name="Luna",
        helper="Theo",
        telling="rainy",
    ),
    StoryParams(
        place="train_station",
        case="red_key",
        name="Mira",
        helper="June",
        telling="sunny",
    ),
    StoryParams(
        place="museum",
        case="green_lens",
        name="Tess",
        helper="Ollie",
        telling="whispered",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        try:
            result = asp_verify()
        except ImportError:
            print("ASP verification requires clingo.")
            result = 1
        if result == 0:
            rng = random.Random(417)
            for _ in range(3):
                params = resolve_params(args, rng)
                sample = generate(params)
                if not sample.story or len(sample.story_qa) < 3:
                    print("Generated-story verification failed.")
                    sys.exit(1)
            print("OK: generated stories exercised.")
        sys.exit(result)

    if args.asp:
        try:
            stories = asp_valid_stories()
        except ImportError:
            print("ASP mode requires clingo.")
            sys.exit(1)
        print(f"{len(stories)} valid stories:")
        for story in stories:
            print(" ", story)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            attempts += 1
            try:
                params = resolve_params(args, random.Random(base_seed + attempts))
            except StoryError as error:
                print(error)
                return
            params.seed = base_seed + attempts
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No stories could be generated.")

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
