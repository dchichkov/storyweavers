#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/acreage_moral_value_heartwarming.py
===============================================================================================================

A small heartwarming story world about acreage, stewardship, and moral value.

Initial seed tale used to shape the world model:
---
A child named June lived beside a little family acre of land. The acre had a patch of tired soil, a crooked fence, and a small row of berry bushes that needed care. June loved the acre because it held summer picnics, cool shade, and a place to breathe.

One day, a neighbor asked if June's family would sell part of the acre so a noisy storage shed could be built there. The offer was tempting, because the money could buy shiny things. But June noticed the berry bushes and the old oak that gave the yard its best shade. June's parent said the land was not just money; it had memory, food, and room for kind hands.

So June chose to help repair the fence and water the bushes instead. The neighbor saw the tidy row of berries and the happy garden, and agreed to leave the acre alone. June felt proud that the family kept something precious because it was worth more than cash.

World model:
---
- Acreage has physical extent, soil quality, shade, and fence state.
- Moral value is tracked as a meme-like score for care, gratitude, and fairness.
- A tempting offer can increase money but reduce shade, food, and belonging.
- Choosing stewardship repairs the land and raises moral value.

Narration instruments:
---
- setup: introduce a child, the acre, and what they love
- tension: a tempting offer threatens a valued part of the land
- turn: the child notices what cannot be priced well
- resolution: the family chooses care, and the acre becomes healthier

"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

MORAL_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they" if self.plural else "it",
                "object": "them" if self.plural else "it",
                "possessive": "their" if self.plural else "its"}[case]


@dataclass
class Acreage:
    acres: float
    soil_health: float
    shade: float
    fence_strength: float
    berries: float
    belonging: float
    money_offer: float
    threatened: bool = False


@dataclass
class MarketOffer:
    buyer: str
    acres_requested: float
    money: float
    replacement_promise: str
    harms: set[str] = field(default_factory=set)


class World:
    def __init__(self, acreage: Acreage) -> None:
        self.acreage = acreage
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(copy.deepcopy(self.acreage))
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    parent_type: str
    acreage_size: int
    offer_kind: str
    seed: Optional[int] = None


PLACES = {
    "farm": "a small family farm",
    "orchard": "a sunny orchard",
    "backlot": "a quiet back lot",
    "meadow": "a green meadow edge",
}

CHILD_NAMES = {
    "girl": ["June", "Mila", "Iris", "Lena", "Ruby"],
    "boy": ["Eli", "Noah", "Owen", "Theo", "Jonah"],
}

