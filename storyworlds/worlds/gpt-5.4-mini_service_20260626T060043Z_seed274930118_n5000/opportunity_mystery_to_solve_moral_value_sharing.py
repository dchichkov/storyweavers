#!/usr/bin/env python3
"""
A fairy-tale storyworld about a child, a mysterious opportunity, and a lesson in sharing.

The world premise:
- A small kingdom has a surprise opportunity hidden in a lantern-lit market.
- One child discovers a mystery: a golden key opens a garden gate, but only if it is shared fairly.
- The tension is whether the child keeps the chance to themself or shares it with a friend.
- The resolution is that sharing reveals the true treasure.

This world is intentionally compact and constraint-checked.  It supports:
- default generation
- -n / --all / --seed / --trace / --qa / --json
- --asp / --verify / --show-asp
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


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "mother", "woman"}
        male = {"boy", "king", "prince", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    setting: str
    affords: set[str] = field(default_factory=set)


@dataclass
class MysteryItem:
    id: str
    label: str
    phrase: str
    clue: str
    truth: str
    carried_by: Optional[str] = None
    owner: Optional[str] = None
    plural: bool = False


@dataclass
class Offer:
    id: str
    label: str
    prep: str
    tail: str
    requires: str
    reveals: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, MysteryItem] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: MysteryItem) -> MysteryItem:
        self.items[item.id] = item
        return item

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
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.items = _copy.deepcopy(self.items)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "market": Place(id="market", label="the moonlit market", setting="outdoors", affords={"find", "share"}),
    "grove": Place(id="grove", label="the whispering grove", setting="outdoors", affords={"find", "share"}),
    "courtyard": Place(id="courtyard", label="the castle courtyard", setting="outdoors", affords={"find", "share"}),
}

HEROINES = [
    ("Ayla", "girl"),
    ("Mina", "girl"),
    ("Nora", "girl"),
    ("Eli", "boy"),
    ("Finn", "boy"),
    ("Theo", "boy"),
]

TRAITS = ["curious", "gentle", "brave", "kind", "dreamy", "clever"]

MYSTERY_ITEMS = {
    "lantern_key": MysteryItem(
        id="lantern_key",
        label="a golden key",
        phrase="a golden key tied with a blue ribbon",
        clue="It glowed when two hands touched it.",
        truth="It opened the garden gate only when shared.",
    ),
    "silver_bell": MysteryItem(
        id="silver_bell",
        label="a silver bell",
        phrase="a silver bell with a tiny heart carved on it",
        clue="It rang softly whenever someone spoke kindly.",
        truth="It summoned the hidden gardener when voices were gentle.",
    ),
    "apple_seed": MysteryItem(
        id="apple_seed",
        label="an apple seed",
        phrase="a little apple seed in a paper pouch",
        clue="It warmed whenever it was passed from palm to palm.",
        truth="It grew into the orchard only if planted together.",
    ),
}

OFFERS = {
    "share_key": Offer(
        id="share_key",
        label="share the key",
        prep="share the key together",
        tail="walked to the gate side by side",
        requires="lantern_key",
        reveals="the garden gate opened to a hidden path",
    ),
    "share_bell": Offer(
        id="share_bell",
        label="share the bell",
        prep="ring the bell together",
        tail="stood close and listened",
        requires="silver_bell",
        reveals="the hidden gardener came with a basket of flowers",
    ),
    "share_seed": Offer(
        id="share_seed",
        label="share the seed",
        prep="plant the seed together",
        tail="kneeled in the soft earth",
        requires="apple_seed",
        reveals="a tiny orchard sprouted overnight",
    ),
}


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    mystery: str
    offer: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Rule helpers
# ---------------------------------------------------------------------------

def mystery_is_usable(mystery: MysteryItem, offer: Offer) -> bool:
    return mystery.id == offer.requires


def resolve_story_choice(place: str, mystery: str, offer: str) -> None:
    if mystery not in MYSTERY_ITEMS:
        raise StoryError("Unknown mystery item.")
    if offer not in OFFERS:
        raise StoryError("Unknown offer.")
    if not mystery_is_usable(MYSTERY_ITEMS[mystery], OFFERS[offer]):
        raise StoryError("That mystery and that sharing choice do not belong to the same tale.")


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity, friend: Entity, mystery: MysteryItem) -> None:
    world.say(
        f"Once upon a time, {hero.id} was a {hero.traits[0]} little {hero.type} "
        f"who loved good surprises. {friend.id} was {friend.pronoun('subject')} "
        f"kind friend, and together they wandered near {world.place.label}."
    )
    world.say(
        f"Then {hero.id} found {mystery.phrase}. {mystery.clue}"
    )


def tension(world: World, hero: Entity, friend: Entity, mystery: MysteryItem) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    hero.memes["greed"] = hero.memes.get("greed", 0) + 1
    world.say(
        f"{hero.id} held the {mystery.label} close and wondered if keeping it would make the day feel larger."
    )
    world.say(
        f"But {friend.id} looked at the glow and asked if there might be a way to use the opportunity together."
    )


def clue_turn(world: World, mystery: MysteryItem) -> None:
    world.say(
        f"At last, the old clue made sense: {mystery.truth}"
    )


def resolution(world: World, hero: Entity, friend: Entity, offer: Offer, mystery: MysteryItem) -> None:
    hero.memes["generosity"] = hero.memes.get("generosity", 0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0) + 1
    world.say(
        f"{hero.id} smiled, opened {hero.pronoun('possessive')} hand, and chose to {offer.prep}."
    )
    world.say(
        f"So {hero.id} and {friend.id} {offer.tail}; then {offer.reveals}. "
        f"In the end, the true opportunity was not keeping the treasure, but sharing it."
    )


def tell(place: Place, mystery: MysteryItem, offer: Offer,
         hero_name: str = "Ayla", hero_type: str = "girl",
         friend_name: str = "Milo", friend_type: str = "boy",
         trait: str = "curious") -> World:
    world = World(place)
    hero = world.add_entity(Entity(id=hero_name, kind="character", type=hero_type, traits=[trait, "gentle"]))
    friend = world.add_entity(Entity(id=friend_name, kind="character", type=friend_type, traits=["kind", "patient"]))
    world.add_item(mystery)
    world.facts = {
        "hero": hero,
        "friend": friend,
        "mystery": mystery,
        "offer": offer,
        "place": place,
    }
    introduce(world, hero, friend, mystery)
    world.para()
    tension(world, hero, friend, mystery)
    world.para()
    clue_turn(world, mystery)
    resolution(world, hero, friend, offer, mystery)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    mystery: MysteryItem = world.facts["mystery"]  # type: ignore[assignment]
    offer: Offer = world.facts["offer"]  # type: ignore[assignment]
    return [
        "Write a fairy-tale story for a small child about an opportunity that becomes meaningful when shared.",
        f"Tell a gentle mystery story where {hero.id} discovers {mystery.phrase} with {friend.id} and must choose whether to share it.",
        f"Write a short story that includes the word 'opportunity' and ends with {hero.id} and {friend.id} solving the mystery together.",
        f"Make the moral clear: {offer.label} should lead to a happy ending."
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    mystery: MysteryItem = world.facts["mystery"]  # type: ignore[assignment]
    offer: Offer = world.facts["offer"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {hero.id} find near {place.label}?",
            answer=f"{hero.id} found {mystery.phrase}, and it carried a clue about how to use the opportunity."
        ),
        QAItem(
            question=f"What made the story's mystery hard to solve at first?",
            answer=f"It was hard because the treasure looked special, and {hero.id} had to decide whether to keep it or share it with {friend.id}."
        ),
        QAItem(
            question=f"What did {hero.id} and {friend.id} do in the end?",
            answer=f"They chose to {offer.prep}, and that sharing solved the mystery and opened the way to a happy reward."
        ),
        QAItem(
            question="What was the moral of the fairy tale?",
            answer="The moral was that sharing can turn a small chance into something better for everyone."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use, enjoy, or have part of something too."
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not understood at first, so people have to think carefully and find clues."
        ),
        QAItem(
            question="What is an opportunity?",
            answer="An opportunity is a chance to do something good, useful, or exciting."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "", "== (2) Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type}) memes={dict(e.memes)}")
    for item in world.items.values():
        lines.append(f"  {item.id:8} (item) owner={item.owner} carried_by={item.carried_by}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts:
% place(P).
% mystery(M).
% offer(O).
% compatible(P, M, O).

compatible(P, M, O) :- place(P), mystery(M), offer(O), req(O, M).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid in MYSTERY_ITEMS:
        lines.append(asp.fact("mystery", mid))
    for oid, offer in OFFERS.items():
        lines.append(asp.fact("offer", oid))
        lines.append(asp.fact("req", oid, offer.requires))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonable story combinations
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid in PLACES:
        for mid, mystery in MYSTERY_ITEMS.items():
            for oid, offer in OFFERS.items():
                if mystery_is_usable(mystery, offer):
                    combos.append((pid, mid, oid))
    return combos


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale world about mystery, sharing, and moral choice.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERY_ITEMS)
    ap.add_argument("--offer", choices=OFFERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.place or args.mystery or args.offer:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.mystery is None or c[1] == args.mystery)
            and (args.offer is None or c[2] == args.offer)
        ]
    if not combos:
        raise StoryError("No valid story matches the given options.")
    place, mystery, offer = rng.choice(sorted(combos))
    hero_name, hero_type = (args.hero_name, args.hero_type)
    if hero_name is None or hero_type is None:
        hero_name, hero_type = rng.choice(HEROINES)
    friend_pool = [h for h in HEROINES if h[0] != hero_name]
    friend_name, friend_type = (args.friend_name, args.friend_type)
    if friend_name is None or friend_type is None:
        friend_name, friend_type = rng.choice(friend_pool)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        mystery=mystery,
        offer=offer,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        MYSTERY_ITEMS[params.mystery],
        OFFERS[params.offer],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        trait=params.trait,
    )
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
    StoryParams(place="market", mystery="lantern_key", offer="share_key", hero_name="Ayla", hero_type="girl", friend_name="Milo", friend_type="boy", trait="curious"),
    StoryParams(place="grove", mystery="silver_bell", offer="share_bell", hero_name="Finn", hero_type="boy", friend_name="Nora", friend_type="girl", trait="kind"),
    StoryParams(place="courtyard", mystery="apple_seed", offer="share_seed", hero_name="Mina", hero_type="girl", friend_name="Theo", friend_type="boy", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, mystery, offer) combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
