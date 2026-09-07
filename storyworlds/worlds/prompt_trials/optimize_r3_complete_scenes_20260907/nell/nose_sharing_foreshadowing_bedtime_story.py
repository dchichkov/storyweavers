#!/usr/bin/env python3
"""A gentle bedtime story about sharing a nose-shaped keepsake and noticing a clue."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field, replace
import itertools
import json
from pathlib import Path
import random
import sys

_here = Path(__file__).resolve()
for parent in (_here.parent, *_here.parents):
    candidate = parent / "results.py"
    if candidate.exists():
        sys.path.insert(0, str(parent))
        break
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


PATHS = ("lantern", "button", "bread")
NAMES = ("Nell", "Milo", "Rose", "Tess")
VOICES = ("gentle", "plain", "playful")
MAX_EVENTS = 12


@dataclass
class StoryParams:
    hero: str = "Nell"
    friend: str = "Milo"
    path: str = "lantern"
    voice: str = "gentle"
    world_seed: int = 777
    prose_seed: int = 42


@dataclass
class Entity:
    name: str
    location: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Event:
    index: int
    kind: str
    facts: tuple[str, ...]
    data: dict


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity]
    history: list[Event] = field(default_factory=list)
    facts: set[str] = field(default_factory=set)
    ending: str = ""

    def record(self, kind: str, facts: tuple[str, ...], **data):
        self.history.append(Event(len(self.history), kind, facts, data))
        self.facts.update(facts)


def validate_params(p: StoryParams):
    if p.path not in PATHS:
        raise StoryError(f"Unknown path: {p.path!r}.")
    if p.voice not in VOICES:
        raise StoryError(f"Unknown voice: {p.voice!r}.")
    if not isinstance(p.world_seed, int) or not isinstance(p.prose_seed, int):
        raise StoryError("Seeds must be integers.")
    for name in (p.hero, p.friend):
        if not name or not name[0].isupper() or not name.isalpha():
            raise StoryError("Names must be simple capitalized words.")
    if p.hero == p.friend:
        raise StoryError("The two children need different names.")


def build_world(p: StoryParams) -> World:
    validate_params(p)
    w = World(
        params=p,
        entities={
            "hero": Entity(p.hero, "bedroom", p.hero, memes={"hope": 1}),
            "friend": Entity(p.friend, "bedroom", p.friend, memes={"worry": 1}),
            "nose": Entity("nose", "pocket", p.hero, meters={"round": 1, "shared": 0}),
            "blanket": Entity("blanket", "bed", p.friend),
            "window": Entity("window", "wall"),
        },
    )
    w.record("bedtime", ("night",), sky="dark")
    return w


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    if p.path == "lantern":
        w.record("whisper", ("worry_named",), words="a light was missing")
        w.record("clue", ("clue_seen",), place="window")
        w.record("share", ("nose_shared",), object="nose")
        w.record("resolution", ("light_returned",), object="lantern")
        w.ending = "lantern"
    elif p.path == "button":
        w.record("whisper", ("worry_named",), words="a coat was lonely")
        w.record("clue", ("clue_seen",), place="blanket")
        w.record("share", ("nose_shared",), object="nose")
        w.record("resolution", ("button_found",), object="button")
        w.ending = "button"
    else:
        w.record("whisper", ("worry_named",), words="a hungry moon")
        w.record("clue", ("clue_seen",), place="pocket")
        w.record("share", ("nose_shared",), object="nose")
        w.record("resolution", ("bread_shared",), object="bread")
        w.ending = "bread"
    validate_world(w)
    return w


def validate_world(w: World):
    if not w.ending or "nose_shared" not in w.facts:
        raise StoryError("The story must resolve through sharing the nose.")
    if len(w.history) > MAX_EVENTS:
        raise StoryError("The bedtime story became too long.")
    if w.entities["nose"].meters["shared"] != 0:
        raise StoryError("The nose marker must begin unused.")


def render(w: World) -> tuple[str, list[QAItem]]:
    p = w.params
    rng = random.Random(p.prose_seed)
    hero, friend = p.hero, p.friend
    gentle_openings = (
        f"At bedtime, {hero} and {friend} lay beneath the same soft blanket.",
        f"The room was quiet when {hero} tucked {friend} into bed.",
        f"Moonlight rested on the floor as {hero} and {friend} settled down.",
    )
    lines = [rng.choice(gentle_openings)]
    if p.path == "lantern":
        lines.append(f'{friend} whispered, "I cannot sleep. The little lantern by the window has gone dark."')
        lines.append(f'{hero} answered, "Then we will look together, but first tell me what you noticed."')
        lines.append(
            f"{friend} pointed toward the window. A thin golden line showed beneath the curtain, "
            "a clue that the lantern had not vanished at all."
        )
        lines.append(f'{hero} took the round nose from a pocket and said, "Share this with me. It is silly enough to make a brave thought."')
        lines.append(f'{friend} held the nose too, and together they found the lantern switch behind the curtain.')
        lines.append(
            f"The lantern glowed again. {friend} smiled, and {hero} left the nose between their pillows "
            "so courage could be shared in the morning."
        )
        qa = [
            QAItem(
                question=f"Why did {hero} and {friend} look behind the curtain?",
                answer="A thin golden line beneath it showed that the missing lantern was still nearby.",
            ),
            QAItem(
                question="How did sharing the nose help?",
                answer=f"{hero} let {friend} hold the round nose too, and the shared silly moment helped them search calmly until they found the lantern switch.",
            ),
        ]
    elif p.path == "button":
        lines.append(f'{friend} whispered, "My coat has lost its bright button, and it feels lonely."')
        lines.append(f'{hero} said, "Tell me where you last felt its smooth spot."')
        lines.append(
            f"{friend} touched the blanket and found a small round hollow in its fold. "
            "The hollow was a clue that the button had slipped beneath the blanket."
        )
        lines.append(f'{hero} offered the little nose and said, "We can share this while we search."')
        lines.append(f'{friend} laughed, held the nose beside the blanket, and lifted the fold.')
        lines.append(
            f"The bright button rolled into view. {hero} sewed it back onto the coat, "
            f"and {friend} kept the nose beside the pillow as a shared bedtime treasure."
        )
        qa = [
            QAItem(
                question=f"What clue did {friend} notice?",
                answer="A small round hollow in the blanket fold showed where the missing button had slipped beneath it.",
            ),
            QAItem(
                question=f"What did {hero} and {friend} share?",
                answer=f"They shared the little round nose while they searched, and the laughter helped {friend} lift the blanket fold.",
            ),
        ]
    else:
        lines.append(f'{friend} whispered, "The moon looks hungry. I wish I had something to give it."')
        lines.append(f'{hero} replied, "What do you have that might make another person feel full?"')
        lines.append(
            f"{friend} heard a soft crinkle from {hero}'s pocket. It was a clue that a small piece of bread "
            "was waiting there."
        )
        lines.append(f'{hero} took out the round nose and said, "Hold this with me while we share the bread."')
        lines.append(f'{friend} held the nose, and {hero} broke the bread into two warm pieces.')
        lines.append(
            f"They shared the bread beneath the moon. The moon stayed high and silver, while {friend} "
            "felt peaceful enough to sleep, with the nose resting between them."
        )
        qa = [
            QAItem(
                question="What clue showed that food was nearby?",
                answer="A soft crinkle from the pocket showed that a small piece of bread was waiting there.",
            ),
            QAItem(
                question=f"Why did {hero} break the bread in two?",
                answer=f"{hero} wanted to share it with {friend}, so they could settle the hungry feeling together.",
            ),
        ]
    return "\n\n".join(lines), qa


def asp_facts():
    from asp import fact
    return "\n".join(fact("path", path) for path in PATHS)


ASP_RULES = """
valid(Path) :- path(Path).
shared(nose) :- valid(Path).
#show valid/1.
#show shared/1.
"""


def asp_paths():
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid"))


def generate(p: StoryParams) -> StorySample:
    world = simulate(p)
    story, qa = render(world)
    return StorySample(
        params=p,
        story=story,
        prompts=[f"Write a gentle bedtime story in which {p.hero} and {p.friend} share a nose-shaped keepsake."],
        story_qa=qa,
        world_qa=[
            QAItem(
                question="What makes sharing useful in this world?",
                answer="Sharing the small nose helps two children notice a clue and face a worry together.",
            )
        ],
        world=world,
    )


def verify():
    if asp_paths() != {(path,) for path in PATHS}:
        raise StoryError("Python and ASP disagree about the available paths.")
    for path in PATHS:
        sample = generate(StoryParams(path=path))
        if "nose" not in sample.story.lower() or len(sample.story_qa) < 2:
            raise StoryError("A generated story lost the required nose or grounded questions.")
    print("OK: three causal bedtime paths; ASP parity; complete scenes.")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", "--world-seed", dest="world_seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--friend", choices=NAMES)
    parser.add_argument("--path", choices=PATHS)
    parser.add_argument("--voice", choices=VOICES, default="gentle")
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, rng: random.Random, index=0, *, sample=False):
    hero = args.hero if args.hero else (rng.choice(NAMES) if sample else "Nell")
    options = tuple(name for name in NAMES if name != hero)
    friend = args.friend if args.friend else (rng.choice(options) if sample else "Milo")
    path = args.path if args.path else (rng.choice(PATHS) if sample else "lantern")
    return StoryParams(
        hero=hero,
        friend=friend,
        path=path,
        voice=args.voice,
        world_seed=args.world_seed + index,
        prose_seed=args.prose_seed + index,
    )


def emit(sample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        world = sample.world
        print("\nTRACE")
        print(json.dumps({
            "ending": world.ending,
            "facts": sorted(world.facts),
            "history": [asdict(event) for event in world.history],
        }, indent=2))


def main():
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
        rng = random.Random(args.world_seed)
        if args.all:
            params = [
                resolve_params(args, rng, index=i)
                for i, path in enumerate(PATHS)
                if args.path is None or args.path == path
            ]
            params = [replace(p, path=path) for p, path in zip(params, PATHS)]
        else:
            params = [
                resolve_params(args, rng, index=i, sample=args.n > 1)
                for i in range(args.n)
            ]
        if args.json:
            rows = [generate(p).to_dict() for p in params]
            print(json.dumps(rows[0] if len(rows) == 1 else rows, ensure_ascii=False, indent=2))
        else:
            for index, params_item in enumerate(params):
                emit(
                    generate(params_item),
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {index + 1}\n" if len(params) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
