#!/usr/bin/env python3
"""
A small animal-story world about sharing a treat that can evaporate.

Premise:
- Two animal friends have one cold snack in a warm place.
- One friend wants to cram the snack quickly instead of sharing.
- The snack evaporates if it sits too long in the heat.
- The story ends badly when greed and delay leave nothing to enjoy.

This world keeps the vocabulary close to an animal friendship story:
friendship, sharing, animal, treat, warm air, evaporate, cram, bad ending.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "dog", "fox", "bear", "rabbit", "mouse", "squirrel"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    warm: bool = True
    can_evaporate: bool = True


@dataclass
class Treat:
    label: str
    phrase: str
    melts: bool = False
    evaporates: bool = False


@dataclass
class StoryParams:
    place: str
    treat: str
    hero1: str
    hero2: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.story_lines: list[str] = []
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.story_lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.story_lines)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.story_lines = []
        w.fired = set(self.fired)
        return w


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal friendship story with sharing and a bad ending.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--treat", choices=sorted(TREATS))
    ap.add_argument("--hero1", choices=sorted(ANIMALS))
    ap.add_argument("--hero2", choices=sorted(ANIMALS))
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


ANIMALS = {
    "cat": "cat",
    "dog": "dog",
    "fox": "fox",
    "bear": "bear",
    "rabbit": "rabbit",
    "mouse": "mouse",
    "squirrel": "squirrel",
}

PLACES = {
    "porch": Place("the porch", warm=True, can_evaporate=True),
    "sunny_hill": Place("a sunny hill", warm=True, can_evaporate=True),
    "garden": Place("the garden", warm=True, can_evaporate=True),
}

TREATS = {
    "juice": Treat("juice", "a cup of sweet juice", evaporates=True),
    "puddle_ice": Treat("ice pop", "a cold ice pop", melts=True, evaporates=True),
    "cream": Treat("cream", "a little bowl of cream", evaporates=True),
}


@dataclass
class Animal:
    id: str
    species: str
    name: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "he", "object": "him", "possessive": "his"}[case]


def make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    hero1 = world.add(Entity(id="A", kind="character", type=params.hero1, label=params.hero1))
    hero2 = world.add(Entity(id="B", kind="character", type=params.hero2, label=params.hero2))
    treat = world.add(Entity(id="T", type=params.treat, label=TREATS[params.treat].label, phrase=TREATS[params.treat].phrase))
    world.facts.update(hero1=hero1, hero2=hero2, treat=treat, place=place, treat_cfg=TREATS[params.treat])
    return world


def story_intro(world: World) -> None:
    h1: Entity = world.facts["hero1"]
    h2: Entity = world.facts["hero2"]
    treat: Entity = world.facts["treat"]
    world.say(f"On {world.place.name}, two animal friends met with one shared snack.")
    world.say(f"{h1.type.capitalize()} and {h2.type} had {treat.phrase}, and both wanted to be kind.")
    h1.memes["friendship"] = 1
    h2.memes["friendship"] = 1
    h1.memes["sharing"] = 0.5
    h2.memes["sharing"] = 0.5


def predict_loss(world: World) -> bool:
    t = world.facts["treat_cfg"]
    return world.place.can_evaporate and t.evaporates


def conflict(world: World) -> None:
    h1: Entity = world.facts["hero1"]
    h2: Entity = world.facts["hero2"]
    treat: Entity = world.facts["treat"]
    h1.meters["cram"] = 1
    h1.memes["greedy"] = 1
    world.say(f"But {h1.type} wanted to cram the treat in a hurry instead of sharing it.")
    if predict_loss(world):
        world.say(f"The warm air on {world.place.name} made the treat start to evaporate.")
    h2.memes["sad"] = 1
    world.say(f"{h2.type.capitalize()} watched and felt left out, because friendship was turning sour.")


def bad_ending(world: World) -> None:
    h1: Entity = world.facts["hero1"]
    h2: Entity = world.facts["hero2"]
    treat: Entity = world.facts["treat"]
    if predict_loss(world):
        world.say(f"Before they could fix it, the treat evaporated away.")
    world.say(f"{h1.type.capitalize()} got only a sticky mouthful, and {h2.type} got almost nothing at all.")
    world.say(f"The friends sat quietly on {world.place.name}, wishing they had shared sooner.")
    h1.memes["friendship"] = 0
    h2.memes["friendship"] = 0
    world.facts["bad_ending"] = True


def tell(world: World) -> World:
    story_intro(world)
    world.say("")
    conflict(world)
    world.say("")
    bad_ending(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short animal story about friendship and sharing, with a bad ending when a treat evaporates.",
        f"Tell a gentle story about a {f['hero1'].type} and a {f['hero2'].type} who try to share {f['treat'].phrase} on {world.place.name}.",
        "Write a tiny animal story that includes the words cram and evaporate and ends sadly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h1: Entity = world.facts["hero1"]
    h2: Entity = world.facts["hero2"]
    treat: Entity = world.facts["treat"]
    place: Place = world.facts["place"]
    return [
        QAItem(
            question=f"Who were the friends in the story?",
            answer=f"The friends were a {h1.type} and a {h2.type} who wanted to share together.",
        ),
        QAItem(
            question=f"What did they have to share?",
            answer=f"They had {treat.phrase} to share on {place.name}.",
        ),
        QAItem(
            question="What went wrong at the end?",
            answer="One friend tried to cram the snack too fast, and the treat evaporated before they could share it well.",
        ),
        QAItem(
            question="Why was it a bad ending?",
            answer="It was a bad ending because the friends ended up unhappy and the treat was mostly gone.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let other people or animals have some of what you have too.",
        ),
        QAItem(
            question="What happens when something evaporates?",
            answer="When something evaporates, it slowly turns into invisible vapor and disappears into the air.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the caring bond between friends who help each other and spend time together.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  place={world.place.name}")
    lines.append(f"  facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.can_evaporate:
            lines.append(asp.fact("can_evaporate", pid))
        if place.warm:
            lines.append(asp.fact("warm", pid))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        if t.evaporates:
            lines.append(asp.fact("evaporates", tid))
    return "\n".join(lines)


ASP_RULES = r"""
bad_end(Place,T) :- place(Place), treat(T), can_evaporate(Place), evaporates(T), warm(Place).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    prog = asp_program("#show bad_end/2.")
    model = asp.one_model(prog)
    asp_set = set(asp.atoms(model, "bad_end"))
    py_set = {(p, t) for p, pobj in PLACES.items() for t, tobj in TREATS.items() if pobject_reason(pobj, tobj)}
    if asp_set == py_set:
        print(f"OK: clingo gate matches python ({len(asp_set)} cases).")
        return 0
    print("MISMATCH:")
    print(" only in asp:", sorted(asp_set - py_set))
    print(" only in python:", sorted(py_set - asp_set))
    return 1


