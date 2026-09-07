#!/usr/bin/env python3
"""The Nose-Warming Scarf: a small bedtime tale about sharing and noticing clues."""

from __future__ import annotations

import argparse
import json
import random
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


@dataclass
class StoryParams:
    child: str = "Nora"
    fox: str = "Pip"
    weather: str = "frost"
    scarf: str = "red"
    seed: int = 777


NAMES = ("Nora", "Milo", "Lina", "Tess", "Owen", "Ivy")
FOXES = ("Pip", "Fenn", "Rufus", "Clover")
WEATHERS = {
    "frost": ("frosty", "cold"),
    "snow": ("snowy", "white"),
    "wind": ("windy", "whistling"),
}
SCARVES = {
    "red": "red",
    "gold": "golden",
    "blue": "blue",
}

PROMPT = (
    "Write a gentle bedtime story in which a child notices clues about a cold night, "
    "shares a scarf with a fox, and discovers why sharing mattered."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        weather_word, cold_word = WEATHERS[params.weather]
        self.entities = {
            "child": Entity(
                "child",
                params.child,
                "character",
                "cottage",
                meters={"warmth": 0.7},
                memes={"kindness": 0.6, "curiosity": 0.7},
            ),
            "fox": Entity(
                "fox",
                params.fox,
                "character",
                "pine_path",
                meters={"warmth": 0.25},
                memes={"trust": 0.3, "hope": 0.4},
            ),
            "scarf": Entity(
                "scarf",
                f"{SCARVES[params.scarf]} scarf",
                "clothing",
                "cottage",
                meters={"length": 2.0, "shared_length": 0.0},
                memes={"comfort": 0.0},
            ),
            "night": Entity(
                "night",
                f"the {weather_word} night",
                "weather",
                "hill",
                meters={"temperature": -2.0 if params.weather == "frost" else -1.0},
            ),
        }
        self.history: list[Event] = []
        self.knowledge: set[str] = set()

    def narrate(self, text: str, *, kind="narration", question="", cause="", result=""):
        self.history.append(Event(kind, text, question, cause, result))

    def say(self, speaker: str, text: str):
        label = self.entities[speaker].label
        verb = "asked" if text.endswith("?") else "said"
        self.history.append(Event("speech", f'"{text}" {label} {verb}.'))

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}


def validate_params(params: StoryParams):
    if params.child == params.fox:
        raise StoryError("The child and fox need different names.")
    if params.child not in NAMES or params.fox not in FOXES:
        raise StoryError("Choose a name from the story's name lists.")
    if params.weather not in WEATHERS or params.scarf not in SCARVES:
        raise StoryError("Unknown weather or scarf color.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    child = world.entities["child"].label
    fox = world.entities["fox"].label
    scarf = world.entities["scarf"].label
    weather_word, cold_word = WEATHERS[params.weather]

    world.narrate(
        f"At bedtime, {child} carried a {scarf} to the little window. "
        f"Outside, the {weather_word} night covered the garden in silver."
    )
    world.say("child", "Good night, garden.")
    world.say("fox", "Good night, little window.")
    world.narrate(
        f"{child} heard a soft sneeze beyond the gate. Then came another sound: "
        f"the quiet tap of paws, and a tiny nose pressed against the cold glass."
    )
    world.knowledge.update({"fox_is_cold", "fox_is_waiting"})
    world.narrate(
        f"The clues made {child} look carefully. {fox} was shivering, and its nose "
        f"had turned pink in the {cold_word} air.",
        kind="clue",
        question="What clues told the child that the fox needed help?",
        cause=f"{fox} sneezed, tapped at the gate, and pressed its cold nose to the window.",
        result=f"{child} understood that the fox was waiting in the cold.",
    )
    world.say("child", "Are you cold, little friend?")
    world.say("fox", "My paws are cold, and my nose is colder.")
    world.say("child", "I have one warm scarf. We can share it.")
    world.say("fox", "Will there be enough for both of us?")
    world.say("child", "There will be enough if we sit close.")

    world.entities["scarf"].location = "garden_gate"
    world.entities["scarf"].meters["shared_length"] = 2.0
    world.entities["scarf"].memes["comfort"] = 1.0
    world.entities["child"].meters["warmth"] = 0.9
    world.entities["fox"].meters["warmth"] = 0.85
    world.entities["fox"].memes["trust"] = 1.0
    world.narrate(
        f"{child} wrapped one end of the {scarf} around {fox}'s neck and kept the "
        f"other end beneath the window. They sat close enough for the scarf to make "
        f"a bright bridge between them.",
        kind="sharing",
        question="How did the child share the scarf?",
        cause=f"{child} wrapped one end around {fox} and kept the other end nearby.",
        result="The two friends sat close together, so one scarf warmed them both.",
    )
    world.say("fox", "My nose is warm now.")
    world.say("child", "And my toes are warm because you are keeping the scarf from blowing away.")
    world.say("fox", "Then sharing warmed both of us.")

    world.narrate(
        f"Just then, the wind lifted a corner of the {scarf}. {child} remembered the "
        f"paw taps and the pink nose. The clues had warned them that the night would "
        f"grow colder, so {child} tied the scarf gently to the gate before the wind "
        f"could carry it off.",
        kind="foreshadowing",
        question="Why did the child tie the scarf to the gate?",
        cause="The wind was rising, just as the earlier cold clues had suggested the night might worsen.",
        result="The scarf stayed in place and continued warming both friends.",
    )
    world.say("child", "Tomorrow, I will bring another scarf.")
    world.say("fox", "Tomorrow, I will bring pine needles for your doorstep.")
    world.narrate(
        f"At last, {fox}'s nose stopped trembling. {child} rested a cheek against the "
        f"window, and the fox curled beneath the shared {scarf}. Above them, the first "
        f"star blinked like a small lamp left on for friends.",
        kind="ending",
        question="What changed by the end of the story?",
        cause=f"{child} noticed {fox}'s need and shared the scarf instead of keeping it alone.",
        result=f"{fox} grew warm and trusting, while {child} learned that shared comfort can return to everyone.",
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
                "Why is sharing useful on a cold night?",
                "Sharing lets two friends use one warm thing together, especially when they sit close and help one another.",
            )
        ],
        world=world,
    )
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    if world.entities["scarf"].location != "garden_gate":
        raise StoryError("The scarf must be shared at the gate.")
    if world.entities["fox"].meters["warmth"] < 0.8:
        raise StoryError("The fox must become warm by the ending.")
    if world.entities["fox"].memes["trust"] < 1.0:
        raise StoryError("The fox must trust the child after the sharing.")
    speeches = [event for event in world.history if event.kind == "speech"]
    if len(speeches) < 8:
        raise StoryError("The story needs a sustained exchange of dialogue.")
    if not any("nose" in event.text.lower() for event in world.history):
        raise StoryError("The nose must matter in the story.")
    if not any(event.kind == "foreshadowing" for event in world.history):
        raise StoryError("The story needs a later consequence for an earlier clue.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs grounded questions and answers.")


