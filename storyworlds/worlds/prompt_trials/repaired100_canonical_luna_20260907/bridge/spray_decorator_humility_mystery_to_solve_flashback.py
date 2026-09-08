#!/usr/bin/env python3
"""A quiet morning mystery about a missing spray, a decorator, and humility."""

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
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
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
    speaker: str = ""
    listener: str = ""
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Luna"
    neighbor: str = "Mara"
    color: str = "yellow"
    place: str = "porch"
    seed: int = 777


NAMES = ("Luna", "Mara", "Nia", "Pia", "Suri", "Tess")
COLORS = ("yellow", "blue", "coral", "green")
PLACES = ("porch", "garden", "window_box")
PROMPT = (
    "Write a gentle slice-of-life children's story about a decorator solving a "
    "missing-spray mystery, using a misunderstanding, a flashback, and humility."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity(
                "hero", params.hero, "character", params.place,
                memes={"curiosity": 0.7, "pride": 0.7, "humility": 0.3},
            ),
            "neighbor": Entity(
                "neighbor", params.neighbor, "character", "hallway",
                memes={"trust": 0.7, "patience": 0.7},
            ),
            "spray": Entity(
                "spray", f"the {params.color} spray bottle", "tool", "shelf",
                meters={"full": 1, "found": 0},
            ),
            "cloth": Entity(
                "cloth", "the soft decorating cloth", "tool", params.place,
                meters={"used": 0},
            ),
            "plant": Entity(
                "plant", "the sleepy fern", "plant", params.place,
                meters={"decorated": 0},
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

    def say(self, speaker: str, text: str, *, to: str = ""):
        actor = self.entities[speaker]
        tag = "asked" if text.endswith("?") else "said"
        self.history.append(
            Event(
                kind="speech",
                text=f'"{text}" {actor.label} {tag}.',
                speaker=speaker,
                listener=to,
                state=self.snapshot(),
            )
        )

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(event.question, f"{event.cause} {event.result}")
                for event in self.history
                if event.question
            ],
            world_qa=[
                QAItem(
                    "What does a decorator use spray for?",
                    "A decorator can use spray to add a light finish or fresh look to an object or plant.",
                ),
                QAItem(
                    "Why is humility helpful when solving a misunderstanding?",
                    "Humility helps a person admit a mistake, listen carefully, and repair trust.",
                ),
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.color not in COLORS:
        raise StoryError("Choose a color from the available spray colors.")
    if params.place not in PLACES:
        raise StoryError("Choose a simple decorating place.")
    if params.hero == params.neighbor:
        raise StoryError("The decorator and neighbor need different names.")
    for name in (params.hero, params.neighbor):
        if not re.fullmatch(r"[A-Z][a-z]+", name):
            raise StoryError("Use simple capitalized names, such as Luna and Mara.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def find_spray(world: World):
    spray = world.entities["spray"]
    spray.location = world.params.place
    spray.meters["found"] = 1


def decorate(world: World):
    spray, cloth, plant = (
        world.entities["spray"],
        world.entities["cloth"],
        world.entities["plant"],
    )
    if not spray.meters["found"]:
        raise StoryError("The decorator must find the spray before using it.")
    spray.meters["full"] = 0
    cloth.meters["used"] = 1
    plant.meters["decorated"] = 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    h = world.entities["hero"].label
    n = world.entities["neighbor"].label
    spray = world.entities["spray"].label
    place = world.params.place

    world.narrate(
        "beginning",
        f"{h} liked making small corners cheerful. That morning, {h} spread a cloth beside "
        f"the sleepy fern on the {place} and planned to finish the leaves with {spray}.",
    )
    world.say("hero", "A little spray, a clean cloth, and this fern will look ready for visitors.")
    world.say("neighbor", "Did you say you would spray the whole porch?")
    world.say("hero", "The whole porch? No, only the fern's leaves.")
    world.narrate(
        "misunderstanding",
        f"{n} hurried away with a worried look. {h} noticed that the {spray} was no longer on the shelf.",
        question="What misunderstanding started the mystery?",
        cause=f"{n} mistook {h}'s plan to spray the fern for a plan to spray the whole {place}.",
        result=f"{n} moved the {spray} away, and {h} had to discover where it went.",
    )

    world.say("hero", f"I thought {n} understood me. Maybe {n} hid the spray.")
    world.say("neighbor", "I heard you say the porch needed spraying.")
    world.say("hero", "I did not say that. Wait. Where did you put the bottle?")
    world.say("neighbor", "I set it somewhere safe. I can help you look.")
    world.say("hero", "I suppose blaming you will not make it appear.")
    world.say("neighbor", "Then let us remember the morning slowly.")

    world.narrate(
        "flashback",
        f"{h} closed their eyes and pictured the first moments again. The cloth had slipped from "
        f"the table, and {h} had carried it to the fern. While picking up a fallen button, {h} had "
        f"placed the {spray} beside the flowerpot instead of back on the shelf.",
        question="What did the flashback reveal?",
        cause=f"{h} remembered carrying the cloth and setting the {spray} beside the flowerpot.",
        result="The missing bottle had been moved by accident, not hidden by the neighbor.",
    )

    world.say("hero", "I remember now. I moved it myself while picking up that button.")
    world.say("neighbor", "The flowerpot is behind the fern. Shall we check there?")
    world.say("hero", "Yes. And I am sorry I guessed that you hid it.")
    find_spray(world)
    world.narrate(
        "discovery",
        f"Behind the fern, {n} spotted {spray} beside the flowerpot. Its cap was closed, "
        "and not a single drop had spilled.",
        question="Where was the spray found?",
        cause=f"{h} had left it beside the flowerpot while moving the decorating cloth.",
        result=f"{n} found {spray} behind the fern, safe and ready to use.",
    )

    world.say("neighbor", "There it is. Your memory solved the mystery.")
    world.say("hero", "My memory also made me accuse you first.")
    world.say("neighbor", "You corrected yourself. That matters.")
    world.say("hero", "Will you help me use one gentle spray on the fern?")
    world.say("neighbor", "Only if you let me hold the cloth under the leaves.")
    world.say("hero", "Deal.")

    decorate(world)
    world.entities["hero"].memes["humility"] = 1.0
    world.entities["neighbor"].memes["trust"] = 1.0
    world.narrate(
        "repair",
        f"{h} held the {spray} far from the fern while {n} held the soft cloth underneath. "
        "One light mist settled on the leaves, and the cloth caught every extra drop.",
        question="How did they finish decorating safely?",
        cause="They used one light spray and held a cloth under the leaves.",
        result="The fern looked fresh without wetting the porch.",
    )
    world.say("neighbor", "That is enough shine for one little fern.")
    world.say("hero", "And enough humility for one little mystery.")
    world.narrate(
        "ending",
        f"The yellow-green fern stood quietly on the {place}. The {spray} rested beside the "
        "flowerpot, and {h} wrote a small label: 'Ask before guessing.'",
    )
    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    if not world.entities["spray"].meters["found"]:
        raise StoryError("The spray must be found.")
    if not world.entities["plant"].meters["decorated"]:
        raise StoryError("The fern must be decorated.")
    if world.entities["hero"].memes["humility"] < 1:
        raise StoryError("The decorator must learn humility.")
    speech = [event for event in world.history if event.kind == "speech"]
    if len(speech) < 12:
        raise StoryError("The story needs a sustained back-and-forth exchange.")
    if {event.speaker for event in speech} != {"hero", "neighbor"}:
        raise StoryError("Both characters must speak.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs grounded questions and answers.")
    if not any(event.kind == "flashback" for event in world.history):
        raise StoryError("The mystery needs a flashback.")


ASP_RULES = """
found_after_memory :- moved_by_decorator, remembers.
solved :- found_after_memory, apology, decorate.
#show solved/0.
"""


def asp_facts() -> str:
    from asp import fact

    return "\n".join(
        [
            fact("moved_by_decorator"),
            fact("remembers"),
            fact("apology"),
            fact("decorate"),
        ]
    )


def asp_solved() -> bool:
    from asp import one_model, atoms

    return bool(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "solved"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--neighbor")
    parser.add_argument("--color", choices=COLORS)
    parser.add_argument("--place", choices=PLACES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    neighbors = [name for name in NAMES if name != hero]
    neighbor = args.neighbor or rng.choice(neighbors)
    params = StoryParams(
        hero=hero,
        neighbor=neighbor,
        color=args.color or rng.choice(COLORS),
        place=args.place or rng.choice(PLACES),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if not asp_solved():
        raise StoryError("ASP did not confirm the repaired mystery.")
    count = 0
    for color in COLORS:
        for place in PLACES:
            sample = generate(
                StoryParams(hero="Luna", neighbor="Mara", color=color, place=place)
            )
            check_sample(sample)
            count += 1
    print(f"OK: {count} story states; Python and ASP agree.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print(
            "\nTRACE\n"
            + json.dumps(
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
            print(json.dumps({"solved": asp_solved()}))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            samples = []
            for color in COLORS:
                for place in PLACES:
                    samples.append(
                        generate(
                            StoryParams(
                                hero=args.hero or "Luna",
                                neighbor=args.neighbor or "Mara",
                                color=color,
                                place=place,
                                seed=args.seed,
                            )
                        )
                    )
        else:
            samples = [generate(resolve_params(args, rng)) for _ in range(args.n)]

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
