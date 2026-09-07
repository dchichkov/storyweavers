#!/usr/bin/env python3
"""A bedtime story about sharing a nose-shaped moon lantern before dawn."""

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
    speaker: str = ""
    listener: str = ""
    revealed: str = ""
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Nora"
    friend: str = "Pip"
    moon: str = "silver"
    sharing: str = "lantern"
    seed: int = 777


NAMES = ("Nora", "Pip", "Milo", "Lina", "Tess", "Owen")
MOONS = {
    "silver": "silver moon",
    "golden": "golden moon",
    "blue": "blue moon",
}
SHARING = {
    "lantern": "the nose-shaped lantern",
    "blanket": "the warm blanket",
    "teacup": "the little teacup",
}
PROMPT = (
    "Write a gentle bedtime story in which two children share a small object, "
    "notice a nose-shaped clue, and prepare kindly for something that happens later."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity(
                "hero", params.hero, "character", "bedroom",
                memes={"kindness": 0.5, "worry": 0.4, "trust": 0.5},
            ),
            "friend": Entity(
                "friend", params.friend, "character", "bedroom",
                memes={"kindness": 0.5, "worry": 0.5, "trust": 0.5},
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

    def say(
        self,
        speaker: str,
        text: str,
        *,
        to: str = "",
        reveal: str = "",
    ):
        actor = self.entities[speaker]
        if reveal:
            if not to or reveal not in actor.beliefs:
                raise StoryError("A speaker cannot share a secret they do not know.")
            self.entities[to].beliefs[reveal] = actor.beliefs[reveal]
        tag = "asked" if text.endswith("?") else "said"
        self.history.append(
            Event(
                kind="speech",
                text=f'"{text}" {actor.label} {tag}.',
                speaker=speaker,
                listener=to,
                revealed=reveal,
                state=self.snapshot(),
            )
        )

    def share(self):
        self.entities["hero"].memes["kindness"] = 1.0
        self.entities["friend"].memes["kindness"] = 1.0
        self.entities["hero"].memes["trust"] = 1.0
        self.entities["friend"].memes["trust"] = 1.0


ASP_RULES = """
can_share(lantern).
can_share(blanket).
can_share(teacup).
gentle(moon).
safe(nose).
ready(X) :- can_share(X), gentle(moon), safe(nose).
#show ready/1.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        [fact("can_share", item) for item in SHARING]
        + [fact("gentle", "moon"), fact("safe", "nose")]
    )


def asp_options() -> set[tuple[str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "ready"))


def validate_params(params: StoryParams):
    if params.moon not in MOONS:
        raise StoryError("Choose a silver, golden, or blue moon.")
    if params.sharing not in SHARING:
        raise StoryError("Choose a lantern, blanket, or teacup to share.")
    if params.hero == params.friend:
        raise StoryError("The two bedtime friends need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", n) for n in (params.hero, params.friend)):
        raise StoryError("Names must be simple capitalized names, such as Nora and Pip.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    world.entities["moon"] = Entity(
        "moon",
        MOONS[params.moon],
        "light",
        "window",
        meters={"brightness": 1.0, "rise": 0.0},
        memes={"calm": 1.0},
    )
    world.entities["object"] = Entity(
        "object",
        SHARING[params.sharing],
        "shared_item",
        "bed",
        meters={"warmth": 1.0, "shared": 0.0, "ready": 0.0},
        memes={"comfort": 1.0},
    )
    world.entities["nose"] = Entity(
        "nose",
        "a tiny nose-shaped mark",
        "clue",
        "window",
        meters={"pointing": 1.0, "noticed": 0.0},
        memes={"curiosity": 1.0},
    )
    world.entities["dawn"] = Entity(
        "dawn",
        "morning",
        "future_event",
        "beyond_window",
        meters={"near": 0.0, "expected": 1.0},
        memes={"hope": 1.0},
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.entities["hero"].label
    friend = world.entities["friend"].label
    moon = world.entities["moon"].label
    shared = world.entities["object"].label

    world.narrate(
        "beginning",
        f"At bedtime, {hero} and {friend} curled up beside the window. "
        f"The {moon} laid a pale stripe across the bed, and their {shared} rested between them.",
    )
    world.say("hero", f"May we share it until the moon goes to sleep?")
    world.say("friend", "Yes, but I want one turn before I close my eyes.")
    world.say("hero", "Then we can make a quiet plan.")
    world.say("friend", "A quiet plan sounds just right.")

    world.entities["nose"].meters["noticed"] = 1.0
    world.entities["friend"].beliefs["clue"] = (
        "the nose-shaped mark points toward a loose window latch"
    )
    world.narrate(
        "clue",
        f"Before the curtains closed, {friend} noticed a tiny mark on the glass. "
        f"It looked like a nose pointing toward the window latch.",
        question="What did the children notice before settling down?",
        cause="A tiny nose-shaped mark pointed toward the window latch.",
        result="They knew the window might need checking before morning.",
    )
    world.say(
        "friend",
        "Look, the little nose points at the latch. I think the wind may visit later.",
        to="hero",
        reveal="clue",
    )
    world.say("hero", "Should we tell an adult before we fall asleep?")
    world.say("friend", "Yes. Sharing a worry makes it smaller and safer.")
    world.say("hero", "I will call Dad, and you can keep the blanket warm.")
    world.say("friend", "I will keep half of it for you.")

    world.entities["dawn"].meters["near"] = 1.0
    world.narrate(
        "foreshadowing",
        "Far beyond the dark garden, morning was already walking softly toward the house. "
        "A cool breeze brushed the curtains, as if practicing its first hello.",
        question="Why did they check the window before sleeping?",
        cause="The nose-shaped mark warned them that a breeze might come through the loose latch.",
        result="They prepared early instead of waiting for the cold wind to wake them.",
    )
    world.say("hero", "When morning comes, the sun will find us ready.")
    world.say("friend", "And if the wind knocks, we will hear it together.")

    world.entities["object"].meters["shared"] = 1.0
    world.entities["object"].meters["ready"] = 1.0
    world.narrate(
        "sharing",
        f"{hero} tucked one edge of the {shared} around {friend}'s shoulders, "
        f"and {friend} tucked the other edge around {hero}.",
        question="How did the children share their bedtime comfort?",
        cause=f"They wanted both friends to be warm while they waited for help with the latch.",
        result=f"They wrapped the {shared} around both of them instead of keeping it for one child.",
    )
    world.say("friend", "Your side is warm now.")
    world.say("hero", "So is yours. That makes two warm sides.")
    world.say("friend", "The best blankets are bigger when shared.")
    world.say("hero", "And the best plans are shared too.")

    world.entities["moon"].meters["rise"] = 1.0
    world.entities["moon"].meters["brightness"] = 0.7
    world.narrate(
        "resolution",
        f"Dad gently fastened the latch. The {moon} climbed higher, "
        f"and the nose-shaped mark became only a small smile in the glass.",
        question="What changed before the children went to sleep?",
        cause="An adult secured the latch after the children shared the warning.",
        result="The breeze could no longer slip in, so both children rested safely.",
    )
    world.say("friend", "The nose is smiling now.")
    world.say("hero", "It knows we listened.")
    world.say("friend", "Good night, sharing friend.")
    world.say("hero", "Good night. Wake me when the sun is ready.")

    world.share()
    world.narrate(
        "ending",
        f"Under one shared cover, {hero} and {friend} drifted to sleep. "
        f"Outside, the moon kept watch, while the tiny nose on the window pointed toward the quiet morning.",
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
                "Why is sharing helpful at bedtime?",
                "Sharing can keep friends comfortable and lets them solve a worry together.",
            ),
            QAItem(
                "What did the nose-shaped mark foreshadow?",
                "It foreshadowed that a breeze might come through the loose window latch.",
            ),
        ],
        world=world,
    )
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    if world.entities["object"].meters["shared"] != 1.0:
        raise StoryError("The bedtime object must truly be shared.")
    if world.entities["object"].meters["ready"] != 1.0:
        raise StoryError("The shared comfort must be ready before sleep.")
    if world.entities["nose"].meters["noticed"] != 1.0:
        raise StoryError("The nose clue must be noticed.")
    if world.entities["dawn"].meters["near"] != 1.0:
        raise StoryError("The foreshadowed morning must affect the ending.")
    speeches = [e for e in world.history if e.kind == "speech"]
    if len(speeches) < 12:
        raise StoryError("The bedtime story needs a sustained back-and-forth exchange.")
    if any(sum(e.speaker == key for e in speeches) < 5 for key in ("hero", "friend")):
        raise StoryError("Both friends need several spoken turns.")
    if not any(e.revealed == "clue" for e in speeches):
        raise StoryError("The useful clue must pass from one child to the other.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs grounded questions and causal answers.")
    if any(word in sample.story.lower() for word in ("meters=", "memes=", "entity(", "{", "}")):
        raise StoryError("Internal world terms leaked into the bedtime story.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--moon", choices=tuple(MOONS))
    parser.add_argument("--sharing", choices=tuple(SHARING))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    friend_choices = [name for name in NAMES if name != hero]
    friend = args.friend or rng.choice(friend_choices)
    params = StoryParams(
        hero=hero,
        friend=friend,
        moon=args.moon or rng.choice(tuple(MOONS)),
        sharing=args.sharing or rng.choice(tuple(SHARING)),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if asp_options() != {("lantern",), ("blanket",), ("teacup",)}:
        raise StoryError("Python and ASP disagree about shareable bedtime objects.")
    count = 0
    for moon in MOONS:
        for sharing in SHARING:
            sample = generate(
                StoryParams(
                    hero="Nora",
                    friend="Pip",
                    moon=moon,
                    sharing=sharing,
                )
            )
            check_sample(sample)
            count += 1
    print(f"OK: {count} bedtime states; ASP/Python sharing options agree.")


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
            print(json.dumps(sorted(asp_options())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            params_list = []
            for moon in MOONS:
                for sharing in SHARING:
                    params_list.append(
                        StoryParams(
                            hero=args.hero or "Nora",
                            friend=args.friend or "Pip",
                            moon=moon,
                            sharing=sharing,
                            seed=args.seed,
                        )
                    )
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
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