ASP_RULES = """
needs_help(F) :- cold_nose(F), waiting(F).
shared_warmth(C,F) :- has_scarf(C), needs_help(F), sits_close(C,F).
safe_scarf :- shared_warmth(C,F), ties_scarf.
#show needs_help/1.
#show shared_warmth/2.
#show safe_scarf/0.
"""


def asp_facts() -> str:
    from asp import fact

    return "\n".join(
        [
            fact("cold_nose", "fox"),
            fact("waiting", "fox"),
            fact("has_scarf", "child"),
            fact("sits_close", "child", "fox"),
            fact("ties_scarf"),
        ]
    )


def asp_state() -> set[tuple]:
    from asp import atoms, one_model

    symbols = one_model(asp_facts() + "\n" + ASP_RULES)
    result = set()
    for name in ("needs_help", "shared_warmth", "safe_scarf"):
        result.update((name,) + tuple(item) for item in atoms(symbols, name))
    return result


def python_state() -> set[tuple]:
    return {
        ("needs_help", "fox"),
        ("shared_warmth", "child", "fox"),
        ("safe_scarf",),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--child")
    parser.add_argument("--fox")
    parser.add_argument("--weather", choices=tuple(WEATHERS))
    parser.add_argument("--scarf", choices=tuple(SCARVES))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child or rng.choice(NAMES)
    fox = args.fox or rng.choice([name for name in FOXES if name != child])
    params = StoryParams(
        child=child,
        fox=fox,
        weather=args.weather or rng.choice(tuple(WEATHERS)),
        scarf=args.scarf or rng.choice(tuple(SCARVES)),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    from asp import atoms, one_model

    if asp_state() != python_state():
        raise StoryError("Python and ASP disagree about the shared-scarf state.")
    tested = 0
    for weather in WEATHERS:
        for scarf in SCARVES:
            sample = generate(
                StoryParams(
                    child="Nora",
                    fox="Pip",
                    weather=weather,
                    scarf=scarf,
                )
            )
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} story states; ASP and Python agree.")


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
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
            print(json.dumps(sorted(asp_state())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            params_list = [
                StoryParams(child=child, fox=fox, weather=weather, scarf=scarf, seed=args.seed)
                for child in (args.child,) if args.child
                for fox in (args.fox,) if args.fox
                for weather in (args.weather,) if args.weather
                for scarf in (args.scarf,) if args.scarf
            ]
            if not params_list:
                params_list = [
                    StoryParams(child="Nora", fox="Pip", weather=weather, scarf=scarf, seed=args.seed)
                    for weather in WEATHERS
                    for scarf in SCARVES
                ]
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
