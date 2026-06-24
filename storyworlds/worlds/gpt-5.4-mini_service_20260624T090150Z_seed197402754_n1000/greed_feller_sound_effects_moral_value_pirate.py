#!/usr/bin/env python3
"""
A tiny pirate tale storyworld about a greedy feller, loud sound effects, and a
moral-value turn toward sharing.

Seed idea:
---
A greedy feller on a small pirate ship keeps scooping up shiny coin after coin.
He ignores the crew, stuffs treasure into his own bag, and the deck begins to
creak and clatter with every greedy grab. When the bag tears and the coins spill,
the captain shows him that sharing the loot keeps the ship steady and the crew
cheerful.

This script models the story as state:
- physical meters: coins, weight, spills, damage, loudness
- emotional memes: greed, worry, relief, trust, cheer

The story changes based on the world state, not by swapping nouns in a frozen
paragraph. It also includes a small ASP twin for the reasonableness gate.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "feller", "pirate", "sailor", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str = "a little pirate ship"
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    seed: Optional[int] = None
    name: str = "Rufus"
    captain: str = "Captain Mara"


GIRL_NAMES = ["Mira", "Nell", "Polly", "Ruby"]
BOY_NAMES = ["Rufus", "Jeb", "Toby", "Finn"]
CAPTAINS = ["Captain Mara", "Captain Bea", "Captain June", "Captain Vale"]


@dataclass
class Setting:
    place: str
    sound: str
    moral: str


SETTING = Setting(
    place="a little pirate ship",
    sound="creak-clatter",
    moral="sharing makes the whole crew steadier and happier",
)


ASP_RULES = r"""
greedy(feller) :- meme(feller, greed_high).
hoard_risk(feller) :- greedy(feller), meter(feller, bag_weight, W), W > 2.
spill(feller) :- hoard_risk(feller), meter(feller, bag_ripped, 1).
moral_turn(feller) :- spill(feller), meme(captain, trust_high).
valid_story :- greedy(feller), moral_turn(feller).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("character", "feller"))
    lines.append(asp.fact("character", "captain"))
    lines.append(asp.fact("meme", "feller", "greed_high"))
    lines.append(asp.fact("meme", "captain", "trust_high"))
    lines.append(asp.fact("meter", "feller", "bag_weight", 3))
    lines.append(asp.fact("meter", "feller", "bag_ripped", 1))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    has = any(sym.name == "valid_story" for sym in model)
    if has:
        print("OK: ASP gate accepts the greedy-feller moral story.")
        return 0
    print("MISMATCH: ASP gate did not derive valid_story.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld about greed and a moral turn.")
    ap.add_argument("--name")
    ap.add_argument("--captain")
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
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(BOY_NAMES + GIRL_NAMES),
        captain=args.captain or rng.choice(CAPTAINS),
    )


def _init_world(params: StoryParams) -> World:
    w = World(place=SETTING.place)
    feller = w.add(Entity(
        id="feller",
        kind="character",
        type="feller",
        label="greedy feller",
        meters={"coins": 0.0, "bag_weight": 0.0, "spill": 0.0, "noise": 0.0},
        memes={"greed": 0.0, "worry": 0.0, "relief": 0.0, "cheer": 0.0},
    ))
    captain = w.add(Entity(
        id="captain",
        kind="character",
        type="captain",
        label=params.captain,
        meters={"trust": 0.0},
        memes={"patience": 0.0, "trust": 1.0},
    ))
    chest = w.add(Entity(
        id="chest",
        kind="thing",
        type="chest",
        label="treasure chest",
        plural=False,
        meters={"coins": 6.0},
    ))
    bag = w.add(Entity(
        id="bag",
        kind="thing",
        type="bag",
        label="canvas bag",
        plural=False,
        owner="feller",
        meters={"capacity": 3.0, "damage": 0.0},
    ))
    w.facts.update(feller=feller, captain=captain, chest=chest, bag=bag)
    return w


