#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

PARADE_STEPS = ["start", "march", "solve", "end"]


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
    hidden: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Place:
    id: str
    label: str
    kind: str
    clues: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    guide_name: str
    guide_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.steps: list[str] = []
        self.flashback_used = False

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.steps.append(text)

    def render(self) -> str:
        return "\n\n".join(self.steps)


SETTINGS = {
    "parade": Place(
        id="parade",
        label="the village parade",
        kind="parade_route",
        clues=["music", "streamers", "drums"],
    ),
    "lantern_square": Place(
        id="lantern_square",
        label="the lantern square",
        kind="square",
        clues=["lanterns", "chalk", "footprints"],
    ),
}

HEROES = ["Mina", "Pip", "Lena", "Tobi", "Anya", "Bram"]
GUIDES = ["Grandma", "Uncle", "Auntie", "Mother", "Father", "Old Ben"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world about a parade mystery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--guide")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    lines.append(asp.fact("story_feature", "mystery_to_solve"))
    lines.append(asp.fact("story_feature", "curiosity"))
    lines.append(asp.fact("story_feature", "flashback"))
    lines.append(asp.fact("seed_word", "parade"))
    lines.append(asp.fact("seed_word", "panty"))
    return "\n".join(lines)


ASP_RULES = r"""
feature(mystery_to_solve) :- story_feature(mystery_to_solve).
feature(curiosity) :- story_feature(curiosity).
feature(flashback) :- story_feature(flashback).
compatible(P) :- place(P).
#show compatible/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/1."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    a = set(asp_valid_places())
    p = {(k,) for k in SETTINGS}
    if a == p:
        print(f"OK: ASP matches Python ({len(a)} places).")
        return 0
    print("MISMATCH")
    print("only ASP:", sorted(a - p))
    print("only Python:", sorted(p - a))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HEROES)
    guide_name = args.guide or rng.choice(GUIDES)
    guide_type = "mother" if guide_name in {"Mother", "Auntie", "Grandma"} else "father"
    hero_type = gender
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, guide_name=guide_name, guide_type=guide_type)


def tell(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    guide = world.add(Entity(id=params.guide_name, kind="character", type=params.guide_type))
    panty = world.add(Entity(
        id="panty", type="panty", label="panty", phrase="a little red panty",
        owner=hero.id, caretaker=guide.id, hidden=True
    ))
    ribbon = world.add(Entity(
        id="ribbon", type="ribbon", label="ribbon", phrase="a ribbon from the laundry line",
        hidden=True
    ))
    world.facts.update(hero=hero, guide=guide, panty=panty, ribbon=ribbon, place=place)

    hero.memes["curiosity"] = 1
    world.say(
        f"Once in the village {place.label}, there lived a small {hero.type} named {hero.id} "
        f"who loved to ask why the wind sang through the flags."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} had a sharp curiosity, and that morning "
        f"{hero.pronoun()} wandered beside the parade drums, looking for whatever the crowd had lost."
    )
    world.say(
        f"Near the bright stalls, {hero.id} saw a tiny {panty.label} tucked under a cart wheel, "
        f"and the sight made {hero.pronoun('object')} stop as still as a cat in rain."
    )
    hero.memes["mystery"] = 1
    panty.hidden = False
    world.say(
        f'“Whose {panty.label} is this?” {hero.id} wondered. “It must have a story.”'
    )

    world.say(
        f"{guide.id} smiled and said the answer might lie in an old memory, "
        f"for folk tales often hide their keys in the past."
    )
    world.flashback_used = True
    world.say(
        f"Then the story slipped into a flashback: before the parade, the {guide.label} had washed clothes on the line, "
        f"and a gust of wind had blown a bright little {panty.label} down into a basket."
    )
    ribbon.found = True
    panty.found = True
    panty.hidden = False
    hero.memes["joy"] = 1
    world.say(
        f"When the memory returned, {hero.id} laughed softly, because the mystery was simple after all: "
        f"the {panty.label} had only been blown away."
    )
    world.say(
        f"{guide.id} pinned the {panty.label} back with the ribbon, and the parade marched on under the sunshine, "
        f"while {hero.id} walked beside the music feeling wiser than before."
    )

    world.facts["solved"] = True
    world.facts["flashback"] = True
    world.facts["curiosity"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a gentle folk tale about a parade mystery involving a lost panty and a curious {hero.type}.",
        f"Tell a child-friendly story where {hero.id} solves a small mystery during a parade by remembering a flashback.",
        "Write a short story with curiosity, a flashback, and a happy ending at a parade.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    guide: Entity = f["guide"]  # type: ignore[assignment]
    panty: Entity = f["panty"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where did {hero.id} find the mystery item?",
            answer=f"{hero.id} found the little {panty.label} beside the parade route at {place.label}.",
        ),
        QAItem(
            question=f"What made {hero.id} curious?",
            answer=f"{hero.id} was curious because the tiny {panty.label} looked as if it had a story to tell.",
        ),
        QAItem(
            question=f"What was the flashback about?",
            answer=f"The flashback showed {guide.id} washing clothes on the line before a gust of wind blew the {panty.label} away.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"The mystery was solved when the memory explained that the {panty.label} had blown from the laundry line, so {guide.id} could pin it back safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is a happy procession where people walk together with music, colors, and cheering.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn why something happened.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that jumps back to something that happened earlier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place={world.place.id} clues={world.place.clues}")
    for e in world.entities.values():
        bits = []
        if e.hidden:
            bits.append("hidden=True")
        if e.found:
            bits.append("found=True")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"flashback_used={world.flashback_used}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(place="parade", hero_name="Mina", hero_type="girl", guide_name="Grandma", guide_type="mother"),
    StoryParams(place="lantern_square", hero_name="Pip", hero_type="boy", guide_name="Old Ben", guide_type="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        places = asp_valid_places()
        print(f"{len(places)} compatible places:")
        for p in places:
            print(p[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
