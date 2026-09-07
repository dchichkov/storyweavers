#!/usr/bin/env python3
"""A heartwarming dining-room quest about deciding what to do, darling."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


PATHS = ("candle", "letter", "cake")
NAMES = ("Mara", "Lina", "Rose")
VOICES = ("gentle", "bright", "quiet")


@dataclass
class StoryParams:
    hero: str = "Mara"
    darling: str = "Darling"
    path: str = "candle"
    voice: str = "gentle"
    world_seed: int = 777
    prose_seed: int = 42


@dataclass
class Event:
    kind: str
    data: dict[str, str]
    facts: tuple[str, ...] = ()
    causes: tuple[int, ...] = ()


@dataclass
class World:
    params: StoryParams
    events: list[Event] = field(default_factory=list)
    facts: set[str] = field(default_factory=set)
    state: dict[str, str] = field(default_factory=dict)

    def record(self, kind: str, facts: tuple[str, ...], **data):
        causes = tuple(i for i, event in enumerate(self.events) if set(event.facts) & self.facts)
        self.events.append(Event(kind, data, facts, causes))
        self.facts.update(facts)
        self.state.update(data)


def validate_params(p: StoryParams):
    if p.path not in PATHS:
        raise StoryError(f"Unknown quest path: {p.path!r}.")
    if p.voice not in VOICES:
        raise StoryError(f"Unknown voice: {p.voice!r}.")
    if not p.hero or not p.hero[0].isupper():
        raise StoryError("The hero name must begin with a capital letter.")
    if not p.darling:
        raise StoryError("The darling needs a name.")
    if type(p.world_seed) is not int or type(p.prose_seed) is not int:
        raise StoryError("Seeds must be integers.")


def build_world(p: StoryParams) -> World:
    validate_params(p)
    w = World(p)
    w.record("opening", ("dining_room_ready",), hero=p.hero, darling=p.darling)
    if p.path == "candle":
        w.record("trouble", ("dark_table",), item="birthday candle")
        w.record("learn", ("wind_known",), lesson="the open window was blowing out the flame")
        w.record("decide", ("decision_made",), decision="close the window before lighting the candle")
        w.record("resolution", ("quest_complete",), result="the candle stayed lit")
    elif p.path == "letter":
        w.record("trouble", ("hidden_letter",), item="a folded letter")
        w.record("learn", ("message_known",), lesson="the letter was a thank-you note for Darling")
        w.record("decide", ("decision_made",), decision="read the letter aloud instead of hiding it")
        w.record("resolution", ("quest_complete",), result="Darling heard the thanks and smiled")
    else:
        w.record("trouble", ("missing_slice",), item="the last cake slice")
        w.record("learn", ("slice_shared",), lesson="Darling had saved it for someone who felt lonely")
        w.record("decide", ("decision_made",), decision="share the slice rather than keep it")
        w.record("resolution", ("quest_complete",), result="two spoons met in one happy slice")
    w.record("closing", ("story_complete",), result=w.state["result"])
    return w


def validate_world(w: World):
    if "story_complete" not in w.facts or "quest_complete" not in w.facts:
        raise StoryError("The dining-room quest did not reach a visible resolution.")
    if "decision_made" not in w.facts:
        raise StoryError("The hero must make a decision.")
    if len(w.events) != 6:
        raise StoryError("Each path needs six complete scenes.")


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    validate_world(w)
    return w


class Teller:
    def __init__(self, w: World):
        self.w = w
        self.p = w.params
        self.rng = random.Random(self.p.prose_seed)
        self.paragraphs: list[str] = []
        self.qa: list[QAItem] = []

    def pick(self, *choices: str) -> str:
        return self.rng.choice(choices)

    def tell(self, text: str):
        self.paragraphs.append(text)

    def dialogue(self, first: str, second: str):
        self.paragraphs.append(f'"{first}" {self.p.hero} said.')
        self.paragraphs.append(f'"{second}" {self.p.darling} replied.')

    def run(self) -> tuple[str, list[QAItem]]:
        path = self.p.path
        self.tell(self.pick(
            f"The dining room was ready, but {self.p.hero} could feel a small quest waiting beside the table and needed to decide how to help.",
            f"At the dining-room table, {self.p.hero} found {self.p.darling} watching the supper things with hopeful eyes and paused to decide how to help."
        ))
        if path == "candle":
            self.tell("A draft kept snuffing the birthday candle before anyone could sing.")
            self.dialogue("Should I keep trying?", "Wait, darling. Listen to the window.")
            self.tell("The curtain lifted each time the flame shrank. {0} learned that the open window was the trouble.".format(self.p.hero))
            self.dialogue("I will close it before I light the candle again.", "Then I will save the song for you.")
            self.tell("The window clicked shut. When {0} struck the match again, the candle burned steadily, and {1} made a wish beside its warm little flame.".format(self.p.hero, self.p.darling))
            self.qa.append(QAItem("Why did the candle keep going out?", "The open dining-room window sent a draft across the table and snuffed the flame."))
            self.qa.append(QAItem("What did the hero decide to do?", "The hero decided to close the window before lighting the candle again."))
        elif path == "letter":
            self.tell("A folded letter lay beneath the blue plate, and {0} wondered whether it was meant to stay hidden.".format(self.p.hero))
            self.dialogue("Should I put it away?", "No, darling. My name is on the fold.")
            self.tell("{0} opened it and learned that the letter was a thank-you note for {1}, written by someone who had felt less alone because of {1}'s kindness.".format(self.p.hero, self.p.darling))
            self.dialogue("I will read it aloud.", "Then let the dining room hear it too.")
            self.tell("When {0} finished reading, {1} pressed the letter to their heart. The empty chair seemed less lonely, and the table held its quiet joy.".format(self.p.hero, self.p.darling))
            self.qa.append(QAItem("What did the hero learn from the letter?", "The hero learned that it was a thank-you note for Darling's kindness."))
            self.qa.append(QAItem("Why did the hero read the letter aloud?", "The hero chose to share the true thanks with Darling instead of hiding the letter."))
        else:
            self.tell("The last slice of cake had vanished from the plate, leaving a bright smear of icing and a worried silence.")
            self.dialogue("Did you take it?", "No, darling. I saved it for someone who felt lonely.")
            self.tell("{0} learned that {1} had carried the slice to the empty chair for a guest who needed company, but the guest had not arrived.".format(self.p.hero, self.p.darling))
            self.dialogue("Then we can share it while we wait.", "That is a very kind decision.")
            self.tell("{0} cut the slice in two. Two spoons met in the same sweet bite, and when the lonely guest finally came in, there was still a welcoming place at the table.".format(self.p.hero))
            self.qa.append(QAItem("Why was the cake slice missing?", "Darling had saved it for someone who felt lonely and expected that person to join the table."))
            self.qa.append(QAItem("What did the hero decide to do?", "The hero decided to share the slice while they waited, leaving a welcoming place for the guest."))
        self.tell(self.pick(
            f"By the end, the dining room felt brighter because {self.p.hero} had listened before deciding.",
            f"The table grew peaceful again, and {self.p.hero} knew that a careful decision could make a small room feel like home."
        ))
        return "\n\n".join(self.paragraphs), self.qa


ASP_RULES = """
valid_path(candle).
valid_path(letter).
valid_path(cake).
#show valid_path/1.
"""


def asp_facts():
    from asp import fact
    return "\n".join(fact("path", path) for path in PATHS)


def asp_paths():
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid_path"))


def generate(p: StoryParams) -> StorySample:
    world = simulate(p)
    story, qa = Teller(world).run()
    return StorySample(
        params=p,
        story=story,
        prompts=[f"Write a heartwarming dining-room Quest in which {p.hero} must decide what to do for {p.darling}, using suspense and inner monologue."],
        story_qa=qa,
        world_qa=[
            QAItem("What makes a quest complete?", "A quest is complete when a character learns what matters, decides what to do, and causes a visible helpful change.")
        ],
        world=world,
    )


def verify():
    if asp_paths() != {(path,) for path in PATHS}:
        raise StoryError("Python and ASP disagree about the available quest paths.")
    for path in PATHS:
        for seed in range(6):
            sample = generate(StoryParams(path=path, world_seed=seed, prose_seed=seed))
            if "darling" not in sample.story.lower() or "decid" not in sample.story.lower():
                raise StoryError("A generated story lost a required narrative word.")
            validate_world(sample.world)
    print("OK: three causal quest paths; ASP parity; seeded renderings.")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", dest="world_seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--darling", default=None)
    parser.add_argument("--path", choices=PATHS)
    parser.add_argument("--voice", choices=VOICES, default="gentle")
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, index: int, rng: random.Random) -> StoryParams:
    p = StoryParams(
        hero=args.hero or rng.choice(NAMES),
        darling=args.darling or "Darling",
        path=args.path or rng.choice(PATHS),
        voice=args.voice,
        world_seed=args.world_seed + index,
        prose_seed=args.prose_seed + index,
    )
    validate_params(p)
    return p


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({"state": sample.world.state, "history": [asdict(e) for e in sample.world.events]}, indent=2))


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
            paths = [path for path in PATHS if args.path is None or args.path == path]
            params = [
                StoryParams(
                    hero=args.hero or "Mara",
                    darling=args.darling or "Darling",
                    path=path,
                    voice=args.voice,
                    world_seed=args.world_seed + i,
                    prose_seed=args.prose_seed + i,
                )
                for i, path in enumerate(paths)
            ]
        else:
            params = [resolve_params(args, i, rng) for i in range(args.n)]
        if args.json:
            rows = [generate(p).to_dict() for p in params]
            print(json.dumps(rows[0] if len(rows) == 1 else rows, ensure_ascii=False, indent=2))
        else:
            for i, p in enumerate(params):
                emit(generate(p), trace=args.trace, qa=args.qa,
                     header=f"\n### Story {i + 1}\n" if len(params) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
