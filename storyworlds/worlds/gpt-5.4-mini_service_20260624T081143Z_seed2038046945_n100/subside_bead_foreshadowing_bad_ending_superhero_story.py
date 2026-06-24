#!/usr/bin/env python3
"""
Standalone storyworld: a superhero tale with foreshadowing, a tiny bead, and a
bad ending where the danger does not fully go away.

The world model tracks physical state in meters and emotional state in memes.
The simulated plot is small and classical:
- setup: introduce hero, city, omen
- foreshadowing: a tiny bead hints that something is wrong
- tension: danger rises and the hero tries to stop it
- ending: the danger only partly subsides, and the bad ending lands

This script is intentionally self-contained and uses only stdlib plus the shared
Storyweavers result containers. ASP support is inline via ASP_RULES and the
shared storyworlds/asp.py helper, imported lazily.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Hero:
    id: str
    role: str = "superhero"
    pronoun_subj: str = "they"
    pronoun_obj: str = "them"
    pronoun_poss: str = "their"
    meters: dict[str, float] = field(default_factory=lambda: {"energy": 6.0, "threat": 0.0, "damage": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"hope": 3.0, "worry": 0.0, "bravery": 2.0})


@dataclass
class Place:
    name: str
    kind: str = "city"
    meters: dict[str, float] = field(default_factory=lambda: {"storm": 0.0, "noise": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"calm": 2.0, "fear": 0.0})


@dataclass
class Thing:
    id: str
    label: str
    kind: str = "thing"
    meters: dict[str, float] = field(default_factory=lambda: {"glow": 0.0, "crack": 0.0, "dust": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"mystery": 0.0})


@dataclass
class World:
    hero: Hero
    place: Place
    bead: Thing
    villain: Thing
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    city: str
    hero_name: str
    villain_name: str
    seed: Optional[int] = None


CITIES = ["Bright Harbor", "Maple City", "Skyline Bay", "Pine Square"]
HERO_NAMES = ["Nova", "Mira", "Jet", "Luna", "Ari", "Kite"]
VILLAIN_NAMES = ["Smog King", "Captain Crackle", "The Gray Shadow", "Doctor Gloom"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with foreshadowing and a bad ending.")
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--villain", choices=VILLAIN_NAMES)
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
    city = args.city or rng.choice(CITIES)
    name = args.name or rng.choice(HERO_NAMES)
    villain = args.villain or rng.choice(VILLAIN_NAMES)
    return StoryParams(city=city, hero_name=name, villain_name=villain)


def _tick_foreshadowing(world: World) -> None:
    if ("foreshadow",) in world.fired:
        return
    world.fired.add(("foreshadow",))
    world.bead.meters["glow"] += 1
    world.bead.memes["mystery"] += 2
    world.place.meters["storm"] += 1
    world.say(
        f"In {world.place.name}, a tiny bead on the rooftop lantern began to glow, "
        f"as if it knew a storm was coming."
    )


def _tick_threat(world: World) -> None:
    if ("threat",) in world.fired:
        return
    world.fired.add(("threat",))
    world.hero.meters["threat"] += 2
    world.hero.memes["worry"] += 1
    world.place.meters["noise"] += 1
    world.say(
        f"{world.hero.id} saw the bead shine and felt a chill, because the bead had "
        f"been a warning all along."
    )
    world.say(
        f"Then {world.villain.id} swept into the square and wrapped the towers in gray dust."
    )


def _tick_battle(world: World) -> None:
    if ("battle",) in world.fired:
        return
    world.fired.add(("battle",))
    world.hero.meters["energy"] -= 4
    world.villain.meters["dust"] += 2
    world.place.memes["fear"] += 2
    world.say(
        f"{world.hero.id} flew up, threw a bright shield, and pushed hard until the gray dust "
        f"started to subside."
    )


def _tick_bad_ending(world: World) -> None:
    if ("ending",) in world.fired:
        return
    world.fired.add(("ending",))
    world.hero.meters["energy"] = max(0.0, world.hero.meters["energy"] - 2)
    world.bead.meters["crack"] += 1
    world.place.meters["storm"] += 1
    world.place.memes["calm"] = max(0.0, world.place.memes["calm"] - 2)
    world.say(
        f"But the storm only partly subsided. The bead cracked, the sky stayed dark, and "
        f"{world.hero.id} could not chase the last shadow away."
    )
    world.say(
        f"By nightfall, {world.place.name} was still messy, and the city learned that even a hero "
        f"cannot fix everything in one day."
    )


def simulate(world: World) -> None:
    world.say(
        f"{world.hero.id} was a superhero in {world.place.name}, and {world.hero.id} always listened "
        f"for signs that trouble was near."
    )
    world.say(
        f"One afternoon, a single bead on the old rooftop lantern shimmered strangely, and that was "
        f"the first foreshadowing."
    )
    world.para()
    _tick_foreshadowing(world)
    _tick_threat(world)
    _tick_battle(world)
    _tick_bad_ending(world)
    world.facts.update(
        city=world.place.name,
        hero=world.hero.id,
        villain=world.villain.label,
        bead_glow=world.bead.meters["glow"],
        bead_crack=world.bead.meters["crack"],
        storm=world.place.meters["storm"],
        threat=world.hero.meters["threat"],
        energy=world.hero.meters["energy"],
    )


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"Who was the story about in {world.place.name}?",
            answer=f"It was about {world.hero.id}, a superhero who tried to protect {world.place.name}.",
        ),
        QAItem(
            question="What did the tiny bead do before the trouble got worse?",
            answer="It glowed like a warning, so it foreshadowed that something bad was coming.",
        ),
        QAItem(
            question="Did the danger go away at the end?",
            answer="No. The danger only partly subsided, and the ending stayed bad because the city was still hurt.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue early in a story that hints something important will happen later.",
        ),
        QAItem(
            question="What does it mean when something subsides?",
            answer="When something subsides, it becomes smaller, weaker, or less intense.",
        ),
        QAItem(
            question="What is a bead?",
            answer="A bead is a tiny small object, often round, that can be strung or used as decoration.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a superhero story set in {world.place.name} that uses a glowing bead as foreshadowing.",
        "Tell a short tale where a hero notices a tiny clue, fights a villain, and the ending is bad.",
        "Make the danger subside only a little, then leave the city with a bittersweet or unhappy finish.",
    ]


ASP_RULES = r"""
hero(H).
place(P).
bead(B).

