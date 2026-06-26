#!/usr/bin/env python3
"""
storyworlds/worlds/notorious_mystery_to_solve_moral_value_sound.py
===================================================================

A small fable-like story world about a notorious mystery, a careful search,
and a moral value learned through sound clues.

The seed idea:
---
In a quiet valley, a notorious raccoon was blamed whenever something went missing.
One morning, the little animals found the bell at the schoolhouse gone, and the
whole lane was full of worried whispers. A kind fox listened to the sound of the
ground, followed the tiny clues, and discovered that the bell had rolled into a
ditch after a windy bump. The fox told the truth, the animals apologized for
their hasty blame, and the valley learned that guessing too fast can be unkind.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "bear", "raccoon", "crow", "dog"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"mole", "hedgehog", "mouse", "rabbit", "squirrel"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    detail: str
    echoes: set[str] = field(default_factory=set)
    sounds: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing: str
    clue_sound: str
    culprit: str
    hiding_place: str
    lesson: str
    moral: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero: str
    sidekick: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, mystery: Mystery) -> None:
        self.place = place
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "valley": Place(
        id="valley",
        label="the quiet valley",
        detail="The valley had reeds, a schoolhouse, and a little ditch by the lane.",
        echoes={"soft", "clear"},
        sounds={"wind", "bell", "rustle"},
    ),
    "orchard": Place(
        id="orchard",
        label="the orchard",
        detail="The orchard had apple trees, a stone wall, and a creaky gate.",
        echoes={"rustle", "thud"},
        sounds={"wind", "gate", "branch"},
    ),
    "brook": Place(
        id="brook",
        label="the brook",
        detail="The brook ran beside a bridge, and wet stones shone in the sun.",
        echoes={"plunk", "splash"},
        sounds={"water", "plunk", "splash"},
    ),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        missing="schoolhouse bell",
        clue_sound="a tiny clink-clink",
        culprit="the wind",
        hiding_place="a ditch",
        lesson="do not blame too quickly",
        moral="A wise heart looks before it leaps to blame.",
    ),
    "basket": Mystery(
        id="basket",
        missing="berry basket",
        clue_sound="a soft bump-bump",
        culprit="a rolling cart",
        hiding_place="under a hedge",
        lesson="listen carefully before deciding",
        moral="Truth is kinder than a hurried guess.",
    ),
    "spoon": Mystery(
        id="spoon",
        missing="silver spoon",
        clue_sound="a little ping",
        culprit="a busy goose",
        hiding_place="in the grass",
        lesson="ask gentle questions",
        moral="A patient search can spare an unfair word.",
    ),
}

HEROES = {
    "fox": Entity(id="fox", kind="character", type="fox", label="fox"),
    "hedgehog": Entity(id="hedgehog", kind="character", type="hedgehog", label="hedgehog"),
    "rabbit": Entity(id="rabbit", kind="character", type="rabbit", label="rabbit"),
    "mouse": Entity(id="mouse", kind="character", type="mouse", label="mouse"),
}

SIDEKICKS = {
    "crow": Entity(id="crow", kind="character", type="crow", label="crow"),
    "mole": Entity(id="mole", kind="character", type="mole", label="mole"),
    "squirrel": Entity(id="squirrel", kind="character", type="squirrel", label="squirrel"),
    "dog": Entity(id="dog", kind="character", type="dog", label="dog"),
}

NAME_BY_KIND = {
    "fox": "Fenn",
    "hedgehog": "Pip",
    "rabbit": "Rose",
    "mouse": "Milo",
    "crow": "Corbin",
    "mole": "Mina",
    "squirrel": "Sage",
    "dog": "Dot",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A fable-like mystery storyworld with sound clues and a moral."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    hero = args.hero or rng.choice(list(HEROES))
    sidekick_choices = [k for k in SIDEKICKS if k != hero]
    sidekick = args.sidekick or rng.choice(sidekick_choices)
    if sidekick == hero:
        raise StoryError("The hero and sidekick must be different characters.")
    return StoryParams(place=place, mystery=mystery, hero=hero, sidekick=sidekick)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for s in sorted(place.echoes):
            lines.append(asp.fact("echoes", pid, s))
        for s in sorted(place.sounds):
            lines.append(asp.fact("has_sound", pid, s))
    for mid, my in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, my.missing))
        lines.append(asp.fact("clue_sound", mid, my.clue_sound))
        lines.append(asp.fact("culprit", mid, my.culprit))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for sid in SIDEKICKS:
        lines.append(asp.fact("sidekick", sid))
    return "\n".join(lines)


ASP_RULES = r"""
clueable(P, M) :- has_sound(P, S), clue_sound(M, S).
compatible(P, M) :- place(P), mystery(M), clueable(P, M).
good_story(P, M, H, S) :- compatible(P, M), hero(H), sidekick(S), H != S.
#show compatible/2.
#show good_story/4.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatible() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_good_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/4."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = {
        (p, m)
        for p in PLACES
        for m in MYSTERIES
        if any(s in PLACES[p].sounds for s in [MYSTERIES[m].clue_sound])
    }
    cl = set(asp_compatible())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(cl)} compatible pairs).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("  only in python:", sorted(py - cl))
    print("  only in ASP:", sorted(cl - py))
    return 1


