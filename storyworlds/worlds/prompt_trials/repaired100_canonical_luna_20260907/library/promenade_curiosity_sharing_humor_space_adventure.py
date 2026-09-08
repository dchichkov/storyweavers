#!/usr/bin/env python3
"""A curious space promenade becomes brighter when Luna shares a joke and a clue."""

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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
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
    friend: str = "Pip"
    destination: str = "the glass comet garden"
    object_name: str = "a blinking star shell"
    seed: int = 777


NAMES = ("Luna", "Milo", "Nova", "Pip", "Zara", "Sol")
DESTINATIONS = {
    "garden": ("the glass comet garden", "a blinking star shell", "a tiny green comet"),
    "observatory": ("the moon observatory", "a silver signal coin", "a sleepy moon"),
    "dock": ("the cloudship promenade", "a feather-light compass", "a purple planet"),
}
PROMPT = (
    "Write a dialogue-rich children's Space Adventure about curiosity, sharing, "
    "and humor on a promenade."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, "character", "promenade",
                           memes={"curiosity": 1.0, "sharing": 0.2, "humor": 0.4}),
            "friend": Entity("friend", params.friend, "character", "promenade",
                             memes={"curiosity": 0.7, "sharing": 0.4, "humor": 0.8}),
            "promenade": Entity("promenade", "the Starway Promenade", "place",
                                "orbit", meters={"lights": 1, "safe": 1}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question: str = "",
                cause: str = "", result: str = "") -> None:
        self.history.append(Event(kind, text, question, cause, result, self.snapshot()))

    def say(self, speaker: str, text: str) -> None:
        label = self.entities[speaker].label
        verb = "asked" if text.endswith("?") else "said"
        self.history.append(Event("speech", f'"{text}" {label} {verb}.',
                                  state=self.snapshot()))

    def share(self, giver: str, receiver: str, fact: str) -> None:
        self.entities[giver].memes["sharing"] = 1.0
        self.entities[receiver].memes["curiosity"] = 1.0
        self.narrate("sharing", f"{self.entities[giver].label} shared {fact}.")


