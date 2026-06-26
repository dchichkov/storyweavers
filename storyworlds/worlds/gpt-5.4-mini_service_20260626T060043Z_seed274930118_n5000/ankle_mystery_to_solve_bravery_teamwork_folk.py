#!/usr/bin/env python3
"""
A small storyworld about a folk tale mystery: an ankle goes missing in a practical
sense, a brave team searches for it, and the village learns to work together.

The seed inspiration is a gentle folk tale in which a child or a helper notices
a strange ankle problem, the group follows clues, and teamwork resolves the
mystery with a warm ending image.
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
class Character:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str


@dataclass
class Mystery:
    id: str
    clue: str
    hidden: str
    solved_by: str
    at_risk: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero: str
    helper: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    mystery: Mystery
    hero: Character
    helper: Character
    found_clues: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    traces: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def record(self, text: str) -> None:
        self.traces.append(text)


PLACES = {
    "brook": Place(id="brook", label="the brook by the willow"),
    "green": Place(id="green", label="the village green"),
    "barn": Place(id="barn", label="the old barn"),
    "path": Place(id="path", label="the pine path"),
}

MYSTERIES = {
    "missing_shoe": Mystery(
        id="missing_shoe",
        clue="a single muddy print near the steps",
        hidden="the lost shoe was caught under a root",
        solved_by="looking together under the roots and reeds",
        at_risk="shoe",
    ),
    "twisted_ankle": Mystery(
        id="twisted_ankle",
        clue="a careful limp after the dance",
        hidden="the ankle was only sore, not broken",
        solved_by="rest, a cool cloth, and three steady friends",
        at_risk="ankle",
    ),
    "stuck_ankle_brace": Mystery(
        id="stuck_ankle_brace",
        clue="a faint clink from the tall grass",
        hidden="the ankle brace had snagged on a thorny vine",
        solved_by="cutting the vine and guiding one another by lantern light",
        at_risk="ankle",
    ),
}

NAMES = ["Mira", "Eli", "Nia", "Jory", "Lena", "Tobin", "Sage", "Ari"]
KINDS = ["girl", "boy", "child"]
HELPERS = ["grandmother", "grandfather", "sister", "brother", "friend"]

ASP_RULES = r"""
#show valid/2.

valid(Place,Mystery) :- place(Place), mystery(Mystery), clue_match(Place,Mystery).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("at_risk", mid, m.at_risk))
        lines.append(asp.fact("solved_by", mid, m.solved_by))
        lines.append(asp.fact("clue_match", "brook" if "brook" in m.clue else "green", mid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    py = {(p, m) for p in PLACES for m in MYSTERIES if valid_combo(p, m)}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only in python:", sorted(py - cl))
    print("only in ASP:", sorted(cl - py))
    return 1

def valid_combo(place: str, mystery: str) -> bool:
    if place == "barn" and mystery == "twisted_ankle":
        return False
    return True

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale mystery storyworld about an ankle and teamwork.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero")
    ap.add_argument("--helper", choices=HELPERS)
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

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [(p, m) for p in PLACES for m in MYSTERIES if valid_combo(p, m)]
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, mystery = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, mystery=mystery, hero=hero, helper=helper)

def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    hero = Character(id=params.hero, type="child")
    helper = Character(id=params.helper, type=params.helper if params.helper in {"grandmother", "grandfather"} else "person")
    world = World(place=place, mystery=mystery, hero=hero, helper=helper)
    return world

def tell(world: World) -> None:
    h, k, m, p = world.hero, world.helper, world.mystery, world.place
    h.memes["curiosity"] = 1
    h.memes["bravery"] = 1
    k.memes["care"] = 1

    world.say(f"Long ago, in {p.label}, there lived a {h.type} named {h.id} who loved old songs and open lanes.")
    world.say(f"One evening, {h.id} found {m.clue}. That set a little mystery humming in the grass.")
    world.para()
    world.say(f"{h.id} did not turn away. {h.pronoun().capitalize()} called for {k.id}, and together they followed the clue.")
    world.say(f"They listened for small sounds, peered under stones, and held their lantern close, because brave hearts shine brighter when they stay near one another.")
    world.para()
    if m.id == "missing_shoe":
        world.say(f"At last they found the lost shoe tucked under a root, exactly where the brook had nudged it.")
        world.say(f"{h.id} laughed, {k.id} smiled, and the muddy print made sense at last.")
        world.say("They walked home in step, and the village path looked friendlier than before.")
    elif m.id == "twisted_ankle":
        world.say(f"The mystery was gentler than it seemed: {h.id}'s ankle was sore from the dancing, but not broken.")
        world.say(f"{k.id} wrapped it with a cool cloth while the neighbors brought soup and a stool by the fire.")
        world.say("Soon the whole room was quiet and kind, and the brave child rested with a warm lamp beside the bed.")
    else:
        world.say(f"They found the answer in the tall grass: the ankle brace had snagged on a thorny vine.")
        world.say(f"{h.id} held still while {k.id} cut the vine free, and their friends lifted the lantern higher.")
        world.say("With careful hands and shared courage, the group set everything right before the stars came out.")
    world.record(f"solved:{m.id}")

    world.facts.update(place=p, mystery=m, hero=h, helper=k, solved=True)

def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a folk tale for children set at {world.place.label} about a mystery involving an ankle.",
        f"Tell a gentle story where {world.hero.id} is brave and {world.helper.id} helps solve the problem together.",
        "Write a simple teamwork story with a clear clue, a careful search, and a warm ending image.",
    ]

def story_qa(world: World) -> list[QAItem]:
    h, k, m, p = world.hero, world.helper, world.mystery, world.place
    return [
        QAItem(
            question=f"Who is the story about at {p.label}?",
            answer=f"It is about {h.id}, who stays brave, and {k.id}, who helps with the mystery.",
        ),
        QAItem(
            question=f"What clue started the mystery in the story?",
            answer=f"The mystery began with {m.clue}. That clue sent everyone searching together.",
        ),
        QAItem(
            question=f"How did {h.id} and {k.id} solve the problem?",
            answer=f"They solved it by working together: {m.solved_by}. Their teamwork made the answer clear.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an ankle?",
            answer="An ankle is the joint that connects your foot to your leg and helps you walk and run.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means you do something hard or scary even when your heart feels nervous.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help one another and solve a problem together.",
        ),
        QAItem(
            question="Why do people use lanterns at night?",
            answer="People use lanterns at night to shine light on the path so they can see where they are going.",
        ),
    ]

def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)

def dump_trace(world: World) -> str:
    return "\n".join([
        "--- trace ---",
        f"place={world.place.id}",
        f"mystery={world.mystery.id}",
        f"hero={world.hero.id} memes={world.hero.memes}",
        f"helper={world.helper.id} memes={world.helper.memes}",
        f"facts={world.facts}",
    ])

def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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

CURATED = [
    StoryParams(place="brook", mystery="missing_shoe", hero="Mira", helper="grandmother"),
    StoryParams(place="green", mystery="twisted_ankle", hero="Eli", helper="sister"),
    StoryParams(place="path", mystery="stuck_ankle_brace", hero="Nia", helper="friend"),
]

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible combos:")
        for place, mystery in combos:
            print(f"  {place:8} {mystery}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
