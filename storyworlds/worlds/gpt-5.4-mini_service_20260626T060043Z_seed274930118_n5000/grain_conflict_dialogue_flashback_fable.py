#!/usr/bin/env python3
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"mouse", "mice", "girl", "woman", "mother", "sister"}
        male = {"fox", "boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Grain:
    id: str
    label: str
    phrase: str
    source: str
    uses: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    grain: str
    hero: str
    rival: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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


PLACES = {
    "mill": Place("the old mill", "mill", {"grain", "grain_storage"}),
    "barn": Place("the red barn", "barn", {"grain", "grain_storage"}),
    "kitchen": Place("the kitchen", "kitchen", {"grain_porridge"}),
}

GRAINS = {
    "wheat": Grain("wheat", "wheat", "golden wheat", "field", {"bread", "porridge"}),
    "corn": Grain("corn", "corn", "bright corn", "field", {"porridge", "feed"}),
    "barley": Grain("barley", "barley", "soft barley", "field", {"porridge", "soup"}),
}

HEROES = {
    "mouse": ("mouse", "little mouse", ["small", "quick", "kind"]),
    "sparrow": ("sparrow", "small sparrow", ["light", "curious", "brave"]),
    "fox": ("fox", "clever fox", ["hungry", "proud", "fast"]),
}

RIVALS = {
    "rat": ("rat", "greedy rat"),
    "crow": ("crow", "sharp-eyed crow"),
    "fox": ("fox", "clever fox"),
}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for grain_id in GRAINS:
            if "grain" in place.affords or "grain_storage" in place.affords or "grain_porridge" in place.affords:
                for hero in HEROES:
                    for rival in RIVALS:
                        if hero != rival:
                            out.append((place_id, grain_id, hero))
    return out


ASP_RULES = r"""
place_ok(P) :- place(P).
grain_ok(G) :- grain(G).
hero_ok(H) :- hero(H).
valid(P,G,H) :- place_ok(P), grain_ok(G), hero_ok(H).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for gid in GRAINS:
        lines.append(asp.fact("grain", gid))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about grain, conflict, dialogue, and flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--grain", choices=GRAINS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--rival", choices=RIVALS)
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
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.grain is None or c[1] == args.grain)
              and (args.hero is None or c[2] == args.hero)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, grain, hero = rng.choice(sorted(combos))
    rival = args.rival or rng.choice(sorted([r for r in RIVALS if r != hero]))
    if rival == hero:
        raise StoryError("The hero and rival must be different.")
    return StoryParams(place=place, grain=grain, hero=hero, rival=rival)


def _setup(world: World) -> None:
    hero_kind, hero_label, hero_traits = HEROES[world.facts["params"].hero]
    rival_kind, rival_label = RIVALS[world.facts["params"].rival]
    grain = GRAINS[world.facts["params"].grain]

    hero = world.add(Entity(id="hero", kind="character", type=hero_kind, label=hero_label, traits=list(hero_traits)))
    rival = world.add(Entity(id="rival", kind="character", type=rival_kind, label=rival_label, traits=["hungry", "pushy"]))
    grain_ent = world.add(Entity(id="grain", kind="thing", type="grain", label=grain.label, phrase=grain.phrase, owner=hero.id))
    hero.memes["care"] = 1
    grain_ent.meters["amount"] = 1
    world.facts.update(hero=hero, rival=rival, grain=grain_ent)


def tell(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    world.facts["params"] = params
    _setup(world)
    hero = world.facts["hero"]
    rival = world.facts["rival"]
    grain = world.facts["grain"]

    world.say(f"At {world.place.name}, a {hero.label} found {grain.phrase} tucked in a wooden bin.")
    world.say(f"{hero.pronoun().capitalize()} smiled and said, 'This grain can feed many bellies.'")

    world.para()
    world.say(f"Then {rival.label} came padding in and said, 'That grain is mine. I saw it first.'")
    hero.memes["conflict"] = 1
    rival.memes["conflict"] = 1
    world.say(f"The {hero.type} held the sack close and answered, 'A hungry mouth is not the same as an empty promise.'")

    world.para()
    world.say(f"That words-sharp moment was not the first time {hero.label} had faced a greedy neighbor.")
    world.say(f"Long ago, when the river had flooded the lower path, {hero.label} had shared crumbs with {rival.label} and gone hungry for a night.")
    world.say(f"The memory returned like a lantern in fog, and {hero.label}'s anger softened.")

    world.para()
    world.say(f"{hero.label} said, 'If we fight, the grain will spill and neither of us will eat. If we share it, we both can.'")
    world.say(f"{rival.label} blinked, then muttered, 'I was only afraid there would be nothing left for me.'")
    world.say(f"{hero.label} answered, 'Then let us split it fairly and grind what we need.'")

    world.para()
    hero.memes["conflict"] = 0
    hero.memes["mercy"] = 1
    rival.memes["conflict"] = 0
    rival.memes["trust"] = 1
    grain.meters["amount"] = 0.5
    world.say(f"So they worked side by side, and the grain became a meal instead of a quarrel.")
    world.say(f"At dusk, the little share was enough for both, and the old mill felt warm with peace.")

    world.facts.update(resolved=True, place=world.place, story_grain=grain, hero=hero, rival=rival)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    grain = GRAINS[p.grain]
    hero_label = HEROES[p.hero][1]
    rival_label = RIVALS[p.rival][1]
    return [
        f"Write a short fable about {hero_label}, {rival_label}, and a bin of {grain.phrase}.",
        f"Tell a child-friendly story with conflict, dialogue, and a flashback at {PLACES[p.place].name}.",
        f"Write a gentle moral tale where {hero_label} learns to share {grain.label} instead of fighting over it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    hero = world.facts["hero"]
    rival = world.facts["rival"]
    grain = world.facts["grain"]
    place = PLACES[p.place]
    return [
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened at {place.name}, where the grain could be stored and shared.",
        ),
        QAItem(
            question=f"What did {hero.label} find?",
            answer=f"{hero.label} found {grain.phrase}, and that became the center of the conflict.",
        ),
        QAItem(
            question=f"Why did {hero.label} and {rival.label} stop arguing?",
            answer=f"They remembered that fighting would spill the grain, so they chose a fair share instead.",
        ),
        QAItem(
            question=f"What lesson did the flashback help teach?",
            answer="The flashback reminded them that kindness in the past can make sharing easier in the present.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is grain?",
            answer="Grain is the small seed part of a plant, like wheat or barley, and people can store it or cook it into food.",
        ),
        QAItem(
            question="Why do fables often use animals?",
            answer="Fables often use animals because they make the lesson feel simple, memorable, and a little magical.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="mill", grain="wheat", hero="mouse", rival="rat"),
    StoryParams(place="barn", grain="barley", hero="sparrow", rival="crow"),
    StoryParams(place="kitchen", grain="corn", hero="mouse", rival="fox"),
]


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
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} / {p.grain} / {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
