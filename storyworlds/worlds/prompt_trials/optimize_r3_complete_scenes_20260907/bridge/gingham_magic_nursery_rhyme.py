#!/usr/bin/env python3
"""Gingham Magic: a nursery-rhyme story about two children mending a magical cloth."""

from __future__ import annotations

import argparse
import json
import random
import re
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
    kind: str
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


@dataclass
class StoryParams:
    hero: str = "Nell"
    friend: str = "Pip"
    trouble: str = "tear"
    seed: int = 777


NAMES = ("Nell", "Pip", "Rose", "Tom", "May", "Kit")
TROUBLES = ("tear", "rain", "sleep")
PROMPT = "Write a gentle nursery-rhyme story about children using magic gingham to mend a small trouble."
TROUBLE_NAMES = {
    "tear": "a tear",
    "rain": "a silver rain",
    "sleep": "a sleepy spell",
}


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, "character", memes={"hope": 0.5}),
            "friend": Entity("friend", params.friend, "character", memes={"hope": 0.5}),
            "cloth": Entity(
                "cloth", "the gingham cloth", "magic_cloth", "basket",
                meters={"magic": 1, "whole": 0}, memes={"kindness": 0.5},
            ),
            "nursery": Entity(
                "nursery", "the nursery", "place", "hill",
                meters={"safe": 0, "dry": 1, "awake": 1},
            ),
        }
        self.history: list[Event] = []

    def narrate(self, text: str, *, kind="scene", question="", cause="", result=""):
        self.history.append(Event(kind, text, question=question, cause=cause, result=result))

    def say(self, who: str, text: str, *, to="", question=""):
        if not text.endswith((".", "?", "!")):
            text += "."
        self.history.append(Event("speech", f'"{text}"', speaker=who, listener=to,
                                  question=question))

    def snapshot(self):
        return {key: asdict(value) for key, value in self.entities.items()}


