#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a desperate problem and a surprising help.

Premise:
A child in a tiny village loses an important treasure before a fairytale feast.
The child grows desperate, searches the woods, and finds a surprise helper who
knows the way home. The ending proves that the lost thing was found and that the
child changed from fear to relief.

This script follows the Storyweavers storyworld contract.
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "witch", "fairy"}
        male = {"boy", "man", "father", "king", "wizard", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    kind: str = "place"
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    tag: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Surprise:
    id: str
    label: str
    helper_type: str
    helper_label: str
    method: str
    gift: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    surprise_used: bool = False

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

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = {k: Entity(**{**v.__dict__, "meters": dict(v.meters), "memes": dict(v.memes)}) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.surprise_used = self.surprise_used
        return clone


@dataclass
class StoryParams:
    place: str
    treasure: str
    hero_name: str
    hero_gender: str
    parent_name: str
    seed: Optional[int] = None


PLACES = {
    "village": Place("village", "the little village", tags={"home", "village"}),
    "forest": Place("forest", "the moonlit forest", tags={"forest", "woods"}),
    "hill": Place("hill", "the windy hill", tags={"hill", "home"}),
}

TREASURES = {
    "crown": Treasure("crown", "a tiny golden crown", "golden crown", "crown"),
    "lantern": Treasure("lantern", "a silver lantern", "silver lantern", "lantern"),
    "key": Treasure("key", "an old brass key", "brass key", "key"),
}

SURPRISES = [
    Surprise(
        id="rabbit",
        label="a white rabbit",
        helper_type="rabbit",
        helper_label="white rabbit",
        method="hopped out of a hollow tree",
        gift="the right path home",
        tags={"forest", "help"},
    ),
    Surprise(
        id="bird",
        label="a bluebird",
        helper_type="bird",
        helper_label="bluebird",
        method="sang from the highest branch",
        gift="a shining clue",
        tags={"forest", "help"},
    ),
    Surprise(
        id="fireflies",
        label="a cloud of fireflies",
        helper_type="lights",
        helper_label="fireflies",
        method="sparkled in a little arrow",
        gift="a bright trail",
        tags={"forest", "help"},
    ),
]

GIRL_NAMES = ["Mira", "Lina", "Nora", "Elsa", "Ivy", "Rosa"]
BOY_NAMES = ["Otto", "Finn", "Milo", "Hugo", "Bram", "Theo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld with a desperate search and a surprise helper.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent")
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
    treasure = args.treasure or rng.choice(list(TREASURES))
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender not in TREASURES[treasure].genders:
        raise StoryError(f"(No story: {TREASURES[treasure].label} does not fit a {gender}'s fairy-tale role here.)")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or ("mother" if gender == "girl" else "father")
    return StoryParams(place=place, treasure=treasure, hero_name=name, hero_gender=gender, parent_name=parent)


def tell(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero_type = params.hero_gender
    hero = world.add(Entity(id=params.hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="parent", kind="character", type="mother" if params.parent_name == "mother" else "father"))
    treasure = world.add(Entity(
        id="treasure",
        kind="thing",
        type=TREASURES[params.treasure].id,
        label=TREASURES[params.treasure].label,
        phrase=TREASURES[params.treasure].phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))
    surprise = random.choice(SURPRISES)

    intro = (
        f"Once upon a time, in {world.place.label}, there was a little {hero_type} named {hero.id}. "
        f"{hero.id} loved {treasure.label} because it was the kind of thing a fairy tale could trust."
    )
    world.say(intro)
    world.say(f"One bright morning, {hero.id}'s {params.parent_name} set down {treasure.label} for a moment, and then it was gone.")
    world.para()

    hero.memes["worry"] = 1.0
    hero.memes["desperate"] = 1.0
    world.say(
        f"{hero.id} searched under chairs, behind baskets, and along the lane, but the treasure did not appear. "
        f"By dusk, {hero.id} was desperate and near tears."
    )
    world.say(
        f"Then {hero.id} slipped beyond the village gate and into {PLACES['forest'].label}, "
        f"hoping the dark trees might still be kind."
    )
    world.para()

    world.say(
        f"Just when the path seemed too long, a surprise appeared: {surprise.label} {surprise.method}. "
        f"It gave {hero.id} {surprise.gift}."
    )
    world.surprise_used = True
    hero.memes["hope"] = 1.0
    hero.memes["desperate"] = 0.0
    world.say(
        f"{hero.id} followed the clue and found {treasure.label} resting safely in the moss, "
        f"as if the woods had been guarding {treasure.it()} all along."
    )
    world.say(
        f"{hero.id} carried it home at once. {params.parent_name.capitalize()} smiled, and the whole little house felt warm again."
    )
    world.say(
        f"At last, {hero.id} was no longer desperate. {hero.id} had a lost treasure, a happy heart, and a surprising friend in the forest."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        treasure=treasure,
        surprise=surprise,
        place=world.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    treasure = f["treasure"]
    return [
        "Write a short fairy tale about a child who loses something precious, feels desperate, and gets a surprise help.",
        f"Tell a gentle story where {hero.id} loses {treasure.label} and a surprising forest helper shows the way.",
        "Write a child-friendly fairy tale with an introduction, a desperate search, a surprise, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    treasure = f["treasure"]
    parent = f["parent"]
    surprise = f["surprise"]
    return [
        QAItem(
            question=f"Who is the fairy tale about?",
            answer=f"It is about {hero.id}, a little {hero.type}, and {parent.pronoun('possessive')} lost treasure, {treasure.label}.",
        ),
        QAItem(
            question=f"What made {hero.id} desperate?",
            answer=f"{hero.id} became desperate when {treasure.label} went missing and the search went on until dusk.",
        ),
        QAItem(
            question=f"What was the surprise in the forest?",
            answer=f"The surprise was {surprise.label}, which appeared at just the right moment and gave a clue home.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} bringing {treasure.label} home safely and feeling happy again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fairy tale?",
            answer="A fairy tale is a made-up story with magical touches, a problem, and a hopeful ending.",
        ),
        QAItem(
            question="What does desperate mean?",
            answer="Desperate means feeling so worried or upset that you really need help right away.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that appears or happens when you do not quite see it coming.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"surprise_used={world.surprise_used}")
    return "\n".join(lines)


ASP_RULES = r"""
% A valid fairy tale needs a hero, a lost treasure, and a surprise helper.
valid_story(P,T,S) :- place(P), treasure(T), surprise(S).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    for s in SURPRISES:
        lines.append(asp.fact("surprise", s.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/3.")
    model = asp.one_model(program)
    triples = set(asp.atoms(model, "valid_story"))
    expected = {(p, t, s.id) for p in PLACES for t in TREASURES for s in SURPRISES}
    if triples == expected:
        print(f"OK: clingo gate matches Python registry set ({len(expected)} combos).")
        return 0
    print("MISMATCH:")
    if triples - expected:
        print(" only in clingo:", sorted(triples - expected))
    if expected - triples:
        print(" only in python:", sorted(expected - triples))
    return 1


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        items = sorted(set(asp.atoms(model, "valid_story")))
        for p, t, s in items:
            print(p, t, s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        all_params = [
            StoryParams(place=p, treasure=t, hero_name="Mira", hero_gender="girl", parent_name="mother")
            for p in PLACES for t in TREASURES
        ]
        for i, sp in enumerate(all_params):
            sp.seed = base_seed + i
            samples.append(generate(sp))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if len(samples) > 1:
            p = sample.params
            print(f"### variant {idx + 1}: {p.hero_name} / {p.place} / {p.treasure}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
