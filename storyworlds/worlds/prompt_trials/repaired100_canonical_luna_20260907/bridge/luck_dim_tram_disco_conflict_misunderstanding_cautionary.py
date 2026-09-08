#!/usr/bin/env python3
"""A luck-dim tram and a disco bell teach a cautious folk-tale lesson."""

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
    friend: str = "Pip"
    trouble: str = "dim"
    choice: str = "inspect"
    cargo: str = "lanterns"
    seed: int = 777


NAMES = ("Luna", "Pip", "Mara", "Tobin", "Nell", "Oren")
TROUBLES = {"dim": "dim"}
CHOICES = ("inspect", "rush")
CARGO = {
    "lanterns": "a basket of moon lanterns",
    "bells": "a basket of silver bells",
    "ribbons": "a basket of bright ribbons",
}
PROMPT = (
    "Write a folk-tale children's story about Luna, a tram, a disco, "
    "a luck-dim lamp, a misunderstanding, and a cautious choice."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, "character", memes={"caution": 0.4, "trust": 0.5}),
            "friend": Entity("friend", params.friend, "character", memes={"caution": 0.5, "trust": 0.5}),
            "tram": Entity("tram", "the little tram", "vehicle", "hill_track",
                           meters={"speed": 0, "safe": 1, "arrived": 0}),
            "lamp": Entity("lamp", "the luck-dim lamp", "tool", "tram_front",
                           meters={"brightness": 1, "checked": 0, "lit": 0}),
            "cargo": Entity("cargo", CARGO[params.cargo], "cargo", "tram",
                            meters={"loaded": 1, "delivered": 0}),
            "disco": Entity("disco", "the village disco", "place", "hilltop",
                            meters={"open": 0, "music": 0}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question="", cause="", result=""):
        self.history.append(Event(kind, text, question=question, cause=cause,
                                  result=result, state=self.snapshot()))

    def say(self, speaker: str, text: str, *, listener: str = ""):
        label = self.entities[speaker].label
        verb = "asked" if text.endswith("?") else "said"
        self.history.append(Event("speech", f'"{text}" {label} {verb}.',
                                  speaker=speaker, listener=listener,
                                  state=self.snapshot()))

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
                QAItem("What does the luck-dim lamp do?",
                       "It grows dim when the tram's safe route has not been checked."),
                QAItem("Why must the tram slow down?",
                       "A careful check protects the cargo and the people waiting at the disco."),
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.trouble not in TROUBLES:
        raise StoryError("The tram story needs the dim-lamp trouble.")
    if params.choice not in CHOICES:
        raise StoryError("Choose inspect or rush.")
    if params.cargo not in CARGO:
        raise StoryError("Choose a known cargo.")
    if params.hero == params.friend:
        raise StoryError("The two travelers need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", n) for n in (params.hero, params.friend)):
        raise StoryError("Names must be simple capitalized names.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def inspect_route(world: World):
    lamp = world.entities["lamp"]
    tram = world.entities["tram"]
    lamp.meters["checked"] = 1
    lamp.meters["brightness"] = 2
    tram.meters["safe"] = 1
    world.entities["hero"].beliefs["meaning"] = "The lamp is warning us to check the bend."


def move_tram(world: World) -> bool:
    tram = world.entities["tram"]
    tram.meters["speed"] += 1
    lamp = world.entities["lamp"]
    if not lamp.meters["checked"]:
        tram.meters["safe"] = 0
        return False
    tram.meters["speed"] = 1
    tram.location = "disco"
    tram.meters["arrived"] = 1
    world.entities["cargo"].location = "disco"
    world.entities["cargo"].meters["delivered"] = 1
    world.entities["disco"].meters.update(open=1, music=1)
    return True


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    h, f = params.hero, params.friend
    cargo = CARGO[params.cargo]

    world.narrate(
        "beginning",
        f"In the village below the hill, {h} and {f} loaded {cargo} onto the little tram. "
        "They were meant to carry it to the disco before the first fiddle played.",
    )
    world.say("hero", "Is the tram ready for the hill?")
    world.say("friend", "The luck-dim lamp is glowing faintly, so I think it is ready.")
    world.say("hero", "Faint light sounds like a warning to me.")

    if params.choice == "rush":
        world.say("friend", "The dancers are waiting. We should hurry.")
        world.say("hero", "Then hold the basket tight.")
        world.narrate(
            "misunderstanding",
            f"{f} mistook the luck-dim lamp for a lucky sign. {h} mistook {f}'s hurry for carelessness, "
            "and the two friends pushed the tram toward the steep bend.",
            question="What misunderstanding sent the tram toward danger?",
            cause="Pip thought the dim lamp promised good luck, while Luna heard the hurry as a wish to ignore danger.",
            result="They began moving before checking the track.",
        )
        if move_tram(world):
            raise StoryError("An unchecked tram cannot safely reach the disco.")
        world.narrate(
            "conflict",
            "At the bend, the tram's wheels squeaked and stopped. The basket tipped, but Luna caught it.",
        )
        world.say("hero", "The lamp was warning us, not blessing us.")
        world.say("friend", "I heard what I hoped it meant. I am sorry.")
        world.say("hero", "Let us ask the track before we ask the dancers to trust us.")
    else:
        world.say("hero", "Let us check the bend before we roll.")
        world.say("friend", "I thought the dim lamp meant luck, but I will look with you.")
        world.narrate(
            "misunderstanding",
            f"{f} had mistaken the dim lamp for a lucky glow. {h} explained that its weak light "
            "meant the tram's path needed care, not celebration.",
            question="What did the friends learn about the dim lamp?",
            cause="The faint lamp was a warning that the route had not been checked.",
            result="They stopped arguing and examined the bend together.",
        )

    inspect_route(world)
    world.narrate(
        "turn",
        f"They found a loose pebble beside the rail and a twig across the switch. "
        f"{h} lifted the twig while {f} swept away the pebble.",
        question="How did they make the route safe?",
        cause="A twig blocked the switch and a pebble could jolt the wheels.",
        result="They cleared both obstacles and checked the bend before moving.",
    )
    world.say("friend", "Now the lamp is bright.")
    world.say("hero", "And now we know why.")
    world.say("friend", "Shall we take the hill slowly?")
    world.say("hero", "Slowly, and with both hands near the basket.")

    if not move_tram(world):
        raise StoryError("The checked route should let the tram travel.")
    world.narrate(
        "arrival",
        f"The tram crept around the bend and reached the disco. {f} carried {cargo} inside "
        f"while {h} rang the little arrival bell.",
        question="Why did they travel slowly after the repair?",
        cause="They wanted to protect the cargo on the hill bend.",
        result="The tram reached the disco without spilling anything.",
    )
    world.say("friend", "The disco can begin!")
    world.say("hero", "First the cargo, then the dancing.")
    world.narrate(
        "ending",
        "The music began, and the luck-dim lamp shone warmly above the quiet tram. "
        "From that night on, the villagers called it lucky only after someone had checked what it was saying.",
    )
    world.entities["hero"].memes.update(caution=1.0, trust=1.0)
    world.entities["friend"].memes.update(caution=1.0, trust=1.0)
    sample = world.sample()
    check_sample(sample)
    return sample


ASP_RULES = """
safe_choice(inspect) :- choice(inspect).
safe_choice(inspect) :- choice(rush), warning(dim).
#show safe_choice/1.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join([
        fact("warning", "dim"),
        fact("choice", "inspect"),
        fact("choice", "rush"),
    ])


def asp_safe_choices() -> set[tuple[str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + ASP_RULES), "safe_choice"))


def check_sample(sample: StorySample):
    world = sample.world
    if not world.entities["tram"].meters["arrived"]:
        raise StoryError("The tram must arrive at the disco.")
    if not world.entities["cargo"].meters["delivered"]:
        raise StoryError("The cargo must be delivered.")
    if not world.entities["lamp"].meters["checked"]:
        raise StoryError("The lamp warning must be investigated.")
    if len([e for e in world.history if e.kind == "speech"]) < 10:
        raise StoryError("The story needs a sustained back-and-forth exchange.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs causal grounded questions.")
    if any(world.entities[k].memes["trust"] < 1 for k in ("hero", "friend")):
        raise StoryError("The friends must reconcile.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--trouble", choices=tuple(TROUBLES))
    parser.add_argument("--choice", choices=CHOICES)
    parser.add_argument("--cargo", choices=tuple(CARGO))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != hero])
    params = StoryParams(
        hero=hero,
        friend=friend,
        trouble=args.trouble or "dim",
        choice=args.choice or rng.choice(CHOICES),
        cargo=args.cargo or rng.choice(tuple(CARGO)),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if asp_safe_choices() != {("inspect",)}:
        raise StoryError("ASP and Python disagree about the safe choice.")
    tested = 0
    for choice in CHOICES:
        for cargo in CARGO:
            sample = generate(StoryParams(choice=choice, cargo=cargo))
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} story states; ASP marks inspect as the safe choice.")


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({
            "entities": sample.world.snapshot(),
            "history": [asdict(e) for e in sample.world.history],
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
            print(json.dumps(sorted(asp_safe_choices())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            params_list = [
                StoryParams(
                    hero=args.hero or "Luna",
                    friend=args.friend or "Pip",
                    trouble="dim",
                    choice=choice,
                    cargo=cargo,
                    seed=args.seed,
                )
                for choice in CHOICES
                for cargo in CARGO
            ]
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
                             ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(sample, trace=args.trace, qa=args.qa,
                     header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
