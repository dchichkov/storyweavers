#!/usr/bin/env python3
"""
A small storyworld for a fairground whodunit with problem solving, inner monologue,
and a deliberately bad ending.

Premise:
A child at a fair notices a missing item, follows clues, reasons through the scene,
and tries to solve the mystery. The world is structured so the deduction matters,
but the ending can still go wrong.

The tone aims at a child-friendly whodunit: concrete clues, little bits of suspense,
and a final twist that proves the problem was not neatly fixed.
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
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    noise: str
    clues: list[str] = field(default_factory=list)
    suspects: list[str] = field(default_factory=list)


@dataclass
class Clue:
    id: str
    text: str
    points_to: str
    strength: float = 1.0


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Mina"
    hero_type: str = "girl"
    helper: str = "Aunt June"
    suspect: str = "the clown"
    missing: str = "ticket booklet"
    place: str = "fair"
    mood: str = "windy"


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


FAIRS = {
    "fair": Place(
        name="the fair",
        noise="bells, laughter, and music",
        clues=["cotton candy fluff", "muddy boot print", "a torn raffle stub"],
        suspects=["the clown", "the prize seller", "the balloon twister"],
    )
}

MISSING_ITEMS = {
    "ticket booklet": "small red ticket booklet",
    "blue ribbon": "blue ribbon with a star",
    "toy fox": "little toy fox",
}

CLUES = {
    "cotton candy fluff": Clue("fluff", "sweet pink fluff stuck to a sleeve", "cotton candy stand", 1.0),
    "muddy boot print": Clue("print", "a muddy boot print near the game booth", "game booth", 1.0),
    "a torn raffle stub": Clue("stub", "a torn raffle stub under a bench", "raffle table", 1.0),
}

ASP_RULES = r"""
missing_item(X) :- item(X).
clue(C) :- clue_fact(C,_).
suspect(S) :- suspect_fact(S).

links(C, P) :- clue_fact(C, P).
possible(S, X) :- suspect_fact(S), item(X), clue_fact(_, P), points_to(P, S).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for k in MISSING_ITEMS:
        lines.append(asp.fact("item", k))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue_fact", cid, clue.points_to))
        lines.append(asp.fact("points_to", clue.points_to, clue.points_to))
    for s in FAIRS["fair"].suspects:
        lines.append(asp.fact("suspect_fact", s))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fair whodunit storyworld with a bad ending.")
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--suspect")
    ap.add_argument("--missing", choices=sorted(MISSING_ITEMS))
    ap.add_argument("--place", choices=sorted(FAIRS))
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
    hero = args.hero or rng.choice(["Mina", "Nico", "Tess", "Owen"])
    helper = args.helper or rng.choice(["Aunt June", "Grandpa Sol", "Ms. Peta"])
    suspect = args.suspect or rng.choice(FAIRS[args.place or "fair"].suspects)
    missing = args.missing or rng.choice(list(MISSING_ITEMS))
    place = args.place or "fair"
    return StoryParams(
        seed=args.seed,
        hero=hero,
        helper=helper,
        suspect=suspect,
        missing=missing,
        place=place,
        mood="windy",
    )

def _inner_monologue(world: World, hero: Entity, clue: Clue) -> None:
    world.say(
        f"{hero.pronoun('subject').capitalize()} frowned and thought, "
        f'"If that clue points to the {clue.points_to}, then someone was there before me."'
    )
    hero.memes["focus"] = hero.memes.get("focus", 0) + 1

def _investigate(world: World, hero: Entity) -> list[Clue]:
    found: list[Clue] = []
    for clue_text in world.place.clues:
        clue = CLUES[clue_text]
        found.append(clue)
        world.say(f"{hero.id} spotted {clue.text}.")
        _inner_monologue(world, hero, clue)
    return found

def _deduce(world: World, hero: Entity, helper: Entity, suspect: Entity, missing: Entity, clues: list[Clue]) -> None:
    if any(c.points_to == "raffle table" for c in clues):
        world.say(
            f"{hero.id} whispered to {helper.id}, "
            f'"The torn raffle stub means the {suspect.label} may have been near the prizes."'
        )
    if any(c.points_to == "game booth" for c in clues):
        world.say(
            f"{helper.id} nodded and said, "
            f'"Then the muddy print shows the {suspect.label} also went by the games."'
        )
    if any(c.points_to == "cotton candy stand" for c in clues):
        world.say(
            f"{hero.id} thought harder. "
            f'"And the sweet fluff means the {suspect.label} passed the candy cart too."'
        )
    hero.memes["certainty"] = hero.memes.get("certainty", 0) + 1
    world.facts["deduced"] = True