def validate_params(params: StoryParams) -> None:
    if params.hero == params.friend:
        raise StoryError("The two space travelers need different names.")
    for name in (params.hero, params.friend):
        if not re.fullmatch(r"[A-Z][a-z]+", name):
            raise StoryError("Names must be simple capitalized words, such as Luna.")
    if not params.destination or not params.object_name:
        raise StoryError("The promenade adventure needs a destination and an object.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    world.entities["mystery"] = Entity(
        "mystery", params.object_name, "artifact", "promenade",
        meters={"glow": 0, "shared": 0}, memes={"wonder": 1.0},
    )
    world.entities["destination"] = Entity(
        "destination", params.destination, "place", "promenade",
        meters={"reached": 0},
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.entities["hero"].label
    friend = world.entities["friend"].label
    item = params.object_name
    destination = params.destination

    world.narrate(
        "beginning",
        f"{hero} and {friend} floated along the Starway Promenade, where silver lamps "
        f"made a bright path toward {destination}.",
    )
    world.say("hero", f"Do you see that blinking light beside the railing?")
    world.say("friend", "I see it. It might be a lost space crumb.")
    world.narrate(
        "mystery",
        f"Behind a row of moon-shaped benches, they found {item}. It blinked once, "
        "then hid its glow.",
        question="What made the travelers stop on the promenade?",
        cause=f"They noticed {item} blinking beside the promenade railing.",
        result="Their curiosity led them behind the moon-shaped benches.",
    )
    world.say("hero", "Maybe it is a message from a tiny explorer.")
    world.say("friend", "Or maybe it is a snack for a very small rocket.")
    world.entities["friend"].memes["humor"] = 1.0
    world.narrate(
        "humor",
        f"{friend}'s silly guess made {hero} laugh, but {item} stayed dark.",
        question="How did humor help during the search?",
        cause=f"{friend} joked that the object could be a snack for a tiny rocket.",
        result=f"The joke made {hero} laugh and helped the friends stay calm and curious.",
    )
    world.say("hero", "What if it glows when someone tells the truth about it?")
    world.say("friend", "Then I will share my best clue. I saw three blue sparks near the fountain.")
    world.share("friend", "hero", "the clue about three blue sparks near the fountain")
    world.say("hero", "I saw three sparks too! Let's follow them together.")
    world.entities["mystery"].location = "fountain"
    world.entities["mystery"].meters["glow"] = 1
    world.narrate(
        "clue",
        f"They followed three blue sparks across the promenade to the fountain. "
        f"When {hero} and {friend} shared what they had seen, {item} began to glow.",
        question="What caused the object to glow?",
        cause=f"The friends shared their matching clues about three blue sparks.",
        result=f"{item} lit up and pointed toward {destination}.",
    )
    world.say("friend", "It is showing us the way!")
    world.say("hero", "Then we should share the discovery with everyone.")
    world.entities["mystery"].meters["shared"] = 1
    world.entities["destination"].meters["reached"] = 1
    world.narrate(
        "resolution",
        f"The glowing object guided them along the promenade to {destination}. "
        f"They invited the passing travelers to see it, and its light painted tiny "
        "smiles across the station windows.",
        question="How did the travelers solve the promenade mystery?",
        cause=f"They combined and shared their clues instead of keeping them secret.",
        result=f"The object glowed, guided them to {destination}, and became a discovery for everyone.",
    )
    world.say("hero", "Curiosity found the path, sharing found the answer.")
    world.say("friend", "And my rocket snack saved the mission from being too serious.")
    world.entities["hero"].memes["sharing"] = 1.0
    world.entities["friend"].memes["sharing"] = 1.0
    world.narrate(
        "ending",
        f"Under the promenade's silver lamps, {hero} and {friend} laughed while "
        f"{item} blinked hello to every new explorer.",
        question="What did the friends learn on their space adventure?",
        cause="They stayed curious, shared clues, and used humor when the mystery felt uncertain.",
        result="Their teamwork turned a blinking object into a joyful discovery for the whole station.",
    )
    sample = StorySample(
        params=params,
        story="\n\n".join(event.text for event in world.history),
        prompts=[PROMPT],
        story_qa=[
            QAItem(event.question, f"{event.cause} {event.result}")
            for event in world.history if event.question
        ],
        world_qa=[
            QAItem(
                "Why is sharing useful during an adventure?",
                "Sharing clues lets friends combine what each person noticed and make a better decision together.",
            ),
            QAItem(
                "What does curiosity encourage a traveler to do?",
                "Curiosity encourages a traveler to look closely, ask questions, and investigate something unknown.",
            ),
        ],
        world=world,
    )
    check_sample(sample)
    return sample


def check_sample(sample: StorySample) -> None:
    world = sample.world
    if world.entities["mystery"].meters["glow"] != 1:
        raise StoryError("The mystery must glow after the clues are shared.")
    if world.entities["mystery"].meters["shared"] != 1:
        raise StoryError("The discovery must be shared.")
    if world.entities["destination"].meters["reached"] != 1:
        raise StoryError("The travelers must reach the destination.")
    speech = [event for event in world.history if event.kind == "speech"]
    if len(speech) < 10:
        raise StoryError("The story needs a sustained back-and-forth conversation.")
    if len(sample.story_qa) < 4:
        raise StoryError("The story needs several causal questions and answers.")
    if any(not item.answer.strip() for item in sample.story_qa):
        raise StoryError("Every story question needs a full answer.")


ASP_RULES = """
glows(Object) :- found(Object), shared_clue(Object).
reaches(Destination) :- glows(Object), points_to(Object, Destination).
shared_clue(Object) :- clue(Object), travelers_share.
#show glows/1.
#show reaches/1.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join([
        fact("found", "mystery"),
        fact("clue", "mystery"),
        fact("travelers_share"),
        fact("points_to", "mystery", "destination"),
    ])


def asp_state() -> set[tuple[str, tuple]]:
    from asp import atoms, one_model
    model = one_model(asp_facts() + "\n" + ASP_RULES)
    return {
        ("glows", args) for args in atoms(model, "glows")
    } | {
        ("reaches", args) for args in atoms(model, "reaches")
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--destination", choices=tuple(value[0] for value in DESTINATIONS.values()))
    parser.add_argument("--object-name")
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice([name for name in NAMES if name != hero])
    destination, item, _ = rng.choice(tuple(DESTINATIONS.values()))
    params = StoryParams(
        hero=hero,
        friend=friend,
        destination=args.destination or destination,
        object_name=args.object_name or item,
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify() -> None:
    if ("glows", ("mystery",)) not in asp_state():
        raise StoryError("ASP did not derive the glowing mystery.")
    if ("reaches", ("destination",)) not in asp_state():
        raise StoryError("ASP did not derive the reached destination.")
    tested = 0
    for destination, item, _ in DESTINATIONS.values():
        sample = generate(StoryParams(destination=destination, object_name=item))
        check_sample(sample)
        tested += 1
    print(f"OK: {tested} story states; Python and ASP agree on the adventure turn.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
            print(json.dumps(sorted((name, list(arguments)) for name, arguments in asp_state())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            params_list = []
            for destination, item, _ in DESTINATIONS.values():
                params_list.append(StoryParams(
                    hero=args.hero or "Luna",
                    friend=args.friend or "Pip",
                    destination=destination,
                    object_name=item,
                    seed=args.seed,
                ))
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
                             ensure_ascii=False, indent=2))
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
