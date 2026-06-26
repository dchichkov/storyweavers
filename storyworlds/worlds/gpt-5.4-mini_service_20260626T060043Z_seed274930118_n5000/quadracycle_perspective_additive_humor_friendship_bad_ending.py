#!/usr/bin/env python3
"""
A standalone storyworld for a tiny detective-style tale:
a curious friend notices a strange clue, follows changing perspectives,
and learns why a harmless-looking additive led to a bad ending.

Seed premise:
- quadracycle
- perspective
- additive

Story shape:
- setup: friends borrow a quadracycle for a parade
- tension: a colorful additive changes the tire gel / paint and a clue is misread
- turn: a detective-like perspective shift reveals the real cause
- ending: the fix comes too late, but the ending image proves the loss and the friendship
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
    type: str = "child"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class ObjectThing:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the riverside path"
    affords: set[str] = field(default_factory=lambda: {"ride", "inspect"})


@dataclass
class StoryParams:
    place: str = "the riverside path"
    hero: str = "Mina"
    friend: str = "Jae"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.lines = []
        clone.facts = dict(self.facts)
        return clone


def _r_additive(world: World) -> None:
    cart: ObjectThing = world.get("quadracycle")
    if cart.meters.get("additive", 0) >= 1 and cart.meters.get("slippery", 0) < 1:
        cart.meters["slippery"] = 1
        world.say("The wheels had turned slick in a way that did not look dangerous at first.")


def _r_friendship(world: World) -> None:
    hero: Character = world.get("hero")
    friend: Character = world.get("friend")
    if hero.memes.get("worry", 0) >= 1 and friend.memes.get("helping", 0) >= 1:
        hero.memes["trust"] = hero.memes.get("trust", 0) + 1
        friend.memes["trust"] = friend.memes.get("trust", 0) + 1
        world.say("They stayed side by side, because a puzzle was easier with two heads than one.")


def tell(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    hero = world.add(Character(id="hero", type="child", label=params.hero, traits=["curious", "funny"]))
    friend = world.add(Character(id="friend", type="child", label=params.friend, traits=["kind", "brave"]))
    quad = world.add(ObjectThing(
        id="quadracycle",
        type="vehicle",
        label="quadracycle",
        phrase="a bright four-wheeled ride",
        owner=hero.id,
    ))
    clue = world.add(ObjectThing(
        id="clue",
        type="clue",
        label="smear",
        phrase="a shiny smear on the handle",
    ))

    world.say(
        f"{params.hero} and {params.friend} found a quadracycle waiting by {world.setting.place}."
    )
    world.say(
        f"They rode it like a tiny parade machine, laughing at the wind and calling out clues like detectives."
    )
    world.say(
        f"Then a strange smear appeared on the handle, and {params.hero} frowned as if the clue had a secret."
    )

    hero.memes["worry"] = 1
    friend.memes["helping"] = 1
    world.say(
        f"{params.friend} looked from one angle, then another, and said the smear had the shape of a message."
    )

    quad.meters["additive"] = 1
    world.say(
        f"The odd part was an additive someone had poured into the shine, just to make the ride look extra fancy."
    )
    _r_additive(world)

    world.say(
        f"From {params.hero}'s first perspective it looked like sabotage, but the second perspective was simpler: the additive made everything slippery."
    )
    world.say(
        f"They tried to brake, but the quadracycle skidded straight into a paint cart and lost its bell in the puddle."
    )
    world.say(
        f"The detective answer came too late, and the parade rolled away without them; the bad ending was a muddy path, a bent bell, and two friends staring at the quiet wheels."
    )
    _r_friendship(world)

    world.facts.update(
        hero=hero,
        friend=friend,
        quadracycle=quad,
        clue=clue,
        setting=params.place,
        additive=True,
        bad_ending=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].label
    friend = f["friend"].label
    place = f["setting"]
    return [
        f"Write a short detective-style story for children about {hero} and {friend} at {place} with a quadracycle and a strange additive.",
        f"Tell a humorous friendship story where two friends inspect a clue from different perspectives and the ending goes badly.",
        "Write a tiny mystery with a quadracycle, a misleading clue, and a bad ending that still shows the friends caring about each other.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    friend = f["friend"].label
    place = f["setting"]
    return [
        QAItem(
            question=f"Who rode the quadracycle at {place}?",
            answer=f"{hero} and {friend} rode the quadracycle together at {place}."
        ),
        QAItem(
            question="Why did the clue look suspicious at first?",
            answer="It looked suspicious because the shiny smear seemed like a mystery clue, but it was really caused by an additive on the ride."
        ),
        QAItem(
            question="What changed when they used a second perspective?",
            answer="They realized the smear was not sabotage at all; it was the slippery additive that made the quadracycle unsafe."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly, with a muddy path, a bent bell, and the parade leaving them behind."
        ),
        QAItem(
            question="Did the friends stay kind to each other?",
            answer="Yes. Even after the bad ending, they stayed together and worked as a team."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quadracycle?",
            answer="A quadracycle is a four-wheeled bike or ride that people can pedal or push."
        ),
        QAItem(
            question="What does perspective mean?",
            answer="Perspective means the way someone sees or समझ? no. perspective means the way someone sees and understands a situation."
        ),
        QAItem(
            question="What is an additive?",
            answer="An additive is something added to another thing to change how it looks, feels, or works."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if getattr(e, "meters", None):
            bits.append(f"meters={e.meters}")
        if getattr(e, "memes", None):
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style quadracycle storyworld.")
    ap.add_argument("--place", choices=["the riverside path", "the market lane", "the park trail"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(["the riverside path", "the market lane", "the park trail"])
    hero = rng.choice(["Mina", "Toby", "Lila", "Noor", "Evan"])
    friend = rng.choice([n for n in ["Mina", "Toby", "Lila", "Noor", "Evan"] if n != hero])
    return StoryParams(place=place, hero=hero, friend=friend, seed=args.seed)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
#show valid/3.
valid(P,H,F) :- place(P), hero(H), friend(F), H != F.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in ["the_riverside_path", "the_market_lane", "the_park_trail"]:
        lines.append(asp.fact("place", p))
    for h in ["mina", "toby", "lila", "noor", "evan"]:
        lines.append(asp.fact("hero", h))
        lines.append(asp.fact("friend", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    triples = sorted(set(asp.atoms(model, "valid")))
    expected = sorted(
        (p, h, f)
        for p in ["the_riverside_path", "the_market_lane", "the_park_trail"]
        for h in ["mina", "toby", "lila", "noor", "evan"]
        for f in ["mina", "toby", "lila", "noor", "evan"]
        if h != f
    )
    if triples == expected:
        print(f"OK: ASP parity check passed ({len(triples)} combos).")
        return 0
    print("MISMATCH:")
    print("ASP:", triples[:10])
    print("PY :", expected[:10])
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world has a simple ASP twin; use --show-asp or --verify.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        for place in ["the riverside path", "the market lane", "the park trail"]:
            samples.append(generate(StoryParams(place=place, hero="Mina", friend="Jae", seed=base_seed)))
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

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
