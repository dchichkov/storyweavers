#!/usr/bin/env python3
"""A cautionary cappuccino whodunit about a missing cork and a foamy cheek."""

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
    kind: str
    location: str = ""
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
    hero: str = "Luna"
    helper: str = "Pip"
    suspect: str = "Mara"
    culprit: str = "Toby"
    drink: str = "cappuccino"
    object_name: str = "cork"
    clue: str = "cheek"
    cautionary: bool = True
    seed: int = 777


NAMES = ("Luna", "Pip", "Mara", "Toby", "Nia", "Sol")
PROMPT = (
    "Write a cautionary children's whodunit about a missing cork, a cappuccino, "
    "and a foamy cheek, with careful friends solving the mystery through dialogue."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
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

    def say(self, speaker: str, text: str, *, tag: str = "said") -> None:
        label = self.entities[speaker].label
        if text.endswith("?"):
            tag = "asked"
        self.history.append(
            Event(kind="speech", text=f'"{text}" {label} {tag}.', state=self.snapshot())
        )


def validate_params(params: StoryParams) -> None:
    if params.drink != "cappuccino":
        raise StoryError("This cautionary mystery requires a cappuccino.")
    if params.object_name != "cork":
        raise StoryError("The missing object must be a cork.")
    if params.clue != "cheek":
        raise StoryError("The visible clue must be a cheek.")
    names = (params.hero, params.helper, params.suspect, params.culprit)
    if len(set(names)) != len(names):
        raise StoryError("Every character needs a different name.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in names):
        raise StoryError("Use simple capitalized names, such as Luna and Pip.")
    if not params.cautionary:
        raise StoryError("The story must keep its cautionary feature.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    world.entities.update(
        {
            "hero": Entity(
                "hero",
                params.hero,
                "character",
                "cafe",
                memes={"curiosity": 1.0, "care": 0.5},
            ),
            "helper": Entity(
                "helper",
                params.helper,
                "character",
                "cafe",
                memes={"curiosity": 0.8, "care": 0.7},
            ),
            "suspect": Entity(
                "suspect",
                params.suspect,
                "character",
                "cafe",
                memes={"worry": 0.4},
            ),
            "culprit": Entity(
                "culprit",
                params.culprit,
                "character",
                "cafe",
                memes={"worry": 0.2},
            ),
            "cup": Entity(
                "cup",
                "the cappuccino cup",
                "drink",
                "counter",
                meters={"foam": 1.0, "safe_temperature": 1.0},
            ),
            "cork": Entity(
                "cork",
                "the cork",
                "object",
                "counter",
                meters={"present": 1.0, "wet": 0.0},
            ),
            "napkin": Entity(
                "napkin",
                "a blue napkin",
                "object",
                "table",
                meters={"foam_mark": 0.0},
            ),
            "door": Entity(
                "door",
                "the café door",
                "place",
                "cafe",
                meters={"draft": 1.0},
            ),
        }
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.entities["hero"].label
    helper = world.entities["helper"].label
    suspect = world.entities["suspect"].label
    culprit = world.entities["culprit"].label
    cup = world.entities["cup"]
    cork = world.entities["cork"]
    napkin = world.entities["napkin"]

    world.narrate(
        "beginning",
        f"{hero} and {helper} were sharing a warm cappuccino at the little café. "
        "A round cork rested beside the cup, keeping the sweet foam from cooling too fast.",
    )
    world.say("hero", "Please leave the cork beside the cup while I fetch two spoons.")
    world.say("helper", "I will watch it carefully.")
    world.narrate(
        "warning",
        f"{hero} pointed to the hot cappuccino. The {helper.lower()} nodded, but "
        "the café door opened with a chilly draft.",
        question="Why did the friends need to watch the cork?",
        cause="The cork helped keep the cappuccino warm, and the open door could send it sliding.",
        result="The friends agreed to leave the cork beside the cup and watch it carefully.",
    )

    cork.location = "missing"
    cork.meters["present"] = 0.0
    world.say("helper", "The cork is gone!")
    world.say("hero", "Nobody touch the cup. We should look for clues before we blame anyone.")
    world.narrate(
        "mystery",
        f"When {hero} returned, the cork had vanished. A tiny brown smear crossed the counter, "
        f"and {suspect} stood nearby with a surprised look.",
        question="What changed while the friends were getting spoons?",
        cause="A draft moved the loose cork away from the cappuccino.",
        result="The cork disappeared from the counter, leaving a small brown smear.",
    )

    world.say("suspect", "I did not take it. I only reached for my scarf.")
    world.say("hero", "Did you see where the cork went?")
    world.say("suspect", "I saw it roll toward the door, but Toby hurried past me.")
    world.say("helper", "Then we need to ask Toby, not guess.")
    world.say("culprit", "Why is everyone looking at me?")
    world.say("hero", "What did you do when the door opened?")
    world.say("culprit", "I caught the cork before it went outside.")
    world.say("helper", "Then where is it now?")
    world.say("culprit", "I put it in my pocket. I wanted to surprise you.")

    world.entities["culprit"].location = "table"
    world.entities["culprit"].memes["worry"] = 0.8
    world.narrate(
        "clue",
        f"{culprit} pulled the cork from a pocket. A white crescent of foam marked one cheek, "
        f"and the blue napkin had a matching round print.",
        question="What clue showed that Toby had handled the cork?",
        cause=f"{culprit} had caught the cork and tucked it into a pocket near the cappuccino.",
        result="Foam on his cheek and a round mark on the napkin connected him to the missing cork.",
    )

    world.say("culprit", "I was going to put it back, but I forgot.")
    world.say("hero", "Your idea was kind, but hiding a useful thing was unsafe.")
    world.say("helper", "And drinking from a cup without checking the cork could make a mess.")
    world.say("culprit", "I am sorry. I should have told you at once.")
    world.say("hero", "Please put it beside the cup, not in your pocket.")
    cork.location = "counter"
    cork.meters["present"] = 1.0
    cup.meters["safe_temperature"] = 1.0
    napkin.meters["foam_mark"] = 1.0
    world.entities["hero"].memes["care"] = 1.0
    world.entities["helper"].memes["care"] = 1.0

    world.narrate(
        "resolution",
        f"{culprit} placed the cork beside the cappuccino and wiped the foam from his cheek. "
        f"{hero} set the cup safely away from the draft, while {helper} folded the marked napkin.",
        question="How did the friends solve the mystery safely?",
        cause=f"{culprit} admitted catching the cork, and the cheek and napkin marks supported his words.",
        result="They returned the cork, moved the cappuccino from the draft, and learned to speak up quickly.",
    )
    world.say("helper", "A surprise is only good when nobody is put at risk.")
    world.say("culprit", "Next time I will ask before I move anything.")
    world.say("hero", "And we will check the cup before taking a sip.")

    world.narrate(
        "ending",
        f"The café door clicked shut. The cork stayed beside the cappuccino, the foam stayed in the cup, "
        f"and {culprit}'s cheek was clean at last.",
        question="What caution did the children learn?",
        cause="The cork had been moved without telling anyone while a cold draft threatened the drink.",
        result="They learned to ask before moving things and to report a surprise immediately.",
    )
    sample = world.sample()
    check_sample(sample)
    return sample


def World_sample(self: World) -> StorySample:
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
                "Why should a hot drink be kept away from a draft?",
                "A draft can cool or move a drink, so it is safer to place the cup securely away from the open door.",
            ),
            QAItem(
                "What should someone do before moving another person's object?",
                "They should ask first and explain where they are putting it.",
            ),
        ],
        world=self,
    )


