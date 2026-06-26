#!/usr/bin/env python3
"""
A small standalone story world for a Space Adventure-style tale about a
crew that meets a strange thorn-like foil object, gets a surprise, and ends
with reconciliation through a little magic.
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pilot", "engineer", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str = "the little starship"
    setting: str = "deep space"
    surprise: str = "a glowing surprise"
    magic: str = "soft magic"
    reconciliation: str = "a kind apology"
    obstacle: str = "a thorn-like foil shard"


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

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
    captain: str
    companion: str
    ship_name: str
    place: str
    seed: Optional[int] = None


CAPTAIN_NAMES = ["Nova", "Mira", "Ari", "Zia", "Lena", "Tess"]
COMPANION_NAMES = ["Pip", "Bo", "Jax", "Rua", "Tavi", "Kio"]
PLACES = [
    "the quiet moon field",
    "the blue comet tunnel",
    "the ringed-planet orbit",
    "the lantern asteroid",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld with surprise, reconciliation, and magic.")
    ap.add_argument("--captain", choices=CAPTAIN_NAMES)
    ap.add_argument("--companion", choices=COMPANION_NAMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ship-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("theme", "space"),
        asp.fact("feature", "surprise"),
        asp.fact("feature", "reconciliation"),
        asp.fact("feature", "magic"),
        asp.fact("word", "thorn"),
        asp.fact("word", "like"),
        asp.fact("word", "foil"),
        asp.fact("obstacle", "thorn_like_foil"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
#show feature/1.
#show word/1.
#show obstacle/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show feature/1.")
    model = asp.one_model(program)
    feats = sorted(set(asp.atoms(model, "feature")))
    wanted = [("magic",), ("reconciliation",), ("surprise",)]
    if sorted(feats) == wanted:
        print("OK: ASP facts include the required features.")
        return 0
    print("MISMATCH: ASP feature facts are wrong.")
    print(feats)
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    companion = args.companion or rng.choice([n for n in COMPANION_NAMES if n != captain])
    place = args.place or rng.choice(PLACES)
    ship_name = args.ship_name or rng.choice(["Star Finch", "Silver Comet", "Moon Ripple", "Bright Loop"])
    return StoryParams(captain=captain, companion=companion, ship_name=ship_name, place=place)


def generate(params: StoryParams) -> StorySample:
    ship = Ship(name=params.ship_name, setting=params.place)
    world = World(ship)

    captain = world.add(Entity(
        id=params.captain,
        kind="character",
        type="captain",
        label="captain",
        phrase=f"Captain {params.captain}",
        location="bridge",
        traits=["brave", "curious"],
    ))
    companion = world.add(Entity(
        id=params.companion,
        kind="character",
        type="engineer",
        label="shipmate",
        phrase=f"{params.companion}",
        location="engine room",
        traits=["quick", "gentle"],
    ))
    shard = world.add(Entity(
        id="shard",
        kind="thing",
        type="artifact",
        label="thorn-like foil shard",
        phrase="a thorn-like foil shard",
        location="outside the hull",
        meters={"gleam": 1.0, "sharpness": 1.0},
        memes={"mystery": 1.0},
    ))
    world.facts.update(captain=captain, companion=companion, shard=shard, params=params)

    world.say(
        f"Captain {captain.id} guided {ship.name} through {ship.setting}, where the stars looked close enough to touch."
    )
    world.say(
        f"Then the scanners blinked at {ship.obstacle}, a strange thing that looked thorn like foil and shimmered with {ship.surprise}."
    )

    world.para()
    world.say(
        f"{companion.id} reached for the controls too fast, wanting to pull the ship away at once."
    )
    world.say(
        f"But the shard sang against the hull, and the song sounded almost like a warning."
    )
    world.say(
        f"Captain {captain.id} felt a pinch of worry, because the strange glow could hide a trap."
    )

    world.para()
    world.say(
        f"Instead of blasting it, {captain.id} floated closer with a lantern glove and spoke softly to the shining thing."
    )
    world.say(
        f"The glove held a little {ship.magic}, and the light turned warm instead of wild."
    )
    world.say(
        f"Inside the glow, they found not a weapon but a lost map-sprite, surprised and blinking."
    )

    world.para()
    world.say(
        f"{companion.id} apologized for rushing, and {captain.id} smiled back without fuss."
    )
    world.say(
        f"Together they used the {ship.magic} to open a tiny path, and the map-sprite led them safely past the shard."
    )
    world.say(
        f"By the time {ship.name} drifted onward, the surprise had become reconciliation, and the dark void felt friendly again."
    )

    world.facts["story_end"] = "reconciled"
    world.facts["magic_used"] = True
    world.facts["surprise"] = True

    prompts = [
        f"Write a short Space Adventure story about a captain named {params.captain} who finds a thorn-like foil shard.",
        f"Tell a gentle spaceship story where surprise turns into reconciliation with magic.",
        f"Write a child-friendly tale about a starship crew, a strange shiny object, and a kind ending.",
    ]
    story_qa = [
        QAItem(
            question=f"What did Captain {params.captain} find in space?",
            answer="Captain " + params.captain + " found a thorn-like foil shard that shimmered with surprise.",
        ),
        QAItem(
            question=f"How did the crew solve the problem?",
            answer=f"They used soft magic, spoke kindly, and turned fear into reconciliation.",
        ),
        QAItem(
            question=f"Why did {params.companion} feel sorry?",
            answer=f"{params.companion} felt sorry for rushing at the strange shard before understanding it.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is surprise in a story like this?",
            answer="Surprise is when something unexpected appears and changes what the characters do next.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after worry or disagreement.",
        ),
        QAItem(
            question="What can magic do in a Space Adventure tale?",
            answer="Magic can help characters understand strange things, calm danger, and solve a problem kindly.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            bits = []
            if e.location:
                bits.append(f"location={e.location}")
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            print(f"  {e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show obstacle/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Nova", "Pip", "Star Finch", "the quiet moon field"),
            StoryParams("Mira", "Bo", "Silver Comet", "the blue comet tunnel"),
            StoryParams("Ari", "Jax", "Moon Ripple", "the ringed-planet orbit"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.captain} and {p.companion} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
