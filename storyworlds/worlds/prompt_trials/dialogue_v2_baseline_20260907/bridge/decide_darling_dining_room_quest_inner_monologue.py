#!/usr/bin/env python3
"""A heartwarming dining-room quest about deciding what to share."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Mia"
    darling: str = "Grandma"
    guest: str = "Ben"
    treat: str = "berry tart"
    clue: str = "silver spoon"
    choice: str = "share"
    seed: int = 777


NAMES = ("Mia", "Noor", "Lily", "Theo", "Sam", "Ava")
DARLINGS = ("Grandma", "Aunt Rosa", "Papa")
GUESTS = ("Ben", "Lena", "Omar", "Nia")
TREATS = {
    "berry": "berry tart",
    "apple": "apple pie",
    "lemon": "lemon cake",
}
CLUES = {
    "silver": "silver spoon",
    "blue": "blue napkin",
    "wooden": "wooden button",
}
CHOICES = ("share", "save")

PROMPT = (
    "Write a heartwarming children's story set in a dining room, where a child "
    "must decide during a suspenseful quest whether to share a special treat "
    "with a darling family member and a waiting friend."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity(
                "hero", params.hero, "character", "dining_room",
                memes={"bravery": 0.4, "kindness": 0.6, "worry": 0.7},
            ),
            "darling": Entity(
                "darling", params.darling, "character", "kitchen",
                memes={"warmth": 0.8, "hope": 0.5},
            ),
            "guest": Entity(
                "guest", params.guest, "character", "hallway",
                memes={"hope": 0.7, "patience": 0.8},
            ),
            "table": Entity(
                "table", "the dining table", "furniture", "dining_room",
                meters={"seats": 4, "place_settings": 2},
            ),
            "treat": Entity(
                "treat", f"the {params.treat}", "food", "sideboard",
                meters={"pieces": 1, "shared": 0, "saved": 0},
            ),
            "clue": Entity(
                "clue", f"the {params.clue}", "object", "under_table",
                meters={"found": 0},
            ),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(entity) for key, entity in self.entities.items()}

    def narrate(
        self,
        kind: str,
        text: str,
        *,
        question: str = "",
        cause: str = "",
        result: str = "",
    ) -> None:
        self.history.append(
            Event(
                kind=kind,
                text=text,
                question=question,
                cause=cause,
                result=result,
                state=self.snapshot(),
            )
        )


def validate_params(params: StoryParams) -> None:
    if params.choice not in CHOICES:
        raise StoryError("The choice must be share or save.")
    if params.treat not in TREATS.values():
        raise StoryError("Choose a recognized dining-room treat.")
    if params.clue not in CLUES.values():
        raise StoryError("Choose a recognized quest clue.")
    if len({params.hero, params.darling, params.guest}) != 3:
        raise StoryError("The child, darling, and guest need different names.")
    if any(
        not re.fullmatch(r"[A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+)*", name)
        for name in (params.hero, params.darling, params.guest)
    ):
        raise StoryError("Names must begin with a capital letter.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.entities["hero"].label
    darling = world.entities["darling"].label
    guest = world.entities["guest"].label
    treat = world.entities["treat"].label
    clue = world.entities["clue"].label

    world.narrate(
        "beginning",
        f"Rain tapped the dining-room windows while {hero} set two cups beside "
        f"the plates. On the sideboard waited {treat}, small and golden beneath "
        "a glass cover.",
    )
    world.narrate(
        "quest",
        f"{darling} had gone to find the family recipe book, but a note beside "
        f"the {treat} said, “Follow the little clue before supper.”",
        question="What quest began in the dining room?",
        cause=f"{darling} left a note asking {hero} to follow a hidden clue.",
        result=f"{hero} began searching for the recipe book before supper.",
    )
    world.narrate(
        "search",
        f"{hero} looked beneath the chairs, behind the curtain, and under the "
        f"table. At last, {hero} spotted {clue} glinting near a table leg.",
        question="Where did the first clue lead?",
        cause=f"The clue was hidden under the dining table.",
        result=f"{hero} found {clue} beside a table leg.",
    )
    world.entities["clue"].meters["found"] = 1
    world.narrate(
        "suspense",
        f"The {clue} pointed toward the sideboard. {hero} lifted the cloth and "
        f"found the recipe book there—but also heard a soft step in the hall.",
    )
    world.narrate(
        "inner_monologue",
        f"“What if someone is waiting?” {hero} thought. “What if the {treat} "
        f"is meant for one person only? I must decide, darling, before the "
        "supper bell rings.”",
        question="Why did the child feel worried?",
        cause=f"{hero} heard a step while guarding the only special treat.",
        result=f"{hero} wondered whether to keep the treat or share it.",
    )
    world.narrate(
        "discovery",
        f"{hero} opened the recipe book. Inside was a picture of {darling} "
        f"cutting the same kind of {treat} into many cheerful slices. A line "
        "under the picture read, “Good food grows happier around a table.”",
        question="What did the recipe book reveal?",
        cause=f"The book showed {darling} serving the treat to many people.",
        result="Its message suggested that sharing could make the supper happier.",
    )

    if params.choice == "share":
        world.entities["treat"].meters.update(pieces=3, shared=1)
        world.entities["table"].meters["place_settings"] = 3
        world.entities["hero"].memes.update(bravery=1.0, kindness=1.0, worry=0.1)
        world.narrate(
            "decision",
            f"{hero} took a careful breath and chose to share. {hero} cut the "
            f"{treat} into three pieces, then set one plate for {darling} and "
            f"one for {guest}.",
            question="What decision did the child make?",
            cause=f"The recipe book showed that the treat belonged around a table.",
            result=f"{hero} divided the {treat} into three pieces for everyone.",
        )
        world.narrate(
            "turn",
            f"The hallway step belonged to {guest}, who had carried a small vase "
            f"of flowers. {darling} followed with the recipe book and smiled "
            f"when {hero} invited both of them to sit.",
            question="Who had made the sound in the hall?",
            cause=f"{guest} was bringing flowers while {darling} carried the book.",
            result="The frightening sound became the arrival of two supper guests.",
        )
        ending = (
            f"At the dining table, {darling} lifted a piece of {treat} to the "
            f"light. “You chose a generous heart,” {darling} said. {hero} "
            f"felt the room grow warmer as {guest} placed the flowers between "
            "the plates."
        )
    else:
        world.entities["treat"].meters.update(saved=1)
        world.entities["hero"].memes.update(bravery=0.8, kindness=0.4, worry=0.4)
        world.narrate(
            "decision",
            f"{hero} chose to save the {treat} beneath its glass cover. "
            f"{hero} placed a note beside it so {darling} would know it was "
            "waiting.",
            question="What decision did the child make?",
            cause=f"{hero} believed the special treat might have been prepared for {darling}.",
            result=f"{hero} saved the {treat} and left a loving note.",
        )
        world.narrate(
            "turn",
            f"The hallway step belonged to {guest}, who carried a basket of "
            f"warm rolls. {darling} arrived with the recipe book and explained "
            f"that the single treat had been saved for a family celebration.",
            question="Why was the treat kept beneath the cover?",
            cause=f"{hero} wanted to protect it for the celebration.",
            result=f"{darling} learned that {hero} had cared for the special food.",
        )
        ending = (
            f"{darling} placed the saved {treat} in the center of the table. "
            f"Then {guest} shared the warm rolls, and everyone made room for "
            "another plate. The little dining room filled with grateful smiles."
        )

    world.narrate(
        "ending",
        ending,
        question="How did the supper end?",
        cause="The hidden quest brought the family together at the dining table.",
        result="Everyone made room for one another and shared a warm, grateful moment.",
    )
    sample = StorySample(
        params=params,
        story="\n\n".join(event.text for event in world.history),
        prompts=[PROMPT],
        story_qa=[
            QAItem(event.question, f"{event.cause} {event.result}")
            for event in world.history
            if event.question
        ],
        world_qa=[
            QAItem(
                "Why can a dining table help people feel close?",
                "A dining table gives people a shared place to sit, talk, and care for one another.",
            ),
            QAItem(
                "What does it mean to decide carefully?",
                "It means noticing what others may need before choosing what to do.",
            ),
        ],
        world=world,
    )
    check_sample(sample)
    return sample


ASP_RULES = """
can_share :- treat_present, place_for_guest.
can_save :- treat_present, celebration.
decision(share) :- can_share.
decision(save) :- can_save, not can_share.
#show decision/1.
"""


def asp_facts() -> str:
    from asp import fact

    return "\n".join(
        [
            fact("treat_present"),
            fact("place_for_guest"),
            fact("celebration"),
        ]
    )


def asp_decisions() -> set[str]:
    from asp import atoms, one_model

    return {row[0] for row in atoms(one_model(asp_facts() + ASP_RULES), "decision")}


def check_sample(sample: StorySample) -> None:
    world = sample.world
    treat = world.entities["treat"]
    clue = world.entities["clue"]
    if not clue.meters["found"]:
        raise StoryError("The quest must discover its clue.")
    expected_ending = "the plates." if sample.params.choice == "share" else "grateful smiles."
    if not sample.story.endswith(expected_ending):
        raise StoryError("The story must end with a warm dining-room image.")
    if sample.params.choice == "share" and not treat.meters["shared"]:
        raise StoryError("A sharing choice must change the treat state.")
    if sample.params.choice == "save" and not treat.meters["saved"]:
        raise StoryError("A saving choice must change the treat state.")
    if len(sample.story_qa) < 4:
        raise StoryError("The story needs several grounded questions.")
    if any(not item.answer.strip() for item in sample.story_qa):
        raise StoryError("Every grounded question needs a natural answer.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--darling")
    parser.add_argument("--guest")
    parser.add_argument("--treat", choices=tuple(TREATS.values()))
    parser.add_argument("--clue", choices=tuple(CLUES.values()))
    parser.add_argument("--choice", choices=CHOICES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    darling = args.darling or rng.choice([name for name in DARLINGS if name != hero])
    guest = args.guest or rng.choice(
        [name for name in GUESTS if name not in (hero, darling)]
    )
    return StoryParams(
        hero=hero,
        darling=darling,
        guest=guest,
        treat=args.treat or rng.choice(tuple(TREATS.values())),
        clue=args.clue or rng.choice(tuple(CLUES.values())),
        choice=args.choice or rng.choice(CHOICES),
        seed=args.seed,
    )


def verify() -> None:
    if asp_decisions() != {"share"}:
        raise StoryError("The ASP decision rule did not produce the expected safe choice.")
    tested = 0
    for choice in CHOICES:
        for treat in TREATS.values():
            for clue in CLUES.values():
                sample = generate(
                    StoryParams(
                        hero="Mia",
                        darling="Grandma",
                        guest="Ben",
                        treat=treat,
                        clue=clue,
                        choice=choice,
                    )
                )
                check_sample(sample)
                tested += 1
    print(f"OK: {tested} story states; ASP decisions: {sorted(asp_decisions())}.")


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
                    "entities": sample.world.snapshot(),
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
            print(json.dumps(sorted(asp_decisions())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            samples = []
            for choice in CHOICES:
                namespace = argparse.Namespace(**vars(args))
                namespace.choice = choice
                samples.append(generate(resolve_params(namespace, rng)))
        else:
            samples = [
                generate(resolve_params(args, rng))
                for _ in range(args.n)
            ]

        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        else:
            for index, sample in enumerate(samples):
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
