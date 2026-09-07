#!/usr/bin/env python3
"""Gingham Magic: a nursery-rhyme tale about a small cloth, a lost spell,
and two friends whose conversation helps the magic find its proper place.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
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
    hero: str = "Pip"
    friend: str = "Dot"
    creature: str = "moonmouse"
    charm: str = "gingham"
    rhyme: str = "twinkle"
    seed: int = 777


CREATURES = {
    "moonmouse": ("moon mouse", "a silver tail", "squeak"),
    "sunbird": ("sunbird", "a golden feather", "tweet"),
    "rainfrog": ("rain frog", "a blue umbrella", "croak"),
}
RHYMES = {
    "twinkle": ("Twinkle, tiny star, show us where the lost things are!"),
    "hush": ("Hush, hush, little light, guide our feet through velvet night!"),
    "tumble": ("Tumble, tumble, shining thread, mend the path where dreams have fled!"),
}
NAMES = ("Pip", "Dot", "Mina", "Bram", "Tess", "Nell")


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {
            "hero": Entity("hero", params.hero, "character", "garden",
                           memes={"wonder": 1.0, "trust": 0.5}),
            "friend": Entity("friend", params.friend, "character", "garden",
                             memes={"wonder": 1.0, "trust": 0.5}),
            "cloth": Entity("cloth", "the gingham cloth", "charm", "basket",
                            meters={"magic": 1, "brightness": 0}),
            "creature": Entity("creature", CREATURES[params.creature][0],
                               "creature", "hedge", meters={"safe": 0}),
            "moon": Entity("moon", "the moon", "light", "sky",
                           meters={"visible": 1}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question: str = "",
                cause: str = "", result: str = ""):
        self.history.append(Event(kind, text, question, cause, result,
                                  self.snapshot()))

    def say(self, speaker: str, text: str):
        if speaker not in self.entities:
            raise StoryError("A story speaker must be a known character.")
        label = self.entities[speaker].label
        tag = "asked" if text.endswith("?") else "said"
        self.history.append(Event("speech", f'"{text}" {label} {tag}.',
                                  state=self.snapshot()))

    def settle(self):
        for key in ("hero", "friend"):
            self.entities[key].memes["trust"] = 1.0
            self.entities[key].memes["wonder"] = 1.0

    def sample(self) -> StorySample:
        questions = [
            QAItem(e.question, f"{e.cause} {e.result}")
            for e in self.history if e.question
        ]
        return StorySample(
            params=self.params,
            story="\n\n".join(e.text for e in self.history),
            prompts=[PROMPT],
            story_qa=questions,
            world_qa=[
                QAItem("What is gingham?", "Gingham is a woven cloth with a simple checked pattern."),
                QAItem("What does a magic charm need in this tale?",
                       "The charm needs a clear purpose and a spoken rhyme to guide its magic."),
            ],
            world=self,
        )


PROMPT = "Write a dialogue-rich nursery-rhyme story about gingham magic helping a small creature."
ASP_RULES = """
usable_charm(C,R) :- charm(C), rhyme(R).
#show usable_charm/2.
"""


def validate_params(params: StoryParams):
    if params.charm != "gingham":
        raise StoryError("This nursery-rhyme charm must be gingham.")
    if params.creature not in CREATURES or params.rhyme not in RHYMES:
        raise StoryError("Choose a known creature and rhyme.")
    if params.hero == params.friend:
        raise StoryError("The two friends must have different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", n)
           for n in (params.hero, params.friend)):
        raise StoryError("Use simple capitalized names, such as Pip and Dot.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero, friend = params.hero, params.friend
    creature, tail, sound = CREATURES[params.creature]
    rhyme = RHYMES[params.rhyme]
    cloth = world.entities["cloth"]
    animal = world.entities["creature"]

    world.narrate(
        "beginning",
        f"By the moonlit gate, {hero} and {friend} found a square of gingham, "
        f"red-check bright and soft as a song. A {creature} peeped from the hedge, "
        f"with {tail} and a worried little {sound}.",
    )
    world.say("hero", f"Shall we wrap the gingham round the {creature}?")
    world.say("friend", "Yes, then it will be safe from the night dew.")
    cloth.location = "hero"
    animal.meters["safe"] = 0
    world.narrate(
        "mistake",
        f"{hero} wrapped the gingham around the {creature}, but the checks stayed still. "
        f"The {creature} shivered, and the moon slipped behind a cloud.",
        question="Why did the gingham spell not work at first?",
        cause=f"{hero} and {friend} treated the cloth as a blanket instead of giving its magic a clear task.",
        result="The charm stayed quiet, so the frightened creature remained outside the hedge.",
    )
    world.say("hero", "It did not shine. Did I fold it wrong?")
    world.say("friend", "Perhaps. What did you hope the gingham would do?")
    world.say("hero", "I wanted it to show the creature a safe way home.")
    world.say("friend", "Then say that plainly, and let the rhyme point the way.")
    world.narrate(
        "turn",
        f"They lifted the gingham beneath the moon. {friend} smoothed one corner, "
        f"while {hero} held the red checks toward the dark garden path.",
        question="How did the friends discover what the charm needed?",
        cause=f"{friend} asked {hero} to name the wish, and {hero} explained that the creature needed a safe path home.",
        result="They understood that the magic needed a clear purpose, not merely a folded cloth.",
    )
    world.say("friend", f"Now speak the rhyme: {rhyme}")
    world.say("hero", "Gingham bright, guide gentle feet; lead our little friend to sleep.")
    cloth.meters["brightness"] = 1
    cloth.location = "path"
    animal.meters["safe"] = 1
    world.narrate(
        "magic",
        f"Check, check, gingham gleamed. A red-and-white path curled from the hedge "
        f"to a warm nest beneath the rosebush. The {creature} gave a happy {sound} "
        f"and padded along it.",
        question="What made the gingham magic guide the creature?",
        cause=f"{hero} named the safe-home wish, and {friend} helped choose a rhyme to guide the spell.",
        result="The glowing gingham made a path from the hedge to the creature's warm nest.",
    )
    world.say("hero", "There is the nest! The little path knows where to go.")
    world.say("friend", "And the cloth knows when its work is done.")
    cloth.meters["magic"] = 0
    world.settle()
    world.narrate(
        "ending",
        f"The {creature} curled beneath the rosebush. The gingham folded itself into "
        f"a neat little square, and the moon came out to clap a pale silver hand. "
        f"{hero} and {friend} skipped home, singing, 'Check by check, and rhyme by rhyme, "
        f"kind words help magic keep good time!'",
        question="What changed by the end of the story?",
        cause="The friends spoke clearly about the creature's need and used the gingham for that purpose.",
        result="The magic made a safe path, the creature reached its nest, and the cloth became quiet again.",
    )
    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    if world.entities["creature"].meters["safe"] != 1:
        raise StoryError("The creature must reach safety.")
    if world.entities["cloth"].meters["brightness"] != 1:
        raise StoryError("The gingham magic must visibly work.")
    speeches = [e for e in world.history if e.kind == "speech"]
    if len(speeches) < 8:
        raise StoryError("The story needs a sustained exchange of dialogue.")
    if not any("hero" not in e.text for e in speeches):
        pass
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs grounded questions and answers.")
    if any(world.entities[k].memes["trust"] < 1 for k in ("hero", "friend")):
        raise StoryError("The friends must reach a trusting resolution.")


def asp_facts() -> str:
    from asp import fact
    return "\n".join([
        fact("charm", "gingham"),
        *[fact("rhyme", key) for key in RHYMES],
    ])


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + ASP_RULES), "usable_charm"))


def valid_combos() -> list[tuple[str, str]]:
    return [("gingham", rhyme) for rhyme in RHYMES]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--creature", choices=tuple(CREATURES))
    parser.add_argument("--rhyme", choices=tuple(RHYMES))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != hero])
    params = StoryParams(
        hero=hero,
        friend=friend,
        creature=args.creature or rng.choice(tuple(CREATURES)),
        rhyme=args.rhyme or rng.choice(tuple(RHYMES)),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree about usable gingham rhymes.")
    tested = 0
    for creature in CREATURES:
        for rhyme in RHYMES:
            sample = generate(StoryParams(creature=creature, rhyme=rhyme))
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} story states; {len(valid_combos())} ASP-compatible charm/rhyme pairs.")


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
            print(json.dumps(sorted(asp_combos())))
            return 0
        rng = random.Random(args.seed)
        if args.all:
            params_list = []
            for creature in CREATURES:
                for rhyme in RHYMES:
                    params_list.append(StoryParams(
                        hero=args.hero or "Pip",
                        friend=args.friend or "Dot",
                        creature=creature,
                        rhyme=rhyme,
                        seed=args.seed,
                    ))
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]
        samples = [generate(p) for p in params_list]
        if args.json:
            payload = [s.to_dict() for s in samples]
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