def pobject_reason(place: Place, treat: Treat) -> bool:
    return place.can_evaporate and place.warm and treat.evaporates


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p, place in PLACES.items():
        for t, treat in TREATS.items():
            if pobject_reason(place, treat):
                for h1 in ANIMALS:
                    for h2 in ANIMALS:
                        if h1 != h2:
                            out.append((p, t, f"{h1},{h2}"))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACES))
    treat = args.treat or rng.choice(sorted(TREATS))
    h1 = args.hero1 or rng.choice(sorted(ANIMALS))
    h2 = args.hero2 or rng.choice(sorted([a for a in ANIMALS if a != h1]))
    if not pobject_reason(PLACES[place], TREATS[treat]):
        raise StoryError("No valid story: the chosen place does not let the treat evaporate.")
    if h1 == h2:
        raise StoryError("No valid story: the two animal friends must be different.")
    return StoryParams(place=place, treat=treat, hero1=h1, hero2=h2)


def generate(params: StoryParams) -> StorySample:
    world = tell(make_world(params))
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
    StoryParams(place="porch", treat="juice", hero1="cat", hero2="dog"),
    StoryParams(place="garden", treat="cream", hero1="fox", hero2="rabbit"),
    StoryParams(place="sunny_hill", treat="puddle_ice", hero1="bear", hero2="mouse"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bad_end/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero1} and {p.hero2} at {p.place} with {p.treat}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
