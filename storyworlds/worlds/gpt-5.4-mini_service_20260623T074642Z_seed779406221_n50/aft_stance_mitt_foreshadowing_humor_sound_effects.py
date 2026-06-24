#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50/aft_stance_mitt_foreshadowing_humor_sound_effects.py
===============================================================================================================

A small pirate-tale storyworld about a deckhand, a tricky stance, and a mitt.
The world is state-driven: the ship, wind, tack, deck footing, and crew moods
shape the prose. The named narrative instruments are used as follows:

- Foreshadowing: the captain notices clues in the sea and the deck
- Humor: a playful misunderstanding about a mitt and a stance
- Sound Effects: splashy, creaky, breezy onomatopoeia woven into prose

Seed words included in the domain: aft, stance, mitt.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    ship: str
    hero: str
    mate: str
    cargo: str
    weather: str
    problem: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def bump(self, key: str, amt: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amt

    def feel(self, key: str, amt: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amt


@dataclass
class Ship:
    name: str
    aft: str
    deck: Entity = field(default_factory=lambda: Entity("deck", label="deck"))
    sea: Entity = field(default_factory=lambda: Entity("sea", label="sea"))
    crew: dict[str, Entity] = field(default_factory=dict)
    cargo: Entity = field(default_factory=lambda: Entity("cargo", label="cargo"))
    history: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.history.append(text)

    def render(self) -> str:
        return " ".join(self.history)


SHIPS = {
    "Sea Sprat": {"aft": "the aft rail"},
    "Merry Gull": {"aft": "the aft deck"},
    "Salt Lantern": {"aft": "the aft hatch"},
}

HEROES = [
    ("Ned", "deckhand"),
    ("Mira", "deckhand"),
    ("Jory", "mate"),
    ("Pip", "sailor"),
]

MATES = ["Captain Bram", "First Mate Sella", "Old Finn", "Mate Hobb"]
CARGOES = [
    ("mitt", "a wool mitt"),
    ("mitt", "a patched mitt"),
    ("mitt", "a tiny mitt"),
]
WEATHERS = ["breezy", "foggy", "spray-splashed"]
PROBLEMS = [
    "the rope ladder slipping near the aft",
    "a crate sliding by the aft rail",
    "the mitt getting blown toward the aft hatch",
]


class World:
    def __init__(self, params: StoryParams) -> None:
        ship_info = SHIPS[params.ship]
        self.params = params
        self.ship = Ship(name=params.ship, aft=ship_info["aft"])
        self.hero = Entity(params.hero, kind="character", label=params.hero, phrase="the hero")
        self.mate = Entity(params.mate, kind="character", label=params.mate, phrase="the mate")
        self.cargo = Entity("mitt", label="mitt", phrase=params.cargo)
        self.ship.crew[self.hero.id] = self.hero
        self.ship.crew[self.mate.id] = self.mate
        self.ship.cargo = self.cargo
        self.deck = self.ship.deck
        self.sea = self.ship.sea
        self.sound_log: list[str] = []
        self.foreshadow = False
        self.resolved = False

    def sound(self, s: str) -> None:
        self.sound_log.append(s)
        self.ship.say(s)

    def trace(self) -> str:
        parts = [
            f"ship={self.ship.name}",
            f"aft={self.ship.aft}",
            f"deck={self.deck.meters}",
            f"sea={self.sea.meters}",
            f"hero={self.hero.memes}",
            f"mate={self.mate.memes}",
            f"cargo={self.cargo.meters}",
            f"foreshadow={self.foreshadow}",
            f"resolved={self.resolved}",
        ]
        return "\n".join(parts)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with aft, stance, and mitt.")
    ap.add_argument("--ship", choices=sorted(SHIPS))
    ap.add_argument("--hero", choices=sorted({h for h, _ in HEROES}))
    ap.add_argument("--mate", choices=MATES)
    ap.add_argument("--cargo", choices=["mitt"])
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    ship = args.ship or rng.choice(sorted(SHIPS))
    hero = args.hero or rng.choice([h for h, _ in HEROES])
    mate = args.mate or rng.choice(MATES)
    cargo = args.cargo or "a wool mitt"
    weather = args.weather or rng.choice(WEATHERS)
    problem = args.problem or rng.choice(PROBLEMS)
    if args.hero == "Pip" and "mitt" not in cargo:
        raise StoryError("This pirate tale needs the mitt to matter.")
    return StoryParams(ship=ship, hero=hero, mate=mate, cargo=cargo, weather=weather, problem=problem)


def intro(world: World) -> None:
    p = world.params
    world.ship.say(f"On the {p.ship}, {p.hero} watched the aft line and kept a brave stance.")
    world.ship.say(f"The wind went whooosh and the boards gave a creak-creak underfoot.")
    world.ship.say(f"{p.hero} liked the {p.cargo}, because it fit one hand like a silly treasure.")
    world.ship.say(f"That was handy, though it also looked like a mitten for a mouse.")


def foreshadow(world: World) -> None:
    p = world.params
    world.foreshadow = True
    world.deck.bump("slick", 1)
    world.ship.say(f"A gull cried caw-caw over the aft, and the captain squinted at the clouds.")
    world.ship.say(f"'That breeze means trouble aft,' said {p.mate}, and the rope answered with a soft twang.")
    world.ship.say(f"The hint came early, like a drumbeat before rain, and nobody laughed yet.")


def problem_turn(world: World) -> None:
    p = world.params
    world.hero.feel("worry", 1)
    world.mate.feel("worry", 1)
    world.ship.say(f"Then {p.problem}, and the deck went skrrt as boots slid.")
    world.ship.say(f"{p.hero} tried a wide stance, but the awkward mitt made the balance wobble.")
    world.ship.say(f"'Hold fast!' cried {p.mate}, and the sea gave a splash-splash below the hull.")
    world.ship.say(f"For one bumpy blink, the aft felt as if it might swallow the whole joke.")


def humorous_fix(world: World) -> None:
    p = world.params
    world.hero.feel("brave", 1)
    world.mate.feel("amused", 1)
    world.ship.say(f"{p.mate} laughed, 'Not that stance, matey! I meant a steady stance, not a fancy dance.'")
    world.ship.say(f"{p.hero} blinked, then grinned. 'Oh! I thought ye wanted the mitt to lead the march.'")
    world.ship.say(f"Har-har went the crew, and even the mast seemed to chuckle in the wind.")
    world.ship.say(f"Together they shifted the cargo aft and tied it down with a snug knot, tug-tug.")


def resolution(world: World) -> None:
    p = world.params
    world.resolved = True
    world.deck.bump("secure", 1)
    world.cargo.bump("safe", 1)
    world.ship.say(f"The crate stayed put, the mitt stayed dry, and the aft was calm again.")
    world.ship.say(f"{p.hero} stood tall with a proper stance, mitt in hand, and the sea only whispered.")
    world.ship.say(f"By supper, the captain called it a tidy save: one clue, one laugh, and one safe deck.")


def generate_story(world: World) -> None:
    intro(world)
    world.ship.say("")
    foreshadow(world)
    world.ship.say("")
    problem_turn(world)
    world.ship.say("")
    humorous_fix(world)
    world.ship.say("")
    resolution(world)


def generate(params: StoryParams) -> StorySample:
    world = World(params)
    generate_story(world)
    hero_role = "deckhand" if params.hero in {"Ned", "Mira"} else "sailor"
    prompts = [
        "Write a short pirate tale about a crew member, an aft deck problem, and a funny fix.",
        f"Tell a child-friendly story where {params.hero} keeps a mitt near the aft and learns a lesson.",
        "Make the story include foreshadowing, humor, and sound effects on a ship at sea.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did the crew worry when the problem reached the aft?",
            answer=f"They worried because {params.problem.lower()} and the deck became slippery near the aft, so someone could lose balance.",
        ),
        QAItem(
            question=f"What did {params.hero} think the mate meant by stance?",
            answer=f"{params.hero} first thought the mate meant a funny dance, but the mate really meant a steady way to stand.",
        ),
        QAItem(
            question=f"What happened to the mitt at the end?",
            answer=f"The mitt stayed dry and safe after the crew tied down the cargo and kept it secure aft.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is the aft of a ship?",
            answer="The aft is the back part of a ship.",
        ),
        QAItem(
            question="What is a stance?",
            answer="A stance is the way someone stands with their feet and body, especially to keep balance.",
        ),
        QAItem(
            question="What is a mitt?",
            answer="A mitt is a soft hand covering like a glove, often used to keep a hand warm.",
        ),
    ]
    return StorySample(params=params, story=world.ship.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


ASP_RULES = r"""
aft_problem(X) :- problem(X), mentions_aft(X).
safe_end(X) :- aft_problem(X), tied_down(X), steady_stance(X).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for ship in SHIPS:
        lines.append(asp.fact("ship", ship))
    lines.append(asp.fact("word", "aft"))
    lines.append(asp.fact("word", "stance"))
    lines.append(asp.fact("word", "mitt"))
    lines.append(asp.fact("feature", "foreshadowing"))
    lines.append(asp.fact("feature", "humor"))
    lines.append(asp.fact("feature", "sound_effects"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        print(sample.world.trace())
    if qa:
        print("\n--- qa ---")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


CURATED = [
    StoryParams(ship="Sea Sprat", hero="Ned", mate="Captain Bram", cargo="a wool mitt", weather="breezy", problem="the rope ladder slipping near the aft"),
    StoryParams(ship="Merry Gull", hero="Mira", mate="First Mate Sella", cargo="a patched mitt", weather="foggy", problem="a crate sliding by the aft rail"),
    StoryParams(ship="Salt Lantern", hero="Jory", mate="Old Finn", cargo="a tiny mitt", weather="spray-splashed", problem="the mitt getting blown toward the aft hatch"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe_end/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show safe_end/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(json.dumps([s.to_dict() for s in samples] if len(samples) > 1 else samples[0].to_dict(), indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
