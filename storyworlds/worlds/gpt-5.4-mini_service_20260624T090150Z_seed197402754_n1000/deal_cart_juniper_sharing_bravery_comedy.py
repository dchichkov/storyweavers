#!/usr/bin/env python3
"""
storyworlds/worlds/deal_cart_juniper_sharing_bravery_comedy.py
==============================================================

A small story world about a shared cart, a stubborn deal, and brave, silly
help under a juniper tree.
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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    has_juniper: bool = False
    roomy: bool = False


@dataclass
class Cart:
    id: str
    label: str
    phrase: str
    wheeled: bool = True
    can_share: bool = True


@dataclass
class Deal:
    id: str
    label: str
    promise: str
    break_reason: str
    fix: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "yard": Place(id="yard", label="the yard", has_juniper=True, roomy=True),
    "garden": Place(id="garden", label="the garden", has_juniper=True, roomy=True),
    "path": Place(id="path", label="the path", has_juniper=False, roomy=False),
}

CARTS = {
    "wagon": Cart(id="wagon", label="wagon cart", phrase="a little wagon cart"),
    "scooter-cart": Cart(id="scooter-cart", label="scooter cart", phrase="a small scooter cart"),
    "toy-cart": Cart(id="toy-cart", label="toy cart", phrase="a shiny toy cart"),
}

DEALS = {
    "share-rides": Deal(
        id="share-rides",
        label="a sharing deal",
        promise="take turns with the cart",
        break_reason="nobody wants to wait",
        fix="count to three and swap",
    ),
    "brave-pull": Deal(
        id="brave-pull",
        label="a brave deal",
        promise="pull the cart past the spooky bump",
        break_reason="the bump looks like a grumpy potato",
        fix="hold the handle together and laugh",
    ),
    "juniper-hide-and-push": Deal(
        id="juniper-hide-and-push",
        label="a juniper deal",
        promise="push the cart under the juniper tree",
        break_reason="the branches tickle like sneaky feathers",
        fix="giggle, duck, and keep going",
    ),
}

NAMES = ["Milo", "Nina", "Pip", "Tessa", "Otto", "Ruby", "Max", "Luna"]
TYPES = ["boy", "girl"]
TRAITS = ["curious", "silly", "careful", "brave", "chatty", "gentle"]


@dataclass
class StoryParams:
    place: str
    cart: str
    deal: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
share_ok(P,C,D) :- place(P), cart(C), deal(D), roomy(P), can_share(C), deal_kind(D,share).
brave_ok(P,C,D) :- place(P), cart(C), deal(D), has_juniper(P), deal_kind(D,brave).
valid(P,C,D) :- share_ok(P,C,D).
valid(P,C,D) :- brave_ok(P,C,D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.roomy:
            lines.append(asp.fact("roomy", pid))
        if p.has_juniper:
            lines.append(asp.fact("has_juniper", pid))
    for cid, c in CARTS.items():
        lines.append(asp.fact("cart", cid))
        if c.can_share:
            lines.append(asp.fact("can_share", cid))
    for did, d in DEALS.items():
        lines.append(asp.fact("deal", did))
        if "share" in did:
            lines.append(asp.fact("deal_kind", did, "share"))
        if "brave" in did:
            lines.append(asp.fact("deal_kind", did, "brave"))
        if "juniper" in did:
            lines.append(asp.fact("deal_kind", did, "juniper"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for c in CARTS:
            for d in DEALS:
                if resolve_combo(p, c, d) is not None:
                    out.append((p, c, d))
    return out


def resolve_combo(place: str, cart: str, deal: str) -> Optional[str]:
    p = PLACES[place]
    c = CARTS[cart]
    d = DEALS[deal]
    if "share" in d.id and p.roomy and c.can_share:
        return "share"
    if "brave" in d.id and p.has_juniper:
        return "brave"
    if "juniper" in d.id and p.has_juniper:
        return "juniper"
    return None


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def tell(place: Place, cart: Cart, deal: Deal, name: str, gender: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name))
    friend = world.add(Entity(id="Friend", kind="character", type="boy", label="the friend"))
    cart_ent = world.add(Entity(id=cart.id, type="cart", label=cart.label, phrase=cart.phrase, owner=hero.id))
    cart_ent.held_by = hero.id

    hero.memes["want"] = 1
    hero.memes["joy"] = 1
    world.say(
        f"{name} was a {trait} {gender} who loved {deal.promise} with {cart.phrase}."
    )
    world.say(
        f"{name} and {friend.label} made a deal: {deal.promise}."
    )

    world.para()
    if place.has_juniper:
        world.say(
            f"At {place.label}, a juniper tree shook its tiny green needles like it was trying not to laugh."
        )
    else:
        world.say(
            f"At {place.label}, the cart waited on the path, and even the pebbles looked nosy."
        )

    if deal.id == "share-rides":
        hero.memes["sharing"] = 1
        world.say(
            f"{name} wanted the first turn, but {friend.label} wanted one too."
        )
        world.say(
            f"So they picked {cart.label} up together and said, \"We can share this deal.\""
        )
        world.say(
            f"They counted to three, switched turns, and both giggled when the cart wobbled like a sleepy duck."
        )
    elif deal.id == "brave-pull":
        hero.memes["bravery"] = 1
        world.say(
            f"The cart reached a bump that looked huge, even though it was only a tiny hill in the dirt."
        )
        world.say(
            f"{name} took a deep breath, grinned at {friend.label}, and said, \"I can be brave.\""
        )
        world.say(
            f"They held the handle together and pulled. The cart squeaked, then rolled over the bump like a bean on a spoon."
        )
    else:
        hero.memes["sharing"] = 1
        hero.memes["bravery"] = 1
        world.say(
            f"The juniper branches tickled {name}'s nose, and {friend.label} made a face so funny that even the cart seemed to smile."
        )
        world.say(
            f"{name} said, \"Let's be brave and share the pushing.\""
        )
        world.say(
            f"They ducked under the green branches, pushed in a wobbly line, and the cart scooted out the other side with a proud little bounce."
        )

    world.para()
    world.say(
        f"In the end, {name} and {friend.label} had a happy deal: the cart kept rolling, the juniper kept rustling, and everyone was laughing."
    )

    world.facts.update(hero=hero, friend=friend, cart=cart_ent, deal=deal, place=place)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    deal = f["deal"]
    cart = f["cart"]
    place = f["place"]
    return [
        f'Write a funny story for a young child about a {hero.type} named {hero.id}, a {cart.label}, and a deal at {place.label}.',
        f'Tell a comedy story where {hero.id} tries to keep {cart.phrase} moving and learns sharing or bravery.',
        f'Write a gentle, silly story that includes a juniper tree, a cart, and a deal that ends with laughter.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    cart = f["cart"]
    deal = f["deal"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who made the deal with {hero.id} about the {cart.label}?",
            answer=f"{hero.id} made the deal with {friend.label} about the {cart.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the {cart.label}?",
            answer=f"{hero.id} wanted to {deal.promise}.",
        ),
        QAItem(
            question=f"Where did the funny cart story happen?",
            answer=f"It happened at {place.label}, where the juniper tree made the whole thing feel extra silly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people use something or take turns with it.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something even when you feel a little scared or unsure.",
        ),
        QAItem(
            question="What is a juniper tree?",
            answer="A juniper is a green tree or bush with little needle-like leaves.",
        ),
        QAItem(
            question="What is a cart?",
            answer="A cart is something with wheels that you can pull, push, or move from place to place.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = [f"type={e.type}"]
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.owner:
            parts.append(f"owner={e.owner}")
        if e.held_by:
            parts.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id}: " + " ".join(parts))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny comedy story world about a cart, a juniper tree, and a deal."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--cart", choices=sorted(CARTS))
    ap.add_argument("--deal", choices=sorted(DEALS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=sorted(TYPES))
    ap.add_argument("--trait", choices=sorted(TRAITS))
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
    combos = valid_combos()
    if args.place and args.cart and args.deal:
        if resolve_combo(args.place, args.cart, args.deal) is None:
            raise StoryError("That place, cart, and deal do not make a good story together.")
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.cart is None or c[1] == args.cart)
        and (args.deal is None or c[2] == args.deal)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, cart, deal = rng.choice(sorted(filtered))
    gender = args.gender or rng.choice(TYPES)
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, cart=cart, deal=deal, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], CARTS[params.cart], DEALS[params.deal], params.name, params.gender, params.trait)
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
    StoryParams(place="yard", cart="wagon", deal="share-rides", name="Milo", gender="boy", trait="silly"),
    StoryParams(place="garden", cart="toy-cart", deal="brave-pull", name="Ruby", gender="girl", trait="brave"),
    StoryParams(place="path", cart="scooter-cart", deal="juniper-hide-and-push", name="Pip", gender="boy", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.deal} with {p.cart} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
