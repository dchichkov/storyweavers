#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import itertools
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


PATHS = ("button", "moon", "rain")
NAMES = ("Nell", "Mara", "Pip")
VOICES = ("plain", "playful")
MAX_STEPS = 12


@dataclass
class StoryParams:
    hero: str = "Nell"
    path: str = "button"
    voice: str = "plain"
    world_seed: int = 777
    prose_seed: int = 42


@dataclass
class Event:
    kind: str
    data: dict[str, str] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    events: list[Event] = field(default_factory=list)
    facts: set[str] = field(default_factory=set)
    outcome: str = ""
    state: dict[str, str] = field(default_factory=dict)

    def record(self, kind: str, **data):
        self.events.append(Event(kind, {k: str(v) for k, v in data.items()}))
        self.facts.add(kind)


def validate_params(p: StoryParams):
    if p.path not in PATHS:
        raise StoryError(f"Unknown path: {p.path!r}.")
    if p.hero not in NAMES:
        raise StoryError(f"Unknown hero: {p.hero!r}.")
    if p.voice not in VOICES:
        raise StoryError(f"Unknown voice: {p.voice!r}.")
    if type(p.world_seed) is not int or type(p.prose_seed) is not int:
        raise StoryError("Seeds must be integers.")


def simulate(p: StoryParams) -> World:
    validate_params(p)
    w = World(p, state={"gingham": "blue-and-white", "magic": "sleeping"})
    w.record("opening", hero=p.hero, cloth="blue-and-white gingham")
    if p.path == "button":
        w.record("spill", problem="a silver button rolled into a crack")
        w.record("learn", clue="the button answered only to a rhyme")
        w.record("choice", decision="the children sang softly instead of pulling")
        w.state.update(button="found", magic="awake", floor="whole")
        w.record("resolution", result="the button hopped out and mended the torn blanket")
        w.outcome = "mended_blanket"
    elif p.path == "moon":
        w.record("shrink", problem="the moon shrank into a gingham pocket")
        w.record("learn", clue="the pocket opened when someone named a true wish")
        w.record("choice", decision="the children wished for light to share")
        w.state.update(moon="full", magic="awake", nursery="bright")
        w.record("resolution", result="the moon rose from the pocket and lit every bed")
        w.outcome = "shared_light"
    elif p.path == "rain":
        w.record("flood", problem="rain climbed the gingham nursery curtains")
        w.record("learn", clue="the curtains would listen to a counting song")
        w.record("choice", decision="the children counted the drops together")
        w.state.update(rain="gentle", magic="awake", curtains="dry")
        w.record("resolution", result="the drops danced into a silver pail")
        w.outcome = "quiet_rain"
    if len(w.events) > MAX_STEPS or not w.outcome:
        raise StoryError("The nursery rhyme did not reach a safe ending.")
    return w


