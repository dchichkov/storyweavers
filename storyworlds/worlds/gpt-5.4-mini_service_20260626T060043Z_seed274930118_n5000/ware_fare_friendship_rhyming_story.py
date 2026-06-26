#!/usr/bin/env python3
"""
A small story world about friendship, ware, and fare in a rhyming-story style.

Seed idea:
- A child has a treasured piece of ware.
- A friend arrives with fare to share.
- A small problem puts the ware at risk.
- Friendship turns the moment into a kind, rhyming solution.
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
# Registries
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class WareItem:
    key: str
    label: str
    phrase: str
    kind: str
    place: str
    treasured: bool = True
    rhymes_with: str = ""


@dataclass(frozen=True)
class FareItem:
    key: str
    label: str
    phrase: str
    kind: str
    shares_well: bool = True
    rhymes_with: str = ""


@dataclass(frozen=True)
class PlaceItem:
    key: str
    label: str
    indoor: bool
    invites: set[str] = field(default_factory=set)


WARES = {
    "cloak": WareItem("cloak", "cloak", "a soft blue cloak", "clothing", "path", True, "broke"),
    "cap": WareItem("cap", "cap", "a little red cap", "clothing", "garden", True, "snap"),
    "boots": WareItem("boots", "boots", "muddy little boots", "clothing", "yard", True, "coats"),
    "kite": WareItem("kite", "kite", "a bright paper kite", "toy", "hill", True, "light"),
    "lantern": WareItem("lantern", "lantern", "a tiny gold lantern", "object", "porch", True, "glow"),
}

FARES = {
    "pie": FareItem("pie", "pie", "warm berry pie", "food", True, "sky"),
    "bread": FareItem("bread", "bread", "fresh oat bread", "food", True, "glad"),
    "jam": FareItem("jam", "jam", "sweet plum jam", "food", True, "clam"),
    "tea": FareItem("tea", "tea", "gentle mint tea", "drink", True, "glee"),
    "pear": FareItem("pear", "pear", "a ripe green pear", "food", True, "share"),
}

PLACES = {
    "path": PlaceItem("path", "the path", False, {"cloak", "tea", "pie"}),
    "garden": PlaceItem("garden", "the garden", False, {"cap", "bread", "jam"}),
    "yard": PlaceItem("yard", "the yard", False, {"boots", "pear"}),
    "hill": PlaceItem("hill", "the hill", False, {"kite", "pie"}),
    "porch": PlaceItem("porch", "the porch", True, {"lantern", "tea", "bread"}),
}

NAMES = ["Mia", "Nora", "Lina", "Tess", "Ruby", "Finn", "Owen", "Eli", "Pip", "June"]
FRIEND_NAMES = ["Bea", "Noa", "Ira", "Remy", "Sage", "Wren", "Kit", "Jules"]
TRAITS = ["kind", "bright", "cheerful", "gentle", "quick", "bold"]

THRESHOLD = 1.0


@dataclass
class StoryParams:
    place: str
    ware: str
    fare: str
    name: str
    friend: str
    trait: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    shared_with: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, place: PlaceItem):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
# Story simulation
# ---------------------------------------------------------------------------
def _rhyming_setup(name: str, trait: str, ware: WareItem, fare: FareItem, place: PlaceItem) -> str:
    return f"{name} was a {trait} child with {ware.phrase}, and {name} loved the smell of {fare.phrase}."


def _friendship_line(name: str, friend: str) -> str:
    return f"{name} and {friend} were friends who liked to share and care."


def _arrival_line(name: str, friend: str, place: PlaceItem, ware: WareItem, fare: FareItem) -> str:
    return f"One day at {place.label}, {friend} came by with {fare.phrase} and a grin so rare."


def _risk_line(ware: WareItem) -> str:
    return f"{name_article(ware)} {ware.label} was in a spot to get sticky, and maybe not fair."


def name_article(item: WareItem) -> str:
    return "the" if item.label[0] in "aeiou" else "the"


def risk_of_fare(place: PlaceItem, ware: WareItem, fare: FareItem) -> bool:
    if ware.kind == "clothing" and fare.kind == "food":
        return place.key in {"path", "garden", "yard", "hill", "porch"}
    if ware.kind == "toy" and fare.kind == "food":
        return place.key in {"hill", "porch", "path"}
    if ware.kind == "object" and fare.kind == "food":
        return place.key in {"porch", "path"}
    return False


def friendship_fix(ware: WareItem, fare: FareItem) -> bool:
    return ware.kind in {"clothing", "toy", "object"} and fare.shares_well


def tell_story(world: World, params: StoryParams) -> World:
    name = params.name
    friend = params.friend
    ware = WARES[params.ware]
    fare = FARES[params.fare]
    place = PLACES[params.place]

    hero = world.add(Entity(id="hero", kind="character", label=name))
    pal = world.add(Entity(id="friend", kind="character", label=friend))
    item = world.add(Entity(id="ware", kind="thing", label=ware.label, phrase=ware.phrase, owner=hero.id))
    snack = world.add(Entity(id="fare", kind="thing", label=fare.label, phrase=fare.phrase, owner=pal.id))

    world.say(_rhyming_setup(name, params.trait, ware, fare, place))
    world.say(_friendship_line(name, friend))

    world.para()
    world.say(_arrival_line(name, friend, place, ware, fare))
    if not risk_of_fare(place, ware, fare):
        world.say(f"But that day was calm, and no trouble came to share.")
        world.say(f"They sat and smiled, and the fare stayed neat and bare.")
        world.facts.update(resolved=False)
        return world

    hero.memes["worry"] = 1.0
    world.say(f"But {fare.phrase} could spill, and {ware.phrase} could get a smear or snare.")
    world.say(f"{name} frowned a little and held {ware.phrase} with care.")
    world.say(f"{friend} saw the frown and said, “My friend, let's make a pair:")
    world.say(f"We can keep the {ware.label} safe and still enjoy the fare.”")

    if friendship_fix(ware, fare):
        hero.memes["joy"] = 1.0
        pal.memes["kindness"] = 1.0
        item.meters["safe"] = 1.0
        snack.meters["shared"] = 1.0
        world.say(f"They moved to the porch or the path, a tidy little lair.")
        if ware.kind == "clothing":
            world.say(f"{friend} wiped hands first, so the {ware.label} stayed fine and fair.")
        elif ware.kind == "toy":
            world.say(f"{name} set the {ware.label} high, above the crumbs in air.")
        else:
            world.say(f"They put the {ware.label} aside, then ate the fare with cheerful stare.")
        world.say(f"They shared the snack and laughed, and friendship filled the air.")
        world.say(f"The day ended bright: the {ware.label} was safe, the fare was fair.")
        world.facts.update(resolved=True)
    else:
        world.say(f"They tried, but could not find a kind and proper care.")
        world.say(f"So they saved the {ware.label} for later and ate the fare elsewhere.")
        world.facts.update(resolved=False)

    world.facts.update(hero=hero, friend=pal, ware=item, fare=snack, ware_cfg=ware, fare_cfg=fare, place=place)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for young children about friendship, "{f["ware_cfg"].label}", and "{f["fare_cfg"].label}".',
        f'Tell a gentle tale where {f["hero"].label} and {f["friend"].label} share {f["fare_cfg"].phrase} without ruining the {f["ware_cfg"].label}.',
        f'Write a simple friendship story set at {f["place"].label} with a bit of worry and a kind fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    ware = f["ware_cfg"]
    fare = f["fare_cfg"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The friends were {hero.label} and {friend.label}. They cared about each other and shared the day kindly.",
        ),
        QAItem(
            question=f"What {ware.label} did {hero.label} want to keep safe?",
            answer=f"{hero.label} wanted to keep {ware.phrase} safe while spending time with a friend.",
        ),
        QAItem(
            question=f"What {fare.label} did {friend.label} bring?",
            answer=f"{friend.label} brought {fare.phrase} to share at {place.label}.",
        ),
        QAItem(
            question=f"Why did the {ware.label} matter in the story?",
            answer=f"The {ware.label} mattered because it was treasured, and the friends did not want the fare to make it messy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let someone else use, eat, or enjoy something with you.",
        ),
        QAItem(
            question="What is fare in a story like this?",
            answer="Fare is food or drink that someone brings, serves, or shares with others.",
        ),
        QAItem(
            question="Why do friends help each other?",
            answer="Friends help each other because friendship means being kind, careful, and ready to care.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_story(P, W, F) :- place(P), ware(W), fare(F), risky(P, W, F), can_fix(W, F).
risky(P, W, F) :- place(P), ware(W), fare(F), ware_kind(W, clothing), fare_kind(F, food).
can_fix(W, F) :- ware(W), fare(F), friendly_share(F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.key))
    for w in WARES.values():
        lines.append(asp.fact("ware", w.key))
        lines.append(asp.fact("ware_kind", w.key, w.kind))
    for f in FARES.values():
        lines.append(asp.fact("fare", f.key))
        lines.append(asp.fact("fare_kind", f.key, f.kind))
        if f.shares_well:
            lines.append(asp.fact("friendly_share", f.key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid_stories() -> list[tuple]:
    out = []
    for p in PLACES.values():
        for w in WARES.values():
            for f in FARES.values():
                if risk_of_fare(p, w, f) and friendship_fix(w, f):
                    out.append((p.key, w.key, f.key))
    return sorted(out)


def asp_verify() -> int:
    a = set(asp_valid_stories())
    b = set(python_valid_stories())
    if a == b:
        print(f"OK: clingo gate matches python gate ({len(a)} stories).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming friendship story world with ware and fare.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ware", choices=WARES)
    ap.add_argument("--fare", choices=FARES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--trait")
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
    if args.ware and args.fare:
        w = WARES[args.ware]
        f = FARES[args.fare]
        if not (risk_of_fare(PLACES[args.place], w, f) if args.place else True):
            raise StoryError("That ware and fare do not create a meaningful friendship worry.")
    valid = []
    for p in PLACES:
        for w in WARES:
            for f in FARES:
                if args.place and p != args.place:
                    continue
                if args.ware and w != args.ware:
                    continue
                if args.fare and f != args.fare:
                    continue
                if risk_of_fare(PLACES[p], WARES[w], FARES[f]) and friendship_fix(WARES[w], FARES[f]):
                    valid.append((p, w, f))
    if not valid:
        raise StoryError("No valid combination matches the requested options.")
    place, ware, fare = rng.choice(sorted(valid))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, ware=ware, fare=fare, name=name, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(World(PLACES[params.place]), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
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
    StoryParams(place="porch", ware="lantern", fare="tea", name="Mia", friend="Bea", trait="gentle"),
    StoryParams(place="path", ware="cloak", fare="pie", name="Finn", friend="Wren", trait="kind"),
    StoryParams(place="garden", ware="cap", fare="bread", name="Ruby", friend="Kit", trait="cheerful"),
    StoryParams(place="yard", ware="boots", fare="pear", name="Owen", friend="Jules", trait="bold"),
    StoryParams(place="hill", ware="kite", fare="pie", name="June", friend="Sage", trait="bright"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print(" ", s)
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
            header = f"### {p.name}: ware={p.ware}, fare={p.fare}, place={p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
