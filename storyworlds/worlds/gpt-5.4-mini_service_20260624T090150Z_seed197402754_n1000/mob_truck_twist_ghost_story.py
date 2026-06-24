#!/usr/bin/env python3
"""
A small ghost-story world with a truck, a curious mob, and a twist ending.

Seed image:
- A spooky truck rattles down a dark lane.
- A little mob of neighbors gathers to peek and whisper.
- The "ghost" turns out to be something ordinary, but the night still changes.

The world is state-driven: the truck can rattle, the mob can gather, fear can rise,
and the twist can settle everything into a safer, friendlier ending.
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
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
    name: str
    dark: bool = True
    open_space: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    parent_type: str
    truck: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


def _join(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + ", and " + items[-1]


def story_setting_detail(place: Place) -> str:
    if place.name == "the old yard":
        return "The old yard was wide and still, with a fence that creaked when the wind touched it."
    if place.name == "the depot lane":
        return "The depot lane was narrow, with one bare light that made long shadows."
    return f"{place.name.capitalize()} felt hushed, as if even the stones were waiting."


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, label=params.parent_type))
    truck = world.add(Entity(id="truck", type="truck", label=params.truck, phrase=f"the {params.truck}", plural=False))
    mob = world.add(Entity(id="mob", kind="group", type="mob", label="mob", plural=True))
    ghost = world.add(Entity(id="ghost", type="ghost", label="ghost", phrase="a pale flutter", plural=False))
    tarp = world.add(Entity(id="tarp", type="thing", label="tarp", phrase="a white tarp", plural=False))

    world.facts.update(hero=hero, parent=parent, truck=truck, mob=mob, ghost=ghost, tarp=tarp, place=place)

    # Setup
    hero.memes["curiosity"] = 1
    truck.meters["rattle"] = 1
    tarp.meters["loose"] = 1
    mob.memes["worry"] = 1
    world.say(
        f"{hero.label} was a little {hero.type} who loved a good ghost story. "
        f"One evening, {hero.label} and {hero.pronoun('possessive')} {params.parent_type} walked to {place.name}."
    )
    world.say(story_setting_detail(place))
    world.say(
        f"Near the dark road stood {truck.phrase}, and a little mob of neighbors had gathered around it. "
        f"They were whispering that a ghost had been seen near the truck."
    )

    # Rising tension
    world.para()
    hero.memes["fear"] = 1
    mob.memes["fear"] = 1
    world.say(
        f"{hero.label} heard the word ghost and felt a chilly tingle in {hero.pronoun('possessive')} tummy. "
        f"The truck gave a slow clank, and the white tarp on top flapped like a pale hand."
    )
    world.say(
        f"The mob took a step back. One person pointed at the tarp and said it looked like a ghost trying to ride away."
    )

    # Twist: ordinary cause
    world.para()
    truck.meters["wind"] = 1
    tarp.meters["flap"] = 1
    ghost.meters["real"] = 0
    world.say(
        f"{hero.label}'s {params.parent_type} did not run. {hero.pronoun().capitalize()} walked closer with a small lantern."
    )
    world.say(
        f"Then the lantern showed the twist: the 'ghost' was only a loose tarp caught on the truck's side mirror. "
        f"It kept snapping in the wind and making the spooky shape."
    )
    world.say(
        f"The mob laughed in relief, and even {hero.label} smiled. The truck was not haunted at all; it just needed a knot tied tight."
    )

    # Resolution
    world.para()
    tarp.meters["loose"] = 0
    tarp.meters["tied"] = 1
    hero.memes["fear"] = 0
    hero.memes["joy"] = 1
    mob.memes["worry"] = 0
    world.say(
        f"{hero.label} held one corner of the tarp while {params.parent_type} tied it down. "
        f"After that, the truck stood still and calm, with no more ghost-shapes on its side."
    )
    world.say(
        f"The little mob drifted away under the quiet sky, and {hero.label} went home with a brave grin, "
        f"happy to know that sometimes a ghost story ends with a knot and a laugh."
    )

    return world


PLACES = {
    "yard": Place(name="the old yard", dark=True, open_space=True, affords={"gather"}),
    "depot": Place(name="the depot lane", dark=True, open_space=True, affords={"gather"}),
    "road": Place(name="the back road", dark=True, open_space=True, affords={"gather"}),
}

TRUCKS = {
    "delivery": "delivery truck",
    "dump": "dump truck",
    "milk": "milk truck",
}

GIRL_NAMES = ["Mina", "Nora", "Lily", "Ivy", "Rosa"]
BOY_NAMES = ["Theo", "Ben", "Milo", "Eli", "Finn"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    truck: Entity = f["truck"]
    return [
        f"Write a short ghost story for a child about {hero.label}, a mob of neighbors, and {truck.phrase}.",
        f"Tell a spooky-but-gentle story where a truck seems haunted, but the twist is ordinary and safe.",
        f"Write a simple story that uses the words 'mob' and 'truck' and ends with a twist that explains the ghost.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    truck: Entity = f["truck"]
    place: Place = f["place"]
    tarp: Entity = f["tarp"]
    qa = [
        QAItem(
            question=f"Who went to {place.name} to see the spooky truck?",
            answer=f"{hero.label}, a little {hero.type}, went with {hero.pronoun('possessive')} {f['parent'].type} to look at the truck.",
        ),
        QAItem(
            question=f"What did the mob think they saw near {truck.phrase}?",
            answer="The mob thought they saw a ghost, because the dark truck and the fluttering tarp looked spooky.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The ghost was not real. It was only {tarp.phrase} flapping in the wind and making a scary shape.",
        ),
        QAItem(
            question=f"How did the story end for {hero.label}?",
            answer=f"{hero.label} ended up feeling brave and happy after the tarp was tied down and the truck looked ordinary again.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a truck?",
            answer="A truck is a big vehicle with strong wheels that can carry heavy things from one place to another.",
        ),
        QAItem(
            question="What is a mob?",
            answer="A mob is a crowd of people all together in one place, usually moving or reacting at the same time.",
        ),
        QAItem(
            question="Why do dark places feel spooky?",
            answer="Dark places can feel spooky because it is harder to see, so ordinary things can look strange for a moment.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Story questions =="]
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== Prompts ==")
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    return "\n".join(out)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        if PLACES[pid].dark:
            lines.append(asp.fact("dark", pid))
        for a in sorted(PLACES[pid].affords):
            lines.append(asp.fact("affords", pid, a))
    for tid in TRUCKS:
        lines.append(asp.fact("truck", tid))
    lines.append(asp.fact("feature", "twist"))
    return "\n".join(lines)


ASP_RULES = r"""
% A ghost-story twist happens when a spooky truck has an ordinary cause.
spooky(Place) :- dark(Place), affords(Place, gather).
twist(Place) :- spooky(Place), truck(_), feature(twist).
valid_story(Place) :- twist(Place).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p,) for p in PLACES if PLACES[p].dark and "gather" in PLACES[p].affords}
    cl = set(asp_valid_places())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} places).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with a truck and a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--truck", choices=TRUCKS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(PLACES))
    truck = args.truck or rng.choice(list(TRUCKS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, hero_name=name, hero_type=gender, parent_type=parent, truck=truck)


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
        print("--- trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            parts = []
            if meters:
                parts.append(f"meters={meters}")
            if memes:
                parts.append(f"memes={memes}")
            if parts:
                print(f"{e.id}: " + " ".join(parts))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="yard", hero_name="Mina", hero_type="girl", parent_type="mother", truck="delivery"),
    StoryParams(place="depot", hero_name="Theo", hero_type="boy", parent_type="father", truck="dump"),
    StoryParams(place="road", hero_name="Lily", hero_type="girl", parent_type="mother", truck="milk"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{p[0]}" for p in asp_valid_places()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
