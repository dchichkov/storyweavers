#!/usr/bin/env python3
"""
storyworlds/worlds/marble_account_ganache_bravery_whodunit.py
=============================================================

A small whodunit-style story world about a missing marble, a careful account,
and a cake with ganache on top.

Premise:
- A child notices something small is missing.
- A mistaken guess creates tension.
- A brave account of what was seen reveals the truth.
- The ending proves the hidden object was found and the story is settled.

The prose is driven by a tiny simulated world with meters and memes:
- physical meters: where objects are, whether something is hidden, whether a
  clue has been handled, whether a treat is missing.
- emotional memes: worry, suspicion, bravery, relief, trust.

The story style is meant to feel close to a gentle whodunit: concrete clues,
a small mystery, a careful reveal, and a satisfying ending image.
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

TARGET_SETTING = "the kitchen"
DEFAULT_SEED = 274930118

NAMES = ["Mina", "Toby", "Lena", "Arlo", "June", "Pip", "Nora", "Theo"]
ADULTS = ["mom", "dad", "grandma", "uncle"]
TRAITS = ["curious", "careful", "brave", "quiet", "sharp-eyed", "kind"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden_in: Optional[str] = None
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mom", "grandma"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "dad", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = TARGET_SETTING
    features: set[str] = field(default_factory=lambda: {"table", "stool", "pan", "tray"})


@dataclass
class StoryParams:
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _init_world(params: StoryParams) -> World:
    world = World(Setting())
    hero_type = "girl" if params.gender == "girl" else "boy"
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=hero_type,
        label=params.name,
        meters={"worry": 0.0},
        memes={"bravery": 0.0, "relief": 0.0, "trust": 0.0},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=params.adult,
        label=f"the {params.adult}",
        meters={"worry": 0.0},
        memes={"suspicion": 0.0, "relief": 0.0},
    ))
    marble = world.add(Entity(
        id="Marble",
        kind="thing",
        type="marble",
        label="marble",
        phrase="a small blue marble",
        owner=hero.id,
        hidden_in="ganache",
        found=False,
        meters={"hidden": 1.0},
    ))
    account = world.add(Entity(
        id="Account",
        kind="thing",
        type="account",
        label="account",
        phrase="a careful account of what happened",
        owner=hero.id,
        meters={"written": 1.0},
    ))
    ganache = world.add(Entity(
        id="Ganache",
        kind="thing",
        type="ganache",
        label="ganache",
        phrase="a glossy bowl of ganache",
        meters={"dark": 1.0, "sticky": 1.0},
    ))
    world.facts.update(hero=hero, adult=adult, marble=marble, account=account, ganache=ganache)
    return world


def _prove_hidden(world: World) -> None:
    hero: Entity = world.facts["hero"]
    adult: Entity = world.facts["adult"]
    marble: Entity = world.facts["marble"]
    account: Entity = world.facts["account"]
    ganache: Entity = world.facts["ganache"]

    world.say(f"{hero.id} was a {hero.id.lower() if False else ''}")
    world.paragraphs[-1].pop()  # no-op; preserve structure without stray text


def tell(world: World) -> World:
    hero: Entity = world.facts["hero"]
    adult: Entity = world.facts["adult"]
    marble: Entity = world.facts["marble"]
    account: Entity = world.facts["account"]
    ganache: Entity = world.facts["ganache"]

    # Act 1: setup
    world.say(
        f"{hero.id} was a little {next((t for t in hero.memes.keys() if False), '')}".strip()
    )
    intro = f"{hero.id} was a {hero.type} who liked quiet clues and careful looks around {world.setting.place}."
    world.say(intro)
    world.say(
        f"One afternoon, {hero.id} made a careful account of the things on the table: a spoon, a tray, and {ganache.phrase}."
    )
    world.say(
        f"Near the bowl sat {marble.phrase}, shiny and bright. {hero.id} liked it best of all."
    )

    # Act 2: mystery
    world.para()
    hero.meters["worry"] += 1
    adult.meters["worry"] += 1
    adult.memes["suspicion"] += 1
    world.say(
        f"Then {hero.id} looked again, and the marble was gone."
    )
    world.say(
        f"{hero.id} felt a small twist of worry. {hero.pronoun('possessive').capitalize()} {adult.label} said, "
        f'"Who moved it?" and peered at the sticky ganache.'
    )
    world.say(
        f"For a moment, it seemed as if the ganache had swallowed the clue."
    )
    world.say(
        f"{hero.id} looked at the account again and remembered seeing the marble on the edge of the tray."
    )

    # Act 3: bravery and reveal
    world.para()
    hero.memes["bravery"] += 1
    hero.memes["trust"] += 1
    adult.memes["suspicion"] = max(0.0, adult.memes["suspicion"] - 1.0)
    world.say(
        f"{hero.id} took a brave breath and told the whole account out loud."
    )
    world.say(
        f"'{hero.id} saw the marble roll,' {hero.pronoun('subject')} said, 'and it slipped under the napkin before the ganache went on top.'"
    )
    marble.hidden_in = "napkin"
    marble.found = True
    world.say(
        f"{hero.id} lifted the napkin, and there it was: the marble, safe and clean."
    )
    hero.meters["worry"] = 0.0
    adult.meters["worry"] = 0.0
    adult.memes["relief"] += 1
    hero.memes["relief"] += 1
    world.say(
        f"{hero.id}'s {adult.label} smiled and laughed softly. The mystery was solved, and the ganache stayed right where it belonged."
    )

    world.facts.update(resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    return [
        f"Write a gentle whodunit for a child named {hero.id} that includes a marble, an account, and ganache.",
        f"Tell a short mystery story where {hero.id} uses a careful account to find a missing marble.",
        f"Write a small brave mystery set in a kitchen with ganache and a lost marble.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    adult: Entity = world.facts["adult"]
    marble: Entity = world.facts["marble"]
    account: Entity = world.facts["account"]
    ganache: Entity = world.facts["ganache"]
    return [
        QAItem(
            question=f"What mystery did {hero.id} have to solve in the kitchen?",
            answer=f"{hero.id} had to solve the mystery of the missing marble near the ganache.",
        ),
        QAItem(
            question=f"What did {hero.id} use to remember the clue?",
            answer=f"{hero.id} used a careful account of what had been seen on the table.",
        ),
        QAItem(
            question=f"How did the story end after {hero.id} showed bravery?",
            answer=f"{hero.id} found the marble hiding under the napkin, and the adults felt relieved.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a marble?",
            answer="A marble is a small hard ball, often made of glass or stone, that can roll easily.",
        ),
        QAItem(
            question="What is an account?",
            answer="An account is a careful telling of what happened, often in order from beginning to end.",
        ),
        QAItem(
            question="What is ganache?",
            answer="Ganache is a smooth, shiny chocolate mixture used on cakes and sweets.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is the feeling that helps someone speak up or do the right thing even when they feel nervous.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.found:
            bits.append("found=True")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
entity(hero;adult;marble;account;ganache).
missing(X) :- entity(X), X = marble.
clue(account).
hidden(marble, napkin).
revealed(marble) :- hidden(marble, napkin), brave(hero), tells(hero, account).
solved :- revealed(marble).
#show solved/0.
#show revealed/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("entity", "hero"),
        asp.fact("entity", "adult"),
        asp.fact("entity", "marble"),
        asp.fact("entity", "account"),
        asp.fact("entity", "ganache"),
        asp.fact("brave", "hero"),
        asp.fact("tells", "hero", "account"),
        asp.fact("hidden", "marble", "napkin"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/0. #show revealed/1."))
    solved = any(sym.name == "solved" for sym in model)
    revealed = any(sym.name == "revealed" and len(sym.arguments) == 1 and str(sym.arguments[0]) == "marble" for sym in model)
    if solved and revealed:
        print("OK: ASP twin agrees that the brave account reveals the marble.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected reveal.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld about marble, account, ganache, and bravery.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=ADULTS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    adult = args.adult or rng.choice(ADULTS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, adult=adult, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = _init_world(params)
    tell(world)
    story = (
        f"{params.name} was a {params.trait} {params.gender} who lived in {TARGET_SETTING}. "
        f"{world.render()}"
    )
    return StorySample(
        params=params,
        story=story,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/0. #show revealed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/0. #show revealed/1."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    rng = random.Random(args.seed)
    samples: list[StorySample] = []
    if args.all:
        combos = [
            StoryParams(name=n, gender=g, adult=a, trait=t)
            for n in NAMES[:3]
            for g in ["girl", "boy"]
            for a in ADULTS[:2]
            for t in TRAITS[:2]
        ]
        samples = [generate(p) for p in combos]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(args.seed + i))
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
