#!/usr/bin/env python3
"""
storyworlds/worlds/dialogue_late_kindness_sharing_conflict_ghost_story.py
=========================================================================

A small ghost-story world about a late-night conflict that is eased by kindness
and sharing. The story stays child-facing and concrete: a child notices a ghost
after dark, the ghost is shy, the child is frightened, and a shared blanket,
lantern, or snack helps them turn fear into friendship.

The model tracks:
- physical meters: light, cold, distance, dampness, fullness
- emotional memes: fear, kindness, sharing, conflict, trust, relief

The domain is intentionally narrow so the simulation can drive the prose:
a late arrival, a spooky first meeting, a dialogue turn, a choice to share,
and an ending image showing that the ghost is no longer lonely.

This file is standalone and follows the Storyweavers storyworld contract.
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: {"light": 0.0, "cold": 0.0, "distance": 0.0, "damp": 0.0, "fullness": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"fear": 0.0, "kindness": 0.0, "sharing": 0.0, "conflict": 0.0, "trust": 0.0, "relief": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    indoors: bool = True
    dark: bool = False
    cozy: bool = False


@dataclass
class ObjectSpec:
    id: str
    label: str
    phrase: str
    type: str
    helps: set[str] = field(default_factory=set)
    shared_by: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    object: str
    hero_name: str
    hero_type: str
    ghost_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)


SETTINGS = {
    "attic": Place(name="the attic", indoors=True, dark=True, cozy=False),
    "hall": Place(name="the old hall", indoors=True, dark=True, cozy=False),
    "cabin": Place(name="the little cabin", indoors=True, dark=False, cozy=True),
}

OBJECTS = {
    "lantern": ObjectSpec("lantern", "lantern", "a small lantern", "lantern", helps={"light"}, shared_by={"ghost", "child"}),
    "blanket": ObjectSpec("blanket", "blanket", "a warm blanket", "blanket", helps={"cold"}, shared_by={"ghost", "child"}),
    "cookie": ObjectSpec("cookie", "cookie", "a plate of cookies", "cookies", helps={"fullness"}, shared_by={"ghost", "child"}),
}

GHOST_NAMES = ["Milo", "Nia", "Boo", "Pip", "Luna"]
HERO_TYPES = ["girl", "boy"]
HERO_NAMES = ["Mia", "Leo", "Nora", "Finn", "Ava", "Theo"]


def reasonableness_gate(place: Place, obj: ObjectSpec) -> bool:
    return place.dark or "light" in obj.helps or "cold" in obj.helps or "fullness" in obj.helps


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pname, place in SETTINGS.items():
        for oname, obj in OBJECTS.items():
            if reasonableness_gate(place, obj):
                out.append((pname, oname))
    return out


def explain_rejection(place: Place, obj: ObjectSpec) -> str:
    return f"(No story: {obj.label} does not fit this calm setting well enough for a ghost story.)"


ASP_RULES = r"""
story_place(P) :- place(P).
object_for_story(O) :- obj(O), useful(O).
valid(P,O) :- story_place(P), object_for_story(O).
#show valid/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("obj", oid))
        if obj.helps:
            lines.append(asp.fact("useful", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A late-night ghost story about kindness and sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--ghost-name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.object is None or c[1] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    return StoryParams(place=place, object=obj, hero_name=hero_name, hero_type=hero_type, ghost_name=ghost_name)


def build_world(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    obj = OBJECTS[params.object]
    w = World(place)
    hero = w.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    ghost = w.add(Entity(id="ghost", kind="character", type="ghost", label=params.ghost_name))
    tool = w.add(Entity(id=obj.id, type=obj.type, label=obj.label, phrase=obj.phrase, owner=hero.id))
    w.facts.update(hero=hero, ghost=ghost, tool=tool, place=place, obj=obj, params=params)
    return w


def tell_story(world: World) -> None:
    hero: Entity = world.facts["hero"]
    ghost: Entity = world.facts["ghost"]
    tool: Entity = world.facts["tool"]
    place: Place = world.facts["place"]
    obj: ObjectSpec = world.facts["obj"]

    world.say(f"It was late at {place.name}, and the room felt very still.")
    world.say(f"{hero.label} held {obj.phrase} and heard a soft sound from the dark corner.")
    world.say(f"Then {ghost.label} appeared with a tiny sigh.")
    world.say(f'"Please do not be afraid," {ghost.label} said. "I am only lonely."')
    hero.memes["fear"] += 1
    world.say(f"{hero.label} felt a little scared, but {hero.label.lower() if hero.label else 'the child'} listened.")
    world.say(f'"If you are lonely, you can stay with me," {hero.label} said.')
    hero.memes["kindness"] += 1
    hero.memes["sharing"] += 1
    hero.memes["conflict"] += 1
    if obj.id == "lantern":
        tool.meters["light"] += 1
        world.say(f"{hero.label} shared the lantern, and its glow made the shadows smaller.")
    elif obj.id == "blanket":
        tool.meters["cold"] -= 1
        world.say(f"{hero.label} shared the blanket, and both of them felt warm and safe.")
    else:
        tool.meters["fullness"] += 1
        world.say(f"{hero.label} shared the cookies, and the ghost's empty feeling went away.")
    hero.memes["conflict"] = 0
    hero.memes["trust"] += 1
    hero.memes["relief"] += 1
    ghost.memes["trust"] += 1
    ghost.memes["relief"] += 1
    world.say(f"They sat together and talked in quiet voices until the room stopped feeling spooky.")
    world.say(f"When the night ended, {ghost.label} was no longer alone, and {hero.label} smiled at the calm dark.")


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f'Write a ghost story for young children that uses the words "dialogue" and "late".',
        f"Tell a gentle late-night story where {p.hero_name} meets a ghost and chooses kindness instead of conflict.",
        f"Write a small story about sharing something useful with a lonely ghost at {SETTINGS[p.place].name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    obj: ObjectSpec = world.facts["obj"]
    return [
        QAItem(
            question=f"Why was the meeting scary at first?",
            answer=f"It was scary at first because it was late, the place was dark, and a ghost appeared before {p.hero_name} knew it was friendly.",
        ),
        QAItem(
            question=f"What did {p.hero_name} share with the ghost?",
            answer=f"{p.hero_name} shared {obj.phrase}, which helped the ghost feel better and turned the conflict into kindness.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {p.ghost_name} no longer lonely and {p.hero_name} feeling calm, safe, and happy in the dark room.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is kindness?", answer="Kindness is when someone is gentle, caring, and tries to help instead of hurt."),
        QAItem(question="What is sharing?", answer="Sharing means letting someone else use or enjoy something with you."),
        QAItem(question="What is a conflict?", answer="A conflict is a problem where feelings clash, but it can get better when people talk and help each other."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="attic", object="lantern", hero_name="Mia", hero_type="girl", ghost_name="Boo"),
    StoryParams(place="hall", object="blanket", hero_name="Leo", hero_type="boy", ghost_name="Luna"),
    StoryParams(place="cabin", object="cookie", hero_name="Nora", hero_type="girl", ghost_name="Pip"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
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
        header = f"### variant {i+1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
