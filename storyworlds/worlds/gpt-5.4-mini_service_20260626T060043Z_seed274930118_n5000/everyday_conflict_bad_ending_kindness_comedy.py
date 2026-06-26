#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/everyday_conflict_bad_ending_kindness_comedy.py
===========================================================================================================

A small everyday storyworld about a tiny conflict, a kind idea, and a comedic
bad ending.

Premise:
- A child wants to use an everyday thing right now.
- A second person wants it too, or worries about it.
- A kind gesture tries to fix the problem.
- The fix may fail in a comic way, leaving a small bad ending image.

This world is intentionally compact and self-contained. It models:
- physical meters: wet, messy, broken, tired, safe
- emotional memes: want, worry, conflict, kindness, laugh, disappointment

The prose is generated from simulated state, not from a fixed paragraph shell.
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

    def __post_init__(self) -> None:
        for k in ["wet", "messy", "broken", "tired", "safe"]:
            self.meters.setdefault(k, 0.0)
        for k in ["want", "worry", "conflict", "kindness", "laugh", "disappointment"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    key: str
    name: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Thing:
    key: str
    label: str
    phrase: str
    risk: str
    mishap: str
    location: str
    shareable: bool = True


@dataclass
class Offer:
    key: str
    label: str
    action: str
    helps: set[str]
    comic_backfire: str


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.lines: list[str] = []
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = _copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    place: str
    thing: str
    offer: str
    child: str
    child_type: str
    other: str
    other_type: str
    seed: Optional[int] = None


PLACES = {
    "kitchen": Place("kitchen", "the kitchen", True, {"sharing", "spill", "cookie"}),
    "playground": Place("playground", "the playground", False, {"sharing", "swing", "rain"}),
    "bus_stop": Place("bus_stop", "the bus stop", False, {"sharing", "umbrella", "rain"}),
    "laundry_room": Place("laundry_room", "the laundry room", True, {"sharing", "basket", "spill"}),
}

THINGS = {
    "cookie": Thing("cookie", "cookie", "the last cookie on the plate", "crumbly", "crumbled", "table"),
    "umbrella": Thing("umbrella", "umbrella", "one little umbrella", "wet", "inside out", "hall"),
    "swing": Thing("swing", "swing", "the only swing", "shared", "stuck", "yard"),
    "basket": Thing("basket", "basket", "the laundry basket", "tippy", "spilled", "floor"),
}

OFFERS = {
    "share": Offer("share", "sharing", "share it nicely", {"cookie", "umbrella", "swing", "basket"}, "someone bumps the thing"),
    "trade": Offer("trade", "trading", "trade places for a turn", {"swing", "basket"}, "the trade turns into a queue"),
    "kind_note": Offer("kind_note", "kind note", "leave a kind note and wait", {"cookie", "basket"}, "the note gets sticky"),
    "help_hold": Offer("help_hold", "helping hands", "hold it together carefully", {"umbrella", "basket"}, "the thing flops anyway"),
}

GIRL_NAMES = ["Mia", "Luna", "Zoe", "Ava", "Nora", "Lily"]
BOY_NAMES = ["Finn", "Max", "Owen", "Leo", "Sam", "Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES.values():
        for thing in THINGS.values():
            if thing.risk in place.affords:
                for offer in OFFERS.values():
                    if thing.key in offer.helps:
                        combos.append((place.key, thing.key, offer.key))
    return combos


def reasonableness_gate(place: Place, thing: Thing, offer: Offer) -> None:
    if thing.risk not in place.affords:
        raise StoryError(f"(No story: {thing.label} does not fit an everyday problem at {place.name}.)")
    if thing.key not in offer.helps:
        raise StoryError(f"(No story: {offer.label} does not reasonably help with {thing.label}.)")


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    thing = THINGS[params.thing]
    offer = OFFERS[params.offer]
    reasonableness_gate(place, thing, offer)

    world = World(place)
    child = world.add(Entity(id=params.child, kind="character", type=params.child_type, label=params.child))
    other = world.add(Entity(id=params.other, kind="character", type=params.other_type, label=params.other))
    item = world.add(Entity(id=thing.key, kind="thing", type=thing.key, label=thing.label, phrase=thing.phrase, caretaker=other.id))
    item.owner = child.id

    child.memes["want"] += 1
    other.memes["worry"] += 1
    world.facts.update(place=place, thing=thing, offer=offer, child=child, other=other, item=item)

    world.say(f"{child.noun()} was in {place.name}, and {child.pronoun()} really wanted {thing.phrase}.")
    world.say(f"But {other.pronoun('possessive')} {thing.label} was there too, and that made a little everyday problem.")
    world.say(f"{child.pronoun().capitalize()} asked first, and {other.pronoun()} said they should be careful.")

    child.memes["conflict"] += 1
    other.memes["conflict"] += 1
    world.say(f"Both of them frowned for a moment, because nobody likes the same thing at the same time.")

    world.say(f"Then {other.noun()} tried {offer.action}, which sounded kind.")
    child.memes["kindness"] += 1
    other.memes["kindness"] += 1

    # Simulated backfire: the kind fix does not quite work.
    if thing.key == "cookie":
        item.meters["broken"] += 1
        item.meters["messy"] += 1
        child.memes["laugh"] += 1
        other.memes["disappointment"] += 1
        world.say(f"The cookie broke in half, then the crumbs jumped onto the table like tiny confetti.")
        world.say(f"That was kind, but not tidy at all.")
    elif thing.key == "umbrella":
        item.meters["wet"] += 1
        item.meters["broken"] += 1
        child.meters["wet"] += 1
        other.meters["wet"] += 1
        child.memes["laugh"] += 1
        world.say(f"The umbrella flipped inside out with a silly pop, and both of them got splashed.")
        world.say(f"Kindness helped a little, but the wind had other ideas.")
    elif thing.key == "swing":
        item.meters["safe"] += 1
        item.meters["broken"] += 1
        child.memes["disappointment"] += 1
        other.memes["laugh"] += 1
        world.say(f"They took turns very politely, but the swing chain made a squeak and stopped moving.")
        world.say(f"That was a comedy of patience, and also a bad ending for fun.")
    else:
        item.meters["messy"] += 1
        item.meters["broken"] += 1
        child.meters["wet"] += 1
        other.meters["wet"] += 1
        world.say(f"The basket tipped, the socks slid out, and one shoe landed in a silly heap.")
        world.say(f"They laughed, then had to pick everything up again.")

    # Ending image proves change.
    if item.meters["broken"] >= THRESHOLD or item.meters["messy"] >= THRESHOLD or item.meters["wet"] >= THRESHOLD:
        child.memes["disappointment"] += 1

    if child.memes["laugh"] >= THRESHOLD:
        world.say(f"In the end, {child.id} was laughing at the mess, even though the day had gone a bit wrong.")
    else:
        world.say(f"In the end, {child.id} looked at the mess and sighed, because the nice plan did not save the day.")

    world.say(f"{thing.phrase.capitalize()} was no longer the same, and the room looked like a tiny comic disaster.")

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = f["place"]
    thing: Thing = f["thing"]
    offer: Offer = f["offer"]
    child: Entity = f["child"]
    other: Entity = f["other"]
    return [
        f'Write a short, funny everyday story set in {place.name} about {child.noun()} and {other.noun()} arguing over {thing.phrase}.',
        f"Tell a comedy story where kindness tries to fix a small conflict about a {thing.label}, but the fix goes wrong in a bad ending.",
        f'Write a child-friendly story that includes {offer.label}, everyday trouble, and a silly ending image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    place: Place = f["place"]
    thing: Thing = f["thing"]
    offer: Offer = f["offer"]
    child: Entity = f["child"]
    other: Entity = f["other"]

    return [
        QAItem(
            question=f"What everyday problem happened in {place.name}?",
            answer=f"{child.id} and {other.id} both wanted {thing.phrase}, so they had a small conflict about sharing it.",
        ),
        QAItem(
            question=f"What kind thing did {other.id} try to do?",
            answer=f"{other.id} tried {offer.action}, because {other.pronoun()} wanted to be kind even though the problem was annoying.",
        ),
        QAItem(
            question=f"Why was the ending a bad one?",
            answer=f"The kind idea backfired: {thing.label} got {ending_word(thing)}, messy, or broken, so the day ended with a comic mess instead of a clean fix.",
        ),
    ]


def ending_word(thing: Thing) -> str:
    return {
        "cookie": "crumbled",
        "umbrella": "flipped inside out",
        "swing": "stuck",
        "basket": "spilled",
    }.get(thing.key, "ruined")


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    thing: Thing = f["thing"]
    offer: Offer = f["offer"]
    qa = [
        QAItem(
            question="What is kindness?",
            answer="Kindness means doing something gentle, helpful, or thoughtful for someone else.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is when people want different things, or when they disagree and feel upset for a while.",
        ),
        QAItem(
            question=f"Why can a {thing.label} be tricky to share?",
            answer=f"A {thing.label} can be tricky to share because it is small, useful, or tempting, so two people may want it at once.",
        ),
        QAItem(
            question=f"What does {offer.label} usually try to do?",
            answer=f"{offer.label.capitalize()} is a way to reduce a problem by being fair, careful, or helpful.",
        ),
    ]
    return qa


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.key))
        if p.indoors:
            lines.append(asp.fact("indoors", p.key))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", p.key, a))
    for t in THINGS.values():
        lines.append(asp.fact("thing", t.key))
        lines.append(asp.fact("risk", t.key, t.risk))
        lines.append(asp.fact("mishap", t.key, t.mishap))
    for o in OFFERS.values():
        lines.append(asp.fact("offer", o.key))
        for x in sorted(o.helps):
            lines.append(asp.fact("helps", o.key, x))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Thing, Offer) :- affords(Place, Risk), risk(Thing, Risk), helps(Offer, Thing).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Everyday conflict, kindness, and a comic bad ending.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--thing", choices=THINGS.keys())
    ap.add_argument("--offer", choices=OFFERS.keys())
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--other")
    ap.add_argument("--other-type", choices=["girl", "boy"])
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
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.thing is None or c[1] == args.thing)
        and (args.offer is None or c[2] == args.offer)
    ]
    if not filtered:
        raise StoryError("(No valid everyday conflict story matches those options.)")
    place, thing, offer = rng.choice(sorted(filtered))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    other_type = args.other_type or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    other = args.other or rng.choice(GIRL_NAMES if other_type == "girl" else BOY_NAMES)
    return StoryParams(place=place, thing=thing, offer=offer, child=child, child_type=child_type, other=other, other_type=other_type)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="kitchen", thing="cookie", offer="share", child="Mia", child_type="girl", other="Max", other_type="boy"),
    StoryParams(place="bus_stop", thing="umbrella", offer="help_hold", child="Finn", child_type="boy", other="Luna", other_type="girl"),
    StoryParams(place="playground", thing="swing", offer="trade", child="Ava", child_type="girl", other="Ben", other_type="boy"),
    StoryParams(place="laundry_room", thing="basket", offer="kind_note", child="Leo", child_type="boy", other="Nora", other_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
