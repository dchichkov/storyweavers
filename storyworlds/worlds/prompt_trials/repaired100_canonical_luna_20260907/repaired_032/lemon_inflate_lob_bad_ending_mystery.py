#!/usr/bin/env python3
"""
A small mystery storyworld about Luna, a lemon, an inflatable raft, and a
careful lob that prevents a bad ending.
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
    owner: Optional[str] = None


@dataclass
class Place:
    id: str
    label: str
    affordances: set[str]


@dataclass
class Clue:
    id: str
    text: str
    points_to: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "canal_bank": Place("canal_bank", "the canal bank", {"inflate", "lob", "search"}),
    "moonlit_park": Place("moonlit_park", "the moonlit park", {"inflate", "lob", "search"}),
    "old_boat_house": Place("old_boat_house", "the old boat house", {"inflate", "lob", "search"}),
}

MYSTERIES = {
    "vanished_bell": {
        "title": "the vanished silver bell",
        "object": "silver bell",
        "clue": Clue("yellow_mark", "a yellow smear on the dock rail", "lemon"),
        "problem": "The silver bell had vanished from the little rescue boat.",
        "answer": "A lemon peel trail showed that a hungry squirrel had dragged the bell toward the reeds.",
        "ending": "The bell rang again from the raft, warning everyone away from the sinking mud.",
    },
    "hidden_key": {
        "title": "the hidden brass key",
        "object": "brass key",
        "clue": Clue("round_dent", "a round dent beside the water", "lemon"),
        "problem": "The brass key to the boat house had disappeared before sunset.",
        "answer": "A lemon-shaped dent revealed that the key had been tucked beneath a loose float.",
        "ending": "The key opened the boat house before the rising water reached its floor.",
    },
    "missing_map": {
        "title": "the missing blue map",
        "object": "blue map",
        "clue": Clue("wet_corner", "a wet corner smelling faintly of lemon", "lemon"),
        "problem": "The blue map was missing, and without it nobody knew the safe route home.",
        "answer": "The lemon scent led Luna to a crate where the map had slipped behind a coil of rope.",
        "ending": "The map guided the raft through the reeds and away from the dark whirlpool.",
    },
}

NAMES = ["Luna", "Mara", "Niko", "Tess", "Owen", "Pia"]
HELPERS = ["Mara", "Niko", "Tess", "Owen", "Pia"]

ASP_RULES = r"""
place(P) :- place_name(P).
mystery(M) :- mystery_name(M).
valid_story(P, M) :- place(P), mystery(M), affords(P, inflate), affords(P, lob),
                      mystery_has_clue(M, lemon).
