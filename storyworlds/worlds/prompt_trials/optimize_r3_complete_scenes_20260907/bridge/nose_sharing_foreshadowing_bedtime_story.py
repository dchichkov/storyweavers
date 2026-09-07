#!/usr/bin/env python3
"""A quiet bedtime story about sharing a nose-shaped treasure and noticing a promise."""

from __future__ import annotations

import argparse
import json
import random
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
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    state: dict = field(default_factory=dict)
    question: str = ""
    cause: str = ""
    result: str = ""


@dataclass
class StoryParams:
    child: str = "Mira"
    companion: str = "Owen"
    path: str = "lantern"
    phrase: str = "nose"
    seed: int = 777


NAMES = ("Mira", "Owen", "Lina", "Tomas", "Nia", "Pip")
PATHS = ("lantern", "button", "dream")
PROMPT = "Write a gentle bedtime story about two children sharing a small nose-shaped keepsake and learning to notice a promise."
PATH_DATA = {
    "lantern": {
        "trouble": "the night lantern had gone dark",
        "clue": "a tiny nose-shaped pebble caught the last warm glimmer",
        "decision": "to share the pebble's place as a marker while they searched together",
        "resolution": "they found the lantern's loose wick and lit it beside the window",
        "ending": "The pebble rested under the glowing lantern, where both children could see its little nose.",
    },
    "button": {
        "trouble": "a red coat button had slipped beneath the bed",
        "clue": "the nose-shaped pebble had rolled toward the same shadow",
        "decision": "to take turns feeling along the floor instead of pulling the bed apart",
        "resolution": "they found the button in a fold of the blanket",
        "ending": "The button shone on the coat, and the pebble waited in its dish like a tiny sleeping nose.",
    },
    "dream": {
        "trouble": "the younger child feared a dream about a giant nose",
        "clue": "the shared pebble felt smooth and warm in the moonlight",
        "decision": "to pass it between them and tell one true, kind thing before sleep",
        "resolution": "the frightening dream softened into a walk beneath friendly stars",
        "ending": "The pebble lay between their pillows, and the room grew quiet enough for kind dreams.",
    },
}


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "child": Entity("child", params.child, "character", "room",
                            memes={"worry": 0.3, "trust": 0.5}),
            "companion": Entity("companion", params.companion, "character", "room",
                                memes={"worry": 0.2, "trust": 0.5}),
            "pebble": Entity("pebble", "the nose-shaped pebble", "keepsake", "shelf",
                             meters={"shared": 0, "found": 1}),
            "problem": Entity("problem", PATH_DATA[params.path]["trouble"], "trouble", "room",
                               meters={"solved": 0}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def scene(self, kind: str, text: str, *, question: str = "", cause: str = "", result: str = ""):
        self.history.append(Event(kind, text, self.snapshot(), question, cause, result))

    def share(self):
        pebble = self.entities["pebble"]
        pebble.meters["shared"] += 1
        self.entities["child"].memes["trust"] = 1.0
        self.entities["companion"].memes["trust"] = 1.0

    def solve(self):
        self.entities["problem"].meters["solved"] = 1
        self.entities["child"].memes["worry"] = 0.0
        self.entities["companion"].memes["worry"] = 0.0


def validate_params(params: StoryParams):
    if params.path not in PATHS:
        raise StoryError("Choose one of the supported bedtime paths.")
    if params.child == params.companion:
        raise StoryError("The two characters need different names.")
    if not params.phrase.strip():
        raise StoryError("The story must keep its nose-shaped keepsake.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    child, companion = params.child, params.companion
    data = PATH_DATA[params.path]
    rng = random.Random(params.seed)
    opening = rng.choice((
        f"At bedtime, {child} and {companion} placed a small nose-shaped pebble on the shelf.",
        f"The moon was climbing the window when {child} showed {companion} a little pebble shaped like a nose.",
    ))
    world.scene("beginning", opening + " They had promised to share it until morning.")
    world.scene("foreshadowing",
                f'"Keep it where we can both find it," said {child}. '
                f'"It may help us remember our promise," {companion} replied.')
    world.scene("trouble",
                f"Then {data['trouble']}. The cozy room suddenly felt less certain.",
                question="What trouble began at bedtime?",
                cause=f"{data['trouble'].capitalize()} before the children were ready to sleep.",
                result="They paused instead of pretending that everything was fine.")

    if params.path == "lantern":
        world.scene("discovery",
                    f"{companion} lifted the pebble. {data['clue'].capitalize()}.",
                    question="What did the children learn from the pebble?",
                    cause="Its faint glimmer showed them where to look first.",
                    result="They searched near the window rather than wandering through the dark.")
        world.scene("choice",
                    f'"I can hold it," said {child}. "You can check the lantern." '
                    f'{companion} nodded, and they {data["decision"]}.')
        world.scene("resolution",
                    f"{data['resolution'].capitalize()}. {child} held the pebble near the sill while {companion} tightened the wick.")
    elif params.path == "button":
        world.scene("discovery",
                    f"{child} remembered that {data['clue']}.",
                    question="What clue changed their search?",
                    cause="The pebble had rolled toward the same shadow as the missing button.",
                    result="They realized the button might be nearby.")
        world.scene("choice",
                    f'"Let us share the searching," said {companion}. '
                    f'"You take the left side, and I will take the right." '
                    f"They chose {data['decision']}.")
        world.scene("resolution",
                    f"{data['resolution'].capitalize()} {child} laughed softly, and {companion} sewed it back before the room grew cold.")
    else:
        world.scene("discovery",
                    f"{companion} held the pebble and whispered that {data['clue']}.",
                    question="What helped the frightened child?",
                    cause="The smooth pebble gave the children a calm thing to feel in the moonlight.",
                    result="They remembered that they could share comfort instead of facing the dream alone.")
        world.scene("choice",
                    f'"Tell me something true," said {child}. '
                    f'"You are safe, and I am here," answered {companion}. '
                    f"Together they decided {data['decision']}.")
        world.scene("resolution",
                    f"{data['resolution'].capitalize()} {child} smiled when the stars in the dream blinked like tiny lamps.")

    world.share()
    world.solve()
    world.scene("ending", data["ending"],
                question="How did sharing change the bedtime?",
                cause="The children listened to the clue and shared the keepsake and the work.",
                result=data["resolution"].capitalize() + " The children could rest together.")
    sample = StorySample(
        params=params,
        story="\n\n".join(event.text for event in world.history),
        prompts=[PROMPT],
        story_qa=[
            QAItem(event.question, f"{event.cause} {event.result}")
            for event in world.history if event.question
        ],
        world_qa=[
            QAItem("What did the children share?", "They shared a small nose-shaped pebble and the care needed to solve the bedtime trouble.")
        ],
        world=world,
    )
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    if world.entities["problem"].meters["solved"] != 1:
        raise StoryError("The bedtime trouble was not resolved.")
    if world.entities["pebble"].meters["shared"] < 1:
        raise StoryError("The keepsake must be shared.")
    if not sample.story.endswith("."):
        raise StoryError("The story needs a finished ending.")
    if len(sample.story_qa) < 2:
        raise StoryError("Each story needs grounded questions and answers.")
    if not all(name in sample.story for name in (sample.params.child, sample.params.companion)):
        raise StoryError("Both selected characters must appear in the story.")


ASP_RULES = """
path(lantern). path(button). path(dream).
valid(P) :- path(P).
#show valid/1.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join(fact("path", path) for path in PATHS)


def asp_paths() -> set[str]:
    from asp import atoms, one_model
    return {row[0] for row in atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid")}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--child")
    parser.add_argument("--companion")
    parser.add_argument("--path", choices=PATHS)
    parser.add_argument("--phrase", default="nose")
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child or rng.choice(NAMES)
    companion = args.companion or rng.choice(tuple(name for name in NAMES if name != child))
    return StoryParams(child=child, companion=companion, path=args.path or rng.choice(PATHS),
                       phrase=args.phrase, seed=args.seed)


def verify():
    if asp_paths() != set(PATHS):
        raise StoryError("Python and ASP disagree about bedtime paths.")
    for path in PATHS:
        check_sample(generate(StoryParams(path=path)))
    print(f"OK: {len(PATHS)} complete bedtime paths verified.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({"entities": sample.world.snapshot(),
                          "history": [asdict(event) for event in sample.world.history]},
                         indent=2))


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
            params_list = [
                StoryParams(child=args.child or "Mira", companion=args.companion or "Owen",
                            path=path, phrase=args.phrase, seed=args.seed + index)
                for index, path in enumerate(PATHS)
                if args.path is None or args.path == path
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
