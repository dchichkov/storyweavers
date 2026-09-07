#!/usr/bin/env python3
"""Nell's dining-room quest: a heartwarming choice told with inner thoughts."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import itertools
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


QUESTS = ("lantern", "recipe")
DARLINGS = ("kitten", "grandmother")
VOICES = ("gentle", "bright")
MAX_ACTIONS = 12


@dataclass
class StoryParams:
    quest: str = "lantern"
    darling: str = "kitten"
    voice: str = "gentle"
    world_seed: int = 777
    prose_seed: int = 42


@dataclass
class Event:
    kind: str
    data: dict[str, str] = field(default_factory=dict)


@dataclass
class Entity:
    id: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity]
    history: list[Event] = field(default_factory=list)
    facts: set[str] = field(default_factory=set)
    outcome: str = ""


def validate_params(p: StoryParams) -> None:
    if p.quest not in QUESTS:
        raise StoryError(f"Unknown quest: {p.quest!r}.")
    if p.darling not in DARLINGS:
        raise StoryError(f"Unknown darling: {p.darling!r}.")
    if p.voice not in VOICES:
        raise StoryError(f"Unknown voice: {p.voice!r}.")
    if type(p.world_seed) is not int or type(p.prose_seed) is not int:
        raise StoryError("Seeds must be integers.")


def build_world(p: StoryParams) -> World:
    validate_params(p)
    entities = {
        "nell": Entity("nell", "Nell", "dining_room", memes={"care": 1.0, "worry": 0.2}),
        "table": Entity("table", "the dining table", "dining_room", meters={"steady": 1}),
        "window": Entity("window", "the dining-room window", "dining_room"),
        "door": Entity("door", "the back door", "dining_room"),
        "darling": Entity(
            "darling",
            "the kitten" if p.darling == "kitten" else "Grandmother",
            "dining_room",
            meters={"safe": 1},
            memes={"trust": 0.8},
        ),
        "lantern": Entity("lantern", "the little lantern", "sideboard", meters={"lit": 0}),
        "recipe": Entity("recipe", "Grandmother's recipe card", "sideboard"),
        "basket": Entity("basket", "the blue basket", "dining_room"),
    }
    w = World(p, entities)
    w.history.append(Event("opening", {"setting": "dining room"}))
    w.facts.add("quest_started")
    return w


def record(w: World, kind: str, **data: str) -> None:
    w.history.append(Event(kind, data))
    w.facts.add(kind)


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    darling = w.entities["darling"]

    record(w, "clue", object=p.quest)
    if p.quest == "lantern":
        record(w, "darkness")
        record(w, "search", place="sideboard")
        w.entities["lantern"].location = "table"
        record(w, "find", object="lantern")
        w.entities["lantern"].meters["lit"] = 1
        record(w, "light", object="lantern")
        if p.darling == "kitten":
            darling.location = "under_table"
            record(w, "suspense", place="under the table")
            darling.location = "table"
            record(w, "rescue", method="Nell's soft calling")
        else:
            darling.location = "hall"
            record(w, "suspense", place="the dark hall")
            darling.location = "dining_room"
            record(w, "rescue", method="the warm lantern")
        w.outcome = "the dining room became warm and safe"
    else:
        record(w, "hunger")
        record(w, "search", place="sideboard")
        w.entities["recipe"].location = "table"
        record(w, "find", object="recipe")
        record(w, "cook", object="supper")
        if p.darling == "kitten":
            darling.location = "chair"
            record(w, "suspense", place="the empty chair")
            darling.location = "dining_room"
            record(w, "rescue", method="a familiar purr")
        else:
            darling.location = "dining_room"
            record(w, "suspense", place="the quiet doorway")
            record(w, "rescue", method="Nell's patient welcome")
        w.outcome = "everyone found a place at the table"

    record(w, "decision", choice="kindness before hurry")
    record(w, "ending")
    validate_world(w)
    return w


def validate_world(w: World) -> None:
    if not w.outcome or "ending" not in w.facts:
        raise StoryError("The quest needs a warm resolution.")
    if "suspense" not in w.facts or "decision" not in w.facts:
        raise StoryError("The story needs suspense and a meaningful decision.")
    if w.entities["darling"].location not in {"dining_room", "table", "chair"}:
        raise StoryError("The darling must reach a safe place.")


def render(w: World) -> tuple[str, list[QAItem]]:
    p = w.params
    suspense_place = next(event.data["place"] for event in w.history if event.kind == "suspense")
    rng = random.Random(p.prose_seed)
    darling = "the kitten" if p.darling == "kitten" else "Grandmother"
    story: list[str] = []
    qa: list[QAItem] = []

    story.append(
        rng.choice(
            [
                "In the dining room, Nell found a small problem waiting beside the supper plates.",
                "The dining room was quiet, but Nell could feel a quest beginning beneath the quiet.",
            ]
        )
    )

    if p.quest == "lantern":
        story.append(
            "The evening light had slipped away, and the little lantern sat unlit on the sideboard. "
            f"Then {darling} was nowhere to be seen."
        )
        qa.append(
            QAItem(
                "What quest did Nell begin?",
                "Nell began a quest to find the little lantern and bring warmth back to the dining room.",
            )
        )
    else:
        story.append(
            "Supper was nearly ready, but Grandmother's recipe card had vanished from the sideboard. "
            f"Then {darling} was nowhere to be seen."
        )
        qa.append(
            QAItem(
                "What quest did Nell begin?",
                "Nell began a quest to find the recipe card so she could finish supper.",
            )
        )

    story.append(
        "Nell's first thought was to hurry. Her second thought was gentler: "
        "\"I must decide carefully, darling. Finding you matters more than being fast.\""
    )

    if p.quest == "lantern":
        story.append(
            f"She searched the sideboard and found the lantern, but a soft sound came from {suspense_place}. "
            "The room seemed to hold its breath."
        )
        qa.append(
            QAItem(
                "What made the middle of the story suspenseful?",
                "Nell heard a soft sound from a shadowy place while the dining room was still dim.",
            )
        )
        if p.darling == "kitten":
            story.append(
                "Nell knelt and called instead of reaching blindly. Two bright eyes blinked under the table. "
                "The kitten crept out when Nell held the lantern low and warm."
            )
        else:
            story.append(
                "Nell carried the lantern toward the hall and called softly. Grandmother answered from the dark, "
                "and Nell guided her home by the golden light."
            )
    else:
        story.append(
            f"She searched the sideboard and found the recipe card, but the chair near {suspense_place} "
            "was empty. The dining room seemed to hold its breath."
        )
        qa.append(
            QAItem(
                "What made the middle of the story suspenseful?",
                "Nell found the recipe card but still could not see her darling in the quiet dining room.",
            )
        )
        if p.darling == "kitten":
            story.append(
                "Nell paused before calling again. A tiny purr answered from the chair. "
                "The kitten climbed into her lap, and Nell smiled before returning to supper."
            )
        else:
            story.append(
                "Nell waited at the doorway instead of calling sharply. Grandmother appeared with a smile, "
                "and Nell drew out a chair beside her."
            )

    story.append(
        "Nell had chosen patience over panic. Soon the table held its meal, its smiles, and one safe darling. "
        "The dining room felt brighter because someone had listened."
    )
    qa.append(
        QAItem(
            "What did Nell decide to do?",
            "Nell decided to move patiently and kindly instead of rushing, because her darling's safety mattered most.",
        )
    )
    qa.append(
        QAItem(
            "How did the story end?",
            "The darling was safe beside Nell, and the dining room became a warm place for everyone to gather.",
        )
    )
    return "\n\n".join(story), qa


ASP_RULES = """
quest(lantern).
quest(recipe).
darling(kitten).
darling(grandmother).
safe_choice(kindness) :- quest(_), darling(_).
#show safe_choice/1.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        [fact("quest", value) for value in QUESTS]
        + [fact("darling", value) for value in DARLINGS]
    )


