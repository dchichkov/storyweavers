#!/usr/bin/env python3
"""
storyworlds/worlds/recyclable_year_sharing_sound_effects_space_adventure.py
===========================================================================

A small, classical story world about a space crew that shares recyclable
materials across the seasons of a year, with sound effects that make the ship
feel alive.

Seed premise:
- A child crew member loves collecting recyclable things on a spaceship.
- Each year, the ship needs those recyclables for repairs and crafts.
- A tension rises when one child wants to keep the special item alone.
- The crew solves it by sharing, and the sound effects become part of the fun.

The world is intentionally compact: fewer, better-supported variations rather
than a large bag of weak ones.
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
# Model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str
    place: str
    year_cycle: list[str]
    sound_effects: dict[str, str]


@dataclass
class Collection:
    label: str
    phrase: str
    type: str
    year_kind: str
    recyclable: bool
    sound: str
    shareable: bool = True


@dataclass
class StoryParams:
    place: str
    collection: str
    name: str
    gender: str
    crewmate: str
    year_part: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.ship)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


THRESHOLD = 1.0


def _bump(e: Entity, key: str, amount: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amount


def _mood(e: Entity, key: str, amount: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amount


# ---------------------------------------------------------------------------
# World state and causal rules
# ---------------------------------------------------------------------------
def _r_sharing(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "thing":
            continue
        if ent.meters.get("shared", 0.0) < THRESHOLD:
            continue
        sig = ("shared_effect", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if ent.owner and ent.shared_with:
            owner = world.get(ent.owner)
            owner.memes["pride"] = owner.memes.get("pride", 0.0) + 1
            out.append(f"That made the whole crew feel proud.")
    return out


def _r_sound(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "thing":
            continue
        if ent.meters.get("used", 0.0) < THRESHOLD:
            continue
        sig = ("sound", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        sound = ent.phrase or ent.label
        out.append(f"{sound} went {world.facts.get('sound_effect', 'beep-beep')}.")
    return out


CAUSAL_RULES = [_r_sharing, _r_sound]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
SHIP = Ship(
    name="The Comet Cart",
    place="the starship",
    year_cycle=["spring", "summer", "autumn", "winter", "new year"],
    sound_effects={
        "can": "clang-clink",
        "paper": "swish-swish",
        "foil": "flick-flick",
        "bottle": "plink-plink",
    },
)

COLLECTIONS = {
    "can": Collection(
        label="can",
        phrase="a shiny recycled can",
        type="can",
        year_kind="summer",
        recyclable=True,
        sound="clang-clink",
    ),
    "paper": Collection(
        label="paper",
        phrase="a folded piece of recyclable paper",
        type="paper",
        year_kind="autumn",
        recyclable=True,
        sound="swish-swish",
    ),
    "foil": Collection(
        label="foil",
        phrase="a bright sheet of recyclable foil",
        type="foil",
        year_kind="winter",
        recyclable=True,
        sound="flick-flick",
    ),
    "bottle": Collection(
        label="bottle",
        phrase="a clear recyclable bottle",
        type="bottle",
        year_kind="spring",
        recyclable=True,
        sound="plink-plink",
    ),
}

NAMES = ["Nova", "Milo", "Iris", "Zane", "Luna", "Tess", "Owen", "Pia"]
TRAITS = ["curious", "gentle", "brave", "cheerful", "careful", "helpful"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for cid, c in COLLECTIONS.items():
        if c.recyclable:
            combos.append((c.year_kind, cid))
    return combos


# ---------------------------------------------------------------------------
# Story screenplay
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    collection = COLLECTIONS[params.collection]
    world = World(SHIP)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    mate = world.add(Entity(id=params.crewmate, kind="character", type="child", label=params.crewmate))
    item = world.add(
        Entity(
            id="item",
            type=collection.type,
            label=collection.label,
            phrase=collection.phrase,
            owner=hero.id,
            caretaker=mate.id,
        )
    )
    world.facts["sound_effect"] = collection.sound

    # Act 1
    world.say(
        f"{hero.id} was a little {params.trait} spacer on {world.ship.name}, "
        f"where every year brought a new job for the crew."
    )
    world.say(
        f"{hero.id} loved collecting {collection.label} because {collection.phrase} could be reused instead of thrown away."
    )
    world.say(
        f"{hero.id} and {mate.id} stored the find in a tidy bin, and the bin made a soft little {collection.sound}."
    )

    # Act 2
    world.para()
    _mood(hero, "want", 1)
    world.say(
        f"One {params.year_part}, {hero.id} wanted to keep the {collection.label} all by {hero.pronoun('possessive')} self."
    )
    world.say(
        f"But the ship needed everyone to share, because a recyclable thing can help more than one job."
    )
    _mood(hero, "stubborn", 1)
    _bump(item, "used", 1)
    world.say(
        f"{mate.id} pointed at the repair table and said the {collection.label} could become a tool, a decoration, or a game piece."
    )
    world.say(
        f"{hero.id} frowned, and the little storage room felt quiet except for the distant hum of the engines."
    )

    # Act 3
    world.para()
    _bump(item, "shared", 1)
    item.shared_with.update({hero.id, mate.id})
    _mood(hero, "joy", 1)
    _mood(hero, "love", 1)
    world.say(
        f"Then {hero.id} took a breath and shared the {collection.label} with {mate.id}."
    )
    propagate(world, narrate=True)
    world.say(
        f"Together they made a bright space collage, and the {collection.sound} sound became part of the fun."
    )
    world.say(
        f"By the end of the year, the crew had a useful recycled treasure, and {hero.id} smiled at how much bigger it felt when shared."
    )

    world.facts.update(
        hero=hero,
        mate=mate,
        item=item,
        collection=collection,
        params=params,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    collection: Collection = f["collection"]
    return [
        f'Write a short space-adventure story for a young child about sharing a recyclable {collection.label} on a starship.',
        f"Tell a gentle story where {hero.id} wants to keep a recyclable {collection.label} during the {f['params'].year_part}, but the crew finds a sharing plan.",
        f'Write a child-friendly story in space that includes the sound effect "{collection.sound}" and ends with everyone sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    item = f["item"]
    collection: Collection = f["collection"]
    params: StoryParams = f["params"]
    return [
        QAItem(
            question=f"Who is the story mostly about on the starship?",
            answer=f"The story is mostly about {hero.id}, a little {params.trait} space child who learns to share.",
        ),
        QAItem(
            question=f"What recyclable thing did {hero.id} want to keep?",
            answer=f"{hero.id} wanted to keep {collection.phrase}, but the crew needed it for more than one job.",
        ),
        QAItem(
            question=f"What helped the crew solve the problem?",
            answer=f"Sharing helped. {hero.id} shared the {item.label} with {mate.id}, so everyone could use it.",
        ),
        QAItem(
            question=f"What sound did the recyclable item make?",
            answer=f"It made a {collection.sound} sound, which made the space craft feel playful and lively.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    collection: Collection = f["collection"]
    return [
        QAItem(
            question="What does recyclable mean?",
            answer="Recyclable means something can be used again instead of being thrown away.",
        ),
        QAItem(
            question="Why do people share things on a spaceship?",
            answer="People share things on a spaceship so the whole crew can help with repairs, games, and daily work.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a special sound that helps a story or scene feel more lively, like clang-clink or swish-swish.",
        ),
        QAItem(
            question=f"Why might a recyclable {collection.label} be useful?",
            answer=f"A recyclable {collection.label} can become something new, so it can help with craft, repair, or play.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
recyclable(C) :- collection(C), recyclable_fact(C).
sharing_story(P, C) :- year_part(P), collection(C), recyclable(C), year_match(P, C).
need_share(C) :- sharing_story(_, C).
soundful(C) :- collection(C), sound(C, _).
valid(P, C) :- sharing_story(P, C), need_share(C), soundful(C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("ship", "comet_cart"))
    for part in SHIP.year_cycle:
        lines.append(asp.fact("year_part", part))
    for cid, c in COLLECTIONS.items():
        lines.append(asp.fact("collection", cid))
        lines.append(asp.fact("recyclable_fact", cid))
        lines.append(asp.fact("year_match", c.year_kind, cid))
        lines.append(asp.fact("sound", cid, c.sound))
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
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    collection: str
    name: str
    gender: str
    crewmate: str
    year_part: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld about sharing recyclable things.")
    ap.add_argument("--place", choices=["starship"])
    ap.add_argument("--collection", choices=sorted(COLLECTIONS))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--crewmate", choices=NAMES)
    ap.add_argument("--year-part", choices=["spring", "summer", "autumn", "winter", "new year"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.collection and args.year_part:
        c = COLLECTIONS[args.collection]
        if args.year_part != c.year_kind:
            raise StoryError("That collection does not fit the chosen part of the year.")
    if args.gender and args.name:
        pass
    choices = [c for c in combos if (args.collection is None or c[1] == args.collection)]
    if args.year_part:
        choices = [c for c in choices if c[0] == args.year_part]
    if not choices:
        raise StoryError("No valid space-adventure combination matches the given options.")

    year_part, collection = rng.choice(sorted(choices))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    crewmate = args.crewmate or rng.choice([n for n in NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place="starship",
        collection=collection,
        name=name,
        gender=gender,
        crewmate=crewmate,
        year_part=year_part,
        trait=trait,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.shared_with:
            bits.append(f"shared_with={sorted(e.shared_with)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="starship", collection="can", name="Nova", gender="girl", crewmate="Milo", year_part="summer", trait="curious"),
    StoryParams(place="starship", collection="paper", name="Iris", gender="girl", crewmate="Zane", year_part="autumn", trait="helpful"),
    StoryParams(place="starship", collection="foil", name="Owen", gender="boy", crewmate="Luna", year_part="winter", trait="brave"),
    StoryParams(place="starship", collection="bottle", name="Tess", gender="girl", crewmate="Pia", year_part="spring", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid_combos()
        print(f"{len(vals)} compatible year/collection combos:\n")
        for year_part, collection in vals:
            print(f"  {year_part:8} {collection}")
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
            except StoryError as e:
                print(e)
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