class Teller:
    def __init__(self, world: World):
        self.w = world
        self.p = world.params
        self.rng = random.Random(self.p.prose_seed)
        self.parts: list[str] = []
        self.qa: list[QAItem] = []

    def pick(self, *items):
        return self.rng.choice(items)

    def speak(self, name: str, words: str) -> str:
        return f'"{words}" {name} said.'

    def render(self):
        hero = self.p.hero
        for event in self.w.events:
            k, d = event.kind, event.data
            if k == "opening":
                self.parts.append(self.pick(
                    f"{hero} tucked the little ones beneath a blue-and-white gingham quilt in the nursery.",
                    f"In the gingham nursery, {hero} checked each small pillow as evening settled."
                ))
                self.parts.append(self.speak(hero, "Hush now, for Magic is near."))
            elif k == "spill":
                self.parts.append("Then a silver button slipped from a coat and rolled into a crack beside the bed.")
                self.parts.append(self.speak("Mara", "We cannot reach it."))
                self.parts.append(self.speak(hero, "Then we must learn what it wants."))
            elif k == "shrink":
                self.parts.append("Then the round moon shrank like a pearl and fell into a gingham pocket.")
                self.parts.append(self.speak("Pip", "The night has lost its lamp!"))
                self.parts.append(self.speak(hero, "We shall ask the pocket kindly."))
            elif k == "flood":
                self.parts.append("Then rain tapped the roof and climbed the gingham curtains in bright little beads.")
                self.parts.append(self.speak("Mara", "The nursery will be wet."))
                self.parts.append(self.speak(hero, "We need a song the curtains can hear."))
            elif k == "learn":
                if self.p.path == "button":
                    self.parts.append("A tiny voice whispered from the crack, and they learned that the button answered only to a rhyme.")
                    self.parts.append(self.speak("Mara", "It wants music, not a tug."))
                    self.qa.append(QAItem("What did the children learn about the button?",
                                          "They learned that the button would answer only to a rhyme."))
                elif self.p.path == "moon":
                    self.parts.append("A silver stitch glimmered, and they learned that the pocket opened when someone named a true wish.")
                    self.parts.append(self.speak("Pip", "A true wish can open it."))
                    self.qa.append(QAItem("What opened the gingham pocket?",
                                          "Naming a true wish opened the gingham pocket."))
                else:
                    self.parts.append("The curtains rustled, and they learned that the drops would listen to a counting song.")
                    self.parts.append(self.speak("Mara", "The rain is waiting for numbers."))
                    self.qa.append(QAItem("What did the children learn about the rain?",
                                          "They learned that the drops would listen to a counting song."))
            elif k == "choice":
                if self.p.path == "button":
                    self.parts.append("So the children sang softly, and the crack began to sparkle.")
                    self.parts.append(self.speak(hero, "One, two, three, come back to me."))
                elif self.p.path == "moon":
                    self.parts.append("So they chose a wish that helped everyone, not just one sleepy child.")
                    self.parts.append(self.speak(hero, "Let there be light for every bed."))
                else:
                    self.parts.append("So the children counted every drop together, keeping a steady, friendly beat.")
                    self.parts.append(self.speak(hero, "One drop, two drops, gently fall."))
            elif k == "resolution":
                if self.p.path == "button":
                    self.parts.append("The button hopped from the crack and stitched the torn blanket closed with a shining thread.")
                    self.parts.append("At dawn, the gingham quilt lay whole, and every child slept warm.")
                elif self.p.path == "moon":
                    self.parts.append("The moon sprang from the pocket, climbed above the roof, and filled every bed with silver light.")
                    self.parts.append("The gingham curtains glowed softly while the children slept beneath the shared moon.")
                else:
                    self.parts.append("The drops danced down the curtains and leaped neatly into a silver pail.")
                    self.parts.append("By morning the gingham curtains were dry, and the nursery smelled of clean rain.")
        return "\n\n".join(self.parts)


ASP_RULES = """
path(button;moon;rain).
valid(button).
valid(moon).
valid(rain).
#show valid/1.
"""


def asp_facts():
    from asp import fact
    return "\n".join(fact("path", p) for p in PATHS)


def verify():
    from asp import atoms, one_model
    model = one_model(asp_facts() + ASP_RULES)
    if set(atoms(model, "valid")) != {(p,) for p in PATHS}:
        raise StoryError("Python and ASP disagree about valid paths.")
    for path in PATHS:
        sample = generate(StoryParams(path=path))
        if not sample.world.outcome or len(sample.story.split()) < 30:
            raise StoryError("A path did not produce a complete story.")
    print("OK: three causal nursery-rhyme paths; ASP parity.")


def generate(p: StoryParams) -> StorySample:
    world = simulate(p)
    story = Teller(world).render()
    qa = list(Teller(world).qa) if False else []
    teller = Teller(world)
    story = teller.render()
    return StorySample(
        params=p,
        story=story,
        prompts=[f"Write a Magic nursery rhyme about {p.hero} in a gingham nursery."],
        story_qa=teller.qa,
        world_qa=[
            QAItem("What kind of cloth appeared in the nursery?",
                   "Blue-and-white gingham appeared in the nursery.")
        ],
        world=world,
    )


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", dest="world_seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--path", choices=PATHS)
    parser.add_argument("--voice", choices=VOICES, default="plain")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args, rng, index=0, sample=False):
    return StoryParams(
        hero=args.hero or (rng.choice(NAMES) if sample else "Nell"),
        path=args.path or (rng.choice(PATHS) if sample else "button"),
        voice=args.voice,
        world_seed=args.world_seed + index,
        prose_seed=args.prose_seed + index,
    )


def emit(sample, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({
            "state": sample.world.state,
            "events": [asdict(e) for e in sample.world.events],
            "outcome": sample.world.outcome,
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
            from asp import atoms, one_model
            print(json.dumps(sorted(atoms(one_model(asp_facts() + ASP_RULES), "valid"))))
            return 0
        rng = random.Random(args.world_seed)
        if args.all:
            params = [
                resolve_params(args, rng, i)
                for i, path in enumerate(PATHS)
                if args.path is None or args.path == path
            ]
            params = [StoryParams(**{**asdict(p), "path": path}) for p, path in zip(params, PATHS)]
        else:
            params = [resolve_params(args, rng, i, sample=args.n > 1)
                      for i in range(args.n)]
        samples = [generate(p) for p in params]
        if args.json:
            rows = [s.to_dict() for s in samples]
            print(json.dumps(rows[0] if len(rows) == 1 else rows,
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
