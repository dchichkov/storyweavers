#!/usr/bin/env python3
"""
Storyworld: nature_stub_twist_adventure
=======================================

A small adventure world about a child exploring a natural place, noticing a
stub, and finding that the path takes a twist that changes the plan.

The story model is intentionally simple:
- a hero wants to explore a nature place
- they notice a stub on the path
- a twist changes what they need to do
- the ending proves the change with a concrete image

The world stays close to an adventure tone: calm outdoors, a small challenge,
a useful turn, and a satisfying finish.
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
# Domain registries
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Place:
    id: str
    name: str
    detail: str
    path_kind: str
    has_water: bool = False
    has_trees: bool = False
    has_hills: bool = False


@dataclass(frozen=True)
class ObjectKind:
    id: str
    label: str
    phrase: str
    risk: str
    helps_with: str
    portable: bool = True


@dataclass(frozen=True)
class TwistKind:
    id: str
    name: str
    reveal: str
    action: str
    ending_image: str


PLACES: dict[str, Place] = {
    "forest": Place(
        id="forest",
        name="the forest",
        detail="Tall trees leaned over the path, and the air smelled green and fresh.",
        path_kind="trail",
        has_trees=True,
        has_hills=False,
    ),
    "meadow": Place(
        id="meadow",
        name="the meadow",
        detail="Soft grass waved in the breeze, and tiny flowers dotted the ground.",
        path_kind="path",
        has_water=False,
        has_hills=True,
    ),
    "riverbank": Place(
        id="riverbank",
        name="the riverbank",
        detail="Water glittered beside the path, and reeds rustled near the edge.",
        path_kind="track",
        has_water=True,
        has_trees=True,
    ),
}

OBJECTS: dict[str, ObjectKind] = {
    "map": ObjectKind(
        id="map",
        label="map",
        phrase="a folded paper map with a bright blue line",
        risk="could tear or flutter away",
        helps_with="finding the right turn",
    ),
    "lantern": ObjectKind(
        id="lantern",
        label="lantern",
        phrase="a small lantern with a warm yellow glow",
        risk="could go out if it got wet",
        helps_with="seeing the path in dim shade",
    ),
    "boots": ObjectKind(
        id="boots",
        label="boots",
        phrase="sturdy boots with thick soles",
        risk="could get muddy",
        helps_with="crossing damp ground",
    ),
    "basket": ObjectKind(
        id="basket",
        label="basket",
        phrase="a woven basket for gathering berries",
        risk="could fill up too fast",
        helps_with="carrying little finds",
    ),
}

TWISTS: dict[str, TwistKind] = {
    "hidden_bridge": TwistKind(
        id="hidden_bridge",
        name="a hidden bridge",
        reveal="the trail bent behind the trees and opened onto a little bridge no one could see from far away",
        action="cross the bridge",
        ending_image="the child standing safely on the other side with the river sparkling below",
    ),
    "baby_deer": TwistKind(
        id="baby_deer",
        name="a baby deer",
        reveal="a tiny deer stepped out from the brush and stared with wide, shiny eyes",
        action="move slowly and keep quiet",
        ending_image="the child kneeling still and gentle while the deer wandered back into the trees",
    ),
    "rain_shelter": TwistKind(
        id="rain_shelter",
        name="a rain shelter",
        reveal="the sky changed, and a small shelter appeared around the next bend like a secret",
        action="hurry to the shelter",
        ending_image="the child listening to raindrops drum on the roof while staying dry and safe",
    ),
}


# ---------------------------------------------------------------------------
# Shared result model
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    object_kind: str
    twist: str
    hero_name: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    object_kind: ObjectKind
    twist: TwistKind
    hero_name: str
    meters: dict[str, float] = field(default_factory=lambda: {
        "distance": 0.0,
        "attention": 0.0,
        "calm": 0.0,
        "wonder": 0.0,
        "safety": 0.0,
    })
    memes: dict[str, float] = field(default_factory=lambda: {
        "curiosity": 0.0,
        "worry": 0.0,
        "delight": 0.0,
        "bravery": 0.0,
    })
    facts: dict[str, str] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def note(self, text: str) -> None:
        self.trace.append(text)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(place: Place, obj: ObjectKind, twist: TwistKind) -> bool:
    if obj.id == "lantern" and not (place.has_trees or place.has_hills):
        return False
    if obj.id == "boots" and place.id == "riverbank" and twist.id == "baby_deer":
        return True
    if obj.id == "map" and twist.id == "hidden_bridge":
        return True
    if obj.id == "basket" and twist.id == "hidden_bridge":
        return True
    if obj.id == "lantern" and twist.id == "rain_shelter":
        return True
    if obj.id == "boots" and twist.id == "rain_shelter":
        return True
    if obj.id == "basket" and twist.id == "baby_deer":
        return False
    return True


def explain_rejection(place: Place, obj: ObjectKind, twist: TwistKind) -> str:
    return (
        f"(No story: {obj.label} and {twist.name} do not make a strong adventure here "
        f"at {place.name}. Try a different object and twist that fit the place.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place_valid(P) :- place(P).
object_valid(O) :- object(O).
twist_valid(T) :- twist(T).

valid(P,O,T) :- place_valid(P), object_valid(O), twist_valid(T), combo_ok(P,O,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.has_water:
            lines.append(asp.fact("has_water", pid))
        if p.has_trees:
            lines.append(asp.fact("has_trees", pid))
        if p.has_hills:
            lines.append(asp.fact("has_hills", pid))
        lines.append(asp.fact("path_kind", pid, p.path_kind))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("helps_with", oid, o.helps_with))
    for tid, t in TWISTS.items():
        lines.append(asp.fact("twist", tid))
        lines.append(asp.fact("twist_name", tid, t.name))
    for pid in PLACES:
        for oid in OBJECTS:
            for tid in TWISTS:
                if valid_combo(PLACES[pid], OBJECTS[oid], TWISTS[tid]):
                    lines.append(asp.fact("combo_ok", pid, oid, tid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = {
        (p.id, o.id, t.id)
        for p in PLACES.values()
        for o in OBJECTS.values()
        for t in TWISTS.values()
        if valid_combo(p, o, t)
    }
    clingo_set = set(asp_valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    if clingo_set - python_set:
        print("  only in ASP:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in Python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

HERO_NAMES = ["Mia", "Leo", "Nora", "Finn", "Ava", "Theo", "Luna", "Ben"]
HERO_TRAITS = ["curious", "brave", "gentle", "lively", "careful", "eager"]


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    obj = OBJECTS[params.object_kind]
    twist = TWISTS[params.twist]
    return World(place=place, object_kind=obj, twist=twist, hero_name=params.hero_name)


def opening(world: World) -> list[str]:
    p = world.place
    o = world.object_kind
    world.memes["curiosity"] += 1
    world.meters["attention"] += 1
    world.note("opening")
    return [
        f"{world.hero_name} was a little {random.choice(HERO_TRAITS)} adventurer who loved quiet days outdoors.",
        f"One morning, {world.hero_name} set out into {p.name} with {o.phrase}.",
        p.detail,
    ]


def middle(world: World) -> list[str]:
    o = world.object_kind
    t = world.twist
    world.meters["distance"] += 1
    world.memes["curiosity"] += 1
    world.memes["worry"] += 0.5
    world.note("middle")
    return [
        f"{world.hero_name} walked farther and noticed a stub near the path.",
        f"It looked like an old tree stump, but it also hinted that something nearby had been cut or changed.",
        f"Then came the twist: {t.reveal}.",
        f"{world.hero_name} had to {t.action}, because {o.label} was useful, but the new surprise changed the adventure.",
    ]


def ending(world: World) -> list[str]:
    t = world.twist
    world.meters["safety"] += 1
    world.meters["calm"] += 1
    world.memes["bravery"] += 1
    world.memes["delight"] += 1
    world.note("ending")
    return [
        f"{world.hero_name} chose the safe way and kept going with steady steps.",
        f"In the end, {t.ending_image}.",
        f"{world.hero_name} smiled, because the stub and the twist had turned an ordinary walk into a real adventure.",
    ]


def render_story(world: World) -> str:
    parts = opening(world) + [""] + middle(world) + [""] + ending(world)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short adventure story for a child set in {world.place.name} with a surprising twist.",
        f"Tell a nature story where {world.hero_name} notices a stub and then has to react to a sudden change.",
        f"Write a gentle outdoor adventure that ends with {world.hero_name} making a careful choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"Where did {world.hero_name} go at the start of the story?",
            answer=f"{world.hero_name} went to {world.place.name} carrying {world.object_kind.phrase}.",
        ),
        QAItem(
            question="What did the stub add to the adventure?",
            answer=(
                "The stub made the path feel like there was something old or changed nearby, "
                "so the walk did not stay ordinary."
            ),
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {world.twist.reveal}.",
        ),
        QAItem(
            question=f"What did {world.hero_name} do when the twist appeared?",
            answer=f"{world.hero_name} stayed careful and chose to {world.twist.action}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stub?",
            answer="A stub is a short leftover part of something, like the base of a tree after it has been cut down.",
        ),
        QAItem(
            question="What does a twist mean in a story?",
            answer="A twist is a surprise turn that changes what the characters expect.",
        ),
        QAItem(
            question="Why are nature paths fun for adventures?",
            answer="Nature paths are fun because they can lead to trees, water, hills, and small surprises to discover.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"place={world.place.id}")
    lines.append(f"object={world.object_kind.id}")
    lines.append(f"twist={world.twist.id}")
    lines.append(f"hero={world.hero_name}")
    lines.append(f"meters={world.meters}")
    lines.append(f"memes={world.memes}")
    lines.append(f"facts={world.trace}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nature stub twist adventure story world.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--object", dest="object_kind", choices=sorted(OBJECTS))
    ap.add_argument("--twist", choices=sorted(TWISTS))
    ap.add_argument("--name")
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
    combos = [
        (p.id, o.id, t.id)
        for p in PLACES.values()
        for o in OBJECTS.values()
        for t in TWISTS.values()
        if valid_combo(p, o, t)
        and (args.place is None or p.id == args.place)
        and (args.object_kind is None or o.id == args.object_kind)
        and (args.twist is None or t.id == args.twist)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj, tw = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(place=place, object_kind=obj, twist=tw, hero_name=hero_name, seed=None)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.object_kind not in OBJECTS:
        raise StoryError(f"Unknown object: {params.object_kind}")
    if params.twist not in TWISTS:
        raise StoryError(f"Unknown twist: {params.twist}")

    place = PLACES[params.place]
    obj = OBJECTS[params.object_kind]
    twist = TWISTS[params.twist]
    if not valid_combo(place, obj, twist):
        raise StoryError(explain_rejection(place, obj, twist))

    world = build_world(params)
    story = render_story(world)
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("#show valid/3."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for p, o, t in triples:
            print(f"  {p:10} {o:10} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in PLACES.values():
            for o in OBJECTS.values():
                for t in TWISTS.values():
                    if valid_combo(p, o, t):
                        params = StoryParams(place=p.id, object_kind=o.id, twist=t.id, hero_name=HERO_NAMES[0])
                        samples.append(generate(params))
    else:
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
