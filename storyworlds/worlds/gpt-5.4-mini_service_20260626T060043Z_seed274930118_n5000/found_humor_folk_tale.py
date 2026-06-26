#!/usr/bin/env python3
"""
storyworlds/worlds/found_humor_folk_tale.py
===========================================

A tiny folk-tale storyworld about something lost, something found, and a
funny turn that makes the village laugh before things come right again.

Seed tale:
---
Long ago, in a small village by a round hill, a shy child named Toma found a
golden spoon in a cabbage patch. The spoon was not magic in a loud way; it only
liked to make a tiny twinkle whenever someone was honest. Toma took it to the
old woman at the market, but on the road a greedy goose kept stealing the spoon,
then dropping it, then honking as if it had planned the whole thing. Toma
chased the goose through mud, nettles, and one very surprised laundry line.
At last the old woman laughed, the goose bowed, and the spoon was returned to
its owner with everyone smiling.

This world turns that premise into a simulated story:
- a child or villager finds a small valuable object;
- a silly creature or helper causes a comic delay;
- honesty and a simple plan restore the object;
- the ending image proves what changed.

The prose is authored from world state, with meters for physical facts and
memes for emotional facts.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | animal
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    found_by: Optional[str] = None
    carried_by: Optional[str] = None
    lost: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    outdoors: bool = True
    features: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    value: str
    type: str
    likes_honesty: bool = True


@dataclass
class Trickster:
    id: str
    type: str
    label: str
    habit: str
    silliness: str
    mischief: str
    hides: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.mood: str = "bright"
        self.footprints: int = 0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
    "market": Place("the market", outdoors=True, features={"stalls", "mud", "crowds"}),
    "cabbage_patch": Place("the cabbage patch", outdoors=True, features={"cabbages", "soil", "rows"}),
    "crossroads": Place("the crossroads", outdoors=True, features={"dust", "signpost"}),
    "barnyard": Place("the barnyard", outdoors=True, features={"fence", "hay", "mud"}),
}

RELICS = {
    "spoon": Relic("spoon", "golden spoon", "a golden spoon", "shiny", "spoon"),
    "bell": Relic("bell", "silver bell", "a silver bell", "ringing", "bell"),
    "button": Relic("button", "blue button", "a bright blue button", "small", "button"),
    "coin": Relic("coin", "old coin", "an old copper coin", "pocket-sized", "coin"),
}

TRICKSTERS = {
    "goose": Trickster("goose", "goose", "a greedy goose", "steals shiny things", "very loud honking", "behind cabbages"),
    "goat": Trickster("goat", "goat", "a nosy goat", "nibbles everything", "chews with purpose", "under fences"),
    "cat": Trickster("cat", "cat", "a sly cat", "swats at dangling things", "sits as if innocent", "inside baskets"),
}

NAMES = {
    "girl": ["Mina", "Toma", "Lina", "Nera", "Sana"],
    "boy": ["Toma", "Milo", "Eli", "Beno", "Arun"],
}
TRAITS = ["shy", "kind", "clever", "gentle", "patient", "lively"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    relic: str
    name: str
    gender: str
    trait: str
    trickster: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A tale is valid when the relic can be found at the chosen place, and a
% trickster can cause a comic delay there.
can_find(P, R) :- place(P), relic(R), drops_at(R, P).
can_mischief(T, P) :- trickster(T), place(P), haunts(T, P).
valid_story(P, R, T) :- can_find(P, R), can_mischief(T, P).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.outdoors:
            lines.append(asp.fact("outdoors", pid))
        for feat in sorted(place.features):
            lines.append(asp.fact("features", pid, feat))
    for rid, relic in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("drops_at", rid, "cabbage_patch"))
        lines.append(asp.fact("value", rid, relic.value))
    for tid, trick in TRICKSTERS.items():
        lines.append(asp.fact("trickster", tid))
        lines.append(asp.fact("haunts", tid, "cabbage_patch"))
        lines.append(asp.fact("habit", tid, trick.habit))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_choices() -> list[tuple[str, str, str]]:
    choices = []
    for place_id in PLACES:
        for relic_id in RELICS:
            for trick_id in TRICKSTERS:
                if place_id == "cabbage_patch" and relic_id in RELICS and trick_id in TRICKSTERS:
                    choices.append((place_id, relic_id, trick_id))
    return choices


def asp_verify() -> int:
    import asp
    py = set(valid_choices())
    clingo_set = set(asp_valid_stories())
    if py == clingo_set:
        print(f"OK: ASP matches Python ({len(py)} valid tale shapes).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in python:", sorted(py - clingo_set))
    print("only in asp:", sorted(clingo_set - py))
    return 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale world about something found, with a comic trickster turn.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--trickster", choices=TRICKSTERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(PLACES))
    relic = args.relic or rng.choice(list(RELICS))
    trickster = args.trickster or rng.choice(list(TRICKSTERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    trait = args.trait or rng.choice(TRAITS)
    if place != "cabbage_patch":
        raise StoryError("(No story: this folk tale needs the cabbage patch where things can be found.)")
    return StoryParams(place=place, relic=relic, name=name, gender=gender, trait=trait, trickster=trickster)


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def story_intro(world: World, hero: Entity, relic: Entity) -> None:
    world.say(f"Once, in {world.place.name}, there lived a {hero.memes['trait_name']} {hero.type} named {hero.id}.")
    world.say(f"{hero.pronoun().capitalize()} was known for noticing small things others missed, especially when {hero.pronoun('possessive')} eyes fell on {relic.phrase}.")


def find_relic(world: World, hero: Entity, relic: Entity) -> None:
    hero.meters["curiosity"] = hero.meters.get("curiosity", 0) + 1
    relic.found_by = hero.id
    relic.meters["clean"] = 1
    world.say(f"One day, {hero.id} {('found' if True else 'saw')} {relic.phrase} in the cabbage patch.")
    world.say(f"It glimmered like a tiny moon, and {hero.pronoun()} tucked {relic.it()} carefully into {hero.pronoun('possessive')} hands.")


def trouble(world: World, hero: Entity, relic: Entity, trick: Trickster) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(f"{hero.id} wanted to bring the {relic.label} to its rightful owner, but {trick.label} had other ideas.")
    world.say(f"Before long, {trick.label} snatched at {relic.it()}, {trick.silliness}, and ran in circles through the mud.")
    world.footprints += 7
    hero.meters["mud"] = hero.meters.get("mud", 0) + 1


def chase(world: World, hero: Entity, relic: Entity, trick: Trickster) -> None:
    hero.meters["running"] = hero.meters.get("running", 0) + 1
    hero.memes["determination"] = hero.memes.get("determination", 0) + 1
    world.say(f"{hero.id} chased {trick.label} past the cabbages and around a fence.")
    world.say(f"At one point, {trick.label} dropped {relic.it()}, then bowed as if all of it had been a joke told by the road itself.")


def resolve(world: World, hero: Entity, relic: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    relic.lost = False
    owner = world.facts["owner"]
    world.say(f"At last, {hero.id} found the true owner and gave back {relic.phrase}.")
    world.say(f"The owner laughed, the trickster went quiet, and {hero.id} smiled as {relic.phrase} shone bright in honest hands again.")


def tell(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={},
        memes={"trait_name": params.trait},
    ))
    relic = world.add(Entity(
        id=params.relic,
        type=params.relic,
        label=RELICS[params.relic].label,
        phrase=RELICS[params.relic].phrase,
        owner="owner",
        lost=True,
    ))
    trick = TRICKSTERS[params.trickster]

    world.facts.update(hero=hero, relic=relic, trick=trick, owner="the old woman")
    story_intro(world, hero, relic)
    world.para()
    find_relic(world, hero, relic)
    trouble(world, hero, relic, trick)
    world.para()
    chase(world, hero, relic, trick)
    resolve(world, hero, relic)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    relic: Entity = f["relic"]
    trick: Trickster = f["trick"]
    return [
        f'Write a short folk tale for children about a {hero.memes["trait_name"]} {hero.type} who finds {relic.phrase}.',
        f"Tell a funny story where {hero.id} carries {relic.phrase} through {world.place.name} and a {trick.label} causes trouble.",
        f'Write a simple tale that includes the word "found" and ends with {relic.phrase} being returned honestly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    relic: Entity = f["relic"]
    trick: Trickster = f["trick"]
    owner = f["owner"]
    return [
        QAItem(
            question=f"Who found the {relic.label} in the cabbage patch?",
            answer=f"{hero.id} found the {relic.label} in the cabbage patch and tried to carry it to {owner}.",
        ),
        QAItem(
            question=f"What made the trip funny after {hero.id} found {relic.phrase}?",
            answer=f"{trick.label} kept stealing at {relic.it()}, then dropping it and honking or acting silly, so the road turned into a joke.",
        ),
        QAItem(
            question=f"What happened in the end with {relic.phrase}?",
            answer=f"{hero.id} returned {relic.phrase} to {owner}, and everyone laughed because honesty won the day.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to find something?",
            answer="To find something means to discover it or come across it, often after it was lost or hidden.",
        ),
        QAItem(
            question="Why do folk tales often have animals that act like people?",
            answer="Folk tales often give animals human-like actions because it makes the story playful, memorable, and easy to tell aloud.",
        ),
        QAItem(
            question="Why is honesty important in a story like this?",
            answer="Honesty is important because it helps the right person get back what belongs to them, and it lets the story end happily.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.lost:
            bits.append("lost=True")
        if e.found_by:
            bits.append(f"found_by={e.found_by}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    lines.append(f"  footprints={world.footprints}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core interface
# ---------------------------------------------------------------------------
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(f"{len(asp.atoms(model, 'valid_story'))} valid story shape(s).")
        for t in sorted(set(asp.atoms(model, "valid_story"))):
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="cabbage_patch", relic="spoon", name="Toma", gender="boy", trait="clever", trickster="goose"),
            StoryParams(place="cabbage_patch", relic="bell", name="Mina", gender="girl", trait="kind", trickster="cat"),
            StoryParams(place="cabbage_patch", relic="coin", name="Beno", gender="boy", trait="patient", trickster="goat"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
