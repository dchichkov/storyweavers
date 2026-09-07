#!/usr/bin/env python3
"""Gingham Magic Nursery Rhyme: three tiny magical troubles find concrete cures."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
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
    speaker: str = ""
    listener: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Nell"
    friend: str = "Pip"
    path: str = "moon"
    seed: int = 777


NAMES = ("Nell", "Pip", "Tansy", "Bram", "Mabel", "Ollie")
PATHS = ("moon", "rain", "bell")
PROMPT = "Write a short magical nursery rhyme about two children solving a small gingham-clad problem together."

ASP_RULES = """
works(moon,moonlight).
works(rain,raindrop).
works(bell,bell_tune).
#show works/2.
"""


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {
            "hero": Entity("hero", params.hero, "character", memes={"curiosity": 1, "confidence": 0}),
            "friend": Entity("friend", params.friend, "character", memes={"curiosity": 1, "confidence": 0}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question="", cause="", result=""):
        self.history.append(Event(kind, text, question, cause, result, state=self.snapshot()))

    def say(self, who: str, text: str, *, to=""):
        if who not in self.entities:
            raise StoryError("A story speaker must be a named character.")
        self.history.append(Event("speech", f'"{text}" said {self.entities[who].label}.',
                                  speaker=who, listener=to, state=self.snapshot()))

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
                QAItem("What kind of cloth carried the magic?", "A gingham cloth carried the magic.")
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.path not in PATHS:
        raise StoryError("Choose one of the three magical nursery-rhyme paths.")
    if params.hero == params.friend:
        raise StoryError("The two characters need different names.")
    for name in (params.hero, params.friend):
        if not name[:1].isupper() or not name.isalpha():
            raise StoryError("Character names must be simple capitalized words.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    world.entities["cloth"] = Entity(
        "cloth", "the gingham cloth", "magical cloth", "nursery shelf",
        meters={"folds": 3, "magic": 1}, memes={"helpfulness": 1},
    )
    world.entities["hero"].beliefs["magic"] = "unknown"
    world.entities["friend"].beliefs["magic"] = "unknown"
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    h, f = params.hero, params.friend
    cloth = world.entities["cloth"]
    world.narrate(
        "beginning",
        f"{h} and {f} played beside the nursery shelf, where a gingham cloth "
        "lay folded under a silver thimble.",
    )
    world.say("hero", "The cloth is humming softly.")
    world.say("friend", "Then let us listen before we tug it.")
    world.narrate(
        "discovery",
        "They leaned close. A tiny golden stitch winked, and the gingham magic stirred.",
    )
    cloth.meters["magic"] = 0
    world.entities["hero"].beliefs["magic"] = "answers careful questions"
    world.entities["friend"].beliefs["magic"] = "answers careful questions"

    if params.path == "moon":
        world.entities["star"] = Entity("star", "the paper moon", "toy", "window ledge",
                                        meters={"height": 0, "lit": 0})
        world.say("hero", "The paper moon has fallen behind the tall curtain.")
        world.say("friend", "The cloth may lift it, but only if we ask where it wants to go.")
        world.narrate(
            "trouble",
            f"The paper moon had slipped behind the curtain, and {h} could not reach it.",
            question="Why could {h} not pick up the paper moon?",
            cause="The moon had fallen behind the tall curtain.",
            result=f"{h} needed the gingham magic to reach it safely.",
        )
        world.say("hero", "Gingham cloth, will you make a little ladder?")
        world.say("friend", "Ask for a ladder that stops at the moon.")
        world.entities["hero"].beliefs["answer"] = "a short ladder"
        world.narrate("decision", "The golden stitch pointed to the floor, so they chose a short ladder instead of a high one.")
        world.entities["star"].meters.update(height=1, lit=1)
        world.narrate(
            "resolution",
            f"The gingham cloth unrolled into three soft steps. {h} climbed one step, "
            f"{f} held the edge, and together they brought down the paper moon.",
            question="How did the children rescue the paper moon?",
            cause="They learned that the cloth could make a short ladder.",
            result="They used the three soft gingham steps and brought the moon down safely.",
        )
        world.say("friend", "Now the moon can shine above the dolls.")
        world.say("hero", "And the ladder can fold away when morning comes.")
        world.narrate("ending", "The cloth folded itself into a gingham square, while the paper moon glowed above the dolls.")

    elif params.path == "rain":
        world.entities["rain"] = Entity("rain", "the indoor rain cloud", "toy", "playroom ceiling",
                                        meters={"drops": 3, "dry": 0})
        world.say("hero", "The toy cloud is dripping on the storybook.")
        world.say("friend", "We must learn whether it needs a bowl or a song.")
        world.narrate(
            "trouble",
            "A toy rain cloud dripped three bright drops onto the open storybook.",
            question="What was threatening the storybook?",
            cause="The toy cloud was dripping on its pages.",
            result="The children had to discover what would stop the indoor rain.",
        )
        world.say("hero", "Gingham cloth, what will make the cloud rest?")
        world.say("friend", "Listen. It is tapping three times, like a sleepy drum.")
        world.entities["friend"].beliefs["answer"] = "a nest"
        world.narrate("decision", "The children learned that the cloud wanted a soft nest, so they shaped the cloth into a bowl.")
        world.entities["rain"].meters.update(drops=0, dry=1)
        world.narrate(
            "resolution",
            f"{h} folded the gingham into a nest, and {f} lifted the cloud into it. "
            "The last raindrop landed in the cloth instead of the book.",
            question="How did they keep the storybook dry?",
            cause="They learned that the sleepy cloud needed a soft nest.",
            result="They folded the gingham into a nest and caught the last raindrop.",
        )
        world.say("hero", "The letters are dry.")
        world.say("friend", "And the little cloud is dreaming without a drip.")
        world.narrate("ending", "The storybook stayed open and dry, while the tiny cloud slept in its gingham nest.")

    else:
        world.entities["bell"] = Entity("bell", "the nursery bell", "toy", "door",
                                        meters={"ringing": 1, "heard": 0})
        world.say("hero", "The nursery bell rings, but no one knows why.")
        world.say("friend", "Perhaps the bell wants a friend to answer its call.")
        world.narrate(
            "trouble",
            "The nursery bell rang again and again, waking the baby rabbit doll.",
            question="Why did the baby rabbit doll wake?",
            cause="The nursery bell kept ringing beside the door.",
            result="The children needed to find what the lonely bell was calling for.",
        )
        world.say("hero", "Gingham cloth, show us what the bell needs.")
        world.say("friend", "Look! Its golden stitch points toward the toy drum.")
        world.entities["hero"].beliefs["answer"] = "a drumbeat"
        world.narrate("decision", "They learned that the bell was calling for a matching drumbeat, so they carried the toy drum beside it.")
        world.entities["bell"].meters.update(ringing=0, heard=1)
        world.narrate(
            "resolution",
            f"{h} tapped the drum once, and {f} answered with the bell. "
            "The two sounds matched, and the bell grew quiet.",
            question="What stopped the nursery bell from ringing?",
            cause="The children learned that the bell wanted a matching drumbeat.",
            result="They answered it with the toy drum, and the bell became quiet.",
        )
        world.say("friend", "The rabbit doll can sleep now.")
        world.say("hero", "The bell has found its little song.")
        world.narrate("ending", "The baby rabbit dreamed beneath the quiet bell, and the gingham cloth made a neat bow on the drum.")
    check_sample(world)
    return world.sample()


def check_sample(world: World):
    if world.entities["cloth"].meters["magic"] != 0:
        raise StoryError("The magical cloth must be used.")
    if not any(event.kind == "ending" for event in world.history):
        raise StoryError("The story needs a visible ending.")
    if len([event for event in world.history if event.kind == "speech"]) < 6:
        raise StoryError("Both characters need a real exchange.")
    if any(not event.cause or not event.result for event in world.history if event.question):
        raise StoryError("Every story question needs a causal answer.")
    if world.params.path == "moon" and world.entities["star"].meters["lit"] != 1:
        raise StoryError("The moon must be rescued.")
    if world.params.path == "rain" and world.entities["rain"].meters["dry"] != 1:
        raise StoryError("The rain cloud must be settled.")
    if world.params.path == "bell" and world.entities["bell"].meters["heard"] != 1:
        raise StoryError("The bell must receive its answer.")


def asp_facts() -> str:
    from asp import fact
    return "\n".join(fact("works", path, result) for path, result in
                     (("moon", "moonlight"), ("rain", "raindrop"), ("bell", "bell_tune")))


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "works"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--path", choices=PATHS)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice(tuple(name for name in NAMES if name != hero))
    params = StoryParams(hero=hero, friend=friend, path=args.path or rng.choice(PATHS), seed=args.seed)
    validate_params(params)
    return params


def verify():
    expected = {("moon", "moonlight"), ("rain", "raindrop"), ("bell", "bell_tune")}
    if asp_combos() != expected:
        raise StoryError("Python and ASP disagree about the magical paths.")
    count = 0
    for path in PATHS:
        sample = generate(StoryParams(path=path))
        check_sample(sample.world)
        count += 1
    print(f"OK: {count} story paths; ASP parity verified.")


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
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
            print(json.dumps(sorted(asp_combos())))
            return 0
        rng = random.Random(args.seed)
        if args.all:
            paths = [path for path in PATHS if args.path is None or path == args.path]
            samples = [generate(StoryParams(
                hero=args.hero or rng.choice(NAMES),
                friend=args.friend or rng.choice(tuple(name for name in NAMES if name != (args.hero or ""))),
                path=path,
                seed=args.seed,
            )) for path in paths]
        else:
            samples = [generate(resolve_params(args, rng)) for _ in range(args.n)]
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
