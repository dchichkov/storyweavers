#!/usr/bin/env python3
"""A warm dining-room quest about deciding what kindness requires."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
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
    location: str = "dining_room"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    question: str = ""
    cause: str = ""
    result: str = ""


@dataclass
class StoryParams:
    hero: str = "Mara"
    companion: str = "Eli"
    path: str = "candle"
    seed: int = 777


PATHS = ("candle", "letter", "cake")
NAMES = ("Mara", "Eli", "Nora", "Theo", "June", "Iris")
PROMPT = (
    "Write a heartwarming children's story set in a dining room, where a quest "
    "and an inner monologue lead to a brave decision."
)

ASP_RULES = """
possible(candle).
possible(letter).
possible(cake).
#show possible/1.
"""


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, "character",
                           memes={"courage": 0.0, "warmth": 0.5}),
            "companion": Entity("companion", params.companion, "character",
                                memes={"courage": 0.0, "warmth": 0.5}),
            "table": Entity("table", "the dining table", "furniture"),
        }
        self.history: list[Event] = []

    def scene(self, kind: str, text: str, *, question: str = "",
              cause: str = "", result: str = ""):
        self.history.append(Event(kind, text, question, cause, result))

    def speak(self, speaker: str, text: str):
        if not text.endswith((".", "?", "!")):
            text += "."
        self.scene("speech", f'"{text}" said {self.entities[speaker].label}.')

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(event.question, f"{event.cause} {event.result}")
                for event in self.history if event.question
            ],
            world_qa=[
                QAItem(
                    "What kind of room was at the heart of the quest?",
                    "The quest took place in a dining room.",
                ),
                QAItem(
                    "What helped the children solve their trouble?",
                    "They listened carefully, thought about what they learned, and made a kind decision.",
                ),
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.path not in PATHS:
        raise StoryError("The quest path must be candle, letter, or cake.")
    if params.hero == params.companion:
        raise StoryError("The two characters need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name)
           for name in (params.hero, params.companion)):
        raise StoryError("Names must be simple capitalized names.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero, companion = params.hero, params.companion
    rng = random.Random(params.seed)
    opening = rng.choice([
        f"{hero} and {companion} stood in the sunny dining room after lunch.",
        f"After lunch, {hero} and {companion} found the dining room unusually quiet.",
    ])
    world.scene(
        "beginning",
        opening + " Their grandmother had left them a small quest: make one thoughtful "
        "choice before she came home.",
    )
    world.speak("hero", "What should we decide, darling?")
    world.speak("companion", "Let's look carefully before we hurry.")
    hero_entity = world.entities["hero"]
    companion_entity = world.entities["companion"]

    if params.path == "candle":
        world.scene(
            "trouble",
            "A little candle trembled near the window, and a cool draft pulled its flame toward the curtain.",
            question="Why did the children need to act quickly?",
            cause="They noticed that a draft was carrying the candle flame toward the curtain.",
            result="They understood that waiting could make the dining room unsafe.",
        )
        world.speak("hero", "I want to blow it out, but Grandma may need it for dinner.")
        world.speak("companion", "The saucer can hold it safely. I saw one beside the sink.")
        world.scene(
            "learning",
            f"{hero} paused. In an inner monologue, {hero} thought, "
            '"A safe dinner is more important than keeping the candle in its pretty place." '
            f"{companion} had learned where the saucer was, so {hero} no longer had to guess.",
            question="What useful information did the children learn?",
            cause=f"{companion} remembered that a saucer was waiting beside the sink.",
            result=f"{hero} realized the candle could be moved without simply wasting it.",
        )
        world.speak("hero", "I decide we should carry it together.")
        world.speak("companion", "I will steady the saucer while you lift the candle.")
        world.scene(
            "resolution",
            f"Together they moved the candle onto the saucer and set it far from the curtain. "
            f"The flame stood still, and {hero} smiled when the room became safe again.",
            question="How did their decision solve the candle trouble?",
            cause=f"{hero} decided to move the candle onto the saucer with {companion}'s help.",
            result="The candle stayed lit in a safe place, away from the curtain.",
        )
    elif params.path == "letter":
        world.scene(
            "trouble",
            "A folded letter lay beneath a plate, and the envelope was already damp from a spilled glass.",
            question="Why was the letter in danger?",
            cause="A spill had reached the envelope beneath the plate.",
            result="The children knew the paper might be ruined if they left it there.",
        )
        world.speak("hero", "Perhaps I should open it to see who needs help.")
        world.speak("companion", "The name on the front says Aunt Rose, and the postmark says tomorrow's village.")
        world.scene(
            "learning",
            f"{hero} held back a hand. In an inner monologue, {hero} thought, "
            '"A secret is not mine just because I am curious." '
            f"{hero} learned that the letter belonged to Aunt Rose, while {companion} learned it was meant to travel soon.",
            question="What did the children learn about the letter?",
            cause=f"They read the name Aunt Rose and saw that it was meant for the next village post.",
            result="They understood both who owned it and why time mattered.",
        )
        world.speak("hero", "I decide we should dry the envelope without opening it.")
        world.speak("companion", "I will fetch a clean towel, and you can tell Aunt Rose what happened.")
        world.scene(
            "resolution",
            f"{companion} brought a towel, and {hero} rested the letter on it. "
            f"When Aunt Rose arrived, the envelope was dry enough to carry, and {hero} felt glad that curiosity had not broken trust.",
            question="How did their decision protect Aunt Rose's letter?",
            cause=f"{hero} decided not to open the letter, and {companion} brought a clean towel.",
            result="They dried the envelope and returned it unopened to its owner.",
        )
    else:
        world.scene(
            "trouble",
            "A small cake waited on the table, but one corner had fallen onto the floor just as Grandma's footsteps sounded outside.",
            question="What trouble did the cake have?",
            cause="One corner of the cake had fallen onto the floor.",
            result="The children could not serve it as if nothing had happened.",
        )
        world.speak("hero", "I could hide the missing corner with berries.")
        world.speak("companion", "The floor was dusty, but there are apples in the basket.")
        world.scene(
            "learning",
            f"{hero} looked at the cake. In an inner monologue, {hero} thought, "
            '"A pretty plate cannot make a fallen piece clean." '
            f"{companion} had found fresh apples, and {hero} learned that an honest new treat could still welcome Grandma.",
            question="What did the children learn before choosing?",
            cause=f"{companion} found fresh apples, and {hero} recognized that the fallen cake should not be served.",
            result="They learned they could make a different, clean treat instead of hiding the mistake.",
        )
        world.speak("hero", "I decide we should tell Grandma and share apple slices.")
        world.speak("companion", "I will wash the apples while you clear the plate.")
        world.scene(
            "resolution",
            f"They cleared the fallen cake and arranged crisp apple slices in a bright circle. "
            f"Grandma entered, heard the truth, and hugged them before sitting at the dining table.",
            question="How did their decision change the ending?",
            cause=f"{hero} decided to tell the truth and offer clean apple slices instead.",
            result="The children shared a fresh snack, and Grandma answered their honesty with a hug.",
        )

    hero_entity.memes["courage"] = 1.0
    companion_entity.memes["courage"] = 1.0
    hero_entity.memes["warmth"] = 1.0
    companion_entity.memes["warmth"] = 1.0
    world.scene(
        "ending",
        f"The dining room glowed with the small proof of their choice: a safe candle, a trusted letter, "
        f"or a clean shared snack. {hero} and {companion} sat side by side, glad that deciding kindly "
        "had made the room feel warmer.",
    )
    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    if len(world.history) < 10:
        raise StoryError("The story needs a beginning, exchange, turn, and ending.")
    speech = [event for event in world.history if event.kind == "speech"]
    if not any("decide" in event.text.lower() for event in speech):
        raise StoryError("The story must include the seed word decide.")
    if not any(event.kind == "ending" for event in world.history):
        raise StoryError("The story needs a visible ending image.")
    if world.entities["hero"].memes["courage"] != 1.0:
        raise StoryError("The resolved state must show the hero's courage.")
    if len(sample.story_qa) != 3:
        raise StoryError("Each path needs three grounded questions.")
    if any(not item.answer.strip() for item in sample.story_qa):
        raise StoryError("Every grounded answer must explain a consequence.")


def valid_combos() -> list[str]:
    return list(PATHS)


def asp_facts() -> str:
    from asp import fact
    return "\n".join(fact("possible", path) for path in PATHS)


def asp_paths() -> set[str]:
    from asp import atoms, one_model
    return {row[0] for row in atoms(one_model(asp_facts() + ASP_RULES), "possible")}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--companion")
    parser.add_argument("--path", choices=PATHS)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    companions = [name for name in NAMES if name != hero and name != args.hero]
    companion = args.companion or rng.choice(companions)
    path = args.path or rng.choice(PATHS)
    params = StoryParams(hero=hero, companion=companion, path=path, seed=args.seed)
    validate_params(params)
    return params


def verify():
    if set(valid_combos()) != asp_paths():
        raise StoryError("Python and ASP disagree about quest paths.")
    for index, path in enumerate(PATHS):
        sample = generate(StoryParams(path=path, seed=900 + index))
        check_sample(sample)
    print(f"OK: {len(PATHS)} complete quest paths verified.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = ""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({
            "entities": {key: asdict(value) for key, value in sample.world.entities.items()},
            "history": [asdict(event) for event in sample.world.history],
        }, indent=2))


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
            print(json.dumps(sorted(asp_paths())))
            return 0
        rng = random.Random(args.seed)
        if args.all:
            paths = [path for path in PATHS
                     if args.path is None or args.path == path]
            params_list = []
            for path in paths:
                local = argparse.Namespace(**vars(args))
                local.path = path
                params_list.append(resolve_params(local, rng))
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]
        samples = [generate(params) for params in params_list]
        if args.json:
            data = [sample.to_dict() for sample in samples]
            print(json.dumps(data[0] if len(data) == 1 else data,
                             ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(sample, trace=args.trace, qa=args.qa,
                     header=f"\n### Story {index + 1}\n"
                     if len(samples) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
