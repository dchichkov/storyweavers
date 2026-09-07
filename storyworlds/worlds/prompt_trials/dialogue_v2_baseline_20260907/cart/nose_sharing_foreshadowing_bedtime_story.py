#!/usr/bin/env python3
"""The Moonlit Nose: a quiet bedtime tale about sharing and a promise kept."""

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
    child: str = "Mina"
    friend: str = "Pip"
    blanket: str = "blue"
    treat: str = "mooncake"
    approach: str = "share"
    seed: int = 777


NAMES = ("Mina", "Owen", "Lila", "Theo", "Nora", "Sam")
BLANKETS = {
    "blue": "blue blanket",
    "red": "red blanket",
    "green": "green blanket",
}
TREATS = {
    "mooncake": "mooncake",
    "biscuit": "biscuit",
    "pear": "pear",
}
APPROACHES = ("share", "wait")

PROMPT = (
    "Write a gentle bedtime story about two small friends who share a comfort "
    "item, notice a warning sign, and keep each other safe."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "child": Entity(
                "child",
                params.child,
                "character",
                "bedroom",
                memes={"calm": 0.5, "kindness": 0.5},
            ),
            "friend": Entity(
                "friend",
                params.friend,
                "character",
                "bedroom",
                memes={"calm": 0.4, "kindness": 0.5},
            ),
            "nose": Entity(
                "nose",
                "a small nose",
                "body",
                "bedroom",
                meters={"warmth": 0.0},
                memes={"comfort": 0.0},
            ),
            "window": Entity(
                "window",
                "the window",
                "place",
                "bedroom",
                meters={"open": 1.0, "wind": 1.0},
            ),
            "blanket": Entity(
                "blanket",
                f"the {params.blanket} blanket",
                "thing",
                "bed",
                meters={"size": 2.0, "warmth": 1.0},
            ),
            "treat": Entity(
                "treat",
                f"the {params.treat}",
                "thing",
                "bedside table",
                meters={"pieces": 2.0},
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
        self.narrate("speech", f"{self.entities[speaker].label} said, “{text}”")

    def share_blanket(self):
        blanket = self.entities["blanket"]
        if blanket.location != "bed":
            raise StoryError("The blanket must be on the bed before it can be shared.")
        blanket.meters["warmth"] = 2.0
        for key in ("child", "friend"):
            self.entities[key].memes["kindness"] = 1.0
            self.entities[key].memes["calm"] = 0.8

    def close_window(self):
        window = self.entities["window"]
        if window.meters["open"] != 1.0:
            raise StoryError("The window is already closed.")
        window.meters["open"] = 0.0
        window.meters["wind"] = 0.0

    def share_treat(self):
        treat = self.entities["treat"]
        if treat.meters["pieces"] != 2.0:
            raise StoryError("There must be two pieces before the treat is shared.")
        treat.meters["pieces"] = 0.0
        self.entities["child"].memes["kindness"] = 1.0
        self.entities["friend"].memes["kindness"] = 1.0

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(
                    question=event.question,
                    answer=f"{event.cause} {event.result}",
                )
                for event in self.history
                if event.question
            ],
            world_qa=[
                QAItem(
                    question="Why can sharing make bedtime feel kinder?",
                    answer="Sharing lets each friend receive comfort instead of leaving one friend without it.",
                ),
                QAItem(
                    question="What can a small warning sign do in a story?",
                    answer="A small warning sign can help characters notice trouble early and choose a safe action.",
                ),
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.blanket not in BLANKETS:
        raise StoryError("Choose a blue, red, or green blanket.")
    if params.treat not in TREATS:
        raise StoryError("Choose a mooncake, biscuit, or pear.")
    if params.approach not in APPROACHES:
        raise StoryError("Choose sharing or waiting as the bedtime approach.")
    if params.child == params.friend:
        raise StoryError("The two bedtime friends must have different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in (params.child, params.friend)):
        raise StoryError("Names must be simple capitalized names, such as Mina and Pip.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    world.entities["blanket"].location = "bed"
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    child = world.entities["child"].label
    friend = world.entities["friend"].label
    blanket = BLANKETS[params.blanket]
    treat = TREATS[params.treat]

    world.narrate(
        "beginning",
        f"At bedtime, {child} and {friend} climbed into the little bed beneath the window. "
        f"A {blanket} waited at the foot of the bed, and one {treat} rested on the bedside table.",
    )
    world.speak("child", f"That blanket is big enough for both of us.")
    world.speak("friend", "And the treat has two pieces, if we split it carefully.")
    world.narrate(
        "promise",
        f"They folded the {blanket} across their knees and placed the {treat} between them.",
        question="What did the two friends decide to share?",
        cause=f"They had one {blanket} and a two-piece {treat}.",
        result="They planned to share both the warm covering and the small snack.",
    )
    world.speak("child", "You may have the piece near the pillow.")
    world.speak("friend", "Then you may have the piece near the lamp.")
    world.share_treat()
    world.narrate(
        "sharing",
        f"They broke the {treat} into two equal pieces. The sweet crumbs made both noses wrinkle with a smile.",
    )

    if params.approach == "wait":
        world.speak("friend", "I am warm now. We can eat the treat later.")
        world.speak("child", "Perhaps we should listen to the room first.")
        world.narrate(
            "foreshadowing",
            "For a moment the room was quiet. Then the curtain lifted, and a cool thread of air brushed the end of one small nose.",
            question="What warning did the friends notice before falling asleep?",
            cause="The curtain lifted and cool air brushed a small nose.",
            result="They understood that the open window could make the bed cold.",
        )
    else:
        world.speak("child", "Wait. My nose feels cold.")
        world.speak("friend", "The curtain is moving, though the night is supposed to be still.")
        world.narrate(
            "foreshadowing",
            "The curtain lifted once more, and a cool thread of air brushed the end of one small nose.",
            question="What warning did the friends notice before falling asleep?",
            cause="A moving curtain and a cold nose showed that air was coming through the window.",
            result="They understood that the open window could make the bed cold.",
        )

    world.speak("child", "The window is open.")
    world.speak("friend", "Let us close it before the cold reaches our toes.")
    world.close_window()
    world.narrate(
        "turn",
        f"Together they padded across the rug and closed the window. The curtain settled, and the room grew quiet again.",
        question="How did the friends solve the cold draft?",
        cause="They noticed the moving curtain and the cold feeling on a nose.",
        result="They closed the open window before returning to bed.",
    )
    world.share_blanket()
    world.narrate(
        "resolution",
        f"Back under the shared {blanket}, {child} tucked one edge beneath {friend}'s shoulder. "
        f"Their noses were warm, their treat was gone, and the moon shone softly on the quiet glass.",
        question="What showed that the bedtime problem was truly solved?",
        cause=f"The window was closed and the {blanket} covered both friends.",
        result="Their noses stayed warm as they settled together beneath the moonlight.",
    )
    world.speak("friend", "Good night. If one of us notices something, both of us will listen.")
    world.speak("child", "Good night. That is what sharing a room is for.")

    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    if world.entities["window"].meters["open"] != 0.0:
        raise StoryError("The window must be closed by the ending.")
    if world.entities["blanket"].meters["warmth"] != 2.0:
        raise StoryError("The blanket must warm both friends by the ending.")
    if world.entities["treat"].meters["pieces"] != 0.0:
        raise StoryError("The shared treat must be divided and eaten.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs beginning, warning, and resolution questions.")
    speech = [event for event in world.history if event.kind == "speech"]
    if len(speech) < 8:
        raise StoryError("Both friends need a sustained bedtime conversation.")
    if not any("nose" in event.text.lower() for event in world.history):
        raise StoryError("The story must include the nose as a concrete warning sign.")
    if not any(event.kind == "foreshadowing" for event in world.history):
        raise StoryError("The story needs a clear foreshadowing event.")
    if any(not item.question.strip() or not item.answer.strip() for item in sample.story_qa):
        raise StoryError("Every grounded question needs a natural answer.")


ASP_RULES = """
safe_share :- two_pieces, shared_blanket, window_closed.
two_pieces :- treat_pieces(2).
shared_blanket :- blanket_size(2).
window_closed :- open_window(0).
#show safe_share/0.
"""


def asp_facts() -> str:
    from asp import fact

    return "\n".join(
        [
            fact("treat_pieces", 2),
            fact("blanket_size", 2),
            fact("open_window", 0),
        ]
    )


def asp_safe() -> bool:
    from asp import one_model, atoms

    model = one_model(asp_facts() + "\n" + ASP_RULES)
    return bool(atoms(model, "safe_share"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--child")
    parser.add_argument("--friend")
    parser.add_argument("--blanket", choices=tuple(BLANKETS))
    parser.add_argument("--treat", choices=tuple(TREATS))
    parser.add_argument("--approach", choices=APPROACHES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child or rng.choice(NAMES)
    friend_choices = [name for name in NAMES if name != child]
    friend = args.friend or rng.choice(friend_choices)
    params = StoryParams(
        child=child,
        friend=friend,
        blanket=args.blanket or rng.choice(tuple(BLANKETS)),
        treat=args.treat or rng.choice(tuple(TREATS)),
        approach=args.approach or rng.choice(APPROACHES),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if not asp_safe():
        raise StoryError("ASP does not recognize the safe shared bedtime state.")
    tested = 0
    for blanket in BLANKETS:
        for treat in TREATS:
            for approach in APPROACHES:
                sample = generate(
                    StoryParams(
                        blanket=blanket,
                        treat=treat,
                        approach=approach,
                    )
                )
                check_sample(sample)
                tested += 1
    print(f"OK: {tested} story states; Python and ASP agree on safe sharing.")


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
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
            print(json.dumps({"safe_share": asp_safe()}))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            samples = []
            for blanket in BLANKETS:
                for treat in TREATS:
                    for approach in APPROACHES:
                        params = StoryParams(
                            child=args.child or rng.choice(NAMES),
                            friend=args.friend or rng.choice(NAMES),
                            blanket=blanket,
                            treat=treat,
                            approach=approach,
                            seed=args.seed,
                        )
                        if params.child == params.friend:
                            params.friend = next(
                                name for name in NAMES if name != params.child
                            )
                        samples.append(generate(params))
        else:
            samples = [generate(resolve_params(args, rng)) for _ in range(args.n)]

        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(
                json.dumps(
                    payload[0] if len(payload) == 1 else payload,
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
                    header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
