#!/usr/bin/env python3
"""
storyworlds/worlds/cluster_gorilla_moral_value_problem_solving_mystery.py
=========================================================================

A small mystery storyworld about a gorilla, a missing cluster, and a kind
problem-solving turn that reveals a moral choice.

Premise:
- A gorilla notices a problem in a familiar place.
- Something important is missing or out of place.
- The gorilla investigates clues, asks around, and solves the puzzle.

Story shape:
- Beginning: a calm scene and a worrying mystery.
- Middle: the gorilla follows clues and makes a choice.
- Ending: the missing thing is found, and the moral value becomes clear.

This world keeps the prose concrete and child-facing while still being
state-driven. The story can vary by location, object cluster, helper, and the
moral value emphasized by the resolution.
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"gorilla"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    clues: list[str] = field(default_factory=list)


@dataclass
class ClusterThing:
    id: str
    label: str
    phrase: str
    where: str
    clue: str
    value: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    cluster: str
    moral_value: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
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


PLACES = {
    "garden": Place(id="garden", label="the garden", clues=["mud on a leaf", "a bent stem", "a shiny pebble"]),
    "riverbank": Place(id="riverbank", label="the riverbank", clues=["wet footprints", "a floating leaf", "a broken twig"]),
    "village_square": Place(id="village_square", label="the village square", clues=["tiny crumbs", "a dropped ribbon", "a careful footprint"]),
    "orchard": Place(id="orchard", label="the orchard", clues=["a peeled peel", "a wobbling branch", "soft fruit smell"]),
}

CLUSTERS = {
    "bananas": ClusterThing(
        id="bananas",
        label="banana cluster",
        phrase="a big cluster of bananas",
        where="high in a tree",
        clue="banana scent on the air",
        value="sharing",
        plural=True,
    ),
    "flowers": ClusterThing(
        id="flowers",
        label="flower cluster",
        phrase="a bright cluster of flowers",
        where="near a stone path",
        clue="pollen on a paw",
        value="care",
    ),
    "keys": ClusterThing(
        id="keys",
        label="key cluster",
        phrase="a small cluster of keys",
        where="under a bench",
        clue="a metal glint",
        value="honesty",
        plural=True,
    ),
    "shells": ClusterThing(
        id="shells",
        label="shell cluster",
        phrase="a little cluster of shells",
        where="by the water",
        clue="salt on the breeze",
        value="patience",
        plural=True,
    ),
}

HELPERS = {
    "parrot": "a talkative parrot",
    "tortoise": "a slow tortoise",
    "child": "a careful child",
    "monkey": "a nimble monkey",
}

MORAL_VALUES = {
    "honesty": "honesty",
    "sharing": "sharing",
    "patience": "patience",
    "care": "care",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld about a gorilla and a missing cluster.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cluster", choices=CLUSTERS)
    ap.add_argument("--moral-value", choices=MORAL_VALUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for cluster in CLUSTERS:
            for moral in MORAL_VALUES:
                combos.append((place, cluster, moral))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.cluster:
        combos = [c for c in combos if c[1] == args.cluster]
    if args.moral_value:
        combos = [c for c in combos if c[2] == args.moral_value]
    if not combos:
        raise StoryError("No valid mystery setup matches the given options.")
    place, cluster, moral = rng.choice(combos)
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=place, cluster=cluster, moral_value=moral, helper=helper)


def _find_clue(world: World, hero: Entity, cluster: ClusterThing, helper: str) -> None:
    world.say(
        f"Near {world.place.label}, {hero.id} noticed something odd: the {cluster.label} was missing from {cluster.where}."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} spotted {cluster.clue} and called over {HELPERS[helper]} for help."
    )


def _solve(world: World, hero: Entity, cluster: ClusterThing, helper: str) -> None:
    if cluster.value == "honesty":
        world.say(
            f"The helper pointed to a small trail, and {hero.id} followed it until the missing {cluster.label} was tucked under a bench."
        )
        world.say(
            f"A nearby friend admitted taking it by mistake, and {hero.id} was glad they told the truth."
        )
    elif cluster.value == "sharing":
        world.say(
            f"The helper heard laughing from the trees, and {hero.id} found the {cluster.label} being saved for everyone to enjoy."
        )
        world.say(
            f"{hero.id} smiled and helped carry it back so the whole group could share."
        )
    elif cluster.value == "patience":
        world.say(
            f"The helper asked {hero.id} to wait quietly, and after a little while the {cluster.label} drifted into view on the water."
        )
        world.say(
            f"{hero.id} waited patiently and used a long branch to bring it safely back."
        )
    else:
        world.say(
            f"The helper noticed careful prints, and {hero.id} followed them to where the {cluster.label} had been set down for safekeeping."
        )
        world.say(
            f"{hero.id} gently returned it to the right place, showing care for what mattered."
        )


def tell(place: Place, cluster: ClusterThing, helper: str, moral_value: str) -> World:
    world = World(place)
    gorilla = world.add(Entity(id="Gogo", kind="character", type="gorilla", label="gorilla"))
    world.add(Entity(id="helper", kind="character", type=helper, label=HELPERS[helper]))
    world.facts.update(gorilla=gorilla, cluster=cluster, helper=helper, moral_value=moral_value, place=place)

    world.say(
        f"Gogo the gorilla lived near {place.label} and loved solving little mysteries."
    )
    world.say(
        f"One morning, {gorilla.pronoun('subject')} noticed that {cluster.phrase} was gone."
    )
    world.para()
    _find_clue(world, gorilla, cluster, helper)
    world.say(
        f"Gogo looked carefully at the clues, because {gorilla.pronoun('subject')} wanted to do the right thing, not just the quick thing."
    )
    world.para()
    _solve(world, gorilla, cluster, helper)
    world.say(
        f"In the end, the missing {cluster.label} was back where it belonged, and Gogo remembered that {moral_value} can help solve a mystery."
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cluster: ClusterThing = f["cluster"]
    helper = f["helper"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"What mystery did Gogo the gorilla notice near {place.label}?",
            answer=f"Gogo noticed that {cluster.phrase} was missing.",
        ),
        QAItem(
            question=f"Who helped Gogo look for the {cluster.label}?",
            answer=f"{HELPERS[helper]} helped Gogo follow the clues.",
        ),
        QAItem(
            question=f"What moral value did Gogo show while solving the mystery?",
            answer=f"Gogo showed {cluster.value}, because the story ends by saying that {cluster.value} helped solve the mystery.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a problem where something is missing, strange, or not yet understood, so someone has to look for clues.",
        ),
        QAItem(
            question="Why do clues matter in a mystery?",
            answer="Clues matter because they help someone figure out what happened and find the answer step by step.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to use careful thinking and actions to fix what is wrong or to find what is missing.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cluster: ClusterThing = f["cluster"]
    place: Place = f["place"]
    return [
        f"Write a short child-friendly mystery about a gorilla who discovers that {cluster.phrase} is missing from {place.label}.",
        f"Tell a story where a gorilla follows clues, asks for help, and learns {cluster.value}.",
        f"Write a gentle mystery ending with the missing {cluster.label} being returned to where it belongs.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type})")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
cluster(C) :- thing(C).
moral(M) :- value(M).
valid(P,C,M) :- place(P), cluster(C), moral(M).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for cid in CLUSTERS:
        lines.append(asp.fact("thing", cid))
    for mid in MORAL_VALUES:
        lines.append(asp.fact("value", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
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


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], CLUSTERS[params.cluster], params.helper, params.moral_value)
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
    StoryParams(place="garden", cluster="bananas", moral_value="sharing", helper="monkey"),
    StoryParams(place="riverbank", cluster="shells", moral_value="patience", helper="tortoise"),
    StoryParams(place="village_square", cluster="keys", moral_value="honesty", helper="child"),
    StoryParams(place="orchard", cluster="flowers", moral_value="care", helper="parrot"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.place} / {p.cluster} / {p.moral_value}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
