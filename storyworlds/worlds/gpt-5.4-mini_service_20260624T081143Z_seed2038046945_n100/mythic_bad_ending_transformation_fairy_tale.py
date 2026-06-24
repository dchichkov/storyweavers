#!/usr/bin/env python3
"""
mythic_bad_ending_transformation_fairy_tale.py

A small fairy-tale storyworld about a mythic bargain, a transformation, and a
bad ending that still feels like a complete tale.
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

ASP_RULES = r"""
heroic(0, H) :- hero(H), has_mythic_boon(H), brave(H).
warns(0, H) :- hero(H), near_forest(H), hears_whisper(H).
transforms(0, H, F) :- hero(H), turned_into(H, F).
bad_ending(0, H) :- hero(H), turned_into(H, F), trapped_as(H, F), not freed(H).
"""

@dataclass
class StoryParams:
    hero: str = "Mira"
    companion: str = "Grandmother"
    boon: str = "silver thread"
    curse: str = "owl-feather curse"
    creature: str = "owl"
    place: str = "the moonlit forest"
    seed: Optional[int] = None

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    transformed_into: str = ""

class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, str] = {}
        self.events: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)

    def trace(self) -> str:
        lines = ["--- world trace ---"]
        for e in self.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            if e.transformed_into:
                bits.append(f"transformed_into={e.transformed_into}")
            lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
        return "\n".join(lines)

HEROES = ["Mira", "Elin", "Talia", "Nora", "Iris"]
COMPANIONS = ["Grandmother", "Old Hunter", "River Aunt"]
BOONS = ["silver thread", "golden key", "star comb", "ember cloak"]
CURSES = ["owl-feather curse", "stone-hush curse", "glass-root curse"]
CREATURES = ["owl", "stag", "wolf", "deer"]
PLACES = ["the moonlit forest", "the hollow hill", "the briar path", "the old well"]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale mythic transformation world with a bad ending.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--boon", choices=BOONS)
    ap.add_argument("--curse", choices=CURSES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--place", choices=PLACES)
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
    return StoryParams(
        hero=args.hero or rng.choice(HEROES),
        companion=args.companion or rng.choice(COMPANIONS),
        boon=args.boon or rng.choice(BOONS),
        curse=args.curse or rng.choice(CURSES),
        creature=args.creature or rng.choice(CREATURES),
        place=args.place or rng.choice(PLACES),
        seed=args.seed,
    )

def asp_facts() -> str:
    import asp
    lines = [asp.fact("hero", 1)]
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{ASP_RULES}\n{show}\n"

def generate(params: StoryParams) -> StorySample:
    w = World()
    hero = w.add(Entity("hero", "character", params.hero, "girl"))
    companion = w.add(Entity("companion", "character", params.companion, "elder"))
    boon = w.add(Entity("boon", "thing", params.boon, "charm"))
    curse = w.add(Entity("curse", "thing", params.curse, "curse"))
    beast = w.add(Entity("beast", "thing", params.creature, "creature"))

    hero.memes["hope"] = 1
    hero.meters["journey"] = 1
    w.say(f"Long ago, {hero.label} walked into {params.place} with {companion.label} and a {boon.label}.")
    w.say(f"They sought a cure for the {curse.label}, because the old tale said a {beast.label} guarded the last spring.")
    w.say(f"At the heart of the wood, the {beast.label} spoke in a voice like wind through reeds and offered a bargain.")
    w.say(f"If {hero.label} gave up the {boon.label}, the beast would grant a wish, but the wish would not come free.")
    hero.memes["fear"] = 1
    hero.transformed_into = "small owl"
    hero.meters["body"] = 1
    w.say(f"{hero.label} accepted, and the magic changed her into a {hero.transformed_into}.")
    w.say(f"The owl flew once above the trees, but the curse took the wish sideways, and the path home vanished under thorns.")
    w.say(f"So the tale ended with {hero.label} still trapped in feather and shadow, while {companion.label} wept beneath the moon.")
    w.facts.update(hero=hero, companion=companion, boon=boon, curse=curse, beast=beast, params=params)
    prompts = [
        f"Write a fairy tale about {params.hero} who meets a mythic creature in {params.place}.",
        f"Tell a short story where a boon and a curse lead to a transformation with a sad ending.",
    ]
    story_qa = [
        QAItem(question="Who went into the forest?", answer=f"{params.hero} went with {params.companion}."),
        QAItem(question="What changed the hero?", answer=f"The magic bargain changed {params.hero} into a {hero.transformed_into}."),
        QAItem(question="How did the story end?", answer=f"It ended badly, with {params.hero} trapped after the transformation."),
    ]
    world_qa = [
        QAItem(question="What is a transformation in a fairy tale?", answer="It is when magic changes one person or creature into another form."),
        QAItem(question="Why can a bargain be dangerous in myths?", answer="A bargain can be dangerous because the gift may hide a cost that hurts the hero later."),
    ]
    return StorySample(params=params, story=w.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=w)

def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(sample.prompts)
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show heroic/2."))
        return
    if args.verify:
        print("OK: verify stub for mythic world.")
        return
    rng = random.Random(args.seed)
    samples = [generate(resolve_params(args, rng)) for _ in range(args.n)]
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))

if __name__ == "__main__":
    main()
