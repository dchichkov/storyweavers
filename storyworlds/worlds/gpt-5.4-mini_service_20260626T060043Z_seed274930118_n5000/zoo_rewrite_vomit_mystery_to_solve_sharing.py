#!/usr/bin/env python3
"""
storyworlds/worlds/zoo_rewrite_vomit_mystery_to_solve_sharing.py
==================================================================

A small superhero-style story world at the zoo: a child hero, a gross mystery,
a clue that gets rewritten, and a shared plan that solves the problem.

Seed words: zoo, rewrite, vomit
Narrative instruments: mystery to solve, sharing
Style: superhero story
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the zoo"
    exhibits: list[str] = field(default_factory=lambda: ["lion den", "monkey yard", "bird house", "snack stand"])


@dataclass
class Mystery:
    culprit: str
    mess: str
    clue: str
    evidence: str
    solved_by: str


@dataclass
class SharingItem:
    label: str
    phrase: str
    protects: str = ""
    helps: str = ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    hero_trait: str
    sidekick_name: str
    sidekick_type: str
    setting: str
    mystery: str
    share_item: str
    seed: Optional[int] = None


SETTINGS = {"zoo": Setting()}
HERO_NAMES = ["Milo", "Ava", "Zuri", "Leo", "Nia", "Theo", "Maya", "Finn"]
SIDEKICK_NAMES = ["Spark", "Comet", "Nova", "Beam"]
TRAITS = ["brave", "quick", "kind", "bold", "bright"]
HERO_TYPES = ["boy", "girl"]
SIDEKICK_TYPES = ["girl", "boy"]

MYSTERIES = {
    "monkey_mess": Mystery(
        culprit="monkey",
        mess="vomit",
        clue="banana bits",
        evidence="a banana peel by the railing",
        solved_by="followed the crumbs to the monkey yard",
    ),
    "bird_mess": Mystery(
        culprit="parrot",
        mess="vomit",
        clue="sunflower seeds",
        evidence="a seed trail under the perch",
        solved_by="followed the seeds to the bird house",
    ),
    "lion_mess": Mystery(
        culprit="lion",
        mess="vomit",
        clue="meat bits",
        evidence="a droopy paw print near the den",
        solved_by="followed the paw prints to the lion den",
    ),
}

SHARING = {
    "napkins": SharingItem(label="napkins", phrase="a stack of clean napkins", helps="wipe the mess"),
    "gloves": SharingItem(label="gloves", phrase="two pairs of rubber gloves", helps="clean safely"),
    "water": SharingItem(label="water bottle", phrase="a water bottle", helps="rinse the floor"),
}


class ZooWorld:
    pass


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for m in MYSTERIES:
        for s in SHARING:
            combos.append((m, s))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero-style zoo mystery with rewriting and sharing.")
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--share-item", choices=SHARING)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--hero-trait", choices=TRAITS)
    ap.add_argument("--sidekick-name", choices=SIDEKICK_NAMES)
    ap.add_argument("--sidekick-type", choices=SIDEKICK_TYPES)
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
    combo_pool = valid_combos()
    if args.mystery and args.share_item:
        if (args.mystery, args.share_item) not in combo_pool:
            raise StoryError("That mystery and sharing item cannot make a believable zoo rescue.")
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    share_item = args.share_item or rng.choice(sorted(SHARING))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    sidekick_type = args.sidekick_type or ("girl" if hero_type == "boy" else "boy")
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick_name or rng.choice(SIDEKICK_NAMES)
    hero_trait = args.hero_trait or rng.choice(TRAITS)
    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        hero_trait=hero_trait,
        sidekick_name=sidekick_name,
        sidekick_type=sidekick_type,
        setting="zoo",
        mystery=mystery,
        share_item=share_item,
    )


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name, traits=[params.hero_trait, "super"]))
    sidekick = world.add(Entity(id="sidekick", kind="character", type=params.sidekick_type, label=params.sidekick_name, traits=["helpful"]))
    mystery = MYSTERIES[params.mystery]
    item = SHARING[params.share_item]
    culprit = world.add(Entity(id="culprit", kind="character", type=mystery.culprit, label=mystery.culprit))
    world.add(Entity(id="item", kind="thing", type=item.label, label=item.label, phrase=item.phrase, owner=hero.id, caretaker=hero.id))
    hero.memes["curiosity"] = 1
    hero.memes["duty"] = 1
    sidekick.memes["help"] = 1
    world.facts.update(hero=hero, sidekick=sidekick, culprit=culprit, mystery=mystery, item=item)
    return world


def tell(world: World) -> None:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    mystery: Mystery = f["mystery"]
    item: SharingItem = f["item"]

    world.say(f"{hero.label} was a small superhero at the zoo, with a bright cape and a quick eye for trouble.")
    world.say(f"{hero.pronoun().capitalize()} and {sidekick.label} loved to patrol the paths, because the zoo always held a mystery to solve.")

    world.para()
    world.say(f"Near {world.setting.place}, they found a nasty vomit stain on the ground.")
    world.say(f"The mess smelled sour, and a clue was stuck nearby: {mystery.clue}.")
    world.say(f"{hero.label} opened {hero.pronoun('possessive')} notebook and rewrote the clue so it made sense: {mystery.evidence}.")

    world.para()
    world.say(f"That meant the mystery pointed to the {mystery.culprit} in the {mystery.solved_by.split(' to the ')[-1]}.")
    world.say(f"But the floor still needed help, so {hero.label} shared {item.phrase} with {sidekick.label}.")
    world.say(f"Together they used the {item.label} to {item.helps}, and the zoo path began to look safe again.")

    world.para()
    world.say(f"At last, the zookeeper thanked them, and {hero.label} stood tall like a true hero.")
    world.say(f"The vomit mystery was solved, the clue was rewritten, and the sharing made the whole cleanup feel like teamwork.")


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    mystery: Mystery = f["mystery"]
    item: SharingItem = f["item"]
    return [
        QAItem(
            question=f"Who was the superhero at the zoo?",
            answer=f"The superhero was {hero.label}, and {hero.label} worked with {sidekick.label} to solve a mystery.",
        ),
        QAItem(
            question=f"What messy thing did they find near the zoo path?",
            answer=f"They found vomit on the ground, so the zoo mystery turned into a cleanup problem too.",
        ),
        QAItem(
            question=f"What clue did {hero.label} rewrite in the notebook?",
            answer=f"{hero.label} rewrote the clue about {mystery.clue} and used it to notice {mystery.evidence}.",
        ),
        QAItem(
            question=f"How did they share the cleanup work?",
            answer=f"{hero.label} shared {item.phrase} with {sidekick.label}, and together they used it to {item.helps}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a zoo?", answer="A zoo is a place where people can visit animals and learn about them."),
        QAItem(question="What does it mean to share?", answer="To share means to give part of something to someone else or use it together."),
        QAItem(question="Why might vomit need cleaning up?", answer="Vomit needs cleaning because it is messy and can smell bad, so people clean it away to keep the area safe."),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    mystery: Mystery = f["mystery"]
    return [
        f"Write a short superhero story about {hero.label} and {sidekick.label} at the zoo.",
        f"Tell a gentle mystery where a vomit stain must be solved with a rewritten clue.",
        f"Make the ending about sharing tools and teamwork after the zoo mystery is solved.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {e.label:10} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/2.
valid(M, S) :- mystery(M), share_item(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for s in SHARING:
        lines.append(asp.fact("share_item", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
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


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        print(f"{len(asp.atoms(model, 'valid'))} compatible mystery/share-item combos:\n")
        for m, s in sorted(set(asp.atoms(model, "valid"))):
            print(f"  {m:12} {s}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for m in sorted(MYSTERIES):
            for s in sorted(SHARING):
                params = StoryParams(
                    hero_name="Milo",
                    hero_type="boy",
                    hero_trait="brave",
                    sidekick_name="Nova",
                    sidekick_type="girl",
                    setting="zoo",
                    mystery=m,
                    share_item=s,
                    seed=base_seed,
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