World.sample = World_sample


def check_sample(sample: StorySample) -> None:
    world = sample.world
    if world.entities["cork"].location != "counter":
        raise StoryError("The cork must be returned to the counter.")
    if world.entities["cork"].meters["present"] != 1.0:
        raise StoryError("The final state must show the cork present.")
    if world.entities["cup"].meters["safe_temperature"] != 1.0:
        raise StoryError("The cappuccino must end in a safe place.")
    speech = [event for event in world.history if event.kind == "speech"]
    if len(speech) < 12:
        raise StoryError("The whodunit needs a sustained dialogue.")
    speakers = {event.text.split('"')[-1].split()[0] for event in speech}
    if len(speakers) < 4:
        raise StoryError("The mystery needs several speaking characters.")
    if len(sample.story_qa) < 4:
        raise StoryError("The story needs grounded questions and answers.")
    if any(not item.answer.strip() for item in sample.story_qa):
        raise StoryError("Every story question needs a natural answer.")


ASP_RULES = """
missing_cork :- cork_moved, not cork_returned.
clue_supports(toby) :- foam_cheek, napkin_mark.
careful_solution :- cork_returned, cup_safe, clue_supports(toby).
#show careful_solution/0.
"""


def asp_facts() -> str:
    from asp import fact

    return "\n".join(
        [
            fact("cork_moved"),
            fact("foam_cheek"),
            fact("napkin_mark"),
            fact("cork_returned"),
            fact("cup_safe"),
        ]
    )


def asp_check() -> bool:
    from asp import atoms, one_model

    model = one_model(asp_facts() + ASP_RULES)
    return bool(atoms(model, "careful_solution"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--suspect")
    parser.add_argument("--culprit")
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    chosen = []
    used = set()
    for requested in (args.hero, args.helper, args.suspect, args.culprit):
        if requested:
            chosen.append(requested)
            used.add(requested)
        else:
            options = [name for name in NAMES if name not in used]
            value = rng.choice(options)
            chosen.append(value)
            used.add(value)
    return StoryParams(
        hero=chosen[0],
        helper=chosen[1],
        suspect=chosen[2],
        culprit=chosen[3],
        seed=args.seed,
    )


def verify() -> None:
    if not asp_check():
        raise StoryError("ASP did not find the careful resolved state.")
    sample = generate(StoryParams())
    check_sample(sample)
    print("OK: Python and ASP agree; the cautionary whodunit resolves safely.")


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
            print(json.dumps({"careful_solution": asp_check()}))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            params_list = []
            for offset in range(4):
                names = list(NAMES)
                rng.shuffle(names)
                params_list.append(
                    StoryParams(
                        hero=names[0],
                        helper=names[1],
                        suspect=names[2],
                        culprit=names[3],
                        seed=args.seed + offset,
                    )
                )
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload, ensure_ascii=False, indent=2))
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
