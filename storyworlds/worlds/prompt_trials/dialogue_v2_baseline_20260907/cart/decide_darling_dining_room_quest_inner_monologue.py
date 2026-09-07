#!/usr/bin/env python3
"""Decide, Darling: a small dining-room quest about choosing together.

A child notices that a surprise supper cannot begin until one important choice
is made. Inner thoughts create suspense, while a gentle quest turns deciding
into a shared act of care.
"""

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
    kind: str = "thing"
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    beliefs: dict[str, str] = field(default_factory=dict)


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
    hero: str = "Nora"
    darling: str = "Grandma"
    choice: str = "lantern"
    clue: str = "blue ribbon"
    seed: int = 777


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {
            "hero": Entity(
                id="hero",
                label=params.hero,
                kind="character",
                location="dining_room",
                memes={"curiosity": 1.0, "worry": 0.4, "courage": 0.5},
            ),
            "darling": Entity(
                id="darling",
                label=params.darling,
                kind="character",
                location="kitchen",
                memes={"trust": 1.0, "warmth": 1.0},
            ),
            "table": Entity(
                id="table",
                label="the dining table",
                kind="furniture",
                location="dining_room",
                meters={"seats": 4, "set": 0},
            ),
            "cupboard": Entity(
                id="cupboard",
                label="the old cupboard",
                kind="furniture",
                location="dining_room",
                meters={"doors": 2},
            ),
            "clue": Entity(
                id="clue",
                label=params.clue,
                kind="clue",
                location="table",
                meters={"found": 0},
            ),
            "choice": Entity(
                id="choice",
                label=params.choice,
                kind="plan",
                location="cupboard",
                meters={"chosen": 0},
            ),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(
        self,
        kind: str,
        text: str,
        *,
        question: str = "",
        cause: str = "",
        result: str = "",
    ):
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

    def speak(self, speaker: str, text: str):
        actor = self.entities[speaker]
        tag = "asked" if text.endswith("?") else "said"
        self.history.append(
            Event(
                kind="speech",
                text=f'"{text}" {actor.label} {tag}.',
                state=self.snapshot(),
            )
        )

    def think(self, text: str):
        self.history.append(
            Event(
                kind="inner_monologue",
                text=f"{self.entities['hero'].label} thought, {text}",
                state=self.snapshot(),
            )
        )

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[QAItem(question=event.question, answer=f"{event.cause} {event.result}")
                      for event in self.history if event.question],
            world_qa=[],
            world=self,
        )


CHOICES = {
    "lantern": {
        "label": "the little brass lantern",
        "sound": "a tiny click",
        "ending": "a golden pool of light",
    },
    "flowers": {
        "label": "the vase of yellow flowers",
        "sound": "a soft rustle",
        "ending": "a bright yellow welcome",
    },
    "music": {
        "label": "the music box",
        "sound": "three tinkling notes",
        "ending": "a gentle tune",
    },
}

CLUES = ("blue ribbon", "paper star", "silver button")
NAMES = ("Nora", "Milo", "Elsie", "Theo", "June", "Cal")


PROMPT = (
    "Write a heartwarming children's story set in a dining room where a child "
    "must decide, darling, which hidden finishing touch will welcome a loved one. "
    "Use a quest, an inner monologue, suspense, and a tender resolution."
)

ASP_RULES = """
valid_choice(C) :- choice(C).
#show valid_choice/1.
"""