def story_intro(world: World, hero: Entity, sidekick: Entity, missing: str) -> None:
    world.say(
        f"In {world.place.label}, there lived a notorious little {hero.type} named {hero.id}, "
        f"and a faithful {sidekick.type} named {sidekick.id}."
    )
    world.say(
        f"One morning, the {missing} went missing, and every tail and ear in the lane began to wonder."
    )


def sound_search(world: World, hero: Entity, sidekick: Entity, mystery: Mystery) -> None:
    world.para()
    world.say(world.place.detail)
    world.say(
        f"{hero.id} listened closely, because {hero.pronoun('subject')} knew that a clue can hide inside a sound."
    )
    world.say(
        f"Then {hero.id} heard {mystery.clue_sound} near the path, while {sidekick.id} heard the same sound by the grass."
    )
    world.say(
        f"They followed the sound to {mystery.hiding_place}, where the missing thing had been caught after a windy bump."
    )
    world.facts["found"] = True
    world.facts["sound"] = mystery.clue_sound
    world.facts["hiding_place"] = mystery.hiding_place


def reveal(world: World, hero: Entity, sidekick: Entity, mystery: Mystery) -> None:
    world.para()
    world.say(
        f"At last, {hero.id} told the truth: the {mystery.missing} was not stolen at all."
    )
    world.say(
        f"It had rolled away when {mystery.culprit} blew hard, and the sharp little sound had pointed the way."
    )
    world.say(
        f"The villagers felt ashamed for their hasty blame, and they thanked {hero.id} for careful ears and a patient heart."
    )
    world.say(
        f"From that day on, the valley remembered {mystery.moral.lower()}"
    )
    world.facts["revealed"] = True


def tell(place: Place, mystery: Mystery, hero_kind: str, sidekick_kind: str) -> World:
    world = World(place, mystery)
    hero = world.add(Entity(id=NAME_BY_KIND[hero_kind], kind="character", type=hero_kind, label=hero_kind))
    sidekick = world.add(Entity(id=NAME_BY_KIND[sidekick_kind], kind="character", type=sidekick_kind, label=sidekick_kind))
    world.facts.update(place=place, mystery=mystery, hero=hero, sidekick=sidekick)
    story_intro(world, hero, sidekick, mystery.missing)
    sound_search(world, hero, sidekick, mystery)
    reveal(world, hero, sidekick, mystery)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    sidekick: Entity = f["sidekick"]  # type: ignore[assignment]
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    return [
        f'Write a short fable about a notorious {hero.type} who helps solve a mystery in {place.label}.',
        f"Tell a child-friendly mystery story where {hero.id} and {sidekick.id} follow a tiny sound clue to find the {mystery.missing}.",
        f'Write a simple story with sound effects like "{mystery.clue_sound}" and a moral about not blaming too fast.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    sidekick: Entity = f["sidekick"]  # type: ignore[assignment]
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the notorious helper in the story?",
            answer=f"The notorious helper was {hero.id}, who listened carefully and helped solve the mystery in {place.label}.",
        ),
        QAItem(
            question=f"What was the missing thing in the story?",
            answer=f"The missing thing was the {mystery.missing}.",
        ),
        QAItem(
            question=f"What sound clue led {hero.id} and {sidekick.id} to the answer?",
            answer=f"They followed {mystery.clue_sound}, which led them to {mystery.hiding_place}.",
        ),
        QAItem(
            question=f"What lesson did the valley learn?",
            answer=f"The valley learned that {mystery.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something unknown that people try to figure out by looking for clues.",
        ),
        QAItem(
            question="What is a sound clue?",
            answer="A sound clue is a noise that helps someone notice where something is or what happened.",
        ),
        QAItem(
            question="What is a moral in a fable?",
            answer="A moral is the lesson the story wants you to remember after it ends.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} ({e.type})")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="valley", mystery="bell", hero="fox", sidekick="crow"),
    StoryParams(place="orchard", mystery="basket", hero="hedgehog", sidekick="mole"),
    StoryParams(place="brook", mystery="spoon", hero="rabbit", sidekick="squirrel"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MYSTERIES[params.mystery], params.hero, params.sidekick)
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


def build_story_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        comps = asp_compatible()
        goods = asp_good_stories()
        print(f"{len(comps)} compatible place/mystery pairs ({len(goods)} with hero+sidekick):\n")
        for p, m in comps:
            pairs = sorted((h, s) for (pp, mm, h, s) in goods if (pp, mm) == (p, m))
            print(f"  {p:8} {m:8}  {pairs}")
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
            header = f"### {p.hero} and {p.sidekick} in {p.place} ({p.mystery})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
