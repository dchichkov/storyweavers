#!/usr/bin/env python3
"""
storyworlds/worlds/trap_inner_monologue_rhyme_comedy.py
========================================================

A small comedy story world about a character who plans a trap, thinks
through it in an inner monologue, and ends with a rhyming payoff.

Seed tale inspiration:
---
A kid wants to catch a sneaky cookie thief with a silly trap. The kid talks to
themselves, sets up the trap badly, learns something funny, and finally solves
the problem in a gentle way.
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
    kind: str = "character"
    type: str = "child"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the kitchen"
    afford: set[str] = field(default_factory=lambda: {"trap"})


@dataclass
class TrapPlan:
    id: str
    name: str
    bait: str
    rhyme: str
    failure: str
    fix: str
    keyword: str = "trap"


@dataclass
class StoryParams:
    place: str
    plan: str
    hero_name: str
    hero_type: str
    intruder: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "kitchen": Setting("the kitchen"),
    "hallway": Setting("the hallway"),
    "backyard": Setting("the backyard"),
    "playroom": Setting("the playroom"),
}

PLANS = {
    "bucket": TrapPlan(
        id="bucket",
        name="bucket-on-the-door trap",
        bait="a shiny cookie on a stool",
        rhyme="Clickety-clack, the bucket will whack",
        failure="the bucket tipped sideways and bonked a broom instead",
        fix="the hero tied the string straighter and moved the stool",
    ),
    "sticker": TrapPlan(
        id="sticker",
        name="sticky-note trail trap",
        bait="a trail of crumbs and a bright sticker",
        rhyme="Tip and tap, follow the trap",
        failure="the crumbs made the cat sneeze and skitter in a loop",
        fix="the hero used fewer crumbs and put the sticker lower",
    ),
    "box": TrapPlan(
        id="box",
        name="cardboard box trap",
        bait="a tiny cheese cube under a box",
        rhyme="If the box should bop, do not make it flop",
        failure="the box landed on the hero's sock",
        fix="the hero propped the box with a pencil instead of a pebble",
    ),
}

HEROES = ["Milo", "Tia", "Nora", "Evan", "Pia", "Arlo", "June", "Zuri"]
INTRUDERS = ["cat", "mouse", "raccoon", "cookie thief"]
TYPES = {"girl": "girl", "boy": "boy"}


class ReasonableTrapError(StoryError):
    pass


def trap_reasonable(plan: TrapPlan, place: str, intruder: str) -> bool:
    return place in SETTINGS and plan.id in PLANS and intruder in INTRUDERS


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy trap story world with inner monologue and rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--intruder", choices=INTRUDERS)
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
    place = args.place or rng.choice(list(SETTINGS))
    plan = args.plan or rng.choice(list(PLANS))
    intruder = args.intruder or rng.choice(INTRUDERS)
    if not trap_reasonable(PLANS[plan], place, intruder):
        raise ReasonableTrapError(f"(No story: the {plan} plan does not make a sensible trap for a {intruder} in {place}.)")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HEROES)
    if args.name is None:
        # keep a loose match to gender for friendliness
        if gender == "girl" and name not in {"Tia", "Nora", "Pia", "June", "Zuri"}:
            name = rng.choice(["Tia", "Nora", "Pia", "June", "Zuri"])
        elif gender == "boy" and name not in {"Milo", "Evan", "Arlo"}:
            name = rng.choice(["Milo", "Evan", "Arlo"])
    return StoryParams(place=place, plan=plan, hero_name=name, hero_type=gender, intruder=intruder)


def inner_monologue(hero: Entity, plan: TrapPlan, intruder: str) -> str:
    return (
        f"'{plan.rhyme},' {hero.id} thought. "
        f"'If {intruder} comes creeping, I will catch {hero.pronoun('object')} peeping. "
        f"Easy, breezy, not too hasty. Please, little trap, do not be wasty.'"
    )


def introduce(world: World, hero: Entity, intruder: str, plan: TrapPlan) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(
        f"{hero.id} was a clever little {hero.type} who wanted to catch a sneaky {intruder}."
    )
    world.say(
        f"{hero.id} had a {plan.name} in mind, because {hero.pronoun('possessive')} nose wrinkled at every missing cookie."
    )


def set_trap(world: World, hero: Entity, plan: TrapPlan) -> None:
    hero.meters["setup"] = hero.meters.get("setup", 0) + 1
    world.say(
        f"At {world.setting.place}, {hero.id} set out {plan.bait} and whispered the plan to {hero.pronoun('object')}self."
    )
    world.say(inner_monologue(hero, plan, world.facts["intruder"]))


def comedy_mishap(world: World, hero: Entity, plan: TrapPlan) -> None:
    hero.memes["embarrassment"] = hero.memes.get("embarrassment", 0) + 1
    world.say(f"Then the first try went flop: {plan.failure}.")
    world.say(
        f"{hero.id} blinked, then giggled. 'Well, that was a flop with a plop,' {hero.pronoun()} muttered."
    )


def fix_trap(world: World, hero: Entity, plan: TrapPlan, intruder: str) -> None:
    hero.meters["repair"] = hero.meters.get("repair", 0) + 1
    hero.memes["confidence"] = hero.memes.get("confidence", 0) + 1
    world.say(
        f"So {hero.id} took a breath and tried again: {plan.fix}."
    )
    world.say(
        f"This time the trap sat steady, and the little trail led right where the {intruder} would go."
    )


def ending(world: World, hero: Entity, plan: TrapPlan, intruder: str) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"At last, the {intruder} came by, and the trap clicked just once, neat and quick."
    )
    world.say(
        f"{hero.id} clapped softly and laughed. '{plan.rhyme},' {hero.pronoun()} said, "
        f"'{intruder} got the snack, and I got the knack!'"
    )


def tell(setting: Setting, plan: TrapPlan, hero_name: str, hero_type: str, intruder: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, type=hero_type, kind="character"))
    world.facts["intruder"] = intruder
    world.facts["plan"] = plan
    world.facts["hero"] = hero
    world.facts["setting"] = setting

    introduce(world, hero, intruder, plan)
    world.para()
    set_trap(world, hero, plan)
    comedy_mishap(world, hero, plan)
    world.para()
    fix_trap(world, hero, plan, intruder)
    ending(world, hero, plan, intruder)

    world.facts["resolved"] = True
    return world


ASP_RULES = r"""
plan(plan_bucket).
plan(plan_sticker).
plan(plan_box).