OFFER_KINDS = {
    "shed": MarketOffer(
        buyer="a builder",
        acres_requested=1.0,
        money=40.0,
        replacement_promise="a shiny storage shed",
        harms={"shade", "belonging"},
    ),
    "road": MarketOffer(
        buyer="the town",
        acres_requested=0.5,
        money=25.0,
        replacement_promise="a straighter road",
        harms={"fence", "peace"},
    ),
    "parking": MarketOffer(
        buyer="a shop owner",
        acres_requested=0.75,
        money=35.0,
        replacement_promise="a bigger parking lot",
        harms={"berries", "soil"},
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming acreage story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--offer", choices=OFFER_KINDS)
    ap.add_argument("--acreage", type=int, choices=[1, 2, 3, 4], help="size in acres")
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        for offer in OFFER_KINDS:
            combos.append((place, offer))
    return combos


def reasonableness_gate(place: str, acreage_size: int, offer_kind: str) -> bool:
    offer = OFFER_KINDS[offer_kind]
    return acreage_size >= offer.acres_requested and place in PLACES


ASP_RULES = r"""
place(farm). place(orchard). place(backlot). place(meadow).
offer(shed). offer(road). offer(parking).

valid(P,O) :- place(P), offer(O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for o in OFFER_KINDS:
        lines.append(asp.fact("offer", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    child_type = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES[child_type])
    parent_type = args.parent or rng.choice(["mother", "father"])
    acreage_size = args.acreage or rng.choice([1, 2, 3, 4])
    offer_kind = args.offer or rng.choice(list(OFFER_KINDS))

    if not reasonableness_gate(place, acreage_size, offer_kind):
        raise StoryError("No story: the offer asks for more land than the family has.")

    return StoryParams(
        place=place,
        child_name=child_name,
        child_type=child_type,
        parent_type=parent_type,
        acreage_size=acreage_size,
        offer_kind=offer_kind,
    )


def make_world(params: StoryParams) -> World:
    acreage = Acreage(
        acres=float(params.acreage_size),
        soil_health=0.7,
        shade=0.8,
        fence_strength=0.6,
        berries=0.8,
        belonging=0.9,
        money_offer=0.0,
    )
    world = World(acreage)
    child = world.add(Entity(id="child", kind="character", type=params.child_type))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type))
    land = world.add(Entity(id="acre", kind="place", type="acreage", label="the acre"))
    offer = OFFER_KINDS[params.offer_kind]
    world.facts.update(child=child, parent=parent, land=land, offer=offer, params=params)
    return world


def simulate(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    offer: MarketOffer = f["offer"]
    params: StoryParams = f["params"]
    acre = world.acreage

    child.memes["love_land"] = 1.0
    child.memes["gratitude"] = 0.5

    world.say(f"{child.pronoun().capitalize()} lived beside {PLACES[params.place]}.")
    world.say(f"The family had {acre.acres:.0f} acres, and {child.pronoun('possessive')} favorite one was the little acre by the house.")
    world.say("It held soft grass, a crooked fence, and berries that turned sweet in the sun.")

    world.para()
    world.say(f"One day, {offer.buyer} came with a tempting offer.")
    world.say(f'"If your family sells {offer.acres_requested:g} acre(s), you could have enough money for {offer.replacement_promise}," the buyer said.')
    acre.money_offer = offer.money
    acre.threatened = True
    world.say(f"The number sounded shiny, but the offer would harm {', '.join(sorted(offer.harms))}.")

    child.memes["worry"] = 1.0
    parent.memes["care"] = 1.0
    world.say(f"{child.pronoun('possessive').capitalize()} {params.parent_type} looked at the acre and said it was more than a price tag.")
    world.say("The land held shade for naps, berries for snacks, and a place where the family could feel at home.")

    world.para()
    child.memes["moral_value"] = 1.0
    acre.soil_health += 0.15
    acre.shade += 0.10
    acre.fence_strength += 0.20
    acre.berries += 0.10
    acre.belonging += 0.20

    world.say(f"{child.pronoun().capitalize()} helped mend the fence and water the berry bushes.")
    world.say(f"Together they chose care over cash, because the acre was worth keeping whole.")
    world.say(f"By evening, the fence stood straighter, the berries looked fuller, and the acre felt safer and kinder.")
    world.say(f"The buyer nodded, smiled, and left the family to enjoy their quiet little land.")
    world.facts["resolved"] = True
    world.facts["moral_value"] = child.memes["moral_value"]


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a heartwarming story about a child who helps protect an acre of land from a tempting sale.",
        f"Tell a gentle story where {p.child_name} learns that land can matter more than money.",
        f"Write a simple story about acreage, family care, and choosing what is morally right.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    offer: MarketOffer = f["offer"]
    return [
        QAItem(
            question=f"What kind of place did {p.child_name} live beside?",
            answer=f"{p.child_name} lived beside {PLACES[p.place]}, and the family had a little acre there.",
        ),
        QAItem(
            question=f"What did the buyer want the family to sell?",
            answer=f"The buyer wanted the family to sell {offer.acres_requested:g} acre(s) of land for {offer.replacement_promise}.",
        ),
        QAItem(
            question=f"Why did {p.child_name}'s family decide not to sell the acre?",
            answer="They decided not to sell because the land had shade, berries, and a homey feeling that were worth more than money.",
        ),
        QAItem(
            question=f"What did {p.child_name} do to help instead of selling the land?",
            answer=f"{p.child_name} helped mend the fence and water the berry bushes, which made the acre healthier.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an acre?",
            answer="An acre is a measure of land area. People use it to talk about how big a piece of ground is.",
        ),
        QAItem(
            question="What does it mean to take care of land?",
            answer="Taking care of land means keeping it clean, healthy, and safe so plants, animals, and people can use it well.",
        ),
        QAItem(
            question="Why can some things be morally valuable even if they do not bring much money?",
            answer="Some things are morally valuable because they help people live well, care for each other, and keep important memories and relationships safe.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    a = world.acreage
    lines = [
        "--- world model state ---",
        f"acreage: acres={a.acres}, soil_health={a.soil_health}, shade={a.shade}, fence_strength={a.fence_strength}, berries={a.berries}, belonging={a.belonging}, money_offer={a.money_offer}, threatened={a.threatened}",
    ]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} memes={dict(e.memes)} meters={dict(e.meters)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    simulate(world)
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
    StoryParams(place="farm", child_name="June", child_type="girl", parent_type="mother", acreage_size=2, offer_kind="shed"),
    StoryParams(place="orchard", child_name="Eli", child_type="boy", parent_type="father", acreage_size=3, offer_kind="parking"),
    StoryParams(place="meadow", child_name="Mila", child_type="girl", parent_type="mother", acreage_size=1, offer_kind="road"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
