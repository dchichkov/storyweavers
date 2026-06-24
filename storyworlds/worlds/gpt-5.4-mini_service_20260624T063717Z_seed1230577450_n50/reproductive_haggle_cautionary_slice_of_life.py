#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T063717Z_seed1230577450_n50/reproductive_haggle_cautionary_slice_of_life.py
=====================================================================================================

A small, self-contained storyworld: a slice-of-life cautionary tale about a child
who wants a new pet, a parent who haggles carefully, and a practical ending that
avoids a reproductive surprise.

Seed premise:
- The child falls in love with a small animal at a shop or market.
- The parent worries about costs, space, and reproductive consequences.
- They haggle over the price and make a safer choice.

The world is intentionally modest: one scene, a few typed entities, meters and
memes, and a state-driven ending image.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Shop:
    place: str = "the market"
    indoors: bool = True
    affords: set[str] = field(default_factory=lambda: {"adopt", "bargain"})


@dataclass
class Creature:
    id: str
    label: str
    phrase: str
    species: str
    price: int
    reproductive_risk: str
    care_need: str
    gendered_pairing: bool = False


@dataclass
class StoryParams:
    place: str
    creature: str
    name: str
    gender: str
    parent: str
    mood: str
    seed: Optional[int] = None


class World:
    def __init__(self, shop: Shop) -> None:
        self.shop = shop
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.lines: list[str] = []
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out = []
        buf = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


SHOP = Shop()

CREATURES = {
    "rabbit_pair": Creature(
        id="rabbit_pair",
        label="two young rabbits",
        phrase="a pair of fluffy rabbits",
        species="rabbit",
        price=18,
        reproductive_risk="babies",
        care_need="a roomy hutch and separate space",
        gendered_pairing=True,
    ),
    "chicks": Creature(
        id="chicks",
        label="two chicks",
        phrase="a little box of chicks",
        species="chick",
        price=12,
        reproductive_risk="more chicks",
        care_need="warmth and feed every day",
        gendered_pairing=False,
    ),
    "guppies": Creature(
        id="guppies",
        label="three guppies",
        phrase="a small bowl of guppies",
        species="fish",
        price=10,
        reproductive_risk="many tiny fish",
        care_need="clean water and a filter",
        gendered_pairing=False,
    ),
}

NAMES = {
    "girl": ["Mia", "Nora", "Lily", "Zoe", "Ava"],
    "boy": ["Leo", "Ben", "Toby", "Finn", "Max"],
}
TRAITS = ["careful", "curious", "gentle", "hopeful", "restless"]
GENDER_TYPES = ["girl", "boy"]