place(kitchen).
place(hallway).
place(backyard).
place(playroom).

intruder(cat).
intruder(mouse).
intruder(raccoon).
intruder(cookie_thief).

reasonable(Place, Plan, Intruder) :- place(Place), plan(Plan), intruder(Intruder).
#show reasonable/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for p in PLANS:
        lines.append(asp.fact("plan", f"plan_{p}"))
    for i in INTRUDERS:
        lines.append(asp.fact("intruder", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    py = {
        (place, f"plan_{plan}", intruder)
        for place in SETTINGS
        for plan in PLANS
        for intruder in INTRUDERS
        if trap_reasonable(PLANS[plan], place, intruder)
    }
    cl = set(asp_reasonable())
    if py == cl:
        print(f"OK: clingo gate matches Python reasonableness ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print(" only in clingo:", sorted(cl - py))
    print(" only in python:", sorted(py - cl))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    plan: TrapPlan = f["plan"]
    intruder = f["intruder"]
    return [
        f'Write a short comedy story about a child named {hero.id} who plans a trap for a {intruder}.',
        f"Tell a gentle story with an inner monologue and a rhyme where {hero.id} tries {plan.name}.",
        f"Write a funny child-friendly story in which a trap fails once, gets fixed, and works in the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    plan: TrapPlan = f["plan"]
    intruder = f["intruder"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.type} who wanted to catch a {intruder} with a silly trap.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to set up {plan.name} and catch the {intruder} without making a big fuss.",
        ),
        QAItem(
            question="What happened after the first try went wrong?",
            answer=f"{hero.id} laughed, fixed the trap, and tried again in a smarter way.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The trap clicked, the {intruder} was caught by the setup, and {hero.id} ended happy and proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a trap?",
            answer="A trap is a setup that is meant to catch something or make it stop for a moment.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private voice in someone's head when they are thinking to themselves.",
        ),
        QAItem(
            question="What does a rhyme do in a story?",
            answer="A rhyme makes words sound playful together, which can make a story feel bouncy and funny.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} ({e.type}) meters={e.meters} memes={e.memes}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", plan="bucket", hero_name="Milo", hero_type="boy", intruder="cat"),
    StoryParams(place="playroom", plan="sticker", hero_name="Tia", hero_type="girl", intruder="mouse"),
    StoryParams(place="backyard", plan="box", hero_name="Arlo", hero_type="boy", intruder="raccoon"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PLANS[params.plan], params.hero_name, params.hero_type, params.intruder)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    plan = args.plan or rng.choice(list(PLANS))
    intruder = args.intruder or rng.choice(INTRUDERS)
    if not trap_reasonable(PLANS[plan], place, intruder):
        raise StoryError(f"(No story: the {plan} trap does not make sense for a {intruder} in {place}.)")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HEROES)
    return StoryParams(place=place, plan=plan, hero_name=name, hero_type=gender, intruder=intruder)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reasonable/3."))
        combos = sorted(set(asp.atoms(model, "reasonable")))
        print(f"{len(combos)} reasonable combos:")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.hero_name}: {p.plan} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