def validate_params(params: StoryParams):
    if params.trouble not in TROUBLES:
        raise StoryError("Choose one of the known nursery troubles.")
    if params.hero == params.friend:
        raise StoryError("The two characters need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", n) for n in (params.hero, params.friend)):
        raise StoryError("Names must be simple capitalized words.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    rng = random.Random(params.seed)
    h, f = params.hero, params.friend
    world.narrate(
        f"{h} and {f} found a square of gingham beneath the nursery bed. "
        "Its blue checks shimmered like little moonlit windows."
    )
    world.say("hero", "What can our gingham do?", to="friend")
    world.say("friend", "Magic listens when we notice the trouble first.", to="hero")

    if params.trouble == "tear":
        world.entities["nursery"].meters["safe"] = 0
        world.narrate(
            f"A cold wind slipped through a tear in the nursery curtain, and the toy stars trembled.",
            question="What trouble did the children notice?",
            cause="A tear let the cold wind into the nursery.",
            result="The toy stars trembled beside the draft.",
        )
        world.say("hero", "I could pull the cloth tight.")
        world.say("friend", "That would hide the tear, but it would not mend it.")
        world.say("hero", "Then we need a stitch and a kind word.")
        world.narrate(
            f"{h} threaded a silver moonbeam through the gingham while {f} held the torn edges together.",
            question="How did they decide to mend the curtain?",
            cause="Pulling the cloth tight would only hide the tear.",
            result="They chose a moonbeam stitch while one child held the edges.",
        )
        world.entities["cloth"].meters["whole"] = 1
        world.entities["nursery"].meters["safe"] = 1
        world.narrate(
            f"The gingham flashed, and the tear closed into a neat blue check. "
            f"The wind became a warm whisper, so {h} tied the curtain with a ribbon.",
            question="What changed after the magical stitch?",
            cause="The gingham joined the torn curtain with a silver moonbeam.",
            result="The draft stopped and the nursery grew warm.",
        )
    elif params.trouble == "rain":
        world.entities["nursery"].meters["dry"] = 0
        world.narrate(
            "A silver rain fell from the ceiling, though the roof was bright and dry outside.",
            question="Why did the children need magic?",
            cause="A silver rain appeared inside the nursery.",
            result="The blankets and picture books began to get wet.",
        )
        world.say("hero", "Let us spread the gingham like an umbrella.")
        world.say("friend", "Wait. The rain is coming from the sad little cloud.")
        world.say("hero", "Then we must cheer the cloud, not cover it.")
        world.narrate(
            f"{f} asked the cloud what it needed, while {h} placed the gingham beneath its soft gray feet.",
            question="What did the children learn about the rain?",
            cause="The rain came from a sad cloud rather than a hole in the roof.",
            result="They decided to comfort the cloud instead of merely covering the room.",
        )
        world.entities["cloth"].meters["whole"] = 1
        world.entities["nursery"].meters["dry"] = 1
        world.narrate(
            f"The gingham made a tiny rainbow pocket. The cloud tucked inside, dried its tears, "
            f"and floated out through the window. {h} shook the books dry.",
            question="How did the nursery become dry?",
            cause="The gingham gave the sad cloud a rainbow pocket.",
            result="The cloud stopped raining and floated outside.",
        )
    else:
        world.entities["nursery"].meters["awake"] = 0
        world.narrate(
            "A sleepy spell rolled through the nursery, and every toy yawned at once.",
            question="What happened to the nursery?",
            cause="A sleepy spell passed over the room.",
            result="The toys yawned and the room fell quiet.",
        )
        world.say("hero", "I will ring the brass bell.")
        world.say("friend", "The bell may wake the toys, but it will not wake the spell.")
        world.say("hero", "Then let the gingham sing to it.")
        world.narrate(
            f"{h} laid the gingham on the floor, and {f} tapped its checks in a soft nursery rhythm.",
            question="What did the children learn about the spell?",
            cause="A loud bell would wake the toys but not change the spell.",
            result="They decided to use the gingham's gentle rhythm.",
        )
        world.entities["cloth"].meters["whole"] = 1
        world.entities["nursery"].meters["awake"] = 1
        world.narrate(
            f"Check by check, the gingham hummed, and the sleepy spell curled into a small silver moth. "
            f"{f} opened the window, and the moth flew into the dawn.",
            question="What became of the sleepy spell?",
            cause="The gingham's gentle rhythm changed the spell.",
            result="The spell became a silver moth and flew away.",
        )

    world.say("friend", "The magic heard us because we listened first.", to="hero")
    world.say("hero", "And the gingham made our careful plan shine.")
    ending = {
        "tear": f"The mended curtain danced in the warm air while {h} and {f} watched the blue checks sparkle.",
        "rain": f"The dry books stood in a sunny row while {h} and {f} folded the rainbow gingham.",
        "sleep": f"The toys blinked awake beneath the morning light while {h} and {f} packed the humming gingham away.",
    }[params.trouble]
    world.narrate(ending, kind="ending")
    sample = StorySample(
        params=params,
        story="\n\n".join(event.text if event.kind != "speech"
                            else f"{world.entities[event.speaker].label} said, {event.text}"
                            for event in world.history),
        prompts=[PROMPT],
        story_qa=[QAItem(e.question, f"{e.cause} {e.result}") for e in world.history if e.question],
        world_qa=[
            QAItem("What special cloth appeared in the story?",
                   "A square of gingham had gentle magic."),
        ],
        world=world,
    )
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    if world.entities["cloth"].meters["whole"] != 1:
        raise StoryError("The magical gingham must complete its work.")
    nursery = world.entities["nursery"].meters
    if sample.params.trouble == "tear" and nursery["safe"] != 1:
        raise StoryError("The curtain trouble was not resolved.")
    if sample.params.trouble == "rain" and nursery["dry"] != 1:
        raise StoryError("The rain trouble was not resolved.")
    if sample.params.trouble == "sleep" and nursery["awake"] != 1:
        raise StoryError("The sleepy spell was not resolved.")
    speech = [e for e in world.history if e.kind == "speech"]
    if not any(e.speaker == "hero" for e in speech) or not any(e.speaker == "friend" for e in speech):
        raise StoryError("Both characters must speak.")
    if len(sample.story_qa) != 3:
        raise StoryError("Each path needs three grounded questions.")
    if "gingham" not in sample.story.lower() or "magic" not in sample.story.lower():
        raise StoryError("The story must visibly include gingham and magic.")


ASP_RULES = """
resolved(T) :- trouble(T), remedy(T).
#show resolved/1.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        [fact("trouble", trouble) for trouble in TROUBLES]
        + [fact("remedy", "tear"), fact("remedy", "rain"), fact("remedy", "sleep")]
    )


def asp_resolved() -> set[str]:
    from asp import atoms, one_model
    return {row[0] for row in atoms(one_model(asp_facts() + ASP_RULES), "resolved")}


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--trouble", choices=TROUBLES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, rng):
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != hero])
    trouble = args.trouble or rng.choice(TROUBLES)
    return StoryParams(hero=hero, friend=friend, trouble=trouble, seed=args.seed)


def verify():
    if asp_resolved() != set(TROUBLES):
        raise StoryError("ASP and Python disagree about available paths.")
    for trouble in TROUBLES:
        check_sample(generate(StoryParams(trouble=trouble)))
    print(f"OK: {len(TROUBLES)} complete story paths verified.")


def emit(sample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps(sample.world.snapshot(), indent=2))


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            print(json.dumps(sorted(asp_resolved())))
            return 0
        rng = random.Random(args.seed)
        if args.all:
            troubles = [t for t in TROUBLES if args.trouble is None or t == args.trouble]
            samples = [
                generate(StoryParams(
                    hero=args.hero or rng.choice(NAMES),
                    friend=args.friend or rng.choice([n for n in NAMES if n != (args.hero or "")]),
                    trouble=trouble,
                    seed=args.seed,
                ))
                for trouble in troubles
            ]
        else:
            samples = [generate(resolve_params(args, rng)) for _ in range(args.n)]
        if args.json:
            payload = [s.to_dict() for s in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
                             ensure_ascii=False, indent=2))
        else:
            for i, sample in enumerate(samples):
                emit(sample, trace=args.trace, qa=args.qa,
                     header=f"\n### Story {i + 1}\n" if len(samples) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