#show valid_story/2.
"""


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.clues: list[Clue] = []
        self.facts: dict[str, object] = {}
        self.events: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mystery storyworld about Luna, a lemon, and an inflatable raft."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--mystery", choices=sorted(MYSTERIES))
    parser.add_argument("--hero")
    parser.add_argument("--helper")
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mystery) for place in PLACES for mystery in MYSTERIES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        pair for pair in valid_combos()
        if (args.place is None or pair[0] == args.place)
        and (args.mystery is None or pair[1] == args.mystery)
    ]
    if not choices:
        raise StoryError("No valid place and mystery combination matches the request.")
    place, mystery = rng.choice(choices)
    hero = args.hero or rng.choice(NAMES)
    helpers = [name for name in HELPERS if name != hero]
    helper = args.helper or rng.choice(helpers)
    if helper == hero:
        raise StoryError("The helper must be a different character from the hero.")
    return StoryParams(place=place, mystery=mystery, hero=hero, helper=helper)


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(place)

    hero = world.add(Entity("hero", "character", params.hero, memes={"curiosity": 1.0}))
    helper = world.add(Entity("helper", "character", params.helper, memes={"caution": 1.0}))
    lemon = world.add(
        Entity("lemon", "fruit", "lemon", memes={"clue_value": 1.0}, owner=hero.id)
    )
    raft = world.add(
        Entity(
            "raft",
            "raft",
            "inflatable raft",
            meters={"air": 0.0, "safe": 0.0},
            memes={"trust": 0.0},
        )
    )
    missing = world.add(
        Entity(
            "missing",
            "mystery_object",
            mystery["object"],
            meters={"found": 0.0},
        )
    )
    clue = mystery["clue"]
    world.clues.append(clue)
    world.facts.update(
        hero=hero,
        helper=helper,
        lemon=lemon,
        raft=raft,
        missing=missing,
        clue=clue,
        mystery=mystery,
        resolved=False,
        bad_ending_avoided=False,
    )

    world.say(
        f"At {place.label}, {params.hero} noticed that the {mystery['object']} was missing."
    )
    world.say(
        f"The only clue was {clue.text}, and a bright lemon lay beside the footprints."
    )
    world.say(
        f'"Do not guess yet," said {params.helper}. "{clue.text.capitalize()} may tell us where to look."'
    )
    world.say(
        f'"Then we should cross carefully," said {params.hero}. "I will inflate the raft, and you watch the current."'
    )

    raft.meters["air"] = 1.0
    world.say(
        f"{params.hero} began to inflate the inflatable raft while {params.helper} studied the water."
    )
    world.say(
        f"The lemon rolled toward a reed bed, so {params.hero} followed its path instead of rushing ahead."
    )

    raft.memes["trust"] = 1.0
    world.say(
        f"Near the reeds, {params.helper} pointed to a dark shape. "
        f'"Lob the lemon past it," {params.helper} whispered. "If something is hiding there, it may move."'
    )
    world.say(
        f"{params.hero} gave the lemon a gentle lob across the mud, not a hard throw."
    )
    world.say(
        f"The lemon bumped a loose float, and the {mystery['object']} slid into view."
    )

    missing.meters["found"] = 1.0
    raft.meters["safe"] = 1.0
    world.facts["resolved"] = True
    world.facts["bad_ending_avoided"] = True
    world.say(mystery["answer"])
    world.say(
        f"Together they pulled the {mystery['object']} onto the inflated raft. "
        f"{mystery['ending']}"
    )
    world.say(
        "The bad ending they feared never happened: nobody stepped into the deep mud, "
        "and the small clue had led them safely home."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    mystery = world.facts["mystery"]
    clue = world.facts["clue"]
    return [
        "Write a child-facing mystery about a lemon, an inflatable raft, and a careful lob.",
        f"Make the clue matter later: {clue.text}. Solve this mystery: {mystery['problem']}",
        "Include brief back-and-forth dialogue and avoid the bad ending by showing a safe choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero: Entity = facts["hero"]
    helper: Entity = facts["helper"]
    mystery = facts["mystery"]
    clue: Clue = facts["clue"]
    return [
        QAItem(
            f"What problem did {hero.label} discover?",
            f"{hero.label} discovered that the {mystery['object']} was missing at {world.place.label}.",
        ),
        QAItem(
            "What clue helped solve the mystery?",
            f"The clue was {clue.text}, and it pointed the children toward the lemon's path near the reeds.",
        ),
        QAItem(
            f"How did {hero.label} and {helper.label} use the raft?",
            f"{hero.label} inflated the raft while {helper.label} watched the current, so they could search without stepping into unsafe mud.",
        ),
        QAItem(
            "Why did Luna lob the lemon?",
            f"Luna lobbed the lemon gently to bump the loose float and reveal what was hidden without rushing into the mud.",
        ),
        QAItem(
            "How was the bad ending avoided?",
            "The children listened to the clue, inflated the raft, and used a gentle lob instead of entering the deep mud.",
        ),
        QAItem(
            "What changed at the end?",
            f"They found the {mystery['object']} and brought it home safely on the raft.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a lemon?",
            "A lemon is a yellow citrus fruit with a fresh, sour taste.",
        ),
        QAItem(
            "What does inflate mean?",
            "To inflate something means to fill it with air so it becomes larger or firm.",
        ),
        QAItem(
            "What does lob mean?",
            "To lob something means to throw it gently in a high, easy arc.",
        ),
        QAItem(
            "What is a mystery?",
            "A mystery is a question or problem solved by noticing clues and reasoning about them.",
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
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.label}; meters={entity.meters}; memes={entity.memes}"
        )
    lines.append(f"  clue: {world.facts['clue'].text}")
    lines.append(f"  resolved: {world.facts['resolved']}")
    lines.append(f"  bad_ending_avoided: {world.facts['bad_ending_avoided']}")
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


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place_name", place_id))
        for affordance in sorted(place.affordances):
            lines.append(asp.fact("affords", place_id, affordance))
    for mystery_id, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery_name", mystery_id))
        lines.append(asp.fact("mystery_has_clue", mystery_id, "lemon"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    try:
        clingo_pairs = set(asp_valid_stories())
    except ImportError:
        print("ASP verification unavailable: clingo is not installed.")
        return 1
    if py == clingo_pairs:
        print(f"OK: ASP and Python agree on {len(py)} valid story combinations.")
        for params in CURATED:
            sample = generate(params)
            if "lemon" not in sample.story or "inflate" not in sample.story or "lob" not in sample.story:
                print("Generated story exercise failed.")
                return 1
            if not sample.world.facts["bad_ending_avoided"]:
                print("Generated story did not avoid its bad ending.")
                return 1
        print("OK: generated stories exercise the resolved path.")
        return 0
    print("Mismatch between ASP and Python:")
    print("  only in ASP:", sorted(clingo_pairs - py))
    print("  only in Python:", sorted(py - clingo_pairs))
    return 1


CURATED = [
    StoryParams(
        place="canal_bank",
        mystery="vanished_bell",
        hero="Luna",
        helper="Mara",
    ),
    StoryParams(
        place="moonlit_park",
        mystery="hidden_key",
        hero="Luna",
        helper="Niko",
    ),
    StoryParams(
        place="old_boat_house",
        mystery="missing_map",
        hero="Luna",
        helper="Tess",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        try:
            stories = asp_valid_stories()
        except ImportError as exc:
            raise SystemExit(f"ASP mode unavailable: {exc}")
        print(f"{len(stories)} valid story combinations:")
        for story in stories:
            print(" ", story)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            try:
                params = resolve_params(args, rng)
            except StoryError as exc:
                print(exc)
                return
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
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