def _bad_turn(world: World, hero: Entity, suspect: Entity, missing: Entity) -> None:
    world.say(
        f"{hero.id} hurried to the {suspect.label}, ready to ask for the {missing.label}."
    )
    world.say(
        f"But the crowd pressed in, the music jumped loud, and someone bumped the table."
    )
    missing.hidden_in = "spilled funnel cake"
    world.say(
        f"When the dust settled, the {missing.label} was gone again, hidden in the mess."
    )
    world.facts["bad_ending"] = True

def tell(params: StoryParams) -> World:
    place = FAIRS[params.place]
    world = World(place)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, label=params.hero))
    helper = world.add(Entity(id=params.helper, kind="character", type="adult", label=params.helper))
    suspect = world.add(Entity(id=params.suspect, kind="character", type="adult", label=params.suspect))
    missing = world.add(Entity(
        id=params.missing,
        kind="thing",
        type="thing",
        label=params.missing,
        phrase=MISSING_ITEMS[params.missing],
        owner=hero.id,
    ))

    world.say(f"{hero.id} came to {place.name} on a {params.mood} evening, where the air rang with {place.noise}.")
    world.say(f"{hero.id} noticed {hero.pronoun('possessive')} {missing.label} was missing.")
    world.say(
        f"{hero.id} and {helper.id} looked under benches, beside games, and near the prize counter."
    )
    clues = _investigate(world, hero)
    _deduce(world, hero, helper, suspect, missing, clues)
    world.para()
    _bad_turn(world, hero, suspect, missing)
    world.say(
        f"{hero.id} stared at the spinning lights and thought, "
        f'"I was sure I could solve it."'
    )
    world.facts.update(hero=hero, helper=helper, suspect=suspect, missing=missing, clues=clues, place=place)
    return world

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    missing: Entity = f["missing"]
    return [
        f"Write a child-friendly whodunit at a fair where {hero.id} searches for a missing {missing.label}.",
        f"Tell a short mystery story with clues, an inner monologue, and a bad ending at the fair.",
        f"Write a story about a fair, a scrubbed-down clue trail, and a child who tries to solve the case.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    suspect: Entity = f["suspect"]
    missing: Entity = f["missing"]
    clues: list[Clue] = f["clues"]
    qa = [
        QAItem(
            question=f"What was missing when {hero.id} arrived at the fair?",
            answer=f"{hero.id} noticed that {hero.pronoun('possessive')} {missing.label} was missing.",
        ),
        QAItem(
            question=f"Who helped {hero.id} look for the missing item?",
            answer=f"{helper.id} helped {hero.id} look under benches, by the games, and near the prize counter.",
        ),
        QAItem(
            question=f"What clue made {hero.id} think about {suspect.label}?",
            answer=f"{hero.id} found clues like {', '.join(c.text for c in clues)} and thought they pointed toward {suspect.label}.",
        ),
        QAItem(
            question=f"Did the mystery end well for {hero.id}?",
            answer=f"No. The story ends badly because the missing {missing.label} is lost again in the crowd and mess.",
        ),
    ]
    return qa

def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fair?",
            answer="A fair is a busy place with games, prizes, food, music, and lots of people moving around.",
        ),
        QAItem(
            question="What does a clue do in a mystery?",
            answer="A clue gives a small piece of information that can help someone figure out what happened.",
        ),
        QAItem(
            question="Why do people scrub things clean?",
            answer="People scrub things when they want to wash off dirt, stains, or sticky messes.",
        ),
    ]

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    lines.append(f"  facts={sorted(world.facts)}")
    return "\n".join(lines)

def format_qa(sample: StorySample) -> str:
    out = ["== Story questions =="]
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)

CURATED = [StoryParams(hero="Mina", helper="Aunt June", suspect="the clown", missing="ticket booklet", place="fair")]

def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    program = asp_program("#show missing_item/1.\n#show clue/1.\n#show suspect/1.\n")
    model = asp.one_model(program)
    if model is None:
        print("ASP produced no model.")
        return 1
    print("OK: ASP program solved.")
    return 0

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

def main() -> None:
    ap = build_parser()
    args = ap.parse_args()

    if args.show_asp:
        print(asp_program("#show missing_item/1.\n#show clue/1.\n#show suspect/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())

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
