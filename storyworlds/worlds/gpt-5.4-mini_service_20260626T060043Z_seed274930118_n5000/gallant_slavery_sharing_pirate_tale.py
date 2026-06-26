#!/usr/bin/env python3
"""
A standalone storyworld for a tiny pirate-tale domain about gallant sharing and
a hard choice about slavery.

The seed words here point to a rescue story rather than an endorsement of harm:
a gallant crew shares food, water, and treasure, and they help free a captive
sailor from slavery. The world model tracks the ship, the crew, a chained
captain's prisoner, and the social/emotional turn from greed to generosity.
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

ASP_RULES = r"""
% The pirate tale is reasonable when the crew can share enough supplies to help
% a prisoner and still keep the ship steady.

needs_sharing(Story) :- story(Story), has_prisoner(Story), has_treasure(Story).
gallant(Story) :- needs_sharing(Story), shares_food(Story), frees_prisoner(Story).
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str
    place: str
    sea: str
    deck: str
    hold: str


@dataclass
class StoryParams:
    place: str = "the bright blue sea"
    ship_name: str = "The Sunfish"
    hero_name: str = "Mara"
    hero_type: str = "girl"
    captain_name: str = "Captain Reed"
    seed: Optional[int] = None


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy
        clone = World(self.ship)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate-tale storyworld about gallant sharing and freeing a captive sailor.")
    ap.add_argument("--place", default="the bright blue sea")
    ap.add_argument("--ship-name", default="The Sunfish")
    ap.add_argument("--hero-name", default=None)
    ap.add_argument("--hero-type", choices=["girl", "boy"], default=None)
    ap.add_argument("--captain-name", default="Captain Reed")
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
    hero_name = args.hero_name or rng.choice(["Mara", "Nell", "Toby", "Finn"])
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    return StoryParams(
        place=args.place,
        ship_name=args.ship_name,
        hero_name=hero_name,
        hero_type=hero_type,
        captain_name=args.captain_name,
    )


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("story", "pirate_tale"),
        asp.fact("has_prisoner", "pirate_tale"),
        asp.fact("has_treasure", "pirate_tale"),
        asp.fact("shares_food", "pirate_tale"),
        asp.fact("frees_prisoner", "pirate_tale"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show gallant/1."))
    yes = bool(asp.atoms(model, "gallant"))
    if yes:
        print("OK: ASP says the pirate tale is gallant.")
        return 0
    print("MISMATCH: ASP did not derive gallant/1.")
    return 1


def names_for(hero_type: str) -> list[str]:
    return ["Mara", "Nell", "Ruby"] if hero_type == "girl" else ["Toby", "Finn", "Pip"]


def tell(params: StoryParams) -> World:
    ship = Ship(name=params.ship_name, place=params.place, sea=params.place, deck="the deck", hold="the hold")
    world = World(ship)

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    mate = world.add(Entity(id="mate", kind="character", type="pirate", label="the first mate"))
    captain = world.add(Entity(id="captain", kind="character", type="captain", label=params.captain_name))
    prisoner = world.add(Entity(id="prisoner", kind="character", type="man", label="a captive sailor"))
    chest = world.add(Entity(id="chest", type="treasure", label="a chest of coins", phrase="a heavy chest of coins"))
    bread = world.add(Entity(id="bread", type="food", label="bread", phrase="warm bread"))
    water = world.add(Entity(id="water", type="water", label="water", phrase="fresh water"))

    prisoner.meters["freedom"] = 0
    prisoner.memes["hope"] = 0
    chest.meters["gleam"] = 1

    world.say(f"On {ship.place}, aboard {ship.name}, {hero.label} was a gallant pirate who loved a fair share.")
    world.say(f"{hero.label.capitalize()} and {mate.label} kept {bread.phrase}, {water.phrase}, and {chest.phrase} safe on {ship.deck}.")
    world.say(f"But in the hold, {captain.label} had kept {prisoner.label} in slavery, with no choice and no room to roam.")

    world.para()
    world.say(f"When the crew heard the prisoner singing softly, {hero.label} brought {bread.label} and {water.label} down to the hold.")
    hero.memes["kindness"] = 1
    prisoner.memes["hope"] += 1
    world.say(f"{hero.label.capitalize()} shared the food and water, and {prisoner.label} lifted {prisoner.pronoun('possessive')} head with hope.")

    world.say(f"{captain.label} scowled and tried to keep the prisoner chained, but the crew would not leave a friend in slavery.")
    hero.memes["defiance"] = 1
    mate.memes["loyalty"] = 1

    world.para()
    world.say(f"The first mate cut the chain, {hero.label} opened the hold door, and the prisoner hurried into the salt air.")
    prisoner.meters["freedom"] = 1
    prisoner.memes["hope"] += 2
    chest.meters["gleam"] = 0
    hero.memes["joy"] = 1
    hero.memes["gallantry"] = 1
    world.say(f"Then the crew shared the coins fairly, so no one fought over the treasure and everyone felt braver.")

    world.para()
    world.say(f"At sunset, {prisoner.label} stood on the deck of {ship.name}, free at last, while the gallant crew watched the waves turn gold.")

    world.facts.update(
        hero=hero,
        mate=mate,
        captain=captain,
        prisoner=prisoner,
        chest=chest,
        bread=bread,
        water=water,
        ship=ship,
        shared_food=True,
        freed_prisoner=True,
        gallant=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        "Write a short pirate tale for a young child about a gallant crew who shares food and helps a captive sailor become free.",
        f"Tell a gentle story where {hero.label} shares bread and water on a ship and refuses to leave a prisoner in slavery.",
        "Write a simple pirate story with treasure, sharing, and a happy ending on the deck at sunset.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    prisoner = f["prisoner"]
    ship = f["ship"]
    captain = f["captain"]
    return [
        QAItem(
            question=f"Who was the gallant pirate in the story?",
            answer=f"{hero.label} was the gallant pirate who shared kindly and helped others.",
        ),
        QAItem(
            question=f"What was wrong with the prisoner in the hold?",
            answer=f"{captain.label} had kept {prisoner.label} in slavery, so {prisoner.label} could not leave on {ship.name}.",
        ),
        QAItem(
            question="What did the crew share before they freed the prisoner?",
            answer="They shared bread, water, and later the treasure so everyone could be fair and calm.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {prisoner.label} standing free on the deck while the sun went down over the sea.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does gallant mean?",
            answer="Gallant means brave and kind in a proud, helpful way.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means giving some of what you have to another person so everyone can use it or enjoy it.",
        ),
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a boat that sails the sea and carries a crew, supplies, and treasure.",
        ),
        QAItem(
            question="Why is slavery wrong?",
            answer="Slavery is wrong because it takes away a person's freedom and treats them like they belong to someone else.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show gallant/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show gallant/1."))
        print("gallant:", bool(asp.atoms(model, "gallant")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    count = len(names_for(args.hero_type or "girl"))
    if args.all:
        for i, name in enumerate(names_for("girl") + names_for("boy")):
            p = StoryParams(hero_name=name, hero_type="girl" if i < 3 else "boy", seed=base_seed + i)
            samples.append(generate(p))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
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