ASP_RULES = r"""
creature(C) :- creature_id(C).
risky(C) :- reproductive_risk(C, R), R != "".
affordable(C) :- price(C, P), budget(B), P =< B.
can_buy(C) :- creature(C), affordable(C).
needs_warning(C) :- reproductive_risk(C, _), care_need(C, _).
good_choice(C) :- can_buy(C), not needs_warning(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("budget", 20))
    for cid, c in CREATURES.items():
        lines.append(asp.fact("creature_id", cid))
        lines.append(asp.fact("price", cid, c.price))
        lines.append(asp.fact("reproductive_risk", cid, c.reproductive_risk))
        lines.append(asp.fact("care_need", cid, c.care_need))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary slice-of-life story world about a child, a pet, and a careful haggle.")
    ap.add_argument("--place", choices=["market"], default="market")
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--gender", choices=GENDER_TYPES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--mood", choices=TRAITS)
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
    creature = args.creature or rng.choice(list(CREATURES))
    gender = args.gender or rng.choice(GENDER_TYPES)
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    mood = args.mood or rng.choice(TRAITS)
    if creature == "rabbit_pair" and parent == "father" and mood == "restless":
        pass
    return StoryParams(place=args.place, creature=creature, name=name, gender=gender, parent=parent, mood=mood)


def generate(params: StoryParams) -> StorySample:
    world = World(SHOP)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={"joy": 0.0}, memes={"desire": 0.0, "worry": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}", meters={"work": 0.0}, memes={"caution": 0.0}))
    critter = CREATURES[params.creature]
    pet = world.add(Entity(id=critter.id, type=critter.species, label=critter.label, phrase=critter.phrase, owner=child.id, caretaker=parent.id))
    child.memes["desire"] += 1
    child.meters["joy"] += 1
    world.say(f"{child.id} and {child.pronoun('possessive')} {parent.noun()} went to {world.shop.place} on an ordinary afternoon.")
    world.say(f"There, {child.id} saw {pet.phrase} and wanted {pet.obj()} right away.")
    world.para()
    if params.creature == "rabbit_pair":
        world.say(f"{child.pronoun('possessive').capitalize()} {parent.noun()} smiled, but also frowned at the thought of reproductive surprises.")
        world.say(f'"If we buy {pet.obj()}, we might end up with babies," {parent.pronoun()} said. "And babies need space and food."')
        world.facts["risk"] = "babies"
    elif params.creature == "chicks":
        world.say(f"{child.pronoun('possessive').capitalize()} {parent.noun()} pointed out that little animals can grow into a lot more work.")
        world.say(f'"We need to think about care first," {parent.pronoun()} said. "Tiny pets need steady attention."')
        world.facts["risk"] = "more chicks"
    else:
        world.say(f"{child.pronoun('possessive').capitalize()} {parent.noun()} warned that even a small tank pet can mean a bigger job at home.")
        world.say(f'"Clean water matters more than a quick buy," {parent.pronoun()} said.")
        world.facts["risk"] = "many tiny fish"
    child.memes["worry"] += 1
    world.say(f"{child.id} tried to haggle a little, asking if the price could be kinder.")
    world.say(f"The {params.parent} did the same, but only enough to keep the choice sensible.")
    world.facts["haggled"] = True
    world.para()
    world.say(f"In the end, they chose to wait and look at a safer pet instead of rushing into a reproductive problem.")
    world.say(f"{child.id} held the pamphlet tightly and walked home knowing not every cute thing was the right thing to bring back.")
    world.facts.update(child=child, parent=parent, pet=pet, creature=critter, params=params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short slice-of-life story about a child who wants a pet, a parent who haggles, and a careful ending.',
        f'Write a cautionary story where {f["child"].id} wants {f["pet"].phrase} but the family notices the reproductive risk first.',
        'Tell a gentle everyday story in which a market conversation turns into a wiser choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    pet: Entity = f["pet"]
    return [
        QAItem(
            question=f"What did {child.id} want at the market?",
            answer=f"{child.id} wanted {pet.phrase} and hoped to take {pet.obj()} home.",
        ),
        QAItem(
            question=f"Why did the {parent.type} caution {child.id} about the pet?",
            answer=f"The {parent.type} cautioned {child.id} because {f['risk']} could lead to more work, more space, and more care than the family wanted.",
        ),
        QAItem(
            question=f"What did {child.id} and the {parent.type} do about the price?",
            answer=f"They haggled a little, but only enough to make the decision thoughtful instead of impulsive.",
        ),
        QAItem(
            question=f"What choice did they make at the end?",
            answer=f"They chose not to buy the pet and looked for a safer option instead.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does reproductive mean?",
            answer="Reproductive means having to do with making babies or young ones.",
        ),
        QAItem(
            question="What is haggling?",
            answer="Haggling means politely talking back and forth about a price until both sides agree.",
        ),
        QAItem(
            question="Why can a small pet become a big job?",
            answer="A small pet can become a big job because it needs food, water, cleaning, and sometimes space for young animals too.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} label={e.label!r} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def asp_verify() -> int:
    import asp
    if asp.one_model(asp_program("#show good_choice/1.")):
        print("OK: ASP program parses and solves.")
        return 0
    print("MISMATCH or no model.")
    return 1


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
    StoryParams(place="market", creature="rabbit_pair", name="Mia", gender="girl", parent="mother", mood="careful"),
    StoryParams(place="market", creature="chicks", name="Leo", gender="boy", parent="father", mood="curious"),
    StoryParams(place="market", creature="guppies", name="Nora", gender="girl", parent="mother", mood="hopeful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good_choice/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show good_choice/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