def asp_combos() -> set[tuple[str]]:
    from asp import atoms, one_model
    model = one_model(asp_facts() + "\n" + ASP_RULES)
    return set(atoms(model, "safe_choice"))


def generate(p: StoryParams) -> StorySample:
    world = simulate(p)
    story, qa = render(world)
    return StorySample(
        params=p,
        story=story,
        prompts=[
            f"Write a heartwarming dining-room quest in which Nell must decide carefully for {p.darling}."
        ],
        story_qa=qa,
        world_qa=[
            QAItem(
                "Why can patience help during a difficult quest?",
                "Patience gives a person time to notice clues and choose a safe, caring action.",
            )
        ],
        world=world,
    )


def verify() -> None:
    from asp import atoms, one_model
    model = one_model(asp_facts() + "\n" + ASP_RULES)
    if set(atoms(model, "safe_choice")) != {("kindness",)}:
        raise StoryError("Python and ASP disagree about the kind choice.")
    count = 0
    for quest, darling in itertools.product(QUESTS, DARLINGS):
        for voice in VOICES:
            p = StoryParams(quest=quest, darling=darling, voice=voice)
            sample = generate(p)
            if "dining room" not in sample.story:
                raise StoryError("The setting disappeared from the story.")
            count += 1
    print(f"OK: {count} configurations; suspense, decision, and ASP parity verified.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", dest="world_seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--quest", choices=QUESTS)
    parser.add_argument("--darling", choices=DARLINGS)
    parser.add_argument("--voice", choices=VOICES, default="gentle")
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    p = StoryParams(
        quest=args.quest or rng.choice(QUESTS),
        darling=args.darling or rng.choice(DARLINGS),
        voice=args.voice,
        world_seed=args.world_seed + index,
        prose_seed=args.prose_seed + index,
    )
    validate_params(p)
    return p


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(
            json.dumps(
                {
                    "world": {
                        "outcome": sample.world.outcome,
                        "entities": {
                            key: asdict(value) for key, value in sample.world.entities.items()
                        },
                    },
                    "history": [asdict(event) for event in sample.world.history],
                },
                indent=2,
            )
        )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            print(json.dumps(sorted(asp_combos())))
            return 0

        rng = random.Random(args.world_seed)
        if args.all:
            params = [
                StoryParams(
                    quest=quest,
                    darling=darling,
                    voice=args.voice,
                    world_seed=args.world_seed + i,
                    prose_seed=args.prose_seed + i,
                )
                for i, (quest, darling) in enumerate(itertools.product(QUESTS, DARLINGS))
            ]
        else:
            params = [resolve_params(args, rng, i) for i in range(args.n)]

        samples = [generate(p) for p in params]
        if args.json:
            rows = [sample.to_dict() for sample in samples]
            print(json.dumps(rows[0] if len(rows) == 1 else rows, ensure_ascii=False, indent=2))
        else:
            for i, sample in enumerate(samples):
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {i + 1}\n" if len(samples) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