def validate_params(params: StoryParams):
    if params.choice not in CHOICES:
        raise StoryError("Choose a real dining-room finishing touch.")
    if params.clue not in CLUES:
        raise StoryError("Choose a recognized household clue.")
    if not re.fullmatch(r"[A-Z][a-z]+", params.hero):
        raise StoryError("The child's name must be a simple capitalized name.")
    if not re.fullmatch(r"[A-Z][a-z]+", params.darling):
        raise StoryError("The darling's name must be a simple capitalized name.")
    if params.hero == params.darling:
        raise StoryError("The child and the darling need different names.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def choose_touch(world: World):
    hero = world.entities["hero"]
    choice = world.entities["choice"]
    if hero.beliefs.get("chosen") != world.params.choice:
        raise StoryError("The child must decide on the promised finishing touch.")
    choice.meters["chosen"] = 1
    choice.location = "table"
    hero.memes["worry"] = 0.0
    hero.memes["courage"] = 1.0


def check_ending(world: World):
    if world.entities["choice"].meters["chosen"] != 1:
        raise StoryError("The selected finishing touch was never placed.")
    if world.entities["choice"].location != "table":
        raise StoryError("The chosen touch must reach the dining table.")
    if world.entities["table"].meters["set"] != 1:
        raise StoryError("The dining table must be ready at the end.")
    if world.entities["clue"].meters["found"] != 1:
        raise StoryError("The useful clue must be found.")
    if not any(event.kind == "inner_monologue" for event in world.history):
        raise StoryError("The story needs the child's inner monologue.")
    if not any(event.kind == "suspense" for event in world.history):
        raise StoryError("The story needs a suspenseful turn.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.entities["hero"].label
    darling = world.entities["darling"].label
    touch = CHOICES[params.choice]
    clue = params.clue

    world.narrate(
        "beginning",
        f"In the dining room, {hero} smoothed the tablecloth until it lay as flat "
        f"as a pond. Tonight, {darling} was coming home to a surprise supper.",
    )
    world.speak("hero", f"I want everything to be just right for {darling}.")
    world.think(
        '"But what should make the table special? If I choose the wrong thing, '
        "the surprise might feel small.\""
    )
    world.narrate(
        "quest",
        f"On the table lay a note from {darling}: “Dear one, follow the "
        f"{clue}.” Beneath it, three tiny paths of flour led toward the old cupboard.",
        question="What started the child's quest?",
        cause=f"{darling} left a note that named the {clue}.",
        result="The child followed the clue toward the cupboard.",
    )

    world.speak("hero", f"All right, {clue}. Show me where to go.")
    world.narrate(
        "search",
        f"{hero} followed the flour past four waiting chairs and under the table. "
        f"The {clue} was tied to the cupboard handle.",
    )
    world.entities["clue"].meters["found"] = 1
    world.entities["clue"].location = "cupboard"
    world.think(
        '"The cupboard has three doors. One may hold the answer, and the others '
        "may hold only dust.\""
    )
    world.narrate(
        "suspense",
        f"The dining room clock gave one slow chime. {hero} reached for a cupboard "
        f"door, but it did not open.",
        question="Why did the child feel suspense?",
        cause="The clock chimed while the first cupboard door stayed shut.",
        result=f"{hero} had to keep searching before {darling} arrived.",
    )

    world.speak("hero", "Please, little cupboard. I need to decide.")
    world.think(
        '"I could pick anything. But a good choice should tell {darling} that I '
        'noticed what makes this room feel like home."'.format(darling=darling)
    )
    world.narrate(
        "discovery",
        f"The {clue} slipped loose. Behind it was a small card with three words: "
        f"“Choose what helps {darling} feel welcome.”",
        question="What helped the child decide?",
        cause="The card said to choose the touch that would help the darling feel welcome.",
        result=f"{hero} stopped guessing and thought about {darling}'s comfort.",
    )

    world.speak("hero", f"I decide on {touch['label']}.")
    world.entities["hero"].beliefs["chosen"] = params.choice
    choose_touch(world)
    world.narrate(
        "decision",
        f"{hero} carried {touch['label']} from the cupboard and placed it at "
        f"the center of the table. The room seemed to hold its breath.",
        question="What did the child decide to place on the table?",
        cause=f"{hero} chose {touch['label']} because it would make {darling} feel welcome.",
        result=f"{touch['label'].capitalize()} took its place at the center of the table.",
    )

    world.entities["table"].meters["set"] = 1
    world.speak("hero", "The table is ready. I hope the welcome is big enough.")
    world.think(
        '"I cannot make the supper perfect. I can make this one small kindness true."'
    )
    world.narrate(
        "arrival",
        f"Then the front door opened. {darling} stepped into the dining room and "
        f"paused when {touch['sound']} sounded near the table.",
    )
    world.speak("darling", f"You remembered what makes this room feel warm.")
    world.speak("hero", "I remembered you.")
    world.narrate(
        "ending",
        f"{darling} hugged {hero}. Around them, the dining room glowed with "
        f"{touch['ending']}, and the supper waited while they sat close together.",
        question="How did the child know the decision was right?",
        cause=f"{darling} recognized the thoughtful welcome at the table.",
        result="They shared a hug before beginning supper together.",
    )

    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    check_ending(sample.world)
    speech = [event for event in sample.world.history if event.kind == "speech"]
    if len(speech) < 6:
        raise StoryError("The story needs enough spoken turns to feel alive.")
    if not any(event.kind == "quest" for event in sample.world.history):
        raise StoryError("The story must contain a quest.")
    if len(sample.story_qa) < 4:
        raise StoryError("The story needs several grounded questions and answers.")
    if any(not item.question or not item.answer for item in sample.story_qa):
        raise StoryError("Every grounded QA item needs a natural question and answer.")


def valid_choices() -> list[str]:
    return list(CHOICES)


def asp_facts() -> str:
    from asp import fact

    return "\n".join(fact("choice", choice) for choice in valid_choices())


def asp_choices() -> set[str]:
    from asp import atoms, one_model

    symbols = one_model(asp_facts() + "\n" + ASP_RULES)
    return {row[0] for row in atoms(symbols, "valid_choice")}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--darling")
    parser.add_argument("--choice", choices=tuple(CHOICES))
    parser.add_argument("--clue", choices=CLUES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    darling_pool = [name for name in NAMES if name != hero]
    darling = args.darling or rng.choice(darling_pool)
    params = StoryParams(
        hero=hero,
        darling=darling,
        choice=args.choice or rng.choice(valid_choices()),
        clue=args.clue or rng.choice(CLUES),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if asp_choices() != set(valid_choices()):
        raise StoryError("Python and ASP disagree about valid dining-room choices.")
    tested = 0
    for choice in valid_choices():
        for clue in CLUES:
            sample = generate(
                StoryParams(
                    hero="Nora",
                    darling="Grandma",
                    choice=choice,
                    clue=clue,
                )
            )
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} story states; ASP agrees on {len(valid_choices())} choices.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""):
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
            print(json.dumps(sorted(asp_choices())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            choices = [
                choice
                for choice in valid_choices()
                if args.choice is None or choice == args.choice
            ]
            if not choices:
                raise StoryError("No choices match the requested options.")
            params_list = [
                resolve_params(
                    argparse.Namespace(
                        **vars(args),
                        choice=choice,
                    ),
                    rng,
                )
                for choice in choices
            ]
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payloads = [sample.to_dict() for sample in samples]
            print(
                json.dumps(
                    payloads[0] if len(payloads) == 1 else payloads,
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            for index, sample in enumerate(samples):
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {index + 1}\n"
                    if len(samples) > 1
                    else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