def _sound(world: World, text: str) -> None:
    world.say(f"Sound effects went {text}.")


def generate_story(world: World, params: StoryParams) -> None:
    feller = world.get("feller")
    captain = world.get("captain")
    chest = world.get("chest")
    bag = world.get("bag")

    world.say(
        f"On {world.place}, there was a greedy feller named {params.name}. "
        f"{params.name} loved shiny treasure and dreamed of keeping it all."
    )
    world.say(
        f"{params.captain} watched the deck and said the best treasure was a fair share for every matey."
    )
    world.para()
    world.say(
        f"One bright day, the chest was opened, and {params.name} scooped up coin after coin."
    )
    feller.memes["greed"] += 2
    feller.meters["coins"] += 4
    feller.meters["bag_weight"] += 4
    feller.meters["noise"] += 1
    _sound(world, "clink-clink and jingle-jangle")
    world.say(
        f"The canvas bag grew heavy, and {params.name} hugged it tighter and tighter."
    )
    world.say(
        f"The more {params.name} grabbed, the more the deck answered with a worried {SETTING.sound}."
    )
    world.para()
    world.say(
        f"Then the stitches gave way with a sharp rip!"
    )
    bag.meters["damage"] += 1
    bag.meters["coins"] = 0
    feller.meters["spill"] += 3
    feller.memes["worry"] += 2
    _sound(world, "rrrrrip and plink-plink-plink")
    world.say(
        f"Coins rolled across the boards and tapped against the boots of the crew."
    )
    world.say(
        f"{params.captain} did not scold. Instead, {params.captain.lower()} pointed to the scattered coins and said, "
        f'"A greedy hand drops more than it keeps."'
    )
    world.para()
    feller.memes["greed"] = 0
    feller.memes["relief"] += 2
    feller.memes["cheer"] += 2
    captain.memes["trust"] += 1
    world.say(
        f"{params.name} blinked, then gathered the treasure and began sharing the coins one by one."
    )
    world.say(
        f"This time the deck sounded soft and happy, with only a gentle {SETTING.sound} under the moon."
    )
    world.say(
        f"By the end, {params.name} had less in the bag but more friends at the rail, and {params.captain} smiled at the steady little ship."
    )
    world.facts.update(moral=SETTING.moral)


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short pirate tale for a young child about greed, a noisy treasure spill, and a moral turn.',
        'Tell a gentle story where a greedy feller hears creak-clatter on a pirate ship and learns to share.',
        'Write a simple pirate story with sound effects and an ending that shows sharing is better than hoarding.',
    ]


def story_qa(world: World) -> list[QAItem]:
    feller = world.get("feller")
    captain = world.get("captain")
    name = world.facts.get("name", "the feller")
    return [
        QAItem(
            question="Who was the greedy feller in the story?",
            answer=f"The greedy feller was {name}. He wanted to keep all the treasure for himself at first.",
        ),
        QAItem(
            question="What sound did the pirate ship make when the bag got too full?",
            answer=f"The ship made a worried {SETTING.sound} sound, and then the bag ripped with a sharp burst.",
        ),
        QAItem(
            question="What lesson did the captain want the feller to learn?",
            answer=f"{captain.label} wanted him to learn that {SETTING.moral}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is greed?",
            answer="Greed is wanting too much for yourself and not wanting to share.",
        ),
        QAItem(
            question="Why are sound effects used in stories?",
            answer="Sound effects help readers hear the action in their minds, like clink-clink, creak, or rip.",
        ),
        QAItem(
            question="What is a moral in a story?",
            answer="A moral is the lesson a story wants to teach, such as being kind, fair, or generous.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _init_world(params)
    world.facts["name"] = params.name
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid() -> bool:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    return any(sym.name == "valid_story" for sym in model)


CURATED = [
    StoryParams(name="Rufus", captain="Captain Mara"),
    StoryParams(name="Mira", captain="Captain Bea"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP reasonableness:", "ok" if asp_valid() else "failed")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