foreshadows(B) :- bead(B), bead_glow(B), bead_crack(B,0).
threatens(H) :- hero(H), threat_level(H,N), N > 0.
subsides(P) :- place(P), storm(P,S), S < 3.
bad_ending :- threatens(_), not fully_safe.

fully_safe :- subsides(_), calm(_), no_cracks.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name in HERO_NAMES:
        lines.append(asp.fact("hero", name))
    for city in CITIES:
        lines.append(asp.fact("place", city))
    lines.append(asp.fact("bead", "bead"))
    lines.append(asp.fact("threat_level", "hero", 1))
    lines.append(asp.fact("storm", "city", 2))
    lines.append(asp.fact("calm", "city", 1))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show foreshadows/1. #show bad_ending/0.")
    model = asp.one_model(program)
    atoms = {a.name for a in model}
    if "bad_ending" in atoms:
        print("OK: ASP program encodes a bad ending.")
        return 0
    print("MISMATCH: ASP program did not derive bad_ending.")
    return 1


def tell(params: StoryParams) -> World:
    world = World(
        hero=Hero(id=params.hero_name),
        place=Place(name=params.city),
        bead=Thing(id="bead", label="bead"),
        villain=Thing(id="villain", label=params.villain_name),
    )
    simulate(world)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        w = sample.world
        print(f"hero={w.hero.id} energy={w.hero.meters['energy']} threat={w.hero.meters['threat']}")
        print(f"bead glow={w.bead.meters['glow']} crack={w.bead.meters['crack']}")
        print(f"storm={w.place.meters['storm']} fear={w.place.memes['fear']}")
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        for item in sample.story_qa + sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show foreshadows/1. #show bad_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(city="Bright Harbor", hero_name="Nova", villain_name="Smog King"),
            StoryParams(city="Maple City", hero_name="Mira", villain_name="Captain Crackle"),
            StoryParams(city="Skyline Bay", hero_name="Jet", villain_name="The Gray Shadow"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
