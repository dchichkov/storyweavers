#!/usr/bin/env python3
"""
storyworlds/worlds/preserve_western_happy_ending_rhyme_slice_of.py
===================================================================

A small slice-of-life story world about a western preserve, a gentle problem,
and a happy ending that sometimes arrives in rhyme.

Premise:
- A child visits a western preserve with a simple plan: gather, save, or share
  something small and meaningful.
- The main tension is practical and local: a jar lid, a trail sign, a basket,
  a bandana, a fence gate, a seed packet, or a lantern can be out of place,
  dry, missing, stuck, or nearly lost.
- The turn is a careful, child-sized act of fixing or preserving.
- The ending proves what changed through one concrete image and a short rhyme.

This script follows the storyworld contract:
- self-contained stdlib world script
- eager import of results containers
- lazy import of storyworlds.asp inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and an inline ASP_RULES twin
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Place:
    id: str
    label: str
    kind: str
    western: bool = True
    affordances: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    location: str
    owner: str = ""
    preserved: bool = False
    needs: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    verb: str
    problem: str
    fix: str
    result: str
    needed_item_kind: str
    needed_place_kind: str
    rhyme_a: str
    rhyme_b: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "child":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_item(self, i: Item) -> Item:
        self.items[i.id] = i
        return i

    def get_entity(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, line: str) -> None:
        self.trace.append(line)

    def render(self) -> str:
        return "\n\n".join(p for p in self.trace if p)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.items = copy.deepcopy(self.items)
        w.facts = copy.deepcopy(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "canyon_trail": Place(
        id="canyon_trail",
        label="the canyon trail",
        kind="trail",
        affordances={"walk", "pick", "fix", "preserve"},
    ),
    "barn_market": Place(
        id="barn_market",
        label="the barn market",
        kind="market",
        affordances={"walk", "buy", "share", "preserve"},
    ),
    "shade_garden": Place(
        id="shade_garden",
        label="the shade garden",
        kind="garden",
        affordances={"walk", "gather", "fix", "preserve"},
    ),
    "river_bend": Place(
        id="river_bend",
        label="the river bend",
        kind="bend",
        affordances={"walk", "fish", "repair", "preserve"},
    ),
}

ITEMS = {
    "jar": Item("jar", "a glass jar", "a glass jar of berry jam", "container", "basket"),
    "sign": Item("sign", "a trail sign", "a small wooden trail sign", "marker", "trail"),
    "basket": Item("basket", "a picnic basket", "a wicker picnic basket", "basket", "bench"),
    "bandana": Item("bandana", "a red bandana", "a red bandana with a bright knot", "cloth", "pocket"),
    "gate": Item("gate", "a fence gate", "a little fence gate", "gate", "fence"),
    "seed_packet": Item("seed packet", "a seed packet", "a seed packet of wildflowers", "packet", "pouch"),
    "lantern": Item("lantern", "a lantern", "a tin lantern for dusk", "light", "hook"),
}

EVENTS = {
    "mend_sign": Event(
        id="mend_sign",
        verb="fix",
        problem="the trail sign leaned sideways",
        fix="straighten the sign and tighten the nail",
        result="the sign stood clear again",
        needed_item_kind="marker",
        needed_place_kind="trail",
        rhyme_a="bright",
        rhyme_b="kite",
        tags={"trail", "fix", "rhyme"},
    ),
    "save_jam": Event(
        id="save_jam",
        verb="preserve",
        problem="the berry jam jar had a loose lid",
        fix="twist the lid tight and tuck the jar safely in a basket",
        result="the jam stayed sweet and safe",
        needed_item_kind="container",
        needed_place_kind="market",
        rhyme_a="glow",
        rhyme_b="slow",
        tags={"jar", "preserve", "sweet", "rhyme"},
    ),
    "patch_gate": Event(
        id="patch_gate",
        verb="repair",
        problem="the fence gate swung open in the wind",
        fix="hold the gate steady and tie it with a cord",
        result="the gate shut with a soft click",
        needed_item_kind="gate",
        needed_place_kind="garden",
        rhyme_a="tight",
        rhyme_b="night",
        tags={"gate", "repair", "rhyme"},
    ),
    "dry_bandana": Event(
        id="dry_bandana",
        verb="preserve",
        problem="the red bandana was damp from the river spray",
        fix="hang the bandana on a warm hook in the sun",
        result="the cloth dried bright and neat",
        needed_item_kind="cloth",
        needed_place_kind="bend",
        rhyme_a="warm",
        rhyme_b="storm",
        tags={"cloth", "preserve", "rhyme"},
    ),
    "plant_seeds": Event(
        id="plant_seeds",
        verb="preserve",
        problem="the seed packet was about to tear in the wind",
        fix="smooth the packet flat and tuck it into a pouch",
        result="the wildflower seeds stayed ready for spring",
        needed_item_kind="packet",
        needed_place_kind="garden",
        rhyme_a="nest",
        rhyme_b="best",
        tags={"packet", "seed", "preserve", "rhyme"},
    ),
    "hang_lantern": Event(
        id="hang_lantern",
        verb="save",
        problem="the lantern was nearly knocked from its hook",
        fix="lift the lantern back up and hang it safely high",
        result="the little light waited for evening",
        needed_item_kind="light",
        needed_place_kind="trail",
        rhyme_a="high",
        rhyme_b="sky",
        tags={"light", "save", "rhyme"},
    ),
}

CHILD_NAMES = ["Mina", "June", "Tess", "Lena", "Ruby", "Nora", "Ivy", "Ada"]
ADULT_NAMES = ["Marta", "Evan", "Rosa", "Dale"]
TRAITS = ["quiet", "careful", "cheerful", "gentle", "curious"]

# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    event: str
    child_name: str
    adult_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def reason_ok(place: Place, event: Event, item: Item) -> bool:
    return (
        place.kind == event.needed_place_kind
        and item.kind == event.needed_item_kind
        and "preserve" in place.affordances
    )


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for eid, event in EVENTS.items():
            for iid, item in ITEMS.items():
                if reason_ok(place, event, item):
                    out.append((pid, eid, iid))
    return sorted(out)


def explain_rejection(place: Place, event: Event, item: Item) -> str:
    return (
        f"(No story: {place.label} does not fit the problem {event.problem}, "
        f"or {item.label} is not the right thing to fix or preserve. "
        f"Try a place and object that naturally go together.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    event = EVENTS[params.event]
    item = ITEMS[next(iid for iid in ITEMS if reason_ok(place, event, ITEMS[iid]))]
    world = World(place)
    child = world.add_entity(Entity(id=params.child_name, kind="child", label=params.child_name, type="child"))
    adult = world.add_entity(Entity(id=params.adult_name, kind="adult", label=params.adult_name, type="adult"))
    story_item = world.add_item(Item(**{**item.__dict__}))

    child.memes["hope"] = 1.0
    child.memes["worry"] = 0.0
    child.meters["steps"] = 0.0

    world.facts.update(
        child=child,
        adult=adult,
        item=story_item,
        event=event,
        place=place,
        preserved=False,
        fixed=False,
    )

    world.say(
        f"{child.label} and {adult.label} went to {place.label} on a calm afternoon."
    )
    world.say(
        f"{child.label} noticed {event.problem}, and {child.label} wanted to {event.verb} it before it was too late."
    )
    child.memes["worry"] += 1.0
    child.meters["steps"] += 2.0
    world.say(
        f"{adult.label} looked with kind eyes and said they could help."
    )
    world.say(
        f"Together they chose to {event.fix}, because small things are easier to keep when hands work side by side."
    )
    story_item.preserved = True
    world.facts["preserved"] = True
    world.facts["fixed"] = event.verb == "fix"
    child.memes["joy"] = 1.0
    child.memes["worry"] = 0.0
    world.say(
        f"{event.result}. {child.label} smiled, and the day felt light again."
    )
    world.say(
        f'"{event.rhyme_a} and {event.rhyme_b}," said {child.label}, and the western sky looked extra bright.'
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    event = world.facts["event"]
    place = world.facts["place"]
    item = world.facts["item"]
    child = world.facts["child"]
    return [
        f"Write a slice-of-life story about {child.label} at {place.label} where someone helps {event.verb} {item.label}.",
        f"Tell a gentle western story that includes the idea of {event.verb} and ends with a happy little rhyme.",
        f"Write a child-friendly story about preserving something small at {place.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    event = world.facts["event"]
    child = world.facts["child"]
    adult = world.facts["adult"]
    item = world.facts["item"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"Where did {child.label} and {adult.label} go?",
            answer=f"They went to {place.label}, a quiet western place where a small problem could be fixed."
        ),
        QAItem(
            question=f"What needed help in the story?",
            answer=f"{event.problem.capitalize()}, so they worked together to {event.fix}."
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"{event.result.capitalize()}, and {child.label} could smile at the safe, neat little thing they had preserved."
        ),
        QAItem(
            question=f"Why was {item.label} important?",
            answer=f"It was the item that needed care, so keeping it safe helped make the happy ending possible."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    place = world.facts["place"]
    event = world.facts["event"]
    items = world.facts["item"]
    out = [
        QAItem(
            question="What does preserve mean?",
            answer="To preserve something means to keep it safe, clean, or in good shape so it can last longer."
        ),
        QAItem(
            question="What is a western setting?",
            answer=f"A western setting is a place like {place.label}, with open air, dusty paths, or simple country details."
        ),
        QAItem(
            question="Why do people fix small things right away?",
            answer="Small things are easier to care for when they are handled early, before they become bigger problems."
        ),
        QAItem(
            question="What makes the ending feel happy?",
            answer="The ending feels happy because the problem is solved, the object is safe again, and everyone can relax."
        ),
    ]
    if "rhyme" in event.tags:
        out.append(
            QAItem(
                question="What is a rhyme?",
                answer="A rhyme is when words sound alike at the end, like bright and kite."
            )
        )
    if items.kind in {"container", "cloth", "gate", "light", "packet"}:
        out.append(
            QAItem(
                question=f"Why is {items.label} easy to care for?",
                answer=f"{items.label.capitalize()} is the kind of thing people can protect by handling it gently and putting it in the right place."
            )
        )
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place_ok(P,trail) :- place(P), kind(P,trail).
place_ok(P,market) :- place(P), kind(P,market).
place_ok(P,garden) :- place(P), kind(P,garden).
place_ok(P,bend) :- place(P), kind(P,bend).

event_ok(E,trail,marker) :- event(E), needs_place(E,trail), needs_item(E,marker).
event_ok(E,market,container) :- event(E), needs_place(E,market), needs_item(E,container).
event_ok(E,garden,gate) :- event(E), needs_place(E,garden), needs_item(E,gate).
event_ok(E,bend,cloth) :- event(E), needs_place(E,bend), needs_item(E,cloth).
event_ok(E,garden,packet) :- event(E), needs_place(E,garden), needs_item(E,packet).
event_ok(E,trail,light) :- event(E), needs_place(E,trail), needs_item(E,light).

valid_story(P,E,I) :- place_ok(P,K), event_ok(E,K,T), item(I), item_kind(I,T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("kind", pid, place.kind))
        if place.western:
            lines.append(asp.fact("western", pid))
        for a in sorted(place.affordances):
            lines.append(asp.fact("affords", pid, a))
    for eid, event in EVENTS.items():
        lines.append(asp.fact("event", eid))
        lines.append(asp.fact("needs_place", eid, event.needed_place_kind))
        lines.append(asp.fact("needs_item", eid, event.needed_item_kind))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_kind", iid, item.kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python reasonableness gate ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and ASP:")
    if py - asp_set:
        print("  only in Python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in ASP:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------
def choose_reasonable_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str]:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.event:
        combos = [c for c in combos if c[1] == args.event]
    if args.item:
        combos = [c for c in combos if c[2] == args.item]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    return rng.choice(sorted(combos))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place, event, item = choose_reasonable_combo(args, rng)
    return StoryParams(
        place=place,
        event=event,
        child_name=args.name or rng.choice(CHILD_NAMES),
        adult_name=args.adult or rng.choice(ADULT_NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print()
        print("--- world trace ---")
        for line in sample.world.trace:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life western preserve story world with a happy ending and rhyme."
    )
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--event", choices=EVENTS.keys())
    ap.add_argument("--item", choices=ITEMS.keys())
    ap.add_argument("--name")
    ap.add_argument("--adult")
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


def curated() -> list[StoryParams]:
    return [
        StoryParams(place="canyon_trail", event="mend_sign", child_name="Mina", adult_name="Dale", trait="careful"),
        StoryParams(place="barn_market", event="save_jam", child_name="June", adult_name="Rosa", trait="cheerful"),
        StoryParams(place="shade_garden", event="patch_gate", child_name="Tess", adult_name="Marta", trait="gentle"),
        StoryParams(place="river_bend", event="dry_bandana", child_name="Lena", adult_name="Evan", trait="curious"),
        StoryParams(place="shade_garden", event="plant_seeds", child_name="Ruby", adult_name="Rosa", trait="quiet"),
        StoryParams(place="canyon_trail", event="hang_lantern", child_name="Nora", adult_name="Dale", trait="cheerful"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for p, e, i in triples:
            print(f"  {p:14} {e:12} {i}")
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
            header = f"### {p.child_name}: {p.event} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
