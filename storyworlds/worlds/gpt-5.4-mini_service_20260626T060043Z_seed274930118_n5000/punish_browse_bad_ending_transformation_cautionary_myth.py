#!/usr/bin/env python3
"""
storyworlds/worlds/punish_browse_bad_ending_transformation_cautionary_myth.py
=============================================================================

A small mythic storyworld about a curious child who browses a forbidden shrine,
disobeys a warning, and is transformed as a cautionary ending.

Premise:
- A young seeker loves to browse old carved tablets in a sacred grove.
- An elder warns the seeker not to touch the sealed idol or read the curse-marked lines.
- The seeker ignores the caution, and a guardian spirit punishes the choice.
- The punishment is a transformation that leaves a lasting, bad ending.

The world is designed to be:
- concrete and state-driven,
- child-facing in prose,
- mythic in tone,
- cautionary in structure,
- and strict about reasonableness.

The story is not a frozen template: state changes drive the narration.
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
# Entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    transformed: bool = False
    transformed_into: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    sacred: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    curse: str
    region: str
    risky: bool = False


@dataclass
class EntityOutcome:
    punished: bool = False
    transformed: bool = False
    ending: str = ""


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.items = _copy.deepcopy(self.items)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "grove": Place(id="grove", label="the old grove", sacred=True, affords={"browse"}),
    "temple": Place(id="temple", label="the temple steps", sacred=True, affords={"browse"}),
    "ruins": Place(id="ruins", label="the moonlit ruins", sacred=True, affords={"browse"}),
}

BROSWABLES = {
    "tablets": Item(
        id="tablets",
        label="stone tablets",
        phrase="old stone tablets with carved lines",
        curse="they carried a sleeping curse",
        region="hands",
        risky=True,
    ),
    "idol": Item(
        id="idol",
        label="sealed idol",
        phrase="a sealed idol wrapped in silver vines",
        curse="it woke when touched",
        region="hands",
        risky=True,
    ),
    "scrolls": Item(
        id="scrolls",
        label="dusty scrolls",
        phrase="dusty scrolls tied with red thread",
        curse="they were bound to a warning",
        region="hands",
        risky=True,
    ),
}

HERO_NAMES = ["Mira", "Soren", "Ilya", "Niko", "Tara", "Lina", "Arin", "Koa"]
GUIDE_NAMES = ["the elder", "the keeper", "the priest", "the grandmother"]
TRAITS = ["curious", "careless", "restless", "brave", "quick-eyed"]


@dataclass
class StoryParams:
    place: str
    browse: str
    name: str
    guide: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A browse target is risky if it is marked risky.
risky_item(I) :- item(I), risky(I).

% Browsing in a sacred place with a risky item is enough to create danger.
danger(P, I) :- sacred(P), browse_at(P), risky_item(I).

% Punishment follows when the child ignores warning and danger is present.
punish(C) :- warning(C), danger(P, I), chooses_browse(C, I), in_place(C, P).

% Transformation is the mythic punishment in this world.
transform(C) :- punish(C).

% A valid myth story requires a punishment and a transformation.
valid_story(P, I) :- sacred(P), item(I), risky_item(I).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.sacred:
            lines.append(asp.fact("sacred", pid))
        for act in sorted(place.affords):
            lines.append(asp.fact("affords", pid, act))
    for iid, item in BROSWABLES.items():
        lines.append(asp.fact("item", iid))
        if item.risky:
            lines.append(asp.fact("risky", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def browse_is_reasonable(place: Place, item: Item) -> bool:
    return "browse" in place.affords and item.risky and place.sacred


def explain_rejection(place: Place, item: Item) -> str:
    return (
        f"(No story: browsing {item.label} at {place.label} would not make a mythic "
        f"turn unless the place is sacred and the object is dangerous.)"
    )


def choose_names(rng: random.Random, guide: str) -> tuple[str, str]:
    name = rng.choice(HERO_NAMES)
    return name, guide


def age_phrase(trait: str) -> str:
    return f"a {trait} child"


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    item = BROSWABLES[params.browse]
    world = World(place)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        traits=[params.trait],
        meters={"curiosity": 1.0, "fear": 0.0},
        memes={"wonder": 1.0, "warning": 0.0, "defiance": 0.0, "shame": 0.0},
    ))
    guide = world.add(Entity(
        id="guide",
        kind="character",
        type="elder",
        label=params.guide,
        meters={"age": 10.0},
        memes={"care": 1.0},
    ))
    world.add_item(item)
    world.facts.update(hero=hero, guide=guide, item=item, place=place, outcome=EntityOutcome())
    return world


def predict_punishment(world: World, hero: Entity, place: Place, item: Item) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["defiance"] = 1.0
    return browse_is_reasonable(place, item)


def tell_story(world: World) -> None:
    hero: Entity = world.facts["hero"]
    guide: Entity = world.facts["guide"]
    item: Item = world.facts["item"]
    place: Place = world.facts["place"]
    outcome: EntityOutcome = world.facts["outcome"]

    world.say(
        f"{hero.id} was {age_phrase(hero.traits[0])} who loved to browse old things in {place.label}."
    )
    world.say(
        f"Every day, {hero.id} looked at carvings and wondered what secrets slept in them."
    )

    world.para()
    world.say(
        f"One dusk, {guide.label} warned {hero.id}, \"Do not browse {item.label}; {item.curse}.\""
    )
    world.say(
        f"But {hero.id}'s wonder was bigger than caution, and {hero.id} stepped closer anyway."
    )
    hero.memes["warning"] += 1.0
    hero.memes["defiance"] += 1.0

    world.para()
    if browse_is_reasonable(place, item):
        hero.meters["near_item"] = 1.0
        world.say(f"{hero.id} reached for {item.phrase}.")
        world.say(f"The air turned still, as if the grove itself was listening.")
        hero.meters["curse"] = 1.0
        outcome.punished = True
        hero.memes["shame"] += 1.0
        world.say(
            f"Then the guardian spirit punished {hero.id} for the choice."
        )
        hero.transformed = True
        hero.transformed_into = "a white stone fox"
        outcome.transformed = True
        world.say(
            f"Light wrapped around {hero.id}, and when it faded, {hero.id} was no longer a child, "
            f"but a white stone fox at the shrine gate."
        )
        world.say(
            f"{guide.label} wept softly, because the lesson had become a bad ending."
        )
        outcome.ending = "bad ending"
    else:
        world.say(
            f"{hero.id} looked, but the old warning felt too strong, and {hero.id} stepped back."
        )
        world.say(f"The grove stayed quiet, and the curse did not wake.")
        outcome.ending = "safe ending"

    world.facts["outcome"] = outcome


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    item: Item = f["item"]
    place: Place = f["place"]
    return [
        f'Write a short mythic story about a curious child who wants to browse "{item.label}" in {place.label}.',
        f"Tell a cautionary tale in which {hero.id} ignores a warning and is punished after browsing a forbidden relic.",
        f"Write a child-friendly myth with a bad ending and a transformation after someone browses a sacred object.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    guide: Entity = f["guide"]
    item: Item = f["item"]
    place: Place = f["place"]
    outcome: EntityOutcome = f["outcome"]

    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, {age_phrase(hero.traits[0])} who loved to browse old things in {place.label}.",
        ),
        QAItem(
            question=f"What did {guide.label} warn {hero.id} not to do?",
            answer=f"{guide.label} warned {hero.id} not to browse {item.label}, because {item.curse}.",
        ),
        QAItem(
            question=f"What happened when {hero.id} ignored the warning?",
            answer=(
                f"{hero.id} was punished by a guardian spirit and transformed into "
                f"{hero.transformed_into or 'something else'}, which made the ending a bad one."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to browse something?",
            answer="To browse means to look through or examine things one by one, often with curiosity.",
        ),
        QAItem(
            question="What is a cautionary tale?",
            answer="A cautionary tale is a story that warns about bad choices and what can happen after them.",
        ),
        QAItem(
            question="What is a transformation in a myth?",
            answer="A transformation is when a person or creature changes into a different form, often because of magic.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} "
            f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}} "
            f"transformed={e.transformed} into={e.transformed_into!r}"
        )
    lines.append(f"ending={world.facts['outcome'].ending}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, place in PLACES.items():
        for iid, item in BROSWABLES.items():
            if browse_is_reasonable(place, item):
                out.append((pid, iid))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.browse:
        place = PLACES[args.place]
        item = BROSWABLES[args.browse]
        if not browse_is_reasonable(place, item):
            raise StoryError(explain_rejection(place, item))

    combos = [
        (p, i) for p, i in valid_combos()
        if (args.place is None or p == args.place)
        and (args.browse is None or i == args.browse)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, browse = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    guide = args.guide or rng.choice(GUIDE_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, browse=browse, name=name, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


# ---------------------------------------------------------------------------
# ASP verification
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    import asp

    py = set(valid_combos())
    model = asp.one_model(asp_program("#show valid_story/2."))
    cl = set(asp.atoms(model, "valid_story"))
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic cautionary storyworld about browsing forbidden things.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--browse", choices=BROSWABLES)
    ap.add_argument("--name")
    ap.add_argument("--guide")
    ap.add_argument("--trait")
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


CURATED = [
    StoryParams(place="grove", browse="idol", name="Mira", guide="the elder", trait="curious"),
    StoryParams(place="temple", browse="tablets", name="Soren", guide="the keeper", trait="restless"),
    StoryParams(place="ruins", browse="scrolls", name="Tara", guide="the grandmother", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/2."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} valid myth stories:")
        for place, item in vals:
            print(f"  {place} / {item}")
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
            header = f"### {p.name}: browse {p.browse} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
